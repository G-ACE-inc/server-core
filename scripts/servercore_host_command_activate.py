#!/usr/bin/env python3
"""Activate existing Host terminal authority, preserving protected Registry bytes on failure.

Host-only, one-time. Reuses existing systemd writer. Never touches dev.job or Docker containers.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path("/home/admin1/server-core")
REGISTRY = ROOT / "operations/master-internal-repositories.json"
BACKUP = Path("/home/admin1/logs/servercore-service-deploy/registry-before-host-command-20261013.json")
EXPECTED_BEFORE = "451d65c5ff704ebd3441b7a9b8e755afee03e05d095a99683d01f41cf18027f1"
UNIT = "gace-servercore-service-deploy.service"
SOCKET = Path("/run/gace/servercore-service-deploy.sock")
REPOS = {"seigo-gace/debug-ai", "G-ACE-inc/server-core",
         "seigo-gace/TGserver", "seigo-gace/webhook-gateway"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def cmd(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=35, check=False)

def report(state, error, original, before, after):
    print("========== GACE_RESULT_BEGIN ==========")
    print("PROJECT=server-core")
    print("PWD=" + str(ROOT))
    print("ACTION=HOST_COMMAND_ACTIVATE")
    print("HOST_HEAD=" + (original or "UNKNOWN"))
    print("REGISTRY_BEFORE=" + before)
    print("REGISTRY_AFTER=" + after)
    print("BACKUP_EXISTS=" + str(BACKUP.is_file()).upper())
    print("WRITER_ACTIVE=" + str(cmd("systemctl", "--user", "is-active", UNIT).stdout.strip() == "active").upper())
    print("WRITER_SOCKET=" + str(SOCKET.is_socket()).upper())
    print("VERIFY=" + state)
    print("EXIT_CODE=" + ("0" if state == "PASS" else "1"))
    print("ERROR=" + error)
    print("PROJECT_END=server-core")
    print("========== GACE_RESULT_END ==========")

def main():
    head, before, changed, error = "", "UNKNOWN", False, "UNKNOWN"
    try:
        if ROOT.is_symlink() or ROOT.resolve() != ROOT or not (ROOT / ".git").is_dir():
            raise ValueError("CANONICAL_ROOT_DENIED")
        head = cmd("git", "-C", str(ROOT), "rev-parse", "HEAD").stdout.strip()
        if len(sys.argv) != 2 or head != sys.argv[1] or len(head) != 40:
            raise ValueError("HOST_SHA_CHANGED")
        before = sha(REGISTRY)
        if before != EXPECTED_BEFORE:
            raise ValueError("REGISTRY_SHA_CHANGED")
        if BACKUP.exists() or BACKUP.is_symlink():
            raise ValueError("BACKUP_ALREADY_EXISTS")
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = data.get("repositories")
        if not isinstance(entries, list) or len(entries) != 4 or {e.get("repository") for e in entries} != REPOS:
            raise ValueError("REGISTRY_REPO_SET_CHANGED")
        for e in entries:
            if e.get("enabled") is not True or e.get("revoked") is not False or e.get("delegation_mode") != "MASTER_INTERNAL_PERSISTENT" or not isinstance(e.get("allowed_operations"), list):
                raise ValueError("REGISTRY_AUTHORITY_CHANGED")
            if "host.command" not in e["allowed_operations"]:
                e["allowed_operations"].append("host.command")
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(BACKUP, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(REGISTRY.read_bytes())
        fd, temp = tempfile.mkstemp(prefix=".registry-activation-", dir=REGISTRY.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.chmod(temp, REGISTRY.stat().st_mode & 0o777)
            os.replace(temp, REGISTRY)
            changed = True
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        restart = cmd("systemctl", "--user", "restart", UNIT)
        if restart.returncode or cmd("systemctl", "--user", "is-active", UNIT).stdout.strip() != "active" or not SOCKET.is_socket():
            raise ValueError("WRITER_RESTART_FAILED")
        error = "NONE"
        report("PASS", error, head, before, sha(REGISTRY))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        error = str(exc) if isinstance(exc, ValueError) else "HOST_ACTIVATION_IO_FAILED"
        if changed and BACKUP.is_file() and sha(BACKUP) == EXPECTED_BEFORE:
            shutil.copy2(BACKUP, REGISTRY)
            try:
                cmd("systemctl", "--user", "restart", UNIT)
            except (OSError, subprocess.TimeoutExpired):
                pass
        report("FAIL", error, head, before, sha(REGISTRY) if REGISTRY.is_file() else "UNKNOWN")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
