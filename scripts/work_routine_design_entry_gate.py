#!/usr/bin/env python3
"""Work Routine §6 design-first and per-turn rule-entry evidence evaluator.

Evaluates supplied JSON receipts only. It does not intercept ordinary ChatGPT/Cursor
turn submission. CI and bounded mutation entry points may call this mechanically.
"""
from __future__ import annotations

import argparse
import json
import sys

PROFILES = {"GPT_CHAT", "SERVER_AI"}
MUTATION_SCOPES = {"design_changing", "routine_fix", "read_only"}
DESIGN_STATUSES = {
    "DESIGN_VERIFIED",
    "DESIGN_NOT_FOUND",
    "DESIGN_NOT_VERIFIED",
    "DESIGN_DRIFT",
    "DESIGN_NOT_APPLICABLE",
}
ADOPTIONS = {"ADOPTED_MAIN", "PROPOSED_PR", "UNKNOWN"}
IMPLEMENTATION_CONTEXTS = {"proposed_pr_staging", "adopted_main_implementation", "not_applicable"}


def evaluate_rule_entry(state: dict) -> str:
    for key in ("manifest_verified", "rule_plane_read", "current_verified"):
        if state.get(key) is not True:
            return "RULE_ENTRY_" + key.upper() + "_NOT_VERIFIED"
    profile = state.get("rule_plane_profile")
    if profile not in PROFILES:
        return "RULE_ENTRY_PROFILE_INVALID"
    if profile == "GPT_CHAT" and state.get("purpose_verified") is not True:
        return "RULE_ENTRY_PURPOSE_NOT_VERIFIED"
    if state.get("cu_verified") is not True:
        return "RULE_ENTRY_CU_NOT_VERIFIED"
    if state.get("purpose_cu_aligned") is not True:
        return "PURPOSE_CU_MISMATCH"
    return "PASS"


def evaluate_design(state: dict) -> str:
    scope = state.get("mutation_scope")
    if scope not in MUTATION_SCOPES:
        return "MUTATION_SCOPE_INVALID"
    if scope == "read_only":
        return "PASS"

    status = state.get("design_status")
    if status not in DESIGN_STATUSES:
        return "DESIGN_STATUS_INVALID"

    adoption = state.get("design_adoption")
    if adoption not in ADOPTIONS:
        return "DESIGN_ADOPTION_INVALID"

    ctx = state.get("implementation_context", "not_applicable")
    if ctx not in IMPLEMENTATION_CONTEXTS:
        return "IMPLEMENTATION_CONTEXT_INVALID"

    if state.get("claimed_adopted_without_merge") is True:
        return "DESIGN_ADOPTION_MISREPRESENTED"

    if scope == "design_changing":
        if status == "DESIGN_NOT_FOUND":
            return "DESIGN_NOT_FOUND_BLOCK"
        if status == "DESIGN_NOT_VERIFIED":
            return "DESIGN_NOT_VERIFIED_BLOCK"
        if status == "DESIGN_DRIFT":
            return "DESIGN_DRIFT_BLOCK"
        if status != "DESIGN_VERIFIED":
            return "DESIGN_STATUS_BLOCK"
        if adoption == "PROPOSED_PR" and ctx != "proposed_pr_staging":
            return "DESIGN_NOT_ADOPTED_BLOCK"
        if adoption == "UNKNOWN":
            return "DESIGN_NOT_VERIFIED_BLOCK"
        if state.get("source_design_aligned") is not True:
            return "SOURCE_DESIGN_MISMATCH"
        return "PASS"

    # routine_fix inside adopted design
    if status == "DESIGN_DRIFT" or state.get("source_design_aligned") is False:
        return "SOURCE_DESIGN_MISMATCH"
    if status in ("DESIGN_NOT_FOUND", "DESIGN_NOT_VERIFIED"):
        return "DESIGN_BASELINE_UNKNOWN_FOR_FIX"
    if status not in ("DESIGN_VERIFIED", "DESIGN_NOT_APPLICABLE"):
        return "DESIGN_STATUS_BLOCK"
    if adoption == "PROPOSED_PR" and ctx == "adopted_main_implementation":
        return "DESIGN_NOT_ADOPTED_BLOCK"
    return "PASS"


def evaluate_turn(state: dict) -> str:
    if not isinstance(state, dict):
        return "TURN_STATE_INVALID"
    rule = evaluate_rule_entry(state)
    if rule != "PASS":
        return rule
    return evaluate_design(state)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True, help="JSON file with turn evidence")
    args = ap.parse_args()
    try:
        with open(args.state, encoding="utf-8") as handle:
            state = json.load(handle)
        outcome = evaluate_turn(state)
    except (OSError, ValueError, TypeError):
        outcome = "TURN_INPUT_UNREADABLE"
    print("WORK_ROUTINE_DESIGN_ENTRY_GATE=" + outcome)
    return 0 if outcome == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
