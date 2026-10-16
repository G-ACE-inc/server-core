import io
import zipfile
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.chat_host_observation_gh_restore import restore, continuation_checkpoint

RID = "req_" + "a" * 24
SHA = "b" * 40


class RestoreTests(unittest.TestCase):
    def receipt(self):
        return {"request_id": RID, "observation": "HOST_RESULT_NOT_RETURNED",
                "next_action": "INSPECT_HOST_DISPATCH_AND_REPLAN", "result_verified": False}

    def artifact(self, artifact_id=19):
        return {"id": artifact_id, "name": "chat-host-observation-" + SHA,
                "expired": False, "size_in_bytes": 500,
                "workflow_run": {"id": 123, "head_sha": SHA}}

    def archive(self, cmd, receipt, **kwargs):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("gace-chat-host-observation.json", json.dumps(receipt))
        if "stdout" in kwargs:
            self.assertNotIn("capture_output", kwargs)
            self.assertTrue(callable(kwargs.get("preexec_fn")))
            kwargs["stdout"].write(data.getvalue())
            return subprocess.CompletedProcess(cmd, 0)
        return subprocess.CompletedProcess(cmd, 0, stdout=data.getvalue())

    def fake_run(self, cmd, **kwargs):
        # Support the previous CLI transport too, so regressions can be replayed
        # against the baseline without changing the authenticated receipt fixture.
        if cmd[1] == "run":
            Path(cmd[-1], "gace-chat-host-observation.json").write_text(
                json.dumps(self.receipt()), encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, stdout="")
        if cmd[2].endswith("/zip"):
            self.assertEqual(cmd[2], "repos/G-ACE-inc/server-core/actions/artifacts/19/zip")
            return self.archive(cmd, self.receipt(), **kwargs)
        if "/artifacts?" in cmd[2]:
            payload = {"total_count": 1, "artifacts": [self.artifact()]}
        else:
            payload = {"id": 123, "head_sha": SHA,
                       "path": ".github/workflows/chatgpt-live-api-verify.yml",
                       "repository": {"full_name": "G-ACE-inc/server-core"}}
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload))

    def test_restores_existing_run_without_issue_scans(self):
        result = restore("G-ACE-inc/server-core", 123, RID, run=self.fake_run)
        self.assertEqual(result["artifact_id"], 19)
        self.assertEqual(result["request_id"], RID)
        self.assertFalse(result["result_verified"])
        self.assertEqual(result["source_sha"], SHA)


    def test_ref_qualified_workflow_path_is_accepted(self):
        def ref_run(cmd, **kwargs):
            response = self.fake_run(cmd, **kwargs)
            if cmd[1] == "api" and cmd[2].endswith("/runs/123"):
                payload = json.loads(response.stdout)
                payload["path"] += "@refs/heads/main"
                return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload))
            return response
        self.assertEqual(restore("G-ACE-inc/server-core", 123, RID, run=ref_run)["artifact_id"], 19)

    def test_request_mismatch_denied(self):
        def wrong_run(cmd, **kwargs):
            if cmd[2].endswith("/zip"):
                return self.archive(cmd, {**self.receipt(), "request_id": "req_" + "f" * 24}, **kwargs)
            return self.fake_run(cmd, **kwargs)
        with self.assertRaisesRegex(ValueError, "REQUEST_MISMATCH"):
            restore("G-ACE-inc/server-core", 123, RID, run=wrong_run)

    def test_repository_invalid(self):
        with self.assertRaisesRegex(ValueError, "RUN_ID_OR_REPOSITORY_INVALID"):
            restore("../other", 12, RID, run=self.fake_run)

    def test_expired_artifact_denied(self):
        def expired(cmd, **kwargs):
            if cmd[1] == "api" and "/artifacts?" in cmd[2]:
                return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"total_count": 1, "artifacts": [{
                    "id": 19, "name": "chat-host-observation-" + SHA,
                    "size_in_bytes": 500, "expired": True
                }]}))
            return self.fake_run(cmd, **kwargs)
        with self.assertRaisesRegex(ValueError, "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"):
            restore("G-ACE-inc/server-core", 123, RID, run=expired)

    def test_zip_size_preflight_refuses_missing_oversized_or_invalid_metadata(self):
        from scripts.chat_host_observation_gh_restore import MAX_OBSERVATION_ZIP_BYTES
        for size in (None, 0, True, -1, MAX_OBSERVATION_ZIP_BYTES + 1):
            calls = []
            def fake(cmd, **kwargs):
                calls.append(cmd[2])
                if "/artifacts?" in cmd[2]:
                    bad = self.artifact()
                    if size is None:
                        bad.pop("size_in_bytes")
                    else:
                        bad["size_in_bytes"] = size
                    return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({
                        "total_count": 1, "artifacts": [bad]}))
                return self.fake_run(cmd, **kwargs)
            with self.subTest(size=size), self.assertRaisesRegex(
                    ValueError, "ARTIFACT_ZIP_SIZE_INVALID_OR_TOO_LARGE"):
                restore("G-ACE-inc/server-core", 123, RID, run=fake)
            self.assertFalse(any(path.endswith("/zip") for path in calls))

    def test_exact_artifact_zip_is_streamed_to_file(self):
        seen = []
        def fake(cmd, **kwargs):
            if cmd[2].endswith("/zip"):
                seen.append((kwargs.get("stdout"), kwargs.get("capture_output"),
                             kwargs.get("preexec_fn")))
            return self.fake_run(cmd, **kwargs)
        result = restore("G-ACE-inc/server-core", 123, RID, run=fake)
        self.assertEqual(result["artifact_id"], 19)
        self.assertEqual(len(seen), 1)
        self.assertTrue(callable(seen[0][2]))
        self.assertIsNotNone(seen[0][0])
        self.assertIsNone(seen[0][1])

    def test_missing_artifact_denied(self):
        def missing(cmd, **kwargs):
            if "/artifacts?" in cmd[2]:
                return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({
                    "total_count": 0, "artifacts": []}))
            return self.fake_run(cmd, **kwargs)
        with self.assertRaisesRegex(ValueError, "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"):
            restore("G-ACE-inc/server-core", 123, RID, run=missing)

    def test_artifact_on_later_page_and_duplicate_on_later_page(self):
        for duplicate in (False, True):
            calls = []
            def pages(cmd, **kwargs):
                calls.append(cmd[2])
                if "/artifacts?" in cmd[2]:
                    if "&page=2" in cmd[2]:
                        artifact = self.artifact()
                    else:
                        artifact = self.artifact(20)
                        if not duplicate:
                            artifact["name"] = "unrelated"
                    return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({
                        "total_count": 2, "artifacts": [artifact]}))
                return self.fake_run(cmd, **kwargs)
            with self.subTest(duplicate=duplicate):
                if duplicate:
                    with self.assertRaisesRegex(ValueError, "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"):
                        restore("G-ACE-inc/server-core", 123, RID, run=pages)
                    self.assertFalse(any(path.endswith("/zip") for path in calls))
                else:
                    self.assertEqual(restore("G-ACE-inc/server-core", 123, RID, run=pages)["artifact_id"], 19)
                self.assertTrue(any("&page=2" in path for path in calls))

    def test_wrong_run_or_workflow_is_rejected(self):
        for patch in ({"id": 124}, {"path": ".github/workflows/other.yml"},
                      {"repository": {"full_name": "other/repo"}}):
            def wrong(cmd, **kwargs):
                payload = json.loads(self.fake_run(cmd, **kwargs).stdout)
                payload.update(patch)
                return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload))
            with self.subTest(patch=patch), self.assertRaisesRegex(ValueError, "RUN_PROVENANCE_MISMATCH"):
                restore("G-ACE-inc/server-core", 123, RID, run=wrong)

    def test_wrong_artifact_run_or_sha_rejected(self):
        for provenance in ({"id": 124, "head_sha": SHA}, {"id": 123, "head_sha": "c" * 40}):
            def wrong(cmd, **kwargs):
                response = self.fake_run(cmd, **kwargs)
                if "/artifacts?" in cmd[2]:
                    payload = json.loads(response.stdout)
                    payload["artifacts"][0]["workflow_run"] = provenance
                    return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload))
                return response
            with self.subTest(provenance=provenance), self.assertRaisesRegex(ValueError, "ARTIFACT_RUN_PROVENANCE_MISMATCH"):
                restore("G-ACE-inc/server-core", 123, RID, run=wrong)

    def test_checkpoint_reuses_existing_run_without_new_dispatch(self):
        result = restore("G-ACE-inc/server-core", 123, RID, run=self.fake_run)
        checkpoint = continuation_checkpoint(result, "https://github.com/G-ACE-inc/server-core/issues/40")
        self.assertEqual(checkpoint["phase"], "OBSERVE")
        self.assertEqual(checkpoint["next_action"], "RECHECK_EXISTING_RUN_AND_HOST_RESULT")
        self.assertEqual(checkpoint["next_tool_target"], "https://github.com/G-ACE-inc/server-core/actions/runs/123")
        self.assertEqual(checkpoint["cu_issue_url"], "https://github.com/G-ACE-inc/server-core/issues/40")

    def test_checkpoint_accepts_canonical_issue_url(self):
        result = restore("G-ACE-inc/server-core", 123, RID, run=self.fake_run)
        checkpoint = continuation_checkpoint(result, "https://github.com/G-ACE-inc/server-core/issues/40")
        self.assertEqual(checkpoint["cu_issue_url"], "https://github.com/G-ACE-inc/server-core/issues/40")

    def test_checkpoint_requires_real_issue_url(self):
        result = restore("G-ACE-inc/server-core", 123, RID, run=self.fake_run)
        with self.assertRaisesRegex(ValueError, "CU_ISSUE_URL_INVALID"):
            continuation_checkpoint(result, "https://invalid.example/issue")

    def test_metadata_only_success_chooses_ledger_not_acceptance(self):
        result = restore("G-ACE-inc/server-core", 123, RID, run=self.fake_run)
        result["result_verified"] = True
        result["observation"] = "HOST_OPERATION_PASSED"
        checkpoint = continuation_checkpoint(result, "https://github.com/G-ACE-inc/server-core/issues/40")
        self.assertEqual(checkpoint["next_action"], "RECOVER_HOST_LEDGER_PAYLOAD")
        self.assertEqual(checkpoint["phase"], "OBSERVE")


if __name__ == "__main__":
    unittest.main()
