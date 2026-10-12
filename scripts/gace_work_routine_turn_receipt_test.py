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
        with patch.object(receipt_mod, "gh_issue_body", return_value="purpose and cu body"):
            receipt = receipt_mod.build_receipt(
                repo_root=Path(__file__).resolve().parents[1],
                profile="GPT_CHAT",
                control_repo="G-ACE-inc/server-core",
                current_issue=40,
                mutation_scope="routine_fix",
                design_status="DESIGN_NOT_APPLICABLE",
                purpose_cu_aligned=True,
            )
        self.assertIs(receipt.get("purpose_verified"), True)
        self.assertEqual(gate_mod.evaluate_turn(receipt), "PASS")

    def test_gpt_chat_receipt_rejects_false_purpose_cu_alignment(self):
        receipt_mod = load("receipt", MODULE)
        gate_mod = load("gate", GATE)
        with patch.object(receipt_mod, "gh_issue_body", return_value="body"):
            receipt = receipt_mod.build_receipt(
                repo_root=Path(__file__).resolve().parents[1],
                profile="GPT_CHAT",
                control_repo="G-ACE-inc/server-core",
                current_issue=40,
                mutation_scope="routine_fix",
                design_status="DESIGN_NOT_APPLICABLE",
                purpose_cu_aligned=False,
            )
        self.assertEqual(gate_mod.evaluate_turn(receipt), "PURPOSE_CU_MISMATCH")


if __name__ == "__main__":
    unittest.main()
