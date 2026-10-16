import base64
import hashlib
import hmac
import http.client
import importlib.util
import json
import secrets
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import servercore_bounded_host_receiver as receiver  # noqa: E402

spec = importlib.util.spec_from_file_location("servercore_result_sink", ROOT / "scripts" / "servercore_result_sink.py")
sink = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sink)

SHA = "a" * 40
RID = "req_" + "0123456789abcdef01234567"


def rec(**kw):
    base = {"schema": sink.RECORD_SCHEMA, "request_id": RID, "command_id": "project.git_head", "state": "PASS",
            "exit_code": 0, "host_sha": SHA, "expected_sha": SHA, "stdout": "{}", "stderr": "", "duration_ms": 5}
    base.update(kw)
    return base


class RedactionTests(unittest.TestCase):
    def test_secrets_redacted_and_bounded(self):
        raw = ("token=abc123 Authorization: Bearer abcdefghijkl ghp_" + "A" * 30 + " github_pat_" + "B" * 30 +
               " HMAC_KEY=zzzz -----BEGIN PRIVATE KEY-----\nMIIE\n-----END PRIVATE KEY----- " + "C" * 60 + " " + SHA)
        text, cut = sink.bound(raw)
        for leaked in ("abc123", "abcdefghijkl", "ghp_" + "A" * 30, "B" * 30, "zzzz", "MIIE", "C" * 60):
            self.assertNotIn(leaked, text)
        self.assertIn(SHA, text)
        self.assertFalse(cut)
        text, cut = sink.bound("line 1\n" * 1000)
        self.assertEqual((len(text), cut), (sink.STREAM_LIMIT, True))

    def test_json_escaped_keyed_values_are_redacted_without_eating_next_line(self):
        text, _ = sink.bound(json.dumps({"content": 'password = "hunter2"\nAPI_KEY: abcdef\nname: ok', "password": "p4ss"}))
        for leaked in ("hunter2", "abcdef", "p4ss"):
            self.assertNotIn(leaked, text)
        self.assertIn("name: ok", text)

    def test_digest_and_control_characters(self):
        digest = "d" * 64
        text, _ = sink.bound("\x1b[31m" + digest + "\x00")
        self.assertEqual(text, digest)


class SinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name) / "r"

    def test_validation_fail_closed(self):
        for bad in (rec(request_id="req_x"), rec(state="MAYBE"), rec(exit_code=1000), rec(host_sha="zz"),
                    rec(command_id="Bad Cmd"), {**rec(), "extra": 1}, rec(schema="x")):
            with self.assertRaises(sink.SinkError):
                sink.accept_record(bad, result_dir=self.dir)

    def test_first_terminal_wins_and_retryable_is_replaced(self):
        self.assertEqual(sink.accept_record(rec(state="RETRYABLE", exit_code=1), result_dir=self.dir)["state"], "RECORDED")
        self.assertEqual(sink.accept_record(rec(), result_dir=self.dir)["recorded_state"], "PASS")
        dup = sink.accept_record(rec(state="FAIL", exit_code=1, stderr="late"), result_dir=self.dir)
        self.assertEqual(dup["state"], "DUPLICATE")
        saved = sink.read_record(RID, self.dir)
        self.assertEqual((saved["state"], saved["stderr"], saved["attempts"]), ("PASS", "", 2))
        self.assertEqual(oct(sink.record_path(RID, self.dir).stat().st_mode & 0o777), "0o600")

    def test_publish_once_with_existing_marker_reuse(self):
        sink.accept_record(rec(stdout="token=secretvalue"), result_dir=self.dir)
        calls = []

        def runner(args, stdin=None, timeout=40):
            calls.append((args, stdin))
            if args[:2] == ["api", "-X"]:
                return json.dumps({"id": 77, "html_url": "https://github.com/x/y/issues/10#issuecomment-77"})
            if "/comments?" in args[-1]:
                return "[]"
            return json.dumps({"comments": 9876})
            return json.dumps({"id": 77, "html_url": "https://github.com/x/y/issues/10#issuecomment-77"})

        found = sink.publish_record(RID, result_dir=self.dir, runner=runner)
        self.assertEqual(found["comment_id"], 77)
        body = json.loads(calls[-1][1])["body"]
        self.assertIn(f"<!-- GACE_BOUNDED_HOST_RESULT request_id={RID} -->", body)
        for marker in ("SERVERCORE_BOUNDED_HOST_STATE=PASS", "SERVERCORE_BOUNDED_HOST_EXIT_CODE=0",
                       f"SERVERCORE_BOUNDED_HOST_SHA={SHA}", f"SERVERCORE_BOUNDED_HOST_REQUEST_ID={RID}"):
            self.assertIn(marker, body)
        self.assertNotIn("secretvalue", body)
        self.assertIsNone(sink.publish_record(RID, result_dir=self.dir, runner=runner))  # already published
        self.assertEqual(len([c for c in calls if c[0][:3] == ["api", "-X", "POST"]]), 1)
        self.assertEqual(sink.pending_ids(self.dir), [])

    def test_host_writer_ledger_metadata_overrides_locator_without_leaking_payload(self):
        # Real large-output Host writer persists both streams; Receiver and
        # Result Sink carry a short locator. The public Issue must refer to
        # the original Writer stream SHA/Unicode chars, not locator bytes.
        stdout = "日本語Ω🙂\\n" * 16000
        stderr = "警告⚠\\n" * 12000
        ledger = self.dir / "writer"
        ledger.mkdir(parents=True)
        evidence = {"request_id": RID, "repository": sink.RESULT_REPOSITORY,
                    "state": "HOST_COMMAND_PASS",
                    "source_sha": SHA, "exit_code": 0,
                    "stdout": stdout, "stderr": stderr}
        (ledger / (RID + ".json")).write_text(
            json.dumps(evidence, ensure_ascii=False), encoding="utf-8")
        sink.accept_record(rec(command_id="host.command",
                               stdout="GACE_HOST_OUTPUT_STORED request_id=" + RID,
                               stderr=""), result_dir=self.dir)
        actual = sink.read_record(RID, self.dir)
        body = sink.comment_body(actual, writer_dir=ledger)
        info = json.loads(body.split("```json\n", 1)[1].split("\n```", 1)[0])
        for name, source in (("stdout", stdout), ("stderr", stderr)):
            self.assertEqual(info[name + "_chars"], len(source))
            self.assertEqual(info[name + "_bytes"], len(source.encode("utf-8")))
            self.assertEqual(info[name + "_sha256"],
                             hashlib.sha256(source.encode("utf-8")).hexdigest())
            self.assertEqual(info[name + "_origin"], "HOST_WRITER_LEDGER_RAW")
            self.assertEqual(info[name], "")
            self.assertTrue(info[name + "_preview_truncated"])
            self.assertNotIn(source[:15], body)
        evidence["source_sha"] = "f" * 40
        (ledger / (RID + ".json")).write_text(
            json.dumps(evidence, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(sink.SinkError, "WRITER_LEDGER_CORRELATION_MISMATCH"):
            sink.comment_body(actual, writer_dir=ledger)
        (ledger / (RID + ".json")).unlink()
        # When no Writer result exists (admission denial), never invent it.
        fallback = sink.comment_body(actual, writer_dir=ledger)
        self.assertNotIn("HOST_WRITER_LEDGER_RAW", fallback)

    def test_cross_repository_target_sha_is_not_dispatcher_sha_and_publishes(self):
        # Actual failure mode of AI Core: Host Writer source_sha is the
        # registered TARGET repo SHA, while Sink host_sha is Dispatcher SHA.
        target = "seigo-gace/ai-core"
        target_sha = "b" * 40
        stdout = "日本語Ω🙂\\n" * 12000
        stderr = "warning⚠\\n" * 3500
        ledger = self.dir / "writer"
        ledger.mkdir(parents=True)
        writer = {"request_id": RID, "repository": target, "source_sha": target_sha,
                  "state": "HOST_COMMAND_PASS", "exit_code": 0,
                  "stdout": stdout, "stderr": stderr}
        (ledger / (RID + ".json")).write_text(json.dumps(writer, ensure_ascii=False),
                                              encoding="utf-8")
        sink.accept_record(rec(command_id="host.command", host_sha=SHA,
                               expected_sha=SHA,
                               stdout="GACE_HOST_OUTPUT_STORED request_id=" + RID,
                               stderr=""), result_dir=self.dir)
        calls = []
        def runner(args, stdin=None, timeout=40):
            calls.append((args, stdin))
            if args[:2] == ["api", "-X"]:
                return json.dumps({"id": 88, "html_url": "https://github.com/x/y/issues/10#issuecomment-88"})
            if "/comments?" in args[-1]:
                return "[]"
            return json.dumps({"comments": 100})
        found = sink.publish_record(RID, result_dir=self.dir, runner=runner,
                                    writer_dir=ledger)
        self.assertEqual(found["comment_id"], 88)
        self.assertEqual(sink.pending_ids(self.dir), [])
        body = json.loads(calls[-1][1])["body"]
        info = json.loads(body.split("```json\n", 1)[1].split("\n```", 1)[0])
        for key, raw in (("stdout", stdout), ("stderr", stderr)):
            self.assertEqual(info[key + "_sha256"], hashlib.sha256(raw.encode("utf-8")).hexdigest())
            self.assertEqual(info[key + "_bytes"], len(raw.encode("utf-8")))
            self.assertEqual(info[key + "_chars"], len(raw))
            self.assertEqual(info[key], "")
            self.assertNotIn(raw[:25], body)
        self.assertEqual(info["host_sha"], SHA)
        self.assertNotEqual(target_sha, SHA)

        # Neither incomplete/corrupt provenance nor same-repo fake SHA may
        # be promoted to an authentic writer/dispatcher correlation.
        with self.assertRaisesRegex(sink.SinkError, "WRITER_LEDGER_CORRELATION_MISMATCH"):
            self._invalid_writer_probe(ledger, writer)

    def _invalid_writer_probe(self, ledger, writer):
        # For a server-core-local request the two SHA pins must still match.
        writer = {**writer, "repository": sink.RESULT_REPOSITORY}
        (ledger / (RID + ".json")).write_text(json.dumps(writer), encoding="utf-8")
        return sink.trusted_writer_metadata(
            sink.read_record(RID, self.dir), writer_dir=ledger)

    def test_source_context_mismatch_publishes_only_verified_safe_hint(self):
        ledger = self.dir / "writer"
        ledger.mkdir(parents=True)
        writer = {"request_id": RID, "repository": "seigo-gace/ai-core",
                  "source_sha": "b" * 40, "state": "FAIL", "exit_code": 74, "source_preflight": True,
                  "stdout": "", "stderr": "CHAT_SOURCE_SHA_MISMATCH\n"}
        p = ledger / (RID + ".json")
        p.write_text(json.dumps(writer), encoding="utf-8")
        sink.accept_record(rec(command_id="host.command", state="FAIL", exit_code=74,
                               stdout="", stderr="GACE_HOST_OUTPUT_STORED"),
                           result_dir=self.dir)
        record = sink.read_record(RID, self.dir)
        comment = sink.comment_body(record, writer_dir=ledger)
        data = json.loads(comment.split("```json\n", 1)[1].split("\n```", 1)[0])
        self.assertEqual(data["diagnostic_hint"], "CHAT_SOURCE_SHA_MISMATCH")
        self.assertEqual(data["stderr"], "")
        self.assertNotIn("CHAT_SOURCE_SHA_MISMATCH\n", comment)
        # A matching exit alone is not evidence of the specific preflight.
        writer["stderr"] = "private stderr details"
        p.write_text(json.dumps(writer), encoding="utf-8")
        without = sink.comment_body(record, writer_dir=ledger)
        self.assertNotIn("diagnostic_hint", without)
        self.assertNotIn("private stderr details", without)

    def test_issue_comment_contains_metadata_not_output(self):
        output = "日本語の長文" * 10000
        sink.accept_record(rec(stdout=output, stderr="private failure details"), result_dir=self.dir)
        saved = sink.read_record(RID, self.dir)
        self.assertEqual(saved["stdout"], output)
        body = sink.comment_body(saved)
        self.assertNotIn("日本語の長文", body)
        self.assertNotIn("private failure details", body)
        self.assertIn(hashlib.sha256(output.encode("utf-8")).hexdigest(), body)
        self.assertIn('"stdout_chars": ' + str(len(output)), body)
        self.assertIn('"stdout": ""', body)

    def test_crash_between_post_and_save_does_not_duplicate_comment(self):
        sink.accept_record(rec(), result_dir=self.dir)

        def runner(args, stdin=None, timeout=40):
            if "/comments?" in args[-1]:
                return json.dumps([{"id": 55, "html_url": "https://github.com/x/y/issues/10#issuecomment-55",
                                    "body": "<!-- GACE_BOUNDED_HOST_RESULT request_id=" + RID + " -->"}])
            if args == ["api", f"repos/{sink.RESULT_REPOSITORY}/issues/{sink.RESULT_ISSUE}"]:
                return json.dumps({"comments": 1})
            raise AssertionError("must not post twice")

        self.assertEqual(sink.publish_record(RID, result_dir=self.dir, runner=runner)["comment_id"], 55)

    def test_gh_binary_uses_fixed_absolute_candidates_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "gh"
            fake.write_text("#!/bin/sh\n")
            fake.chmod(0o755)
            self.assertEqual(sink.gh_binary((str(Path(tmp) / "missing"), str(fake))), str(fake))
            with self.assertRaises(sink.SinkError):
                sink.gh_binary((str(Path(tmp) / "missing"),))
        self.assertTrue(all(c.startswith("/") for c in sink.GH_CANDIDATES))

    def test_record_dir_is_traversable_under_service_umask(self):
        import os
        old = os.umask(0o117)
        try:
            sink.accept_record(rec(), result_dir=self.dir)
        finally:
            os.umask(old)
        self.assertEqual(oct(self.dir.stat().st_mode & 0o777), "0o700")
        self.assertEqual(sink.read_record(RID, self.dir)["state"], "PASS")

    def test_retryable_never_published(self):
        sink.accept_record(rec(state="RETRYABLE", exit_code=1, host_sha=""), result_dir=self.dir)
        self.assertEqual(sink.pending_ids(self.dir), [])

    def test_durable_publish_retry_backoff_never_abandons_result(self):
        self.assertEqual([sink.publisher_retry_seconds(n) for n in (1, 2, 3, 40, 41, 500)],
                         [15, 30, 60, 300, 300, 300])
        sink.accept_record(rec(), result_dir=self.dir)

        def offline(args, stdin=None, timeout=40):
            raise sink.SinkError("GH_COMMAND_FAILED")

        with self.assertRaises(sink.SinkError):
            sink.publish_record(RID, result_dir=self.dir, runner=offline)
        self.assertIn(RID, sink.pending_ids(self.dir))

        def online(args, stdin=None, timeout=40):
            if args[:2] == ["api", "-X"]:
                return json.dumps({"id": 77, "html_url": "https://github.com/x/y/issues/10#issuecomment-77"})
            if "/comments?" in args[-1]:
                return "[]"
            return json.dumps({"comments": 9876})
            return json.dumps({"id": 77, "html_url": "https://github.com/x/y/issues/10#issuecomment-77"})

        self.assertEqual(sink.publish_record(RID, result_dir=self.dir, runner=online)["comment_id"], 77)
        self.assertNotIn(RID, sink.pending_ids(self.dir))

    def test_fixed_publish_target_matches_contract(self):
        contract = json.loads((ROOT / "operations" / "github-project-bounded-host.json").read_text())
        target = contract["result_return"]
        self.assertEqual((target["repository"], target["issue_number"]), (sink.RESULT_REPOSITORY, sink.RESULT_ISSUE))
        self.assertEqual(target["marker"], sink.MARKER)


class ReceiverResultTests(unittest.TestCase):
    def serve(self, now=1700000000, secret=b"k", root="/nonexistent"):
        contract = {"request_schema": "gace.servercore-bounded-host.request/v1",
                    "allowed_command_ids": ["project.git_head", "project.git_status", "service.deploy", "host.command"],
                    "canonical_host_root": root}
        handler = receiver.make_handler(contract, delivery_key=secret, now_fn=lambda: now)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        return server.server_address[1]

    def post(self, port, payload, secret=b"k"):
        body = json.dumps(payload).encode()
        mid, ts = "msg_" + secrets.token_hex(6), "1700000000"
        digest = hmac.new(secret, mid.encode() + b"." + ts.encode() + b"." + body, hashlib.sha256).digest()
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("POST", receiver.RECEIVER_PATH, body, {
            "content-type": "application/json", "x-gace-destination": "server-core-bounded-host",
            "webhook-id": mid, "webhook-timestamp": ts,
            "webhook-signature": "v1," + base64.b64encode(digest).decode()})
        resp = conn.getresponse()
        return resp.status, json.loads(resp.read())

    def request(self, **kw):
        base = {"schema": "gace.servercore-bounded-host.request/v1", "id": RID,
                "command_id": "project.git_head", "expected_sha": SHA}
        base.update(kw)
        return base

    def test_receiver_denial_has_redacted_diagnostic_log(self):
        log = __import__("io").StringIO()
        with patch.object(receiver.sys, "stderr", log):
            status, body = self.post(self.serve(), self.request(command_id="not.registered"))
        self.assertEqual((status, body["error"]), (422, "COMMAND_NOT_REGISTERED"))
        value = log.getvalue()
        self.assertIn("GACE_RECEIVER_RESULT status=422", value)
        self.assertIn("request_id=" + RID, value)
        self.assertIn("error=COMMAND_NOT_REGISTERED", value)
        self.assertNotIn("webhook-signature", value)
        self.assertNotIn("secret", value)

    def test_success_is_reported_with_exit_code_sha_and_stdout(self):
        reports = []
        fake = {"command_id": "project.git_head", "source_sha": SHA, "read_only": True}
        with patch.object(receiver.bounded_host, "execute", return_value=fake), \
                patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, body = self.post(self.serve(), self.request())
        self.assertEqual((status, body["state"], body["result_recorded"]), (200, "PASS", True))
        r = reports[0]
        self.assertEqual((r["request_id"], r["state"], r["exit_code"], r["host_sha"], r["expected_sha"]),
                         (RID, "PASS", 0, SHA, SHA))
        self.assertEqual(json.loads(r["stdout"]), fake)
        self.assertEqual(r["stderr"], "")

    def test_read_only_command_retries_when_sink_down(self):
        fake = {"command_id": "project.git_head", "source_sha": SHA, "read_only": True}
        with patch.object(receiver.bounded_host, "execute", return_value=fake), \
                patch.object(receiver, "report_result", return_value=False):
            status, body = self.post(self.serve(), self.request())
        self.assertEqual((status, body["error"]), (503, "RESULT_SINK_UNAVAILABLE"))

    def test_host_command_sink_failure_returns_retryable_503_not_false_success(self):
        request = self.request(command_id="host.command",
                               repository="G-ACE-inc/server-core", repo_sha=SHA,
                               command="printf safe")
        # The Host writer already completed this durable request, but the
        # result sink did not record it: Gateway must not be told 200.
        writer = {"command_id": "host.command", "source_sha": SHA,
                  "state": "HOST_COMMAND_PASS", "exit_code": 0, "stdout": "safe",
                  "stderr": ""}
        reports = []
        with patch.object(receiver, "dispatch_host_command", return_value=writer), \
                patch.object(receiver, "report_result",
                             side_effect=lambda record, p=None: reports.append(record) or False):
            status, body = self.post(self.serve(), request)
        self.assertEqual(status, 503)
        self.assertEqual(body["error"], "RESULT_SINK_UNAVAILABLE")
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["request_id"], RID)
        self.assertEqual(reports[0]["state"], "PASS")
        self.assertNotIn("result_recorded", body)

    def test_boundary_failure_reports_fail_exit_one(self):
        reports = []
        with patch.object(receiver.bounded_host, "execute", side_effect=receiver.bounded_host.BoundaryError("SOURCE_SHA_MISMATCH")), \
                patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, body = self.post(self.serve(), self.request())
        self.assertEqual(status, 422)
        self.assertEqual((reports[0]["state"], reports[0]["exit_code"], reports[0]["stderr"]),
                         ("FAIL", 1, "SOURCE_SHA_MISMATCH"))

    def real_repo(self):
        import subprocess
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(__import__("shutil").rmtree, tmp, ignore_errors=True)
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(tmp)]
        subprocess.run([*git, "init", "-q", "-b", "main"], check=True, capture_output=True)
        (tmp / "a").write_text("x")
        subprocess.run([*git, "add", "a"], check=True, capture_output=True)
        subprocess.run([*git, "commit", "-q", "-m", "c"], check=True, capture_output=True)
        head = subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        return tmp, head

    def test_sha_mismatch_reports_the_real_host_head_so_one_denial_is_enough_to_repin(self):
        root, head = self.real_repo()
        reports = []
        with patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, body = self.post(self.serve(root=str(root)), self.request())
        self.assertEqual((status, body["error"], body["host_sha"]), (422, "SOURCE_SHA_MISMATCH", head))
        self.assertEqual((reports[0]["state"], reports[0]["host_sha"], reports[0]["expected_sha"], reports[0]["stderr"]),
                         ("FAIL", head, SHA, "SOURCE_SHA_MISMATCH"))
        self.assertEqual(sink.validate_record({**reports[0], "schema": sink.RECORD_SCHEMA})["host_sha"], head)
        self.assertEqual(reports[0]["stdout"], "")

    def test_matching_sha_still_passes_and_other_denials_never_disclose_head(self):
        root, head = self.real_repo()
        reports = []
        with patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, body = self.post(self.serve(root=str(root)), self.request(expected_sha=head))
            self.assertEqual((status, body["state"], reports[-1]["host_sha"]), (200, "PASS", head))
            with patch.object(receiver.bounded_host, "execute",
                              side_effect=receiver.bounded_host.BoundaryError("COMMAND_NOT_REGISTERED")):
                status, body = self.post(self.serve(root=str(root)), self.request())
        self.assertEqual(status, 422)
        self.assertNotIn("host_sha", body)
        self.assertEqual(reports[-1]["host_sha"], "")

    def test_unauthenticated_mismatch_discloses_nothing(self):
        root, _ = self.real_repo()
        reports = []
        with patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, body = self.post(self.serve(root=str(root)), self.request(), secret=b"wrong")
        self.assertGreaterEqual(status, 400)
        self.assertNotIn("host_sha", body)
        self.assertEqual(reports, [])

    def test_validation_failure_with_valid_id_is_reported(self):
        reports = []
        with patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, _ = self.post(self.serve(), self.request(command_id="project.nope"))
        self.assertEqual(status, 422)
        self.assertEqual((reports[0]["request_id"], reports[0]["state"], reports[0]["command_id"]),
                         (RID, "FAIL", "project.nope"))

    def test_unauthenticated_delivery_is_never_reported(self):
        reports = []
        with patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, _ = self.post(self.serve(), self.request(), secret=b"wrong")
        self.assertGreaterEqual(status, 400)
        self.assertEqual(reports, [])

    def test_transient_error_is_retryable_not_terminal(self):
        reports = []
        with patch.object(receiver.bounded_host, "execute", side_effect=RuntimeError("boom")), \
                patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, _ = self.post(self.serve(), self.request())
        self.assertEqual(status, 500)
        self.assertEqual(reports[0]["state"], "RETRYABLE")


