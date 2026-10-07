#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import github_project_internal_receiver as receiver
import github_project_internal_send as sender

CONTRACT = {
    "schema_version": "1.0",
    "name": "gace-github-project-control",
    "request_schema": "gace.github-project-control/v1",
    "request_actor": "seigo-gace",
    "project": {
        "owner": "seigo-gace",
        "number": 1,
        "node_id": "PVT_kwHODOQFoM4BEJII",
        "title": "G-ACE Development Platform",
    },
    "allowed_repository_owners": ["seigo-gace", "G-ACE-inc"],
    "allowed_fields": {
        "Wave": {"max_length": 16, "pattern": "Wave [0-9]{1,2}"},
        "Gate": {"max_length": 64, "pattern": "[A-Z][A-Z0-9_]{0,63}"},
        "Change Unit": {"max_length": 160},
        "Mutation Owner": {"max_length": 120},
    },
    "timeouts": {"command_seconds": 30},
    "internal_event_transport": {
        "result_sink": {
            "repository": "G-ACE-inc/server-core",
            "issue_number": 10,
            "dedupe_window_comments": 100,
        }
    },
}


def request_payload():
    return {
        "schema": "gace.github-project-control/v1",
        "id": "gpc_0123456789abcdef01234567",
        "actor": "seigo-gace",
        "operation": "set_field",
        "item_url": "https://github.com/G-ACE-inc/server-core/issues/10",
        "field": "Gate",
        "value": "CI_PASS",
    }


def signed_headers(body, secret=b"delivery-secret", now=1700000000):
    message_id = "delivery-123"
    timestamp = str(now)
    digest = hmac.new(
        secret,
        message_id.encode() + b"." + timestamp.encode() + b"." + body,
        hashlib.sha256,
    ).digest()
    return {
        "Content-Type": "application/json",
        "x-gace-destination": receiver.EXPECTED_DESTINATION,
        "webhook-id": message_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": "v1," + base64.b64encode(digest).decode(),
    }


class FakeResponse:
    def __init__(self, payload, status=202):
        self.status = status
        self.payload = json.dumps(payload).encode()

    def read(self, _limit=-1):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout=None):
        self.request = request
        self.timeout = timeout
        return self.response


