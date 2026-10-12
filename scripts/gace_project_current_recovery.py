#!/usr/bin/env python3
"""Read-only recovery of registered G-ACE Project Issue contexts.

This inventory is evidence for a CHAT planner, NEVER authorization to mutate.
Uses the existing authenticated gh CLI; no workflow, token or state store.
"""
import argparse
import json
import re
import subprocess
import sys
from urllib.parse import urlparse

ISSUE_URL = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/issues/([1-9][0-9]*)$")
QUERY = """query($id:ID!,$cursor:String){
 node(id:$id){... on ProjectV2 {
 id items(first:100,after:$cursor){
 pageInfo{hasNextPage endCursor}
 nodes{id content{__typename ... on Issue{url state title}} fieldValues(first:20){
 nodes{... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2FieldCommon{name}}}
 ... on ProjectV2ItemFieldSingleSelectValue{name field{... on ProjectV2FieldCommon{name}}}}}
 }}}}}}
"""
FIELDS = ("Wave", "Gate", "Change Unit", "Mutation Owner")

def gh_graphql(query, variables):
    args = ["gh", "api", "graphql", "-f", "query=" + query]
    for name, value in variables.items():
        if value is not None:
            args += ["-f", name + "=" + value]
    p = subprocess.run(args, capture_output=True, text=True, timeout=60, check=False)
    if p.returncode:
        raise RuntimeError("GRAPHQL_REQUEST_FAILED")
    try:
        data = json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError("GRAPHQL_RESPONSE_INVALID") from exc
    if data.get("errors") or not isinstance(data.get("data"), dict):
        raise RuntimeError("GRAPHQL_ERRORS")
    return data["data"]

def issue_fields(item):
    result = {}
    for node in ((item.get("fieldValues") or {}).get("nodes") or []):
        field = node.get("field") or {}
        name = field.get("name")
        if name in FIELDS:
            value = node.get("text") if "text" in node else node.get("name")
            if isinstance(value, str) and value.strip():
                result[name] = value.strip()
    return result

def recover(project_id, fetch=gh_graphql):
    if not project_id or not re.fullmatch(r"PVT_[A-Za-z0-9_-]+", project_id):
        raise ValueError("PROJECT_ID_INVALID")
    seen_ids, rows, cursor = set(), [], None
    while True:
        data = fetch(QUERY, {"id": project_id, "cursor": cursor})
        project = data.get("node")
        if not isinstance(project, dict) or project.get("id") != project_id:
            raise RuntimeError("PROJECT_ID_MISMATCH")
        items = project.get("items") or {}
        for item in items.get("nodes") or []:
            if not isinstance(item, dict) or not item.get("id") or item["id"] in seen_ids:
                raise RuntimeError("PROJECT_ITEM_DUPLICATE_OR_INVALID")
            seen_ids.add(item["id"])
            content = item.get("content") or {}
            if content.get("__typename") != "Issue":
                continue
            url = content.get("url") or ""
            match = ISSUE_URL.fullmatch(url)
            if not match:
                raise RuntimeError("REGISTERED_ISSUE_URL_INVALID")
            fields = issue_fields(item)
            missing = [f for f in FIELDS if not fields.get(f)]
            state = content.get("state")
            if state not in ("OPEN", "CLOSED"):
                raise RuntimeError("ISSUE_STATE_UNVERIFIED")
            # Only a complete owner+CU pair can be considered for dispatch;
            # this tool never executes that dispatch.
            verdict = ("CLOSED_NO_DISPATCH" if state == "CLOSED" else
                       "OWNER_OR_CU_REQUIRED" if not fields.get("Mutation Owner") or not fields.get("Change Unit") else
                       "READY_FOR_OWNER_CURRENT_RECHECK")
            rows.append({"item_id":item["id"], "issue_url":url,
                         "repository":match.group(1)+"/"+match.group(2),
                         "issue_number":int(match.group(3)),
                         "state":state, "fields":fields, "missing_fields":missing,
                         "recovery":verdict})
        page = items.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            break
        nxt = page.get("endCursor")
        if not nxt or nxt == cursor:
            raise RuntimeError("PROJECT_PAGINATION_INVALID")
        cursor = nxt
    urls = [r["issue_url"] for r in rows]
    if len(set(urls)) != len(urls):
        raise RuntimeError("DUPLICATE_ISSUE_REGISTRATION")
    return {"project_id":project_id, "issue_items":rows, "issue_count":len(rows),
            "dispatch_authorized":False,
            "note":"Registry recovery only; owning Current, branch, CI and actual one-writer lock require independent verification."}

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id",required=True)
    args=parser.parse_args(argv)
    try:
        print(json.dumps(recover(args.project_id),ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,RuntimeError,subprocess.TimeoutExpired,OSError) as exc:
        print("PROJECT_RECOVERY_FAILED="+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
