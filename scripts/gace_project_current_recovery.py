#!/usr/bin/env python3
"""Read-only recovery of registered G-ACE Project Issue contexts.

This inventory is evidence for a CHAT planner, NEVER authorization to mutate.
Uses the existing authenticated gh CLI; no workflow, token or state store.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from urllib.parse import urlparse

ISSUE_URL = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/issues/([1-9][0-9]*)$")
QUERY = """query($id:ID!,$cursor:String){
  node(id:$id){
    ... on ProjectV2 {
      id
      items(first:100,after:$cursor){
        pageInfo{hasNextPage endCursor}
        nodes{
          id
          content{__typename ... on Issue{url state title}}
          fieldValues(first:20){
            nodes{
              ... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2FieldCommon{name}}}
              ... on ProjectV2ItemFieldSingleSelectValue{name field{... on ProjectV2FieldCommon{name}}}
            }
          }
        }
      }
    }
  }
}
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

def gh_issue(repo, number):
    p = subprocess.run(["gh", "api", f"repos/{repo}/issues/{number}"], capture_output=True, text=True, timeout=60, check=False)
    if p.returncode:
        raise RuntimeError("ISSUE_CURRENT_READ_FAILED")
    try:
        doc = json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError("ISSUE_CURRENT_INVALID") from exc
    if not isinstance(doc, dict):
        raise RuntimeError("ISSUE_CURRENT_INVALID")
    return doc

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

def recover(project_id, fetch=gh_graphql, fetch_issue=None, *, issue_urls=None,
            include_body=False):
    if not project_id or not re.fullmatch(r"PVT_[A-Za-z0-9_-]+", project_id):
        raise ValueError("PROJECT_ID_INVALID")
    if issue_urls is not None and (
            not isinstance(issue_urls, (list, tuple)) or not issue_urls
            or any(not isinstance(url, str) or not ISSUE_URL.fullmatch(url)
                   for url in issue_urls)):
        raise ValueError("SELECTED_ISSUE_URL_INVALID")
    selected = set(issue_urls) if issue_urls is not None else None
    if include_body and (selected is None or fetch_issue is None):
        raise ValueError("CURRENT_BODY_REQUIRES_SCOPED_LIVE_READ")
    seen_ids, rows, cursor, seen_cursors = set(), [], None, set()
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
            rows.append({"item_id": item["id"], "issue_url": url,
                         "repository": match.group(1) + "/" + match.group(2),
                         "issue_number": int(match.group(3)),
                         "state": content.get("state"), "fields": fields,
                         "missing_fields": [f for f in FIELDS if not fields.get(f)]})
        page = items.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            break
        nxt = page.get("endCursor")
        if not nxt or nxt in seen_cursors:
            raise RuntimeError("PROJECT_PAGINATION_INVALID")
        seen_cursors.add(nxt)
        cursor = nxt
    urls = [r["issue_url"] for r in rows]
    if len(set(urls)) != len(urls):
        raise RuntimeError("DUPLICATE_ISSUE_REGISTRATION")
    if selected is not None and not selected.issubset(urls):
        raise RuntimeError("SELECTED_ISSUE_NOT_REGISTERED")
    registered_count = len(rows)
    # Validate the complete registration before reading ANY Issue body. A scoped
    # caller must not fetch unrelated Current bodies or refetch a returned body.
    rows = [row for row in rows if selected is None or row["issue_url"] in selected]
    for row in rows:
        current = None
        if fetch_issue is not None:
            current = fetch_issue(row["repository"], row["issue_number"])
            if (not isinstance(current, dict) or current.get("html_url") != row["issue_url"]
                    or "pull_request" in current or current.get("state") not in ("open", "closed")
                    or not isinstance(current.get("body"), str)):
                raise RuntimeError("ISSUE_CURRENT_IDENTITY_INVALID")
        state, fields = row["state"], row["fields"]
        if current is not None and current["state"].upper() != state:
            # Fresh owning Current overrides ProjectV2's cached Issue state.
            state = current["state"].upper()
            fields["Project state mismatch"] = "YES"
        if state not in ("OPEN", "CLOSED"):
            raise RuntimeError("ISSUE_STATE_UNVERIFIED")
        row.update({
            "state": state,
            "current_updated_at": current.get("updated_at") if current else None,
            "current_body_sha256": hashlib.sha256(current["body"].encode()).hexdigest() if current else None,
            "recovery": ("CLOSED_NO_DISPATCH" if state == "CLOSED" else
                         "OWNER_OR_CU_REQUIRED" if not fields.get("Mutation Owner") or not fields.get("Change Unit") else
                         "READY_FOR_OWNER_CURRENT_RECHECK"),
        })
        if include_body:
            row["current_body"] = current["body"]
    return {"project_id": project_id, "issue_items": rows, "issue_count": len(rows),
            "registered_issue_count": registered_count, "dispatch_authorized": False,
            "note": "Registry and selected Current evidence only; branch, CI and actual one-writer lock require independent verification."}

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id",required=True)
    parser.add_argument("--issue-url", action="append", help="Recover only this exact registered Issue; repeat for related owned CUs")
    parser.add_argument("--include-body", action="store_true", help="Return the fetched Current body with its hash; requires --issue-url")
    args=parser.parse_args(argv)
    try:
        print(json.dumps(recover(args.project_id, fetch_issue=gh_issue,
                                 issue_urls=args.issue_url, include_body=args.include_body),ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,RuntimeError,subprocess.TimeoutExpired,OSError) as exc:
        print("PROJECT_RECOVERY_FAILED="+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
