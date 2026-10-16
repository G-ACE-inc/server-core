"""One purposeful check for the real Host ZIP -> existing Vault/Gateway APIs."""
import base64
import hashlib
import io
import json
import random
import string
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.error import HTTPError

from scripts.servercore_host_output_gateway_relay import (
    CHUNK_BYTES, RelayError, export_and_relay, private_endpoint,
)


RID = "req_" + "7" * 24


class Response:
    def __init__(self, status, obj):
        self.status = status
        self.value = json.dumps(obj).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def read(self, max_bytes):
        return self.value[:max_bytes]


class ExistingApi:
    def __init__(self):
        self.frags = []
        self.gateway = []
        self.fail_vault = False

    def __call__(self, request):
        url = request.full_url
        body = json.loads(request.data)
        if url.endswith("/internal/v1/crypto/seal"):
            if self.fail_vault:
                raise HTTPError(url, 403, "denied", {}, None)
            frag = base64.b64decode(body["plaintext_base64"], validate=True)
            self.frags.append(frag)
            # Fake response tests interface only; the runtime cryptography
            # is the *existing Vault service*, never implemented here.
            return Response(200, {
                "iv": base64.b64encode(b"I" * 12).decode(),
                "ciphertext": base64.b64encode(b"C" * len(frag) + b"A" * 16).decode(),
            })
        if url.endswith("/internal/events"):
            self.gateway.append(body)
            if "plaintext_base64" in json.dumps(body):
                raise AssertionError("RAW_HOST_LOG_LEAKED_TO_GATEWAY")
            return Response(202, {"ok": True, "deliveries": 1})
        raise AssertionError("WRONG_EXISTING_API")


class ConfidentialRelayTests(unittest.TestCase):
    def test_complete_unicode_stdout_stderr_go_through_seal_only(self):
        # Incompressible enough to require several existing Gateway events.
        rng = random.Random(14)
        noise = "".join(rng.choices(string.ascii_letters + string.digits, k=600000))
        stdout = "日本語Ω🙂\\n" * 20000 + noise
        stderr = "stderr日本語\n" * 40000
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, RID + ".json").write_text(json.dumps({
                "request_id": RID, "stdout": stdout, "stderr": stderr
            }), encoding="utf-8")
            api = ExistingApi()
            result = export_and_relay(
                RID, result_dir=directory, vault_base="http://127.0.0.1:8791",
                vault_token="x", vault_key_ref="configured-existing-ref",
                vault_consumer="g-ace-workspace", gateway_base="https://gateway.example",
                gateway_token="x", destination_id="registered-output-target",
                opener=api,
            )
            assert result["parts_enqueued"] > 1
            assert result["parts_enqueued"] == len(api.gateway) == len(api.frags)
            archive = b"".join(api.frags)
            self.assertEqual(hashlib.sha256(archive).hexdigest(), result["zip_sha256"])
            self.assertEqual(len(archive), result["zip_bytes"])
            with zipfile.ZipFile(io.BytesIO(archive)) as z:
                self.assertEqual(z.read("stdout.txt"), stdout.encode("utf-8"))
                self.assertEqual(z.read("stderr.txt"), stderr.encode("utf-8"))
                self.assertEqual(json.loads(z.read("manifest.json"))["request_id"], RID)
            for i, event in enumerate(api.gateway):
                data = event["data"]
                self.assertEqual(data["index"], i)
                self.assertEqual(data["total_parts"], result["parts_enqueued"])
                self.assertEqual(data["zip_sha256"], result["zip_sha256"])
                self.assertLessEqual(data["chunk_bytes"], CHUNK_BYTES)
                self.assertEqual(data["schema"], "gace.host-output.encrypted-chunk/v1")
                self.assertNotIn("plaintext_base64", data)
            self.assertEqual(result["state"], "GATEWAY_ENQUEUED_NOT_CHAT_DELIVERED")
            self.assertFalse(list(Path(directory).glob("gace-host-output-*")))

    def test_rejected_vault_fails_before_gateway(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, RID + ".json").write_text(json.dumps({
                "request_id": RID, "stdout": "private", "stderr": ""
            }), encoding="utf-8")
            api = ExistingApi()
            api.fail_vault = True
            with self.assertRaisesRegex(RelayError, "INTERNAL_API_HTTP_403"):
                export_and_relay(
                    RID, result_dir=directory, vault_base="http://127.0.0.1:8791",
                    vault_token="x", vault_key_ref="configured-existing-ref",
                    vault_consumer="g-ace-workspace", gateway_base="https://gateway.example",
                    gateway_token="x", destination_id="registered-output-target",
                    opener=api,
                )
            self.assertEqual(api.gateway, [])

    def test_denies_external_http_and_invalid_request_id(self):
        with self.assertRaisesRegex(RelayError, "PRIVATE_ENDPOINT_REQUIRED"):
            private_endpoint("http://not-private.example", "/internal/events")
        with self.assertRaisesRegex(RelayError, "ENDPOINT_INVALID"):
            private_endpoint("https://example.com/?key=x", "/internal/events")
        with self.assertRaisesRegex(RelayError, "REQUEST_ID_INVALID"):
            export_and_relay("garbage", result_dir="/unused")


if __name__ == "__main__":
    unittest.main()
