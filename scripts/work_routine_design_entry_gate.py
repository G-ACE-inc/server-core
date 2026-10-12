#!/usr/bin/env python3
"""Work Routine §6 design-first and per-turn rule-entry evidence evaluator.

Evaluates supplied JSON receipts only. It does not intercept ordinary ChatGPT/Cursor
turn submission. CI and bounded mutation entry points may call this mechanically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

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

DESIGN_BASELINE_CANONICAL_PATH = "docs/G_ACE_WORKSPACE.md"
DESIGN_BASELINE_SECTIONS = {
    "work_routine_section_6": (
        "### Design-alignment checks within the existing Work Routine",
        "## 7. Documentation Gate",
    ),
}


def extract_marked_section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise ValueError("section_start_missing")
    end = text.find(end_marker, start)
    if end < 0:
        raise ValueError("section_end_missing")
    return text[start:end].strip()


def design_baseline_hash_required(state: dict) -> bool:
    if os.environ.get("GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH") != "1":
        return False
    if state.get("mutation_scope") == "read_only":
        return False
    if state.get("design_status") == "DESIGN_VERIFIED":
        return True
    if state.get("source_design_aligned") is True:
        return True
    return False


def verify_design_baseline_content_hashes(state: dict) -> str:
    if not design_baseline_hash_required(state):
        return "PASS"
    for key in (
        "design_baseline_path",
        "design_baseline_section_id",
        "design_baseline_section_sha256",
    ):
        if state.get(key) in (None, ""):
            return "DESIGN_BASELINE_EVIDENCE_HASH_REQUIRED"
    section_id = state.get("design_baseline_section_id")
    markers = DESIGN_BASELINE_SECTIONS.get(section_id)
    if not markers:
        return "DESIGN_BASELINE_SECTION_ID_INVALID"
    root_raw = os.environ.get("GACE_WORK_ROUTINE_REPO_ROOT", "").strip()
    if not root_raw:
        return "DESIGN_BASELINE_REPO_ROOT_REQUIRED"
    rel = state.get("design_baseline_path")
    if section_id == "work_routine_section_6" and rel != DESIGN_BASELINE_CANONICAL_PATH:
        return "DESIGN_BASELINE_PATH_NOT_CANONICAL"
    if not isinstance(rel, str) or ".." in rel or rel.startswith("/"):
        return "DESIGN_BASELINE_PATH_INVALID"
    design_path = Path(root_raw) / rel
    if not design_path.is_file():
        return "DESIGN_BASELINE_FILE_MISSING"
    try:
        doc = design_path.read_text(encoding="utf-8")
        section = extract_marked_section(doc, markers[0], markers[1])
    except (OSError, ValueError):
        return "DESIGN_BASELINE_SECTION_UNREADABLE"
    actual = sha256_text(section)
    if actual != state.get("design_baseline_section_sha256"):
        return "DESIGN_BASELINE_HASH_MISMATCH"
    return "PASS"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def gh_issue_body(control_repo: str, issue_number: int) -> str:
    proc = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", control_repo, "--json", "body", "-q", ".body"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("GH_ISSUE_READ_FAILED")
    return proc.stdout


def manifest_rule_issue(manifest_path: Path, profile: str) -> int:
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    key = "server_ai" if profile == "SERVER_AI" else "gpt_chat"
    block = (doc.get("rule_planes") or {}).get(key) or {}
    num = block.get("issue_number")
    if not isinstance(num, int):
        raise ValueError("invalid")
    return num


def verify_evidence_content_hashes(state: dict) -> str:
    if os.environ.get("GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH") != "1":
        return "PASS"
    for key in (
        "manifest_sha256",
        "rule_plane_body_sha256",
        "current_body_sha256",
        "current_issue",
        "rule_plane_issue",
    ):
        if state.get(key) in (None, ""):
            return "RULE_ENTRY_EVIDENCE_HASH_REQUIRED"
    root_raw = os.environ.get("GACE_WORK_ROUTINE_REPO_ROOT", "").strip()
    if not root_raw:
        return "RULE_ENTRY_REPO_ROOT_REQUIRED"
    manifest_rel = state.get("manifest_path") or "operations/github-project-rule-plane.json"
    manifest_path = Path(root_raw) / manifest_rel
    if not manifest_path.is_file():
        return "RULE_ENTRY_MANIFEST_FILE_MISSING"
    actual_manifest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if actual_manifest != state.get("manifest_sha256"):
        return "RULE_ENTRY_MANIFEST_HASH_MISMATCH"
    profile = state.get("rule_plane_profile")
    if profile not in PROFILES:
        return "RULE_ENTRY_PROFILE_INVALID"
    control_repo = os.environ.get("GACE_CONTROL_REPO", "G-ACE-inc/server-core").strip()
    try:
        rule_body = gh_issue_body(control_repo, int(state["rule_plane_issue"]))
        current_body = gh_issue_body(control_repo, int(state["current_issue"]))
        expected_rule = manifest_rule_issue(manifest_path, profile)
    except (RuntimeError, OSError, ValueError, TypeError, json.JSONDecodeError):
        return "RULE_ENTRY_EVIDENCE_READ_FAILED"
    if expected_rule != int(state["rule_plane_issue"]):
        return "RULE_ENTRY_RULE_ISSUE_MISMATCH"
    if sha256_text(rule_body) != state.get("rule_plane_body_sha256"):
        return "RULE_ENTRY_RULE_PLANE_HASH_MISMATCH"
    if sha256_text(current_body) != state.get("current_body_sha256"):
        return "RULE_ENTRY_CURRENT_HASH_MISMATCH"
    return "PASS"


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
    content = verify_evidence_content_hashes(state)
    if content != "PASS":
        return content
    return "PASS"


def evaluate_design(state: dict) -> str:
    scope = state.get("mutation_scope")
    if scope not in MUTATION_SCOPES:
        return "MUTATION_SCOPE_INVALID"
    if scope == "read_only":
        return "PASS"

    baseline = verify_design_baseline_content_hashes(state)
    if baseline != "PASS":
        return baseline

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
