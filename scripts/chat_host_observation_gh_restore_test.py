import io
import zipfile
import json
import subprocess
import hashlib
import stat
import tempfile
import unittest
from pathlib import Path

from scripts.chat_host_observation_gh_restore import restore, continuation_checkpoint
from scripts import chat_host_observation_gh_restore as reader
from unittest.mock import patch

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

    def test_known_failures_recheck_original_run_before_payload_recovery(self):
        for observation in (
            "HOST_SOURCE_SHA_MISMATCH", "HOST_OPERATION_FAILED",
            "HOST_OPERATION_RETRYABLE", "HOST_SOURCE_CONTEXT_STALE",
            "HOST_SOURCE_CONTEXT_INVALID", "CORRELATION_FAILED",
            "HOST_RESULT_UNVERIFIED",
        ):
            for complete in (False, True):
                with self.subTest(observation=observation, complete=complete):
                    result = {"repository": "G-ACE-inc/server-core", "run_id": 123,
                              "artifact_id": 19, "source_sha": SHA, "request_id": RID,
                              "result_verified": True, "output_complete": complete,
                              "observation": observation, "result_url": "existing"}
                    checkpoint = continuation_checkpoint(
                        result, "https://github.com/G-ACE-inc/server-core/issues/40")
                    self.assertEqual(checkpoint["phase"], "OBSERVE")
                    self.assertEqual(checkpoint["next_action"], "RECHECK_EXISTING_RUN_AND_HOST_RESULT")


