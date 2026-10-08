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
    branch: str | None = None,
) -> dict[str, Any]:
    """Strict static CHAT preflight; the Host must independently enforce its policy."""
    doc = load_routes()
    try:
        route = find_route(doc, route_id)
    except KeyError:
        return _fail("ROUTE_NOT_FOUND")
    if not REPO_RE.fullmatch(repository):
        return _fail("REPOSITORY_INVALID")
    if repository != route.get("workflow_repository"):
        return _fail("WORKFLOW_REPOSITORY_MISMATCH")
    if not project_control_url:
        return _fail("PROJECT_CONTROL_URL_REQUIRED")
    if project_control_url != route.get("project_control_url"):
        return _fail("PROJECT_CONTROL_URL_MISMATCH")
    if not branch:
        return _fail("WORKFLOW_BRANCH_REQUIRED")
    if branch not in (route.get("github_trigger", {}).get("allowed_branches") or []):
        return _fail("WORKFLOW_BRANCH_FORBIDDEN")
    if not COMMAND_ID_RE.fullmatch(command_id):
        return _fail("COMMAND_ID_INVALID")
    sc = route["server_command"]
    if command_id not in (sc.get("allowed_command_ids") or []):
        return _fail("COMMAND_NOT_ALLOWLISTED")
    supported = route.get("workflow_supported_command_ids") or []
    if command_id not in supported:
        return _fail("COMMAND_UNSUPPORTED_BY_TRIGGER")
    command_effect = (route.get("command_effects") or {}).get(command_id)
    if command_effect not in ("read_only", "bounded_probe_start"):
        return _fail("COMMAND_EFFECT_UNVERIFIED")
    # Prefix admission is unsafe: a nested path is a different execution target.
    if execution_repo != sc.get("execution_repo"):
        return _fail("EXECUTION_REPO_FORBIDDEN")
    # This preflight intentionally does not claim GitHub Project/Host admission.
    return {
        "schema": "gace.github-project-chat-host-dispatch/v1",
        "result": "PASS",
        "route_id": route_id,
        "repository": repository,
        "subject_repository": route.get("subject_repository"),
        "project_control_url": project_control_url,
        "branch": branch,
        "command_id": command_id,
        "execution_repo": execution_repo,
        "read_only": command_effect == "read_only",
        "command_effect": command_effect,
        "transport": doc["transport"]["kind"],
        "host_authorization_verified": False,
        "static_preflight_only": True,
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
    """Parse emitted GitHub Actions markers, not source-command echoes or ANSI text."""
    doc = load_routes()
    contract = doc["evidence_contract"]
    found: dict[str, str] = {}
    duplicate_conflicts: list[str] = []
    marker_re = re.compile(r"^([A-Z][A-Z0-9_]{1,80})=([^\r\n]*)$")
    timestamp_re = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\s+")
    ansi_re = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
    for raw_line in lines:
        line = timestamp_re.sub("", ansi_re.sub("", raw_line)).strip()
        # GitHub Actions logs contain script source and 'Run echo' annotations;
        # those are not command output or trustworthy result markers.
        match = marker_re.fullmatch(line)
        if not match:
            continue
        key, val = match.group(1), match.group(2).strip()
        if key in found and found[key] != val:
            duplicate_conflicts.append(key)
        found[key] = val

    forbidden = [
        m for m in contract.get("forbidden_markers", [])
        if found.get(m.partition("=")[0]) == m.partition("=")[2]
    ]
    invalid_safety = [
        key for key in ("PRODUCTION_DEPLOY_CALLED", "APPROVE_APPLY_VERIFY_CALLED")
        if key in found and found[key] not in ("YES", "NO")
    ]
    groups = contract.get("required_markers_any_of_groups") or []
    group_ok = any(all(g in found for g in group) for group in groups) if groups else False
    cmd = found.get("SERVER_COMMAND_REQUEST_ID", "")
    cmd_ok = bool(CMD_ID_RE.fullmatch(cmd))
    server_pass = (
        bool(cmd) and cmd_ok
        and found.get("SERVER_COMMAND_STATE") == "PASS"
        and found.get("SERVER_COMMAND_READ_ONLY") == "TRUE"
    )
    # Asteria Host-head readback is transport evidence, not a completed probe.
    host_head_pass = (
        found.get("LIVE_HEALTH") == "PASS"
        and bool(re.fullmatch(r"[a-f0-9]{40}", found.get("LIVE_HOST_HEAD", "")))
    )
    terminal_pass = (server_pass or host_head_pass) and found.get("PROBE_RESULT") != "FAIL"
    usable = (
        group_ok and terminal_pass and not forbidden and not invalid_safety
        and not duplicate_conflicts
    )
    return {
        "schema": "gace.github-project-chat-host-evidence/v1",
        "markers": {
            k: found[k] for k in sorted(found)
            if not any(s in k.upper() for s in ("SECRET", "TOKEN", "PASSWORD"))
        },
        "forbidden_markers_present": forbidden,
        "invalid_safety_markers": invalid_safety,
        "duplicate_conflicting_markers": sorted(set(duplicate_conflicts)),
        "required_group_satisfied": group_ok,
        "command_id_format_valid": cmd_ok if cmd else False,
        "runtime_terminal_pass": terminal_pass,
        "action_green_alone": False,
        "evidence_usable_for_chat": usable,
        "runtime_route_enforcement_verified": False,
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
    vd.add_argument("--branch", required=True)
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
            branch=args.branch,
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
