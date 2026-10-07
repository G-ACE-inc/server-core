#!/usr/bin/env python3
import argparse
import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from github_project_control import (
    ControlError,
    DEFAULT_CONTRACT,
    execute,
    gh_run,
    load_json,
    parse_json,
    validate_contract,
    validate_request,
)

RECEIVER_PATH = "/internal/github-project-control"
HEALTH_PATH = "/healthz"
EXPECTED_DESTINATION = "server-core-project-control"
MAX_BODY_BYTES = 16_384
DEFAULT_TOLERANCE_SECONDS = 300
RESULT_COMMENTS_QUERY = """query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      comments(last: 100) {
        nodes { body }
      }
    }
  }
}"""


class ReceiverError(RuntimeError):
    def __init__(self, code, status):
        super().__init__(code)
        self.code = code
        self.status = status


def fail(code, status):
    raise ReceiverError(code, status)


def decode_secret(value):
    if not isinstance(value, str) or not value:
        fail("DELIVERY_SECRET_MISSING", 503)
    if value.startswith("base64:"):
        try:
            decoded = base64.b64decode(value[len("base64:"):], validate=True)
        except (binascii.Error, ValueError):
            fail("DELIVERY_SECRET_INVALID", 503)
        if not decoded:
            fail("DELIVERY_SECRET_INVALID", 503)
        return decoded
    return value.encode("utf-8")


def read_secret():
    value = os.environ.get("GACE_PROJECT_CONTROL_DELIVERY_SECRET")
    file_path = os.environ.get("GACE_PROJECT_CONTROL_DELIVERY_SECRET_FILE")
    if value and file_path:
        fail("DELIVERY_SECRET_SOURCE_AMBIGUOUS", 503)
    if file_path:
        try:
            value = Path(file_path).read_text(encoding="utf-8").strip()
        except Exception:
            fail("DELIVERY_SECRET_FILE_UNREADABLE", 503)
    return decode_secret(value)


