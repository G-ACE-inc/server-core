#!/usr/bin/env python3
"""Fail-closed GPT CHAT mutation preflight.

This is an admission contract for mutation-capable GPT CHAT turns. It does
not claim to intercept ordinary ChatGPT replies; callers must invoke it before
any source, commit, Host, or external mutation.
"""
from __future__ import annotations

import re
from typing import Any

MUTATION_SCOPES = {"design_changing", "routine_fix"}
STATUSES = {"PLANNED", "EXECUTING", "OBSERVED", "VERIFIED", "INCOMPLETE", "BLOCKED"}
EVIDENCE_LOCATOR = re.compile(
    r"^https://github\.com/[^/\s]+/[^/\s]+/"
    r"(?:issues/[1-9][0-9]*(?:#issuecomment-[1-9][0-9]*)?|"
    r"actions/runs/[1-9][0-9]*|commit/[0-9a-f]{40}|pull/[1-9][0-9]*)$"
)
REQUIRED_STRINGS = (
    "project_current",
    "mission",
    "change_unit",
    "mutation_owner",
    "work_branch",
    "worktree_path",
    "exact_head",
    "exact_next_gate",
    "rollback_plan",
)
REANCHOR_FIELDS = (
    "profile",
    "project_current",
    "mission",
    "change_unit",
    "mutation_owner",
    "adopted_design",
    "exact_next_gate",
    "status",
)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _evidence_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and EVIDENCE_LOCATOR.fullmatch(item) for item in value)
    )


def evaluate_mutation_preflight(state: dict[str, Any]) -> str:
    """Return PASS only when a mutation turn has a complete, correlated preflight."""
    if not isinstance(state, dict):
        return "PREFLIGHT_STATE_INVALID"
    if state.get("mutation_scope") not in MUTATION_SCOPES:
        return "PREFLIGHT_MUTATION_SCOPE_REQUIRED"
    if state.get("profile") != "GPT_CHAT":
        return "PREFLIGHT_PROFILE_MISMATCH"
    for key in REQUIRED_STRINGS:
        if not _nonempty(state.get(key)):
            return "PREFLIGHT_" + key.upper() + "_MISSING"
    owned_paths = state.get("owned_paths")
    if not isinstance(owned_paths, list) or not owned_paths:
        return "PREFLIGHT_OWNED_PATHS_MISSING"
    if any(not _nonempty(path) for path in owned_paths):
        return "PREFLIGHT_OWNED_PATHS_INVALID"
    if not _evidence_list(state.get("evidence_refs")):
        return "PREFLIGHT_EVIDENCE_REFS_INVALID"
    reanchor = state.get("reanchor")
    if not isinstance(reanchor, dict):
        return "PREFLIGHT_REANCHOR_MISSING"
    for key in REANCHOR_FIELDS:
        if key not in reanchor or not _nonempty(reanchor[key]):
            return "PREFLIGHT_REANCHOR_" + key.upper() + "_MISSING"
        if key != "status" and reanchor[key] != state.get(key):
            return "PREFLIGHT_REANCHOR_" + key.upper() + "_MISMATCH"
    if reanchor.get("status") not in STATUSES:
        return "PREFLIGHT_REANCHOR_STATUS_INVALID"
    return "PASS"


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    args = parser.parse_args()
    try:
        with open(args.state, encoding="utf-8") as handle:
            outcome = evaluate_mutation_preflight(json.load(handle))
    except (OSError, ValueError, TypeError):
        outcome = "PREFLIGHT_INPUT_UNREADABLE"
    print("GPT_CHAT_MUTATION_PREFLIGHT=" + outcome)
    return 0 if outcome == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