class PrivateOutputTests(unittest.TestCase):
    def setUp(self):
        self.streams = {"stdout": "private 日本語🙂\n" * 18000, "stderr": "error\n"}
        self.expected = {name: {"bytes": len(text.encode()), "chars": len(text),
                               "sha256": hashlib.sha256(text.encode()).hexdigest()}
                         for name, text in self.streams.items()}
        manifest = {"request_id": RID, "streams": {
            name + ".txt": {k: value[k] for k in ("bytes", "sha256")}
            for name, value in self.expected.items()}}
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as z:
            for name, text in self.streams.items():
                z.writestr(name + ".txt", text)
            z.writestr("manifest.json", json.dumps(manifest))
        self.payload = data.getvalue()
        self.wrapper = self.wrap([("output.zip", self.payload)])
        self.recipient = {"private": True, "full_name": reader.PRIVATE_OUTPUT_REPOSITORY}
        self.info = {"id": 123, "repository": {"full_name": reader.PRIVATE_OUTPUT_REPOSITORY},
                     "head_sha": SHA, "path": ".github/workflows/ci.yml@main", "event": "release",
                     "status": "completed", "conclusion": "success"}
        self.item = {"id": 19, "name": "gace-host-output-" + RID, "expired": False,
                     "size_in_bytes": len(self.wrapper),
                     "workflow_run": {"id": 123, "head_sha": SHA}}
        self.items = [self.item]
        self.downloads = []
        self.calls = []

    def wrap(self, members):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in members:
                z.writestr(name, data)
        return buffer.getvalue()

    def fake_run(self, cmd, **kwargs):
        path = cmd[2]
        self.calls.append(path)
        if path.endswith("/zip"):
            self.assertEqual(path, f"repos/{reader.PRIVATE_OUTPUT_REPOSITORY}/actions/artifacts/19/zip")
            self.assertNotIn("capture_output", kwargs)
            self.assertTrue(callable(kwargs["preexec_fn"]))
            self.assertEqual(kwargs["preexec_fn"].args, (reader.MAX_VERIFIED_ARCHIVE_BYTES,))
            self.downloads.append(Path(kwargs["stdout"].name))
            kwargs["stdout"].write(self.wrapper)
            return subprocess.CompletedProcess(cmd, 0)
        if "/artifacts?" in path:
            value = {"total_count": len(self.items), "artifacts": self.items}
        elif "/runs/" in path:
            value = self.info
        else:
            value = self.recipient
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(value))

    def recover(self, expected=None):
        return reader.private_host_output(123, RID, expected or self.expected, run=self.fake_run)

    def assert_no_files(self):
        self.assertTrue(all(not path.parent.exists() for path in self.downloads))

    def test_private_unicode_payload_verified_and_removed_after_consumption(self):
        with self.recover() as (path, proof):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(proof["streams"], self.expected)
            self.assertEqual(proof["artifact_id"], 19)
            self.assertNotIn("private 日本語", json.dumps(proof, ensure_ascii=False))
            self.assertTrue(path.exists())
        self.assertFalse(path.exists())
        self.assert_no_files()

    def test_consumer_exception_also_removes_plaintext(self):
        with self.assertRaisesRegex(RuntimeError, "CONSUMER_FAILED"):
            with self.recover():
                raise RuntimeError("CONSUMER_FAILED")
        self.assert_no_files()

    def test_public_or_wrong_recipient_never_downloaded(self):
        for recipient in ({**self.recipient, "private": False},
                          {**self.recipient, "full_name": "other/repo"}):
            self.recipient = recipient
            with self.subTest(recipient=recipient), self.assertRaisesRegex(
                    ValueError, "PRIVATE_REPOSITORY_NOT_VERIFIED"), self.recover():
                self.fail("must not yield")
        self.assertEqual(self.downloads, [])

    def test_wrong_or_incomplete_private_run_never_downloaded(self):
        original = dict(self.info)
        for change in ({"id": 124}, {"event": "push"}, {"head_sha": "invalid"},
                       {"status": "in_progress"}, {"conclusion": "failure"},
                       {"repository": {"full_name": "other/repo"}}, {"path": "other.yml"}):
            self.info = {**original, **change}
            with self.subTest(change=change), self.assertRaisesRegex(
                    ValueError, "PRIVATE_RUN_PROVENANCE_MISMATCH"), self.recover():
                self.fail("must not yield")
        self.assertEqual(self.downloads, [])

    def test_missing_expired_ambiguous_or_wrong_provenance_artifact(self):
        for items, error in (([], "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"),
                ([{**self.item, "expired": True}], "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"),
                ([self.item, {**self.item, "id": 20}], "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"),
                ([{**self.item, "workflow_run": {"id": 124, "head_sha": SHA}}], "ARTIFACT_RUN_PROVENANCE_MISMATCH"),
                ([{**self.item, "size_in_bytes": True}], "ARTIFACT_ZIP_SIZE_INVALID_OR_TOO_LARGE")):
            self.items = items
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error), self.recover():
                self.fail("must not yield")
        self.assertEqual(self.downloads, [])

    def test_independent_digest_mismatch_refused_and_download_cleaned(self):
        bad = {**self.expected, "stdout": {**self.expected["stdout"], "sha256": "f" * 64}}
        with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_MANIFEST_MISMATCH"), self.recover(bad):
            self.fail("must not yield")
        self.assert_no_files()

    def test_wrapper_does_not_extract_arbitrary_members(self):
        for members in ([("../escape", self.payload)], [("output.zip", self.payload), ("extra", b"x")]):
            self.wrapper = self.wrap(members)
            with self.assertRaisesRegex(ValueError, "PRIVATE_ARTIFACT_MEMBERS_INVALID"), self.recover():
                self.fail("must not yield")
            self.assert_no_files()

    def test_compressed_oversized_wrapper_refused_before_unwrapping(self):
        self.wrapper = self.wrap([("output.zip", b"x" * 100000)])
        self.item["size_in_bytes"] = len(self.wrapper)
        with patch.object(reader, "MAX_VERIFIED_ARCHIVE_BYTES", 1000):
            with self.assertRaisesRegex(ValueError, "PRIVATE_ARTIFACT_PAYLOAD_SIZE_OR_COMPRESSION_INVALID"), self.recover():
                self.fail("must not yield")
        self.assert_no_files()

    def test_actual_download_cap_enforced_even_if_size_metadata_lies(self):
        self.wrapper = b"x" * 2000
        self.item["size_in_bytes"] = 100
        with patch.object(reader, "MAX_VERIFIED_ARCHIVE_BYTES", 1000):
            with self.assertRaisesRegex(ValueError, "ARTIFACT_ZIP_SIZE_EXCEEDED"), self.recover():
                self.fail("must not yield")
        self.assert_no_files()

    def test_invalid_expectations_rejected_before_github_access(self):
        with self.assertRaisesRegex(ValueError, "EXPECTED_HOST_STREAM_METADATA_REQUIRED"):
            with reader.private_host_output(123, RID, None, run=self.fake_run):
                self.fail("must not yield")
        self.assertEqual(self.calls, [])

    def test_original_request_finds_one_artifact_without_run_scan_or_redundant_listing(self):
        with reader.private_host_output(None, RID, self.expected, run=self.fake_run) as (_, proof):
            self.assertEqual(proof["run_id"], 123)
        self.assertEqual(self.calls, [
            f"repos/{reader.PRIVATE_OUTPUT_REPOSITORY}",
            f"repos/{reader.PRIVATE_OUTPUT_REPOSITORY}/actions/artifacts?name=gace-host-output-{RID}&per_page=100",
            f"repos/{reader.PRIVATE_OUTPUT_REPOSITORY}/actions/runs/123",
            f"repos/{reader.PRIVATE_OUTPUT_REPOSITORY}/actions/artifacts/19/zip"])
        self.assert_no_files()

    def test_auto_lookup_reads_later_pages_and_rejects_duplicate_candidates(self):
        def paged(cmd, **kwargs):
            if "/artifacts?name=" in cmd[2]:
                item = {**self.item, "id": 20} if "&page=2" in cmd[2] else self.item
                return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({
                    "total_count": 2, "artifacts": [item]}))
            return self.fake_run(cmd, **kwargs)
        with self.assertRaisesRegex(ValueError, "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"):
            with reader.private_host_output(None, RID, self.expected, run=paged):
                self.fail("must not select latest candidate")
        self.assertEqual(self.downloads, [])

    def test_auto_lookup_missing_expired_or_malformed_run_reference_never_downloads(self):
        for items, error in (([], "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"),
                ([{**self.item, "expired": True}], "ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS"),
                ([{**self.item, "workflow_run": {"id": True}}], "ARTIFACT_RUN_PROVENANCE_MISMATCH"),
                ([{**self.item, "workflow_run": {"id": 123, "head_sha": "c" * 40}}],
                 "ARTIFACT_RUN_PROVENANCE_MISMATCH")):
            self.items = items
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                with reader.private_host_output(None, RID, self.expected, run=self.fake_run):
                    self.fail("must not yield")
        self.assertEqual(self.downloads, [])


if __name__ == "__main__":
    unittest.main()
