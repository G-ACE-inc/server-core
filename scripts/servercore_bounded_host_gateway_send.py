#!/usr/bin/env python3
"""Submit bounded Host requests through the existing Generic Internal Event API."""
import argparse
import json
import os
import re
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_CONTRACT = Path(__file__).resolve().parents[1] / "operations" / "github-project-bounded-host.json"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
SERVICE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
REQUEST_ID_PATTERN = re.compile(r"^req_[0-9a-f]{24}$")
FILE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]{0,159}$")
CONTAINER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class SendError(RuntimeError):
    pass


def load_contract(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        raise SendError("CONTRACT_JSON_INVALID") from None


def gateway_url(value):
    base = str(value or "").strip().rstrip("/")
    if not base:
        raise SendError("GATEWAY_URL_MISSING")
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SendError("GATEWAY_URL_INVALID")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SendError("GATEWAY_URL_INVALID")
    if base.endswith("/internal/events"):
        return base
    return base + "/internal/events"


def build_event(request, contract):
    transport = contract.get("transport") or {}
    return {
        "eventId": request["id"],
        "eventType": transport.get("event_type"),
        "sourceId": transport.get("source_id"),
        "destinationId": transport.get("destination_id"),
        "subject": "servercore-bounded-host/" + request["command_id"],
        "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data": request,
    }


def validate_cli(command_id, expected_sha, contract, expected_before=None, repository=None,
                 service=None, deploy_request_id=None, path=None, offset=None, container=None, tail=None,
                 session=None, argv=None, timeout_s=None, fresh=None, repo_sha=None,
                 docker_operation=None, host_command=None):
    allowed = contract.get("allowed_command_ids") or []
    if command_id not in allowed:
        raise SendError("COMMAND_NOT_REGISTERED")
    if not SHA_PATTERN.match(expected_sha):
        raise SendError("EXPECTED_SHA_INVALID")
    request = {
        "schema": contract.get("request_schema"),
        "id": "req_" + secrets.token_hex(12),
        "command_id": command_id,
        "expected_sha": expected_sha,
    }
    if command_id == "project.source_reflect":
        if not isinstance(expected_before, str) or not SHA_PATTERN.fullmatch(expected_before):
            raise SendError("REFLECT_BEFORE_INVALID")
        request["expected_before"] = expected_before
    elif expected_before is not None:
        raise SendError("UNEXPECTED_BEFORE_SHA")
    if command_id in {"service.deploy", "docker.operation"}:
        if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository) \
                or not isinstance(service, str) or not SERVICE_PATTERN.fullmatch(service):
            raise SendError("SERVICE_DEPLOY_TARGET_INVALID")
        request["repository"] = repository
        request["service"] = service
    elif command_id not in {"dev.job", "host.command"} and (repository is not None or service is not None):
        raise SendError("UNEXPECTED_DEPLOY_TARGET")
    if command_id == "dev.job":
        if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository) \
                or not isinstance(session, str) or not REQUEST_ID_PATTERN.fullmatch(session) \
                or not isinstance(argv, list) or not 1 <= len(argv) <= 8 \
                or any(not isinstance(a, str) or not 1 <= len(a) <= 1200 for a in argv) \
                or type(timeout_s) is not int or not 1 <= timeout_s <= 15 or type(fresh) is not bool:
            raise SendError("DEV_JOB_TARGET_INVALID")
        if repo_sha is not None and (not isinstance(repo_sha, str) or not SHA_PATTERN.fullmatch(repo_sha)):
            raise SendError("DEV_JOB_REPO_SHA_INVALID")
        if repo_sha is not None:
            request["repo_sha"] = repo_sha
        request.update({"repository": repository, "session": session, "argv": argv,
                        "timeout_s": timeout_s, "fresh": fresh})
    elif session is not None or (argv is not None and command_id != "docker.operation") or timeout_s is not None or fresh is not None:
        raise SendError("UNEXPECTED_DEV_JOB_TARGET")
    if command_id == "host.command":
        if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository) \
                or not isinstance(host_command, str) or not 1 <= len(host_command) <= 1600 or "\x00" in host_command:
            raise SendError("HOST_COMMAND_TARGET_INVALID")
        if not isinstance(repo_sha, str) or not SHA_PATTERN.fullmatch(repo_sha):
            raise SendError("HOST_COMMAND_REPO_SHA_INVALID")
        request.update({"repository": repository, "repo_sha": repo_sha, "command": host_command})
    elif host_command is not None:
        raise SendError("UNEXPECTED_HOST_COMMAND")
    if command_id == "docker.operation":
        if docker_operation not in {"ps", "inspect", "logs", "stats", "start", "stop",
                                    "restart", "up", "exec"}:
            raise SendError("DOCKER_OPERATION_INVALID")
        values = argv or []
        if not isinstance(values, list) or len(values) > 10 or any(
                not isinstance(a, str) or not 1 <= len(a) <= 512 for a in values
        ) or sum(map(len, values)) > 1000 or (docker_operation == "exec") != bool(values):
            raise SendError("DOCKER_OPERATION_ARGV_INVALID")
        if tail is None:
            tail = 100
        if type(tail) is not int or not 1 <= tail <= 200:
            raise SendError("DOCKER_OPERATION_TAIL_INVALID")
        request.update({"operation": docker_operation, "argv": values, "tail": tail})
    elif docker_operation is not None:
        raise SendError("UNEXPECTED_DOCKER_OPERATION")
    if command_id == "service.deploy_status":
        if not isinstance(deploy_request_id, str) or not REQUEST_ID_PATTERN.fullmatch(deploy_request_id):
            raise SendError("DEPLOY_REQUEST_ID_INVALID")
        request["deploy_request_id"] = deploy_request_id
    elif deploy_request_id is not None:
        raise SendError("UNEXPECTED_DEPLOY_REQUEST_ID")
    if command_id == "project.file_inspect":
        if not isinstance(path, str) or not FILE_PATH_PATTERN.fullmatch(path) or ".." in path \
                or type(offset) is not int or not 0 <= offset <= 4_000_000:
            raise SendError("FILE_INSPECT_TARGET_INVALID")
        request["path"] = path
        request["offset"] = offset
    elif path is not None or offset is not None:
        raise SendError("UNEXPECTED_FILE_TARGET")
    if command_id == "docker.logs":
        if not isinstance(container, str) or not CONTAINER_PATTERN.fullmatch(container) \
                or type(tail) is not int or not 1 <= tail <= 200:
            raise SendError("DOCKER_LOGS_TARGET_INVALID")
        request["container"] = container
        request["tail"] = tail
    elif container is not None or (tail is not None and command_id != "docker.operation"):
        raise SendError("UNEXPECTED_LOG_TARGET")
    return request


