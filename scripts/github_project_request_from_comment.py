#!/usr/bin/env python3
import hashlib
import json
import re
import sys
from pathlib import Path

PREFIX = "[GACE-PROJECT]"
AUTHORIZED_LOGIN = "seigo-gace"
CONTROL_REPOSITORY = "G-ACE-inc/server-core"
ALLOWED_KEYS = {"item_url", "field", "value"}
SECRET_LIKE = re.compile(
    r"(?:Bearer\s+[A-Za-z0-9._~+/=-]{8,}|"
    r"(?:api[_-]?key|secret|password|access[_-]?token|refresh[_-]?token)"
    r"\s*[:=]\s*['\"]?[^\s'\",}]{8,})",
    re.IGNORECASE,
)


class RequestBuildError(RuntimeError):
    pass


def fail(code):
    raise RequestBuildError(code)


def parse_comment_event(event):
    if not isinstance(event, dict):
        fail("EVENT_INVALID")
    repository = event.get("repository")
    if not isinstance(repository, dict) or repository.get("full_name") != CONTROL_REPOSITORY:
        fail("CONTROL_REPOSITORY_INVALID")

    comment = event.get("comment")
    issue = event.get("issue")
    if not isinstance(comment, dict) or not isinstance(issue, dict):
        fail("COMMENT_EVENT_INVALID")

    user = comment.get("user")
    if not isinstance(user, dict) or user.get("login") != AUTHORIZED_LOGIN:
        fail("COMMENT_ACTOR_NOT_ALLOWED")

    body = comment.get("body")
    if not isinstance(body, str) or not body.startswith(PREFIX):
        fail("COMMENT_PREFIX_INVALID")
    raw = body[len(PREFIX):].strip()
    if not raw:
        fail("COMMENT_PAYLOAD_MISSING")

    try:
        payload = json.loads(raw)
    except Exception:
        fail("COMMENT_JSON_INVALID")
    if not isinstance(payload, dict):
        fail("COMMENT_PAYLOAD_INVALID")
    if set(payload) != ALLOWED_KEYS:
        fail("COMMENT_KEYS_INVALID")

    for key in ("item_url", "field", "value"):
        if not isinstance(payload[key], str) or not payload[key]:
            fail(f"COMMENT_{key.upper()}_INVALID")
    if any(SECRET_LIKE.search(payload[key]) for key in ("item_url", "field", "value")):
        fail("COMMENT_SECRET_LIKE_VALUE_REJECTED")

    comment_id = comment.get("id")
    issue_number = issue.get("number")
    if not isinstance(comment_id, int) or comment_id < 1:
        fail("COMMENT_ID_INVALID")
    if not isinstance(issue_number, int) or issue_number < 1:
        fail("ISSUE_NUMBER_INVALID")

    seed = f"{CONTROL_REPOSITORY}:{issue_number}:{comment_id}".encode("utf-8")
    request_id = "gpc_" + hashlib.sha256(seed).hexdigest()[:24]

    request = {
        "schema": "gace.github-project-control/v1",
        "id": request_id,
        "actor": AUTHORIZED_LOGIN,
        "operation": "set_field",
        "item_url": payload["item_url"],
        "field": payload["field"],
        "value": payload["value"],
    }
    meta = {
        "schema": "gace.github-project-control-comment/v1",
        "request_id": request_id,
        "source_repository": CONTROL_REPOSITORY,
        "source_issue_number": issue_number,
        "source_comment_id": comment_id,
        "source_actor": AUTHORIZED_LOGIN,
        "execution": "NOT_RUN",
    }
    return request, meta


def main():
    if len(sys.argv) != 4:
        fail("USAGE_ERROR")
    event_path, request_path, meta_path = map(Path, sys.argv[1:])
    try:
        event = json.loads(event_path.read_text(encoding="utf-8"))
        request, meta = parse_comment_event(event)
        request_path.write_text(json.dumps(request, ensure_ascii=False) + "\n", encoding="utf-8")
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"REQUEST_ID={request['id']}")
        print("COMMENT_REQUEST_BUILD=PASS")
        return 0
    except RequestBuildError as exc:
        print(f"COMMENT_REQUEST_BUILD=FAIL ERROR={str(exc)[:120]}")
        return 2
    except Exception:
        print("COMMENT_REQUEST_BUILD=FAIL ERROR=UNEXPECTED")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
