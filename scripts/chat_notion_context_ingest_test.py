import unittest
from scripts.chat_notion_context_ingest import ingest
from scripts.chat_notion_cu_context import build
CU = "https://github.com/G-ACE-inc/server-core/issues/40"
class IntegrationTests(unittest.TestCase):
    def test_real_notional_comments_are_consumable(self):
        payload={"text":'{"text":"<discussions><discussion><comment id=\\"a\\" url=\\"https://app.notion.com/p/abc\\">'+CU+'</comment></discussion></discussions>"}'}
        rows=ingest(payload,CU)
        got=build(CU,rows,CU)
        self.assertEqual(got["count"],1)
        self.assertEqual(got["records"][0]["state"],"UNKNOWN")
    def test_notion_search_is_not_fake_decision_history(self):
        self.assertEqual(ingest({"structuredContent":{"results":[{"id":"x"}]}},CU),[])
    def test_formatted_records_pass_through(self):
        self.assertEqual(ingest([],CU),[])
if __name__=="__main__":
    unittest.main()
