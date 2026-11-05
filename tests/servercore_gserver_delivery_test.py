"""Signed target delivery through the existing Host ledger and Result Sink."""
import base64
import copy
import hashlib
import hmac
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import servercore_gserver_target as target
import servercore_result_sink as sink
import servercore_bounded_result_poll as poll
from gace_internal_delivery_auth import DeliveryAuthError


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.contract = json.loads((ROOT / "operations/github-project-bounded-host.json").read_text())
        self.contract["host_targets"]["gserver"].update(
            status="HOST_ADMITTED", canonical_host_root=str(self.root))
        self.key = b"isolated-test-key"
        self.request = dict(schema=self.contract["request_schema"], id="req_" + "a" * 24,
                            command_id="host.command", expected_sha="b" * 40,
                            repository=target.REPOSITORY, repo_sha="c" * 40,
                            command="printf test", command_sha256=hashlib.sha256(b"printf test").hexdigest(),
                            host_target="gserver")
        self.executions = 0

    def execute(self, request, root):
        self.executions += 1
        return dict(request_id=request["id"], host_target="gserver", repository=target.REPOSITORY,
                    repo_sha=request["repo_sha"], host_sha=request["repo_sha"],
                    dispatcher_sha=request["expected_sha"], command_sha256=request["command_sha256"],
                    state="PASS", exit_code=0, stdout="private output", stderr="",
                    stdout_sha256=hashlib.sha256(b"private output").hexdigest(),
                    stderr_sha256=hashlib.sha256(b"").hexdigest())

    def report(self, record):
        sink.accept_record(record, result_dir=self.root / "sink")
        return True

    def deliver(self, *, request=None, bad_signature=False, report=None, execute=None):
        body = json.dumps(request or self.request).encode()
        signature = hmac.new(self.key, b"delivery.1000." + body, hashlib.sha256).digest()
        headers = {"x-gace-destination": "gserver-bounded-host", "webhook-id": "delivery",
                   "webhook-timestamp": "1000", "webhook-signature": "v1," + base64.b64encode(signature).decode()}
        if bad_signature:
            body += b" "
        return target.receive_delivery(headers, body, contract=self.contract, delivery_key=self.key,
                                       root=self.root, result_dir=self.root / "writer",
                                       lock_path=self.root / "lock", execute=execute or self.execute,
                                       report=report or self.report, now=1000)

    def test_signed_delivery_persists_and_duplicate_does_not_execute(self):
        first = self.deliver()
        self.assertEqual(first, self.deliver())
        self.assertEqual(self.executions, 1)
        record = sink.read_record(self.request["id"], self.root / "sink")
        self.assertEqual(record["target_evidence"]["dispatcher_sha"], self.request["expected_sha"])
        public = sink.comment_body(record)
        self.assertNotIn("private output", public)
        self.assertIn(first["command_sha256"], public)
        view = json.loads(public.split("```json\n", 1)[1].split("\n```", 1)[0])
        pins = dict(host_target="gserver", repo_sha=self.request["repo_sha"],
                    command_sha256=self.request["command_sha256"])
        self.assertEqual(poll.evaluate(view, self.request["id"], "host.command",
                                       self.request["expected_sha"], **pins), (0, "OK"))
        view["target_evidence"]["command_sha256"] = "f" * 64
        self.assertEqual(poll.evaluate(view, self.request["id"], "host.command",
                                       self.request["expected_sha"], **pins)[0], 3)

    def test_invalid_signature_and_unadmitted_host_never_execute(self):
        with self.assertRaises(DeliveryAuthError):
            self.deliver(bad_signature=True)
        self.contract["host_targets"]["gserver"]["status"] = "SOURCE_CONTRACT_ONLY"
        with self.assertRaisesRegex(target.GserverTargetError, "HOST_NOT_ADMITTED"):
            self.deliver()
        self.assertEqual(self.executions, 0)
        self.assertFalse((self.root / "writer").exists())

    def test_sink_retry_reuses_durable_result(self):
        with self.assertRaisesRegex(target.GserverTargetError, "SINK_UNAVAILABLE"):
            self.deliver(report=lambda record: False)
        self.deliver()
        self.assertEqual(self.executions, 1)

    def test_same_id_changed_command_is_rejected(self):
        self.deliver()
        changed = dict(self.request, command="printf other",
                       command_sha256=hashlib.sha256(b"printf other").hexdigest())
        with self.assertRaisesRegex(target.GserverTargetError, "REPLAY_CONFLICT"):
            self.deliver(request=changed)
        self.assertEqual(self.executions, 1)

    def test_interrupted_execution_never_reexecutes(self):
        def crash(request, root):
            raise RuntimeError("simulated worker crash")
        with self.assertRaises(RuntimeError):
            self.deliver(execute=crash)
        with self.assertRaisesRegex(target.GserverTargetError, "OUTCOME_UNKNOWN"):
            self.deliver()
        self.assertEqual(self.executions, 0)

    def test_sink_rejects_tampered_evidence(self):
        record = target.sink_record(self.execute(self.request, self.root), self.request)
        for field in ("stdout_sha256", "dispatcher_sha", "repo_sha"):
            bad = copy.deepcopy(record)
            bad["target_evidence"][field] = "f" * (64 if field.endswith("256") else 40)
            with self.subTest(field=field), self.assertRaises(sink.SinkError):
                sink.accept_record(bad, result_dir=self.root / "sink")


if __name__ == "__main__":
    unittest.main()
