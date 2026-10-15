"""Reassemble bounded Host output pages into verified TXT/ZIP Actions artifacts.

Input is JSONL from the existing host-output-read helper (stdout/stderr pages).
The GitHub Actions caller must collect every page from the admitted Host channel.
No log text is placed in GitHub issue comments.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def assemble(pages, output_dir):
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError("OUTPUT_DIR_ALREADY_EXISTS")
    state = {}
    request_id = None
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("PAGE_INVALID")
        rid = page.get("request_id")
        if not isinstance(rid, str) or not rid.startswith("req_") or len(rid) != 28 or any(c not in "0123456789abcdef" for c in rid[4:]):
            raise ValueError("REQUEST_ID_INVALID")
        if request_id is None:
            request_id = rid
        elif request_id != rid:
            raise ValueError("REQUEST_ID_MISMATCH")
        stream = page.get("stream")
        if stream not in ("stdout", "stderr"):
            raise ValueError("STREAM_INVALID")
        data = page.get("data")
        offset, next_offset, total = (page.get(k) for k in ("offset", "next_offset", "total_chars"))
        digest = page.get("sha256")
        if not isinstance(data, str) or any(type(v) is not int for v in (offset, next_offset, total)):
            raise ValueError("PAGE_INVALID")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("HASH_INVALID")
        entry = state.setdefault(stream, {"parts": [], "cursor": 0, "total": total, "sha256": digest, "complete": False})
        if entry["complete"] or entry["cursor"] != offset or next_offset != offset + len(data) or total != entry["total"] or digest != entry["sha256"] or offset < 0 or next_offset > total:
            raise ValueError("PAGE_SEQUENCE_INVALID")
        entry["parts"].append(data)
        entry["cursor"] = next_offset
        if page.get("complete") is not (next_offset == total):
            raise ValueError("COMPLETE_FLAG_INVALID")
        entry["complete"] = page["complete"]
    if request_id is None or set(state) != {"stdout", "stderr"} or not all(v["complete"] for v in state.values()):
        raise ValueError("INCOMPLETE_OUTPUT")
    streams = {}
    for name, entry in state.items():
        data = "".join(entry["parts"]).encode("utf-8")
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("CONTENT_HASH_MISMATCH")
        streams[name + ".txt"] = data
    output_dir.mkdir(parents=True)
    manifest = {"request_id": request_id, "streams": {n: {"bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()} for n, v in streams.items()}}
    (output_dir / "stdout.txt").write_bytes(streams["stdout.txt"])
    (output_dir / "stderr.txt").write_bytes(streams["stderr.txt"])
    with zipfile.ZipFile(output_dir / "output.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in streams.items():
            archive.writestr(name, data)
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", help="Collected pages from existing admitted host.command read")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    with open(args.jsonl, encoding="utf-8") as source:
        manifest = assemble((json.loads(line) for line in source), args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
