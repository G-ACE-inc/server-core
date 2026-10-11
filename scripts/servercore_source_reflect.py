#!/usr/bin/env python3
"""Fixed server-core source reflection: no arbitrary repo, branch, shell or deployment hooks.

HOST-LOCAL ONLY. Not exposed by the HMAC-bearing read-only receiver.
"""
import argparse
import fcntl
import json
from pathlib import Path
import re
import subprocess
import sys

CANONICAL_ROOT = Path("/home/admin1/server-core")
LOCK_PATH = Path("/tmp/gace-servercore-source-reflect.lock")
SHA = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_ORIGINS = frozenset(("https://github.com/G-ACE-inc/server-core.git",
                             "git@github.com:G-ACE-inc/server-core.git"))


class ReflectError(Exception):
    pass


def git(root, *args):
    command = [
        "git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
        "-c", "safe.directory=" + str(root), "-C", str(root), *args
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ReflectError("GIT_EXECUTION_FAILED") from None
    if result.returncode:
        raise ReflectError("GIT_COMMAND_FAILED") from None
    return result.stdout.strip()


def reflect(root, expected_before, target_sha, *, dry_run=False):
    if not SHA.fullmatch(expected_before) or not SHA.fullmatch(target_sha):
        raise ReflectError("SHA_INVALID")
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or root.resolve() != CANONICAL_ROOT:
        raise ReflectError("CANONICAL_ROOT_DENIED")
    if (root / ".git").is_symlink() or not (root / ".git").is_dir():
        raise ReflectError("GIT_CHECKOUT_MISSING")
    # A local directory named server-core is not sufficient authorization.
    # Do not fetch from a substituted remote (including local file URLs).
    if git(root, "remote", "get-url", "origin") not in ALLOWED_ORIGINS:
        raise ReflectError("ORIGIN_REMOTE_DENIED")
    if git(root, "rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise ReflectError("BRANCH_NOT_MAIN")
    before = git(root, "rev-parse", "HEAD")
    if before != expected_before:
        raise ReflectError("BEFORE_SHA_MISMATCH")
    # Intentionally includes staged/unstaged/untracked files; no checkout/reset/stash.
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ReflectError("DIRTY_CHECKOUT_DENIED")
    # Fetch only the registered main branch. Never accept a branch from the request.
    git(root, "fetch", "--no-tags", "origin", "refs/heads/main")
    current_remote = git(root, "rev-parse", "FETCH_HEAD")
    if current_remote != target_sha:
        raise ReflectError("REMOTE_MAIN_SHA_MISMATCH")
    if git(root, "merge-base", before, target_sha) != before:
        raise ReflectError("NON_FAST_FORWARD_DENIED")
    if dry_run:
        return {"state": "PREFLIGHT_PASS", "before_sha": before, "target_sha": target_sha,
                "mutation_performed": False}
    git(root, "merge", "--ff-only", "--no-commit", target_sha)
    after = git(root, "rev-parse", "HEAD")
    if after != target_sha:
        raise ReflectError("POST_REFLECT_SHA_MISMATCH")
    return {"state": "SOURCE_REFLECT_PASS", "before_sha": before, "target_sha": after,
            "mutation_performed": before != after}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-before", required=True)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        with LOCK_PATH.open("w") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = reflect(CANONICAL_ROOT, args.expected_before, args.target_sha,
                             dry_run=args.dry_run)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ReflectError, BlockingIOError, PermissionError) as exc:
        code = str(exc) if isinstance(exc, ReflectError) else "LOCK_OR_PERMISSION_DENIED"
        print(json.dumps({"state": "FAIL", "failure_class": code}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
