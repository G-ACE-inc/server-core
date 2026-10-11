#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import secrets
import unittest
from unittest.mock import patch

import servercore_bounded_host_gateway_send as sender
import servercore_bounded_host_receiver as receiver
from gace_internal_delivery_auth import verify_delivery

CONTRACT = {
    "request_schema": "gace.servercore-bounded-host.request/v1",
    "allowed_command_ids": ["project.git_head", "project.git_status"],
    "transport": {
        "event_type": "gace.servercore-bounded-host.requested",
        "destination_id": "server-core-bounded-host",
        "source_id": "server-core-github",
        "gateway_url_env": "GACE_EVENT_GATEWAY_URL",
        "gateway_token_env": "GACE_EVENT_GATEWAY_TOKEN",
    },
}


class GatewaySendTests(unittest.TestCase):
    def test_build_event(self):
        req = {
            "schema": "gace.servercore-bounded-host.request/v1",
            "id": "req_" + "a" * 24,
            "command_id": "project.git_head",
            "expected_sha": "b" * 40,
        }
        event = sender.build_event(req, CONTRACT)
        self.assertEqual(event["destinationId"], "server-core-bounded-host")
        self.assertEqual(event["eventType"], "gace.servercore-bounded-host.requested")
        self.assertEqual(event["data"], req)

    def test_rejects_unregistered_command(self):
        with self.assertRaises(sender.SendError):
            sender.validate_cli("system.shell", "a" * 40, CONTRACT)

    def test_remote_registered_tests_denied(self):
        from pathlib import Path
        contract = json.loads((Path(__file__).resolve().parents[1] / "operations" / "github-project-bounded-host.json").read_text())
        self.assertNotIn("project.registered_tests", contract["allowed_command_ids"])
        with self.assertRaisesRegex(sender.SendError, "COMMAND_NOT_REGISTERED"):
            sender.validate_cli("project.registered_tests", "a" * 40, contract)

    def test_reflect_requires_before_sha_and_rejects_extra_fields(self):
        contract = {**CONTRACT, "allowed_command_ids": [*CONTRACT["allowed_command_ids"], "project.source_reflect"]}
        with self.assertRaisesRegex(sender.SendError, "REFLECT_BEFORE_INVALID"):
            sender.validate_cli("project.source_reflect", "b" * 40, contract)
        request = sender.validate_cli("project.source_reflect", "b" * 40, contract,
                                      expected_before="a" * 40)
        self.assertEqual(request["expected_before"], "a" * 40)
        self.assertEqual(receiver.validate_request(request, contract)["expected_sha"], "b" * 40)
        with self.assertRaisesRegex(receiver.ReceiverError, "REFLECT_KEYS_INVALID"):
            receiver.validate_request({**request, "shell": "echo nope"}, contract)
        with self.assertRaisesRegex(sender.SendError, "UNEXPECTED_BEFORE_SHA"):
            sender.validate_cli("project.git_head", "b" * 40, contract,
                                expected_before="a" * 40)

    def test_reflect_rejected_without_admitted_socket(self):
        contract = {**CONTRACT, "allowed_command_ids": [*CONTRACT["allowed_command_ids"], "project.source_reflect"]}
        request = sender.validate_cli("project.source_reflect", "b" * 40, contract,
                                      expected_before="a" * 40)
        with self.assertRaisesRegex(receiver.ReceiverError, "REFLECT_EXECUTOR_UNAVAILABLE"):
            receiver.dispatch_reflect(request, "/tmp/no-such-gace-approved-socket")

    def test_terminal_host_preflight_denials_do_not_retry_as_infrastructure(self):
        import io
        class Socket:
            def __init__(self, code): self.code = code
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def settimeout(self, _): pass
            def connect(self, _): pass
            def sendall(self, _): pass
            def makefile(self, _):
                return io.BytesIO(json.dumps({"ok": False, "error": self.code}).encode() + b"\\n")
        request = {"id": "req_" + "a"*24, "command_id": "project.source_reflect",
                   "expected_sha": "b"*40, "expected_before": "a"*40}
        for code in ("DIRTY_CHECKOUT_DENIED", "REMOTE_MAIN_SHA_MISMATCH", "BEFORE_SHA_MISMATCH"):
            with self.subTest(code=code), patch.object(receiver.socket, "socket", return_value=Socket(code)):
                with self.assertRaises(receiver.ReceiverError) as error:
                    receiver.dispatch_reflect(request)
                self.assertEqual(error.exception.status, 422)
                self.assertEqual(error.exception.code, "REFLECT_PREFLIGHT_" + code)
        with patch.object(receiver.socket, "socket", return_value=Socket("GIT_EXECUTION_FAILED")):
            with self.assertRaises(receiver.ReceiverError) as error:
                receiver.dispatch_reflect(request)
            self.assertEqual(error.exception.status, 503)

    def test_gateway_send_accepts_202(self):
        req = sender.validate_cli("project.git_head", "c" * 40, CONTRACT)

        class FakeResponse:
            status = 202

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, _n):
                return b'{"ok":true}'

        class FakeOpener:
            def open(self, request, timeout=0):
                self.request = request
                return FakeResponse()

        opener = FakeOpener()
        env = {
            "GACE_EVENT_GATEWAY_URL": "https://gateway.test",
            "GACE_EVENT_GATEWAY_TOKEN": "token",
        }
        payload = sender.send(req, CONTRACT, env=env, opener=opener)
        self.assertEqual(payload["ok"], True)
        self.assertIn(b"servercore-bounded-host", opener.request.data)


class DeliveryAuthTests(unittest.TestCase):
    def test_signature_roundtrip(self):
        secret = b"test-secret"
        body = b'{"schema":"gace.servercore-bounded-host.request/v1"}'
        message_id = "msg_" + secrets.token_hex(8)
        timestamp = "1700000000"
        digest = hmac.new(
            secret,
            message_id.encode() + b"." + timestamp.encode() + b"." + body,
            hashlib.sha256,
        ).digest()
        headers = {
            "x-gace-destination": "server-core-bounded-host",
            "webhook-id": message_id,
            "webhook-timestamp": timestamp,
            "webhook-signature": "v1," + base64.b64encode(digest).decode(),
        }
        verify_delivery(
            headers,
            body,
            expected_destination="server-core-bounded-host",
            delivery_key=secret,
            now=1700000000,
            tolerance_seconds=300,
        )


if __name__ == "__main__":
    unittest.main()
