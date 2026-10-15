"""Validate one development's real GitHub/Notion evidence before CU use."""
import json
from pathlib import Path

def audit_evidence(record):
    if record.get("schema") != "gace.notion.efficiency.evidence.v1":
        raise ValueError("EVIDENCE_SCHEMA_INVALID")
    design = record.get("design", {})
    if design.get("section") != "13" or not design.get("url", "").startswith("https://github.com/"):
        raise ValueError("DESIGN_NOT_GROUNDED")
    prs = record.get("pull_requests", [])
    if not isinstance(prs, list) or not prs:
        raise ValueError("NO_PR_EVIDENCE")
    ids = set()
    for pr in prs:
        n = pr.get("pr_number")
        if type(n) is not int or n in ids or pr.get("url") != (
            "https://github.com/G-ACE-inc/server-core/pull/" + str(n)
        ):
            raise ValueError("PR_IDENTITY_INVALID")
        ids.add(n)
        if pr.get("merged") is not True or len(pr.get("merge_sha", "")) != 40:
            raise ValueError("MERGE_NOT_PROVEN")
    statuses = record.get("acceptance", {})
    if statuses.get("notion_connector_to_cli_live") != "NOT_VERIFIED":
        raise ValueError("UNSUPPORTED_LIVE_CLAIM")
    if statuses.get("cross_chat_tool_action") != "NOT_VERIFIED":
        raise ValueError("UNSUPPORTED_CROSS_CHAT_CLAIM")
    return {
        "schema": "gace.notion.efficiency.audit.v1",
        "cu_url": record["cu"]["url"],
        "design_url": design["url"],
        "notion_minutes_url": record["notion"]["minutes_url"],
        "merged_pr_count": len(prs),
        "first_pr": min(ids),
        "last_pr": max(ids),
        "source_status": "MERGED_EVIDENCE_ONLY",
        "live_status": "NOT_VERIFIED",
        "next_action": "RUN_ONE_CU_LIVE_NOTION_GITHUB_CONTINUATION_PILOT"
    }

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    args = p.parse_args()
    result = audit_evidence(json.loads(args.source.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
