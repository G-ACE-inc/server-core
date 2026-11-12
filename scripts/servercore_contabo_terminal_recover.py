#!/usr/bin/env python3
"""One-shot Contabo recovery for the existing common Terminal result publisher.

Run locally as the existing admin1 user. This is not a new Terminal transport,
a privileged daemon, or an authorization bypass. It reuses the installed
source-reflect guard and restarts ONLY the existing result-sink user service.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path("/home/admin1/server-core")
SOCKET = Path("/run/gace/servercore-result.sock")
SERVICE = "gace-servercore-result-sink.service"
ORIGINS = frozenset(("https://github.com/G-ACE-inc/server-core.git",
                     "git@github.com:G-ACE-inc/server-core.git"))
SHA = re.compile(r"^[0-9a-f]{40}$")


class RecoveryError(Exception):
    pass


def command(*argv, root=ROOT, timeout=60, env=None):
    try:
        result = subprocess.run(list(argv), cwd=root, capture_output=True, text=True,
                                timeout=timeout, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired):
        raise RecoveryError("COMMAND_UNAVAILABLE") from None
    if result.returncode:
        # Never expose arbitrary stderr: it may contain tokens or local paths.
        raise RecoveryError("COMMAND_FAILED")
    return result.stdout.strip()


def recover(*, root=ROOT):
    root = Path(root)
    if (root.is_symlink() or not root.is_dir() or not (root / ".git").is_dir()
            or root.resolve() != root or os.geteuid() == 0
            or os.geteuid() != root.stat().st_uid):
        raise RecoveryError("LOCAL_HOST_IDENTITY_DENIED")
    git = lambda *args: command("git", "-C", str(root), *args, root=root)
    if git("remote", "get-url", "origin") not in ORIGINS:
        raise RecoveryError("REMOTE_ORIGIN_DENIED")
    if git("branch", "--show-current") != "main":
        raise RecoveryError("BRANCH_NOT_MAIN")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise RecoveryError("TRACKED_WORKTREE_DIRTY")
    before = git("rev-parse", "HEAD")
    if not SHA.fullmatch(before):
        raise RecoveryError("HOST_HEAD_INVALID")
    command("git", "-C", str(root), "fetch", "--no-tags", "origin",
            "refs/heads/main", root=root, timeout=70)
    target = git("rev-parse", "FETCH_HEAD")
    if not SHA.fullmatch(target):
        raise RecoveryError("REMOTE_HEAD_INVALID")
    if before != target:
        # This existing guard owns clean-checkout, fast-forward, origin and
        # untracked collision protection. Do not duplicate its git mutation.
        command(sys.executable, "-B", "scripts/servercore_source_reflect.py",
                "--expected-before", before, "--target-sha", target,
                root=root, timeout=160)
    after = git("rev-parse", "HEAD")
    if after != target:
        raise RecoveryError("SOURCE_READBACK_MISMATCH")
    try:
        issue = json.loads((root / "operations/github-project-bounded-host.json")
                           .read_text(encoding="utf-8"))["result_return"]["issue_number"]
    except (OSError, ValueError, TypeError, KeyError):
        raise RecoveryError("RESULT_TARGET_UNAVAILABLE") from None
    if type(issue) is not int or issue < 1:
        raise RecoveryError("RESULT_TARGET_INVALID")
    runtime = Path("/run/user") / str(os.geteuid())
    env = dict(os.environ)
    if runtime.is_dir():
        env["XDG_RUNTIME_DIR"] = str(runtime)
    command("systemctl", "--user", "restart", SERVICE, root=root, timeout=40, env=env)
    active = command("systemctl", "--user", "is-active", SERVICE, root=root, timeout=20, env=env)
    if active != "active" or not SOCKET.is_socket():
        raise RecoveryError("RESULT_SINK_NOT_READY")
    return {"state": "SOURCE_AND_SINK_ACTIVE", "before_head": before,
            "target_head": target, "after_head": after, "result_issue": issue,
            "result_sink_service": active, "result_publication": "NOT_VERIFIED"}


def main():
    try:
        outcome = recover()
    except RecoveryError as exc:
        outcome = {"state": "FAIL", "failure_class": str(exc)}
    print(json.dumps(outcome, sort_keys=True))
    return 0 if outcome["state"] == "SOURCE_AND_SINK_ACTIVE" else 1


if __name__ == "__main__":
    sys.exit(main())
