#!/usr/bin/env python3
"""Registered Docker Compose service operations for the existing Host-only UNIX writer.

No network transport, no Host Docker socket export and no shell invocation.
The writer must verify caller admission and resolve the entry from the protected
master-internal registry; never use request-supplied path or compose file.
"""
import re
import subprocess
from pathlib import Path

SERVICE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
COMPOSE_RE = re.compile(r"^[A-Za-z0-9_.-]+\.ya?ml$")
CONTAINER_ID_RE = re.compile(r"^[a-f0-9]{12,64}$")
ARG_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,512}$")
READ_OPS = frozenset({"ps", "inspect", "logs", "stats"})
WRITE_OPS = frozenset({"start", "stop", "restart", "up", "exec"})
OPS = READ_OPS | WRITE_OPS

class DockerOperationError(Exception):
    pass

def checked_service(entry, service):
    if not isinstance(entry, dict) or not isinstance(service, str) or not SERVICE_RE.fullmatch(service):
        raise DockerOperationError("TARGET_INVALID")
    runtime = entry.get("runtime_target")
    if not isinstance(runtime, dict):
        raise DockerOperationError("RUNTIME_NOT_REGISTERED")
    root = entry.get("server_project_path")
    compose_file = runtime.get("compose_file")
    if not isinstance(root, str) or not (
        root.startswith("/home/admin1/projects/") or root == "/home/admin1/server-core"
    ) or ".." in Path(root).parts:
        raise DockerOperationError("ROOT_NOT_REGISTERED")
    if not isinstance(compose_file, str) or not COMPOSE_RE.fullmatch(compose_file):
        raise DockerOperationError("COMPOSE_NOT_REGISTERED")
    registered = runtime.get("services")
    if not isinstance(registered, list) or not registered or any(
        not isinstance(x, str) or not SERVICE_RE.fullmatch(x) for x in registered
    ) or len(set(registered)) != len(registered):
        raise DockerOperationError("SERVICE_REGISTRY_INVALID")
    if service not in registered:
        raise DockerOperationError("SERVICE_NOT_REGISTERED")
    return ["docker", "compose", "--project-directory", root, "-f", str(Path(root) / compose_file)], root

def checked_argv(argv):
    if not isinstance(argv, list) or not 1 <= len(argv) <= 10:
        raise DockerOperationError("EXEC_ARGV_INVALID")
    if any(not isinstance(x, str) or not ARG_RE.fullmatch(x) for x in argv):
        raise DockerOperationError("EXEC_ARGV_INVALID")
    return list(argv)

def execute(command, root, timeout, runner):
    try:
        result = runner(command, cwd=root, text=True, capture_output=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise DockerOperationError("DOCKER_EXECUTION_UNAVAILABLE") from None
    if result.returncode != 0:
        raise DockerOperationError("DOCKER_OPERATION_FAILED")
    return result.stdout or "", result.stderr or ""

def operate(entry, service, operation, *, argv=None, tail=100, timeout=45, runner=None):
    """Perform one operation against an existing registered Compose service.

    Caller (Host writer) must check protected registry delegation, request ID,
    and mutation idempotency. This function never resolves arbitrary containers.
    """
    if not isinstance(operation, str) or operation not in OPS:
        raise DockerOperationError("OPERATION_DENIED")
    prefix, root = checked_service(entry, service)
    if type(timeout) is not int or not 1 <= timeout <= 45:
        raise DockerOperationError("TIMEOUT_INVALID")
    if type(tail) is not int or not 1 <= tail <= 200:
        raise DockerOperationError("TAIL_INVALID")
    if (operation == "exec") != (argv is not None):
        raise DockerOperationError("EXEC_ARGV_REQUIRED_OR_UNEXPECTED")
    command = {
        "ps": [*prefix, "ps", service],
        "inspect": [*prefix, "ps", "--format", "json", service],
        "logs": [*prefix, "logs", "--no-color", "--tail", str(tail), service],
        "start": [*prefix, "start", service],
        "stop": [*prefix, "stop", service],
        "restart": [*prefix, "restart", service],
        "up": [*prefix, "up", "--detach", "--no-deps", service],
    }.get(operation)
    run = runner or subprocess.run
    if operation == "stats":
        ids, _ = execute([*prefix, "ps", "--quiet", service], root, timeout, run)
        ids = ids.splitlines()
        if len(ids) != 1 or not CONTAINER_ID_RE.fullmatch(ids[0]):
            raise DockerOperationError("SERVICE_CONTAINER_ID_INVALID")
        command = ["docker", "stats", "--no-stream", "--format",
                   "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}", ids[0]]
    elif operation == "exec":
        command = [*prefix, "exec", "-T", service, *checked_argv(argv)]
    stdout, stderr = execute(command, root, timeout, run)
    return {"operation": operation, "service": service,
            "stdout": stdout[:4000], "stderr": stderr[:1000], "exit_code": 0}
