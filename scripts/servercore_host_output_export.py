"""Export complete persisted Host stdout/stderr to TXT or ZIP without clipping."""
import argparse
import hashlib
import json
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
    if zipped:
        with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in streams.items():
                archive.writestr(name, data)
            archive.writestr("manifest.json", json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        # Single text file with no length caps; use ZIP for separate streams.
        target.write_bytes(streams["stdout.txt"])
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
