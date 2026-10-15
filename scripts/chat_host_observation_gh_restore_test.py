import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.chat_host_observation_gh_restore import restore

RID = "req_" + "a" * 24
SHA = "b" * 40


class RestoreTests(unittest.TestCase):
    def fake_run(self, cmd, **kwargs):
        if cmd[1] == "api" and "/artifacts?" not in cmd[2]:
            payload = {"head_sha": SHA}
        elif cmd[1] == "api":
            payload = {"artifacts": [{"id": 19, "name": "chat-host-observation-" + SHA, "expired": False}]}
        else:
            Path(cmd[-1], "gace-chat-host-observation.json").write_text(json.dumps({
                "request_id": RID, "observation": "HOST_RESULT_NOT_RETURNED",
                "next_action": "INSPECT_HOST_DISPATCH_AND_REPLAN", "result_verified": False,
            }), encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, stdout="")
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload))

    def test_restores_existing_run_without_issue_scans(self):
        result = restore("G-ACE-inc/server-core", 123, RID, run=self.fake_run)
        self.assertEqual(result["artifact_id"], 19)
        self.assertEqual(result["request_id"], RID)
        self.assertFalse(result["result_verified"])
        self.assertEqual(result["source_sha"], SHA)

    def test_request_mismatch_denied(self):
        def wrong_run(cmd, **kwargs):
            if cmd[1] == "run":
                Path(cmd[-1], "gace-chat-host-observation.json").write_text(json.dumps({
                    "request_id": "req_" + "f" * 24, "observation": "HOST_RESULT_NOT_RETURNED",
                    "next_action": "INSPECT_HOST_DISPATCH_AND_REPLAN", "result_verified": False,
                }))
                return subprocess.CompletedProcess(cmd, 0, stdout="")
            return self.fake_run(cmd, **kwargs)
        with self.assertRaisesRegex(ValueError, "REQUEST_MISMATCH"):
            restore("G-ACE-inc/server-core", 123, RID, run=wrong_run)

    def test_repository_invalid(self):
        with self.assertRaisesRegex(ValueError, "RUN_ID_OR_REPOSITORY_INVALID"):
            restore("../other", 12, RID, run=self.fake_run)

    def test_expired_artifact_denied(self):
        def expired(cmd, **kwargs):
            if cmd[1] == "api" and "/artifacts?" in cmd[2]:
                return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"artifacts": [{
                    "id": 19, "name": "chat-host-observation-" + SHA, "expired": True
                }]}))
            return self.fake_run(cmd, **kwargs)
        with self.assertRaisesRegex(ValueError, "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"):
            restore("G-ACE-inc/server-core", 123, RID, run=expired)


if __name__ == "__main__":
    unittest.main()
