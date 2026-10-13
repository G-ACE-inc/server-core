#!/usr/bin/env python3
"""Source-reflect admission from the protected master-internal registry only."""
import json
from pathlib import Path
import re

REGISTRY = Path("/home/admin1/server-core/operations/master-internal-repositories.json")
SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class AdmissionError(ValueError):
    pass


def _delegation_entry(registry, repository):
    if not isinstance(registry, dict) or not isinstance(registry.get("repositories"), list):
        raise AdmissionError("REGISTRY_INVALID")
    matches = [x for x in registry["repositories"]
               if isinstance(x, dict) and x.get("repository") == repository]
    if len(matches) != 1:
        raise AdmissionError("REGISTERED_REPOSITORY_NOT_UNIQUE")
    return matches[0]


def require_reflect(registry, repository, branch, target_sha):
    if not isinstance(repository, str) or not REPO.fullmatch(repository):
        raise AdmissionError("REPOSITORY_INVALID")
    if not isinstance(branch, str) or not branch or branch.startswith("-") or ".." in branch:
        raise AdmissionError("BRANCH_INVALID")
    if not isinstance(target_sha, str) or not SHA.fullmatch(target_sha):
        raise AdmissionError("TARGET_SHA_INVALID")
    entry = _delegation_entry(registry, repository)
    if entry.get("enabled") is not True or entry.get("revoked") is not False:
        raise AdmissionError("DELEGATION_DISABLED")
    if entry.get("delegation_mode") != "MASTER_INTERNAL_PERSISTENT" or entry.get("allow_production") is not True:
        raise AdmissionError("DELEGATION_AUTHORITY_DENIED")
    if "reflect" not in entry.get("allowed_operations", []):
        raise AdmissionError("REFLECT_OPERATION_NOT_REGISTERED")
    branches = entry.get("allowed_branches")
    if not isinstance(branches, list) or branch not in branches:
        raise AdmissionError("BRANCH_NOT_ALLOWED")
    remote = entry.get("remote")
    if not isinstance(remote, str) or remote != "https://github.com/" + repository + ".git":
        raise AdmissionError("REGISTERED_REMOTE_INVALID")
    root = Path(str(entry.get("server_project_path", "")))
    if not root.is_absolute() or root.is_symlink() or ".." in root.parts:
        raise AdmissionError("HOST_REPOSITORY_PATH_DENIED")
    if not (str(root) == "/home/admin1/server-core" or str(root).startswith("/home/admin1/projects/")):
        raise AdmissionError("HOST_REPOSITORY_PATH_DENIED")
    runtime = entry.get("runtime_target") or {}
    if runtime.get("kind") != "source_only":
        raise AdmissionError("REFLECT_RUNTIME_NOT_SOURCE_ONLY")
    allowed_origins = frozenset({
        remote,
        "git@github.com:" + repository + ".git",
        "git@github.com-server-core:" + repository + ".git",
    })
    return {
        "repository": repository,
        "branch": branch,
        "target_sha": target_sha,
        "root": root,
        "remote": remote,
        "allowed_origins": allowed_origins,
        "runtime_target_id": runtime.get("id"),
        "delegation_id": entry.get("id"),
    }


def load_registry(path=REGISTRY):
    return json.loads(Path(path).read_text(encoding="utf-8"))
