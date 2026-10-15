import unittest
from scripts.chat_cu_continuation import resume

BASE = {
    "schema": "gace.chat.cu.handoff.v1",
    "cu_issue_url": "https://github.com/G-ACE-inc/server-core/issues/40",
    "repository": "G-ACE-inc/server-core", "run_id": 123, "request_id": "req_" + "a" * 24,
    "source_sha": "b" * 40, "next_action": "RECOVER_HOST_LEDGER_PAYLOAD",
    "next_tool_target": "https://github.com/G-ACE-inc/server-core/actions/runs/123",
    "result_verified": True, "output_complete": False,
}


class ContinuationTests(unittest.TestCase):
    def test_actual_readback_selects_next_step(self):
        called = []
        def api(path):
            called.append(path)
            return {"head_sha": "b" * 40, "status": "completed", "conclusion": "success"}
        result = resume(BASE, api=api)
        self.assertEqual(called, ["repos/G-ACE-inc/server-core/actions/runs/123"])
        self.assertEqual(result["next_action"], "RECOVER_HOST_LEDGER_PAYLOAD")

    def test_unverified_result_does_not_complete(self):
        cp = {**BASE, "result_verified": False, "next_action": "RECHECK_EXISTING_RUN_AND_HOST_RESULT"}
        result = resume(cp, api=lambda path: {"head_sha": "b" * 40, "status": "completed", "conclusion": "success"})
        self.assertEqual(result["observation"], "HOST_RESULT_UNVERIFIED")

    def test_stale_sha_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "STALE_OR_WRONG_SOURCE_SHA"):
            resume(BASE, api=lambda path: {"head_sha": "c" * 40, "status": "completed"})

    def test_wrong_run_target_rejected_before_call(self):
        cp = {**BASE, "next_tool_target": "https://github.com/G-ACE-inc/server-core/actions/runs/124"}
        with self.assertRaisesRegex(ValueError, "RUN_TARGET_MISMATCH"):
            resume(cp, api=lambda path: self.fail("MUST_NOT_CALL_API"))

    def test_failed_action_readback_not_false_pass(self):
        result = resume(BASE, api=lambda path: {"head_sha": "b" * 40, "status": "completed", "conclusion": "failure"})
        self.assertEqual(result["next_action"], "READ_RUN_FAILURE_LOGS")


if __name__ == "__main__":
    unittest.main()
