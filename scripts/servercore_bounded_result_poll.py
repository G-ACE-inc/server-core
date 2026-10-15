#!/usr/bin/env python3
"""Read the Host-published result of ONE bounded Host request id from the control Issue.

Runs inside the existing GitHub Actions job (GITHUB_TOKEN, issues: read) so the
CHAT-visible job log carries exact result markers correlated by request id.
Exit codes: 0 PASS, 1 Host FAIL, 2 result not returned in time, 3 correlation mismatch.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

MARKER = "GACE_BOUNDED_HOST_RESULT"
REQ_ID = re.compile(r"^req_[0-9a-f]{24}$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def gh_api(path):
    """Fetch only the newest 100 Issue comments, never the entire Issue history.

    GraphQL's comments(last:100) is bounded independent of Issue age. Normal
    polling happens every few seconds; a missing result is UNKNOWN, not PASS.
    """
    matched = re.match(r"^repos/([^/]+)/([^/]+)/issues/(\\d+)/comments(?:\\?.*)?$", path)
    if not matched:
        raise RuntimeError("INVALID_ISSUE_COMMENTS_PATH")
    owner, name, issue_number = matched.groups()
    query = (
        "query($owner:String!,$name:String!,$number:Int!){"
        "repository(owner:$owner,name:$name){"
        "issue(number:$number){comments(last:100){nodes{body url}}}}}"
    )
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", "query=" + query,
         "-F", "owner=" + owner, "-F", "name=" + name,
         "-F", "number=" + issue_number],
        capture_output=True, text=True, timeout=60, check=False,
    )
    if result.returncode:
        raise RuntimeError("GH_GRAPHQL_FAILED")
    try:
        payload = json.loads(result.stdout)
        nodes = payload["data"]["repository"]["issue"]["comments"]["nodes"]
        return [{"body": node.get("body") or "", "html_url": node.get("url") or ""}
                for node in nodes]
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("GH_GRAPHQL_RESULT_INVALID") from exc


def find_result(comments, request_id):
    needle = f"<!-- {MARKER} request_id={request_id} -->"
    for comment in comments:
        body = comment.get("body") or ""
        if needle in body:
            match = re.search(r"```json\n(.*?)\n```", body, re.S)
            if not match:
                continue
            try:
                return comment, json.loads(match.group(1))
            except ValueError:
                continue
    return None, None


def evaluate(record, request_id, command_id, expected_sha):
    if record.get("request_id") != request_id:
        return 3, "REQUEST_ID_MISMATCH"
    if record.get("command_id") != command_id and record.get("command_id") != "invalid.request":
        return 3, "COMMAND_MISMATCH"
    if record.get("expected_sha") not in (expected_sha, ""):
        return 3, "EXPECTED_SHA_MISMATCH"
    return (0 if record.get("state") == "PASS" and record.get("exit_code") == 0 else 1), "OK"



def continuation_observation(record, verdict):
    """Translate one verified Host result into a CHAT-visible observation.

    This is not automatic ChatGPT invocation, a permission grant, or a
    declaration that the user's development mission is finished.
    """
    if verdict != "OK":
        return "CORRELATION_FAILED", "INSPECT_RESULT_CORRELATION"
    if record.get("state") == "PASS" and record.get("exit_code") == 0:
        return "HOST_OPERATION_PASSED", "RECHECK_MISSION_ACCEPTANCE_AND_CONTINUE"
    stderr = str(record.get("stderr") or "")
    if "SOURCE_SHA_MISMATCH" in stderr:
        return "HOST_SOURCE_SHA_MISMATCH", "READBACK_HOST_SHA_AND_REPLAN_AUTHORIZED_ACTION"
    if record.get("state") == "FAIL":
        return "HOST_OPERATION_FAILED", "INSPECT_FAILURE_EVIDENCE_AND_REPLAN"
    return "HOST_RESULT_UNVERIFIED", "INSPECT_HOST_RESULT_AND_REPLAN"

def emit(record, comment, verdict):
    print(f"SERVERCORE_BOUNDED_HOST_RESULT={'RETURNED' if verdict == 'OK' else verdict}")
    print(f"SERVERCORE_BOUNDED_HOST_REQUEST_ID={record.get('request_id')}")
    print(f"SERVERCORE_BOUNDED_HOST_COMMAND={record.get('command_id')}")
    print(f"SERVERCORE_BOUNDED_HOST_STATE={record.get('state')}")
    print(f"SERVERCORE_BOUNDED_HOST_EXIT_CODE={record.get('exit_code')}")
    print(f"SERVERCORE_BOUNDED_HOST_SHA={record.get('host_sha') or 'NONE'}")
    print(f"SERVERCORE_BOUNDED_HOST_EXPECTED_SHA={record.get('expected_sha') or 'NONE'}")
    print(f"SERVERCORE_BOUNDED_HOST_RESULT_URL={comment.get('html_url')}")
    observation, next_action = continuation_observation(record, verdict)
    print(f"CHAT_HOST_OBSERVATION={observation}")
    print(f"CHAT_NEXT_ACTION={next_action}")
    for stream in ("stdout", "stderr"):
        text = str(record.get(stream) or "")
        print(f"SERVERCORE_BOUNDED_HOST_{stream.upper()}_BEGIN")
        print(text)
        print(f"SERVERCORE_BOUNDED_HOST_{stream.upper()}_END")


def main(argv=None, fetch=gh_api, sleep=time.sleep, clock=time.monotonic):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--interval", type=int, default=6)
    args = parser.parse_args(argv)
    if not REQ_ID.fullmatch(args.request_id) or not SHA.fullmatch(args.expected_sha):
        print("SERVERCORE_BOUNDED_HOST_RESULT=INPUT_INVALID")
        return 3
    since = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = f"repos/{args.repository}/issues/{args.issue}/comments?per_page=100&since={since}"
    deadline = clock() + max(1, min(args.timeout, 600))
    while True:
        try:
            comment, record = find_result(fetch(path), args.request_id)
        except (RuntimeError, ValueError, OSError):
            comment = record = None
        if record:
            code, verdict = evaluate(record, args.request_id, args.command_id, args.expected_sha)
            emit(record, comment, verdict)
            return code
        if clock() >= deadline:
            print("SERVERCORE_BOUNDED_HOST_RESULT=NOT_RETURNED")
            print(f"SERVERCORE_BOUNDED_HOST_REQUEST_ID={args.request_id}")
            return 2
        sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
