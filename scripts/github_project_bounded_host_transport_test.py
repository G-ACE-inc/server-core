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
    def test_cli_host_command_does_not_shift_into_dev_job_arguments(self):
        from unittest.mock import patch
        import sys
        contract = {**CONTRACT, "allowed_command_ids": ["host.command"]}
        argv = ["sender", "--command-id", "host.command", "--expected-sha", "a"*40,
                "--repository", "seigo-gace/astera_v8", "--repo-sha", "b"*40,
                "--host-command", "git status --short"]
        with patch.object(sys, "argv", argv), patch.object(sender, "load_contract", return_value=contract), \
             patch.object(sender, "send", return_value={"ok": True}) as send:
            self.assertEqual(sender.main(), 0)
        request = send.call_args.args[0]
        self.assertEqual(request["command_id"], "host.command")
        self.assertEqual(request["repository"], "seigo-gace/astera_v8")
        self.assertEqual(request["command"], "git status --short")

    def test_cli_source_reflect_passes_repository_and_branch(self):
        from unittest.mock import patch
        import sys
        contract = {**CONTRACT, "allowed_command_ids": ["project.source_reflect"]}
        argv = ["sender", "--command-id", "project.source_reflect", "--expected-sha", "b"*40,
                "--expected-before", "a"*40, "--reflect-repository", "seigo-gace/TGserver",
                "--reflect-branch", "main"]
        with patch.object(sys, "argv", argv), patch.object(sender, "load_contract", return_value=contract), \
             patch.object(sender, "send", return_value={"ok": True}) as send:
            self.assertEqual(sender.main(), 0)
        request = send.call_args.args[0]
        self.assertEqual(request["repository"], "seigo-gace/TGserver")
        self.assertEqual(request["branch"], "main")

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
                return io.BytesIO(json.dumps({"ok": False, "error": self.code}).encode() + bytes([10]))
        request = {"id": "req_" + "a"*24, "command_id": "project.source_reflect",
                   "expected_sha": "b"*40, "expected_before": "a"*40}
        for code in ("DIRTY_CHECKOUT_DENIED", "REMOTE_BRANCH_SHA_MISMATCH", "BEFORE_SHA_MISMATCH"):
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


