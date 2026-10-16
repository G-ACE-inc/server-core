"""Thin adapter: existing Host ZIP -> Libral Vault seal -> Gateway internal events.

Does not implement a new transport, issue sink or key service. The chosen
Gateway destination must already be registered and must consume encrypted
chunks; 202 means durable enqueue, never downstream CHAT receipt.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

try:
    from scripts.servercore_host_output_export import export_output
except ModuleNotFoundError:
    from servercore_host_output_export import export_output


REQUEST = re.compile(r"req_[0-9a-f]{24}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9._:/-]{1,160}\Z")
CHUNK_BYTES = 128 * 1024  # below both existing Vault 2 MB and Gateway 1 MB limits


class RelayError(ValueError):
    pass


def private_endpoint(base, suffix):
    """Accept HTTPS or loopback HTTP only; never follow untrusted URLs."""
    p = urlparse(base)
    if (p.scheme != "https" and not (p.scheme == "http" and
            p.hostname in {"127.0.0.1", "localhost", "::1"})):
        raise RelayError("PRIVATE_ENDPOINT_REQUIRED")
    if not p.netloc or p.username or p.password or p.query or p.fragment or p.path not in ("", "/"):
        raise RelayError("ENDPOINT_INVALID")
    return base.rstrip("/") + suffix


def post_json(url, payload, token, *, opener=None):
    if not token or not isinstance(token, str):
        raise RelayError("INTERNAL_TOKEN_UNAVAILABLE")
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token,
        "User-Agent": "gace-host-output-existing-api/1",
    })
    try:
        if opener is None:
            response = urllib.request.urlopen(req, timeout=30)
        else:
            response = opener(req)
        with response:
            if response.status not in (200, 201, 202):
                raise RelayError("INTERNAL_API_REJECTED")
            raw = response.read(1_048_577)
            if len(raw) > 1_048_576:
                raise RelayError("INTERNAL_RESPONSE_TOO_LARGE")
            return response.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        # Do not propagate response bodies: they can contain sensitive values.
        raise RelayError("INTERNAL_API_HTTP_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RelayError("INTERNAL_API_UNAVAILABLE") from None


def canonical_base64(value):
    if not isinstance(value, str):
        raise RelayError("VAULT_ENVELOPE_INVALID")
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception:
        raise RelayError("VAULT_ENVELOPE_INVALID") from None
    if base64.b64encode(decoded).decode("ascii") != value:
        raise RelayError("VAULT_ENVELOPE_INVALID")
    return decoded


def relay_zip(zip_path, *, request_id, vault_base, vault_token,
              vault_key_ref, vault_consumer, gateway_base, gateway_token,
              destination_id, opener=None):
    """Send ciphertext only; never log plaintext, auth tokens or envelopes."""
    if not REQUEST.fullmatch(request_id):
        raise RelayError("REQUEST_ID_INVALID")
    if not all(isinstance(x, str) and IDENTIFIER.fullmatch(x)
               for x in (vault_key_ref, vault_consumer, destination_id)):
        raise RelayError("ROUTE_OR_CONSUMER_INVALID")
    vault_url = private_endpoint(vault_base, "/internal/v1/crypto/seal")
    gateway_url = private_endpoint(gateway_base, "/internal/events")
    path = Path(zip_path)
    if path.is_symlink() or not path.is_file():
        raise RelayError("ZIP_UNAVAILABLE")
    archive_sha = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            archive_sha.update(block)
    digest = archive_sha.hexdigest()
    total_bytes = path.stat().st_size
    if not total_bytes:
        raise RelayError("EMPTY_ZIP")
    parts = (total_bytes + CHUNK_BYTES - 1) // CHUNK_BYTES
    delivered = 0
    with path.open("rb") as stream:
        for index in range(parts):
            fragment = stream.read(CHUNK_BYTES)
            status, sealed = post_json(vault_url, {
                "plaintext_base64": base64.b64encode(fragment).decode("ascii"),
                "key_ref": vault_key_ref, "consumer": vault_consumer,
            }, vault_token, opener=opener)
            if status != 200 or not isinstance(sealed, dict):
                raise RelayError("VAULT_SEAL_UNCONFIRMED")
            ciphertext = canonical_base64(sealed.get("ciphertext"))
            iv = canonical_base64(sealed.get("iv"))
            if len(iv) != 12 or len(ciphertext) != len(fragment) + 16:
                raise RelayError("VAULT_ENVELOPE_INVALID")
            # The existing Gateway sanitizer limits each string to 4,000 chars
            # and redacts keys containing "key". Preserve the encrypted bytes
            # with smaller individually-safe string pieces, not a new API.
            ciphertext_parts = [sealed["ciphertext"][start:start + 3000]
                                for start in range(0, len(sealed["ciphertext"]), 3000)]
            # The full ciphertext is the only body that enters Gateway/DB.
            # Its digest participates in the idempotency ID so a fresh seal
            # cannot conflict with a previously accepted, randomized envelope.
            tag = hashlib.sha256(iv + ciphertext).hexdigest()[:20]
            event_id = f"hostout.{request_id}.{index}.{tag}"
            status, receipt = post_json(gateway_url, {
                "eventId": event_id,
                "eventType": "gace.host-output.encrypted-chunk.v1",
                "sourceId": "server-core-host",
                "destinationId": destination_id,
                "subject": "host-output/" + request_id,
                "data": {
                    "schema": "gace.host-output.encrypted-chunk/v1",
                    "request_id": request_id,
                    "zip_sha256": digest,
                    "zip_bytes": total_bytes,
                    "total_parts": parts,
                    "index": index,
                    "chunk_bytes": len(fragment),
                    "chunk_sha256": hashlib.sha256(fragment).hexdigest(),
                    "vault_ref": vault_key_ref,
                    "consumer": vault_consumer,
                    "ciphertext_parts": ciphertext_parts,
                    "iv": sealed["iv"],
                },
            }, gateway_token, opener=opener)
            if status != 202 or not isinstance(receipt, dict) or receipt.get("ok") is not True:
                raise RelayError("GATEWAY_ENQUEUE_UNCONFIRMED")
            delivered += 1
    return {"request_id": request_id, "zip_bytes": total_bytes,
            "zip_sha256": digest, "parts_enqueued": delivered,
            "state": "GATEWAY_ENQUEUED_NOT_CHAT_DELIVERED"}


def export_and_relay(request_id, *, result_dir, **kwargs):
    if not REQUEST.fullmatch(request_id):
        raise RelayError("REQUEST_ID_INVALID")
    # Temporary plaintext ZIP is local-only, mode 0600, removed on return/failure.
    with tempfile.TemporaryDirectory(prefix="gace-host-output-") as tmp:
        path = Path(tmp, "output.zip")
        export_output(request_id, path, result_dir=result_dir, zipped=True)
        return relay_zip(path, request_id=request_id, **kwargs)


def main():
    parser = argparse.ArgumentParser(description="Relay confidential Host ZIP through existing Vault/Gateway APIs")
    parser.add_argument("request_id")
    parser.add_argument("--destination", required=True, help="Existing registered Gateway destination ID")
    parser.add_argument("--vault-key-ref", required=True, help="Existing authorized Vault AES key reference")
    parser.add_argument("--vault-consumer", required=True, help="Existing approved Vault consumer")
    parser.add_argument("--vault-base", default="http://127.0.0.1:8791")
    parser.add_argument("--gateway-base", required=True)
    parser.add_argument("--vault-token-file", default="/home/admin1/.config/libral-vault/internal-token")
    parser.add_argument("--ledger-dir", default="/home/admin1/logs/servercore-service-deploy")
    args = parser.parse_args()
    try:
        token = Path(args.vault_token_file).read_text(encoding="utf-8").strip()
        result = export_and_relay(
            args.request_id, result_dir=args.ledger_dir,
            vault_base=args.vault_base, vault_token=token,
            vault_key_ref=args.vault_key_ref, vault_consumer=args.vault_consumer,
            gateway_base=args.gateway_base,
            gateway_token=os.environ.get("GACE_EVENT_GATEWAY_TOKEN", ""),
            destination_id=args.destination,
        )
        print(json.dumps(result, sort_keys=True))
    except (RelayError, OSError) as exc:
        reason = str(exc) if isinstance(exc, RelayError) else "PRIVATE_RUNTIME_UNAVAILABLE"
        raise SystemExit(reason) from None


if __name__ == "__main__":
    main()
