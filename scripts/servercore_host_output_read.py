"""Read lossless chunks from a completed Host terminal output ledger.

This is a read helper for the existing host.command execution channel.
The request id is validated; no arbitrary file path or command is accepted.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

RESULT_DIR = Path("/home/admin1/logs/servercore-service-deploy")
REQUEST_ID = re.compile(r"req_[0-9a-f]{24}")


def chunk(request_id, stream, offset=0, count=8192, result_dir=RESULT_DIR):
    if not REQUEST_ID.fullmatch(request_id):
        raise ValueError("REQUEST_ID_INVALID")
    if stream not in ("stdout", "stderr"):
        raise ValueError("STREAM_INVALID")
    if offset < 0 or not 1 <= count <= 8192:
        raise ValueError("RANGE_INVALID")
    path = Path(result_dir) / (request_id + ".json")
    if path.is_symlink() or not path.is_file():
        raise ValueError("RESULT_UNAVAILABLE")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("request_id") != request_id:
        raise ValueError("RECORD_ID_MISMATCH")
    value = record.get(stream, "")
    if not isinstance(value, str):
        raise ValueError("STREAM_INVALID")
    data = value[offset:offset + count]
    return {
        "request_id": request_id, "stream": stream, "offset": offset,
        "next_offset": offset + len(data), "total_chars": len(value),
        "complete": offset + len(data) >= len(value),
        "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        "data": data,
    }


def main():
    parser = argparse.ArgumentParser(description="Read a Host terminal output slice")
    parser.add_argument("request_id")
    parser.add_argument("stream", choices=("stdout", "stderr"))
    parser.add_argument("offset", type=int)
    parser.add_argument("count", type=int, nargs="?", default=8192)
    args = parser.parse_args()
    print(json.dumps(chunk(args.request_id, args.stream, args.offset, args.count),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
