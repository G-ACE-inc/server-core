#!/usr/bin/env python3
"""Apply only the existing Webhook API Host admission delta to the protected registry.

Run through the admitted Host operator after exact-SHA source review. Neither
the GitHub registry snapshot nor this tool overwrites Host-only registrations.
No secrets, service restarts, or Docker effects are performed here.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

ROOT = Path("/home/admin1/server-core")
REGISTRY = ROOT / "operations/master-internal-repositories.json"
BACKUP_DIR = Path("/home/admin1/logs/servercore-service-deploy")
LOCK = Path("/tmp/gace-webhook-api-admission.lock")
REPO = "seigo-gace/webhook-gateway"
COMPOSE_DIGEST = "e0a877658e9d5cdffd112d5077c25773cce7496065125d8eb7ac00429e903d25"


class AdmissionError(ValueError):
    pass


def sha256(contents):
    return hashlib.sha256(contents).hexdigest()


def upgrade(data, phase):
    if phase not in ("reflect", "deploy") or not isinstance(data, dict):
        raise AdmissionError("PHASE_INVALID")
    result = copy.deepcopy(data)
    entries = result.get("repositories")
    if not isinstance(entries, list):
        raise AdmissionError("REGISTRY_INVALID")
    hits = [entry for entry in entries if isinstance(entry, dict) and entry.get("repository") == REPO]
    if len(hits) != 1:
        raise AdmissionError("TARGET_NOT_UNIQUE")
    entry = hits[0]
    runtime = entry.get("runtime_target")
    effects = entry.get("effects")
    if (entry.get("enabled") is not True or entry.get("revoked") is not False
            or entry.get("allow_production") is not True
            or entry.get("delegation_mode") != "MASTER_INTERNAL_PERSISTENT"
            or entry.get("server_project_path") != "/home/admin1/projects/webhook-gateway"
            or entry.get("remote") != "https://github.com/" + REPO + ".git"
            or "main" not in entry.get("allowed_branches", [])
            or not isinstance(runtime, dict) or runtime.get("id") != "webhook-gateway.compose"
            or runtime.get("compose_file") != "docker-compose.yml"
            or runtime.get("compose_digest") != COMPOSE_DIGEST
            or runtime.get("services") != ["api", "worker", "postgres"]
            or not isinstance(effects, dict) or effects.get("secrets") is not False
            or not isinstance(entry.get("allowed_operations"), list)
            or not isinstance(entry.get("allowed_scopes"), list)):
        raise AdmissionError("TARGET_IDENTITY_CHANGED")
    operations = entry["allowed_operations"]
    scopes = entry["allowed_scopes"]
    if "host.command" not in operations or "docker.operation" not in operations:
        raise AdmissionError("EXISTING_HOST_GRANT_MISSING")
    if phase == "deploy" and ("reflect" not in operations or runtime.get("source_reflect") is not True):
        raise AdmissionError("SOURCE_REFLECT_NOT_ENABLED")
    if phase == "deploy" and runtime.get("deploy_services", ["api"]) != ["api"]:
        raise AdmissionError("DEPLOY_SERVICES_CHANGED")
    permission = "reflect" if phase == "reflect" else "deploy"
    scope = "gace.source.reflect" if phase == "reflect" else "gace.service.deploy"
    if permission not in operations:
        operations.append(permission)
    if scope not in scopes:
        scopes.append(scope)
    if phase == "reflect":
        runtime["source_reflect"] = True
    else:
        runtime["deploy_services"] = ["api"]
    return result


def activate(path, expected_sha, phase, *, apply=False, backup_dir=BACKUP_DIR, lock_path=LOCK):
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise AdmissionError("EXPECTED_HASH_INVALID")
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise AdmissionError("REGISTRY_PATH_INVALID")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "r+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        original = path.read_bytes()
        before = sha256(original)
        if before != expected_sha:
            raise AdmissionError("REGISTRY_SHA_MISMATCH")
        payload = upgrade(json.loads(original), phase)
        after_bytes = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
        after = sha256(after_bytes)
        if apply and after != before:
            backup_dir = Path(backup_dir)
            if not backup_dir.is_dir() or backup_dir.is_symlink():
                raise AdmissionError("BACKUP_DIRECTORY_UNAVAILABLE")
            backup = backup_dir / ("registry-before-gateway-" + phase + "-" + before[:16] + ".json")
            descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
            tmp = None
            try:
                descriptor, tmp = tempfile.mkstemp(prefix=".webhook-admission-", dir=path.parent)
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(after_bytes)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(tmp, path.stat().st_mode & 0o777)
                os.replace(tmp, path)
            finally:
                if tmp and os.path.exists(tmp):
                    os.unlink(tmp)
        return {"state": "PASS", "phase": phase, "dry_run": not apply,
                "before": before, "after": after, "changed": before != after}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--phase", required=True, choices=("reflect", "deploy"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = activate(REGISTRY, args.expected_sha256, args.phase, apply=args.apply)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (AdmissionError, ValueError, OSError, json.JSONDecodeError):
        print(json.dumps({"state": "FAIL", "error": "PROTECTED_REGISTRY_ADMISSION_DENIED"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
