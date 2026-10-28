#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import socket
import stat
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from gace_internal_delivery_auth import DeliveryAuthError, read_delivery_key, verify_delivery

import servercore_bounded_host as bounded_host

RECEIVER_PATH = "/internal/servercore-bounded-host"
HEALTH_PATH = "/healthz"
CIPHER_PATH = "/internal/servercore-host-output"
CIPHER_DESTINATION = "server-core-host-output"
EXPECTED_DESTINATION = "server-core-bounded-host"
MAX_BODY_BYTES = 1048576
# Deterministic Host preflight denials must not enter infrastructure retry loops.
TERMINAL_REFLECT_ERRORS = frozenset({
    "BEFORE_SHA_MISMATCH", "DIRTY_CHECKOUT_DENIED", "REMOTE_BRANCH_SHA_MISMATCH",
    "NON_FAST_FORWARD_DENIED", "ORIGIN_REMOTE_DENIED", "BRANCH_NOT_ALLOWED",
    "CANONICAL_ROOT_DENIED", "GIT_CHECKOUT_MISSING", "SHA_INVALID",
    "REFLECT_OPERATION_NOT_REGISTERED", "BRANCH_NOT_ALLOWED", "BRANCH_INVALID",
    "REFLECT_RUNTIME_NOT_SOURCE_ONLY", "REGISTERED_REPOSITORY_NOT_UNIQUE",
})
DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "operations" / "github-project-bounded-host.json"
REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{24}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
SERVICE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
DEPLOY_SOCKET = "/run/gace/servercore-service-deploy.sock"
# Publish only fixed admission codes, never arbitrary writer exception text.
HOST_COMMAND_ADMISSION_ERRORS = frozenset({
    "HOST_COMMAND_NOT_REGISTERED", "HOST_COMMAND_ROOT_INVALID",
    "HOST_COMMAND_SHA_MISMATCH", "HOST_COMMAND_KEYS_INVALID",
    "HOST_COMMAND_INVALID", "HOST_SOURCE_PREFLIGHT_INVALID",
    "REPOSITORY_INVALID", "TARGET_SHA_INVALID", "REQUEST_INVALID",
})
DOCKER_LOGS_SOCKET = "/run/gace/servercore-docker-logs.sock"
DEV_JOB_SOCKET = "/run/gace/servercore-dev-job.sock"
DEV_JOB_RETRYABLE = frozenset({"DOCKER_BINARY_MISSING", "INTERNAL_ERROR", "DEV_JOB_BUSY", "WORKSPACE_CREATE_FAILED", "HOST_GIT_FAILED"})
FILE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]{0,159}$")
CONTAINER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
RESULT_SOCKET = "/run/gace/servercore-result.sock"
RESULT_SCHEMA = "gace.servercore-bounded-result.record/v1"
COMMAND_PATTERN = re.compile(r"^[a-z][a-z0-9_.]{2,63}$")


class ReceiverError(RuntimeError):
    def __init__(self, code, status):
        super().__init__(code)
        self.code = code
        self.status = status


def fail(code, status):
    raise ReceiverError(code, status)