class ServiceDeployTransportTests(unittest.TestCase):
    CONTRACT = {**CONTRACT, "allowed_command_ids": [*CONTRACT["allowed_command_ids"],
                                                    "service.deploy", "service.deploy_status"]}
    SHA = "c" * 40

    def deploy_request(self):
        return sender.validate_cli("service.deploy", self.SHA, self.CONTRACT,
                                   repository="seigo-gace/webhook-gateway", service="api")

    def test_sender_requires_exact_target_and_rejects_wildcards(self):
        request = self.deploy_request()
        self.assertEqual((request["repository"], request["service"]), ("seigo-gace/webhook-gateway", "api"))
        for service in ("*", "api;x", "../api", None):
            with self.assertRaisesRegex(sender.SendError, "SERVICE_DEPLOY_TARGET_INVALID"):
                sender.validate_cli("service.deploy", self.SHA, self.CONTRACT,
                                    repository="seigo-gace/webhook-gateway", service=service)
        with self.assertRaisesRegex(sender.SendError, "UNEXPECTED_DEPLOY_TARGET"):
            sender.validate_cli("project.git_head", self.SHA, self.CONTRACT, repository="a/b", service="api")
        with self.assertRaisesRegex(sender.SendError, "DEPLOY_REQUEST_ID_INVALID"):
            sender.validate_cli("service.deploy_status", self.SHA, self.CONTRACT, deploy_request_id="latest")

    def test_receiver_validation_keys(self):
        request = self.deploy_request()
        self.assertEqual(receiver.validate_request(request, self.CONTRACT)["service"], "api")
        with self.assertRaisesRegex(receiver.ReceiverError, "DEPLOY_KEYS_INVALID"):
            receiver.validate_request({**request, "compose_file": "/tmp/x.yml"}, self.CONTRACT)
        with self.assertRaisesRegex(receiver.ReceiverError, "DEPLOY_TARGET_INVALID"):
            receiver.validate_request({**request, "service": "api;whoami"}, self.CONTRACT)
        status = sender.validate_cli("service.deploy_status", self.SHA, self.CONTRACT,
                                     deploy_request_id="req_" + "1" * 24)
        self.assertEqual(receiver.validate_request(status, self.CONTRACT)["deploy_request_id"], "req_" + "1" * 24)

    def test_receiver_unavailable_socket_fails_closed(self):
        with self.assertRaisesRegex(receiver.ReceiverError, "DEPLOY_EXECUTOR_UNAVAILABLE"):
            receiver.dispatch_deploy(receiver.validate_request(self.deploy_request(), self.CONTRACT),
                                     "/tmp/no-such-gace-deploy-socket")

    def test_receiver_maps_writer_replies(self):
        request = receiver.validate_request(self.deploy_request(), self.CONTRACT)
        ok = {"ok": True, "request_id": request["id"], "state": "SERVICE_DEPLOY_ACCEPTED"}
        with patch.object(receiver, "deploy_socket_call", return_value=ok):
            self.assertEqual(receiver.dispatch_deploy(request)["deploy_state"], "SERVICE_DEPLOY_ACCEPTED")
        for reply, status in (({"ok": False, "error": "DEPLOY_LOCK_BUSY"}, 503),
                              ({"ok": False, "error": "SERVICE_NOT_REGISTERED"}, 422)):
            with patch.object(receiver, "deploy_socket_call", return_value=reply):
                with self.assertRaises(receiver.ReceiverError) as raised:
                    receiver.dispatch_deploy(request)
                self.assertEqual(raised.exception.status, status)
        with patch.object(receiver, "deploy_socket_call", return_value={**ok, "request_id": "req_" + "9" * 24}):
            with self.assertRaisesRegex(receiver.ReceiverError, "DEPLOY_RESULT_MISMATCH"):
                receiver.dispatch_deploy(request)

    def test_status_requires_terminal_pass_and_exact_sha(self):
        status = receiver.validate_request(sender.validate_cli(
            "service.deploy_status", self.SHA, self.CONTRACT, deploy_request_id="req_" + "1" * 24), self.CONTRACT)
        passed = {"ok": True, "state": "SERVICE_DEPLOY_PASS", "source_sha": self.SHA, "service": "api",
                  "repository": "seigo-gace/webhook-gateway", "recreated": False, "http_health": "HTTP_200"}
        with patch.object(receiver, "deploy_socket_call", return_value=passed):
            self.assertEqual(receiver.dispatch_deploy_status(status)["state"], "SERVICE_DEPLOY_PASS")
        for reply, code, http in (
                ({"ok": True, "state": "RUNNING"}, "DEPLOY_IN_PROGRESS", 503),
                ({"ok": True, "state": "FAIL"}, "DEPLOY_FAILED_OR_SHA_MISMATCH", 422),
                ({**passed, "source_sha": "d" * 40}, "DEPLOY_FAILED_OR_SHA_MISMATCH", 422),
                ({"ok": False, "error": "DEPLOY_REQUEST_UNKNOWN"}, "DEPLOY_REQUEST_UNKNOWN", 422)):
            with patch.object(receiver, "deploy_socket_call", return_value=reply):
                with self.assertRaises(receiver.ReceiverError) as raised:
                    receiver.dispatch_deploy_status(status)
                self.assertEqual((raised.exception.code, raised.exception.status), (code, http))

    def test_committed_contract_registers_effects(self):
        from pathlib import Path
        contract = json.loads((Path(__file__).resolve().parents[1] / "operations" / "github-project-bounded-host.json").read_text())
        self.assertEqual(contract["command_effects"]["service.deploy"], "service_deploy")
        self.assertEqual(contract["command_effects"]["service.deploy_status"], "read_only")


if __name__ == "__main__":
    unittest.main()
