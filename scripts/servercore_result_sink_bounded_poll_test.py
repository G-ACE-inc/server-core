"""Publisher must not enumerate all Issue #10 comments."""
import json
import unittest
from scripts import servercore_result_sink as sink


class PublisherLookupTest(unittest.TestCase):
    def test_only_latest_two_pages(self):
        calls = []
        def runner(args, stdin=None):
            calls.append(args)
            if "/comments?" not in args[-1]:
                return json.dumps({"comments": 9876})
            if args[-1].endswith("page=98"):
                return json.dumps([{"id": 42, "html_url": "https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-42",
                                    "body": "<!-- GACE_BOUNDED_HOST_RESULT request_id=req_" + "a"*24 + " -->"}])
            return "[]"
        result = sink.find_published("req_" + "a"*24, "2026-10-15T00:00:00Z", runner)
        self.assertEqual(result["comment_id"], 42)
        self.assertEqual(len(calls), 3)
        self.assertNotIn("--paginate", repr(calls))
        self.assertIn("page=99", calls[1][-1])
        self.assertIn("page=98", calls[2][-1])


if __name__ == "__main__":
    unittest.main()