def load_contract(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit("CONTRACT_JSON_INVALID") from exc


def validate_request(value, contract):
    if not isinstance(value, dict):
        fail("REQUEST_SHAPE_INVALID", 422)
    if value.get("schema") != contract.get("request_schema"):
        fail("REQUEST_SCHEMA_INVALID", 422)
    req_id = value.get("id")
    if not isinstance(req_id, str) or not REQUEST_ID_PATTERN.match(req_id):
        fail("REQUEST_ID_INVALID", 422)
    command_id = value.get("command_id")
    allowed = contract.get("allowed_command_ids") or []
    if command_id not in allowed:
        fail("COMMAND_NOT_REGISTERED", 422)
    expected_sha = value.get("expected_sha")
    if not isinstance(expected_sha, str) or not SHA_PATTERN.match(expected_sha):
        fail("EXPECTED_SHA_INVALID", 422)
    if command_id == "project.source_reflect":
        base_keys = {"schema", "id", "command_id", "expected_sha", "expected_before"}
        extra = set(value) - base_keys
        if extra - {"repository", "branch"}:
            fail("REFLECT_KEYS_INVALID", 422)
        if not base_keys <= set(value):
            fail("REFLECT_KEYS_INVALID", 422)
        before = value["expected_before"]
        if not isinstance(before, str) or not SHA_PATTERN.match(before):
            fail("REFLECT_BEFORE_INVALID", 422)
        repository = value.get("repository", "G-ACE-inc/server-core")
        branch = value.get("branch", "main")
        if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository)                 or not isinstance(branch, str) or not branch or branch.startswith("-") or ".." in branch:
            fail("REFLECT_TARGET_INVALID", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha,
                "expected_before": before, "repository": repository, "branch": branch}
    if command_id == "service.deploy":
        if set(value) != {"schema", "id", "command_id", "expected_sha", "repository", "service"}:
            fail("DEPLOY_KEYS_INVALID", 422)
        repository, service = value["repository"], value["service"]
        if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository) \
                or not isinstance(service, str) or not SERVICE_PATTERN.fullmatch(service):
            fail("DEPLOY_TARGET_INVALID", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha,
                "repository": repository, "service": service}
    if command_id == "service.deploy_status":
        if set(value) != {"schema", "id", "command_id", "expected_sha", "deploy_request_id"}:
            fail("DEPLOY_STATUS_KEYS_INVALID", 422)
        deploy_id = value["deploy_request_id"]
        if not isinstance(deploy_id, str) or not REQUEST_ID_PATTERN.match(deploy_id):
            fail("DEPLOY_STATUS_ID_INVALID", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha,
                "deploy_request_id": deploy_id}
    if command_id == "project.file_inspect":
        if set(value) != {"schema", "id", "command_id", "expected_sha", "path", "offset"}:
            fail("FILE_INSPECT_KEYS_INVALID", 422)
        path, offset = value["path"], value["offset"]
        if not isinstance(path, str) or not FILE_PATH_PATTERN.fullmatch(path) or ".." in path \
                or type(offset) is not int or not 0 <= offset <= 4_000_000:
            fail("FILE_INSPECT_TARGET_INVALID", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha, "path": path, "offset": offset}
    if command_id == "docker.operation":
        if set(value) != {"schema", "id", "command_id", "expected_sha", "repository",
                           "service", "operation", "argv", "tail"}:
            fail("DOCKER_OPERATION_KEYS_INVALID", 422)
        repo, service, operation, argv, tail = (
            value["repository"], value["service"], value["operation"], value["argv"], value["tail"])
        if not isinstance(repo, str) or not REPOSITORY_PATTERN.fullmatch(repo) \
                or not isinstance(service, str) or not SERVICE_PATTERN.fullmatch(service):
            fail("DOCKER_OPERATION_TARGET_INVALID", 422)
        if not isinstance(operation, str) or operation not in {
                "ps", "inspect", "logs", "stats", "start", "stop", "restart", "up", "exec"}:
            fail("DOCKER_OPERATION_UNSUPPORTED", 422)
        if not isinstance(argv, list) or len(argv) > 10 or any(
                not isinstance(arg, str) or not 1 <= len(arg) <= 512 for arg in argv
        ) or sum(map(len, argv)) > 1000 or (operation == "exec") != bool(argv):
            fail("DOCKER_OPERATION_ARGV_INVALID", 422)
        if type(tail) is not int or not 1 <= tail <= 200:
            fail("DOCKER_OPERATION_TAIL_INVALID", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha,
                "repository": repo, "service": service, "operation": operation,
                "argv": argv, "tail": tail}
    if command_id == "host.command":
        required = {"schema", "id", "command_id", "expected_sha", "repository", "repo_sha", "command"}
        if not required <= set(value) or set(value) - required - {"source_preflight", "command_sha256"}:
            fail("HOST_COMMAND_KEYS_INVALID", 422)
        repository, command = value["repository"], value["command"]
        repo_sha = value["repo_sha"]
        if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository) \
                or not isinstance(repo_sha, str) or not SHA_PATTERN.fullmatch(repo_sha) \
                or not isinstance(command, str) or not command or "\x00" in command:
            fail("HOST_COMMAND_TARGET_INVALID", 422)
        if "source_preflight" in value and value["source_preflight"] is not True:
            fail("HOST_SOURCE_PREFLIGHT_INVALID", 422)
        # New senders bind the exact UTF-8 command before Gateway normalization.
        # Keep old authenticated deliveries compatible; never repair/re-encode a mismatch.
        if "command_sha256" in value:
            digest = value["command_sha256"]
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                fail("HOST_COMMAND_DIGEST_INVALID", 422)
            if hashlib.sha256(command.encode("utf-8")).hexdigest() != digest:
                fail("HOST_COMMAND_TRANSPORT_CHANGED", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha,
                "repository": repository, "repo_sha": repo_sha, "command": command,
                "source_preflight": value.get("source_preflight") is True}
    if command_id == "docker.logs":
        if set(value) != {"schema", "id", "command_id", "expected_sha", "container", "tail"}:
            fail("DOCKER_LOGS_KEYS_INVALID", 422)
        container, tail = value["container"], value["tail"]
        if not isinstance(container, str) or not CONTAINER_PATTERN.fullmatch(container) \
                or type(tail) is not int or not 1 <= tail <= 200:
            fail("DOCKER_LOGS_TARGET_INVALID", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha,
                "container": container, "tail": tail}
    if command_id == "dev.job":
        if set(value) not in ({"schema", "id", "command_id", "expected_sha", "repository", "session", "argv", "timeout_s", "fresh"},
                              {"schema", "id", "command_id", "expected_sha", "repository", "session", "argv", "timeout_s", "fresh", "repo_sha"}):
            fail("DEV_JOB_KEYS_INVALID", 422)
        repository, session, argv = value["repository"], value["session"], value["argv"]
        timeout_s, fresh = value["timeout_s"], value["fresh"]
        if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository) \
                or not isinstance(session, str) or not REQUEST_ID_PATTERN.fullmatch(session) \
                or not isinstance(argv, list) or not 1 <= len(argv) <= 8 \
                or any(not isinstance(a, str) or not 1 <= len(a) <= 1200 for a in argv) \
                or type(timeout_s) is not int or not 1 <= timeout_s <= 15 or type(fresh) is not bool:
            fail("DEV_JOB_TARGET_INVALID", 422)
        repo_sha = value.get("repo_sha", expected_sha)
        if not isinstance(repo_sha, str) or not SHA_PATTERN.fullmatch(repo_sha):
            fail("DEV_JOB_REPO_SHA_INVALID", 422)
        return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha, "repo_sha": repo_sha,
                "repository": repository, "session": session, "argv": argv, "timeout_s": timeout_s, "fresh": fresh}
    if set(value) != {"schema", "id", "command_id", "expected_sha"}:
        fail("REQUEST_KEYS_INVALID", 422)
    return {"id": req_id, "command_id": command_id, "expected_sha": expected_sha}


