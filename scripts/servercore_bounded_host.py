#!/usr/bin/env python3
"""server-core-owned bounded local Host primitive. No network listener or credentials."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

CANONICAL_ROOT = Path("/home/admin1/server-core")
COMMANDS = frozenset(("project.git_head", "project.git_status", "project.git_recent_commits", "project.registered_tests"))
TESTS = (
    "scripts/github_project_rule_plane_test.py",
    "scripts/github_project_chat_host_route_test.py",
)


class BoundaryError(Exception):
    pass


def checked_root(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise BoundaryError("CANONICAL_ROOT_INVALID")
    actual = root.resolve(strict=True)
    if not (actual / ".git").exists():
        raise BoundaryError("CANONICAL_GIT_MISSING")
    return actual


def _run(argv, root, timeout=35):
    if argv and argv[0] == "git":
        # The container runs under an unprivileged UID while the canonical
        # checkout is owned by the Host user. Trust ONLY the prevalidated root
        # for these fixed read-only Git subcommands; never use --global config.
        argv = ["git", "-c", "safe.directory=" + str(root),
                "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null",
                *argv[1:]]
    try:
        p = subprocess.run(argv, cwd=root, capture_output=True, text=True,
                           timeout=timeout, check=False, env={
                               "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                               "HOME": str(root),
                               "GIT_CONFIG_NOSYSTEM": "1",
                               "GIT_TERMINAL_PROMPT": "0",
                           })
    except (OSError, subprocess.TimeoutExpired):
        raise BoundaryError("COMMAND_EXECUTION_FAILED") from None
    if p.returncode:
        raise BoundaryError("COMMAND_FAILED")
    return p.stdout


def execute(command_id, root=CANONICAL_ROOT, expected_sha=None):
    if command_id not in COMMANDS:
        raise BoundaryError("COMMAND_NOT_REGISTERED")
    root = checked_root(root)
    sha = _run(["git", "rev-parse", "HEAD"], root).strip()
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise BoundaryError("GIT_HEAD_INVALID")
    if expected_sha is not None and sha != expected_sha:
        raise BoundaryError("SOURCE_SHA_MISMATCH")
    result = {"command_id": command_id, "source_sha": sha, "read_only": True}
    if command_id == "project.git_head":
        return result
    if command_id == "project.git_status":
        result["clean"] = not bool(_run(["git", "status", "--porcelain"], root).strip())
        return result
    if command_id == "project.git_recent_commits":
        commits = _run(["git", "log", "-n", "5", "--format=%H"], root).splitlines()
        if not commits or len(commits) > 5 or any(len(x) != 40 or any(c not in "0123456789abcdef" for c in x) for x in commits):
            raise BoundaryError("GIT_HISTORY_INVALID")
        result["commits"] = commits
        return result
    if _run(["git", "status", "--porcelain"], root).strip():
        raise BoundaryError("TEST_CHECKOUT_DIRTY")
    for relative in TESTS:
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.resolve().parent != (root / "scripts").resolve():
            raise BoundaryError("REGISTERED_TEST_MISSING")
        _run([sys.executable, "-I", str(path)], root, timeout=90)
    result["registered_tests"] = "PASS"
    result["count"] = len(TESTS)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    try:
        if len(args.expected_sha) != 40 or any(c not in "0123456789abcdef" for c in args.expected_sha):
            raise BoundaryError("EXPECTED_SHA_INVALID")
        print(json.dumps({"state": "PASS", **execute(args.command_id, expected_sha=args.expected_sha)}, sort_keys=True))
        return 0
    except BoundaryError as exc:
        print(json.dumps({"state": "FAIL", "failure_class": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
