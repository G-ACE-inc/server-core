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
import hashlib
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
HOST_WRITER_RESULT_DIR = Path("/home/admin1/logs/servercore-service-deploy")
RESULT_REPOSITORY = "G-ACE-inc/server-core"
RESULT_ISSUE = 10
MARKER = "GACE_BOUNDED_HOST_RESULT"
RECORD_SCHEMA = "gace.servercore-bounded-result.record/v1"
QUERY_SCHEMA = "gace.servercore-bounded-result.query/v1"
MAX_REQUEST = 16777216
STREAM_LIMIT = 4000  # GitHub comment preview only; durable sanitized record uses RECORD_LIMIT
RECORD_LIMIT = 20000
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
_KEYED = re.compile(r"(?i)\b([A-Za-z0-9_.-]*(?:secret|token|password|passwd|api[_-]?key|authorization|hmac|private[_-]?key)[A-Za-z0-9_.-]*)(\\?[\"']?\s*[:=]\s*)(\\?\"[^\"]*\"|'[^']*'|(?:(?!\\n)\S)+)")
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
        if not isinstance(value[key], str):
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
    os.chmod(path.parent, 0o700)  # mkdir mode is masked by the service UMask=0117 (no x bit)
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
    stdout, out_cut = redact(value["stdout"]), False
    stderr, err_cut = redact(value["stderr"]), False
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


def trusted_writer_metadata(record, *, writer_dir=HOST_WRITER_RESULT_DIR):
    """Read exact Host writer ledger for stream hashes, never public raw text.

    The Receiver replaces multi-MB data with a *locator string*, so hashing
    the Result Sink's stdout produces a hash of the locator, not the output.
    Only the separately persisted same-request Writer ledger is authoritative.
    """
    if record.get("command_id") != "host.command":
        return None
    rid = record.get("request_id")
    if not isinstance(rid, str) or not REQ_ID.fullmatch(rid):
        raise SinkError("WRITER_REQUEST_INVALID")
    path = Path(writer_dir) / (rid + ".json")
    if path.is_symlink():
        raise SinkError("WRITER_LEDGER_SYMLINK")
    if not path.is_file():
        # A stored-output locator proves that the Receiver did not carry the
        # original bytes; publishing its digest would forge output evidence.
        if any("GACE_HOST_OUTPUT_STORED" in str(record.get(stream) or "")
               for stream in ("stdout", "stderr")):
            raise SinkError("WRITER_LEDGER_REQUIRED_FOR_STORED_OUTPUT")
        return None  # Pre-execution admission rejection has no Writer ledger.
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SinkError("WRITER_LEDGER_UNREADABLE") from None
    # The Writer executes the *target repository*, so raw.source_sha is
    # request.repo_sha. The Result Sink receipt's record.host_sha instead
    # identifies the shared server-core Dispatcher checkout. Equating these
    # two SHAs worked only when the target was server-core itself; for every
    # other registered repository it permanently blocked result publication.
    # Receiver already verifies the immutable writer request id, repository
    # and target SHA against the original admitted request before Sink write.
    target_repo = raw.get("repository") if isinstance(raw, dict) else None
    target_sha = raw.get("source_sha") if isinstance(raw, dict) else None
    writer_execution_failed = bool(
        isinstance(raw, dict) and raw.get("state") == "FAIL"
        and raw.get("failure_class") == "HOST_COMMAND_EXECUTION_FAILED"
        and raw.get("exit_code") is None
        and "stdout" not in raw and "stderr" not in raw
        and record.get("state") == "FAIL" and record.get("exit_code") == 1)
    if (not isinstance(raw, dict) or raw.get("request_id") != rid
            or not isinstance(target_repo, str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", target_repo)
            or not isinstance(target_sha, str) or not SHA.fullmatch(target_sha)
            or (target_repo == RESULT_REPOSITORY and target_sha != record.get("host_sha"))
            or (not writer_execution_failed and raw.get("exit_code") != record.get("exit_code"))
            or (raw.get("state") == "HOST_COMMAND_PASS") != (record.get("state") == "PASS")):
        raise SinkError("WRITER_LEDGER_CORRELATION_MISMATCH")
    if writer_execution_failed:
        return {"unavailable": True}  # timeout/OS error: original streams unknown
    meta = {}
    for name in ("stdout", "stderr"):
        value = raw.get(name)
        if not isinstance(value, str):
            raise SinkError("WRITER_LEDGER_STREAM_INVALID")
        data = value.encode("utf-8")
        meta[name] = {"bytes": len(data), "chars": len(value),
                      "sha256": hashlib.sha256(data).hexdigest()}
    # Preserve ONLY a recognized source-bound preflight error marker (never
    # the private stderr). It is a diagnostic hint, not causal proof by itself.
    source_errors = {
        70: "CHAT_SOURCE_WORKDIR_MISSING",
        71: "CHAT_SOURCE_GIT_UNAVAILABLE",
        72: "CHAT_SOURCE_ROOT_MISMATCH",
        73: "CHAT_SOURCE_SHA_UNAVAILABLE",
        74: "CHAT_SOURCE_SHA_MISMATCH",
        75: "CHAT_SOURCE_REQUIRED_FILE_MISSING",
        76: "CHAT_SOURCE_DIRTY_WORKTREE",
    }
    marker = source_errors.get(raw.get("exit_code"))
    if (raw.get("source_preflight") is True
            and raw.get("source_preflight_failure") is True
            and raw.get("state") == "FAIL"
            and marker and str(raw.get("stderr") or "").strip() == marker):
        meta["diagnostic_hint"] = marker
    return meta


def comment_body(record, *, writer_dir=HOST_WRITER_RESULT_DIR):
    view = public_view(record)
    view.pop("published", None)
    # The authorized Host Writer ledger is the source of full Host stream
    # digest/length, not the Receiver's GACE_HOST_OUTPUT_STORED locator.
    writer = trusted_writer_metadata(record, writer_dir=writer_dir)
    if writer and writer.get("diagnostic_hint"):
        view["diagnostic_hint"] = writer["diagnostic_hint"]
    # Issue is an index/status surface; never include any Host output text.
    for stream in ("stdout", "stderr"):
        full = str(record.get(stream) or "")
        if writer and writer.get("unavailable") is True:
            # Never invent a zero-byte stdout/stderr digest for a Writer crash
            # or timeout where original output is unavailable.
            view[stream + "_chars"] = None
            view[stream + "_bytes"] = None
            view[stream + "_sha256"] = None
            view[stream + "_preview_truncated"] = True
            view[stream] = ""
            continue
        evidence = (writer or {}).get(stream)
        if evidence is not None:
            view[stream + "_chars"] = evidence["chars"]
            view[stream + "_bytes"] = evidence["bytes"]
            view[stream + "_sha256"] = evidence["sha256"]
            view[stream + "_origin"] = "HOST_WRITER_LEDGER_RAW"
            view[stream + "_preview_truncated"] = evidence["bytes"] != 0
        else:
            view[stream + "_chars"] = len(full)
            view[stream + "_bytes"] = len(full.encode("utf-8"))
            view[stream + "_sha256"] = hashlib.sha256(full.encode("utf-8")).hexdigest()
            view[stream + "_preview_truncated"] = bool(full)
        view[stream] = ""
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


GH_CANDIDATES = ("/home/admin1/bin/gh", "/usr/local/bin/gh", "/usr/bin/gh")


def gh_binary(candidates=GH_CANDIDATES):
    """The user systemd PATH does not include ~/bin; use only fixed absolute candidates."""
    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise SinkError("GH_BINARY_MISSING")


def _gh(args, stdin=None, timeout=40):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.environ.get("HOME", "/home/admin1"),
           "GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1"}
    try:
        result = subprocess.run([gh_binary(), *args], input=stdin, capture_output=True, text=True,
                                timeout=timeout, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired):
        raise SinkError("GH_EXECUTION_FAILED") from None
    if result.returncode:
        raise SinkError("GH_COMMAND_FAILED")
    return result.stdout


