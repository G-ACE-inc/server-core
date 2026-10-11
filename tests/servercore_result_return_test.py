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
            if args[:2] == ["api", "--paginate"]:
                return ""
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

    def test_crash_between_post_and_save_does_not_duplicate_comment(self):
        sink.accept_record(rec(), result_dir=self.dir)

        def runner(args, stdin=None, timeout=40):
            if args[:2] == ["api", "--paginate"]:
                return "55\thttps://github.com/x/y/issues/10#issuecomment-55\ttrue\n"
            raise AssertionError("must not post twice")

        self.assertEqual(sink.publish_record(RID, result_dir=self.dir, runner=runner)["comment_id"], 55)

    def test_retryable_never_published(self):
        sink.accept_record(rec(state="RETRYABLE", exit_code=1, host_sha=""), result_dir=self.dir)
        self.assertEqual(sink.pending_ids(self.dir), [])

    def test_fixed_publish_target_matches_contract(self):
        contract = json.loads((ROOT / "operations" / "github-project-bounded-host.json").read_text())
        target = contract["result_return"]
        self.assertEqual((target["repository"], target["issue_number"]), (sink.RESULT_REPOSITORY, sink.RESULT_ISSUE))
        self.assertEqual(target["marker"], sink.MARKER)


class ReceiverResultTests(unittest.TestCase):
    def serve(self, now=1700000000, secret=b"k"):
        contract = {"request_schema": "gace.servercore-bounded-host.request/v1",
                    "allowed_command_ids": ["project.git_head", "project.git_status", "service.deploy"],
                    "canonical_host_root": "/nonexistent"}
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

    def test_boundary_failure_reports_fail_exit_one(self):
        reports = []
        with patch.object(receiver.bounded_host, "execute", side_effect=receiver.bounded_host.BoundaryError("SOURCE_SHA_MISMATCH")), \
                patch.object(receiver, "report_result", side_effect=lambda r, p=None: reports.append(r) or True):
            status, body = self.post(self.serve(), self.request())
        self.assertEqual(status, 422)
        self.assertEqual((reports[0]["state"], reports[0]["exit_code"], reports[0]["stderr"]),
                         ("FAIL", 1, "SOURCE_SHA_MISMATCH"))

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
