import importlib.util
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
import os

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "servercore_terminal_one_step", SCRIPTS / "servercore_terminal_one_step.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

gateway_send = module.gateway_send
result_lookup = module.result_lookup
CONTRACT = json.loads((ROOT / "operations" / "github-project-bounded-host.json").read_text())
RID = "req_" + "a" * 24
HEAD_SHA = "c" * 40
HOST_SHA = "b" * 40

# host.command is the ordinary CHAT command and the only effect that accepts an
# explicit (operator-correlated) Request ID in the reused sender validator.
HOST_KW = {"command_id": "host.command", "expected_sha": HEAD_SHA,
           "repository": "G-ACE-inc/server-core", "host_command": "git status --porcelain",
           "repo_sha": HEAD_SHA}
READ_KW = {"command_id": "project.git_head", "expected_sha": HEAD_SHA}


def _recorded(state="PASS", exit_code=0, host_sha=HOST_SHA, request_id=RID):
    return {"request_id": request_id, "status": "RECORDED", "state": state,
            "exit_code": exit_code, "host_sha": host_sha,
            "recorded_at": "2026-11-12T00:00:00Z", "published": False}


NOT_RECORDED = {"request_id": RID, "status": "NOT_RECORDED"}


class _SequencedLookup:
    """Return successive canned lookup results; raise if an item is an Exception."""

    def __init__(self, items):
        self.items = list(items)
        self.calls = 0

    def __call__(self, request_id, socket_path=None, connect=None):
        item = self.items[min(self.calls, len(self.items) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


class _SendRecorder:
    def __init__(self, receipt=None, error=None):
        self.receipt = receipt or {"ok": True, "receipt": "durable"}
        self.error = error
        self.calls = 0

    def __call__(self, request, contract, env=None, opener=None):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.receipt


class OneStepOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self._orig_lookup = result_lookup.lookup
        self._orig_send = gateway_send.send
        self.sleeps = []
        self.addCleanup(self._restore)

    def _restore(self):
        result_lookup.lookup = self._orig_lookup
        gateway_send.send = self._orig_send

    def _run(self, command_kwargs, lookup_items, *, send=None, **kwargs):
        result_lookup.lookup = _SequencedLookup(lookup_items)
        self.sender = send or _SendRecorder()
        gateway_send.send = self.sender
        return module.execute_and_fetch(
            CONTRACT, command_kwargs, env={}, sleep=self.sleeps.append, **kwargs)

    def test_read_only_pass_returns_host_sha_only(self):
        data = self._run(READ_KW, [NOT_RECORDED, _recorded()])
        self.assertEqual(data["outcome"], "HOST_PASS")
        self.assertEqual(data["host_sha"], HOST_SHA)
        self.assertTrue(data["read_only"])
        self.assertEqual(self.sender.calls, 1)
        self.assertNotIn("stdout", json.dumps(data))
        self.assertNotIn("stderr", json.dumps(data))

    def test_host_fail_is_distinct_outcome(self):
        data = self._run(HOST_KW, [NOT_RECORDED, _recorded(state="FAIL", exit_code=75, host_sha="")],
                         request_id=RID)
        self.assertEqual((data["outcome"], data["exit_code"]), ("HOST_FAIL", 75))
        self.assertFalse(data["read_only"])

    def test_same_id_already_recorded_is_refused_without_sending(self):
        with self.assertRaisesRegex(module.OneStepError, "REQUEST_ID_ALREADY_RECORDED"):
            self._run(HOST_KW, [_recorded()], request_id=RID)
        self.assertEqual(self.sender.calls, 0)

    def test_gateway_failure_is_distinct_and_not_a_sink_class(self):
        send = _SendRecorder(error=gateway_send.SendError("GATEWAY_HTTP_502"))
        with self.assertRaisesRegex(module.OneStepError, r"^GATEWAY:GATEWAY_HTTP_502$"):
            self._run(HOST_KW, [NOT_RECORDED, NOT_RECORDED], send=send, request_id=RID)

    def test_sink_failure_is_distinct_and_blocks_send(self):
        unavailable = result_lookup.ResultQueryError("SINK_SOCKET_UNAVAILABLE")
        with self.assertRaisesRegex(module.OneStepError, r"^SINK:SINK_SOCKET_UNAVAILABLE$"):
            self._run(HOST_KW, [unavailable], request_id=RID)
        self.assertEqual(self.sender.calls, 0)

    def test_result_timeout_after_bounded_retries(self):
        with self.assertRaisesRegex(module.OneStepError, "RESULT_TIMEOUT"):
            self._run(READ_KW, [NOT_RECORDED] * 20)
        # Pre-check + attempts polls; backoff sleeps = attempts - 1.
        self.assertEqual(len(self.sleeps), module.DEFAULT_ATTEMPTS - 1)

    def test_read_only_pin_mismatch_rejected(self):
        data = self._run(READ_KW, [NOT_RECORDED, _recorded(host_sha="d" * 40)], pinned_sha=HOST_SHA)
        self.assertEqual(data["outcome"], "HOST_SHA_MISMATCH")

    def test_read_only_pin_match_passes(self):
        data = self._run(READ_KW, [NOT_RECORDED, _recorded()], pinned_sha=HOST_SHA)
        self.assertEqual(data["outcome"], "HOST_PASS")

    def test_pin_only_for_read_only(self):
        with self.assertRaisesRegex(module.OneStepError, "PIN_ONLY_FOR_READ_ONLY"):
            module.plan_request(CONTRACT, dict(HOST_KW), pinned_sha=HOST_SHA)

    def test_read_only_forbids_expected_before(self):
        with self.assertRaisesRegex(module.OneStepError, "READ_ONLY_FORBIDS_EXPECTED_BEFORE"):
            module.plan_request(CONTRACT, dict(READ_KW, expected_before=HEAD_SHA))

    def test_mutating_keeps_expected_before_guard(self):
        # source_reflect without a before SHA is rejected by the reused validator.
        with self.assertRaisesRegex(module.OneStepError, "REQUEST_INVALID:REFLECT_BEFORE_INVALID"):
            module.plan_request(CONTRACT, {"command_id": "project.source_reflect",
                                           "expected_sha": HEAD_SHA})
        plan = module.plan_request(CONTRACT, {"command_id": "project.source_reflect",
                                              "expected_sha": HEAD_SHA, "expected_before": HOST_SHA})
        self.assertFalse(plan["read_only"])
        self.assertEqual(plan["request"]["expected_before"], HOST_SHA)

    def test_explicit_invalid_request_id_denied(self):
        with self.assertRaisesRegex(module.OneStepError, "REQUEST_ID_INVALID"):
            self._run(HOST_KW, [NOT_RECORDED], request_id="../secrets")


class OneStepDefaultOffTests(unittest.TestCase):
    def test_live_cli_uses_single_planned_id_for_send_and_result(self):
        # A fixed read command is assigned an ID by the sender. CLI planning
        # must NOT assign a second ID when it invokes the live runner.
        observed = {"sent": None, "lookups": 0}
        original_send = gateway_send.send
        original_lookup = result_lookup.lookup
        self.addCleanup(lambda: setattr(gateway_send, "send", original_send))
        self.addCleanup(lambda: setattr(result_lookup, "lookup", original_lookup))

        def send(request, contract, **kwargs):
            observed["sent"] = request["id"]
            return {"ok": True, "receipt": "durable"}

        def lookup(request_id, **kwargs):
            observed["lookups"] += 1
            if observed["lookups"] == 1:
                return {"request_id": request_id, "status": "NOT_RECORDED"}
            if request_id != observed["sent"]:
                raise AssertionError("sink lookup must use the exact sent ID")
            return _recorded(request_id=request_id)

        gateway_send.send = send
        result_lookup.lookup = lookup
        with patch.dict(os.environ, {"GACE_TERMINAL_ONE_STEP_ENABLED": "1"}), \
             patch.object(module, "plan_request", wraps=module.plan_request) as planned:
            output = io.StringIO()
            with redirect_stdout(output):
                code = module.main(["--command-id", "project.git_head", "--expected-sha", HEAD_SHA])
        self.assertEqual(code, 0)
        self.assertEqual(planned.call_count, 1)
        self.assertEqual(observed["lookups"], 2)
        result = json.loads(output.getvalue().splitlines()[0])
        self.assertEqual(result["request_id"], observed["sent"])
        self.assertEqual(result["outcome"], "HOST_PASS")

    def test_result_id_mismatch_is_rejected_even_if_lookup_is_mocked(self):
        with self.assertRaisesRegex(module.OneStepError, "RESULT_REQUEST_ID_MISMATCH"):
            module._finalize(
                RID, {"read_only": True, "pinned_sha": None, "effect": "read_only"},
                {"ok": True}, _recorded(request_id="req_" + "f" * 24))

    def test_plan_mode_contacts_nothing_when_disabled(self):
        orig_lookup, orig_send = result_lookup.lookup, gateway_send.send

        def boom(*a, **k):
            raise AssertionError("must not run while disabled")

        result_lookup.lookup = boom
        gateway_send.send = boom
        self.addCleanup(lambda: setattr(result_lookup, "lookup", orig_lookup))
        self.addCleanup(lambda: setattr(gateway_send, "send", orig_send))
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = module.main(["--command-id", "project.git_head", "--expected-sha", HEAD_SHA])
        out = buffer.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("ONE_STEP_MODE=PLAN_DISABLED", out)
        self.assertNotIn("QUEUED", out)


class OneStepReuseWiringTests(unittest.TestCase):
    """Integration: exercise the REAL reused send (via opener) and REAL lookup (via socket)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "sink.sock"

    def _serve(self, responses):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.path))
        server.listen(4)
        self.addCleanup(server.close)

        def handler():
            for payload in responses:
                try:
                    conn, _ = server.accept()
                except OSError:
                    return
                with conn:
                    incoming = b""
                    while not incoming.endswith(b"\n"):
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        incoming += chunk
                    conn.sendall((json.dumps(payload) + "\n").encode("utf-8"))

        thread = threading.Thread(target=handler, daemon=True)
        thread.start()
        self.addCleanup(lambda: thread.join(timeout=3))

    def _opener(self, status=202, body=b'{"ok": true}'):
        test = self

        class _Resp:
            status = None

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False

            def read(self_inner, size=-1):
                return body

        class _Opener:
            def open(self_inner, request, timeout=None):
                test.sent = request
                resp = _Resp()
                resp.status = status
                return resp

        return _Opener()

    def test_real_send_and_real_lookup_pass(self):
        self._serve([
            {"ok": True, "found": False, "record": None},
            {"ok": True, "found": True, "record": {
                "request_id": RID, "command_id": "host.command", "state": "PASS",
                "exit_code": 0, "host_sha": HOST_SHA, "recorded_at": "2026-11-12T00:00:00Z",
                "published": None, "stdout": "SECRET-STREAM", "stderr": "SECRET-STREAM"}},
        ])
        env = {"GACE_EVENT_GATEWAY_URL": "http://gateway.internal",
               "GACE_EVENT_GATEWAY_TOKEN": "t" * 24}
        data = module.execute_and_fetch(
            CONTRACT, HOST_KW, request_id=RID, env=env, opener=self._opener(),
            sink_socket_path=self.path, sleep=lambda *_: None)
        self.assertEqual(data["outcome"], "HOST_PASS")
        self.assertEqual(data["host_sha"], HOST_SHA)
        self.assertNotIn("SECRET-STREAM", json.dumps(data))
        # The reused sender actually posted to the existing Gateway events endpoint.
        self.assertTrue(self.sent.full_url.endswith("/internal/events"))

    def test_real_gateway_non_202_is_gateway_class(self):
        self._serve([{"ok": True, "found": False, "record": None}])
        env = {"GACE_EVENT_GATEWAY_URL": "http://gateway.internal",
               "GACE_EVENT_GATEWAY_TOKEN": "t" * 24}
        with self.assertRaisesRegex(module.OneStepError, r"^GATEWAY:"):
            module.execute_and_fetch(
                CONTRACT, HOST_KW, request_id=RID, env=env,
                opener=self._opener(status=500, body=b'{"ok": false}'),
                sink_socket_path=self.path, sleep=lambda *_: None)


if __name__ == "__main__":
    unittest.main()
