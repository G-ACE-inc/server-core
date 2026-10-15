import unittest
from scripts.chat_notion_cu_context import build
CU="https://github.com/G-ACE-inc/server-core/issues/40"
class NotionContextTests(unittest.TestCase):
    def test_accepts_relevant_decision_and_rejects_unrelated(self):
        rows=[{"cu_url":CU,"kind":"ALTERNATIVE","state":"REJECTED","notion_url":"https://notion.so/a","summary":"Reject duplicate Current"}, {"cu_url":"https://github.com/x/y/issues/3","kind":"DECISION","notion_url":"https://notion.so/b","summary":"unrelated"}]
        got=build(CU,rows,CU)
        self.assertEqual(got["count"],1)
        self.assertEqual(got["records"][0]["state"],"REJECTED")
    def test_refuses_divergent_authority(self):
        with self.assertRaisesRegex(ValueError,"GITHUB_CURRENT_REQUIRED"):
            build(CU,[], "https://github.com/x/y/issues/1")
    def test_no_fabricated_completeness(self):
        self.assertEqual(build(CU,[],CU)["coverage"],"PARTIAL_RETRIEVED_RECORDS_ONLY")
if __name__=="__main__":
    unittest.main()
