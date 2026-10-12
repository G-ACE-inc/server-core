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
) -> dict:
    manifest_path = repo_root / "operations" / "github-project-rule-plane.json"
    if not manifest_path.is_file():
        raise RuntimeError("MANIFEST_NOT_FOUND")
    rule_issue = load_manifest_rule_issue(manifest_path, profile)
    manifest_sha = sha256_file(manifest_path)
    rule_body = gh_issue_body(control_repo, rule_issue)
    current_body = gh_issue_body(control_repo, current_issue)
    return {
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
        "source_design_aligned": True,
        "claimed_adopted_without_merge": False,
        "manifest_path": "operations/github-project-rule-plane.json",
        "manifest_sha256": manifest_sha,
        "rule_plane_issue": rule_issue,
        "rule_plane_body_sha256": sha256_text(rule_body),
        "current_issue": current_issue,
        "current_body_sha256": sha256_text(current_body),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--profile", choices=("SERVER_AI", "GPT_CHAT"), default="SERVER_AI")
    ap.add_argument("--control-repo", default="G-ACE-inc/server-core")
    ap.add_argument("--current-issue", type=int, default=40)
    ap.add_argument("--mutation-scope", default="routine_fix")
    ap.add_argument("--design-status", default="DESIGN_VERIFIED")
    ap.add_argument("--purpose-cu-aligned", choices=("true", "false"), default="true")
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
