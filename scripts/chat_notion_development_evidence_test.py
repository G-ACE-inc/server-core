"""Regression against real, checked-in development evidence (no mock PRs)."""
import json
import unittest
from pathlib import Path
from scripts.chat_notion_development_evidence import audit_evidence

SOURCE = Path(__file__).resolve().parents[1] / "operations" / "notion-efficiency-development-evidence.json"

class RealNotionEvidenceTests(unittest.TestCase):
    def test_real_pr_chain_and_design(self):
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
        result = audit_evidence(data)
        self.assertEqual(result["merged_pr_count"], 11)
        self.assertEqual((result["first_pr"], result["last_pr"]), (263, 273))
        self.assertEqual(result["live_status"], "NOT_VERIFIED")
    def test_source_evidence_does_not_become_runtime_acceptance(self):
        data = json.loads(SOURCE.read_text(encoding="utf-8"))
        data["acceptance"]["cross_chat_tool_action"] = "PASS"
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_CROSS_CHAT_CLAIM"):
            audit_evidence(data)

if __name__ == "__main__":
    unittest.main()
