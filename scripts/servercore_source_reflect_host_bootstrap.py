#!/usr/bin/env python3
"""Idempotent opt-in installer for the separate server-core Host reflection executor.

No external service, workflow, token, root shell or Docker socket is created.
Host authority must authorize systemd admission and approved receiver GID.
"""
import argparse
import grp
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess

ROOT = Path("/home/admin1/server-core")
UNIT = Path("/etc/systemd/system/gace-servercore-source-reflect.service")
SOCKET = Path("/run/gace/servercore-source-reflect.sock")
SERVICE = UNIT.name
APPROVED_ORIGINS = frozenset((
    "https://github.com/G-ACE-inc/server-core.git",
    "git@github.com:G-ACE-inc/server-core.git",
))
SHA = re.compile(r"^[0-9a-f]{40}$")


class AdmissionError(Exception):
    pass


def git(*args):
    cmd = ["git", "-c", "core.hooksPath=/dev/null",
           "-c", "core.fsmonitor=false",
           "-c", "safe.directory=" + str(ROOT),
           "-C", str(ROOT), *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    except (OSError, subprocess.TimeoutExpired):
        raise AdmissionError("GIT_PREFLIGHT_FAILED") from None
    if result.returncode:
        raise AdmissionError("GIT_PREFLIGHT_FAILED")
    return result.stdout.strip()


def preflight(expected_head, gid):
    if not isinstance(expected_head, str) or not SHA.fullmatch(expected_head):
        raise AdmissionError("EXPECTED_SHA_INVALID")
    if not ROOT.is_dir() or ROOT.is_symlink() or ROOT.resolve() != ROOT:
        raise AdmissionError("CANONICAL_ROOT_DENIED")
    if not (ROOT / ".git").is_dir() or (ROOT / ".git").is_symlink():
        raise AdmissionError("GIT_CHECKOUT_INVALID")
    if not (ROOT / "scripts/servercore_source_reflect_socket.py").is_file():
        raise AdmissionError("SOCKET_EXECUTOR_SOURCE_MISSING")
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise AdmissionError("BRANCH_NOT_MAIN")
    if git("remote", "get-url", "origin") not in APPROVED_ORIGINS:
        raise AdmissionError("REMOTE_ORIGIN_DENIED")
    if git("rev-parse", "HEAD") != expected_head:
        raise AdmissionError("SOURCE_HEAD_MISMATCH")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise AdmissionError("DIRTY_CHECKOUT_DENIED")
    try:
        number = int(gid)
        group = grp.getgrgid(number)
        owner = pwd.getpwnam("admin1")
    except (ValueError, KeyError):
        raise AdmissionError("HOST_IDENTITY_MISSING") from None
    if number <= 0 or owner.pw_uid == 0:
        raise AdmissionError("HOST_IDENTITY_UNSAFE")
    if UNIT.is_symlink():
        raise AdmissionError("UNIT_SYMLINK_DENIED")
    return group.gr_name


def unit_text(group):
    if not isinstance(group, str) or not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", group):
        raise AdmissionError("SERVICE_GROUP_INVALID")
    return f"""[Unit]
Description=G-ACE server-core fixed SHA Source Reflection (UNIX only)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=admin1
Group={group}
WorkingDirectory=/home/admin1/server-core
ExecStart=/usr/bin/python3 /home/admin1/server-core/scripts/servercore_source_reflect_socket.py
RuntimeDirectory=gace
RuntimeDirectoryMode=0750
UMask=0117
NoNewPrivileges=yes
CapabilityBoundingSet=
RestrictSUIDSGID=yes
PrivateDevices=yes
ProtectSystem=strict
ReadWritePaths=/home/admin1/server-core /run/gace /tmp
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


def call_systemctl(*args):
    try:
        cmd = subprocess.run(["systemctl", *args], capture_output=True, text=True, timeout=25)
    except (OSError, subprocess.TimeoutExpired):
        raise AdmissionError("SYSTEMD_COMMAND_FAILED") from None
    if cmd.returncode:
        raise AdmissionError("SYSTEMD_COMMAND_FAILED")


def install(expected_head, gid):
    group = preflight(expected_head, gid)
    if os.geteuid() != 0:
        raise AdmissionError("HOST_ADMIN_REQUIRED")
    unit = unit_text(group)
    if UNIT.exists():
        if UNIT.read_text() != unit:
            raise AdmissionError("EXISTING_UNIT_CONFLICT")
    else:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        fd = os.open(UNIT, flags, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(unit)
    call_systemctl("daemon-reload")
    call_systemctl("enable", "--now", SERVICE)
    call_systemctl("restart", SERVICE)
    if not SOCKET.is_socket():
        raise AdmissionError("HOST_SOCKET_NOT_RUNNING")
    info = SOCKET.stat()
    if info.st_gid != int(gid) or stat.S_IMODE(info.st_mode) & 0o007:
        raise AdmissionError("HOST_SOCKET_ACCESS_INVALID")
    return {"state": "HOST_SOCKET_READY", "sha": expected_head, "socket": str(SOCKET)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--receiver-gid", required=True)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    try:
        if args.install:
            result = install(args.expected_head, args.receiver_gid)
        else:
            group = preflight(args.expected_head, args.receiver_gid)
            result = {"state": "HOST_BOOTSTRAP_PREFLIGHT_PASS",
                      "sha": args.expected_head, "receiver_group": group,
                      "mutation_performed": False}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (AdmissionError, PermissionError, OSError) as exc:
        code = str(exc) if isinstance(exc, AdmissionError) else "HOST_PERMISSION_OR_IO_DENIED"
        print(json.dumps({"state": "FAIL", "failure_class": code}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
