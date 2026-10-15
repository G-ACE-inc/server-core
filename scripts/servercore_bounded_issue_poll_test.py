"""Issue poll must stay bounded even after thousands of comments."""
import json
import unittest
from unittest.mock import patch
from scripts import servercore_bounded_result_poll as poll


class FakeResult:
    def __init__(self, content):
        self.returncode = 0
        self.stdout = json.dumps(content)


class BoundedIssuePollTests(unittest.TestCase):
    def test_reads_only_latest_two_pages(self):
        calls = []
        def fake_run(argv, **kwargs):
            calls.append(argv[-1])
            if "/comments?" not in argv[-1]:
                return FakeResult({"comments": 9876})
            return FakeResult([{"body": argv[-1]}])
        with patch.object(poll.subprocess, "run", side_effect=fake_run):
            result = poll.gh_api("repos/G-ACE-inc/server-core/issues/10/comments?per_page=100&since=now")
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[1].endswith("page=98"))
        self.assertTrue(calls[2].endswith("page=99"))
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
