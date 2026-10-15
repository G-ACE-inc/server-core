import unittest
import json
from scripts.chat_notion_comment_adapter import parse_comments
from scripts.chat_notion_cu_context import build
CU = "https://github.com/G-ACE-inc/server-core/issues/40"
class AdapterTests(unittest.TestCase):
    def test_realistic_discussion(self):
        xml = '<discussions><discussion><comment url="https://app.notion.com/p/abc" id="1">Decision references '+CU+' but source state is unverified</comment><comment url="https://app.notion.com/p/def">unrelated</comment></discussion></discussions>'
        rows = parse_comments({"text":xml}, CU)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["state"], "UNKNOWN")
        self.assertEqual(build(CU,rows,CU)["count"],1)
    def test_json_wrapped_connector_result(self):
        xml = '<discussions><comment url="https://app.notion.com/p/abc" id="a">'+CU+'</comment></discussions>'
        self.assertEqual(len(parse_comments({"text":json.dumps({"text":xml})},CU)),1)
    def test_reject_wrong_root(self):
        with self.assertRaises(ValueError):
            parse_comments({"text":"<html/>"},CU)
if __name__ == "__main__":
    unittest.main()
