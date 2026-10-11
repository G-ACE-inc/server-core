#!/usr/bin/env python3
"""Host-local bounded Host command result sink and GitHub result publisher.

The low-privilege Receiver reports the terminal result of each registered
command by request id over a fixed UNIX socket. This service redacts and
bounds stdout/stderr, persists one durable record per request id (first
terminal result wins), and publishes it once as a marker comment on the fixed
control Issue using the Host's existing GitHub CLI connection. No new token,
MCP, workflow or network listener.
"""
import argparse
import json
import os
from pathlib import Path
import re
import socketserver
import stat
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone

SOCKET_PATH = Path("/run/gace/servercore-result.sock")
RESULT_DIR = Path("/home/admin1/logs/servercore-bounded-results")
RESULT_REPOSITORY = "G-ACE-inc/server-core"
RESULT_ISSUE = 10
MARKER = "GACE_BOUNDED_HOST_RESULT"
RECORD_SCHEMA = "gace.servercore-bounded-result.record/v1"
QUERY_SCHEMA = "gace.servercore-bounded-result.query/v1"
MAX_REQUEST = 24576
STREAM_LIMIT = 2000
REQ_ID = re.compile(r"^req_[0-9a-f]{24}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
COMMAND = re.compile(r"^[a-z][a-z0-9_.]{2,63}$")
STATES = {"PASS", "FAIL", "RETRYABLE"}
RECORD_KEYS = {"schema", "request_id", "command_id", "state", "exit_code", "host_sha",
               "expected_sha", "stdout", "stderr", "duration_ms"}
TERMINAL = {"PASS", "FAIL"}
_LOCK = threading.Lock()
_WAKE = threading.Event()

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
)
_KEYED = re.compile(r"(?i)\b([A-Za-z0-9_.-]*(?:secret|token|password|passwd|api[_-]?key|authorization|hmac|private[_-]?key)[A-Za-z0-9_.-]*)(\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|\S+)")
_LONG = re.compile(r"[A-Za-z0-9+/=_-]{48,}")
_CTRL = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class SinkError(Exception):
    pass


def redact(text):
    value = _CTRL.sub("", str(text))
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub("<redacted>", value)
    value = _KEYED.sub(lambda m: m.group(1) + m.group(2) + "<redacted>", value)

    def long_token(match):
        token = match.group(0)
        if re.fullmatch(r"[0-9a-f]{64}", token):  # sha256 digests are evidence, not secrets
            return token
        return "<redacted>"
    return _LONG.sub(long_token, value)


def bound(text, limit=STREAM_LIMIT):
    value = redact(text)
    if len(value) <= limit:
        return value, False
    return value[:limit], True


def validate_record(value):
    if not isinstance(value, dict) or set(value) != RECORD_KEYS or value.get("schema") != RECORD_SCHEMA:
        raise SinkError("RECORD_SHAPE_INVALID")
    if not isinstance(value["request_id"], str) or not REQ_ID.fullmatch(value["request_id"]):
        raise SinkError("REQUEST_ID_INVALID")
    if not isinstance(value["command_id"], str) or not COMMAND.fullmatch(value["command_id"]):
        raise SinkError("COMMAND_ID_INVALID")
    if value["state"] not in STATES:
        raise SinkError("STATE_INVALID")
    if type(value["exit_code"]) is not int or not -1 <= value["exit_code"] <= 255:
        raise SinkError("EXIT_CODE_INVALID")
    for key in ("host_sha", "expected_sha"):
        if not isinstance(value[key], str) or (value[key] and not SHA.fullmatch(value[key])):
            raise SinkError("SHA_INVALID")
    for key in ("stdout", "stderr"):
        if not isinstance(value[key], str) or len(value[key]) > 20000:
            raise SinkError("STREAM_INVALID")
    if type(value["duration_ms"]) is not int or not 0 <= value["duration_ms"] <= 3_600_000:
        raise SinkError("DURATION_INVALID")
    return value


