#!/usr/bin/env python3
"""Export the EXISTING full Issue #10 comment history in Actions, not into CHAT context."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ISSUE = "repos/G-ACE-inc/server-core/issues/10"
OUT = Path("/tmp/gace-issue10-export")
def api(path):
    proc = subprocess.run(["gh", "api", path], text=True, capture_output=True, timeout=60)
    if proc.returncode:
        raise RuntimeError("GITHUB_ISSUE_API_FAILED:" + proc.stderr[:250])
    return json.loads(proc.stdout)
def main():
    meta = api(ISSUE)
    count = int(meta["comments"])
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "issue10-comments.txt"
    records = OUT / "issue10-comments.jsonl"
    pages = (count + 99) // 100
    ids = set()
    n = 0
    digest = hashlib.sha256()
    with target.open("wb") as dest, records.open("w", encoding="utf-8") as jsonout:
        for page in range(1, pages + 1):
            batch = api(ISSUE + f"/comments?per_page=100&page={page}")
            if not isinstance(batch, list) or len(batch) != (100 if page < pages else count - 100 * (pages - 1)):
                raise RuntimeError("ISSUE_PAGE_SIZE_MISMATCH")
            for item in batch:
                cid = item["id"]
                if cid in ids:
                    raise RuntimeError("ISSUE_DUPLICATE_COMMENT_ID")
                ids.add(cid)
                record = {"id": cid, "created_at": item.get("created_at"), "updated_at": item.get("updated_at"),
                          "url": item.get("html_url"), "author": (item.get("user") or {}).get("login"),
                          "body": item.get("body") or ""}
                jsonout.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                data = ("\n" + "=" * 64 + "\n" + f"COMMENT_ID={cid} URL={record['url']}\n" +
                        f"CREATED={record['created_at']} AUTHOR={record['author']}\n" +
                        "=" * 64 + "\n" + record["body"] + "\n").encode("utf-8")
                dest.write(data)
                digest.update(data)
                n += 1
    if n != count:
        raise RuntimeError("ISSUE_COUNT_MISMATCH")
    manifest = {"issue": "G-ACE-inc/server-core#10", "comment_count_at_snapshot": count,
                "exported_comments": n, "text_bytes": target.stat().st_size,
                "text_sha256": digest.hexdigest(), "jsonl_sha256": hashlib.sha256(records.read_bytes()).hexdigest(),
                "snapshot_note": "GitHub Issue metadata count captured before fetch; concurrent writes may cause fail-closed mismatch"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    with zipfile.ZipFile(OUT / "issue10-comments.zip", "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for name in ("issue10-comments.txt", "issue10-comments.jsonl", "manifest.json"):
            z.write(OUT / name, name)
    print("ISSUE10_EXPORT=PASS")
    print("ISSUE10_EXPORT_COMMENTS=" + str(n))
    print("ISSUE10_EXPORT_TEXT_SHA256=" + digest.hexdigest())
    print("ISSUE10_EXPORT_ZIP_BYTES=" + str((OUT / "issue10-comments.zip").stat().st_size))
if __name__ == "__main__":
    main()
