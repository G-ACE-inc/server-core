#!/usr/bin/env python3
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gpt_chat_mutation_preflight import evaluate_mutation_preflight


def valid_state():
    state = {
        "profile": "GPT_CHAT",
        "mutation_scope": "routine_fix",
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
    state["reanchor"] = {key: state[key] for key in (
        "profile", "project_current", "mission", "change_unit",
        "mutation_owner", "adopted_design", "exact_next_gate", "status",
    )}
    return state


class MutationPreflightTests(unittest.TestCase):
    def test_complete_preflight_passes(self):
        self.assertEqual(evaluate_mutation_preflight(valid_state()), "PASS")

    def test_missing_mission_is_denied(self):
        state = valid_state()
        state["mission"] = ""
        self.assertEqual(
            evaluate_mutation_preflight(state), "PREFLIGHT_MISSION_MISSING"
        )

    def test_unverifiable_evidence_is_denied(self):
        state = valid_state()
        state["evidence_refs"] = ["analysis says source was read"]
        self.assertEqual(
            evaluate_mutation_preflight(state), "PREFLIGHT_EVIDENCE_REFS_INVALID"
        )

    def test_reanchor_drift_is_denied(self):
        state = valid_state()
        state["reanchor"]["mission"] = "different mission"
        self.assertEqual(
            evaluate_mutation_preflight(state), "PREFLIGHT_REANCHOR_MISSION_MISMATCH"
        )

    def test_three_turn_reanchor_remains_valid(self):
        state = valid_state()
        for status in ("PLANNED", "EXECUTING", "OBSERVED"):
            state["status"] = status
            state["reanchor"]["status"] = status
            self.assertEqual(evaluate_mutation_preflight(state), "PASS")


if __name__ == "__main__":
    unittest.main()
