import json
import unittest
from types import SimpleNamespace
from scripts.chat_notion_cu_context import readback_issue
CU = "https://github.com/G-ACE-inc/server-core/issues/40"

class FreshReadbackTests(unittest.TestCase):
    def test_actual_api_endpoint_and_matching_issue(self):
        calls = []
        def runner(argv, **kwargs):
            calls.append(argv)
            return SimpleNamespace(stdout=json.dumps({"html_url": CU, "state":"open", "updated_at":"2026-10-16T00:00:00Z"}))
        got = readback_issue(CU, runner)
        self.assertEqual(calls[0][-1], "repos/G-ACE-inc/server-core/issues/40")
        self.assertEqual(got["url"],CU)
    def test_wrong_issue_rejected(self):
        def runner(argv, **kwargs):
            return SimpleNamespace(stdout=json.dumps({"html_url": "https://github.com/example/example/issues/1"}))
        with self.assertRaisesRegex(ValueError,"GITHUB_CURRENT_MISMATCH"):
            readback_issue(CU,runner)
    def test_pr_not_issue(self):
        def runner(argv, **kwargs):
            return SimpleNamespace(stdout=json.dumps({"html_url": CU, "pull_request":{}}))
        with self.assertRaisesRegex(ValueError,"GITHUB_CURRENT_MISMATCH"):
            readback_issue(CU,runner)

if __name__ == "__main__":
    unittest.main()
