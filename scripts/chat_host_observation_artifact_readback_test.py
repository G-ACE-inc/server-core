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

    def test_sha_mismatch_carries_only_correlated_recovery_evidence(self):
        record = self.record()
        record.update({"observation": "HOST_SOURCE_SHA_MISMATCH",
                       "next_action": "READBACK_HOST_SHA_AND_REPLAN_AUTHORIZED_ACTION",
                       "host_sha": "d" * 40, "exit_code": 1})
        result = validate(record, RID)
        self.assertEqual(result["expected_sha"], SHA)
        self.assertEqual(result["host_sha"], "d" * 40)
        self.assertEqual(result["exit_code"], 1)
        self.assertNotIn("stdout", result)
        record["host_sha"] = SHA
        with self.assertRaisesRegex(ValueError, "HOST_SHA_MISMATCH_EVIDENCE_INVALID"):
            validate(record, RID)

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


    def test_metadata_only_must_not_claim_full_payload(self):
        record = self.record()
        record["observation"] = "HOST_OPERATION_PASSED"
        record["next_action"] = "RECHECK_MISSION_ACCEPTANCE_AND_CONTINUE"
        record["streams"] = {
            "stdout": {"complete": True, "sha256": None, "chars": None},
            "stderr": {"complete": True, "sha256": None, "chars": None},
        }
        result = validate(record, RID)
        self.assertFalse(result["output_complete"])
        self.assertEqual(result["next_action"], "INSPECT_HOST_LEDGER_OUTPUT_COMPLETENESS_AND_CONTINUE")

    def test_full_hashes_can_validate_stream_metadata(self):
        record = self.record()
        record["streams"]["stdout"] = {"complete": True, "sha256": DIGEST, "chars": 100}
        result = validate(record, RID)
        self.assertFalse(result["output_complete"])
        self.assertTrue(result["stream_metadata_complete"])


if __name__ == "__main__":
    unittest.main()
