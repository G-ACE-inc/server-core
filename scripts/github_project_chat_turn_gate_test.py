#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

module_path = Path(__file__).with_name("github_project_chat_turn_gate.py")
spec = importlib.util.spec_from_file_location("gate", module_path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class DecisionTests(unittest.TestCase):
    def test_start(self):
        good = dict(phase="START", profile="GPT_CHAT",
                    manifest_verified=True, rule_full_read=True,
                    current_verified=True, purpose_verified=True,
                    cu_verified=True, source_evidence="github://run/1")
        self.assertEqual(gate.evaluate(good), "PASS")
        for key in ("manifest_verified", "rule_full_read", "current_verified", "purpose_verified", "cu_verified"):
            self.assertNotEqual(gate.evaluate({**good, key: False}), "PASS")
        self.assertEqual(gate.evaluate({**good, "profile": "SERVER_AI"}), "START_PROFILE_MISMATCH")

    def test_failure_replan(self):
        good = dict(phase="FAILURE", failed_step="Host read", failure_evidence="run/42",
                    independent_actions=["Inspect registry"], next_action="Inspect registry",
                    completed_actions=["Inspect registry"],
                    next_action_evidence="https://github.com/G-ACE-inc/server-core/issues/40#issuecomment-6107486587")
        self.assertEqual(gate.evaluate(good), "PASS")
        self.assertEqual(gate.evaluate({**good, "next_action": ""}), "FAILURE_REPLAN_REQUIRED")
        self.assertEqual(gate.evaluate({**good, "next_action": "deploy"}), "FAILURE_NEXT_NOT_IN_AVAILABLE_ACTIONS")
        self.assertEqual(gate.evaluate({**good, "completed_actions": []}), "FAILURE_NEXT_ACTION_NOT_COMPLETED")
        self.assertEqual(gate.evaluate({**good, "completed_actions": ["Deploy"]}), "FAILURE_COMPLETED_NOT_IN_AVAILABLE_ACTIONS")
        self.assertEqual(gate.evaluate({**good, "completed_actions": None}), "FAILURE_COMPLETED_ACTIONS_INVALID")
        self.assertEqual(gate.evaluate({**good, "next_action_evidence": ""}), "FAILURE_NEXT_ACTION_NOT_EXECUTED")
        self.assertEqual(gate.evaluate({**good, "next_action_evidence": None}), "FAILURE_NEXT_ACTION_NOT_EXECUTED")
        self.assertEqual(gate.evaluate({**good, "next_action_evidence": "readback obtained"}), "FAILURE_NEXT_ACTION_NOT_EXECUTED")
        self.assertEqual(gate.evaluate({**good, "next_action_evidence": "https://github.com/G-ACE-inc/server-core/issues/40#issuecomment-6107486587"}), "PASS")
        self.assertEqual(gate.evaluate({**good, "next_action_evidence": "https://github.com/attacker/other/anything"}), "FAILURE_NEXT_ACTION_NOT_EXECUTED")

    def test_live_workflow_has_request_gate_before_host_access(self):
        workflow = (module_path.parents[1] / ".github/workflows/chatgpt-live-api-verify.yml").read_text(encoding="utf-8")
        assert "CHAT_START_GATE_RECEIPT_MISSING" in workflow
        assert "CHAT_START_GATE_PHASE_DENIED" in workflow
        assert '.chat_decision_checkpoint.phase == "START"' in workflow
        assert "python3 scripts/github_project_chat_turn_gate.py --state" in workflow
        assert workflow.index("START Gate for explicit CHAT Host requests") < workflow.index("Require Cloudflare Access credentials")
        assert "CHAT_START_GATE=IDLE" in workflow

    def test_existing_guard_requires_design_preflight_for_cu40(self):
        guard = (module_path.parents[1] / ".github/workflows/server-core-guard.yml").read_text(encoding="utf-8")
        self.assertIn("CU40 design-before-source preflight", guard)
        self.assertIn("DESIGN_BASELINE_REF=", guard)
        self.assertIn("DESIGN_ALIGNMENT_EVIDENCE=", guard)
        self.assertIn("README_UPDATE_REQUIRED=", guard)
        self.assertIn("PROJECT_TREE_UPDATE_REQUIRED=", guard)
        self.assertIn("DESIGN_DELTA_REQUIRED=", guard)
        self.assertIn("SYSTEM_DOCUMENT_REQUIRED=", guard)

    def test_stop_rejects_unfinished(self):
        base = dict(phase="STOP", stop_reason="ALL_ACTIONS_BLOCKED",
                    stop_evidence="run/42", remaining_actions=[])
        self.assertEqual(gate.evaluate(base), "PASS")
        self.assertEqual(gate.evaluate({**base, "remaining_actions": ["Inspect logs"]}), "STOP_RUNNABLE_ACTIONS_REMAIN")
        self.assertEqual(gate.evaluate({**base, "stop_reason": "VERIFIED_COMPLETE"}), "STOP_COMPLETION_UNVERIFIED")
        self.assertEqual(gate.evaluate({**base, "stop_reason": "VERIFIED_COMPLETE",
                                        "completion_verified": True}), "PASS")
        self.assertEqual(gate.evaluate({**base, "stop_reason": "NO_RESPONSE"}), "STOP_REASON_UNVERIFIED")
        self.assertEqual(gate.evaluate({**base, "remaining_actions": None}), "STOP_REMAINING_ACTIONS_UNVERIFIED")

    def test_start_design_gate_blocks_missing_design(self):
        good = dict(
            phase="START", profile="GPT_CHAT",
            manifest_verified=True, rule_full_read=True,
            current_verified=True, purpose_verified=True,
            cu_verified=True, source_evidence="github://run/1",
            mutation_scope="design_changing",
            design_status="DESIGN_NOT_FOUND",
            design_adoption="ADOPTED_MAIN",
            implementation_context="adopted_main_implementation",
            source_design_aligned=True,
        )
        self.assertEqual(gate.evaluate(good), "START_DESIGN_NOT_FOUND_BLOCK")

    def test_start_design_gate_pass_routine_fix(self):
        good = dict(
            phase="START", profile="GPT_CHAT",
            manifest_verified=True, rule_full_read=True,
            current_verified=True, purpose_verified=True,
            cu_verified=True, source_evidence="github://run/1",
            mutation_scope="routine_fix",
            design_status="DESIGN_VERIFIED",
            design_adoption="ADOPTED_MAIN",
            implementation_context="adopted_main_implementation",
            source_design_aligned=True,
        )
        self.assertEqual(gate.evaluate(good), "PASS")

if __name__ == "__main__":
    unittest.main()
