"""A source-changing Host command must return its saved result on retry."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import servercore_bounded_host_receiver as receiver
import servercore_service_deploy_socket as writer

RID = "req_" + "a" * 24
OLD = "b" * 40
REPO = "G-ACE-inc/server-core"
COMMAND = "printf completed"


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.writer_request = {"schema": writer.HOST_COMMAND_SCHEMA, "id": RID,
                               "repository": REPO, "target_sha": OLD, "command": COMMAND}
        self.saved = {"request_id": RID, "repository": REPO, "source_sha": OLD,
                      "source_preflight": False,
                      **writer.command_ingress_fingerprint(COMMAND),
                      "state": "HOST_COMMAND_PASS", "exit_code": 0,
                      "stdout": "completed", "stderr": ""}

    def test_writer_returns_only_exact_saved_command_without_execution(self):
        directory = self.root / "results"
        writer.write_result(RID, self.saved, directory)
        with patch("subprocess.run") as run:
            result = writer.run_host_command({**self.writer_request, "replay_only": True},
                                             result_dir=directory)
            self.assertEqual(result["state"], "HOST_COMMAND_DUPLICATE")
            run.assert_not_called()
        with self.assertRaisesRegex(writer.AdmissionError, "HOST_COMMAND_REPLAY_CONFLICT"):
            writer.run_host_command({**self.writer_request, "replay_only": True,
                                     "command": "printf changed"}, result_dir=directory)

    def test_replay_only_never_executes_missing_request(self):
        with patch("subprocess.run") as run:
            with self.assertRaisesRegex(writer.AdmissionError, "HOST_COMMAND_REPLAY_MISSING"):
                writer.run_host_command({**self.writer_request, "replay_only": True},
                                        result_dir=self.root / "missing")
            run.assert_not_called()

    def test_incomplete_saved_request_is_retryable_not_a_finished_result(self):
        directory = self.root / "results"
        writer.write_result(RID, {**self.saved, "state": "RUNNING"}, directory)
        with self.assertRaisesRegex(writer.AdmissionError, "HOST_COMMAND_REPLAY_INCOMPLETE"):
            writer.run_host_command({**self.writer_request, "replay_only": True},
                                    result_dir=directory)

    def test_receiver_uses_saved_result_after_dispatcher_head_advances(self):
        request = {"id": RID, "command_id": "host.command", "repository": REPO,
                   "expected_sha": OLD, "repo_sha": OLD, "command": COMMAND}
        reply = {"ok": True, "state": "HOST_COMMAND_DUPLICATE", "result": self.saved}
        with patch.object(receiver.bounded_host, "checked_root", side_effect=lambda p: p), \
             patch.object(receiver.bounded_host, "head_sha",
                          side_effect=receiver.bounded_host.BoundaryError("SOURCE_SHA_MISMATCH")), \
             patch.object(receiver, "deploy_socket_call", return_value=reply) as call:
            result = receiver.dispatch_host_command(request, self.root)
        self.assertEqual(result["source_sha"], OLD)
        self.assertEqual(result["state"], "HOST_COMMAND_PASS")
        self.assertTrue(call.call_args.args[0]["replay_only"])
        changed = dict(reply, result={**self.saved,
                                      "command_sha256": hashlib.sha256(b"changed").hexdigest()})
        with patch.object(receiver.bounded_host, "checked_root", side_effect=lambda p: p), \
             patch.object(receiver.bounded_host, "head_sha",
                          side_effect=receiver.bounded_host.BoundaryError("SOURCE_SHA_MISMATCH")), \
             patch.object(receiver, "deploy_socket_call", return_value=changed):
            with self.assertRaisesRegex(receiver.ReceiverError, "HOST_COMMAND_RESULT_MISMATCH"):
                receiver.dispatch_host_command(request, self.root)


if __name__ == "__main__":
    unittest.main()
