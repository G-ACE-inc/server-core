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



def project_item_issue_identity(project_node: str, item_id: str, expected_url: str) -> bool:
    """Match the exact registered Project item to an Issue URL, never a PR or CU title."""
    query = (
        "query($id:ID!){node(id:$id){... on ProjectV2Item "
        "{id project{id} content{__typename ... on Issue{url}}}}}"
    )
    try:
        proc = subprocess.run(
            ["gh", "api", "graphql", "-f", "query=" + query, "-F", "id=" + item_id],
            capture_output=True, text=True, timeout=60, check=False,
        )
        if proc.returncode:
            return False
        doc = json.loads(proc.stdout)
        if doc.get("errors"):
            return False
        item = (doc.get("data") or {}).get("node") or {}
        return (
            item.get("id") == item_id
            and (item.get("project") or {}).get("id") == project_node
            and (item.get("content") or {}).get("__typename") == "Issue"
            and (item.get("content") or {}).get("url") == expected_url
        )
    except (OSError, ValueError, subprocess.TimeoutExpired, AttributeError):
        return False


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
    purpose_cu_aligned: bool | None,
    cu_verified: bool = False,
    project_item_id: str | None = None,
    source_design_aligned: bool | None = None,
    design_baseline_section_id: str | None = None,
    design_baseline_path: str = "docs/G_ACE_WORKSPACE.md",
) -> dict:
    manifest_path = repo_root / "operations" / "github-project-rule-plane.json"
    if not manifest_path.is_file():
        raise RuntimeError("MANIFEST_NOT_FOUND")
    if current_issue < 1:
        raise RuntimeError("CURRENT_ISSUE_INVALID")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_repo = (manifest.get("control_plane") or {}).get("repository")
    if not expected_repo or control_repo.lower() != expected_repo.lower():
        raise RuntimeError("CURRENT_CONTROL_REPOSITORY_MISMATCH")
    project_node = (manifest.get("project") or {}).get("node_id")
    expected_issue_url = f"https://github.com/{control_repo}/issues/{current_issue}"
    item_identity = bool(project_node and project_item_id and project_item_issue_identity(project_node, project_item_id, expected_issue_url))
    if project_item_id and not item_identity:
        raise RuntimeError("PROJECT_ITEM_CURRENT_IDENTITY_MISMATCH")
    rule_issue = load_manifest_rule_issue(manifest_path, profile)
    manifest_sha = sha256_file(manifest_path)
    rule_body = gh_issue_body(control_repo, rule_issue)
    current_body = gh_issue_body(control_repo, current_issue)
    purpose_marker = "## Fixed Project purpose (verbatim)"
    purpose_section = current_body.split(purpose_marker, 1)[1].split("\n## ", 1)[0].strip() if purpose_marker in current_body else ""
    purpose_verified = bool(purpose_section and not purpose_section.startswith("#"))
    receipt = {
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rule_plane_profile": profile,
        "manifest_verified": True,
        "rule_plane_read": True,
        "current_verified": True,
        "project_item_verified": item_identity,
        # A successful Current fetch is not itself proof that canonical purpose is present.
        "purpose_verified": purpose_verified,
        "cu_verified": cu_verified,
        "purpose_cu_aligned": purpose_cu_aligned is True,
        "mutation_scope": mutation_scope,
        "design_status": design_status,
        "design_adoption": "ADOPTED_MAIN",
        "implementation_context": "adopted_main_implementation",
        "claimed_adopted_without_merge": False,
    }
    if source_design_aligned is True:
        receipt["source_design_aligned"] = True
    elif source_design_aligned is False:
        receipt["source_design_aligned"] = False
    receipt.update({
        "manifest_path": "operations/github-project-rule-plane.json",
        "manifest_sha256": manifest_sha,
        "rule_plane_issue": rule_issue,
        "rule_plane_body_sha256": sha256_text(rule_body),
        "current_issue": current_issue,
        "project_item_id": project_item_id or "",
        "current_body_sha256": sha256_text(current_body),
    })
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
    ap.add_argument("--current-issue", type=int, required=True, help="Explicit owning Current issue; never default to CU40")
    ap.add_argument("--project-item-id", default=None, help="Exact Project #1 Issue item ID for live identity check")
    ap.add_argument("--mutation-scope", default="routine_fix")
    ap.add_argument("--design-status", default="DESIGN_NOT_VERIFIED")
    ap.add_argument("--purpose-cu-aligned", choices=("true", "false"), default=None)
    ap.add_argument("--cu-verified", choices=("true", "false"), default=None)
    ap.add_argument("--source-design-aligned", choices=("true", "false"), default=None)
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
            purpose_cu_aligned=(args.purpose_cu_aligned == "true" if args.purpose_cu_aligned else None),
            cu_verified=(args.cu_verified == "true"),
            project_item_id=args.project_item_id,
            source_design_aligned=(
                True
                if args.source_design_aligned == "true"
                else False
                if args.source_design_aligned == "false"
                else None
            ),
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
