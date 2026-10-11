#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import secrets
import unittest
from unittest.mock import patch

import servercore_bounded_host_gateway_send as sender
from gace_internal_delivery_auth import verify_delivery

CONTRACT = {
    "request_schema": "gace.servercore-bounded-host.request/v1",
    "allowed_command_ids": ["project.git_head", "project.git_status", "project.registered_tests"],
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
            secret=secret,
            now=1700000000,
            tolerance_seconds=300,
        )


if __name__ == "__main__":
    unittest.main()
