#!/usr/bin/env python3
"""Registered service deploy admission — read-only authorization/preflight.

This module does NOT execute Docker, mutate a checkout, or grant a receiver
new permissions. A later, separately authorized Host executor may consume its
validated fixed service mapping. Never infer deploy ownership from docker ps.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

REGISTRY = Path("/home/admin1/server-core/operations/master-internal-repositories.json")
SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class AdmissionError(ValueError):
    pass


def require_registered(registry, repository, target_sha, service, *, permission="deploy"):
    if not isinstance(repository, str) or not REPO.fullmatch(repository):
        raise AdmissionError("REPOSITORY_INVALID")
    if not isinstance(target_sha, str) or not SHA.fullmatch(target_sha):
        raise AdmissionError("TARGET_SHA_INVALID")
    if not isinstance(service, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,62}", service):
        raise AdmissionError("SERVICE_INVALID")
    if not isinstance(registry, dict) or not isinstance(registry.get("repositories"), list):
        raise AdmissionError("REGISTRY_INVALID")
    matches = [x for x in registry["repositories"] if isinstance(x, dict) and x.get("repository") == repository]
    if len(matches) != 1:
        raise AdmissionError("REGISTERED_REPOSITORY_NOT_UNIQUE")
    entry = matches[0]
    if entry.get("enabled") is not True or entry.get("revoked") is not False:
        raise AdmissionError("DELEGATION_DISABLED")
    if entry.get("delegation_mode") != "MASTER_INTERNAL_PERSISTENT" or entry.get("allow_production") is not True:
        raise AdmissionError("DELEGATION_AUTHORITY_DENIED")
    grants = entry.get("allowed_operations", [])
    if permission == "deploy":
        if "deploy" not in grants:
            raise AdmissionError("DEPLOY_OPERATION_NOT_REGISTERED")
    elif permission == "docker.operation":
        # Preserve the already-qualified DebugAI legacy grant, without allowing
        # new per-repository Docker rights to imply image build/deploy rights.
        if "docker.operation" not in grants and not (
            repository == "seigo-gace/debug-ai" and "deploy" in grants
        ):
            raise AdmissionError("DOCKER_OPERATION_NOT_REGISTERED")
    else:
        raise AdmissionError("OPERATION_PERMISSION_INVALID")
    runtime = entry.get("runtime_target")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("services"), list):
        raise AdmissionError("DEPLOY_RUNTIME_NOT_REGISTERED")
    if service not in runtime["services"] or len(set(runtime["services"])) != len(runtime["services"]):
        raise AdmissionError("SERVICE_NOT_REGISTERED")
    # Deployment can be more restricted than registered Docker read/status.
    if permission == "deploy" and "deploy_services" in runtime:
        permitted = runtime["deploy_services"]
        if (not isinstance(permitted, list) or not permitted
                or any(not isinstance(item, str) or item not in runtime["services"] for item in permitted)
                or len(set(permitted)) != len(permitted) or service not in permitted):
            raise AdmissionError("DEPLOY_SERVICE_NOT_REGISTERED")
    compose = runtime.get("compose_file")
    digest = runtime.get("compose_digest")
    if not isinstance(compose, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+\.ya?ml", compose):
        raise AdmissionError("COMPOSE_PATH_INVALID")
    if not isinstance(digest, str) or not SHA.fullmatch(digest) and not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise AdmissionError("COMPOSE_DIGEST_INVALID")
    path = entry.get("server_project_path")
    if not isinstance(path, str) or not path.startswith("/home/admin1/projects/") or ".." in Path(path).parts:
        raise AdmissionError("HOST_REPOSITORY_PATH_DENIED")
    remote = entry.get("remote")
    branches = entry.get("allowed_branches")
    if not isinstance(remote, str) or remote != "https://github.com/" + repository + ".git":
        raise AdmissionError("REGISTERED_REMOTE_INVALID")
    if not isinstance(branches, list) or not branches or any(not isinstance(x, str) or not x for x in branches):
        raise AdmissionError("REGISTERED_BRANCHES_INVALID")
    return {"remote": remote, "allowed_branches": list(branches),
            "repository": repository, "target_sha": target_sha, "service": service,
            "root": path, "compose_file": compose, "compose_digest": digest,
            "health_service": runtime.get("health_service"), "health_url": runtime.get("health_url")}


def inspect_host(registry, repository, target_sha, service):
    admission = require_registered(registry, repository, target_sha, service)
    root = Path(admission["root"])
    if root.is_symlink() or not root.is_dir() or not (root / ".git").is_dir():
        raise AdmissionError("HOST_CHECKOUT_INVALID")
    compose = root / admission["compose_file"]
    if compose.is_symlink() or not compose.is_file() or compose.resolve().parent != root.resolve():
        raise AdmissionError("COMPOSE_FILE_NOT_CANONICAL")
    if hashlib.sha256(compose.read_bytes()).hexdigest() != admission["compose_digest"]:
        raise AdmissionError("COMPOSE_DIGEST_MISMATCH")
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "safe.directory=" + str(root), "-C", str(root)]
    def read_git(*args):
        result = subprocess.run([*cmd, *args], capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise AdmissionError("HOST_GIT_READ_FAILED")
        return result.stdout.strip()
    if read_git("remote", "get-url", "origin") != admission["remote"]:
        raise AdmissionError("HOST_ORIGIN_MISMATCH")
    if read_git("symbolic-ref", "--short", "HEAD") not in admission["allowed_branches"]:
        raise AdmissionError("HOST_BRANCH_DENIED")
    if read_git("rev-parse", "HEAD") != target_sha:
        raise AdmissionError("HOST_SOURCE_SHA_MISMATCH")
    if read_git("status", "--porcelain"):
        raise AdmissionError("HOST_CHECKOUT_DIRTY")
    return {**admission, "state": "DEPLOY_ADMISSION_PREFLIGHT_PASS", "mutation_performed": False}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository", required=True)
    ap.add_argument("--target-sha", required=True)
    ap.add_argument("--service", required=True)
    args = ap.parse_args()
    try:
        result = inspect_host(json.loads(REGISTRY.read_text()), args.repository, args.target_sha, args.service)
        print(json.dumps(result, sort_keys=True))
    except (AdmissionError, OSError, ValueError, subprocess.TimeoutExpired):
        print(json.dumps({"state":"FAIL", "failure_class":"DEPLOY_ADMISSION_DENIED"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
