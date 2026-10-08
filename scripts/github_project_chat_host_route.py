#!/usr/bin/env python3
"""Common CHAT→GitHub→DebugAI bounded Host route validation (server-core contract only)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "operations/github-project-chat-host-routes.json"
CMD_ID_RE = re.compile(r"^cmd_[0-9a-f]{24}$")
COMMAND_ID_RE = re.compile(r"^[a-z][a-z0-9_.]{1,80}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def load_routes() -> dict[str, Any]:
    return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))


def find_route(routes: dict[str, Any], route_id: str) -> dict[str, Any]:
    for route in routes.get("routes", []):
        if route.get("id") == route_id:
            return route
    raise KeyError("ROUTE_NOT_FOUND")


def validate_dispatch(
    *,
    route_id: str,
    repository: str,
    command_id: str,
    execution_repo: str,
    project_control_url: str | None = None,
) -> dict[str, Any]:
    doc = load_routes()
    route = find_route(doc, route_id)
    if not REPO_RE.fullmatch(repository):
        return _fail("REPOSITORY_INVALID")
    if repository not in (route.get("workflow_repository"), route.get("subject_repository")):
        return _fail("REPOSITORY_NOT_BOUND_TO_ROUTE")
    if project_control_url and project_control_url != route.get("project_control_url"):
        return _fail("PROJECT_CONTROL_URL_MISMATCH")
    if not COMMAND_ID_RE.fullmatch(command_id):
        return _fail("COMMAND_ID_INVALID")
    sc = route["server_command"]
    allowed = sc.get("allowed_command_ids") or []
    if command_id not in allowed:
        return _fail("COMMAND_NOT_ALLOWLISTED")
    prefixes = sc.get("allowed_execution_repo_prefixes") or [sc.get("execution_repo")]
    if not any(execution_repo == p or execution_repo.startswith(p.rstrip("/") + "/") for p in prefixes if p):
        return _fail("EXECUTION_REPO_FORBIDDEN")
    if ";" in execution_repo or "|" in execution_repo or "`" in execution_repo:
        return _fail("EXECUTION_REPO_SHELL_METACHAR")
    return {
        "schema": "gace.github-project-chat-host-dispatch/v1",
        "result": "PASS",
        "route_id": route_id,
        "repository": repository,
        "command_id": command_id,
        "execution_repo": execution_repo,
        "read_only": sc.get("read_only", True),
        "transport": doc["transport"]["kind"],
    }


def _fail(code: str) -> dict[str, Any]:
    return {"schema": "gace.github-project-chat-host-dispatch/v1", "result": "FAIL", "error": code}


def chat_handoff(route_id: str) -> dict[str, Any]:
    doc = load_routes()
    route = find_route(doc, route_id)
    return {
        "schema": "gace.github-project-chat-host-handoff/v1",
        "route_id": route_id,
        "project_control_url": route.get("project_control_url"),
        "workflow_repository": route.get("workflow_repository"),
        "subject_repository": route.get("subject_repository"),
        "github_trigger": route.get("github_trigger"),
        "allowed_command_ids": route["server_command"]["allowed_command_ids"],
        "execution_repo": route["server_command"]["execution_repo"],
        "evidence_contract": doc.get("evidence_contract"),
        "note": route.get("chat_handoff_note"),
    }


def parse_evidence(lines: list[str]) -> dict[str, Any]:
    doc = load_routes()
    contract = doc["evidence_contract"]
    text = "\n".join(lines)
    found: dict[str, str] = {}
    for line in lines:
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        found[key.strip()] = val.strip()
    forbidden = [m for m in contract.get("forbidden_markers", []) if m.split("=")[0] in found]
    groups = contract.get("required_markers_any_of_groups") or []
    group_ok = any(all(g in found for g in group) for group in groups) if groups else True
    cmd = found.get("SERVER_COMMAND_REQUEST_ID", "")
    cmd_ok = bool(CMD_ID_RE.fullmatch(cmd)) if cmd else True
    runtime_pass = (
        found.get("SERVER_COMMAND_STATE") == "PASS"
        or found.get("LIVE_HEALTH") == "PASS"
        or found.get("PROBE_RESULT") == "PASS"
    )
    return {
        "schema": "gace.github-project-chat-host-evidence/v1",
        "markers": {k: found[k] for k in sorted(found) if not any(s in k.upper() for s in ("SECRET", "TOKEN", "PASSWORD"))},
        "forbidden_markers_present": forbidden,
        "required_group_satisfied": group_ok,
        "command_id_format_valid": cmd_ok,
        "runtime_terminal_pass": runtime_pass,
        "action_green_alone": False,
        "evidence_usable_for_chat": group_ok and not forbidden and cmd_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    vd = sub.add_parser("validate-dispatch")
    vd.add_argument("--route-id", required=True)
    vd.add_argument("--repository", required=True)
    vd.add_argument("--command-id", required=True)
    vd.add_argument("--execution-repo", required=True)
    vd.add_argument("--project-control-url")
    sub.add_parser("list-routes")
    ho = sub.add_parser("chat-handoff")
    ho.add_argument("--route-id", required=True)
    pe = sub.add_parser("parse-evidence")
    pe.add_argument("--file")
    args = parser.parse_args()
    if args.cmd == "validate-dispatch":
        out = validate_dispatch(
            route_id=args.route_id,
            repository=args.repository,
            command_id=args.command_id,
            execution_repo=args.execution_repo,
            project_control_url=args.project_control_url,
        )
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0 if out.get("result") == "PASS" else 1
    if args.cmd == "list-routes":
        doc = load_routes()
        print(json.dumps([r["id"] for r in doc.get("routes", [])]))
        return 0
    if args.cmd == "chat-handoff":
        print(json.dumps(chat_handoff(args.route_id), indent=2, sort_keys=True))
        return 0
    lines = Path(args.file).read_text(encoding="utf-8").splitlines() if args.file else sys.stdin.read().splitlines()
    print(json.dumps(parse_evidence(lines), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
