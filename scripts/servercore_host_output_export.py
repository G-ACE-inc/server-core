"""Export complete persisted Host stdout/stderr to TXT or ZIP without clipping."""
import argparse
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path

RESULT_DIR = Path("/home/admin1/logs/servercore-service-deploy")
REQ = re.compile(r"req_[0-9a-f]{24}\Z")


def export_output(request_id, target, *, result_dir=RESULT_DIR, zipped=False):
    if not REQ.fullmatch(request_id):
        raise ValueError("REQUEST_ID_INVALID")
    source = Path(result_dir) / (request_id + ".json")
    if source.is_symlink() or not source.is_file():
        raise ValueError("RESULT_UNAVAILABLE")
    record = json.loads(source.read_text(encoding="utf-8"))
    if record.get("request_id") != request_id:
        raise ValueError("RECORD_ID_MISMATCH")
    streams = {}
    for name in ("stdout", "stderr"):
        value = record.get(name, "")
        if not isinstance(value, str):
            raise ValueError("STREAM_INVALID")
        streams[name + ".txt"] = value.encode("utf-8")
    target = Path(target)
    if target.exists() or target.is_symlink():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    meta = {"request_id": request_id, "streams": {
        name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in streams.items()}}
    # Host plaintext stays owner-only even with a permissive caller umask.
    # Exclusive creation also closes the exists()/write race for TXT exports.
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            if zipped:
                with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    for name, data in streams.items():
                        archive.writestr(name, data)
                    archive.writestr("manifest.json", json.dumps(meta, ensure_ascii=False, indent=2))
            else:
                # Single text file; use ZIP for separate streams.
                output.write(streams["stdout.txt"])
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return meta


def main():
    p = argparse.ArgumentParser()
    p.add_argument("request_id")
    p.add_argument("target")
    p.add_argument("--zip", action="store_true")
    args = p.parse_args()
    print(json.dumps(export_output(args.request_id, args.target, zipped=args.zip)))


if __name__ == "__main__":
    main()
