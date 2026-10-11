#!/usr/bin/env python3
import argparse
import json
import os
import re
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from gace_internal_delivery_auth import DeliveryAuthError, read_delivery_key, verify_delivery

import servercore_bounded_host as bounded_host

RECEIVER_PATH = "/internal/servercore-bounded-host"
HEALTH_PATH = "/healthz"
EXPECTED_DESTINATION = "server-core-bounded-host"
MAX_BODY_BYTES = 4096
DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "operations" / "github-project-bounded-host.json"
REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{24}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class ReceiverError(RuntimeError):
    def __init__(self, code, status):
        super().__init__(code)
        self.code = code
        self.status = status


def fail(code, status):
    raise ReceiverError(code, status)


def load_contract(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit("CONTRACT_JSON_INVALID") from exc


def validate_request(value, contract):
    if not isinstance(value, dict):
        fail("REQUEST_SHAPE_INVALID", 422)
    if value.get("schema") != contract.get("request_schema"):
        fail("REQUEST_SCHEMA_INVALID", 422)
    req_id = value.get("id")
    if not isinstance(req_id, str) or not REQUEST_ID_PATTERN.match(req_id):
        fail("REQUEST_ID_INVALID", 422)
    command_id = value.get("command_id")
    allowed = contract.get("allowed_command_ids") or []
    if command_id not in allowed:
        fail("COMMAND_NOT_REGISTERED", 422)
    expected_sha = value.get("expected_sha")
    if not isinstance(expected_sha, str) or not SHA_PATTERN.match(expected_sha):
        fail("EXPECTED_SHA_INVALID", 422)
    if command_id == "project.source_reflect":
        if set(value) != {"schema", "id", "command_id", "expected_sha", "expected_before"}:
            fail("REFLECT_KEYS_INVALID", 422)
        before = value["expected_before"]
        if not isinstance(before, str) or not SHA_PATTERN.match(before):
            fail("REFLECT_BEFORE_INVALID", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha,
                "expected_before": before}
    if set(value) != {"schema", "id", "command_id", "expected_sha"}:
        fail("REQUEST_KEYS_INVALID", 422)
    return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha}


def dispatch_reflect(request, socket_path="/run/gace/servercore-source-reflect.sock"):
    payload = {
        "schema": "gace.servercore-source-reflect.request/v1",
        "id": request["id"],
        "repository": "G-ACE-inc/server-core",
        "branch": "main",
        "expected_before": request["expected_before"],
        "target_sha": request["expected_sha"],
    }
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(120)
            client.connect(socket_path)
            client.sendall(data)
            with client.makefile("rb") as stream:
                result = json.loads(stream.readline(4096))
    except (OSError, ValueError, TypeError):
        fail("REFLECT_EXECUTOR_UNAVAILABLE", 503)
    if not isinstance(result, dict) or result.get("ok") is not True:
        fail("REFLECT_EXECUTION_FAILED", 503)
    if result.get("request_id") != request["id"] or result.get("target_sha") != request["expected_sha"]:
        fail("REFLECT_RESULT_MISMATCH", 503)
    if result.get("state") != "SOURCE_REFLECT_PASS":
        fail("REFLECT_RESULT_INVALID", 503)
    return {"source_sha": result["target_sha"], "command_id": request["command_id"],
            "source_reflect": True, "read_only": False}


def make_handler(contract, *, delivery_key=None, now_fn=None):
    root = Path(contract.get("canonical_host_root") or bounded_host.CANONICAL_ROOT)

    class Handler(BaseHTTPRequestHandler):
        server_version = "gace-servercore-bounded-host/1"

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
            self.send_json(200, {"ok": True, "service": "servercore-bounded-host"})

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
                tolerance = int(os.environ.get("GACE_BOUNDED_HOST_SIGNATURE_TOLERANCE_SECONDS", "300"))
                verify_delivery(
                    headers,
                    body,
                    expected_destination=EXPECTED_DESTINATION,
                    delivery_key=delivery_key,
                    now=now_fn() if now_fn else None,
                    tolerance_seconds=tolerance,
                )
                request = validate_request(json.loads(body.decode("utf-8")), contract)
                if request["command_id"] == "project.source_reflect":
                    result = dispatch_reflect(request)
                else:
                    result = bounded_host.execute(
                        request["command_id"],
                        root=root,
                        expected_sha=request["expected_sha"],
                    )
                self.send_json(
                    200,
                    {
                        "ok": True,
                        "request_id": request["id"],
                        "state": "PASS",
                        "command_id": request["command_id"],
                        "source_sha": result.get("source_sha"),
                        "read_only": bool(result.get("read_only", True)),
                        "result": result,
                    },
                    accepted=True,
                )
            except DeliveryAuthError as exc:
                self.send_json(exc.status, {"ok": False, "error": exc.code})
            except ReceiverError as exc:
                self.send_json(exc.status, {"ok": False, "error": exc.code})
            except bounded_host.BoundaryError as exc:
                self.send_json(422, {"ok": False, "error": str(exc), "state": "FAIL"})
            except Exception:
                self.send_json(500, {"ok": False, "error": "INTERNAL_ERROR"})

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Bounded internal HTTP receiver for server-core Host primitive")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8789)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    if args.port < 1 or args.port > 65535:
        raise SystemExit("PORT_INVALID")
    contract = load_contract(args.contract)
    delivery_key = read_delivery_key(env_prefix="GACE_BOUNDED_HOST")
    server = ThreadingHTTPServer((args.host, args.port), make_handler(contract, delivery_key=delivery_key))
    server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
