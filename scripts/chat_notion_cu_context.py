#!/usr/bin/env python3
"""Build bounded CU decision context from existing Notion search results.

Notion retrieval is performed by the connected CHAT plugin, not by a new token.
GitHub Current remains authoritative. This helper only filters, validates and
packs the retrieved records so a CHAT can resume the Agent Loop.
"""
import argparse
import json
import re
from pathlib import Path

ISSUE = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*\Z")
KIND = {"IDEA", "RESEARCH", "ALTERNATIVE", "DECISION", "DESIGN", "IMPLEMENTATION",
        "OBSERVATION", "VERIFICATION", "FAILURE_LESSON", "DEPENDENCY", "NEXT"}
STATE = {"PROPOSED", "ADOPTED", "REJECTED", "SUPERSEDED", "UNKNOWN"}

def build(cu_url, records, github_current_url, max_records=40):
    if not isinstance(cu_url, str) or not ISSUE.fullmatch(cu_url):
        raise ValueError("CU_URL_INVALID")
    if github_current_url != cu_url:
        raise ValueError("GITHUB_CURRENT_REQUIRED")
    if not isinstance(records, list) or len(records) > 200:
        raise ValueError("RECORDS_INVALID")
    selected, seen = [], set()
    for rec in records:
        if not isinstance(rec, dict) or rec.get("cu_url") != cu_url:
            continue
        if rec.get("kind") not in KIND or rec.get("state", "UNKNOWN") not in STATE:
            continue
        url, summary = rec.get("notion_url"), rec.get("summary")
        if not isinstance(url, str) or not url.startswith("https://") or not isinstance(summary, str):
            continue
        if len(summary) > 1500 or len(url) > 500 or url in seen:
            continue
        seen.add(url)
        selected.append({"kind": rec["kind"], "state": rec.get("state", "UNKNOWN"),
                         "summary": summary, "notion_url": url,
                         "design_url": rec.get("design_url") if isinstance(rec.get("design_url"), str) else None})
        if len(selected) >= max_records:
            break
    return {"schema": "gace.chat.notion-context.v1", "cu_url": cu_url,
            "github_current_authority": github_current_url,
            "records": selected, "count": len(selected),
            "next_action": "READ_GITHUB_CURRENT_AND_EXECUTE_TOOL",
            "coverage": "PARTIAL_RETRIEVED_RECORDS_ONLY"}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cu-url", required=True)
    p.add_argument("--github-current-url", required=True)
    p.add_argument("--notion-search-json", type=Path, required=True)
    args = p.parse_args()
    data = json.loads(args.notion_search_json.read_text(encoding="utf-8"))
    print(json.dumps(build(args.cu_url, data, args.github_current_url), ensure_ascii=False))

if __name__ == "__main__":
    main()
