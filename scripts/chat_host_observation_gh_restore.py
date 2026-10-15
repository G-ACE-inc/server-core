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
    from scripts.chat_host_observation_artifact_readback import validate
except ModuleNotFoundError:
    from chat_host_observation_artifact_readback import validate

REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
REQUEST_ID = re.compile(r"req_[a-f0-9]{24}\Z")
ARTIFACT_SHA = re.compile(r"[a-f0-9]{40}\Z")


def restore(repository, run_id, request_id, run=subprocess.run):
    if not REPOSITORY.fullmatch(repository) or type(run_id) is not int or run_id <= 0:
        raise ValueError("RUN_ID_OR_REPOSITORY_INVALID")
    if not REQUEST_ID.fullmatch(request_id):
        raise ValueError("REQUEST_ID_INVALID")
    # GitHub artifact naming contract from existing workflow: name includes source SHA.
    metadata = run(
        ["gh", "api", f"repos/{repository}/actions/runs/{run_id}"],
        capture_output=True, text=True, timeout=25, check=True,
    )
    info = json.loads(metadata.stdout)
    source_sha = info.get("head_sha")
    if not isinstance(source_sha, str) or not ARTIFACT_SHA.fullmatch(source_sha):
        raise ValueError("RUN_SHA_UNVERIFIED")
    artifact_name = "chat-host-observation-" + source_sha
    listing = run(
        ["gh", "api", f"repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100"],
        capture_output=True, text=True, timeout=25, check=True,
    )
    artifacts = json.loads(listing.stdout).get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("ARTIFACT_LIST_INVALID")
    matching = [a for a in artifacts if a.get("name") == artifact_name and not a.get("expired")]
    if len(matching) != 1:
        raise ValueError("ARTIFACT_UNAVAILABLE_OR_AMBIGUOUS")
    artifact_id = matching[0].get("id")
    if type(artifact_id) is not int:
        raise ValueError("ARTIFACT_ID_INVALID")
    with tempfile.TemporaryDirectory(prefix="gace-observation-") as directory:
        run(
            ["gh", "run", "download", str(run_id), "-R", repository,
             "-n", artifact_name, "-D", directory],
            capture_output=True, text=True, timeout=90, check=True,
        )
        path = Path(directory) / "gace-chat-host-observation.json"
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 32768:
            raise ValueError("OBSERVATION_FILE_INVALID")
        observation = validate(json.loads(path.read_text(encoding="utf-8")), request_id)
    return {"repository": repository, "run_id": run_id, "artifact_id": artifact_id,
            "source_sha": source_sha, **observation}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--request-id", required=True)
    args = parser.parse_args()
    print(json.dumps(restore(args.repository, args.run_id, args.request_id),
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
