#!/usr/bin/env python3
"""Fixed read-only Docker log reader for registered containers (UNIX socket only).

Separate admin1 user-level Host service so the low-privilege Receiver never holds
Docker authority. The only operation is `docker logs --tail N --timestamps <name>`
(fixed argv) for a container named in the COMMITTED contract
`operations/github-project-bounded-host.json` -> `registered_log_containers`.
Output is bounded here and redacted/bounded again by the result sink.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socketserver
import stat
import subprocess
import threading
import time

SOCKET_PATH = Path("/run/gace/servercore-docker-logs.sock")
ROOT = Path("/home/admin1/server-core")
CONTRACT_REL = "operations/github-project-bounded-host.json"
SCHEMA = "gace.servercore-docker-logs.request/v1"
KEYS = {"schema", "id", "container", "tail"}
REQ_ID = re.compile(r"^req_[0-9a-f]{24}$")
CONTAINER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
MAX_REQUEST = 1024
MAX_TAIL = 200
MAX_LOG_CHARS = 16000
DOCKER_CANDIDATES = ("/usr/bin/docker", "/usr/local/bin/docker")


class LogsError(Exception):
    pass


def git(*args):
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
           "-c", "safe.directory=" + str(ROOT), "-C", str(ROOT), *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise LogsError("CONTRACT_GIT_FAILED") from None
    return result


def registered_containers(root=ROOT):
    """Authority is the committed contract only (a locally edited contract is denied)."""
    path = Path(root) / CONTRACT_REL
    if path.is_symlink() or not path.is_file():
        raise LogsError("CONTRACT_MISSING")
    if root == ROOT and git("diff", "--quiet", "HEAD", "--", CONTRACT_REL).returncode:
        raise LogsError("CONTRACT_NOT_COMMITTED_STATE")
    try:
        names = json.loads(path.read_text(encoding="utf-8")).get("registered_log_containers")
    except (OSError, ValueError):
        raise LogsError("CONTRACT_INVALID") from None
    if not isinstance(names, list) or any(not isinstance(n, str) or not CONTAINER.fullmatch(n) for n in names):
        raise LogsError("CONTRACT_INVALID")
    return frozenset(names)


def validate(value, registered):
    if not isinstance(value, dict) or set(value) != KEYS or value.get("schema") != SCHEMA:
        raise LogsError("REQUEST_SHAPE_INVALID")
    if not isinstance(value["id"], str) or not REQ_ID.fullmatch(value["id"]):
        raise LogsError("REQUEST_ID_INVALID")
    if not isinstance(value["container"], str) or value["container"] not in registered:
        raise LogsError("CONTAINER_NOT_REGISTERED")
    if type(value["tail"]) is not int or not 1 <= value["tail"] <= MAX_TAIL:
        raise LogsError("TAIL_INVALID")
    return value


def docker_binary(candidates=DOCKER_CANDIDATES):
    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise LogsError("DOCKER_BINARY_MISSING")


def read_logs(request, *, runner=subprocess.run, binary=None):
    argv = [binary or docker_binary(), "logs", "--tail", str(request["tail"]), "--timestamps", request["container"]]
    try:
        result = runner(argv, capture_output=True, text=True, timeout=20, check=False,
                        env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/home/admin1")})
    except (OSError, subprocess.TimeoutExpired):
        raise LogsError("DOCKER_LOGS_EXECUTION_FAILED") from None
    if result.returncode:
        raise LogsError("DOCKER_LOGS_FAILED")
    text = (result.stdout or "") + (result.stderr or "")
    cut = len(text) > MAX_LOG_CHARS
    return {"container": request["container"], "tail": request["tail"],
            "logs": text[-MAX_LOG_CHARS:] if cut else text, "truncated": cut}


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(40)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if not raw or len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise LogsError("REQUEST_SIZE_DENIED")
            request = validate(json.loads(raw.decode("utf-8")), registered_containers())
            reply = {"ok": True, "request_id": request["id"], **read_logs(request)}
        except LogsError as exc:
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
        raise LogsError("SOCKET_PATH_DENIED")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise LogsError("SOCKET_PARENT_INVALID")
    if path.is_socket():
        path.unlink()
    elif path.exists() or path.is_symlink():
        raise LogsError("SOCKET_ALREADY_EXISTS")
    old = os.umask(0o117)
    try:
        with Server(str(path), Handler) as server:
            info = path.stat()
            if stat.S_IMODE(info.st_mode) & 0o007:
                raise LogsError("SOCKET_WORLD_ACCESS_DENIED")
            threading.Thread(target=watch_socket, args=(path, info.st_ino), daemon=True).start()
            server.serve_forever()
    finally:
        os.umask(old)
        if path.is_socket():
            path.unlink()


def main():
    argparse.ArgumentParser(description="Registered container log reader").parse_args()
    serve()


if __name__ == "__main__":
    main()
