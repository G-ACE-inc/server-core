"""Integration regression with the real merged Notion-efficiency PR record."""
import json
import unittest
from pathlib import Path
from scripts.chat_notion_development_evidence import audit_evidence

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "operations" / "notion-efficiency-development-evidence.json"

def attach_for_cu(cu_url, data):
    audited = audit_evidence(data)
    if audited["cu_url"] != cu_url:
        raise ValueError("DEVELOPMENT_CU_MISMATCH")
    return audited

class RealEvidenceContinuationTests(unittest.TestCase):
    def test_real_development_data_matches_existing_cu(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        got = attach_for_cu("https://github.com/G-ACE-inc/server-core/issues/40", data)
        self.assertEqual(got["merged_pr_count"], 11)
        self.assertEqual(got["live_status"], "NOT_VERIFIED")

    def test_cannot_attach_same_history_to_unrelated_cu(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "DEVELOPMENT_CU_MISMATCH"):
            attach_for_cu("https://github.com/G-ACE-inc/server-core/issues/10", data)

if __name__ == "__main__":
    unittest.main()
