#!/usr/bin/env python3
"""Thin Gserver target adapter for the shared server-core host.command route.

This module selects and validates an already-registered target contract. It does
not implement a command dispatcher, fixed command menu, network listener or
credential store.
"""
import hashlib
import re

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
    if result.get("dispatcher_sha") != request.get("expected_sha"):
        raise GserverTargetError("GSERVER_RESULT_DISPATCHER_SHA_MISMATCH")
    if result.get("command_sha256") != request.get("command_sha256"):
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