class InternalTransportTests(unittest.TestCase):
    def test_sender_uses_internal_api_and_fixed_destination(self):
        opener = FakeOpener(FakeResponse({"ok": True, "duplicate": False, "deliveries": 1}))
        result = sender.send(
            request_payload(),
            env={
                "GACE_EVENT_GATEWAY_URL": "https://gateway.example.test",
                "GACE_EVENT_GATEWAY_TOKEN": "test-token",
            },
            opener=opener,
        )
        self.assertEqual(result, {"duplicate": False, "deliveries": 1})
        self.assertEqual(opener.request.full_url, "https://gateway.example.test/internal/events")
        body = json.loads(opener.request.data)
        self.assertEqual(body["destinationId"], "server-core-project-control")
        self.assertEqual(body["data"], request_payload())
        self.assertNotIn("test-token", opener.request.data.decode())

    def test_receiver_verifies_standard_webhook_signature(self):
        body = json.dumps(request_payload(), separators=(",", ":")).encode()
        headers = {key.lower(): value for key, value in signed_headers(body).items()}
        receiver.verify_delivery(headers, body, secret=b"delivery-secret", now=1700000000)
        headers["webhook-signature"] = "v1," + base64.b64encode(b"x" * 32).decode()
        with self.assertRaisesRegex(receiver.ReceiverError, "DELIVERY_SIGNATURE_INVALID"):
            receiver.verify_delivery(headers, body, secret=b"delivery-secret", now=1700000000)

    def test_receiver_rejects_stale_delivery(self):
        body = json.dumps(request_payload(), separators=(",", ":")).encode()
        headers = {key.lower(): value for key, value in signed_headers(body).items()}
        with self.assertRaisesRegex(receiver.ReceiverError, "DELIVERY_TIMESTAMP_OUT_OF_RANGE"):
            receiver.verify_delivery(headers, body, secret=b"delivery-secret", now=1700001000)

    def test_receiver_executes_only_valid_project_control_request(self):
        calls = []
        def fake_execute(request, _contract):
            calls.append(request)
            return {"REQUEST_ID":request["id"],"READBACK":request["value"],"MUTATION_PERFORMED":"YES"}
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            receiver.make_handler(
                CONTRACT, secret=b"delivery-secret", execute_fn=fake_execute,
                publish_fn=lambda _request, _result, _contract: "PUBLISHED",
                now_fn=lambda:1700000000,
            ),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body=json.dumps(request_payload(),separators=(",",":")).encode()
            request=urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}{receiver.RECEIVER_PATH}",
                data=body,method="POST",headers=signed_headers(body),
            )
            with urllib.request.urlopen(request) as response:
                payload=json.loads(response.read())
                self.assertEqual(response.status,200)
                self.assertEqual(response.headers["x-gace-accepted"],"true")
            self.assertEqual(payload["result_evidence"],"PUBLISHED")
            self.assertEqual(len(calls),1)

            bad=request_payload()
            bad["field"]="Forbidden"
            bad_body=json.dumps(bad,separators=(",",":")).encode()
            bad_request=urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}{receiver.RECEIVER_PATH}",
                data=bad_body,method="POST",headers=signed_headers(bad_body),
            )
            with self.assertRaises(urllib.error.HTTPError) as context:
                urllib.request.urlopen(bad_request)
            self.assertEqual(context.exception.code,422)
            self.assertEqual(len(calls),1)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)

    def test_result_comment_is_bounded_and_deduplicated(self):
        calls=[]
        def fake_gh(args,_contract):
            calls.append(args)
            if args[:2]==["api","graphql"]:
                return json.dumps({"data":{"repository":{"issue":{"comments":{"nodes":[]}}}}})
            return json.dumps({"id":1})
        result={"REQUEST_ID":request_payload()["id"],"READBACK":"CI_PASS","MUTATION_PERFORMED":"YES"}
        state=receiver.publish_result_comment(request_payload(),result,CONTRACT,gh_fn=fake_gh)
        self.assertEqual(state,"PUBLISHED")
        self.assertEqual(len(calls),2)
        posted=next(arg for arg in calls[1] if arg.startswith("body="))
        self.assertIn("PROJECT_CONTROL_EXECUTION: PASS",posted)
        self.assertIn(request_payload()["id"],posted)
        self.assertNotIn("delivery-secret",posted)

        marker=f"<!-- gace-project-control-result:{request_payload()['id']} -->"
        calls.clear()
        def already_gh(args,_contract):
            calls.append(args)
            return json.dumps({"data":{"repository":{"issue":{"comments":{"nodes":[{"body":marker}]}}}}})
        state=receiver.publish_result_comment(request_payload(),result,CONTRACT,gh_fn=already_gh)
        self.assertEqual(state,"ALREADY_PUBLISHED")
        self.assertEqual(len(calls),1)

    def test_receiver_maps_operational_failure_to_retryable_status(self):
        def fake_execute(_request,_contract):
            from github_project_control import ControlError
            raise ControlError("GH_COMMAND_TIMEOUT")
        server=ThreadingHTTPServer(
            ("127.0.0.1",0),
            receiver.make_handler(
                CONTRACT,secret=b"delivery-secret",execute_fn=fake_execute,
                publish_fn=lambda _request,_result,_contract:"PUBLISHED",
                now_fn=lambda:1700000000,
            ),
        )
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            body=json.dumps(request_payload(),separators=(",",":")).encode()
            request=urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}{receiver.RECEIVER_PATH}",
                data=body,method="POST",headers=signed_headers(body),
            )
            with self.assertRaises(urllib.error.HTTPError) as context:
                urllib.request.urlopen(request)
            self.assertEqual(context.exception.code,503)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


if __name__=="__main__":
    unittest.main()
