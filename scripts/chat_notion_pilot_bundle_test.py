import unittest
from scripts.chat_notion_context_ingest import ingest
from scripts.chat_notion_cu_context import build

CU = "https://github.com/G-ACE-inc/server-core/issues/40"
PAGE = "https://app.notion.com/p/3facdcf128e4816793c7c611228e9dad"

class BundleTests(unittest.TestCase):
    def test_two_actual_source_shapes_one_cu(self):
        page = {"structuredContent":{"text":'<page url="'+PAGE+'"><content>Design evidence '+CU+'</content></page>'}}
        comments = {"text":'<discussions><comment id="one" url="'+PAGE+'">'+CU+' discussed</comment></discussions>'}
        bundle = {"sources":[{"type":"page","page_url":PAGE,"response":page},
                             {"type":"comments","response":comments}]}
        records = ingest(bundle, CU)
        self.assertEqual(len(records), 2)
        self.assertEqual(build(CU,records,CU)["count"],2)
        self.assertTrue(all(item["state"]=="UNKNOWN" for item in records))
    def test_unrelated_data_does_not_become_decision(self):
        page = {"structuredContent":{"text":'<page url="'+PAGE+'"><content>unrelated</content></page>'}}
        self.assertEqual(ingest({"sources":[{"type":"page","page_url":PAGE,"response":page}]}, CU),[])
    def test_unbounded_sources_fail(self):
        with self.assertRaisesRegex(ValueError, "NOTION_SOURCES_TOO_MANY"):
            ingest({"sources":[{"type":"comments","response":{}}]*21}, CU)
    def test_mismatched_page_provenance_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"PAGE_SOURCE_MISMATCH"):
            ingest({"sources":[{"type":"page","page_url":PAGE,
                                 "response":'<page url="https://app.notion.com/p/other"><content>'+CU+'</content></page>'}]}, CU)

if __name__ == "__main__":
    unittest.main()
