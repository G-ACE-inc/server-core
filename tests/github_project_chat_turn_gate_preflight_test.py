#!/usr/bin/env python3
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from github_project_chat_turn_gate import evaluate


def base_state():
    return {
        "phase": "START",
        "profile": "GPT_CHAT",
        "manifest_verified": True,
        "rule_full_read": True,
        "rule_plane_read": True,
        "rule_plane_profile": "GPT_CHAT",
        "current_verified": True,
        "purpose_verified": True,
        "cu_verified": True,
        "purpose_cu_aligned": True,
        "mutation_scope": "routine_fix",
        "design_status": "DESIGN_NOT_APPLICABLE",
        "design_adoption": "ADOPTED_MAIN",
        "implementation_context": "not_applicable",
        "source_design_aligned": None,
        "claimed_adopted_without_merge": False,
        "source_evidence": "https://github.com/G-ACE-inc/server-core/issues/40",
        "project_current": "https://github.com/G-ACE-inc/server-core/issues/40",
        "mission": "enforce GPT CHAT preflight",
        "change_unit": "CU-PREFLIGHT",
        "mutation_owner": "GPT_CHAT",
        "adopted_design": "Work Routine section 6",
        "status": "PLANNED",
        "work_branch": "codex/main/gpt-chat-preflight-enforcement-20261106",
        "worktree_path": "/home/admin1/server-core",
        "exact_head": "fda997ca2e008cea74ffed11955c3af9e2158462",
        "owned_paths": ["scripts/gpt_chat_mutation_preflight.py"],
        "exact_next_gate": "run focused preflight tests",
        "rollback_plan": "revert the preflight commit",
        "evidence_refs": ["https://github.com/G-ACE-inc/server-core/issues/40"],
    }


class GatePreflightTests(unittest.TestCase):
    def test_start_denies_missing_preflight(self):
        state = base_state()
        self.assertEqual(evaluate(state), "START_PREFLIGHT_REANCHOR_MISSING")

    def test_start_accepts_complete_preflight(self):
        state = base_state()
        state["reanchor"] = {key: state[key] for key in (
            "profile", "project_current", "mission", "change_unit",
            "mutation_owner", "adopted_design", "exact_next_gate", "status",
        )}
        self.assertEqual(evaluate(state), "PASS")


if __name__ == "__main__":
    unittest.main()