def verify_delivery(headers, body, *, secret=None, now=None, tolerance_seconds=None):
    if headers.get("x-gace-destination") != EXPECTED_DESTINATION:
        fail("DELIVERY_DESTINATION_INVALID", 401)
    message_id = headers.get("webhook-id")
    timestamp = headers.get("webhook-timestamp")
    signature = headers.get("webhook-signature")
    if not message_id or not timestamp or not signature:
        fail("DELIVERY_SIGNATURE_HEADERS_MISSING", 401)
    try:
        timestamp_int = int(timestamp)
    except ValueError:
        fail("DELIVERY_TIMESTAMP_INVALID", 401)
    current = int(time.time() if now is None else now)
    tolerance = DEFAULT_TOLERANCE_SECONDS if tolerance_seconds is None else int(tolerance_seconds)
    if tolerance < 1 or tolerance > 900:
        fail("DELIVERY_TOLERANCE_INVALID", 503)
    if abs(current - timestamp_int) > tolerance:
        fail("DELIVERY_TIMESTAMP_OUT_OF_RANGE", 401)
    if not signature.startswith("v1,"):
        fail("DELIVERY_SIGNATURE_INVALID", 401)
    try:
        supplied = base64.b64decode(signature[3:], validate=True)
    except (binascii.Error, ValueError):
        fail("DELIVERY_SIGNATURE_INVALID", 401)
    key = read_secret() if secret is None else secret
    expected = hmac.new(
        key,
        message_id.encode() + b"." + timestamp.encode() + b"." + body,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(supplied, expected):
        fail("DELIVERY_SIGNATURE_INVALID", 401)


def parse_request_body(body, contract):
    try:
        value = json.loads(body.decode("utf-8"))
    except Exception:
        fail("DELIVERY_JSON_INVALID", 422)
    try:
        return validate_request(value, contract)
    except ControlError as exc:
        fail(str(exc), 422)


def execution_status(code):
    if code in {"PROJECT_CONTROL_BUSY", "GH_COMMAND_TIMEOUT", "GH_COMMAND_FAILED", "GH_DEPENDENCY_MISSING"}:
        return 503
    if code.startswith("PROJECT_") or code.startswith("GH_"):
        return 503
    return 500


def publish_result_comment(request, result, contract, *, gh_fn=gh_run):
    sink = contract["internal_event_transport"]["result_sink"]
    repository = sink["repository"]
    owner, name = repository.split("/", 1)
    issue_number = int(sink["issue_number"])
    marker = f"<!-- gace-project-control-result:{request['id']} -->"
    raw = gh_fn(
        [
            "api", "graphql",
            "-f", "query=" + RESULT_COMMENTS_QUERY,
            "-f", "owner=" + owner,
            "-f", "name=" + name,
            "-F", "number=" + str(issue_number),
        ],
        contract,
    )
    data = parse_json(raw, "RESULT_SINK_READBACK_JSON_INVALID")
    try:
        nodes = data["data"]["repository"]["issue"]["comments"]["nodes"]
    except Exception:
        fail("RESULT_SINK_READBACK_INVALID", 503)
    if not isinstance(nodes, list):
        fail("RESULT_SINK_READBACK_INVALID", 503)
    if any(isinstance(node, dict) and marker in str(node.get("body") or "") for node in nodes):
        return "ALREADY_PUBLISHED"

    body = "\n".join([
        marker,
        "G-ACE Project control execution completed.",
        "",
        f"- REQUEST_ID: {request['id']}",
        "- PROJECT_CONTROL_EXECUTION: PASS",
        f"- ITEM_URL: {request['item_url']}",
        f"- FIELD: {request['field']}",
        f"- VALUE: {request['value']}",
        f"- READBACK: {result.get('READBACK')}",
        f"- MUTATION_PERFORMED: {result.get('MUTATION_PERFORMED')}",
        "- RUNTIME_EVIDENCE: receiver execution + exact Project field readback",
    ])
    gh_fn(
        ["api", f"repos/{repository}/issues/{issue_number}/comments", "-f", "body=" + body],
        contract,
    )
    return "PUBLISHED"


def make_handler(
    contract,
    *,
    secret=None,
    execute_fn=execute,
    publish_fn=publish_result_comment,
    now_fn=time.time,
):
    class Handler(BaseHTTPRequestHandler):
        server_version = "gace-project-control/1"

        def log_message(self, _format, *_args):
            return

        def send_json(self, status, payload, *, accepted=False):
            data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            if accepted:
                self.send_header("x-gace-accepted", "true")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path != HEALTH_PATH:
                self.send_json(404, {"ok": False, "error": "NOT_FOUND"})
                return
            self.send_json(200, {"ok": True, "service": "github-project-control"})

        def do_POST(self):
            if self.path != RECEIVER_PATH:
                self.send_json(404, {"ok": False, "error": "NOT_FOUND"})
                return
            raw_length = self.headers.get("content-length")
            try:
                length = int(raw_length or "")
            except ValueError:
                self.send_json(411, {"ok": False, "error": "CONTENT_LENGTH_REQUIRED"})
                return
            if length < 1 or length > MAX_BODY_BYTES:
                self.send_json(413, {"ok": False, "error": "BODY_SIZE_INVALID"})
                return
            body = self.rfile.read(length)
            headers = {key.lower(): value for key, value in self.headers.items()}
            try:
                tolerance = int(os.environ.get(
                    "GACE_PROJECT_CONTROL_SIGNATURE_TOLERANCE_SECONDS",
                    str(DEFAULT_TOLERANCE_SECONDS),
                ))
                verify_delivery(headers, body, secret=secret, now=now_fn(), tolerance_seconds=tolerance)
                request = parse_request_body(body, contract)
                result = execute_fn(request, contract)
                evidence = publish_fn(request, result, contract)
                self.send_json(
                    200,
                    {
                        "ok": True,
                        "request_id": result.get("REQUEST_ID"),
                        "readback": result.get("READBACK"),
                        "mutation_performed": result.get("MUTATION_PERFORMED"),
                        "result_evidence": evidence,
                    },
                    accepted=True,
                )
            except ReceiverError as exc:
                self.send_json(exc.status, {"ok": False, "error": exc.code})
            except ControlError as exc:
                code = str(exc)[:120]
                self.send_json(execution_status(code), {"ok": False, "error": code})
            except Exception:
                self.send_json(500, {"ok": False, "error": "INTERNAL_ERROR"})

    return Handler


def main():
    parser = argparse.ArgumentParser(
        description="Bounded internal HTTP receiver for GitHub Project #1 control"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()

    if args.port < 1 or args.port > 65535:
        raise SystemExit("PORT_INVALID")
    contract = validate_contract(load_json(args.contract, "CONTRACT_JSON_INVALID"))
    secret = read_secret()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(contract, secret=secret))
    server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
