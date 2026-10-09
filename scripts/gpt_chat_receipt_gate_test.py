#!/usr/bin/env python3
import copy
import unittest
from gpt_chat_receipt_gate import validate

PURPOSE = "Maintain the Master-defined project outcome without rewriting it."
REPORT = """## 開発目的
""" + PURPOSE + """
## 作業目的
Verify a bounded proof of re-anchor.
## 作業内容
Verified one readback and an actual change.
## NEXT
Check independent CI evidence.
## プロジェクト進行表
➔今ここ: receipt proof in progress
"""


def valid():
    return {
        "project_purpose_canonical": PURPOSE,
        "master_latest_intent": "Only GPT CHAT compliance",
        "current_work_purpose": "Enforce observable evidence at a controlled boundary",
        "current_task": "Receipt validation",
        "last_confirmed_state": "Issue #40 scoped",
        "next_action": "Verify independent CI",
        "must_preserve": "Original reporting order and parallel owners",
        "must_not_happen": "Server/Host mutation",
        "blocker": "None",
        "rule_revision": "test-revision",
        "expected_rule_revision": "test-revision",
        "owner_cu": "G-ACE-inc/server-core#40",
        "expected_owner_cu": "G-ACE-inc/server-core#40",
        "current_issue_url": "https://github.com/G-ACE-inc/server-core/issues/40",
        "readback_verified": True,
        "outstanding_in_scope_work": True,
        "turn_continuation": "EXECUTED_TO_SAFE_GATE",
        "report": REPORT,
    }


def expected():
    x = valid()
    return {k: x[k] for k in ("owner_cu", "rule_revision", "project_purpose_canonical", "current_issue_url")}


class ReceiptGate(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate(valid(), expected()), [])

    def test_stale_rule(self):
        x = valid()
        x["rule_revision"] = "stale"
        self.assertIn("RULE_STALE_OR_MISMATCH", validate(x, expected()))

    def test_wrong_cu(self):
        x = valid()
        x["owner_cu"] = "other-chat"
        self.assertIn("CU_OWNER_MISMATCH", validate(x, expected()))

    def test_no_readback(self):
        x = valid()
        x["readback_verified"] = False
        self.assertIn("CURRENT_NOT_READ_BACK", validate(x, expected()))

    def test_missing_current(self):
        x = valid()
        x["current_issue_url"] = ""
        self.assertIn("CURRENT_ISSUE_INVALID", validate(x, expected()))

    def test_changed_purpose(self):
        x = valid()
        x["report"] = x["report"].replace(PURPOSE, "A different purpose")
        self.assertIn("PROJECT_PURPOSE_CHANGED", validate(x, expected()))

    def test_invalid_order(self):
        x = valid()
        x["report"] = x["report"].replace("## 作業目的", "## NEXT")
        self.assertIn("REPORT_ORDER_INVALID", validate(x, expected()))

    def test_no_current_marker(self):
        x = valid()
        x["report"] = x["report"].replace("➔今ここ", "elsewhere")
        self.assertIn("CURRENT_POSITION_MISSING", validate(x, expected()))

    def test_premature_stop(self):
        x = valid()
        x["turn_continuation"] = "INCOMPLETE"
        self.assertIn("TURN_PREMATURELY_STOPPED", validate(x, expected()))

    def test_missing_trusted_expected(self):
        self.assertIn("TRUSTED_EXPECTATIONS_MISSING", validate(valid()))

    def test_self_declared_expected_is_ignored(self):
        x = valid()
        x["rule_revision"] = "stale"
        x["expected_rule_revision"] = "stale"
        self.assertIn("RULE_STALE_OR_MISMATCH", validate(x, expected()))

    def test_wrong_canonical_in_metadata(self):
        x = valid()
        x["project_purpose_canonical"] = "new invented project goal"
        x["report"] = x["report"].replace(PURPOSE, "new invented project goal")
        self.assertIn("CANONICAL_PURPOSE_MISMATCH", validate(x, expected()))

    def test_current_url_source_mismatch(self):
        x = valid()
        x["current_issue_url"] = "https://github.com/G-ACE-inc/server-core/issues/17"
        self.assertIn("CURRENT_SOURCE_MISMATCH", validate(x, expected()))

    def test_empty_receipt(self):
        self.assertTrue(validate({}, expected()))


if __name__ == "__main__":
    unittest.main()
