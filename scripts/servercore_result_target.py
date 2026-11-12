#!/usr/bin/env python3
"""Resolve the common Terminal's single registered GitHub result target."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


CONTRACT = Path(__file__).resolve().parents[1] / "operations" / "github-project-bounded-host.json"
OWNER = "G-ACE-inc/server-core"
GITHUB_COMMENT_LIMIT = 2500


class ResultTargetError(ValueError):
    pass


def load_target(path=CONTRACT):
    try:
        target = json.loads(Path(path).read_text(encoding="utf-8"))["result_return"]
    except (OSError, ValueError, KeyError, TypeError):
        raise ResultTargetError("RESULT_TARGET_CONTRACT_UNAVAILABLE") from None
    if not isinstance(target, dict):
        raise ResultTargetError("RESULT_TARGET_CONTRACT_INVALID")
    issue = target.get("issue_number")
    ceiling = target.get("dispatch_comment_ceiling")
    if (target.get("kind") != "github_issue_comment" or target.get("repository") != OWNER
            or type(issue) is not int or issue < 1
            or target.get("marker") != "GACE_BOUNDED_HOST_RESULT"
            or type(ceiling) is not int or not 1 <= ceiling < GITHUB_COMMENT_LIMIT):
        raise ResultTargetError("RESULT_TARGET_CONTRACT_INVALID")
    return target


def check_capacity(target, runner=subprocess.run):
    path = f"repos/{target['repository']}/issues/{target['issue_number']}"
    try:
        result = runner(["gh", "api", path], capture_output=True, text=True,
                        timeout=20, check=False)
        if result.returncode:
            raise ResultTargetError("RESULT_TARGET_API_UNAVAILABLE")
        issue = json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError):
        raise ResultTargetError("RESULT_TARGET_API_UNAVAILABLE") from None
    if not isinstance(issue, dict) or type(issue.get("comments")) is not int:
        raise ResultTargetError("RESULT_TARGET_RESPONSE_INVALID")
    if issue.get("locked") is True or issue.get("state") != "open":
        raise ResultTargetError("RESULT_TARGET_NOT_WRITABLE")
    if issue["comments"] >= target["dispatch_comment_ceiling"]:
        raise ResultTargetError("RESULT_TARGET_CAPACITY_EXHAUSTED")
    return issue["comments"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args(argv)
    try:
        target = load_target()
        if args.repository != target["repository"]:
            raise ResultTargetError("RESULT_TARGET_REPOSITORY_MISMATCH")
        check_capacity(target)
    except ResultTargetError as exc:
        print("RESULT_SINK_CAPACITY=" + str(exc), file=sys.stderr)
        return 48
    print(target["issue_number"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
