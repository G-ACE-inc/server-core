#!/usr/bin/env python3
"""Thin Gserver target adapter for the shared server-core host.command route.

This module selects and validates an already-registered target contract. It does
not implement a command dispatcher, fixed command menu, network listener or
credential store.
"""
import hashlib
import re

EVIDENCE_KEYS = {"host_target", "repository", "repo_sha", "dispatcher_sha",
                 "command_sha256", "stdout_sha256", "stderr_sha256"}

SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
REQUEST_ID = re.compile(r"^req_[0-9a-f]{24}$")
TARGET_ID = "gserver"
REPOSITORY = "seigo-gace/G-ACEserver"


class GserverTargetError(ValueError):
    pass


def target_config(contract):
    targets = contract.get("host_targets")
    target = targets.get(TARGET_ID) if isinstance(targets, dict) else None
    if not isinstance(target, dict):
        raise GserverTargetError("GSERVER_TARGET_NOT_REGISTERED")
    if target.get("target_id") != TARGET_ID or target.get("repository") != REPOSITORY:
        raise GserverTargetError("GSERVER_TARGET_CONTRACT_INVALID")
    if target.get("common_command_id") != "host.command":
        raise GserverTargetError("GSERVER_TARGET_COMMAND_INVALID")
    if target.get("fixed_command_terminal") is not False:
        raise GserverTargetError("GSERVER_FIXED_TERMINAL_FORBIDDEN")
    transport = target.get("transport")
    if not isinstance(transport, dict) or not transport.get("destination_id") or not transport.get("receiver_endpoint"):
        raise GserverTargetError("GSERVER_TARGET_TRANSPORT_INVALID")
    if target.get("status") not in {"SOURCE_CONTRACT_ONLY", "HOST_ADMITTED"}:
        raise GserverTargetError("GSERVER_TARGET_STATUS_INVALID")
    return target


def validate_request(request, contract):
    target = target_config(contract)
    if not isinstance(request, dict):
        raise GserverTargetError("GSERVER_REQUEST_INVALID")
    required = {"schema", "id", "command_id", "expected_sha", "repository", "repo_sha",
                "command", "command_sha256", "host_target"}
    if set(request) != required:
        raise GserverTargetError("GSERVER_REQUEST_KEYS_INVALID")
    if request["schema"] != contract.get("request_schema"):
        raise GserverTargetError("GSERVER_REQUEST_SCHEMA_INVALID")
    if not isinstance(request["id"], str) or not REQUEST_ID.fullmatch(request["id"]):
        raise GserverTargetError("GSERVER_REQUEST_ID_INVALID")
    if request["host_target"] != TARGET_ID or request["repository"] != target["repository"]:
        raise GserverTargetError("GSERVER_TARGET_MISMATCH")
    if request["command_id"] != target["common_command_id"]:
        raise GserverTargetError("GSERVER_COMMAND_MISMATCH")
    if not SHA.fullmatch(request["expected_sha"]) or not SHA.fullmatch(request["repo_sha"]):
        raise GserverTargetError("GSERVER_SHA_INVALID")
    command = request["command"]
    if not isinstance(command, str) or not command or "\x00" in command:
        raise GserverTargetError("GSERVER_COMMAND_INVALID")
    digest = request["command_sha256"]
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        raise GserverTargetError("GSERVER_COMMAND_DIGEST_INVALID")
    if hashlib.sha256(command.encode("utf-8")).hexdigest() != digest:
        raise GserverTargetError("GSERVER_COMMAND_TRANSPORT_CHANGED")
    return target


def event_destination(request, contract):
    target = validate_request(request, contract)
    return target["transport"]["destination_id"]


