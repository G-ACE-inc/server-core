"""CU40 full Writer -> ZIP -> encrypted Gateway inbox -> Vault -> private GH handoff."""
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.servercore_host_output_export import export_output
from scripts.servercore_host_output_cipher_inbox import store
from scripts.servercore_host_output_private_artifact_publish import run, publish_writer_output

RID="req_"+"9"*24

class Reply:
    status=200
    def __init__(self,obj):self.data=json.dumps(obj).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.data[:n]

class MockVault:
    def __init__(self,fragments):self.fragments=fragments;self.fail=False
    def __call__(self,request):
        req=json.loads(request.data)
        assert request.full_url.endswith("/internal/v1/crypto/unseal")
        i=int.from_bytes(base64.b64decode(req["iv"]),"big")
        raw=self.fragments[i]
        if self.fail:raw=b"altered"
        return Reply({"plaintext_base64":base64.b64encode(raw).decode()})

class MockRelease:
    def __init__(self):self.calls=[]
    def __call__(self,args,**_):
        self.calls.append(args)
        class Result:
            returncode=0
            stdout="true"
        return Result()

def setup(directory):
    root=Path(directory)
    stdout="日本語Ω🙂\n"*30000
    stderr="error日本語\n"*12000
    (root/(RID+".json")).write_text(json.dumps({"request_id":RID,"stdout":stdout,"stderr":stderr}),encoding="utf-8")
    zip_path=root/"source.zip"
    export_output(RID,zip_path,result_dir=root,zipped=True)
    data=zip_path.read_bytes()
    fragments=[data[i:i+131072] for i in range(0,len(data),131072)]
    inbox=root/"cipher"
    for i,part in enumerate(fragments):
        ct=base64.b64encode(b"x"*(len(part)+16)).decode()
        iv=base64.b64encode(i.to_bytes(12,"big")).decode()
        store({"schema":"gace.host-output.encrypted-chunk/v1",
          "request_id":RID,"zip_sha256":hashlib.sha256(data).hexdigest(),
          "zip_bytes":len(data),"total_parts":len(fragments),"index":i,
          "chunk_bytes":len(part),"chunk_sha256":hashlib.sha256(part).hexdigest(),
          "vault_ref":"registered-ref","consumer":"g-ace-workspace",
          "iv":iv,"ciphertext_parts":[ct[j:j+3000] for j in range(0,len(ct),3000)]},
          root=inbox)
    return inbox,fragments,stdout,stderr

