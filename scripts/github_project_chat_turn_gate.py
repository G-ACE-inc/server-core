#!/usr/bin/env python3
"""Bounded START/FAILURE/STOP decision gate for workflow checkpoint receipts.

This checks supplied evidence. It cannot intercept a normal ChatGPT reply.
"""
import argparse
import json
import re
import sys

PHASES = {"START", "FAILURE", "STOP"}
STOP_REASONS = {"MASTER_INTERRUPT", "MASTER_ONLY_ACTION", "VERIFIED_COMPLETE", "ALL_ACTIONS_BLOCKED"}
# A locator is only a syntax check: no network readback or provenance claim.
EVIDENCE_LOCATOR = re.compile(r"^https://github\\.com/[^/\\s]+/[^/\\s]+/(?:issues/[1-9][0-9]*(?:#issuecomment-[1-9][0-9]*)?|actions/runs/[1-9][0-9]*|commit/[0-9a-f]{40}|pull/[1-9][0-9]*)$")


def evidence_locator(value):
    return isinstance(value, str) and bool(EVIDENCE_LOCATOR.fullmatch(value))


def evaluate(state):
    if not isinstance(state, dict) or set(state) - {
        "phase", "profile", "manifest_verified", "rule_full_read",
        "current_verified", "purpose_verified", "cu_verified",
        "source_evidence", "failed_step", "failure_evidence", "next_action",
        "independent_actions", "completed_actions", "next_action_evidence", "stop_reason",
        "stop_evidence", "remaining_actions", "completion_verified",
    }:
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
        if not isinstance(state.get("source_evidence"), str) or not state["source_evidence"].strip():
            return "START_EVIDENCE_MISSING"
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
    if reason == "VERIFIED_COMPLETE" and state.get("completion_verified") is not True:
        return "STOP_COMPLETION_UNVERIFIED"
    return "PASS"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    args = ap.parse_args()
    try:
        with open(args.state, encoding="utf-8") as f:
            state = json.load(f)
        outcome = evaluate(state)
    except (OSError, ValueError):
        outcome = "GATE_INPUT_UNREADABLE"
    print("CHAT_WORKFLOW_DECISION_GATE=" + outcome)
    return 0 if outcome == "PASS" else 2

if __name__ == "__main__":
    sys.exit(main())