def record_path(request_id, result_dir=None):
    if not REQ_ID.fullmatch(request_id or ""):
        raise SinkError("REQUEST_ID_INVALID")
    return Path(result_dir or RESULT_DIR) / (request_id + ".json")


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
    os.replace(tmp, path)


def read_record(request_id, result_dir=None):
    path = record_path(request_id, result_dir)
    if path.is_symlink() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SinkError("RECORD_UNREADABLE") from None
    return data if isinstance(data, dict) else None


def public_view(record):
    keep = ("request_id", "command_id", "state", "exit_code", "host_sha", "expected_sha",
            "stdout", "stderr", "stdout_truncated", "stderr_truncated", "duration_ms",
            "recorded_at", "attempts", "published")
    return {k: record[k] for k in keep if k in record}


def accept_record(value, *, result_dir=None, now=None):
    validate_record(value)
    stdout, out_cut = bound(value["stdout"])
    stderr, err_cut = bound(value["stderr"])
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _LOCK:
        existing = read_record(value["request_id"], result_dir)
        attempts = int(existing.get("attempts", 0)) + 1 if existing else 1
        if existing and existing.get("state") in TERMINAL:
            # First terminal result wins; a duplicate delivery never rewrites or republishes.
            return {"state": "DUPLICATE", "recorded_state": existing["state"], "attempts": attempts}
        record = {"request_id": value["request_id"], "command_id": value["command_id"],
                  "state": value["state"], "exit_code": value["exit_code"],
                  "host_sha": value["host_sha"], "expected_sha": value["expected_sha"],
                  "stdout": stdout, "stderr": stderr, "stdout_truncated": out_cut,
                  "stderr_truncated": err_cut, "duration_ms": value["duration_ms"],
                  "recorded_at": stamp, "attempts": attempts, "published": None}
        _write(record_path(value["request_id"], result_dir), record)
    if record["state"] in TERMINAL:
        _WAKE.set()
    return {"state": "RECORDED", "recorded_state": record["state"], "attempts": attempts}


def comment_body(record):
    view = public_view(record)
    view.pop("published", None)
    lines = [
        f"<!-- {MARKER} request_id={record['request_id']} -->",
        f"[{MARKER}] request_id={record['request_id']}",
        f"SERVERCORE_BOUNDED_HOST_REQUEST_ID={record['request_id']}",
        f"SERVERCORE_BOUNDED_HOST_COMMAND={record['command_id']}",
        f"SERVERCORE_BOUNDED_HOST_STATE={record['state']}",
        f"SERVERCORE_BOUNDED_HOST_EXIT_CODE={record['exit_code']}",
        f"SERVERCORE_BOUNDED_HOST_SHA={record['host_sha'] or 'NONE'}",
        f"SERVERCORE_BOUNDED_HOST_EXPECTED_SHA={record['expected_sha'] or 'NONE'}",
        "",
        "```json",
        json.dumps(view, sort_keys=True, ensure_ascii=False, indent=1),
        "```",
    ]
    return "\n".join(lines)


def _gh(args, stdin=None, timeout=40):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.environ.get("HOME", "/home/admin1"),
           "GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1"}
    try:
        result = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True,
                                timeout=timeout, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired):
        raise SinkError("GH_EXECUTION_FAILED") from None
    if result.returncode:
        raise SinkError("GH_COMMAND_FAILED")
    return result.stdout


def find_published(request_id, since, runner=_gh):
    path = f"repos/{RESULT_REPOSITORY}/issues/{RESULT_ISSUE}/comments?per_page=100&since={since}"
    out = runner(["api", "--paginate", path, "--jq", ".[] | [.id, .html_url, (.body | contains(\"" +
                  f"<!-- {MARKER} request_id={request_id} -->" + "\"))] | @tsv"])
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[2] == "true":
            return {"comment_id": int(parts[0]), "url": parts[1]}
    return None


