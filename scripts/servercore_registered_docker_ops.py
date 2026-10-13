#!/usr/bin/env python3
"""Docker/Compose operations for a registered service, never a raw Docker socket to CHAT.

This module deliberately does not publish a receiver command: the existing
Host-local writer must validate and authorize each request before calling it.
"""
import re
import subprocess
from pathlib import Path

SERVICE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
SAFE_ARG = re.compile(r"^[^\x00-\x1f\x7f]{1,512}$")
READ_OPS = frozenset({"ps", "inspect", "logs", "stats", "exec"})
WRITE_OPS = frozenset({"start", "stop", "restart", "build", "up"})
OPS = READ_OPS | WRITE_OPS

class DockerOperationError(Exception):
    pass

def checked_service(entry, service):
    """Verify requested service against the existing registry-owned Compose scope."""
    if not isinstance(entry, dict) or not isinstance(service, str) or not SERVICE_RE.fullmatch(service):
        raise DockerOperationError("TARGET_INVALID")
    runtime = entry.get("runtime_target") or {}
    root = entry.get("server_project_path")
    compose_file = runtime.get("compose_file")
    if not isinstance(root, str) or not root.startswith("/home/admin1/") or ".." in Path(root).parts:
        raise DockerOperationError("ROOT_NOT_REGISTERED")
    if not isinstance(compose_file, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+\\.ya?ml", compose_file):
        raise DockerOperationError("COMPOSE_NOT_REGISTERED")
    configured = runtime.get("services")
    if configured is None:
        configured = [runtime.get("service")]
    if service not in configured:
        raise DockerOperationError("SERVICE_NOT_REGISTERED")
    return ["docker", "compose", "--project-directory", root, "-f", str(Path(root) / compose_file)], root

def checked_argv(argv):
    if not isinstance(argv, list) or not 1 <= len(argv) <= 12:
        raise DockerOperationError("EXEC_ARGV_INVALID")
    if any(not isinstance(s, str) or not SAFE_ARG.fullmatch(s) or len(s) > 512 for s in argv):
        raise DockerOperationError("EXEC_ARGV_INVALID")
    return argv

def operate(entry, service, operation, *, argv=None, tail=100, timeout=45, runner=None):
    """Run a bounded, service-scoped operation; caller owns authorization and audit.

    No shell=True, no arbitrary docker flags, no compose down/volume removal.
    'exec' can execute arbitrary code inside an admitted container and therefore
    must be exposed ONLY through an explicit separately authorized Host path.
    """
    if operation not in OPS:
        raise DockerOperationError("OPERATION_DENIED")
    prefix, root = checked_service(entry, service)
    if type(timeout) is not int or not 1 <= timeout <= 900:
        raise DockerOperationError("TIMEOUT_INVALID")
    if type(tail) is not int or not 1 <= tail <= 200:
        raise DockerOperationError("TAIL_INVALID")
    if argv is not None and operation != "exec":
        raise DockerOperationError("UNEXPECTED_ARGV")
    commands = {
        "ps": [*prefix, "ps", service],
        "inspect": [*prefix, "ps", "--format", "json", service],
        "logs": [*prefix, "logs", "--no-color", "--tail", str(tail), service],
        "stats": [*prefix, "ps", "--format", "json", service],
        "start": [*prefix, "start", service],
        "stop": [*prefix, "stop", service],
        "restart": [*prefix, "restart", service],
        "build": [*prefix, "build", service],
        "up": [*prefix, "up", "--detach", "--no-deps", service],
    }
    if operation == "exec":
        if argv is None:
            raise DockerOperationError("EXEC_ARGV_REQUIRED")
        commands["exec"] = [*prefix, "exec", "-T", service, *checked_argv(argv)]
    command = commands[operation]
    proc = (runner or subprocess.run)(command, cwd=root, text=True, capture_output=True,
                                      timeout=timeout, check=False)
    if proc.returncode:
        raise DockerOperationError("DOCKER_OPERATION_FAILED")
    return {"operation": operation, "service": service, "stdout": proc.stdout[:4000],
            "stderr": proc.stderr[:1000], "exit_code": proc.returncode}
