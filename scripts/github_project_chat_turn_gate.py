#!/usr/bin/env python3
"""Bounded START/FAILURE/STOP decision gate for workflow checkpoint receipts.

This checks supplied evidence. It cannot intercept a normal ChatGPT reply.
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

PHASES = {"START", "FAILURE", "STOP"}
STOP_REASONS = {"MASTER_INTERRUPT", "MASTER_ONLY_ACTION", "VERIFIED_COMPLETE", "ALL_ACTIONS_BLOCKED"}

# A locator is only a syntax check: no network readback or provenance claim.
EVIDENCE_LOCATOR = re.compile(
    r"^https://github\.com/[^/\s]+/[^/\s]+/(?:issues/[1-9][0-9]*(?:#issuecomment-[1-9][0-9]*)?|actions/runs/[1-9][0-9]*|commit/[0-9a-f]{40}|pull/[1-9][0-9]*)$"
)


def evidence_locator(value):
    return isinstance(value, str) and bool(EVIDENCE_LOCATOR.fullmatch(value))

ALLOWED_KEYS = {
    "phase", "profile", "manifest_verified", "rule_full_read", "rule_plane_read",
    "rule_plane_profile", "current_verified", "purpose_verified", "cu_verified",
    "purpose_cu_aligned", "mutation_scope", "design_status", "design_adoption",
    "implementation_context", "source_design_aligned", "claimed_adopted_without_merge",
    "source_evidence", "failed_step", "failure_evidence", "next_action",
    "independent_actions", "completed_actions", "next_action_evidence", "stop_reason",
    "stop_evidence", "remaining_actions", "completion_verified",
    "mission_acceptance_verified", "same_cu_actions_reviewed", "next_action_decision",
}


def _design_gate():
    module_path = Path(__file__).with_name("work_routine_design_entry_gate.py")
    spec = importlib.util.spec_from_file_location("work_routine_design_entry_gate", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_design_turn(state: dict) -> str:
    module = _design_gate()
    mapped = {
        "manifest_verified": state.get("manifest_verified"),
        "rule_plane_profile": state.get("rule_plane_profile") or state.get("profile"),
        "rule_plane_read": state.get("rule_plane_read", state.get("rule_full_read")),
        "current_verified": state.get("current_verified"),
        "purpose_verified": state.get("purpose_verified"),
        "cu_verified": state.get("cu_verified"),
        "purpose_cu_aligned": state.get("purpose_cu_aligned", True),
        "mutation_scope": state.get("mutation_scope", "routine_fix"),
        "design_status": state.get("design_status", "DESIGN_NOT_APPLICABLE"),
        "design_adoption": state.get("design_adoption", "ADOPTED_MAIN"),
        "implementation_context": state.get("implementation_context", "not_applicable"),
        "source_design_aligned": state.get("source_design_aligned"),
        "claimed_adopted_without_merge": state.get("claimed_adopted_without_merge", False),
    }
    return module.evaluate_turn(mapped)


def evaluate(state):
    if not isinstance(state, dict) or set(state) - ALLOWED_KEYS:
        return "GATE_STATE_INVALID"
    phase = state.get("phase")
    if phase not in PHASES:
        return "GATE_PHASE_INVALID"
    if phase == "START":
        for k in ("manifest_verified", "rule_full_read", "current_verified",
                  "purpose_verified", "cu_verified"):
            if state.get(k) is not True:
                return "START_" + k.upper() + "_NOT_VERIFIED"
        if state.get("profile") != "GPT_CHAT":
            return "START_PROFILE_MISMATCH"
        if state.get("purpose_cu_aligned") is not True:
            return "START_PURPOSE_CU_ALIGNMENT_NOT_VERIFIED"
        if not isinstance(state.get("source_evidence"), str) or not state["source_evidence"].strip():
            return "START_EVIDENCE_MISSING"
        design_out = evaluate_design_turn(state)
        if design_out != "PASS":
            return "START_" + design_out
        return "PASS"
    if phase == "FAILURE":
        if not all(isinstance(state.get(k), str) and state[k].strip()
                   for k in ("failed_step", "failure_evidence")):
            return "FAILURE_EVIDENCE_MISSING"
        independent = state.get("independent_actions")
        if not isinstance(independent, list) or any(not isinstance(a, str) or not a.strip() for a in independent):
            return "FAILURE_ACTIONS_INVALID"
        next_action = state.get("next_action")
        if independent and (not isinstance(next_action, str) or not next_action.strip()):
            return "FAILURE_REPLAN_REQUIRED"
        if next_action and next_action not in independent:
            return "FAILURE_NEXT_NOT_IN_AVAILABLE_ACTIONS"
        completed = state.get("completed_actions")
        if not isinstance(completed, list) or any(not isinstance(a, str) or not a.strip() for a in completed):
            return "FAILURE_COMPLETED_ACTIONS_INVALID"
        if any(a not in independent for a in completed):
            return "FAILURE_COMPLETED_NOT_IN_AVAILABLE_ACTIONS"
        if independent and next_action not in completed:
            return "FAILURE_NEXT_ACTION_NOT_COMPLETED"
        if independent and not evidence_locator(state.get("next_action_evidence")):
            return "FAILURE_NEXT_ACTION_NOT_EXECUTED"
        return "PASS"
    reason = state.get("stop_reason")
    if reason not in STOP_REASONS:
        return "STOP_REASON_UNVERIFIED"
    if not isinstance(state.get("stop_evidence"), str) or not state["stop_evidence"].strip():
        return "STOP_EVIDENCE_MISSING"
    remaining = state.get("remaining_actions")
    if not isinstance(remaining, list) or any(not isinstance(a, str) or not a.strip() for a in remaining):
        return "STOP_REMAINING_ACTIONS_UNVERIFIED"
    if remaining and reason != "MASTER_INTERRUPT":
        return "STOP_RUNNABLE_ACTIONS_REMAIN"
    if reason != "MASTER_INTERRUPT":
        if state.get("same_cu_actions_reviewed") is not True:
            return "STOP_SAME_CU_ACTIONS_NOT_REVIEWED"
        decisions = {
            "VERIFIED_COMPLETE": "MISSION_ACCEPTED",
            "ALL_ACTIONS_BLOCKED": "NO_RUNNABLE_ACTIONS",
            "MASTER_ONLY_ACTION": "MASTER_ONLY_ACTION_REQUIRED",
        }
        if state.get("next_action_decision") != decisions.get(reason):
            return "STOP_MISSION_DECISION_MISMATCH"
    if reason == "VERIFIED_COMPLETE":
        if state.get("completion_verified") is not True or state.get("mission_acceptance_verified") is not True:
            return "STOP_MISSION_ACCEPTANCE_UNVERIFIED"
    elif state.get("mission_acceptance_verified") is True:
        return "STOP_MISSION_ACCEPTANCE_CONTRADICTORY"
    return "PASS"


def next_agent_action(state):
    """Recommend the next in-scope action from existing evidence, without executing it.

    Action/observation separation follows the public OpenHands agent pattern.
    The owning CHAT or existing admitted tool route performs the actual action.
    """
    if not isinstance(state, dict):
        return "RECHECK_CURRENT"
    phase = state.get("phase")
    if phase == "FAILURE":
        actions = state.get("independent_actions")
        if not isinstance(actions, list):
            return "INSPECT_FAILURE_EVIDENCE"
        completed = state.get("completed_actions")
        completed = completed if isinstance(completed, list) else []
        remaining = [a for a in actions if isinstance(a, str) and a.strip() and a not in completed]
        return remaining[0] if remaining else "REASSESS_FAILURE_AND_DESIGN"
    if phase == "STOP":
        remaining = state.get("remaining_actions")
        if isinstance(remaining, list) and remaining:
            return remaining[0]
        if state.get("stop_reason") == "VERIFIED_COMPLETE" and state.get("mission_acceptance_verified") is True:
            return "MISSION_ACCEPTED"
        return "RECHECK_STOP_EVIDENCE"
    if phase == "START":
        return "CONTINUE_OWNED_CU" if evaluate(state) == "PASS" else "RECHECK_CURRENT_AND_DESIGN"
    return "RECHECK_CURRENT"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    args = ap.parse_args()
    state = None
    try:
        with open(args.state, encoding="utf-8") as f:
            state = json.load(f)
        outcome = evaluate(state)
    except (OSError, ValueError):
        outcome = "GATE_INPUT_UNREADABLE"
    print("CHAT_WORKFLOW_DECISION_GATE=" + outcome)
    print("CHAT_NEXT_ACTION=" + next_agent_action(state) if isinstance(state, dict) else "CHAT_NEXT_ACTION=RECHECK_CURRENT")
    return 0 if outcome == "PASS" else 2

if __name__ == "__main__":
    sys.exit(main())
