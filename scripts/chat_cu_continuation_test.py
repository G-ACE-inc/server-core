import unittest
from scripts.chat_cu_continuation import resume, assess_diagnostic_context, discover_common_host_run

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



    def test_five_runs_including_push_prevent_false_missing_run(self):
        sha = "b" * 40
        calls = []
        def api(path):
            calls.append(path)
            return {"total_count": 5, "workflow_runs": [
                {"id": 42, "head_sha": sha, "event": "push",
                 "path": ".github/workflows/chatgpt-live-api-verify.yml",
                 "status": "completed", "conclusion": "failure"},
                *[{"id": i, "head_sha": sha, "event": "push",
                   "path": ".github/workflows/other.yml"} for i in range(43, 47)]]}
        result = discover_common_host_run("G-ACE-inc/server-core", sha, api=api)
        self.assertEqual(result["run_id"], 42)
        self.assertTrue(result["actions_trigger_verified"])
        self.assertEqual(result["other_run_count"], 4)
        self.assertEqual(calls, [f"repos/G-ACE-inc/server-core/actions/runs?head_sha={sha}&per_page=100"])

    def test_empty_complete_run_list_not_claimed_to_be_trigger_failure(self):
        result = discover_common_host_run("G-ACE-inc/server-core", "b" * 40,
                 api=lambda path: {"total_count": 0, "workflow_runs": []})
        self.assertEqual(result["observation"], "NO_MATCHING_COMMON_HOST_RUN_IN_COMPLETE_LIST")
        self.assertFalse(result["actions_trigger_verified"])

    def test_incomplete_run_page_does_not_invent_absence(self):
        with self.assertRaisesRegex(ValueError, "RUN_LIST_PAGINATION_REQUIRED"):
            discover_common_host_run("G-ACE-inc/server-core", "b" * 40,
                api=lambda path: {"total_count": 101, "workflow_runs": []})

    def test_verified_host_mismatch_triggers_second_tool_read_and_replan(self):
        checkpoint = {**BASE, "observation": "HOST_SOURCE_SHA_MISMATCH",
            "expected_sha": "a" * 40, "host_sha": "c" * 40,
            "exit_code": 1, "result_verified": True}
        calls = []
        def api(path):
            calls.append(path)
            if path.endswith("/jobs?per_page=100"):
                return {"jobs": [{"steps": [
                    {"name": "Bounded Host result return (request id correlated)", "conclusion": "failure"}]}]}
            return {"head_sha": "b" * 40, "status": "completed", "conclusion": "failure"}
        result = resume(checkpoint, api=api)
        self.assertEqual(result["observation"], "CORRELATED_HOST_SHA_MISMATCH")
        self.assertEqual(result["next_action"], "RECHECK_REGISTERED_TARGET_REPO_SHA_AND_REPLAN_HOST_REQUEST")
        self.assertEqual(result["observed_host_sha"], "c" * 40)
        self.assertEqual(len(calls), 2)
        self.assertIn("jobs?per_page=100", calls[1])

    def test_unverified_host_mismatch_cannot_override_actions_failure(self):
        checkpoint = {**BASE, "observation": "HOST_SOURCE_SHA_MISMATCH",
            "expected_sha": "a" * 40, "host_sha": "c" * 40,
            "exit_code": 1, "result_verified": False}
        result = resume(checkpoint, api=lambda path: {
            "head_sha": "b" * 40, "status": "completed", "conclusion": "failure"})
        self.assertEqual(result["next_action"], "READ_RUN_FAILURE_LOGS")

class DiagnosticReasoningTests(unittest.TestCase):
    def test_repeated_hypothesis_is_not_proven_cause(self):
        context = {"symptom": "Actions run missing", "hypotheses": [
            {"id": "token_recursion", "previous_attempt_failed": True,
             "evidence_url": "https://github.com/G-ACE-inc/server-core/issues/40"}]}
        result = assess_diagnostic_context(context, {"next_action": "READ_RUN_FAILURE_LOGS"})
        self.assertEqual(result["hypotheses"][0]["status"], "REVIEW_BEFORE_REPEAT")
        self.assertFalse(result["causal_claim_verified"])
        self.assertEqual(result["observed_action"], "READ_RUN_FAILURE_LOGS")

    def test_unsubstantiated_theory_stays_hypothesis(self):
        result = assess_diagnostic_context(
            {"symptom": "missing", "hypotheses": [{"id": "suspected_token"}]}, {})
        self.assertEqual(result["hypotheses"][0]["status"], "HYPOTHESIS_ONLY")

    def test_invalid_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "DIAGNOSTIC_EVIDENCE_URL_INVALID"):
            assess_diagnostic_context({"symptom": "missing", "hypotheses": [
                {"id": "guess", "evidence_url": "https://example.com/fake"}]}, {})


if __name__ == "__main__":
    unittest.main()
