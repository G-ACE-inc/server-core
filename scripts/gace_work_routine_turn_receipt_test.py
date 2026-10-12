#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).with_name("gace_work_routine_turn_receipt.py")
GATE = Path(__file__).with_name("work_routine_design_entry_gate.py")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TurnReceiptTests(unittest.TestCase):
    def test_gpt_chat_receipt_passes_design_entry_gate(self):
        receipt_mod = load("receipt", MODULE)
        gate_mod = load("gate", GATE)
        with patch.object(receipt_mod, "gh_issue_body", return_value="## Fixed Project purpose (verbatim)\nCanonical G-ACE purpose\n\n## CURRENT\n"):
            receipt = receipt_mod.build_receipt(
                repo_root=Path(__file__).resolve().parents[1],
                profile="GPT_CHAT",
                control_repo="G-ACE-inc/server-core",
                current_issue=40,
                mutation_scope="routine_fix",
                design_status="DESIGN_NOT_APPLICABLE",
                purpose_cu_aligned=True,
                cu_verified=True,
            )
        self.assertIs(receipt.get("purpose_verified"), True)
        self.assertEqual(gate_mod.evaluate_turn(receipt), "PASS")

    def test_gpt_chat_receipt_rejects_current_without_canonical_purpose(self):
        receipt_mod = load("receipt_no_purpose", MODULE)
        gate_mod = load("gate_no_purpose", GATE)
        with patch.object(receipt_mod, "gh_issue_body", return_value="unrelated current"):
            receipt = receipt_mod.build_receipt(
                repo_root=Path(__file__).resolve().parents[1],
                profile="GPT_CHAT", control_repo="G-ACE-inc/server-core",
                current_issue=40, mutation_scope="routine_fix",
                design_status="DESIGN_NOT_APPLICABLE", purpose_cu_aligned=True, cu_verified=True,
                cu_verified=True,
            )
        self.assertIs(receipt["purpose_verified"], False)
        self.assertEqual(gate_mod.evaluate_turn(receipt), "RULE_ENTRY_PURPOSE_NOT_VERIFIED")

    def test_gpt_chat_receipt_rejects_false_purpose_cu_alignment(self):
        receipt_mod = load("receipt", MODULE)
        gate_mod = load("gate", GATE)
        with patch.object(receipt_mod, "gh_issue_body", return_value="## Fixed Project purpose (verbatim)\nCanonical G-ACE purpose\n"):
            receipt = receipt_mod.build_receipt(
                repo_root=Path(__file__).resolve().parents[1],
                profile="GPT_CHAT",
                control_repo="G-ACE-inc/server-core",
                current_issue=40,
                mutation_scope="routine_fix",
                design_status="DESIGN_NOT_APPLICABLE",
                purpose_cu_aligned=False, cu_verified=True,
            )
        self.assertEqual(gate_mod.evaluate_turn(receipt), "PURPOSE_CU_MISMATCH")


    def test_missing_cu_attestation_is_not_automatically_verified(self):
        receipt_mod = load("receipt_missing_cu", MODULE)
        gate_mod = load("gate_missing_cu", GATE)
        with patch.object(receipt_mod, "gh_issue_body", return_value="## Fixed Project purpose (verbatim)\\nCanonical purpose\\n"):
            receipt = receipt_mod.build_receipt(
                repo_root=Path(__file__).resolve().parents[1],
                profile="GPT_CHAT", control_repo="G-ACE-inc/server-core",
                current_issue=40, mutation_scope="routine_fix",
                design_status="DESIGN_NOT_APPLICABLE", purpose_cu_aligned=None,
            )
        self.assertIs(receipt["cu_verified"], False)
        self.assertIs(receipt["purpose_cu_aligned"], False)
        self.assertNotEqual(gate_mod.evaluate_turn(receipt), "PASS")

    def test_explicit_alignment_is_not_sufficient_without_cu_verification(self):
        receipt_mod = load("receipt_explicit_alignment", MODULE)
        gate_mod = load("gate_explicit_alignment", GATE)
        with patch.object(receipt_mod, "gh_issue_body", return_value="## Fixed Project purpose (verbatim)\\nCanonical purpose\\n"):
            receipt = receipt_mod.build_receipt(
                repo_root=Path(__file__).resolve().parents[1],
                profile="GPT_CHAT", control_repo="G-ACE-inc/server-core",
                current_issue=40, mutation_scope="routine_fix",
                design_status="DESIGN_NOT_APPLICABLE", purpose_cu_aligned=True,
            )
        self.assertIs(receipt["cu_verified"], False)
        self.assertNotEqual(gate_mod.evaluate_turn(receipt), "PASS")


if __name__ == "__main__":
    unittest.main()