spec_poll = importlib.util.spec_from_file_location("servercore_bounded_result_poll", ROOT / "scripts" / "servercore_bounded_result_poll.py")
poll = importlib.util.module_from_spec(spec_poll)
spec_poll.loader.exec_module(poll)


class PollTests(unittest.TestCase):
    def comment(self, **kw):
        record = {"request_id": RID, "command_id": "project.git_head", "state": "PASS", "exit_code": 0,
                  "host_sha": SHA, "expected_sha": SHA, "stdout": "{}", "stderr": ""}
        record.update(kw)
        body = f"<!-- GACE_BOUNDED_HOST_RESULT request_id={record['request_id']} -->\n```json\n" + json.dumps(record) + "\n```"
        return {"body": body, "html_url": "https://example.test/c/1"}

    def run_poll(self, comments, **extra):
        args = ["--repository", "o/r", "--issue", "10", "--request-id", RID, "--command-id", "project.git_head",
                "--expected-sha", SHA, "--timeout", "3", "--interval", "1"]
        ticks = iter(range(0, 100))
        import io, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = poll.main(args, fetch=lambda path: comments, sleep=lambda s: None, clock=lambda: next(ticks))
        return code, out.getvalue()

    def test_pass_prints_correlated_markers(self):
        code, out = self.run_poll([{"body": "unrelated"}, self.comment()])
        self.assertEqual(code, 0)
        for line in ("SERVERCORE_BOUNDED_HOST_RESULT=RETURNED", f"SERVERCORE_BOUNDED_HOST_REQUEST_ID={RID}",
                     "SERVERCORE_BOUNDED_HOST_EXIT_CODE=0", f"SERVERCORE_BOUNDED_HOST_SHA={SHA}"):
            self.assertIn(line, out)

    def test_fail_state_exits_one(self):
        code, out = self.run_poll([self.comment(state="FAIL", exit_code=1, stderr="SOURCE_SHA_MISMATCH")])
        self.assertEqual(code, 1)
        self.assertIn("SOURCE_SHA_MISMATCH", out)

    def test_timeout_is_not_a_pass(self):
        code, out = self.run_poll([])
        self.assertEqual(code, 2)
        self.assertIn("SERVERCORE_BOUNDED_HOST_RESULT=NOT_RETURNED", out)

    def test_other_request_id_is_ignored_and_mismatch_detected(self):
        other = self.comment(request_id="req_" + "f" * 24)
        self.assertEqual(self.run_poll([other])[0], 2)
        self.assertEqual(self.run_poll([self.comment(command_id="project.git_status")])[0], 3)
        self.assertEqual(self.run_poll([self.comment(expected_sha="b" * 40)])[0], 3)


if __name__ == "__main__":
    unittest.main()
