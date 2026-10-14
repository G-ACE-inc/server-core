#!/usr/bin/env python3
"""Host-local fixed-service Compose deploy using approved registry admission.

Never exposed to network or the existing read-only Receiver. No shell invocation.
Requires separately approved Host service permission and explicit --apply.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from servercore_service_deploy_admission import (
    AdmissionError, REGISTRY, SHA, inspect_host,
)


def command(args, *, timeout=120):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise AdmissionError("HOST_EXECUTION_FAILED") from None
    if result.returncode:
        raise AdmissionError("HOST_COMMAND_FAILED")
    return result.stdout.strip()



def wait_for_service_health(container_id, *, timeout_seconds=120, poll_seconds=2):
    """Compose may return before Docker's health start period completes."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        status = command(["docker", "inspect", "--format", "{{.State.Status}}", container_id], timeout=15)
        if status != "running":
            raise AdmissionError("SERVICE_RUNTIME_MISMATCH")
        health = command(["docker", "inspect", "--format",
                          "{{if .State.Health}}{{.State.Health.Status}}{{else}}NONE{{end}}",
                          container_id], timeout=15)
        if health in {"healthy", "NONE"}:
            return health
        if health not in {"starting", "unhealthy"}:
            raise AdmissionError("SERVICE_HEALTH_STATUS_INVALID")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdmissionError("SERVICE_HEALTH_NOT_READY")
        time.sleep(min(poll_seconds, remaining))


def deploy(registry, repository, target_sha, service, *, apply=False):
    a = inspect_host(registry, repository, target_sha, service)
    root = a["root"]
    compose = a["compose_file"]
    prefix = ["docker", "compose", "--project-directory", root, "-f", str(Path(root) / compose)]
    # Validate project-owned Compose topology before any apply. No arbitrary service name.
    services = command([*prefix, "config", "--services"], timeout=45).splitlines()
    if service not in services:
        raise AdmissionError("COMPOSE_SERVICE_MISMATCH")
    if not apply:
        return {"state": "SERVICE_DEPLOY_PREFLIGHT_PASS", "repository": repository,
                "service": service, "source_sha": target_sha, "mutation_performed": False}
    # Exact source+Compose hash must still be stable after preflight.
    inspected = inspect_host(registry, repository, target_sha, service)
    if inspected["compose_digest"] != a["compose_digest"]:
        raise AdmissionError("COMPOSE_CHANGED_DURING_PREFLIGHT")
    command([*prefix, "up", "--detach", "--no-deps", "--build", service], timeout=900)
    # Docker Compose ps ID must correspond to the registered service (not arbitrary docker ps).
    ids = command([*prefix, "ps", "--quiet", service], timeout=30).splitlines()
    if len(ids) != 1 or not re.fullmatch(r"[a-f0-9]{12,64}", ids[0]):
        raise AdmissionError("COMPOSE_CONTAINER_ID_MISSING")
    container_id = ids[0]
    label = command(["docker", "inspect", "--format",
                     '{{index .Config.Labels "com.docker.compose.service"}}', container_id], timeout=15)
    status = command(["docker", "inspect", "--format", "{{.State.Status}}", container_id], timeout=15)
    if label != service or status != "running":
        raise AdmissionError("SERVICE_RUNTIME_MISMATCH")
    health = wait_for_service_health(container_id)
    return {"state": "SERVICE_DEPLOY_RUNTIME_RUNNING", "repository": repository,
            "service": service, "source_sha": target_sha, "container_id": container_id,
            "health": health, "mutation_performed": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository", required=True)
    ap.add_argument("--target-sha", required=True)
    ap.add_argument("--service", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    try:
        result = deploy(json.loads(REGISTRY.read_text()), args.repository, args.target_sha,
                        args.service, apply=args.apply)
        print(json.dumps(result, sort_keys=True))
    except (AdmissionError, OSError, ValueError):
        print(json.dumps({"state": "FAIL", "failure_class": "SERVICE_DEPLOY_DENIED"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
