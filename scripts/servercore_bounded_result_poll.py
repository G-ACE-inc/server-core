#!/usr/bin/env python3
"""Read the Host-published result of ONE bounded Host request id from the control Issue.

Runs inside the existing GitHub Actions job (GITHUB_TOKEN, issues: read) so the
CHAT-visible job log carries exact result markers correlated by request id.
Exit codes: 0 PASS, 1 Host FAIL, 2 result not returned in time, 3 correlation mismatch.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

MARKER = "GACE_BOUNDED_HOST_RESULT"
REQ_ID = re.compile(r"^req_[0-9a-f]{24}$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def gh_api(path):
    """Read at most the newest two Issue comment pages; never paginate the whole Issue."""
    issue_path = path.split("/comments?", 1)[0]
    metadata = subprocess.run(["gh", "api", issue_path], capture_output=True,
                              text=True, timeout=20, check=False)
    if metadata.returncode:
        raise RuntimeError("GH_API_FAILED")
    count = int(json.loads(metadata.stdout).get("comments", 0))
    last_page = max(1, (count + 99) // 100)
    items = []
    for page in sorted({max(1, last_page - 1), last_page}):
        page_path = issue_path + f"/comments?per_page=100&page={page}"
        result = subprocess.run(["gh", "api", page_path], capture_output=True,
                                text=True, timeout=20, check=False)
        if result.returncode:
            raise RuntimeError("GH_API_FAILED")
        batch = json.loads(result.stdout)
        if not isinstance(batch, list):
            raise RuntimeError("GH_API_INVALID")
        items.extend(batch)
    return items


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
    # All public Issue records deliberately redact both streams to metadata.
    # Diagnose authenticated Host failure before checking partial previews:
    # otherwise every failed result with *_bytes is mislabelled "output partial".
    if record.get("state") == "RETRYABLE":
        return "HOST_OPERATION_RETRYABLE", "TRACE_EXISTING_HOST_DELIVERY_AND_RESULT_SINK"
    failed = record.get("state") == "FAIL" or (
        type(record.get("exit_code")) is int and record["exit_code"] != 0)
    if failed:
        hint = record.get("diagnostic_hint")
        if record.get("exit_code") == 74 and hint == "CHAT_SOURCE_SHA_MISMATCH":
            return "HOST_SOURCE_CONTEXT_STALE", "REFRESH_TARGET_PR_HEAD_AND_REPLAN"
        if hint in {
                "CHAT_SOURCE_WORKDIR_MISSING", "CHAT_SOURCE_GIT_UNAVAILABLE",
                "CHAT_SOURCE_ROOT_MISMATCH", "CHAT_SOURCE_SHA_UNAVAILABLE",
                "CHAT_SOURCE_REQUIRED_FILE_MISSING"}:
            return "HOST_SOURCE_CONTEXT_INVALID", "CHECK_TARGET_WORKDIR_AND_SOURCE_FILES"
        host_sha = record.get("host_sha")
        expected_sha = record.get("expected_sha")
        if (isinstance(host_sha, str) and isinstance(expected_sha, str)
                and re.fullmatch(r"[a-f0-9]{40}", host_sha)
                and re.fullmatch(r"[a-f0-9]{40}", expected_sha)
                and host_sha != expected_sha):
            return "HOST_SOURCE_SHA_MISMATCH", "READBACK_HOST_SHA_AND_REPLAN_AUTHORIZED_ACTION"
        # Legacy complete stderr may explicitly say SOURCE_SHA_MISMATCH while
        # its old receipt lacks the true Host SHA. Keep the diagnostic hint,
        # but never treat it as proved: artifact restore/continuation demands
        # independently different authenticated Host and expected SHAs.
        if (str(record.get("stderr") or "").strip() == "SOURCE_SHA_MISMATCH"
                and not any(k + "_bytes" in record for k in ("stdout", "stderr"))):
            return "HOST_SOURCE_SHA_MISMATCH", "READBACK_HOST_SHA_AND_REPLAN_AUTHORIZED_ACTION"
        return "HOST_OPERATION_FAILED", "INSPECT_FAILURE_EVIDENCE_AND_REPLAN"
    if any(record.get(stream + "_preview_truncated") or record.get(stream + "_truncated") for stream in ("stdout", "stderr")):
        return "HOST_OUTPUT_PARTIAL", "READ_STORED_HOST_OUTPUT_CHUNKS_AND_CONTINUE"
    if any(stream + "_bytes" in record for stream in ("stdout", "stderr")):
        return "HOST_LEDGER_RECOVERY_REQUIRED", "READ_STORED_HOST_OUTPUT_CHUNKS_AND_CONTINUE"
    if record.get("state") == "PASS" and record.get("exit_code") == 0:
        return "HOST_OPERATION_PASSED", "RECHECK_MISSION_ACCEPTANCE_AND_CONTINUE"
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
        partial = bool(record.get(stream + "_preview_truncated") or record.get(stream + "_truncated") or stream + "_bytes" in record)
        print(f"CHAT_HOST_{stream.upper()}_COMPLETE={str(not partial).upper()}")
        if stream + "_sha256" in record:
            print(f"CHAT_HOST_{stream.upper()}_SHA256={record[stream + '_sha256']}")
        if stream + "_chars" in record:
            print(f"CHAT_HOST_{stream.upper()}_CHARS={record[stream + '_chars']}")
    # A metadata-only Issue record is a pointer to the Host ledger, not an
    # empty stdout/stderr result. Never misrepresent it as the full payload.
    metadata_only = any(stream + "_bytes" in record for stream in ("stdout", "stderr"))
    if metadata_only:
        print("CHAT_HOST_OUTPUT_TRANSPORT=HOST_LEDGER_ONLY")
        print(f"CHAT_HOST_OUTPUT_RECORD_REQUEST_ID={record.get('request_id')}")
        for stream in ("stdout", "stderr"):
            print(f"CHAT_HOST_{stream.upper()}_BYTES={record.get(stream + '_bytes', 'UNKNOWN')}")
        return
    for stream in ("stdout", "stderr"):
        text = str(record.get(stream) or "")
        print(f"SERVERCORE_BOUNDED_HOST_{stream.upper()}_BEGIN")
        print(text)
        print(f"SERVERCORE_BOUNDED_HOST_{stream.upper()}_END")


def stream_receipt_metadata(record, stream):
    """Prefer Host-ledger digests, fall back ONLY to complete legacy previews."""
    raw = record.get(stream)
    digest = record.get(stream + "_sha256")
    chars = record.get(stream + "_chars")
    # Older Host publishers supplied complete small text previews but no SHA.
    # Never hash an empty preview for a metadata-only ledger pointer or a
    # truncated preview: it would misrepresent the actual Host output.
    if (digest is None and chars is None and isinstance(raw, str)
            and stream + "_bytes" not in record
            and not record.get(stream + "_preview_truncated")
            and not record.get(stream + "_truncated")):
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        chars = len(raw)
    return {"chars": chars, "sha256": digest,
            "complete": not bool(
                record.get(stream + "_preview_truncated") or
                record.get(stream + "_truncated") or
                stream + "_bytes" in record)}


def write_observation(path, request_id, record=None, comment=None, verdict=None):
    """Durable, secret-free receipt; never include stdout/stderr or private command text."""
    if not path:
        return
    if record is None:
        receipt = {"request_id": request_id, "observation": "HOST_RESULT_NOT_RETURNED",
                   "next_action": "INSPECT_HOST_DISPATCH_AND_REPLAN", "result_verified": False}
    else:
        observation, next_action = continuation_observation(record, verdict)
        receipt = {"request_id": request_id, "command_id": record.get("command_id"),
                   "state": record.get("state"), "exit_code": record.get("exit_code"),
                   "expected_sha": record.get("expected_sha"), "host_sha": record.get("host_sha"),
                   "result_url": (comment or {}).get("html_url"), "observation": observation,
                   "next_action": next_action, "result_verified": verdict == "OK",
                   "diagnostic_hint": record.get("diagnostic_hint"),
                   "streams": {stream: stream_receipt_metadata(record, stream)
                               for stream in ("stdout", "stderr")}}
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main(argv=None, fetch=gh_api, sleep=time.sleep, clock=time.monotonic):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--observation-json", default=None)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--interval", type=int, default=6)
    args = parser.parse_args(argv)
    if not REQ_ID.fullmatch(args.request_id) or not SHA.fullmatch(args.expected_sha):
        print("SERVERCORE_BOUNDED_HOST_RESULT=INPUT_INVALID")
        return 3
    since = (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = f"repos/{args.repository}/issues/{args.issue}/comments?per_page=100&since={since}"
    deadline = clock() + max(1, min(args.timeout, 600))
    api_failures = 0
    successful_reads = 0
    while True:
        try:
            comment, record = find_result(fetch(path), args.request_id)
            successful_reads += 1
        except (RuntimeError, ValueError, OSError):
            api_failures += 1
            comment = record = None
        if record:
            code, verdict = evaluate(record, args.request_id, args.command_id, args.expected_sha)
            emit(record, comment, verdict)
            write_observation(args.observation_json, args.request_id, record, comment, verdict)
            return code
        if clock() >= deadline:
            print("SERVERCORE_BOUNDED_HOST_RESULT=NOT_RETURNED")
            print(f"SERVERCORE_BOUNDED_HOST_REQUEST_ID={args.request_id}")
            print(f"SERVERCORE_BOUNDED_HOST_ISSUE_API_READS={successful_reads}")
            print(f"SERVERCORE_BOUNDED_HOST_ISSUE_API_FAILURES={api_failures}")
            if api_failures and not successful_reads:
                print("SERVERCORE_BOUNDED_HOST_FAILURE_CLASS=ISSUE_API_UNAVAILABLE")
            elif api_failures:
                print("SERVERCORE_BOUNDED_HOST_FAILURE_CLASS=ISSUE_API_INTERMITTENT")
            else:
                print("SERVERCORE_BOUNDED_HOST_FAILURE_CLASS=REQUEST_RESULT_NOT_FOUND")
            write_observation(args.observation_json, args.request_id)
            return 2
        sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
