import unittest
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts import chat_cu_continuation as continuation
from scripts.chat_cu_continuation import resume, assess_diagnostic_context, discover_common_host_run, verified_output_evidence
from scripts.servercore_host_output_artifact_assemble import assemble

BASE = {
    "schema": "gace.chat.cu.handoff.v1",
    "cu_issue_url": "https://github.com/G-ACE-inc/server-core/issues/40",
    "repository": "G-ACE-inc/server-core", "run_id": 123, "request_id": "req_" + "a" * 24,
    "source_sha": "b" * 40, "next_action": "RECOVER_HOST_LEDGER_PAYLOAD",
    "next_tool_target": "https://github.com/G-ACE-inc/server-core/actions/runs/123",
    "result_verified": True, "output_complete": False,
}


class ContinuationTests(unittest.TestCase):
    def test_verified_large_unicode_host_output_enables_next_acceptance_step(self):
        stdout = "日本語Ω🙂\n" * 22000
        stderr = "stderr 日本語\n" * 7500
        rid = BASE["request_id"]
        def pages(name, data):
            sha = hashlib.sha256(data.encode("utf-8")).hexdigest()
            for offset in range(0, max(len(data), 1), 8192):
                part = data[offset:offset + 8192]
                yield {"request_id": rid, "stream": name, "offset": offset,
                       "next_offset": offset + len(part), "total_chars": len(data),
                       "complete": offset + len(part) == len(data),
                       "sha256": sha, "data": part}
        with tempfile.TemporaryDirectory() as d:
            target = Path(d, "artifact")
            manifest = assemble([*pages("stdout", stdout), *pages("stderr", stderr)], target)
            cp = {**BASE, "observation": "HOST_OPERATION_PASSED", "exit_code": 0, "stream_metadata": {
                name: {"sha256": manifest["streams"][name + ".txt"]["sha256"],
                       "chars": len(data), "bytes": len(data.encode("utf-8"))}
                for name, data in (("stdout", stdout), ("stderr", stderr))}}
            api = lambda path: {"head_sha": BASE["source_sha"], "status": "completed",
                                "conclusion": "success"}
            self.assertEqual(resume(cp, api=api)["next_action"], "RECOVER_HOST_LEDGER_PAYLOAD")
            evidence = verified_output_evidence(cp, target / "output.zip")
            self.assertTrue(evidence["output_complete"])
            self.assertEqual(evidence["streams"]["stdout"]["bytes"], len(stdout.encode("utf-8")))
            self.assertEqual(resume(cp, api=api, host_output_zip=target / "output.zip")["next_action"],
                             "VERIFY_CU_ACCEPTANCE")
            with self.assertRaises(TypeError):
                resume(cp, api=api, output_verified=True)  # old bypass parameter removed
            with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_MANIFEST_MISMATCH"):
                resume({**cp, "stream_metadata": {**cp["stream_metadata"],
                         "stdout": {"sha256": "f" * 64, "chars": len(stdout)}}},
                       api=api, host_output_zip=target / "output.zip")
            with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_RUN_NOT_SUCCESS"):
                resume(cp, api=lambda p: {"head_sha": BASE["source_sha"],
                       "status": "completed", "conclusion": "failure"},
                       host_output_zip=target / "output.zip")
            self.assertEqual(cp["output_complete"], False)
            with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_MANIFEST_MISMATCH"):
                verified_output_evidence(
                    {**cp, "stream_metadata": {**cp["stream_metadata"],
                     "stdout": {"sha256": "0"*64, "chars": len(stdout)}}},
                    target / "output.zip")
            with self.assertRaisesRegex(ValueError, "OUTPUT_VERIFICATION_STATE_INVALID"):
                verified_output_evidence({**cp, "result_verified": False}, target / "output.zip")

    def test_failed_ledger_pointer_must_not_promote_even_with_matching_zip(self):
        cp = {**BASE, "observation": "HOST_LEDGER_RECOVERY_REQUIRED",
              "exit_code": 1, "stream_metadata": {
                 "stdout": {"sha256": "0" * 64, "chars": 0},
                 "stderr": {"sha256": "0" * 64, "chars": 0}}}
        with self.assertRaisesRegex(ValueError, "OUTPUT_VERIFICATION_STATE_INVALID"):
            verified_output_evidence(cp, Path("irrelevant.zip"))

    def test_forged_cached_complete_flag_does_not_skip_actual_zip_verification(self):
        cp = {**BASE, "output_complete": True,
              "next_action": "RECHECK_ACCEPTANCE_AND_EXECUTE_NEXT_TOOL"}
        result = resume(cp, api=lambda path: {"head_sha": BASE["source_sha"],
                      "status": "completed", "conclusion": "success"})
        self.assertEqual(result["next_action"], "RECOVER_HOST_LEDGER_PAYLOAD")

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
                 "path": ".github/workflows/chatgpt-live-api-verify.yml@main",
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
        with self.assertRaisesRegex(ValueError, "GITHUB_LIST_INCOMPLETE"):
            discover_common_host_run("G-ACE-inc/server-core", "b" * 40,
                api=lambda path: {"total_count": 101, "workflow_runs": []})

    def test_complete_paginated_run_discovery(self):
        calls = []
        def api(path):
            calls.append(path)
            runs = [{"id": i, "head_sha": "b" * 40, "event": "push",
                     "path": ".github/workflows/other.yml"} for i in range(1, 101)]
            if "&page=2" in path:
                runs = [{"id": 101, "head_sha": "b" * 40, "event": "push",
                         "path": ".github/workflows/chatgpt-live-api-verify.yml"}]
            return {"total_count": 101, "workflow_runs": runs}
        self.assertEqual(discover_common_host_run("G-ACE-inc/server-core", "b" * 40, api=api)["run_id"], 101)
        self.assertEqual(len(calls), 2)

    def test_discovered_sha_must_match_restored_sha_before_resume(self):
        argv = ["continuation", "--repository", BASE["repository"],
                "--discover-head-sha", BASE["source_sha"],
                "--request-id", BASE["request_id"], "--cu-issue-url", BASE["cu_issue_url"]]
        with patch("sys.argv", argv), patch.object(continuation, "discover_common_host_run", return_value={
                "run_id": 123, "source_sha": BASE["source_sha"]}), patch.object(
                continuation, "restore", return_value={"source_sha": "c" * 40}), patch.object(
                continuation, "resume") as resume_mock:
            with self.assertRaisesRegex(ValueError, "DISCOVERY_RESTORE_SHA_MISMATCH"):
                continuation.main()
            resume_mock.assert_not_called()

    def test_paginated_ambiguity_is_rejected(self):
        def api(path):
            return {"total_count": 2, "workflow_runs": [{
                "id": 2 if "&page=2" in path else 1, "head_sha": "b" * 40,
                "event": "push", "path": ".github/workflows/chatgpt-live-api-verify.yml"}]}
        with self.assertRaisesRegex(ValueError, "MULTIPLE_COMMON_HOST_RUNS"):
            discover_common_host_run("G-ACE-inc/server-core", "b" * 40, api=api)

    def test_incomplete_unstable_or_duplicate_pages_rejected(self):
        first = {"total_count": 2, "workflow_runs": [{"id": 1}]}
        for second, error in [
                ({"total_count": 2, "workflow_runs": []}, "GITHUB_LIST_INCOMPLETE"),
                ({"total_count": 3, "workflow_runs": [{"id": 2}]}, "GITHUB_LIST_CHANGED"),
                (first, "GITHUB_LIST_ID_INVALID_OR_DUPLICATE")]:
            with self.subTest(second=second), self.assertRaisesRegex(ValueError, error):
                discover_common_host_run("G-ACE-inc/server-core", "b" * 40,
                    api=lambda path: second if "&page=2" in path else first)

    def test_repository_dot_segments_rejected_without_api(self):
        for repository in ("../other", "owner/..", "./repo", "owner/."):
            with self.subTest(repository=repository), self.assertRaisesRegex(ValueError, "DISCOVERY_REPOSITORY_INVALID"):
                discover_common_host_run(repository, "b" * 40, api=lambda path: self.fail("MUST_NOT_CALL_API"))

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

    def test_host_exit_failure_preserves_correlated_non_sha_diagnosis(self):
        checkpoint = {**BASE, "observation": "HOST_OPERATION_FAILED",
                      "exit_code": 42, "result_verified": True}
        calls = []
        def api(path):
            calls.append(path)
            if path.endswith("/jobs?per_page=100"):
                return {"total_count": 1, "jobs": [{"id": 400, "steps": [
                    {"name": "Bounded Host result return (request id correlated)",
                     "conclusion": "failure"}]}]}
            return {"head_sha": BASE["source_sha"], "status": "completed",
                    "conclusion": "failure"}
        result = resume(checkpoint, api=api)
        self.assertEqual(result["observation"], "CORRELATED_HOST_OPERATION_FAILED")
        self.assertEqual(result["next_action"], "INSPECT_CORRELATED_HOST_FAILURE_AND_REPLAN")
        self.assertEqual(len(calls), 2)

    def test_real_context_mismatch_rechecks_fresh_run_and_targets_pr_replan(self):
        checkpoint = {**BASE, "observation": "HOST_SOURCE_CONTEXT_STALE",
                      "exit_code": 74, "result_verified": True,
                      "diagnostic_hint": "CHAT_SOURCE_SHA_MISMATCH"}
        calls = []
        def api(path):
            calls.append(path)
            if "/jobs?" in path:
                return {"total_count": 1, "jobs": [{"steps": [
                    {"name": "Bounded Host result return (request id correlated)",
                     "conclusion": "failure"}]}]}
            return {"head_sha": BASE["source_sha"], "status": "completed",
                    "conclusion": "failure"}
        result = resume(checkpoint, api=api)
        self.assertEqual(result["observation"], "CORRELATED_SOURCE_CONTEXT_STALE")
        self.assertEqual(result["next_action"], "REFRESH_TARGET_PR_HEAD_AND_REPLAN_EXISTING_WORKTREE")
        self.assertEqual(len(calls), 2)
        # A generic unrelated Actions failure cannot be a source-context root cause.
        result2 = resume(checkpoint, api=lambda p: (
            {"total_count": 1, "jobs": [{"steps": [
                {"name": "Unrelated CI test", "conclusion": "failure"}]}]}
            if "/jobs?" in p else {"head_sha": BASE["source_sha"], "status": "completed",
                                     "conclusion": "failure"}))
        self.assertEqual(result2["observation"], "RUN_FAILED_OR_INCOMPLETE")


    def test_checkpoint_mismatched_source_hint_and_exit_never_replans_pr(self):
        def api(path):
            if "/jobs?" in path:
                return {"total_count": 1, "jobs": [{"steps": [
                    {"name": "Bounded Host result return (request id correlated)",
                     "conclusion": "failure"}]}]}
            return {"head_sha": BASE["source_sha"], "status": "completed",
                    "conclusion": "failure"}
        cases = [
            ("HOST_SOURCE_CONTEXT_STALE", 70, "CHAT_SOURCE_WORKDIR_MISSING"),
            ("HOST_SOURCE_CONTEXT_STALE", 74, "CHAT_SOURCE_WORKDIR_MISSING"),
            ("HOST_SOURCE_CONTEXT_INVALID", 74, "CHAT_SOURCE_SHA_MISMATCH"),
            ("HOST_SOURCE_CONTEXT_INVALID", 76, "CHAT_SOURCE_SHA_MISMATCH"),
        ]
        for observation, exit_code, hint in cases:
            with self.subTest(observation=observation, exit_code=exit_code):
                cp = {**BASE, "observation": observation, "exit_code": exit_code,
                      "diagnostic_hint": hint}
                result = resume(cp, api=api)
                self.assertEqual(result["observation"], "RUN_FAILED_OR_INCOMPLETE")
                self.assertEqual(result["next_action"], "READ_RUN_FAILURE_LOGS")
        valid = {**BASE, "observation": "HOST_SOURCE_CONTEXT_INVALID",
                 "exit_code": 76, "diagnostic_hint": "CHAT_SOURCE_DIRTY_WORKTREE"}
        actual = resume(valid, api=api)
        self.assertEqual(actual["observation"], "CORRELATED_SOURCE_CONTEXT_INVALID")
        self.assertEqual(actual["next_action"], "CHECK_TARGET_WORKTREE_AND_REQUIRED_FILES")

    def test_correlated_absent_host_receipt_points_at_existing_delivery(self):
        checkpoint = {**BASE, "observation": "HOST_RESULT_NOT_RETURNED",
                      "result_verified": False, "exit_code": None}
        def api(path):
            if "/jobs?" in path:
                return {"total_count": 1, "jobs": [{"id": 99, "steps": [
                    {"name": "Bounded Host result return (request id correlated)",
                     "conclusion": "failure"}]}]}
            return {"head_sha": BASE["source_sha"], "status": "completed",
                    "conclusion": "failure"}
        result = resume(checkpoint, api=api)
        self.assertEqual(result["observation"], "CORRELATED_HOST_RESULT_MISSING")
        self.assertEqual(result["next_action"], "TRACE_ORIGINAL_REQUEST_AND_RESULT_SINK")

    def test_other_failing_step_must_not_be_called_host_failure(self):
        checkpoint = {**BASE, "observation": "HOST_OPERATION_FAILED",
                      "exit_code": 42, "result_verified": True}
        def api(path):
            if "/jobs?" in path:
                return {"total_count": 1, "jobs": [{"id": 99, "steps": [
                    {"name": "Unrelated PR CI", "conclusion": "failure"}]}]}
            return {"head_sha": BASE["source_sha"], "status": "completed",
                    "conclusion": "failure"}
        self.assertEqual(resume(checkpoint, api=api)["observation"],
                         "RUN_FAILED_OR_INCOMPLETE")

    def test_incomplete_failed_job_collection_does_not_claim_correlated_cause(self):
        checkpoint = {**BASE, "observation": "HOST_OPERATION_FAILED",
                      "exit_code": 42, "result_verified": True}
        def api(path):
            if "/jobs?" in path:
                return {"total_count": 2, "jobs": [{"id": 1, "steps": []}]}
            return {"head_sha": BASE["source_sha"], "status": "completed",
                    "conclusion": "failure"}
        with self.assertRaisesRegex(ValueError, "FAILED_RUN_JOBS_INCOMPLETE"):
            resume(checkpoint, api=api)

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
