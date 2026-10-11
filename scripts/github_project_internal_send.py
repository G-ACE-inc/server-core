#!/usr/bin/env python3
import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from github_project_control import (
    DEFAULT_CONTRACT,
    load_json,
    validate_contract,
    validate_request,
)

DESTINATION_ID = "server-core-project-control"
EVENT_TYPE = "gace.github-project-control.requested"
SOURCE_ID = "server-core-github"


class SendError(RuntimeError):
    pass


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


def build_event(request):
    return {
        "eventId": request["id"],
        "eventType": EVENT_TYPE,
        "sourceId": SOURCE_ID,
        "destinationId": DESTINATION_ID,
        "subject": "github-project-control/" + request["field"].lower().replace(" ", "-"),
        "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": request,
    }


def send(request, *, env=None, opener=None):
    current = dict(os.environ if env is None else env)
    url = gateway_url(current.get("GACE_EVENT_GATEWAY_URL"))
    token = str(current.get("GACE_EVENT_GATEWAY_TOKEN") or "").strip()
    if not token:
        raise SendError("GATEWAY_TOKEN_MISSING")
    body = json.dumps(build_event(request), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
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
    if payload.get("duplicate") not in {True, False}:
        raise SendError("GATEWAY_DUPLICATE_STATE_INVALID")
    return {
        "duplicate": bool(payload["duplicate"]),
        "deliveries": int(payload.get("deliveries", 0)),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Submit bounded GitHub Project control request to Generic Internal Event API"
    )
    parser.add_argument("--request", required=True)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    try:
        contract = validate_contract(load_json(args.contract, "CONTRACT_JSON_INVALID"))
        request = validate_request(load_json(Path(args.request), "REQUEST_JSON_INVALID"), contract)
        result = send(request)
        print("GACE_RESULT_BEGIN")
        print("RESULT=PASS")
        print(f"REQUEST_ID={request['id']}")
        print(f"DESTINATION_ID={DESTINATION_ID}")
        print(f"DUPLICATE={'YES' if result['duplicate'] else 'NO'}")
        print(f"DELIVERIES={result['deliveries']}")
        print("GACE_RESULT_END")
        return 0
    except Exception as exc:
        print("GACE_RESULT_BEGIN")
        print("RESULT=FAIL")
        print(f"ERROR={str(exc)[:120]}")
        print("GACE_RESULT_END")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
