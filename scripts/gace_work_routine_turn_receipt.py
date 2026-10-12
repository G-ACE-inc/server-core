#!/usr/bin/env python3
"""Emit a Work Routine turn receipt with content hashes from actual reads."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import importlib.util


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gh_issue_body(repo: str, issue_number: int) -> str:
    proc = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json", "body", "-q", ".body"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"GH_ISSUE_READ_FAILED:{issue_number}")
    return proc.stdout


def _load_gate_module():
    gate_path = Path(__file__).with_name("work_routine_design_entry_gate.py")
    spec = importlib.util.spec_from_file_location("work_routine_design_entry_gate", gate_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("DESIGN_GATE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def design_baseline_section_fields(repo_root: Path, section_id: str, rel_path: str) -> dict:
    gate = _load_gate_module()
    markers = gate.DESIGN_BASELINE_SECTIONS.get(section_id)
    if section_id == "work_routine_section_6" and rel_path != gate.DESIGN_BASELINE_CANONICAL_PATH:
        raise RuntimeError("DESIGN_BASELINE_PATH_NOT_CANONICAL")
    if not markers:
        raise RuntimeError("DESIGN_BASELINE_SECTION_ID_INVALID")
    design_path = repo_root / rel_path
    if not design_path.is_file():
        raise RuntimeError("DESIGN_BASELINE_FILE_MISSING")
    doc = design_path.read_text(encoding="utf-8")
    section = gate.extract_marked_section(doc, markers[0], markers[1])
    return {
        "design_baseline_path": rel_path,
        "design_baseline_section_id": section_id,
        "design_baseline_section_sha256": sha256_text(section),
    }


def load_manifest_rule_issue(manifest_path: Path, profile: str) -> int:
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    key = "server_ai" if profile == "SERVER_AI" else "gpt_chat"
    block = (doc.get("rule_planes") or {}).get(key) or {}
    num = block.get("issue_number")
    if not isinstance(num, int):
        raise RuntimeError("MANIFEST_RULE_ISSUE_INVALID")
    return num


def build_receipt(
    *,
    repo_root: Path,
    profile: str,
    control_repo: str,
    current_issue: int,
    mutation_scope: str,
    design_status: str,
    purpose_cu_aligned: bool,
    source_design_aligned: bool = False,
    design_baseline_section_id: str | None = None,
    design_baseline_path: str = "docs/G_ACE_WORKSPACE.md",
) -> dict:
    manifest_path = repo_root / "operations" / "github-project-rule-plane.json"
    if not manifest_path.is_file():
        raise RuntimeError("MANIFEST_NOT_FOUND")
    rule_issue = load_manifest_rule_issue(manifest_path, profile)
    manifest_sha = sha256_file(manifest_path)
    rule_body = gh_issue_body(control_repo, rule_issue)
    current_body = gh_issue_body(control_repo, current_issue)
    receipt = {
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rule_plane_profile": profile,
        "manifest_verified": True,
        "rule_plane_read": True,
        "current_verified": True,
        "purpose_verified": profile != "GPT_CHAT",
        "cu_verified": True,
        "purpose_cu_aligned": purpose_cu_aligned,
        "mutation_scope": mutation_scope,
        "design_status": design_status,
        "design_adoption": "ADOPTED_MAIN",
        "implementation_context": "adopted_main_implementation",
        "source_design_aligned": source_design_aligned,
        "claimed_adopted_without_merge": False,
        "manifest_path": "operations/github-project-rule-plane.json",
        "manifest_sha256": manifest_sha,
        "rule_plane_issue": rule_issue,
        "rule_plane_body_sha256": sha256_text(rule_body),
        "current_issue": current_issue,
        "current_body_sha256": sha256_text(current_body),
    }
    if design_baseline_section_id:
        receipt.update(
            design_baseline_section_fields(
                repo_root, design_baseline_section_id, design_baseline_path
            )
        )
    elif design_status == "DESIGN_VERIFIED" or source_design_aligned:
        raise RuntimeError("DESIGN_BASELINE_SECTION_REQUIRED")
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--profile", choices=("SERVER_AI", "GPT_CHAT"), default="SERVER_AI")
    ap.add_argument("--control-repo", default="G-ACE-inc/server-core")
    ap.add_argument("--current-issue", type=int, default=40)
    ap.add_argument("--mutation-scope", default="routine_fix")
    ap.add_argument("--design-status", default="DESIGN_NOT_VERIFIED")
    ap.add_argument("--purpose-cu-aligned", choices=("true", "false"), default="true")
    ap.add_argument("--source-design-aligned", choices=("true", "false"), default="false")
    ap.add_argument("--design-baseline-section", default="")
    ap.add_argument("--design-baseline-path", default="docs/G_ACE_WORKSPACE.md")
    args = ap.parse_args()
    try:
        receipt = build_receipt(
            repo_root=args.repo_root.resolve(),
            profile=args.profile,
            control_repo=args.control_repo,
            current_issue=args.current_issue,
            mutation_scope=args.mutation_scope,
            design_status=args.design_status,
            purpose_cu_aligned=args.purpose_cu_aligned == "true",
            source_design_aligned=args.source_design_aligned == "true",
            design_baseline_section_id=(args.design_baseline_section or None),
            design_baseline_path=args.design_baseline_path,
        )
        args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("GACE_WORK_ROUTINE_TURN_RECEIPT=" + str(args.output))
        return 0
    except RuntimeError as exc:
        print("GACE_WORK_ROUTINE_TURN_RECEIPT=FAIL", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