def publish_record(request_id, *, result_dir=None, runner=_gh, now=None):
    record = read_record(request_id, result_dir)
    if not record or record.get("state") not in TERMINAL or record.get("published"):
        return None
    recorded = datetime.strptime(record["recorded_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    since = (recorded - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = find_published(request_id, since, runner)
    if not found:
        payload = json.dumps({"body": comment_body(record)})
        out = runner(["api", "-X", "POST", f"repos/{RESULT_REPOSITORY}/issues/{RESULT_ISSUE}/comments",
                      "--input", "-"], stdin=payload)
        data = json.loads(out)
        found = {"comment_id": int(data["id"]), "url": str(data["html_url"])}
    with _LOCK:
        current = read_record(request_id, result_dir)
        current["published"] = {**found, "at": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")}
        _write(record_path(request_id, result_dir), current)
    return found


def pending_ids(result_dir=None):
    base = Path(result_dir or RESULT_DIR)
    ids = []
    if base.is_dir():
        for path in sorted(base.glob("req_*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if data.get("state") in TERMINAL and not data.get("published") and REQ_ID.fullmatch(path.stem):
                ids.append(path.stem)
    return ids


def publisher_loop(result_dir=None, runner=_gh, interval=15):
    failures = {}
    while True:
        _WAKE.wait(interval)
        _WAKE.clear()
        for request_id in pending_ids(result_dir):
            if failures.get(request_id, 0) > 40:
                continue
            try:
                publish_record(request_id, result_dir=result_dir, runner=runner)
                failures.pop(request_id, None)
            except (SinkError, ValueError, KeyError, OSError):
                failures[request_id] = failures.get(request_id, 0) + 1


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(30)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if not raw or len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise SinkError("REQUEST_SIZE_DENIED")
            value = json.loads(raw.decode("utf-8"))
            if isinstance(value, dict) and value.get("schema") == QUERY_SCHEMA and set(value) == {"schema", "request_id"}:
                record = read_record(value["request_id"])
                reply = {"ok": True, "found": bool(record), "record": public_view(record) if record else None}
            else:
                reply = {"ok": True, **accept_record(value)}
        except SinkError as exc:
            reply = {"ok": False, "error": str(exc)[:80]}
        except (ValueError, UnicodeError, TypeError, KeyError):
            reply = {"ok": False, "error": "REQUEST_INVALID"}
        except Exception:
            reply = {"ok": False, "error": "INTERNAL_ERROR"}
        self.wfile.write((json.dumps(reply, separators=(",", ":")) + "\n").encode("utf-8"))


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def watch_socket(path, inode):
    while True:
        time.sleep(10)
        try:
            if path.stat().st_ino != inode:
                os._exit(75)
        except OSError:
            os._exit(75)


def serve(path=SOCKET_PATH):
    path = Path(path)
    if path != SOCKET_PATH:
        raise SinkError("SOCKET_PATH_DENIED")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise SinkError("SOCKET_PARENT_INVALID")
    if path.is_socket():
        path.unlink()
    elif path.exists() or path.is_symlink():
        raise SinkError("SOCKET_ALREADY_EXISTS")
    old = os.umask(0o117)
    try:
        with Server(str(path), Handler) as server:
            info = path.stat()
            if stat.S_IMODE(info.st_mode) & 0o007:
                raise SinkError("SOCKET_WORLD_ACCESS_DENIED")
            threading.Thread(target=watch_socket, args=(path, info.st_ino), daemon=True).start()
            threading.Thread(target=publisher_loop, daemon=True).start()
            _WAKE.set()  # publish anything left unpublished before a restart
            server.serve_forever()
    finally:
        os.umask(old)
        if path.is_socket():
            path.unlink()


def main():
    argparse.ArgumentParser(description="Bounded Host result sink and publisher").parse_args()
    serve()


if __name__ == "__main__":
    main()