def find_published(request_id, since, runner=_gh):
    """Query only recent comment pages, not the entire growing Issue history."""
    issue_path = f"repos/{RESULT_REPOSITORY}/issues/{RESULT_ISSUE}"
    issue = json.loads(runner(["api", issue_path]))
    count = int(issue.get("comments", 0))
    last = max(1, (count + 99) // 100)
    needle = f"<!-- {MARKER} request_id={request_id} -->"
    for page in range(last, max(0, last - 2), -1):
        comments = json.loads(runner(["api", f"{issue_path}/comments?per_page=100&page={page}"]))
        for item in reversed(comments):
            if needle in str(item.get("body") or ""):
                return {"comment_id": int(item["id"]), "url": str(item["html_url"])}
    return None


def publish_record(request_id, *, result_dir=None, runner=_gh, now=None, writer_dir=HOST_WRITER_RESULT_DIR):
    record = read_record(request_id, result_dir)
    if not record or record.get("state") not in TERMINAL or record.get("published"):
        return None
    recorded = datetime.strptime(record["recorded_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    since = (recorded - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = find_published(request_id, since, runner)
    if not found:
        payload = json.dumps({"body": comment_body(record, writer_dir=writer_dir)})
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


def publisher_retry_seconds(failure_count, interval=15):
    """Bound retries without ever abandoning a durable terminal result."""
    return min(300, max(interval, 1) * (2 ** min(max(failure_count - 1, 0), 8)))


def publisher_loop(result_dir=None, runner=_gh, interval=15):
    failures = {}
    retry_at = {}
    while True:
        _WAKE.wait(interval)
        _WAKE.clear()
        for request_id in pending_ids(result_dir):
            if time.monotonic() < retry_at.get(request_id, 0):
                continue
            try:
                publish_record(request_id, result_dir=result_dir, runner=runner)
                failures.pop(request_id, None)
                retry_at.pop(request_id, None)
            except (SinkError, ValueError, KeyError, OSError) as exc:
                failures[request_id] = failures.get(request_id, 0) + 1
                retry_at[request_id] = time.monotonic() + publisher_retry_seconds(failures[request_id], interval)
                print(f"RESULT_PUBLISH_FAILED request_id={request_id} class={type(exc).__name__}:{str(exc)[:60]}",
                      flush=True)


from servercore_host_output_cipher_inbox import InboxError, SCHEMA as CIPHER_SCHEMA, store as store_cipher_chunk


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(30)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if not raw or len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise SinkError("REQUEST_SIZE_DENIED")
            value = json.loads(raw.decode("utf-8"))
            if isinstance(value, dict) and value.get("schema") == CIPHER_SCHEMA:
                reply = {"ok": True, **store_cipher_chunk(value)}
            elif isinstance(value, dict) and value.get("schema") == QUERY_SCHEMA and set(value) == {"schema", "request_id"}:
                record = read_record(value["request_id"])
                reply = {"ok": True, "found": bool(record), "record": public_view(record) if record else None}
            else:
                reply = {"ok": True, **accept_record(value)}
        except InboxError as exc:
            reply = {"ok": False, "error": str(exc)[:80]}
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