def dispatch_reflect(request, socket_path="/run/gace/servercore-source-reflect.sock"):
    repository = request.get("repository", "G-ACE-inc/server-core")
    branch = request.get("branch", "main")
    payload = {
        "schema": "gace.servercore-source-reflect.request/v1",
        "id": request["id"],
        "repository": repository,
        "branch": branch,
        "expected_before": request["expected_before"],
        "target_sha": request["expected_sha"],
    }
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(120)
            client.connect(socket_path)
            client.sendall(data)
            with client.makefile("rb") as stream:
                result = json.loads(stream.readline(4096))
    except (OSError, ValueError, TypeError):
        fail("REFLECT_EXECUTOR_UNAVAILABLE", 503)
    if not isinstance(result, dict):
        fail("REFLECT_EXECUTION_FAILED", 503)
    if result.get("ok") is not True:
        code = result.get("error")
        if code in TERMINAL_REFLECT_ERRORS:
            fail("REFLECT_PREFLIGHT_" + code, 422)
        fail("REFLECT_EXECUTION_FAILED", 503)
    if result.get("request_id") != request["id"] or result.get("target_sha") != request["expected_sha"]:
        fail("REFLECT_RESULT_MISMATCH", 503)
    if result.get("state") != "SOURCE_REFLECT_PASS":
        fail("REFLECT_RESULT_INVALID", 503)
    return {"source_sha": result["target_sha"], "command_id": request["command_id"],
            "source_reflect": True, "read_only": False}


def deploy_socket_call(payload, socket_path, timeout=60):
    data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout)
            client.connect(socket_path)
            client.sendall(data)
            with client.makefile("rb") as stream:
                raw_reply = stream.readline(16777217)
                if not raw_reply.endswith(b"\n") or len(raw_reply) > 16777216:
                    fail("DEPLOY_RESULT_INVALID", 503)
                result = json.loads(raw_reply)
    except (OSError, ValueError, TypeError):
        fail("DEPLOY_EXECUTOR_UNAVAILABLE", 503)
    if not isinstance(result, dict):
        fail("DEPLOY_RESULT_INVALID", 503)
    return result


def dispatch_deploy(request, socket_path=DEPLOY_SOCKET):
    result = deploy_socket_call({
        "schema": "gace.servercore-service-deploy.request/v1",
        "id": request["id"],
        "repository": request["repository"],
        "service": request["service"],
        "target_sha": request["expected_sha"],
    }, socket_path)
    if result.get("ok") is not True:
        # Lock contention is transient; every admission denial is terminal.
        fail("DEPLOY_EXECUTOR_BUSY" if result.get("error") == "DEPLOY_LOCK_BUSY" else "DEPLOY_ADMISSION_DENIED",
             503 if result.get("error") == "DEPLOY_LOCK_BUSY" else 422)
    if result.get("request_id") != request["id"] or result.get("state") not in {
            "SERVICE_DEPLOY_ACCEPTED", "SERVICE_DEPLOY_DUPLICATE"}:
        fail("DEPLOY_RESULT_MISMATCH", 503)
    return {"source_sha": request["expected_sha"], "command_id": request["command_id"],
            "deploy_state": result["state"], "service_deploy": True, "read_only": False}


