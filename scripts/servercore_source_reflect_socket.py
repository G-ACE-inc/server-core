#!/usr/bin/env python3
"""Host-local privilege-separated source-reflect server (UNIX socket ONLY).

The HMAC-bearing Gateway receiver is permanently read-only for its checkout and
may reach this socket only through explicit Host ACL admission.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import socketserver
import stat

from servercore_source_reflect import CANONICAL_ROOT, SHA, ReflectError, reflect

SOCKET_PATH = Path("/run/gace/servercore-source-reflect.sock")
MAX_REQUEST = 2048
REPO = "G-ACE-inc/server-core"
SCHEMA = "gace.servercore-source-reflect.request/v1"
REQ_ID = re.compile(r"^req_[0-9a-f]{24}$")


class AdmissionError(Exception):
    pass


def validate(value):
    if not isinstance(value, dict) or set(value) != {
        "schema", "id", "repository", "branch", "expected_before", "target_sha"
    }:
        raise AdmissionError("REQUEST_KEYS_DENIED")
    if value["schema"] != SCHEMA or value["repository"] != REPO or value["branch"] != "main":
        raise AdmissionError("REQUEST_TARGET_DENIED")
    if not isinstance(value["id"], str) or not REQ_ID.fullmatch(value["id"]):
        raise AdmissionError("REQUEST_ID_DENIED")
    if not isinstance(value["expected_before"], str) or not SHA.fullmatch(value["expected_before"]):
        raise AdmissionError("BEFORE_SHA_INVALID")
    if not isinstance(value["target_sha"], str) or not SHA.fullmatch(value["target_sha"]):
        raise AdmissionError("TARGET_SHA_INVALID")
    return value


def execute_request(value):
    request = validate(value)
    # A socket request never selects the Host repo, branch, command, or effects.
    with open('/tmp/gace-servercore-source-reflect.lock', 'w') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return reflect(CANONICAL_ROOT, request["expected_before"], request["target_sha"])


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(120)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if not raw or len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise AdmissionError("REQUEST_SIZE_DENIED")
            value = json.loads(raw.decode("utf-8"))
            result = execute_request(value)
            reply = {"ok": True, "request_id": value["id"], **result}
        except (AdmissionError, ReflectError) as exc:
            reply = {"ok": False, "error": str(exc)[:80]}
        except (ValueError, UnicodeError, TypeError):
            reply = {"ok": False, "error": "REQUEST_JSON_INVALID"}
        except Exception:
            reply = {"ok": False, "error": "INTERNAL_ERROR"}
        self.wfile.write((json.dumps(reply, separators=(",", ":")) + "\n").encode("utf-8"))


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def serve(path=SOCKET_PATH):
    path = Path(path)
    if path != SOCKET_PATH:
        raise AdmissionError("SOCKET_PATH_DENIED")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise AdmissionError("SOCKET_PARENT_INVALID")
    if path.exists() or path.is_symlink():
        raise AdmissionError("SOCKET_ALREADY_EXISTS")
    old = os.umask(0o117)  # socket 0660; caller group requires Host admission
    try:
        with Server(str(path), Handler) as server:
            mode = stat.S_IMODE(path.stat().st_mode)
            if mode & 0o007:
                raise AdmissionError("SOCKET_WORLD_ACCESS_DENIED")
            server.serve_forever()
    finally:
        os.umask(old)
        # Do not unlink a replaced socket belonging to another service.
        if path.is_socket():
            path.unlink()


def main():
    argparse.ArgumentParser(description="Fixed server-core Host local source reflect socket").parse_args()
    serve()


if __name__ == "__main__":
    main()
