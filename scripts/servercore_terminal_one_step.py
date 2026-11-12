#!/usr/bin/env python3
"""One-step common Terminal client: single Execute + single Result read.

This is an INDEPENDENT, default-OFF client that composes two already-installed,
already-authorized pieces and adds no new daemon, service, token, endpoint,
contract or authorization:

  * Execute  -> ``servercore_bounded_host_gateway_send`` submits ONE request to
    the EXISTING authenticated Gateway ``POST /internal/events`` (202 durable
    receipt). Request identity and the exact command digest are bound there.
  * Result   -> ``servercore_result_local_lookup`` reads ONE durable Request ID
    from the EXISTING local Result Sink socket. Metadata only; stdout/stderr are
    never returned.

Correlating both halves by a single Request ID removes the need for a per-command
Git commit and GitHub Issue-comment result polling, matching the PROPOSED design
in docs/proposals/COMMON_TERMINAL_ONE_STEP_20261112.md (PR #359) and adopted
design docs/SERVER_CORE_DESIGN.md section 16. It does NOT change the production
route: the live Gateway send is only attempted when the operator explicitly opts
in via ``GACE_TERMINAL_ONE_STEP_ENABLED=1``; otherwise the client runs in PLAN
mode and contacts nothing.

Guarantees layered on top of the reused primitives:
  * Replay / same-ID conflict: before sending, the existing Sink is queried for
    the Request ID; an already-recorded result is refused, never re-executed.
  * Gateway failure vs Sink failure vs Host FAIL vs result timeout are distinct,
    non-overlapping outcome classes.
  * read-only effects return the Host-observed SHA; an explicit pin only rejects
    on mismatch. Mutating effects keep the existing expected-before SHA guard
    enforced by the sender's validator.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import servercore_bounded_host_gateway_send as gateway_send
import servercore_result_local_lookup as result_lookup

REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{24}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ENABLE_ENV = "GACE_TERMINAL_ONE_STEP_ENABLED"
ATTEMPTS_ENV = "GACE_TERMINAL_ONE_STEP_POLL_ATTEMPTS"
BACKOFF_ENV = "GACE_TERMINAL_ONE_STEP_POLL_BACKOFF_SECONDS"
DEFAULT_ATTEMPTS = 12
DEFAULT_BACKOFF = 1.0
MAX_ATTEMPTS = 60
MAX_BACKOFF = 10.0


class OneStepError(RuntimeError):
    """Raised with a stable, non-secret failure class string."""


def _effect(contract, command_id):
    effects = contract.get("command_effects") or {}
    effect = effects.get(command_id)
    if not isinstance(effect, str) or not effect:
        raise OneStepError("COMMAND_EFFECT_UNKNOWN")
    return effect


def _is_read_only(effect):
    return effect == "read_only"


def is_enabled(env=None):
    current = os.environ if env is None else env
    return str(current.get(ENABLE_ENV, "")).strip() == "1"


def _poll_plan(env=None):
    current = os.environ if env is None else env
    try:
        attempts = int(str(current.get(ATTEMPTS_ENV, "")).strip() or DEFAULT_ATTEMPTS)
    except ValueError as exc:
        raise OneStepError("POLL_ATTEMPTS_INVALID") from exc
    try:
        backoff = float(str(current.get(BACKOFF_ENV, "")).strip() or DEFAULT_BACKOFF)
    except ValueError as exc:
        raise OneStepError("POLL_BACKOFF_INVALID") from exc
    if not 1 <= attempts <= MAX_ATTEMPTS:
        raise OneStepError("POLL_ATTEMPTS_OUT_OF_RANGE")
    if not 0 <= backoff <= MAX_BACKOFF:
        raise OneStepError("POLL_BACKOFF_OUT_OF_RANGE")
    return attempts, backoff


def plan_request(contract, command_kwargs, *, pinned_sha=None):
    """Build (without sending) the request and classify its effect/pin rules."""
    command_id = command_kwargs.get("command_id")
    expected_sha = command_kwargs.get("expected_sha")
    if not isinstance(command_id, str) or not isinstance(expected_sha, str):
        raise OneStepError("COMMAND_ARGUMENTS_INVALID")
    effect = _effect(contract, command_id)
    read_only = _is_read_only(effect)
    if pinned_sha is not None:
        if not read_only:
            raise OneStepError("PIN_ONLY_FOR_READ_ONLY")
        if not isinstance(pinned_sha, str) or not SHA_PATTERN.match(pinned_sha):
            raise OneStepError("PINNED_SHA_INVALID")
    if read_only and command_kwargs.get("expected_before") is not None:
        raise OneStepError("READ_ONLY_FORBIDS_EXPECTED_BEFORE")
    try:
        request = gateway_send.validate_cli(command_id, expected_sha, contract,
                                            **{k: v for k, v in command_kwargs.items()
                                               if k not in ("command_id", "expected_sha")})
    except gateway_send.SendError as exc:
        raise OneStepError(f"REQUEST_INVALID:{exc}") from exc
    request_id = request["id"]
    if not REQUEST_ID_PATTERN.match(request_id):
        raise OneStepError("REQUEST_ID_INVALID")
    return {"request": request, "request_id": request_id, "effect": effect,
            "read_only": read_only, "pinned_sha": pinned_sha}


def _sink_lookup(request_id, *, socket_path, connect):
    try:
        return result_lookup.lookup(request_id, socket_path=socket_path, connect=connect)
    except result_lookup.ResultQueryError as exc:
        raise OneStepError(f"SINK:{exc}") from exc


def _finalize(request_id, plan, receipt, record):
    state = record["state"]
    host_sha = record.get("host_sha") or ""
    outcome = {"PASS": "HOST_PASS", "FAIL": "HOST_FAIL", "RETRYABLE": "HOST_RETRYABLE"}[state]
    if plan["read_only"] and plan["pinned_sha"] is not None and host_sha != plan["pinned_sha"]:
        outcome = "HOST_SHA_MISMATCH"
    return {"request_id": request_id, "effect": plan["effect"],
            "read_only": plan["read_only"], "gateway": "QUEUED", "gateway_receipt": receipt,
            "outcome": outcome, "state": state, "exit_code": record.get("exit_code"),
            "host_sha": host_sha, "recorded_at": record.get("recorded_at", ""),
            "published": bool(record.get("published"))}


def execute_and_fetch(contract, command_kwargs, *, request_id=None, pinned_sha=None,
                      env=None, opener=None, sink_socket_path=result_lookup.SOCKET,
                      sink_connect=None, sleep=time.sleep):
    """Submit one Execute through the existing Gateway, then read one Result.

    Returns metadata only (never stdout/stderr). Raises :class:`OneStepError`
    with a distinct class for Gateway, Sink, replay and timeout failures.
    """
    if request_id is not None:
        if not isinstance(request_id, str) or not REQUEST_ID_PATTERN.match(request_id):
            raise OneStepError("REQUEST_ID_INVALID")
        command_kwargs = dict(command_kwargs, request_id=request_id)
    plan = plan_request(contract, command_kwargs, pinned_sha=pinned_sha)
    rid = plan["request_id"]
    attempts, backoff = _poll_plan(env)

    # Replay / same-ID conflict guard: an already-recorded Request ID is never
    # re-executed. A missing Sink here is a Sink failure, not a licence to send.
    existing = _sink_lookup(rid, socket_path=sink_socket_path, connect=sink_connect)
    if existing.get("status") == "RECORDED":
        raise OneStepError("REQUEST_ID_ALREADY_RECORDED")

    try:
        receipt = gateway_send.send(plan["request"], contract, env=env, opener=opener)
    except gateway_send.SendError as exc:
        raise OneStepError(f"GATEWAY:{exc}") from exc

    for index in range(attempts):
        found = _sink_lookup(rid, socket_path=sink_socket_path, connect=sink_connect)
        if found.get("status") == "RECORDED":
            return _finalize(rid, plan, receipt, found)
        if index + 1 < attempts and backoff:
            sleep(backoff)
    raise OneStepError("RESULT_TIMEOUT")


def _build_command_kwargs(args):
    kwargs = {"command_id": args.command_id, "expected_sha": args.expected_sha}
    optional = {
        "repository": args.repository,
        "host_command": args.host_command,
        "repo_sha": args.repo_sha,
        "expected_before": args.expected_before,
        "reflect_repository": args.reflect_repository,
        "reflect_branch": args.reflect_branch,
        "service": args.service,
        "path": args.path,
        "offset": args.offset,
        "container": args.container,
        "tail": args.tail,
        "host_target": args.host_target,
    }
    for key, value in optional.items():
        if value is not None:
            kwargs[key] = value
    if args.source_preflight:
        kwargs["source_preflight"] = True
    return kwargs


def main(argv=None):
    parser = argparse.ArgumentParser(description="One-step Execute + Result client (default-OFF).")
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--repository")
    parser.add_argument("--host-command")
    parser.add_argument("--repo-sha")
    parser.add_argument("--expected-before")
    parser.add_argument("--reflect-repository")
    parser.add_argument("--reflect-branch")
    parser.add_argument("--service")
    parser.add_argument("--path")
    parser.add_argument("--offset", type=int)
    parser.add_argument("--container")
    parser.add_argument("--tail", type=int)
    parser.add_argument("--host-target")
    parser.add_argument("--source-preflight", action="store_true")
    parser.add_argument("--request-id")
    parser.add_argument("--pinned-sha")
    parser.add_argument("--contract", default=str(gateway_send.DEFAULT_CONTRACT))
    args = parser.parse_args(argv)

    try:
        contract = gateway_send.load_contract(args.contract)
        command_kwargs = _build_command_kwargs(args)
        if args.request_id is not None:
            command_kwargs = dict(command_kwargs, request_id=args.request_id)
        plan = plan_request(contract, command_kwargs, pinned_sha=args.pinned_sha)
    except (OneStepError, gateway_send.SendError) as exc:
        print(json.dumps({"mode": "PLAN", "state": "FAIL", "failure_class": str(exc)}, sort_keys=True))
        return 1

    if not is_enabled():
        print(json.dumps({"mode": "PLAN_DISABLED", "request_id": plan["request_id"],
                          "effect": plan["effect"], "read_only": plan["read_only"],
                          "note": f"set {ENABLE_ENV}=1 to perform the live Execute/Result"},
                         sort_keys=True))
        print("ONE_STEP_MODE=PLAN_DISABLED")
        return 0

    try:
        data = execute_and_fetch(contract, command_kwargs,
                                 request_id=args.request_id, pinned_sha=args.pinned_sha)
    except OneStepError as exc:
        print(json.dumps({"mode": "LIVE", "state": "FAIL", "request_id": plan["request_id"],
                          "failure_class": str(exc)}, sort_keys=True))
        return 2
    data["mode"] = "LIVE"
    print(json.dumps(data, sort_keys=True))
    return 0 if data["outcome"] == "HOST_PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
