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
import os
import zipfile
from contextlib import contextmanager
from functools import partial
from pathlib import Path

try:
    from scripts.chat_host_observation_artifact_readback import from_artifact
    from scripts.servercore_host_output_private_artifact_publish import REPO as PRIVATE_OUTPUT_REPOSITORY
    from scripts.servercore_host_output_artifact_assemble import (
        verify_artifact_zip, validate_expected_streams, MAX_VERIFIED_ARCHIVE_BYTES)
except ModuleNotFoundError:
    from chat_host_observation_artifact_readback import from_artifact
    from servercore_host_output_private_artifact_publish import REPO as PRIVATE_OUTPUT_REPOSITORY
    from servercore_host_output_artifact_assemble import (
        verify_artifact_zip, validate_expected_streams, MAX_VERIFIED_ARCHIVE_BYTES)

REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
REQUEST_ID = re.compile(r"req_[a-f0-9]{24}\Z")
ARTIFACT_SHA = re.compile(r"[a-f0-9]{40}\Z")
# This limit applies only to small observation metadata ZIPs, not Host ledger
# stdout/stderr transport. GitHub's actual two ZIPs are ~0.5 KiB.
MAX_OBSERVATION_ZIP_BYTES = 1024 * 1024


def _enforce_zip_file_limit(limit=MAX_OBSERVATION_ZIP_BYTES):
    """Bound child stdout writes on the existing Linux execution path."""
    import resource
    resource.setrlimit(resource.RLIMIT_FSIZE, (
        limit, limit))


def _download_artifact(repository, artifact_id, path, limit, run):
    """Stream authenticated bytes to private temporary storage with a hard cap."""
    if os.name != "posix":
        raise RuntimeError("BOUNDED_ARTIFACT_DOWNLOAD_UNSUPPORTED_PLATFORM")
    with path.open("xb") as output:
        path.chmod(0o600)
        run(["gh", "api", f"repos/{repository}/actions/artifacts/{artifact_id}/zip"],
            stdout=output, stderr=subprocess.PIPE, timeout=90, check=True,
            preexec_fn=partial(_enforce_zip_file_limit, limit))
    if path.stat().st_size > limit:
        raise ValueError("ARTIFACT_ZIP_SIZE_EXCEEDED")



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
            or not isinstance(info.get("path"), str)
            or info["path"].split("@", 1)[0] != ".github/workflows/chatgpt-live-api-verify.yml"):
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
    # Reject oversized or missing GitHub size metadata before any download.
    size = artifact.get("size_in_bytes")
    if type(size) is not int or size <= 0 or size > MAX_OBSERVATION_ZIP_BYTES:
        raise ValueError("ARTIFACT_ZIP_SIZE_INVALID_OR_TOO_LARGE")
    artifact_id = artifact["id"]
    with tempfile.TemporaryDirectory(prefix="gace-observation-") as directory:
        path = Path(directory) / "observation.zip"
        _download_artifact(repository, artifact_id, path, MAX_OBSERVATION_ZIP_BYTES, run)
        observation = from_artifact(path, request_id)
    return {"repository": repository, "run_id": run_id, "artifact_id": artifact_id,
            "source_sha": source_sha, **observation}


