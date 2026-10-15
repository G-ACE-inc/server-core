#!/usr/bin/env python3
"""Bounded Issue polling regression: no full-history pagination."""
import importlib.util
import json
import pathlib
import subprocess
import unittest
from unittest.mock import patch

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts/servercore_bounded_result_poll.py"
spec = importlib.util.spec_from_file_location("servercore_bounded_result_poll", SCRIPT)
poll = importlib.util.module_from_spec(spec)
spec.loader.exec_module(poll)


class ResultTailTest(unittest.TestCase):
    def test_only_latest_issue_comments_queried(self):
        observed = []
        def fake_run(argv, **kwargs):
            observed.extend(argv)
            return subprocess.CompletedProcess(argv, 0, json.dumps({
                "data": {"repository": {"issue": {"comments": {"nodes": [
                    {"body": "<!-- GACE_BOUNDED_HOST_RESULT request_id=req_" + "a"*24 + " -->", "url": "https://github.com/example#issuecomment-7"}
                ]}}}}
            }), "")
        with patch.object(poll.subprocess, "run", fake_run):
            values = poll.gh_api("repos/G-ACE-inc/server-core/issues/10/comments?per_page=100&since=2026-10-15T00:00:00Z")
        self.assertEqual(observed[:3], ["gh", "api", "graphql"])
        self.assertNotIn("--paginate", observed)
        self.assertIn("comments(last:100)", " ".join(observed))
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["html_url"], "https://github.com/example#issuecomment-7")

    def test_invalid_path_does_not_query(self):
        with patch.object(poll.subprocess, "run") as run:
            with self.assertRaises(RuntimeError):
                poll.gh_api("repos/test/other")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
