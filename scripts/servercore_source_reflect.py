#!/usr/bin/env python3
"""Fixed server-core source reflection: no arbitrary repo, branch, shell or deployment hooks.

HOST-LOCAL ONLY. Not exposed by the HMAC-bearing read-only receiver.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys

# SOURCE_REFLECT_LIVE_E2E_MARKER=tool-b-independent-host-source-20261011
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
                                text=True, timeout=60, check=False,
                                umask=0o022)  # checkout files must stay readable/executable despite the 0117 service umask
    except (OSError, subprocess.TimeoutExpired):
        raise ReflectError("GIT_EXECUTION_FAILED") from None
    if result.returncode:
        raise ReflectError("GIT_COMMAND_FAILED") from None
    return result.stdout.strip()


def reflect(root, expected_before, target_sha, *, branch="main", allowed_origins=None, dry_run=False):
    if not SHA.fullmatch(expected_before) or not SHA.fullmatch(target_sha):
        raise ReflectError("SHA_INVALID")
    root = Path(root).resolve()
    if root.is_symlink() or not root.is_dir():
        raise ReflectError("CANONICAL_ROOT_DENIED")
    if not (root == CANONICAL_ROOT.resolve() or str(root).startswith("/home/admin1/projects/")):
        raise ReflectError("CANONICAL_ROOT_DENIED")
    if (root / ".git").is_symlink() or not (root / ".git").is_dir():
        raise ReflectError("GIT_CHECKOUT_MISSING")
    # A local directory named server-core is not sufficient authorization.
    # Do not fetch from a substituted remote (including local file URLs).
    origins = allowed_origins if allowed_origins is not None else ALLOWED_ORIGINS
    if git(root, "remote", "get-url", "origin") not in origins:
        raise ReflectError("ORIGIN_REMOTE_DENIED")
    active_branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if active_branch != branch:
        raise ReflectError("BRANCH_NOT_ALLOWED")
    before = git(root, "rev-parse", "HEAD")
    if before != expected_before:
        raise ReflectError("BEFORE_SHA_MISMATCH")
    # Intentionally includes staged/unstaged/untracked files; no checkout/reset/stash.
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ReflectError("DIRTY_CHECKOUT_DENIED")
    # Fetch only the registered main branch. Never accept a branch from the request.
    git(root, "fetch", "--no-tags", "origin", "refs/heads/" + branch)
    current_remote = git(root, "rev-parse", "FETCH_HEAD")
    if current_remote != target_sha:
        raise ReflectError("REMOTE_BRANCH_SHA_MISMATCH")
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
        fd = os.open(LOCK_PATH, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as lock:
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