def validate_result(result, request):
    if not isinstance(result, dict):
        raise GserverTargetError("GSERVER_RESULT_INVALID")
    if result.get("request_id") != request.get("id"):
        raise GserverTargetError("GSERVER_RESULT_REQUEST_MISMATCH")
    if result.get("host_target") != TARGET_ID or result.get("repository") != REPOSITORY:
        raise GserverTargetError("GSERVER_RESULT_TARGET_MISMATCH")
    if result.get("repo_sha") != request.get("repo_sha"):
        raise GserverTargetError("GSERVER_RESULT_REPO_SHA_MISMATCH")
    if not SHA.fullmatch(str(result.get("host_sha", ""))):
        raise GserverTargetError("GSERVER_RESULT_HOST_SHA_INVALID")
    if result["host_sha"] != request.get("repo_sha"):
        raise GserverTargetError("GSERVER_RESULT_HOST_SHA_MISMATCH")
    if not SHA.fullmatch(str(result.get("dispatcher_sha", ""))) or result.get("dispatcher_sha") != request.get("expected_sha"):
        raise GserverTargetError("GSERVER_RESULT_DISPATCHER_SHA_MISMATCH")
    if not DIGEST.fullmatch(str(result.get("command_sha256", ""))) or result.get("command_sha256") != request.get("command_sha256"):
        raise GserverTargetError("GSERVER_RESULT_COMMAND_SHA_MISMATCH")
    if result.get("state") not in {"PASS", "FAIL"} or type(result.get("exit_code")) is not int:
        raise GserverTargetError("GSERVER_RESULT_STATE_INVALID")
    if not 0 <= result["exit_code"] <= 255 or (result["state"] == "PASS") != (result["exit_code"] == 0):
        raise GserverTargetError("GSERVER_RESULT_EXIT_STATE_MISMATCH")
    for key in ("stdout_sha256", "stderr_sha256"):
        if not DIGEST.fullmatch(str(result.get(key, ""))):
            raise GserverTargetError("GSERVER_RESULT_STREAM_HASH_INVALID")
        stream = result.get(key.removesuffix("_sha256"))
        if not isinstance(stream, str) or hashlib.sha256(stream.encode()).hexdigest() != result[key]:
            raise GserverTargetError("GSERVER_RESULT_STREAM_HASH_MISMATCH")
    return result


def sink_record(result, request):
    """Adapt verified target output to the existing shared Result Sink."""
    validate_result(result, request)
    return {
        "schema": "gace.servercore-bounded-result.record/v1",
        "request_id": request["id"], "command_id": "host.command",
        "expected_sha": request["expected_sha"], "host_sha": result["host_sha"],
        "state": result["state"], "exit_code": result["exit_code"],
        "stdout": result["stdout"], "stderr": result["stderr"], "duration_ms": 0,
        "target_evidence": {k: result[k] for k in EVIDENCE_KEYS},
    }


def receive_delivery(headers, body, *, contract, delivery_key, root, result_dir,
                     lock_path, execute, report, now=None):
    """Trusted Host wiring for signed JSON delivery, not a new listener.

    Paths, executor, key and reporter are supplied by Host deployment code,
    never by the request. Reuse the common HMAC verifier and Writer ledger.
    A persisted RUNNING receipt is intentionally not automatically rerun.
    """
    import fcntl
    import json
    import os
    from pathlib import Path
    from gace_internal_delivery_auth import verify_delivery
    from servercore_service_deploy_socket import read_result, write_result

    if not isinstance(body, bytes) or not 1 <= len(body) <= 1048576:
        raise GserverTargetError("GSERVER_DELIVERY_SIZE_INVALID")
    target = target_config(contract)
    verify_delivery(headers, body, expected_destination=target["transport"]["destination_id"],
                    delivery_key=delivery_key, now=now)
    request = json.loads(body.decode("utf-8"))
    validate_request(request, contract)
    if target["status"] != "HOST_ADMITTED":
        raise GserverTargetError("GSERVER_HOST_NOT_ADMITTED")
    root = Path(root)
    if root.is_symlink() or str(root.resolve(strict=True)) != target["canonical_host_root"]:
        raise GserverTargetError("GSERVER_HOST_ROOT_MISMATCH")
    fingerprint = hashlib.sha256(json.dumps(request, sort_keys=True,
                                           separators=(",", ":")).encode()).hexdigest()

    def persist(value):
        write_result(request["id"], value, result_dir)
        # A durable claim must precede execution even across a Host crash.
        with (Path(result_dir) / (request["id"] + ".json")).open("rb") as stream:
            os.fsync(stream.fileno())
        directory = os.open(result_dir, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        previous = read_result(request["id"], result_dir)
        if previous is not None:
            if previous.get("request_fingerprint") != fingerprint:
                raise GserverTargetError("GSERVER_REQUEST_REPLAY_CONFLICT")
            if previous.get("state") != "COMPLETED":
                raise GserverTargetError("GSERVER_EXECUTION_OUTCOME_UNKNOWN")
            result = previous["result"]
        else:
            persist({"state": "RUNNING", "request_fingerprint": fingerprint})
            result = execute(request, root)
            validate_result(result, request)
            persist({"state": "COMPLETED", "request_fingerprint": fingerprint, "result": result})
    if report(sink_record(result, request)) is not True:
        raise GserverTargetError("GSERVER_RESULT_SINK_UNAVAILABLE")
    return result
