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

# Verification admission limits, never silent truncation. These are separate
# from the Host Writer's lossless storage and can be revised with evidence.
MAX_VERIFIED_STREAM_BYTES = 512 * 1024 * 1024
MAX_VERIFIED_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_VERIFIED_ARCHIVE_BYTES = 512 * 1024 * 1024


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



def validate_expected_streams(expected_streams):
    """Apply the same independent metadata admission before download or unzip."""
    import re
    if not isinstance(expected_streams, dict) or set(expected_streams) != {"stdout", "stderr"}:
        raise ValueError("EXPECTED_HOST_STREAM_METADATA_REQUIRED")
    total_expected_bytes = 0
    for info in expected_streams.values():
        if (not isinstance(info, dict) or
                not isinstance(info.get("sha256"), str) or
                not re.fullmatch(r"[a-f0-9]{64}", info["sha256"]) or
                type(info.get("chars")) is not int or info["chars"] < 0 or
                type(info.get("bytes")) is not int or info["bytes"] < 0):
            raise ValueError("EXPECTED_HOST_STREAM_METADATA_INVALID")
        if info["bytes"] > MAX_VERIFIED_STREAM_BYTES:
            raise ValueError("HOST_OUTPUT_UNCOMPRESSED_SIZE_LIMIT")
        total_expected_bytes += info["bytes"]
    if total_expected_bytes > MAX_VERIFIED_TOTAL_BYTES:
        raise ValueError("HOST_OUTPUT_UNCOMPRESSED_SIZE_LIMIT")


def verify_artifact_zip(zip_path, request_id, expected_streams):
    """Verify every byte of an existing Host output ZIP against correlated metadata.

    Never trust the ZIP's self-declared digest alone, and never return plaintext
    Host output in a CHAT checkpoint. The source of expected_streams must be the
    separately validated observation Artifact for the same request id.
    """
    import codecs
    import re

    if not isinstance(request_id, str) or not re.fullmatch(r"req_[a-f0-9]{24}", request_id):
        raise ValueError("REQUEST_ID_INVALID")
    validate_expected_streams(expected_streams)
    if Path(zip_path).stat().st_size > MAX_VERIFIED_ARCHIVE_BYTES:
        raise ValueError("HOST_OUTPUT_ARCHIVE_SIZE_LIMIT")
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if len(names) != 3 or set(names) != {"stdout.txt", "stderr.txt", "manifest.json"}:
            raise ValueError("HOST_OUTPUT_ARCHIVE_MEMBERS_INVALID")
        if any(item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
               for item in archive.infolist()):
            raise ValueError("HOST_OUTPUT_COMPRESSION_UNSUPPORTED")
        if archive.getinfo("manifest.json").file_size > 32768:
            raise ValueError("HOST_OUTPUT_MANIFEST_TOO_LARGE")
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        if not isinstance(manifest, dict) or manifest.get("request_id") != request_id:
            raise ValueError("HOST_OUTPUT_REQUEST_MISMATCH")
        specs = manifest.get("streams")
        if not isinstance(specs, dict) or set(specs) != {"stdout.txt", "stderr.txt"}:
            raise ValueError("HOST_OUTPUT_MANIFEST_STREAMS_INVALID")
        verified = {}
        for stream in ("stdout", "stderr"):
            name = stream + ".txt"
            zip_entry = archive.getinfo(name)
            if zip_entry.file_size > MAX_VERIFIED_STREAM_BYTES:
                raise ValueError("HOST_OUTPUT_EXPANSION_LIMIT")
            item = specs[name]
            expect = expected_streams[stream]
            if (not isinstance(item, dict) or
                    type(item.get("bytes")) is not int or item["bytes"] < 0 or
                    item.get("sha256") != expect["sha256"] or
                    archive.getinfo(name).file_size != item["bytes"] or
                    expect["bytes"] != item["bytes"]):
                raise ValueError("HOST_OUTPUT_MANIFEST_MISMATCH")
            digest = hashlib.sha256()
            decoder = codecs.getincrementaldecoder("utf-8")("strict")
            count = chars = 0
            with archive.open(name, "r") as source:
                while True:
                    data = source.read(65536)
                    if not data:
                        break
                    count += len(data)
                    if count > item["bytes"]:
                        raise ValueError("HOST_OUTPUT_BYTE_COUNT_MISMATCH")
                    digest.update(data)
                    chars += len(decoder.decode(data))
                chars += len(decoder.decode(b"", final=True))
            if (count != item["bytes"] or digest.hexdigest() != item["sha256"] or
                    chars != expect["chars"]):
                raise ValueError("HOST_OUTPUT_DIGEST_OR_LENGTH_MISMATCH")
            verified[stream] = {"bytes": count, "chars": chars, "sha256": digest.hexdigest()}
    return {"request_id": request_id, "streams": verified, "output_complete": True}

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
