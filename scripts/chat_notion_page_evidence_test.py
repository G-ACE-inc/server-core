import json
import unittest
from scripts.chat_notion_page_evidence import page_evidence
from scripts.chat_notion_context_ingest import ingest
from scripts.chat_notion_cu_context import build
CU="https://github.com/G-ACE-inc/server-core/issues/40"
PAGE="https://app.notion.com/p/3facdcf128e4816793c7c611228e9dad"
class PageEvidenceTests(unittest.TestCase):
    def test_page_to_cu_context(self):
        page={"structuredContent":{"text":'<page url="'+PAGE+'"><content>Planning and evidence '+CU+' has an adopted GitHub Source authority.</content></page>'}}
        rows=ingest(page,CU,PAGE)
        self.assertEqual(build(CU,rows,CU)["count"],1)
        self.assertEqual(rows[0]["state"],"UNKNOWN")
    def test_unrelated_page_not_attributed(self):
        self.assertEqual(page_evidence('<page url="'+PAGE+'"><content>different CU</content></page>',CU,PAGE),[])
    def test_wrong_source_page_rejected(self):
        with self.assertRaisesRegex(ValueError,"PAGE_SOURCE_MISMATCH"):
            page_evidence('<page url="https://app.notion.com/p/other"><content>'+CU+'</content></page>',CU,PAGE)
    def test_malformed_page_fails(self):
        with self.assertRaisesRegex(ValueError,"PAGE_FORMAT_INVALID"):
            page_evidence("some text",CU,PAGE)
    def test_actual_mcp_text_wrapper(self):
        actual = {"content": [{"type": "text", "text": json.dumps({
            "id": "page", "text": '<page url="'+PAGE+'" icon="x">\n<content>'+CU+'</content></page>'})}],
            "isError": False}
        self.assertEqual(ingest(actual, CU, PAGE)[0]["state"], "UNKNOWN")
    def test_rejected_tool_cannot_smuggle_valid_page(self):
        payload = {"isError": True, "structuredContent": {
            "text": '<page url="'+PAGE+'"><content>'+CU+'</content></page>'}}
        with self.assertRaisesRegex(ValueError, "NOTION_TOOL_REJECTED"):
            ingest(payload, CU, PAGE)
    def test_ambiguous_page_headers_are_not_provenance(self):
        raw = '<page url="'+PAGE+'"><page url="https://app.notion.com/p/other"><content>'+CU+'</content>'
        with self.assertRaisesRegex(ValueError, "PAGE_SOURCE_MISMATCH"):
            page_evidence(raw, CU, PAGE)
    def test_malformed_tool_block_has_fixed_failure(self):
        with self.assertRaisesRegex(ValueError, "NOTION_TOOL_CONTENT_AMBIGUOUS"):
            ingest({"content": [None]}, CU, PAGE)
    def test_wrapped_search_hits_are_only_pointers(self):
        payload = {"content": [{"type": "text", "text": json.dumps({"results": [{"id": "x"}]})}]}
        self.assertEqual(ingest(payload, CU), [])
if __name__=="__main__":
    unittest.main()