class FullBridgeTests(unittest.TestCase):
    def writer(self, directory):
        Path(directory, RID + ".json").write_text(json.dumps({
            "request_id": RID, "stdout": "日本語 result\n", "stderr": ""}), encoding="utf-8")

    def test_local_writer_reuses_private_release_without_vault(self):
        with tempfile.TemporaryDirectory() as d:
            self.writer(d)
            gh = MockRelease()
            result = publish_writer_output(RID, writer_dir=d, runner=gh)
            self.assertEqual(result["state"], "PRIVATE_RELEASE_PUBLISHED_AWAIT_ARTIFACT")
            self.assertEqual(result["input"], "writer-ledger")
            self.assertEqual(result["streams"]["stdout"]["chars"], len("日本語 result\n"))
            self.assertNotIn("日本語", json.dumps(result, ensure_ascii=False))
            self.assertEqual(len(gh.calls), 3)
            archive_arg = gh.calls[1][4]
            self.assertFalse(Path(archive_arg.split("#")[0]).exists())

    def test_local_verify_does_not_publish(self):
        with tempfile.TemporaryDirectory() as d:
            self.writer(d)
            gh = MockRelease()
            result = publish_writer_output(RID, writer_dir=d, verify_only=True, runner=gh)
            self.assertEqual(result["state"], "FULL_ZIP_VERIFIED_LOCAL")
            self.assertEqual(gh.calls, [])

    def test_missing_or_mismatched_ledger_never_publishes(self):
        with tempfile.TemporaryDirectory() as d:
            gh = MockRelease()
            with self.assertRaisesRegex(ValueError, "WRITER_LEDGER_MISSING"):
                publish_writer_output(RID, writer_dir=d, runner=gh)
            Path(d, RID + ".json").write_text(json.dumps({"request_id": "wrong"}))
            with self.assertRaisesRegex(ValueError, "WRITER_ID_MISMATCH"):
                publish_writer_output(RID, writer_dir=d, runner=gh)
            self.assertEqual(gh.calls, [])

    def test_local_writer_refuses_public_recipient(self):
        with tempfile.TemporaryDirectory() as d:
            self.writer(d)
            calls = []
            def public(args, **kwargs):
                calls.append(args)
                class Result:
                    returncode = 0
                    stdout = "false"
                return Result()
            with self.assertRaisesRegex(ValueError, "PRIVATE_REPOSITORY_NOT_VERIFIED"):
                publish_writer_output(RID, writer_dir=d, runner=public)
            self.assertEqual(len(calls), 1)

    def test_changed_ledger_fails_independent_digest_before_upload(self):
        from unittest.mock import patch
        from scripts.servercore_host_output_private_artifact_publish import independently_expected
        with tempfile.TemporaryDirectory() as d:
            self.writer(d)
            expected = independently_expected(RID, writer_dir=d)
            Path(d, RID + ".json").write_text(json.dumps({
                "request_id": RID, "stdout": "different", "stderr": ""}))
            gh = MockRelease()
            with patch("scripts.servercore_host_output_private_artifact_publish.independently_expected",
                       return_value=expected):
                with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_MANIFEST_MISMATCH"):
                    publish_writer_output(RID, writer_dir=d, runner=gh)
            self.assertEqual(gh.calls, [])

    def test_local_request_id_cannot_select_other_paths(self):
        for rid in ("../ledger", None, "req_" + "f" * 23):
            with self.subTest(rid=rid), self.assertRaisesRegex(ValueError, "REQUEST_ID_INVALID"):
                publish_writer_output(rid)

    def test_full_verified_zip_and_private_release_only_after_original_hash(self):
        with tempfile.TemporaryDirectory() as d:
            inbox,frags,out,err=setup(d)
            mock=MockVault(frags)
            gh=MockRelease()
            v=run(RID,cipher_root=inbox,writer_dir=d,vault_base="http://127.0.0.1:8791",
                  vault_token="x",expected_key_ref="registered-ref",
                  expected_consumer="g-ace-workspace",opener=mock,runner=gh)
            self.assertEqual(v["state"],"PRIVATE_RELEASE_PUBLISHED_AWAIT_ARTIFACT")
            self.assertEqual(v["streams"]["stdout"]["bytes"],len(out.encode()))
            self.assertEqual(v["streams"]["stderr"]["chars"],len(err))
            self.assertEqual(len(gh.calls),3)
            self.assertEqual(gh.calls[0][:3],["gh","api","repos/seigo-gace/TGserver"])
            self.assertEqual(gh.calls[1][:3],["gh","release","create"])
            self.assertIn("seigo-gace/TGserver",gh.calls[1])

    def test_corrupt_unseal_denied_without_github_upload(self):
        with tempfile.TemporaryDirectory() as d:
            inbox,frags,*_=setup(d)
            mock=MockVault(frags);mock.fail=True
            gh=MockRelease()
            with self.assertRaisesRegex(ValueError,"UNSEALED_CHUNK_DIGEST_MISMATCH"):
                run(RID,cipher_root=inbox,writer_dir=d,vault_base="http://127.0.0.1:8791",
                    vault_token="x",expected_key_ref="registered-ref",
                  expected_consumer="g-ace-workspace",opener=mock,runner=gh)
            self.assertEqual(gh.calls,[])


    def test_attacker_supplied_consumer_never_selects_vault_key(self):
        with tempfile.TemporaryDirectory() as d:
            inbox,frags,*_=setup(d)
            gh=MockRelease()
            with self.assertRaisesRegex(ValueError,"VAULT_CONSUMER_CONTRACT_MISMATCH"):
                run(RID,cipher_root=inbox,writer_dir=d,vault_base="http://127.0.0.1:8791",
                    vault_token="x",expected_key_ref="another-protected-ref",
                    expected_consumer="g-ace-workspace",opener=MockVault(frags),runner=gh)
            self.assertEqual(gh.calls,[])

if __name__=="__main__": unittest.main()
