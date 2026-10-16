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



def discover_common_host_run(repository, head_sha, api=api_read):
    """Find existing common Host workflow across ALL GitHub event types."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository or ""):
        raise ValueError("DISCOVERY_REPOSITORY_INVALID")
    if not re.fullmatch(r"[a-f0-9]{40}", head_sha or ""):
        raise ValueError("DISCOVERY_SHA_INVALID")
    response = api(f"repos/{repository}/actions/runs?head_sha={head_sha}&per_page=100")
    if not isinstance(response, dict) or type(response.get("total_count")) is not int or not isinstance(response.get("workflow_runs"), list):
        raise ValueError("RUN_LIST_INVALID")
    if response["total_count"] > len(response["workflow_runs"]):
        raise ValueError("RUN_LIST_PAGINATION_REQUIRED")
    matches = [run for run in response["workflow_runs"]
               if isinstance(run, dict)
               and run.get("head_sha") == head_sha
               and run.get("path") == ".github/workflows/chatgpt-live-api-verify.yml"
               and run.get("event") == "push"]
    if len(matches) > 1:
        raise ValueError("MULTIPLE_COMMON_HOST_RUNS_REQUIRE_EXACT_SELECTION")
    if not matches:
        return {"repository": repository, "source_sha": head_sha,
                "observation": "NO_MATCHING_COMMON_HOST_RUN_IN_COMPLETE_LIST",
                "actions_trigger_verified": False,
                "next_action": "INSPECT_WORKFLOW_TRIGGER_AND_COMMIT_PROVENANCE",
                "other_run_count": response["total_count"]}
    run = matches[0]
    if type(run.get("id")) is not int or run["id"] <= 0:
        raise ValueError("RUN_ID_INVALID")
    return {"repository": repository, "source_sha": head_sha,
            "run_id": run["id"], "status": run.get("status"),
            "conclusion": run.get("conclusion"), "actions_trigger_verified": True,
            "observation": "EXISTING_COMMON_HOST_RUN_FOUND",
            "next_action": "RESTORE_CORRELATED_HOST_OBSERVATION",
            "evidence_url": f"https://github.com/{repository}/actions/runs/{run['id']}",
            "other_run_count": response["total_count"] - 1}

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
    # Preserve a verified Host failure instead of losing it under Actions failure.
    host_failure_step = None
    if (status == "completed" and conclusion != "success"
            and checkpoint.get("observation") == "HOST_SOURCE_SHA_MISMATCH"
            and checkpoint.get("result_verified") is True
            and isinstance(checkpoint.get("host_sha"), str)
            and re.fullmatch(r"[a-f0-9]{40}", checkpoint["host_sha"])
            and isinstance(checkpoint.get("expected_sha"), str)
            and re.fullmatch(r"[a-f0-9]{40}", checkpoint["expected_sha"])
            and checkpoint["host_sha"] != checkpoint["expected_sha"]
            and type(checkpoint.get("exit_code")) is int
            and checkpoint["exit_code"] != 0):
        jobs = api(f"repos/{repository}/actions/runs/{run_id}/jobs?per_page=100")
        if not isinstance(jobs, dict) or not isinstance(jobs.get("jobs"), list):
            raise ValueError("FAILED_RUN_JOBS_UNVERIFIED")
        for job in jobs["jobs"]:
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if (isinstance(step, dict) and step.get("conclusion") == "failure"
                        and step.get("name") == "Bounded Host result return (request id correlated)"):
                    host_failure_step = step["name"]
                    break
    if status != "completed":
        observed = "RUN_NOT_FINISHED"
    elif host_failure_step:
        observed = "CORRELATED_HOST_SHA_MISMATCH"
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
            "CORRELATED_HOST_SHA_MISMATCH": "RECHECK_REGISTERED_TARGET_REPO_SHA_AND_REPLAN_HOST_REQUEST",
            "HOST_RESULT_UNVERIFIED": "RECHECK_HOST_OBSERVATION",
            "HOST_LEDGER_RECOVERY_REQUIRED": "RECOVER_HOST_LEDGER_PAYLOAD",
            "READY_FOR_ACCEPTANCE_VERIFICATION": "VERIFY_CU_ACCEPTANCE",
        }[observed],
        "evidence_url": url,
        "host_failure_step": host_failure_step,
        "observed_host_sha": checkpoint.get("host_sha") if host_failure_step else None,
        "stale_expected_host_sha": checkpoint.get("expected_sha") if host_failure_step else None,
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


def assess_diagnostic_context(context, continuation):
    """Distinguish evidence from hypotheses without overriding Host observations."""
    if not isinstance(context, dict) or not isinstance(continuation, dict):
        raise ValueError("DIAGNOSTIC_CONTEXT_INVALID")
    symptom = context.get("symptom")
    hypotheses = context.get("hypotheses", [])
    if not isinstance(symptom, str) or not symptom.strip() or not isinstance(hypotheses, list):
        raise ValueError("DIAGNOSTIC_CONTEXT_INVALID")
    if len(hypotheses) > 16:
        raise ValueError("DIAGNOSTIC_CONTEXT_TOO_LARGE")
    checked = []
    for item in hypotheses:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
            raise ValueError("DIAGNOSTIC_HYPOTHESIS_INVALID")
        proof = item.get("evidence_url")
        refutation = item.get("refutation_url")
        for url in (proof, refutation):
            if url is not None and (not isinstance(url, str) or not re.fullmatch(
                r"https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:issues/[1-9][0-9]*(?:#issuecomment-[1-9][0-9]*)?|actions/runs/[1-9][0-9]*|commit/[a-f0-9]{40}|pull/[1-9][0-9]*)", url
            )):
                raise ValueError("DIAGNOSTIC_EVIDENCE_URL_INVALID")
        repeated = item.get("previous_attempt_failed") is True
        status = ("REFUTED" if refutation else
                  "REVIEW_BEFORE_REPEAT" if repeated else
                  "EVIDENCE_REFERENCED_NOT_CAUSE_PROVEN" if proof else "HYPOTHESIS_ONLY")
        checked.append({"id": item["id"], "status": status,
                        "evidence_url": proof, "refutation_url": refutation})
    return {"symptom": symptom, "hypotheses": checked,
            "observed_action": continuation.get("next_action"),
            "action_authority": "FRESH_GITHUB_HOST_EVIDENCE_NOT_DIAGNOSTIC_TEXT",
            "causal_claim_verified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-json", type=Path, default=None)
    parser.add_argument("--repository")
    parser.add_argument("--discover-head-sha")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--request-id")
    parser.add_argument("--cu-issue-url")
    parser.add_argument("--receipt-json", type=Path)
    parser.add_argument("--diagnostic-context-json", type=Path)
    parser.add_argument("--notion-context-json", type=Path)
    parser.add_argument("--notion-page-url")
    parser.add_argument("--development-evidence-json", type=Path)
    args = parser.parse_args()
    if args.discover_head_sha:
        if args.checkpoint_json or args.run_id or not args.repository:
            parser.error("discovery requires repository and no checkpoint/run-id")
        discovery = discover_common_host_run(args.repository, args.discover_head_sha)
        if args.request_id or args.cu_issue_url:
            if not args.request_id or not args.cu_issue_url or "run_id" not in discovery:
                parser.error("correlated recovery requires discovered run, request id and CU issue")
            checkpoint = continuation_checkpoint(
                restore(args.repository, discovery["run_id"], args.request_id),
                args.cu_issue_url)
            result = {"discovery": discovery, "checkpoint": checkpoint,
                      "continuation": resume(checkpoint)}
        else:
            result = {"discovery": discovery}
        if args.receipt_json and "continuation" in result:
            persist_receipt(args.receipt_json, result)
        elif args.receipt_json:
            parser.error("receipt requires correlated recovery")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return
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
    if args.diagnostic_context_json:
        diagnostic = json.loads(args.diagnostic_context_json.read_text(encoding="utf-8"))
        result["diagnostic_assessment"] = assess_diagnostic_context(diagnostic, result["continuation"])
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
        records = ingest(source, checkpoint["cu_issue_url"], args.notion_page_url)
        context = build(checkpoint["cu_issue_url"], records, checkpoint["cu_issue_url"])
        context["fresh_github_issue"] = readback_issue(checkpoint["cu_issue_url"])
        context["pilot_measure"] = {
            "source_count": len(source.get("sources", [])) if isinstance(source, dict) else 1,
            "matched_records": context["count"],
            "fetched_records": len(records),
            "unselected_records": max(0, len(records) - context["count"]),
            "baseline_read_calls": None,
            "efficiency_improvement": "NOT_MEASURED",
        }
        context["pilot_measure"]["github_issue_readback_verified"] = True
        context["pilot_measure"]["run_readback_status"] = result["continuation"]["readback_status"]
        context["pilot_measure"]["continuation_action"] = result["continuation"]["next_action"]
        result["notion_context"] = context
        # Context augments rationale; only fresh GitHub run verification
        # determines the executable next action.
    if args.development_evidence_json:
        try:
            from scripts.chat_notion_development_evidence import audit_evidence
        except ModuleNotFoundError:
            from chat_notion_development_evidence import audit_evidence
        development = audit_evidence(json.loads(
            args.development_evidence_json.read_text(encoding="utf-8")))
        if development["cu_url"] != checkpoint["cu_issue_url"]:
            raise ValueError("DEVELOPMENT_CU_MISMATCH")
        result["development_evidence"] = development
        result["development_evidence"]["acceptance"] = "SOURCE_ONLY_NOT_LIVE"
    if args.receipt_json:
        persist_receipt(args.receipt_json, result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
