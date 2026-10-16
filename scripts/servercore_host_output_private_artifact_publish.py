"""Complete existing Gateway/Vault cipher inbox -> private GitHub Actions Artifact.

No new workflow, token, key generation, public artifact, or always-on service.
The private TGserver *existing CI workflow* turns a temporary private release
asset into a one-day Actions Artifact, then deletes that release/tag.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

try:
    from scripts.servercore_host_output_cipher_inbox import collect, InboxError
    from scripts.servercore_host_output_gateway_relay import post_json, private_endpoint, canonical_base64, RelayError
    from scripts.servercore_host_output_artifact_assemble import verify_artifact_zip
    from scripts.servercore_host_output_export import export_output
except ModuleNotFoundError:
    from servercore_host_output_cipher_inbox import collect, InboxError
    from servercore_host_output_gateway_relay import post_json, private_endpoint, canonical_base64, RelayError
    from servercore_host_output_artifact_assemble import verify_artifact_zip
    from servercore_host_output_export import export_output

DEFAULT_WRITER = Path("/home/admin1/logs/servercore-service-deploy")
REPO = "seigo-gace/TGserver"  # verified private repo, owning existing CI
RID = re.compile(r"req_[a-f0-9]{24}\Z")


class PublishError(ValueError):
    pass


def independently_expected(request_id, *, writer_dir=DEFAULT_WRITER):
    path=Path(writer_dir)/(request_id+".json")
    if path.is_symlink() or not path.is_file():
        raise PublishError("WRITER_LEDGER_MISSING")
    record=json.loads(path.read_text(encoding="utf-8"))
    if record.get("request_id") != request_id:
        raise PublishError("WRITER_ID_MISMATCH")
    expected={}
    for name in ("stdout","stderr"):
        value=record.get(name)
        if not isinstance(value,str):
            raise PublishError("WRITER_STREAM_MISSING")
        encoded=value.encode("utf-8")
        expected[name]={"sha256":hashlib.sha256(encoded).hexdigest(),
                        "bytes":len(encoded),"chars":len(value)}
    return expected


def reconstruct(request_id, target, *, vault_base, vault_token,
                cipher_root, expected_key_ref, expected_consumer,
                writer_dir=DEFAULT_WRITER, opener=None):
    if not RID.fullmatch(request_id):
        raise PublishError("REQUEST_ID_INVALID")
    parts=collect(request_id,root=cipher_root)
    # Project/key/consumer are locally authorized inputs, never selected by
    # an arbitrary Gateway event. Gateway keys are not role-scoped.
    if not expected_key_ref or not expected_consumer or any(
        p["vault_ref"] != expected_key_ref or p["consumer"] != expected_consumer for p in parts
    ):
        raise PublishError("VAULT_CONSUMER_CONTRACT_MISMATCH")
    url=private_endpoint(vault_base,"/internal/v1/crypto/unseal")
    path=Path(target)
    if path.exists() or path.is_symlink():
        raise PublishError("DEST_ALREADY_EXISTS")
    result_digest=hashlib.sha256()
    written=0
    # Plaintext only in private 0600 local temporary file; no stdout/log.
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"wb") as f:
            for p in parts:
                c64="".join(p["ciphertext_parts"])
                status,body=post_json(url,{
                    "ciphertext":c64,"iv":p["iv"],
                    "key_ref":p["vault_ref"],"consumer":p["consumer"],
                },vault_token,opener=opener)
                if status!=200 or not isinstance(body,dict):
                    raise PublishError("VAULT_UNSEAL_UNCONFIRMED")
                raw=canonical_base64(body.get("plaintext_base64"))
                if (len(raw)!=p["chunk_bytes"] or
                    hashlib.sha256(raw).hexdigest()!=p["chunk_sha256"]):
                    raise PublishError("UNSEALED_CHUNK_DIGEST_MISMATCH")
                f.write(raw)
                written+=len(raw)
                result_digest.update(raw)
            f.flush()
            os.fsync(f.fileno())
        if written!=parts[0]["zip_bytes"] or result_digest.hexdigest()!=parts[0]["zip_sha256"]:
            raise PublishError("ZIP_DIGEST_MISMATCH")
        trusted=independently_expected(request_id,writer_dir=writer_dir)
        result=verify_artifact_zip(path,request_id,trusted)
        if result.get("output_complete") is not True:
            raise PublishError("WRITER_ZIP_NOT_COMPLETE")
        return {"request_id":request_id,"zip_bytes":written,
                "zip_sha256":result_digest.hexdigest(),"streams":result["streams"],
                "state":"FULL_ZIP_VERIFIED_LOCAL"}
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def private_release(request_id, path, *, runner=subprocess.run):
    """Use existing authenticated gh CLI, not an additional token."""
    tag="gace-host-output-"+request_id
    # Fail closed if a collaborator changed the recipient repository's
    # visibility; do not silently publish output in a public repository.
    try:
        privacy=runner(["gh","api","repos/"+REPO,"--jq",".private"],
                       capture_output=True,text=True,timeout=15,check=False)
    except (OSError,subprocess.TimeoutExpired):
        raise PublishError("PRIVATE_GITHUB_UNAVAILABLE") from None
    if privacy.returncode!=0 or privacy.stdout.strip()!="true":
        raise PublishError("PRIVATE_REPOSITORY_NOT_VERIFIED")
    cmds=[
      ["gh","release","create",tag,str(path)+"#output.zip",
       "--repo",REPO,"--draft","--prerelease","--latest=false",
       "--title","G-ACE temporary Host artifact "+request_id,
       "--notes","Private transient handoff to existing TGS CI Artifact. No Issue contents."],
      ["gh","release","edit",tag,"--repo",REPO,"--draft=false"],
    ]
    created=False
    for cmd in cmds:
        try:
            p=runner(cmd,capture_output=True,text=True,timeout=60,check=False)
            if p.returncode:
                raise PublishError("PRIVATE_RELEASE_SUBMISSION_FAILED")
            created=True
        except (OSError,subprocess.TimeoutExpired,PublishError):
            # If publication failed *after* our draft was created, clean it.
            # If create itself failed, do not delete another attempt's tag.
            if created:
                try:
                    runner(["gh","release","delete",tag,"--repo",REPO,"--yes","--cleanup-tag"],
                           capture_output=True,text=True,timeout=20,check=False)
                except (OSError,subprocess.TimeoutExpired):
                    pass
            raise PublishError("PRIVATE_RELEASE_SUBMISSION_FAILED") from None
    return {"state":"PRIVATE_RELEASE_PUBLISHED_AWAIT_ARTIFACT",
            "repository":REPO,"release_tag":tag}


def run(request_id, *, cipher_root, writer_dir, vault_base, vault_token,
        expected_key_ref, expected_consumer,
        verify_only=False, opener=None, runner=subprocess.run):
    with tempfile.TemporaryDirectory(prefix="gace-private-output-") as temp:
        archive=Path(temp,"output.zip")
        status=reconstruct(request_id,archive,vault_base=vault_base,
                           vault_token=vault_token,cipher_root=cipher_root,
                           expected_key_ref=expected_key_ref,
                           expected_consumer=expected_consumer,
                           writer_dir=writer_dir,opener=opener)
        if verify_only:
            return status
        return {**status, **private_release(request_id,archive,runner=runner)}


def publish_writer_output(request_id, *, writer_dir=DEFAULT_WRITER,
                          verify_only=False, runner=subprocess.run):
    """Recover an existing result on its trusted Host, without executing it again.

    Explicit local input, never an automatic fallback after Vault failure.
    The caller must already have read access to the protected Writer ledger.
    Remote CHAT still uses the admitted Host channel; no HTTP endpoint is added.
    """
    if not isinstance(request_id, str) or not RID.fullmatch(request_id):
        raise PublishError("REQUEST_ID_INVALID")
    expected = independently_expected(request_id, writer_dir=writer_dir)
    with tempfile.TemporaryDirectory(prefix="gace-private-output-") as temp:
        archive = Path(temp, "output.zip")
        export_output(request_id, archive, result_dir=writer_dir, zipped=True)
        # Independent ledger expectations also detect changes during export.
        verified = verify_artifact_zip(archive, request_id, expected)
        with archive.open("rb") as source:
            zip_digest = hashlib.file_digest(source, "sha256").hexdigest()
        status = {"request_id": request_id, "streams": verified["streams"],
                  "state": "FULL_ZIP_VERIFIED_LOCAL", "input": "writer-ledger",
                  "zip_bytes": archive.stat().st_size,
                  "zip_sha256": zip_digest}
        if verify_only:
            return status
        return {**status, **private_release(request_id, archive, runner=runner)}


def main():
    parser=argparse.ArgumentParser(description="Host private ZIP verification and existing CI handoff")
    parser.add_argument("request_id")
    parser.add_argument("--cipher-root",default="/run/gace/host-output-inbox")
    parser.add_argument("--writer-dir",default=str(DEFAULT_WRITER))
    parser.add_argument("--vault-base",default="http://127.0.0.1:8791")
    parser.add_argument("--vault-key-ref",help="existing approved crypto ref")
    parser.add_argument("--vault-consumer",help="approved consumer")
    parser.add_argument("--writer-ledger",action="store_true",
                        help="explicit local protected Writer input; no Vault fallback")
    parser.add_argument("--vault-token-file",default="/home/admin1/.config/libral-vault/internal-token")
    parser.add_argument("--verify-only",action="store_true")
    x=parser.parse_args()
    if x.writer_ledger and (x.vault_key_ref or x.vault_consumer):
        parser.error("--writer-ledger cannot select a Vault consumer")
    if not x.writer_ledger and (not x.vault_key_ref or not x.vault_consumer):
        parser.error("encrypted input requires --vault-key-ref and --vault-consumer")
    try:
        if x.writer_ledger:
            result=publish_writer_output(x.request_id,writer_dir=x.writer_dir,
                                         verify_only=x.verify_only)
        else:
            token=Path(x.vault_token_file).read_text().strip()
            result=run(x.request_id,cipher_root=x.cipher_root,writer_dir=x.writer_dir,
                       vault_base=x.vault_base,vault_token=token,
                       expected_key_ref=x.vault_key_ref,expected_consumer=x.vault_consumer,
                       verify_only=x.verify_only)
        print(json.dumps(result,sort_keys=True))
    except (PublishError,InboxError,RelayError,ValueError,OSError) as exc:
        print("CU40_PRIVATE_OUTPUT_HANDOFF=FAILED")
        raise SystemExit(1) from None


if __name__=="__main__":
    main()