def send(request, contract, *, env=None, opener=None):
    current = dict(os.environ if env is None else env)
    transport = contract.get("transport") or {}
    url = gateway_url(current.get(transport.get("gateway_url_env", "GACE_EVENT_GATEWAY_URL")))
    token = str(current.get(transport.get("gateway_token_env", "GACE_EVENT_GATEWAY_TOKEN")) or "").strip()
    if not token:
        raise SendError("GATEWAY_TOKEN_MISSING")
    body = json.dumps(build_event(request, contract), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    user_agent = str(
        current.get("GACE_EVENT_GATEWAY_USER_AGENT", "G-ACE-server-core-internal-event/1")
    ).strip()
    http_request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent or "G-ACE-server-core-internal-event/1",
        },
    )
    try:
        timeout = max(1, min(int(current.get("GACE_EVENT_GATEWAY_TIMEOUT_SECONDS", "10")), 30))
    except ValueError as exc:
        raise SendError("GATEWAY_TIMEOUT_INVALID") from exc
    client = opener or urllib.request.build_opener()
    try:
        with client.open(http_request, timeout=timeout) as response:
            status = int(getattr(response, "status", 0) or 0)
            payload = json.loads(response.read(65536))
    except urllib.error.HTTPError as exc:
        raise SendError(f"GATEWAY_HTTP_{exc.code}") from exc
    except Exception as exc:
        raise SendError("GATEWAY_TRANSPORT_FAILED") from exc
    if status != 202 or not isinstance(payload, dict) or payload.get("ok") is not True:
        raise SendError("GATEWAY_DURABLE_RECEIPT_INVALID")
    return payload


def parse_argv(text):
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        raise SendError("DEV_JOB_TARGET_INVALID") from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--expected-before")
    parser.add_argument("--repository")
    parser.add_argument("--service")
    parser.add_argument("--docker-operation")
    parser.add_argument("--host-command")
    parser.add_argument("--deploy-request-id")
    parser.add_argument("--path")
    parser.add_argument("--offset", type=int)
    parser.add_argument("--container")
    parser.add_argument("--tail", type=int)
    parser.add_argument("--session")
    parser.add_argument("--job-argv-json")
    parser.add_argument("--timeout-s", type=int)
    parser.add_argument("--fresh", choices=("true", "false"))
    parser.add_argument("--repo-sha")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    args = parser.parse_args()
    contract = load_contract(args.contract)
    request = validate_cli(args.command_id, args.expected_sha, contract, args.expected_before,
                           args.repository, args.service, args.deploy_request_id,
                           args.path, args.offset, args.container, args.tail,
                           args.session, parse_argv(args.job_argv_json),
                           args.timeout_s, None if args.fresh is None else args.fresh == "true", args.repo_sha,
                           args.docker_operation, args.host_command)
    try:
        receipt = send(request, contract)
        print(json.dumps({"state": "QUEUED", "request_id": request["id"], "gateway": receipt}, sort_keys=True))
        print(f"SERVERCORE_BOUNDED_HOST_COMMAND={request['command_id']}")
        print(f"SERVERCORE_BOUNDED_HOST_SHA={request['expected_sha']}")
        print("SERVERCORE_BOUNDED_HOST_GATEWAY=ACCEPTED")
        return 0
    except SendError as exc:
        print(json.dumps({"state": "FAIL", "failure_class": str(exc)}, sort_keys=True))
        print(f"SERVERCORE_BOUNDED_HOST_GATEWAY={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
