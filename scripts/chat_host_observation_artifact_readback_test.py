import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.chat_host_observation_artifact_readback import from_artifact, validate

RID = "req_" + "a" * 24
SHA = "b" * 40
DIGEST = "c" * 64


class ObservationReadbackTests(unittest.TestCase):
    def record(self):
        return {
            "request_id": RID, "command_id": "host.command", "expected_sha": SHA,
            "result_verified": True, "observation": "HOST_OUTPUT_PARTIAL",
            "next_action": "READ_STORED_HOST_OUTPUT_CHUNKS_AND_CONTINUE",
            "result_url": "https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-1",
            "streams": {
                "stdout": {"complete": False, "sha256": DIGEST, "chars": 50000},
                "stderr": {"complete": True, "sha256": DIGEST, "chars": 0},
            }, "stdout": "SENSITIVE_HOST_OUTPUT",
        }

    def test_only_safe_decision_fields(self):
        result = validate(self.record(), RID)
        self.assertFalse(result["output_complete"])
        self.assertNotIn("SENSITIVE_HOST_OUTPUT", json.dumps(result))
        self.assertEqual(result["observation"], "HOST_OUTPUT_PARTIAL")

    def test_request_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "REQUEST_MISMATCH"):
            validate(self.record(), "req_" + "d" * 24)

    def test_unverified_timeout_roundtrip(self):
        result = validate({"request_id": RID, "result_verified": False,
                           "observation": "HOST_RESULT_NOT_RETURNED",
                           "next_action": "INSPECT_HOST_DISPATCH_AND_REPLAN"}, RID)
        self.assertFalse(result["result_verified"])

    def test_archive_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "host.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("gace-chat-host-observation.json", json.dumps(self.record()))
            self.assertEqual(from_artifact(path, RID)["request_id"], RID)

    def test_wrong_file_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "host.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("stdout.txt", "UNSAFE")
            with self.assertRaisesRegex(ValueError, "ARTIFACT_CONTENT_INVALID"):
                from_artifact(path, RID)


if __name__ == "__main__":
    unittest.main()
