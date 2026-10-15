#!/usr/bin/env python3
"""Resume an existing CU handoff with a real read-only next Tool action.

Uses existing GitHub CLI credentials; never scans Issue comments, redispatches
Host work, or invents a new workflow. A step is complete only after API readback.
"""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

try:
    from scripts.chat_host_observation_gh_restore import continuation_checkpoint, restore
except ModuleNotFoundError:
    from chat_host_observation_gh_restore import continuation_checkpoint, restore

RUN_URL = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/actions/runs/([1-9][0-9]*)\Z")


def api_read(path, run=subprocess.run):
    p = run(["gh", "api", path], capture_output=True, text=True, timeout=30, check=True)
    return json.loads(p.stdout)


def resume(checkpoint, api=api_read):
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != "gace.chat.cu.handoff.v1":
        raise ValueError("INVALID_CHECKPOINT_SCHEMA")
    run_id = checkpoint.get("run_id")
    source_sha = checkpoint.get("source_sha")
    request_id = checkpoint.get("request_id")
    url = checkpoint.get("next_tool_target")
    matched = RUN_URL.fullmatch(url) if isinstance(url, str) else None
    if not matched or type(run_id) is not int or int(matched.group(2)) != run_id:
        raise ValueError("RUN_TARGET_MISMATCH")
    repository = matched.group(1)
    if repository != checkpoint.get("repository"):
        raise ValueError("REPOSITORY_MISMATCH")
    # The next Tool action is an actual fresh call, never simply a string recommendation.
    current = api(f"repos/{repository}/actions/runs/{run_id}")
    if current.get("head_sha") != source_sha or not isinstance(source_sha, str):
        raise ValueError("STALE_OR_WRONG_SOURCE_SHA")
    if checkpoint.get("next_action") not in (
        "RECHECK_EXISTING_RUN_AND_HOST_RESULT", "RECOVER_HOST_LEDGER_PAYLOAD",
        "RECHECK_ACCEPTANCE_AND_EXECUTE_NEXT_TOOL",
    ):
        raise ValueError("UNSUPPORTED_ACTION")
    status = current.get("status")
    conclusion = current.get("conclusion")
    if status != "completed":
        observed = "RUN_NOT_FINISHED"
    elif conclusion != "success":
        observed = "RUN_FAILED_OR_INCOMPLETE"
    elif checkpoint.get("result_verified") is not True:
        observed = "HOST_RESULT_UNVERIFIED"
    elif checkpoint.get("output_complete") is not True:
        observed = "HOST_LEDGER_RECOVERY_REQUIRED"
    else:
        observed = "READY_FOR_ACCEPTANCE_VERIFICATION"
    return {
        "schema": "gace.chat.cu.continuation.v1",
        "cu_issue_url": checkpoint.get("cu_issue_url"),
        "repository": repository, "run_id": run_id, "request_id": request_id,
        "source_sha": source_sha, "readback_status": status,
        "readback_conclusion": conclusion, "observation": observed,
        "next_action": {
            "RUN_NOT_FINISHED": "POLL_EXISTING_RUN",
            "RUN_FAILED_OR_INCOMPLETE": "READ_RUN_FAILURE_LOGS",
            "HOST_RESULT_UNVERIFIED": "RECHECK_HOST_OBSERVATION",
            "HOST_LEDGER_RECOVERY_REQUIRED": "RECOVER_HOST_LEDGER_PAYLOAD",
            "READY_FOR_ACCEPTANCE_VERIFICATION": "VERIFY_CU_ACCEPTANCE",
        }[observed],
        "evidence_url": url,
    }


def persist_receipt(path, payload):
    """Write small safe continuation evidence atomically for existing Artifact upload."""
    destination = Path(path)
    if destination.is_symlink():
        raise ValueError("RECEIPT_SYMLINK_DENIED")
    if not isinstance(payload, dict) or "continuation" not in payload:
        raise ValueError("RECEIPT_INVALID")
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if len(encoded.encode("utf-8")) > 32768:
        raise ValueError("RECEIPT_TOO_LARGE")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, delete=False) as tmp:
        tmp.write(encoded)
        staged = Path(tmp.name)
    staged.replace(destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-json", type=Path, default=None)
    parser.add_argument("--repository")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--request-id")
    parser.add_argument("--cu-issue-url")
    parser.add_argument("--receipt-json", type=Path)
    parser.add_argument("--notion-context-json", type=Path)
    args = parser.parse_args()
    if args.checkpoint_json:
        if any([args.repository, args.run_id, args.request_id, args.cu_issue_url]):
            parser.error("--checkpoint-json cannot be combined with discovery flags")
        checkpoint = json.loads(args.checkpoint_json.read_text(encoding="utf-8"))
    else:
        if not all([args.repository, args.run_id, args.request_id, args.cu_issue_url]):
            parser.error("supply checkpoint file or all exact identifiers")
        checkpoint = continuation_checkpoint(
            restore(args.repository, args.run_id, args.request_id), args.cu_issue_url)
    result = {"checkpoint": checkpoint, "continuation": resume(checkpoint)}
    if args.notion_context_json:
        try:
            from scripts.chat_notion_cu_context import build, readback_issue
        except ModuleNotFoundError:
            from chat_notion_cu_context import build, readback_issue
        source = json.loads(args.notion_context_json.read_text(encoding="utf-8"))
        try:
            from scripts.chat_notion_context_ingest import ingest
        except ModuleNotFoundError:
            from chat_notion_context_ingest import ingest
        records = ingest(source, checkpoint["cu_issue_url"])
        context = build(checkpoint["cu_issue_url"], records, checkpoint["cu_issue_url"])
        context["fresh_github_issue"] = readback_issue(checkpoint["cu_issue_url"])
        result["notion_context"] = context
        # Context augments rationale; only fresh GitHub run verification
        # determines the executable next action.
    if args.receipt_json:
        persist_receipt(args.receipt_json, result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