@contextmanager
def private_host_output(run_id, request_id, expected_streams, run=subprocess.run):
    """Yield a verified existing private payload, then remove all plaintext.

    The destination is the existing publisher's fixed private repository. The
    expected stream digests must come from independent common-Host observation,
    never from this private ZIP's own manifest. No new Host work is dispatched.
    """
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("PRIVATE_RUN_ID_INVALID")
    if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
        raise ValueError("REQUEST_ID_INVALID")
    validate_expected_streams(expected_streams)
    repository = PRIVATE_OUTPUT_REPOSITORY

    def api(path):
        response = run(["gh", "api", path], capture_output=True, text=True,
                       timeout=25, check=True)
        return json.loads(response.stdout)

    recipient = api(f"repos/{repository}")
    if (not isinstance(recipient, dict) or recipient.get("private") is not True
            or recipient.get("full_name", "").lower() != repository.lower()):
        raise ValueError("PRIVATE_REPOSITORY_NOT_VERIFIED")
    info = api(f"repos/{repository}/actions/runs/{run_id}")
    if (not isinstance(info, dict) or info.get("id") != run_id
            or not isinstance(info.get("repository"), dict)
            or info["repository"].get("full_name", "").lower() != repository.lower()
            or not isinstance(info.get("path"), str)
            or info["path"].split("@", 1)[0] != ".github/workflows/ci.yml"
            or info.get("event") != "release"
            or info.get("status") != "completed" or info.get("conclusion") != "success"
            or not isinstance(info.get("head_sha"), str)
            or not ARTIFACT_SHA.fullmatch(info["head_sha"])):
        raise ValueError("PRIVATE_RUN_PROVENANCE_MISMATCH")
    artifacts = paginated_list(
        f"repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100", "artifacts", api)
    matches = [a for a in artifacts if a.get("name") == "gace-host-output-" + request_id]
    if len(matches) != 1 or matches[0].get("expired") is not False:
        raise ValueError("ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS")
    artifact = matches[0]
    provenance = artifact.get("workflow_run")
    if (not isinstance(provenance, dict) or provenance.get("id") != run_id
            or provenance.get("head_sha") != info["head_sha"]):
        raise ValueError("ARTIFACT_RUN_PROVENANCE_MISMATCH")
    size = artifact.get("size_in_bytes")
    if type(size) is not int or not 0 < size <= MAX_VERIFIED_ARCHIVE_BYTES:
        raise ValueError("ARTIFACT_ZIP_SIZE_INVALID_OR_TOO_LARGE")
    with tempfile.TemporaryDirectory(prefix="gace-private-readback-") as directory:
        outer, payload = Path(directory, "artifact.zip"), Path(directory, "output.zip")
        _download_artifact(repository, artifact["id"], outer, MAX_VERIFIED_ARCHIVE_BYTES, run)
        with zipfile.ZipFile(outer) as archive:
            if archive.namelist() != ["output.zip"]:
                raise ValueError("PRIVATE_ARTIFACT_MEMBERS_INVALID")
            entry = archive.getinfo("output.zip")
            if (not 0 < entry.file_size <= MAX_VERIFIED_ARCHIVE_BYTES
                    or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                raise ValueError("PRIVATE_ARTIFACT_PAYLOAD_SIZE_OR_COMPRESSION_INVALID")
            with archive.open(entry) as source, payload.open("xb") as target:
                payload.chmod(0o600)
                count = 0
                while data := source.read(65536):
                    count += len(data)
                    if count > entry.file_size:
                        raise ValueError("PRIVATE_ARTIFACT_PAYLOAD_SIZE_MISMATCH")
                    target.write(data)
            if count != entry.file_size:
                raise ValueError("PRIVATE_ARTIFACT_PAYLOAD_SIZE_MISMATCH")
        proof = verify_artifact_zip(payload, request_id, expected_streams)
        yield payload, {"repository": repository, "run_id": run_id,
                        "artifact_id": artifact["id"], "source_sha": info["head_sha"],
                        **proof}


def continuation_checkpoint(result, cu_issue_url):
    """Emit a bounded, evidence-backed next step; never mutate Issue/Host here."""
    if not isinstance(cu_issue_url, str) or not re.fullmatch(
        r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*", cu_issue_url
    ):
        raise ValueError("CU_ISSUE_URL_INVALID")
    if result["result_verified"] is not True:
        phase, next_action = "OBSERVE", "RECHECK_EXISTING_RUN_AND_HOST_RESULT"
    elif result.get("observation") in {
        "HOST_SOURCE_SHA_MISMATCH", "HOST_OPERATION_FAILED",
        "HOST_OPERATION_RETRYABLE", "HOST_SOURCE_CONTEXT_STALE",
        "HOST_SOURCE_CONTEXT_INVALID", "HOST_RESULT_UNVERIFIED",
        "CORRELATION_FAILED",
    }:
        # Failure provenance must be rechecked against the original Job before
        # payload recovery or replanning; missing plaintext is not the first gate.
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
        "command_id": result.get("command_id"),
        "source_truncated": result.get("source_truncated", False),
        "observation": result["observation"],
        "result_verified": result["result_verified"],
        "expected_sha": result.get("expected_sha"),
        "host_sha": result.get("host_sha"),
        "exit_code": result.get("exit_code"),
        "diagnostic_hint": result.get("diagnostic_hint"),
        "output_complete": result["output_complete"],
        "stream_metadata": result.get("stream_metadata"),
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
