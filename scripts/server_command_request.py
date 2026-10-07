#!/usr/bin/env python3
import argparse
import json
import os
import re
import secrets
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "operations" / "server-command.json"
REQUEST_FILE_RE = re.compile(r"^cmd_[0-9a-f]{24}\.json$")


class ServerCommandError(RuntimeError):
    pass


def fail(code):
    raise ServerCommandError(code)


def load_contract(path=DEFAULT_CONTRACT):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ServerCommandError("SERVER_COMMAND_CONTRACT_INVALID") from exc
    if data.get("request_schema") != "gace.server-command-request/v1":
        fail("SERVER_COMMAND_CONTRACT_REQUEST_SCHEMA_INVALID")
    if data.get("status_schema") != "gace.server-command-status/v1":
        fail("SERVER_COMMAND_CONTRACT_STATUS_SCHEMA_INVALID")
    if not isinstance(data.get("commands"), dict) or not data["commands"]:
        fail("SERVER_COMMAND_CONTRACT_COMMANDS_INVALID")
    if not isinstance(data.get("targets"), dict) or not data["targets"]:
        fail("SERVER_COMMAND_CONTRACT_TARGETS_INVALID")
    queue = data.get("queue")
    if not isinstance(queue, dict):
        fail("SERVER_COMMAND_CONTRACT_QUEUE_INVALID")
    ttl = int(queue.get("ttl_ms", 0))
    if ttl < 1000 or ttl > 300000:
        fail("SERVER_COMMAND_CONTRACT_TTL_INVALID")
    return data


def queue_root(contract, env=None):
    current = os.environ if env is None else env
    override = str(current.get("GACE_SERVER_COMMAND_QUEUE_ROOT") or "").strip()
    if override:
        return Path(override).resolve()
    rel = str(contract["queue"].get("relative_root") or "").strip()
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        fail("SERVER_COMMAND_QUEUE_ROOT_INVALID")
    return (ROOT / rel).resolve()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def validate_command(contract, command_id, target_id):
    command = str(command_id or "").strip()
    target = str(target_id or "").strip()
    cfg = contract["commands"].get(command)
    if not isinstance(cfg, dict):
        fail("SERVER_COMMAND_NOT_ALLOWED")
    if cfg.get("action") != "read" or cfg.get("arguments") != "none":
        fail("SERVER_COMMAND_CONTRACT_ACTION_INVALID")
    if target not in contract["targets"]:
        fail("SERVER_COMMAND_TARGET_NOT_ALLOWED")
    return command, target


def make_request(contract, command_id, target_id, *, now_ms=None):
    command, target = validate_command(contract, command_id, target_id)
    created = int(time.time() * 1000 if now_ms is None else now_ms)
    ttl = int(contract["queue"]["ttl_ms"])
    return {
        "schema": contract["request_schema"],
        "id": "cmd_" + secrets.token_hex(12),
        "action": "read",
        "command_id": command,
        "target_id": target,
        "created_at": created,
        "expires_at": created + ttl,
    }


def enqueue(contract, command_id, target_id, *, env=None, now_ms=None):
    request = make_request(contract, command_id, target_id, now_ms=now_ms)
    root = queue_root(contract, env=env)
    atomic_json(root / "requests" / f"{request['id']}.json", request)
    return {
        "schema": contract["request_schema"],
        "id": request["id"],
        "state": "QUEUED",
        "action": "read",
        "command_id": request["command_id"],
        "target_id": request["target_id"],
    }


def validate_request_id(contract, request_id):
    value = str(request_id or "").strip()
    try:
        pattern = re.compile(contract["request_id_pattern"])
    except Exception as exc:
        raise ServerCommandError("SERVER_COMMAND_CONTRACT_REQUEST_ID_PATTERN_INVALID") from exc
    if not pattern.fullmatch(value):
        fail("SERVER_COMMAND_REQUEST_ID_INVALID")
    return value


def status(contract, request_id, *, env=None):
    value = validate_request_id(contract, request_id)
    root = queue_root(contract, env=env)
    status_file = root / "status" / f"{value}.json"
    processing = root / "processing" / f"{value}.json"
    request_file = root / "requests" / f"{value}.json"
    if status_file.is_file():
        try:
            result = json.loads(status_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ServerCommandError("SERVER_COMMAND_STATUS_JSON_INVALID") from exc
        if result.get("schema") != contract["status_schema"]:
            fail("SERVER_COMMAND_STATUS_SCHEMA_INVALID")
        return result
    if processing.is_file():
        return {"schema": contract["status_schema"], "id": value, "state": "RUNNING"}
    if request_file.is_file():
        return {"schema": contract["status_schema"], "id": value, "state": "QUEUED"}
    fail("SERVER_COMMAND_REQUEST_NOT_FOUND")


def main():
    parser = argparse.ArgumentParser(description="G-ACE shared bounded server-command queue client")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    sub = parser.add_subparsers(dest="action", required=True)

    req = sub.add_parser("request")
    req.add_argument("--command-id", required=True)
    req.add_argument("--target-id", required=True)

    stat = sub.add_parser("status")
    stat.add_argument("--id", required=True)

    args = parser.parse_args()
    try:
        contract = load_contract(args.contract)
        if args.action == "request":
            result = enqueue(contract, args.command_id, args.target_id)
        else:
            result = status(contract, args.id)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except ServerCommandError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