def dispatch_deploy_status(request, socket_path=DEPLOY_SOCKET):
    result = deploy_socket_call({
        "schema": "gace.servercore-service-deploy.status/v1",
        "id": request["deploy_request_id"],
    }, socket_path)
    if result.get("ok") is not True:
        fail("DEPLOY_REQUEST_UNKNOWN", 422)
    state = result.get("state")
    if state in {"QUEUED", "RUNNING"}:
        fail("DEPLOY_IN_PROGRESS", 503)  # retryable until terminal
    if state != "SERVICE_DEPLOY_PASS" or result.get("source_sha") != request["expected_sha"]:
        fail("DEPLOY_FAILED_OR_SHA_MISMATCH", 422)
    keep = ("repository", "service", "source_sha", "container_id", "health", "http_health",
            "compose_digest", "recreated", "state")
    return {**{k: result[k] for k in keep if k in result}, "command_id": request["command_id"],
            "read_only": True}




def dispatch_docker_operation(request, root, socket_path=DEPLOY_SOCKET):
    """Use the same protected Host writer as service.deploy; never expose Docker to dev.job."""
    sha = bounded_host.head_sha(bounded_host.checked_root(root), request["expected_sha"])
    reply = deploy_socket_call({
        "schema": "gace.servercore-docker-operation.request/v1",
        "id": request["id"],
        "repository": request["repository"],
        "service": request["service"],
        "target_sha": sha,
        "operation": request["operation"],
        "argv": request["argv"],
        "tail": request["tail"],
    }, socket_path, timeout=60)
    if reply.get("ok") is not True:
        if reply.get("error") == "DEPLOY_LOCK_BUSY":
            fail("DOCKER_OPERATION_BUSY", 503)
        fail("DOCKER_OPERATION_ADMISSION_DENIED", 422)
    if reply.get("request_id") != request["id"]:
        fail("DOCKER_OPERATION_RESULT_ID_MISMATCH", 503)
    value = reply.get("result", reply)
    if reply.get("state") == "DOCKER_OPERATION_DUPLICATE":
        if reply.get("recorded_state") != "DOCKER_OPERATION_PASS":
            fail("DOCKER_OPERATION_PREVIOUSLY_FAILED", 422)
    elif reply.get("state") != "DOCKER_OPERATION_PASS":
        fail("DOCKER_OPERATION_FAILED", 422)
    if not isinstance(value, dict) or value.get("service") != request["service"] \
            or value.get("repository") != request["repository"] \
            or value.get("operation") != request["operation"] \
            or value.get("source_sha") != sha:
        fail("DOCKER_OPERATION_RESULT_MISMATCH", 503)
    read_only = request["operation"] in {"ps", "inspect", "logs", "stats"}
    return {"command_id": request["command_id"], "source_sha": sha,
            "service": value["service"], "repository": value["repository"],
            "operation": value["operation"],
            "stdout": str(value.get("stdout") or ""),
            "stderr": str(value.get("stderr") or ""),
            "stdout_truncated": bool(value.get("stdout_truncated")),
            "stderr_truncated": bool(value.get("stderr_truncated")),
            "read_only": read_only, "exit_code": 0, "state": "DOCKER_OPERATION_PASS"}

def dispatch_host_command(request, root, socket_path=DEPLOY_SOCKET):
    sha = bounded_host.head_sha(bounded_host.checked_root(root), request["expected_sha"])
    writer_request = {
        "schema": "gace.servercore-host-command.request/v1", "id": request["id"],
        "repository": request["repository"], "target_sha": request["repo_sha"],
        "command": request["command"],
    }
    if request.get("source_preflight") is True:
        writer_request["source_preflight"] = True
    reply = deploy_socket_call(writer_request, socket_path, timeout=120)
    if reply.get("ok") is not True:
        error = reply.get("error")
        if error == "DEPLOY_LOCK_BUSY":
            fail("HOST_COMMAND_BUSY", 503)
        if isinstance(error, str) and error in HOST_COMMAND_ADMISSION_ERRORS:
            fail(error, 422)
        fail("HOST_COMMAND_ADMISSION_DENIED", 422)
    if reply.get("state") == "HOST_COMMAND_DUPLICATE":
        result = reply.get("result")
        if not isinstance(result, dict):
            fail("HOST_COMMAND_RESULT_INVALID", 503)
    else:
        result = reply
    if result.get("request_id") != request["id"] or result.get("repository") != request["repository"] \
            or result.get("source_sha") != request["repo_sha"]:
        fail("HOST_COMMAND_RESULT_MISMATCH", 503)
    return {"command_id": request["command_id"], "repository": request["repository"],
            "source_sha": sha, "repo_sha": request["repo_sha"], "state": result.get("state"), "exit_code": result.get("exit_code", 1),
            "stdout": str(result.get("stdout") or ""),
            "stderr": str(result.get("stderr") or ""), "read_only": False,
            "output_record_request_id": result.get("output_record_request_id"),
            "stdout_sha256": result.get("stdout_sha256"),
            "stderr_sha256": result.get("stderr_sha256"),
            "stdout_chars": result.get("stdout_chars"),
            "stderr_chars": result.get("stderr_chars"),
            "stdout_stored_complete": result.get("stdout_stored_complete", False),
            "stderr_stored_complete": result.get("stderr_stored_complete", False)}


