#!/usr/bin/env python3
"""Inspect one durable Host result through the EXISTING local Result Sink socket.

No GitHub Issue, token, network listener, shell command, or re-execution.  The
existing result sink authorizes local callers through the Unix socket's owner
and mode; this client does not broaden that boundary.  Output is intentionally
metadata-only and safe to include in bounded operational readback.
"""
import argparse
import json
from pathlib import Path
import re
import socket
import stat
import sys

SOCKET = Path("/run/gace/servercore-result.sock")
SCHEMA = "gace.servercore-bounded-result.query/v1"
REQ_ID = re.compile(r"req_[0-9a-f]{24}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_REPLY = 65536


class ResultQueryError(Exception):
    pass


def lookup(request_id, *, socket_path=SOCKET, connect=None):
    if not isinstance(request_id, str) or not REQ_ID.fullmatch(request_id):
        raise ResultQueryError("REQUEST_ID_INVALID")
    path = Path(socket_path)
    if path.is_symlink() or not path.exists() or not stat.S_ISSOCK(path.stat().st_mode):
        raise ResultQueryError("SINK_SOCKET_UNAVAILABLE")
    client_factory = connect or (lambda: socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))
    client = client_factory()
    try:
        client.settimeout(5)
        client.connect(str(path))
        client.sendall((json.dumps({"schema": SCHEMA, "request_id": request_id}) + "\n").encode("utf-8"))
        chunks, size = [], 0
        while True:
            part = client.recv(min(4096, MAX_REPLY + 1 - size))
            if not part:
                raise ResultQueryError("SINK_REPLY_INCOMPLETE")
            end = part.find(b"\n")
            if end >= 0:
                chunks.append(part[:end])
                break
            size += len(part)
            if size > MAX_REPLY:
                raise ResultQueryError("SINK_REPLY_OVERSIZED")
            chunks.append(part)
        if sum(map(len, chunks)) > MAX_REPLY:
            raise ResultQueryError("SINK_REPLY_OVERSIZED")
        try:
            response = json.loads(b"".join(chunks).decode("utf-8"))
        except (ValueError, UnicodeError):
            raise ResultQueryError("SINK_REPLY_INVALID") from None
    except (OSError, socket.timeout):
        raise ResultQueryError("SINK_CONNECTION_FAILED") from None
    finally:
        client.close()
    if not isinstance(response, dict) or response.get("ok") is not True:
        raise ResultQueryError("SINK_QUERY_REJECTED")
    record = response.get("record")
    if response.get("found") is False and record is None:
        return {"request_id": request_id, "status": "NOT_RECORDED"}
    if not isinstance(record, dict) or record.get("request_id") != request_id:
        raise ResultQueryError("SINK_RECORD_MISMATCH")
    state, code, host_sha = record.get("state"), record.get("exit_code"), record.get("host_sha")
    if (state not in {"PASS", "FAIL", "RETRYABLE"} or type(code) is not int
            or not -1 <= code <= 255
            or not isinstance(host_sha, str) or (host_sha and not SHA.fullmatch(host_sha))):
        raise ResultQueryError("SINK_RECORD_INVALID")
    return {"request_id": request_id, "status": "RECORDED", "state": state,
            "exit_code": code, "host_sha": host_sha,
            "recorded_at": str(record.get("recorded_at") or ""),
            "published": isinstance(record.get("published"), dict)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_id")
    args = parser.parse_args(argv)
    try:
        data = lookup(args.request_id)
        print(json.dumps(data, sort_keys=True))
        return 0
    except ResultQueryError as exc:
        print(json.dumps({"status": "QUERY_FAILED", "failure_class": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
