#!/usr/bin/env python3
"""Restore a correlated CHAT observation from an existing GitHub Actions run.

Reuse gh CLI authentication and the existing #247 artifact. Never scan Issue #10.
No new workflow, API key, or server-side service required.
"""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

try:
    from scripts.chat_host_observation_artifact_readback import from_artifact
except ModuleNotFoundError:
    from chat_host_observation_artifact_readback import from_artifact

REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
REQUEST_ID = re.compile(r"req_[a-f0-9]{24}\Z")
ARTIFACT_SHA = re.compile(r"[a-f0-9]{40}\Z")


def paginated_list(path, key, api):
    """Read a complete, stable GitHub collection before selecting evidence."""
    items, ids, total, page = [], set(), None, 1
    while True:
        response = api(path if page == 1 else f"{path}&page={page}")
        if (not isinstance(response, dict)
                or type(response.get("total_count")) is not int
                or response["total_count"] < 0
                or not isinstance(response.get(key), list)):
            raise ValueError("GITHUB_LIST_INVALID")
        if total is None:
            total = response["total_count"]
        elif total != response["total_count"]:
            raise ValueError("GITHUB_LIST_CHANGED_DURING_READBACK")
        batch = response[key]
        if not batch and len(items) < total:
            raise ValueError("GITHUB_LIST_INCOMPLETE")
        for item in batch:
            if (not isinstance(item, dict) or type(item.get("id")) is not int
                    or item["id"] <= 0 or item["id"] in ids):
                raise ValueError("GITHUB_LIST_ID_INVALID_OR_DUPLICATE")
            ids.add(item["id"])
            items.append(item)
        if len(items) > total:
            raise ValueError("GITHUB_LIST_COUNT_MISMATCH")
        if len(items) == total:
            return items
        page += 1


def valid_repository(repository):
    return (isinstance(repository, str) and REPOSITORY.fullmatch(repository)
            and all(part not in {".", ".."} for part in repository.split("/")))


def restore(repository, run_id, request_id, run=subprocess.run):
    if (not valid_repository(repository)
            or type(run_id) is not int or run_id <= 0):
        raise ValueError("RUN_ID_OR_REPOSITORY_INVALID")
    if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
        raise ValueError("REQUEST_ID_INVALID")
    def api(path):
        response = run(["gh", "api", path], capture_output=True, text=True,
                       timeout=25, check=True)
        return json.loads(response.stdout)

    info = api(f"repos/{repository}/actions/runs/{run_id}")
    if (not isinstance(info, dict) or info.get("id") != run_id
            or not isinstance(info.get("repository"), dict)
            or info["repository"].get("full_name", "").lower() != repository.lower()
            or info.get("path") != ".github/workflows/chatgpt-live-api-verify.yml"):
        raise ValueError("RUN_PROVENANCE_MISMATCH")
    source_sha = info.get("head_sha")
    if not isinstance(source_sha, str) or not ARTIFACT_SHA.fullmatch(source_sha):
        raise ValueError("RUN_SHA_UNVERIFIED")
    artifact_name = "chat-host-observation-" + source_sha
    artifacts = paginated_list(
        f"repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100", "artifacts", api)
    matching = [a for a in artifacts if a.get("name") == artifact_name]
    if len(matching) != 1 or matching[0].get("expired") is not False:
        raise ValueError("ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS")
    artifact = matching[0]
    provenance = artifact.get("workflow_run")
    if (not isinstance(provenance, dict) or provenance.get("id") != run_id
            or provenance.get("head_sha") != source_sha):
        raise ValueError("ARTIFACT_RUN_PROVENANCE_MISMATCH")
    artifact_id = artifact["id"]
    with tempfile.TemporaryDirectory(prefix="gace-observation-") as directory:
        # Download the exact validated ID, rather than selecting again by name.
        archive = run(["gh", "api", f"repos/{repository}/actions/artifacts/{artifact_id}/zip"],
                      capture_output=True, timeout=90, check=True)
        path = Path(directory) / "observation.zip"
        path.write_bytes(archive.stdout)
        observation = from_artifact(path, request_id)
    return {"repository": repository, "run_id": run_id, "artifact_id": artifact_id,
            "source_sha": source_sha, **observation}


def continuation_checkpoint(result, cu_issue_url):
    """Emit a bounded, evidence-backed next step; never mutate Issue/Host here."""
    if not isinstance(cu_issue_url, str) or not re.fullmatch(
        r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*", cu_issue_url
    ):
        raise ValueError("CU_ISSUE_URL_INVALID")
    if result["result_verified"] is not True:
        phase, next_action = "OBSERVE", "RECHECK_EXISTING_RUN_AND_HOST_RESULT"
    elif result["output_complete"] is not True:
        phase, next_action = "OBSERVE", "RECOVER_HOST_LEDGER_PAYLOAD"
    else:
        phase, next_action = "VERIFY", "RECHECK_ACCEPTANCE_AND_EXECUTE_NEXT_TOOL"
    return {
        "schema": "gace.chat.cu.handoff.v1",
        "cu_issue_url": cu_issue_url,
        "phase": phase,
        "repository": result["repository"],
        "run_id": result["run_id"],
        "artifact_id": result["artifact_id"],
        "source_sha": result["source_sha"],
        "request_id": result["request_id"],
        "observation": result["observation"],
        "result_verified": result["result_verified"],
        "expected_sha": result.get("expected_sha"),
        "host_sha": result.get("host_sha"),
        "exit_code": result.get("exit_code"),
        "output_complete": result["output_complete"],
        "result_url": result["result_url"],
        "next_action": next_action,
        "next_tool_target": (
            f"https://github.com/{result['repository']}/actions/runs/{result['run_id']}"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--cu-issue-url", default=None)
    parser.add_argument("--checkpoint-json", default=None)
    args = parser.parse_args()
    result = restore(args.repository, args.run_id, args.request_id)
    if args.cu_issue_url:
        result = continuation_checkpoint(result, args.cu_issue_url)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n"
    if args.checkpoint_json:
        if not args.cu_issue_url:
            parser.error("--checkpoint-json requires --cu-issue-url")
        destination = Path(args.checkpoint_json)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, delete=False) as temp:
            temp.write(encoded)
            staged = Path(temp.name)
        staged.replace(destination)
    print(encoded, end="")


if __name__ == "__main__":
    main()