def dispatch_docker_logs(request, root, socket_path=None):
    sha = bounded_host.head_sha(bounded_host.checked_root(root), request["expected_sha"])
    data = (json.dumps({"schema": "gace.servercore-docker-logs.request/v1", "id": request["id"],
                        "container": request["container"], "tail": request["tail"]},
                       separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(45)
            client.connect(socket_path or DOCKER_LOGS_SOCKET)
            client.sendall(data)
            with client.makefile("rb") as stream:
                reply = json.loads(stream.readline(32768))
    except (OSError, ValueError, TypeError):
        fail("DOCKER_LOGS_EXECUTOR_UNAVAILABLE", 503)
    if not isinstance(reply, dict):
        fail("DOCKER_LOGS_RESULT_INVALID", 503)
    if reply.get("ok") is not True:
        error = str(reply.get("error", ""))
        if error in {"DOCKER_LOGS_FAILED", "DOCKER_LOGS_EXECUTION_FAILED", "INTERNAL_ERROR", "DOCKER_BINARY_MISSING"}:
            fail("DOCKER_LOGS_EXECUTION_FAILED", 503)
        fail("DOCKER_LOGS_DENIED_" + (error if re.fullmatch(r"[A-Z_]{3,60}", error) else "UNKNOWN"), 422)
    if reply.get("request_id") != request["id"] or reply.get("container") != request["container"]:
        fail("DOCKER_LOGS_RESULT_MISMATCH", 503)
    return {"command_id": request["command_id"], "source_sha": sha, "read_only": True,
            "container": reply["container"], "tail": reply["tail"], "truncated": bool(reply.get("truncated")),
            "logs": str(reply.get("logs", ""))}


def dispatch_dev_job(request, root, socket_path=None):
    """Generic isolated development job: admission + Docker authority live only in the Host provisioner."""
    sha = bounded_host.head_sha(bounded_host.checked_root(root), request["expected_sha"])
    data = (json.dumps({"schema": "gace.servercore-dev-job.request/v1", "id": request["id"],
                        "repository": request["repository"], "expected_sha": request.get("repo_sha", request["expected_sha"]),
                        "session": request["session"], "argv": request["argv"],
                        "timeout_s": request["timeout_s"], "fresh": request["fresh"]},
                       separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(60)
            client.connect(socket_path or DEV_JOB_SOCKET)
            client.sendall(data)
            with client.makefile("rb") as stream:
                reply = json.loads(stream.readline(262144))
    except (OSError, ValueError, TypeError):
        fail("DEV_JOB_EXECUTOR_UNAVAILABLE", 503)
    if not isinstance(reply, dict):
        fail("DEV_JOB_RESULT_INVALID", 503)
    if reply.get("ok") is not True:
        error = str(reply.get("error", ""))
        if error in DEV_JOB_RETRYABLE:
            fail("DEV_JOB_EXECUTION_FAILED", 503)
        fail("DEV_JOB_DENIED_" + (error if re.fullmatch(r"[A-Z_]{3,60}", error) else "UNKNOWN"), 422)
    if reply.get("request_id") != request["id"] or reply.get("session") != request["session"]:
        fail("DEV_JOB_RESULT_MISMATCH", 503)
    keep = ("session", "repository", "project_item", "base_sha", "workspace_head", "job_exit", "timed_out",
            "output_limit_exceeded", "workspace_budget_exceeded", "stdout_truncated", "stderr_truncated",
            "stdout", "stderr", "changed", "diff_stat",
            "duration_ms", "replayed")
    return {**{k: reply.get(k) for k in keep}, "command_id": request["command_id"], "source_sha": sha,
            "read_only": False}


def dev_job_record_fields(result):
    """Bounded sink fields: first stdout line is a compact metadata record, then job stdout."""
    meta = {k: result.get(k) for k in ("session", "base_sha", "workspace_head", "job_exit", "timed_out",
                                       "output_limit_exceeded", "workspace_budget_exceeded", "stdout_truncated", "stderr_truncated",
                                       "diff_stat",
                                       "duration_ms", "replayed")}
    meta["changed"] = list(result.get("changed") or [])[:10]
    job_exit = result.get("job_exit")
    ok = job_exit == 0 and not result.get("timed_out") and not result.get("output_limit_exceeded")
    code = 0 if ok else (job_exit if type(job_exit) is int and 1 <= job_exit <= 255 else 1)
    stdout = "GACE_DEV_JOB " + json.dumps(meta, sort_keys=True, separators=(",", ":"), ensure_ascii=False) \
        + "\n" + str(result.get("stdout") or "")
    return ("PASS" if ok else "FAIL"), code, stdout, str(result.get("stderr") or "")


def report_result(record, socket_path=None):
    """Hand the terminal result to the Host result sink (durable + GitHub publish)."""
    data = (json.dumps({"schema": RESULT_SCHEMA, **record}, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(15)
            client.connect(socket_path or RESULT_SOCKET)
            client.sendall(data)
            with client.makefile("rb") as stream:
                reply = json.loads(stream.readline(4096))
    except (OSError, ValueError, TypeError):
        return False
    return isinstance(reply, dict) and reply.get("ok") is True


def result_record(request_id, command_id, expected_sha, state, exit_code, host_sha, stdout, stderr, started):
    return {
        "request_id": request_id,
        "command_id": command_id if isinstance(command_id, str) and COMMAND_PATTERN.fullmatch(command_id)
        else "invalid.request",
        "state": state,
        "exit_code": exit_code,
        "host_sha": host_sha if isinstance(host_sha, str) and SHA_PATTERN.fullmatch(host_sha) else "",
        "expected_sha": expected_sha if isinstance(expected_sha, str) and SHA_PATTERN.fullmatch(expected_sha) else "",
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": max(0, min(int((time.monotonic() - started) * 1000), 3_600_000)),
    }


def host_dependency_status(paths=None):
    """Probe fixed local RPC listeners without dispatching a command or writing a result.

    Empty objects are rejected by both protocols before execution/persistence.
    Reading the bounded reply avoids broken-pipe noise from connect-only probes.
    """
    paths = paths or {"host_writer": DEPLOY_SOCKET, "result_sink": RESULT_SOCKET}
    status = {}
    for name, path in paths.items():
        status[name] = False
        try:
            if not stat.S_ISSOCK(Path(path).lstat().st_mode):
                continue
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(1)
                client.connect(str(path))
                client.sendall(b"{}\n")
                with client.makefile("rb") as stream:
                    raw = stream.readline(4097)
                if len(raw) > 4096 or not raw.endswith(b"\n"):
                    continue
                reply = json.loads(raw)
                status[name] = isinstance(reply, dict) and type(reply.get("ok")) is bool
        except (OSError, ValueError, TypeError):
            pass
    return status


def watch_host_dependencies(server, stop, *, interval=5, grace_seconds=60,
                            ready=None, monotonic=time.monotonic):
    """Exit this Receiver after sustained dependency loss; Docker rebinds /run/gace.

    Socket services can legitimately restart. A full grace window avoids flapping;
    a replaced parent-directory bind otherwise stays stale indefinitely.
    """
    ready = ready or (lambda: all(host_dependency_status().values()))
    failed_since = None
    while not stop.wait(interval):
        if ready():
            failed_since = None
        elif failed_since is None:
            failed_since = monotonic()
        elif monotonic() - failed_since >= grace_seconds:
            server.host_dependency_shutdown = True
            print("GACE_RECEIVER_DEPENDENCIES=UNAVAILABLE_REBIND_REQUIRED", flush=True)
            server.shutdown()
            return


def make_handler(contract, *, delivery_key=None, now_fn=None):
    root = Path(contract.get("canonical_host_root") or bounded_host.CANONICAL_ROOT)

    class Handler(BaseHTTPRequestHandler):
        server_version = "gace-servercore-bounded-host/1"

        def log_message(self, _format, *_args):
            # Do not log raw headers, paths, signatures, tokens or request bodies.
            return

        def send_json(self, status, payload, *, accepted=False):
            # Always expose the bounded admission/result status in Docker logs.
            # Only authenticated, pattern-verified request ids may be correlated.
            request_id = getattr(self, "_verified_request_id", None)
            safe_id = request_id if isinstance(request_id, str) and REQUEST_ID_PATTERN.fullmatch(request_id) else "-"
            error = payload.get("error") if isinstance(payload, dict) else None
            safe_error = error if isinstance(error, str) and re.fullmatch(r"[A-Z_]{3,80}", error) else "-"
            print(f"GACE_RECEIVER_RESULT status={int(status)} request_id={safe_id} error={safe_error} recorded={str(payload.get('result_recorded', '-')).lower() if isinstance(payload, dict) else '-'}",
                  file=sys.stderr, flush=True)
            data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            if accepted:
                self.send_header("x-gace-accepted", "true")
            try:
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                # The caller disconnected; the Host result is handled by the durable sink,
                # not by re-running the request or dumping an uncorrelated traceback.
                print("GACE_RECEIVER_CLIENT_DISCONNECTED status=" + str(status),
                      file=sys.stderr, flush=True)

        def do_GET(self):
            if self.path != HEALTH_PATH:
                self.send_json(404, {"ok": False, "error": "NOT_FOUND"})
                return
            dependencies = host_dependency_status()
            ready = all(dependencies.values())
            self.send_json(200 if ready else 503, {
                "ok": ready, "service": "servercore-bounded-host", "dependencies": dependencies,
                **({} if ready else {"error": "HOST_DEPENDENCIES_UNAVAILABLE"}),
            })

        def do_POST(self):
            if self.path == CIPHER_PATH:
                # Separate signed, ciphertext-only ingress; no Host commands
                # accepted through this endpoint. Uses the existing HMAC key,
                # UNIX result socket and bound Receiver container.
                try:
                    raw_length = self.headers.get("content-length")
                    try:
                        length = int(raw_length or "")
                    except ValueError:
                        fail("CONTENT_LENGTH_REQUIRED", 411)
                    if not 1 <= length <= MAX_BODY_BYTES:
                        fail("BODY_SIZE_INVALID", 413)
                    body = self.rfile.read(length)
                    headers = {k.lower(): v for k, v in self.headers.items()}
                    verify_delivery(
                        headers, body, expected_destination=CIPHER_DESTINATION,
                        delivery_key=delivery_key, now=now_fn() if now_fn else None,
                        tolerance_seconds=int(os.environ.get("GACE_BOUNDED_HOST_SIGNATURE_TOLERANCE_SECONDS", "300")),
                    )
                    chunk = json.loads(body.decode("utf-8"))
                    if not isinstance(chunk, dict) or chunk.get("schema") != "gace.host-output.encrypted-chunk/v1":
                        fail("CIPHER_ENVELOPE_INVALID", 422)
                    reply = deploy_socket_call(chunk, RESULT_SOCKET, timeout=10)
                    if reply.get("ok") is not True:
                        fail("CIPHER_INBOX_REJECTED", 422 if reply.get("error") in {
                            "ENVELOPE_INVALID", "CHUNK_REPLAY_CONFLICT", "CHUNK_BOUNDS_INVALID",
                            "CHUNK_LENGTH_MISMATCH", "CHUNK_SHA_INVALID", "CIPHER_PARTS_INVALID"
                        } else 503)
                    self.send_json(200, {"ok": True, "state": reply.get("state")}, accepted=True)
                except DeliveryAuthError as exc:
                    self.send_json(exc.status, {"ok": False, "error": exc.code})
                except ReceiverError as exc:
                    self.send_json(exc.status, {"ok": False, "error": exc.code})
                except (ValueError, TypeError, UnicodeError):
                    self.send_json(422, {"ok": False, "error": "CIPHER_ENVELOPE_INVALID"})
                except Exception:
                    self.send_json(503, {"ok": False, "error": "CIPHER_DELIVERY_RETRYABLE"})
                return
            if self.path != RECEIVER_PATH:
                self.send_json(404, {"ok": False, "error": "NOT_FOUND"})
                return
            raw_length = self.headers.get("content-length")
            try:
                length = int(raw_length or "")
            except ValueError:
                self.send_json(411, {"ok": False, "error": "CONTENT_LENGTH_REQUIRED"})
                return
            if length < 1 or length > MAX_BODY_BYTES:
                self.send_json(413, {"ok": False, "error": "BODY_SIZE_INVALID"})
                return
            body = self.rfile.read(length)
            headers = {key.lower(): value for key, value in self.headers.items()}
            started = time.monotonic()
            hint_id = hint_command = hint_sha = None
            authenticated = False

            def record_failure(code, state, host_sha=""):
                # Only authenticated deliveries with a well-formed request id are recorded.
                if authenticated and hint_id:
                    report_result(result_record(hint_id, hint_command, hint_sha, state, 1, host_sha, "", code, started))
            try:
                tolerance = int(os.environ.get("GACE_BOUNDED_HOST_SIGNATURE_TOLERANCE_SECONDS", "300"))
                verify_delivery(
                    headers,
                    body,
                    expected_destination=EXPECTED_DESTINATION,
                    delivery_key=delivery_key,
                    now=now_fn() if now_fn else None,
                    tolerance_seconds=tolerance,
                )
                authenticated = True
                parsed = json.loads(body.decode("utf-8"))
                if isinstance(parsed, dict):
                    hint_id = parsed.get("id") if isinstance(parsed.get("id"), str) \
                        and REQUEST_ID_PATTERN.fullmatch(parsed.get("id")) else None
                    hint_command, hint_sha = parsed.get("command_id"), parsed.get("expected_sha")
                    self._verified_request_id = hint_id
                request = validate_request(parsed, contract)
                if request["command_id"] == "project.source_reflect":
                    result = dispatch_reflect(request)
                elif request["command_id"] == "service.deploy":
                    result = dispatch_deploy(request)
                elif request["command_id"] == "service.deploy_status":
                    result = dispatch_deploy_status(request)
                elif request["command_id"] == "project.file_inspect":
                    result = bounded_host.file_inspect(root, request["expected_sha"], request["path"],
                                                       request["offset"], contract.get("registered_files"))
                elif request["command_id"] == "docker.logs":
                    result = dispatch_docker_logs(request, root)
                elif request["command_id"] == "docker.operation":
                    result = dispatch_docker_operation(request, root)
                elif request["command_id"] == "host.command":
                    result = dispatch_host_command(request, root)
                elif request["command_id"] == "dev.job":
                    result = dispatch_dev_job(request, root)
                else:
                    result = bounded_host.execute(
                        request["command_id"],
                        root=root,
                        expected_sha=request["expected_sha"],
                    )
                read_only = bool(result.get("read_only", True))
                state, exit_code, out, err = "PASS", 0, json.dumps(result, sort_keys=True, separators=(",", ":")), ""
                if request["command_id"] == "dev.job":
                    state, exit_code, out, err = dev_job_record_fields(result)
                elif request["command_id"] == "host.command":
                    exit_code = result.get("exit_code", 1)
                    state = "PASS" if result.get("state") == "HOST_COMMAND_PASS" and exit_code == 0 else "FAIL"
                    out, err = str(result.get("stdout") or ""), str(result.get("stderr") or "")
                    if result.get("stdout_stored_complete") or result.get("stderr_stored_complete"):
                        receipt = (
                            "GACE_HOST_OUTPUT_STORED request_id=" + str(request["id"])
                            + " stdout_chars=" + str(result.get("stdout_chars", 0))
                            + " stdout_sha256=" + str(result.get("stdout_sha256", ""))
                            + " stderr_chars=" + str(result.get("stderr_chars", 0))
                            + " stderr_sha256=" + str(result.get("stderr_sha256", ""))
                            + " (lossless chunks: scripts/servercore_host_output_read.py)"
                        )
                        out = receipt + ("\\n" + out if out else "")
                recorded = report_result(result_record(
                    request["id"], request["command_id"], request["expected_sha"], state, exit_code,
                    result.get("source_sha"), out, err, started))
                # A failed Sink handoff is NEVER a successful Host result delivery.
                # For host.command the Host writer persists the exact request ID
                # before execution and de-duplicates re-delivery, so signalling
                # 503 lets Gateway retry the SAME request without re-executing.
                # Do not turn an unrecorded PASS into a silent 200 acknowledgement.
                if not recorded and (read_only or request["command_id"] in {"dev.job", "host.command"}):
                    fail("RESULT_SINK_UNAVAILABLE", 503)
                self.send_json(
                    200,
                    {
                        "ok": True,
                        "request_id": request["id"],
                        "state": state,
                        "command_id": request["command_id"],
                        "source_sha": result.get("source_sha"),
                        "read_only": read_only,
                        "result_recorded": recorded,
                        "result": result,
                    },
                    accepted=True,
                )
            except DeliveryAuthError as exc:
                self.send_json(exc.status, {"ok": False, "error": exc.code})
            except ReceiverError as exc:
                if exc.code != "RESULT_SINK_UNAVAILABLE":
                    record_failure(exc.code, "FAIL" if exc.status < 500 else "RETRYABLE")
                self.send_json(exc.status, {"ok": False, "error": exc.code})
            except bounded_host.BoundaryError as exc:
                payload = {"ok": False, "error": str(exc), "state": "FAIL"}
                host_head = ""
                if str(exc) == "SOURCE_SHA_MISMATCH":
                    # An authenticated caller learns the real Host HEAD (a commit id, not a secret) so one denied
                    # request is enough to re-pin; otherwise the caller can only guess at SHAs.
                    try:
                        host_head = bounded_host.head_sha(bounded_host.checked_root(root))
                    except bounded_host.BoundaryError:
                        host_head = ""
                    if host_head:
                        payload["host_sha"] = host_head
                record_failure(str(exc), "FAIL", host_head)
                self.send_json(422, payload)
            except Exception:
                record_failure("INTERNAL_ERROR", "RETRYABLE")
                self.send_json(500, {"ok": False, "error": "INTERNAL_ERROR"})

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Bounded internal HTTP receiver for server-core Host primitive")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8789)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    if args.port < 1 or args.port > 65535:
        raise SystemExit("PORT_INVALID")
    contract = load_contract(args.contract)
    delivery_key = read_delivery_key(env_prefix="GACE_BOUNDED_HOST")
    server = ThreadingHTTPServer((args.host, args.port), make_handler(contract, delivery_key=delivery_key))
    stop = threading.Event()
    server.host_dependency_shutdown = False
    threading.Thread(target=watch_host_dependencies, args=(server, stop), daemon=True).start()
    try:
        server.serve_forever()
    finally:
        stop.set()
        server.server_close()
    if server.host_dependency_shutdown:
        raise SystemExit("HOST_DEPENDENCIES_UNAVAILABLE")


if __name__ == "__main__":
    raise SystemExit(main())
