#!/usr/bin/env python3
"""Expose a public metadata locator for one CHAT Host request commit.

The commit status contains no Host stdout or stderr. The existing private
output path remains the only route for command output.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


REPOSITORY = "G-ACE-inc/server-core"
REQUEST_ID = re.compile(r"req_[a-f0-9]{24}\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
RUN_ID = re.compile(r"[1-9][0-9]{0,19}\Z")
RESULT_URL = re.compile(
    r"https://github[.]com/G-ACE-inc/server-core/issues/10#issuecomment-[1-9][0-9]*\Z"
)


def status_payload(request_id, commit_sha, run_id, observation=None):
    if not REQUEST_ID.fullmatch(request_id) or not SHA.fullmatch(commit_sha) or not RUN_ID.fullmatch(run_id):
        raise ValueError("STATUS_LOCATOR_INPUT_INVALID")
    state = "error"
    result_url = f"https://github.com/{REPOSITORY}/actions/runs/{run_id}"
    result = "RESULT_NOT_RETURNED"
    if isinstance(observation, dict) and observation.get("request_id") == request_id:
        url = observation.get("result_url")
        if isinstance(url, str) and RESULT_URL.fullmatch(url):
            result_url = url
        if observation.get("result_verified") is True:
            if observation.get("state") == "PASS" and observation.get("exit_code") == 0:
                state, result = "success", "HOST_PASS_OUTPUT_SEPARATE"
            elif observation.get("state") == "FAIL" and type(observation.get("exit_code")) is int:
                state, result = "failure", "HOST_FAIL"
    return {
        "state": state,
        "target_url": result_url,
        "description": f"{result} req={request_id} run={run_id}",
        "context": "gace/server-terminal",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--observation-json", required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or not os.environ.get("GH_TOKEN"):
        raise SystemExit("STATUS_LOCATOR_AUTH_UNAVAILABLE")
    try:
        observation = json.loads(Path(args.observation_json).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        observation = None
    payload = status_payload(args.request_id, args.commit_sha, args.run_id, observation)
    if len(payload["description"]) > 140:
        raise SystemExit("STATUS_LOCATOR_DESCRIPTION_TOO_LONG")
    response = subprocess.run(
        ["gh", "api", "-X", "POST", f"repos/{REPOSITORY}/statuses/{args.commit_sha}", "--input", "-"],
        input=json.dumps(payload), capture_output=True, text=True, timeout=30,
    )
    if response.returncode:
        raise SystemExit("STATUS_LOCATOR_PUBLISH_FAILED")
    print(f"CHAT_HOST_STATUS_LOCATOR=PASS request_id={args.request_id} run_id={args.run_id}")


if __name__ == "__main__":
    main()
