#!/usr/bin/env python3
"""Submit bounded Host requests through the existing Generic Internal Event API."""
import argparse
import json
import os
import re
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "operations" / "github-project-bounded-host.json"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class SendError(RuntimeError):
    pass


def load_contract(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        raise SendError("CONTRACT_JSON_INVALID") from None


def gateway_url(value):
    base = str(value or "").strip().rstrip("/")
    if not base:
        raise SendError("GATEWAY_URL_MISSING")
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SendError("GATEWAY_URL_INVALID")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SendError("GATEWAY_URL_INVALID")
    if base.endswith("/internal/events"):
        return base
    return base + "/internal/events"


def build_event(request, contract):
    transport = contract.get("transport") or {}
    return {
        "eventId": request["id"],
        "eventType": transport.get("event_type"),
        "sourceId": transport.get("source_id"),
        "destinationId": transport.get("destination_id"),
        "subject": "servercore-bounded-host/" + request["command_id"],
        "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": request,
    }


def validate_cli(command_id, expected_sha, contract):
    allowed = contract.get("allowed_command_ids") or []
    if command_id not in allowed:
        raise SendError("COMMAND_NOT_REGISTERED")
    if not SHA_PATTERN.match(expected_sha):
        raise SendError("EXPECTED_SHA_INVALID")
    return {
        "schema": contract.get("request_schema"),
        "id": "req_" + secrets.token_hex(12),
        "command_id": command_id,
        "expected_sha": expected_sha,
    }


def send(request, contract, *, env=None, opener=None):
    current = dict(os.environ if env is None else env)
    transport = contract.get("transport") or {}
    url = gateway_url(current.get(transport.get("gateway_url_env", "GACE_EVENT_GATEWAY_URL")))
    token = str(current.get(transport.get("gateway_token_env", "GACE_EVENT_GATEWAY_TOKEN")) or "").strip()
    if not token:
        raise SendError("GATEWAY_TOKEN_MISSING")
    body = json.dumps(build_event(request, contract), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    user_agent = str(
        current.get("GACE_EVENT_GATEWAY_USER_AGENT", "G-ACE-server-core-internal-event/1")
    ).strip()
    http_request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent or "G-ACE-server-core-internal-event/1",
        },
    )
    try:
        timeout = max(1, min(int(current.get("GACE_EVENT_GATEWAY_TIMEOUT_SECONDS", "10")), 30))
    except ValueError as exc:
        raise SendError("GATEWAY_TIMEOUT_INVALID") from exc
    client = opener or urllib.request.build_opener()
    try:
        with client.open(http_request, timeout=timeout) as response:
            status = int(getattr(response, "status", 0) or 0)
            payload = json.loads(response.read(65536))
    except urllib.error.HTTPError as exc:
        raise SendError(f"GATEWAY_HTTP_{exc.code}") from exc
    except Exception as exc:
        raise SendError("GATEWAY_TRANSPORT_FAILED") from exc
    if status != 202 or not isinstance(payload, dict) or payload.get("ok") is not True:
        raise SendError("GATEWAY_DURABLE_RECEIPT_INVALID")
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    contract = load_contract(args.contract)
    request = validate_cli(args.command_id, args.expected_sha, contract)
    try:
        receipt = send(request, contract)
        print(json.dumps({"state": "QUEUED", "request_id": request["id"], "gateway": receipt}, sort_keys=True))
        print(f"SERVERCORE_BOUNDED_HOST_COMMAND={request['command_id']}")
        print(f"SERVERCORE_BOUNDED_HOST_SHA={request['expected_sha']}")
        print("SERVERCORE_BOUNDED_HOST_GATEWAY=ACCEPTED")
        return 0
    except SendError as exc:
        print(json.dumps({"state": "FAIL", "failure_class": str(exc)}, sort_keys=True))
        print(f"SERVERCORE_BOUNDED_HOST_GATEWAY={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
