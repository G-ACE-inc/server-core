#!/usr/bin/env python3
"""Merge verified Project #1 VPS Git repos into existing protected Host writer Registry.

Never touches Master PC, KB consumer, ai-core runtime, other repository entries or
isolated dev.job workspace. One-use Host operation with fail-closed digest pin.
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
EXPECTED_DIGEST = "11dd50b161409982ca9b22cba52598cc8fcec3eeea7ac2313f8f516e47e5a45f"
BACKUP = Path("/home/admin1/logs/servercore-service-deploy/registry-before-project1-enroll-20261013.json")
UNIT = "gace-servercore-service-deploy.service"
SOCKET = Path("/run/gace/servercore-service-deploy.sock")
NEW = {
    "seigo-gace/asteria": "/home/admin1/projects/asteria",
    "seigo-gace/astera_v8": "/home/admin1/projects/astera_v8",
    "seigo-gace/astera-app": "/home/admin1/projects/astera-app",
    "seigo-gace/modular-catalog": "/home/admin1/projects/Catalog/modular-catalog",
    "seigo-gace/Deterministic-Japanese-Parser-MCP": "/home/admin1/projects/Deterministic-Japanese-Parser-MCP",
    "seigo-gace/Libral-Vault": "/home/admin1/projects/libral-vault",
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(*args):
    p = subprocess.run(args, text=True, capture_output=True, timeout=30, check=False)
    if p.returncode:
        raise ValueError("HOST_CHECK_FAILED")
    return p.stdout.strip()

def verify_checkout(repo, raw):
    root = Path(raw)
    if not root.is_dir() or root.is_symlink() or root.resolve() != root or not (root / ".git").is_dir():
        raise ValueError("CHECKOUT_NOT_READY")
    top = run("git", "-C", raw, "rev-parse", "--show-toplevel")
    if top != raw:
        raise ValueError("CHECKOUT_TOPLEVEL_MISMATCH")
    remote = run("git", "-C", raw, "remote", "get-url", "origin")
    accepted = {
        "https://github.com/" + repo + ".git", "https://github.com/" + repo,
        "git@github.com:" + repo + ".git",
        "git@github.com-server-core:" + repo + ".git"
    }
    if remote not in accepted:
        raise ValueError("CHECKOUT_REMOTE_MISMATCH")

def main():
    status, error, before, changed = "FAIL", "UNKNOWN", "UNKNOWN", False
    try:
        if len(sys.argv) != 2 or run("git", "-C", str(ROOT), "rev-parse", "HEAD") != sys.argv[1]:
            raise ValueError("HOST_HEAD_MISMATCH")
        before = digest(REGISTRY)
        if before != EXPECTED_DIGEST:
            raise ValueError("REGISTRY_CHANGED")
        if BACKUP.exists() or BACKUP.is_symlink():
            raise ValueError("BACKUP_ALREADY_EXISTS")
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = data.get("repositories")
        if not isinstance(entries, list):
            raise ValueError("REGISTRY_INVALID")
        repos = [entry.get("repository") for entry in entries]
        if len(repos) != len(set(repos)) or len(repos) != 4 or set(repos) & set(NEW):
            raise ValueError("REGISTRY_SCOPE_CHANGED")
        for repo, root in NEW.items():
            verify_checkout(repo, root)
        for repo, root in NEW.items():
            entries.append({
                "schema": "debugai.master-internal-delegation/v1",
                "id": "dlg_project1_" + repo.split("/")[-1].lower().replace("-", "_"),
                "delegation_mode": "MASTER_INTERNAL_PERSISTENT",
                "repository": repo,
                "server_project_path": root,
                "enabled": True, "revoked": False,
                "allowed_operations": ["host.command"],
            })
        BACKUP.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(BACKUP, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(REGISTRY.read_bytes())
        fd, tmp = tempfile.mkstemp(dir=REGISTRY.parent, prefix=".project1-enroll-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            os.chmod(tmp, REGISTRY.stat().st_mode & 0o777)
            os.replace(tmp, REGISTRY)
            changed = True
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        run("systemctl", "--user", "restart", UNIT)
        if run("systemctl", "--user", "is-active", UNIT) != "active" or not SOCKET.is_socket():
            raise ValueError("WRITER_NOT_READY")
        status, error = "PASS", "NONE"
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        error = str(exc) if isinstance(exc, ValueError) else "ENROLLMENT_IO_FAILED"
        if changed and BACKUP.is_file() and digest(BACKUP) == EXPECTED_DIGEST:
            shutil.copy2(BACKUP, REGISTRY)
            try: subprocess.run(["systemctl", "--user", "restart", UNIT], timeout=30, check=False)
            except (OSError, subprocess.TimeoutExpired): pass
    print("========== GACE_RESULT_BEGIN ==========")
    for key, value in {
        "PROJECT": "server-core", "ACTION": "HOST_PROJECT1_REPO_ENROLL",
        "REGISTRY_BEFORE": before,
        "REGISTRY_AFTER": digest(REGISTRY) if REGISTRY.is_file() else "UNKNOWN",
        "BACKUP_EXISTS": str(BACKUP.is_file()).upper(),
        "NEW_REGISTERED_REPOS": ",".join(NEW) if status == "PASS" else "NONE",
        "WRITER_SOCKET": str(SOCKET.is_socket()).upper(),
        "VERIFY": status, "EXIT_CODE": "0" if status == "PASS" else "1",
        "ERROR": error, "PROJECT_END": "server-core",
    }.items(): print(key + "=" + value)
    print("========== GACE_RESULT_END ==========")
    return 0 if status == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
