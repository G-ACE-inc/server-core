#!/usr/bin/env python3
"""Idempotent opt-in installer for the trusted isolated development job provisioner.

Installs ONE admin1 user-level systemd unit (no root, no new Token, workflow,
MCP or network listener). The UNIX socket lives next to the source-reflect
socket; the read-only Receiver can connect but never receives Docker access; executed code never
reaches this unit's Docker authority (it only gets a project-local workspace mount).
Preflight (default) mutates nothing.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

ROOT = Path("/home/admin1/server-core")
UNIT = Path("/home/admin1/.config/systemd/user/gace-servercore-dev-job.service")
RUN_DIR = Path("/run/gace")
SOCKET = RUN_DIR / "servercore-dev-job.sock"
SERVICE = UNIT.name
SHA = re.compile(r"^[0-9a-f]{40}$")
APPROVED_ORIGINS = frozenset((
    "https://github.com/G-ACE-inc/server-core.git",
    "git@github.com:G-ACE-inc/server-core.git",
))

LEGACY_UNIT_TEXTS = ()

# The long-lived user systemd manager can start without the docker supplementary group (membership added
# later) and an unprivileged unit cannot setgroups, so the Docker-admitted writer starts through `sg docker`
# (setuid, hence NoNewPrivileges=no). It stays a user-level admin1 unit with a UNIX-only fixed-schema socket.
UNIT_TEXT = """[Unit]
Description=G-ACE server-core isolated development job provisioner (UNIX only)

[Service]
Type=simple
WorkingDirectory=/home/admin1/server-core
ExecStartPre=/usr/bin/test -d /run/gace
ExecStart=/usr/bin/sg docker -c "/usr/bin/python3 /home/admin1/server-core/scripts/servercore_dev_job_socket.py"
UMask=0117
NoNewPrivileges=no
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""


class AdmissionError(Exception):
    pass


def git(*args):
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
           "-c", "safe.directory=" + str(ROOT), "-C", str(ROOT), *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    except (OSError, subprocess.TimeoutExpired):
        raise AdmissionError("GIT_PREFLIGHT_FAILED") from None
    if result.returncode:
        raise AdmissionError("GIT_PREFLIGHT_FAILED")
    return result.stdout.strip()


def preflight(expected_head):
    if not isinstance(expected_head, str) or not SHA.fullmatch(expected_head):
        raise AdmissionError("EXPECTED_SHA_INVALID")
    if not ROOT.is_dir() or ROOT.is_symlink() or ROOT.resolve() != ROOT:
        raise AdmissionError("CANONICAL_ROOT_DENIED")
    if not (ROOT / ".git").is_dir() or (ROOT / ".git").is_symlink():
        raise AdmissionError("GIT_CHECKOUT_INVALID")
    if not (ROOT / "scripts/servercore_dev_job_socket.py").is_file():
        raise AdmissionError("DEV_JOB_SOURCE_MISSING")
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise AdmissionError("BRANCH_NOT_MAIN")
    if git("remote", "get-url", "origin") not in APPROVED_ORIGINS:
        raise AdmissionError("REMOTE_ORIGIN_DENIED")
    if git("rev-parse", "HEAD") != expected_head:
        raise AdmissionError("SOURCE_HEAD_MISMATCH")
    # Tracked source files must be exact; Host-local registry edits owned by other CUs are not touched.
    if [line for line in git("status", "--porcelain", "--", "scripts").splitlines() if line]:
        raise AdmissionError("DEV_JOB_SOURCE_DIRTY")
    if not RUN_DIR.is_dir() or RUN_DIR.is_symlink():
        raise AdmissionError("SOCKET_PARENT_MISSING")
    if os.geteuid() == 0:
        raise AdmissionError("ROOT_INSTALL_DENIED")
    if UNIT.is_symlink():
        raise AdmissionError("UNIT_SYMLINK_DENIED")


def systemctl_user(*args):
    try:
        result = subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        raise AdmissionError("SYSTEMD_COMMAND_FAILED") from None
    if result.returncode:
        raise AdmissionError("SYSTEMD_COMMAND_FAILED")


def install(expected_head):
    preflight(expected_head)
    if UNIT.exists():
        existing = UNIT.read_text()
        if existing in LEGACY_UNIT_TEXTS:
            tmp = UNIT.with_suffix(".service.new")
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(UNIT_TEXT)
            os.replace(tmp, UNIT)
        elif existing != UNIT_TEXT:
            raise AdmissionError("EXISTING_UNIT_CONFLICT")
    else:
        UNIT.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(UNIT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(UNIT_TEXT)
    systemctl_user("daemon-reload")
    systemctl_user("enable", "--now", SERVICE)
    systemctl_user("restart", SERVICE)
    for _ in range(20):
        if SOCKET.is_socket():
            break
        time.sleep(0.5)
    if not SOCKET.is_socket():
        raise AdmissionError("HOST_SOCKET_NOT_RUNNING")
    info = SOCKET.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o007:
        raise AdmissionError("HOST_SOCKET_ACCESS_INVALID")
    return {"state": "DEV_JOB_READY", "sha": expected_head, "socket": str(SOCKET)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    try:
        if args.install:
            result = install(args.expected_head)
        else:
            preflight(args.expected_head)
            result = {"state": "DEV_JOB_PREFLIGHT_PASS", "sha": args.expected_head,
                      "mutation_performed": False}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (AdmissionError, OSError) as exc:
        code = str(exc) if isinstance(exc, AdmissionError) else "HOST_PERMISSION_OR_IO_DENIED"
        print(json.dumps({"state": "FAIL", "failure_class": code}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
