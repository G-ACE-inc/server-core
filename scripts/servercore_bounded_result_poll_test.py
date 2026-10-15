#!/usr/bin/env python3
"""Regression: terminal streams must not be silently clipped by the CHAT path."""
import contextlib
import io
import unittest
from scripts import servercore_bounded_result_poll as poll


class TerminalOutputTests(unittest.TestCase):
    def test_host_observation_retains_long_streams(self):
        stdout = "START-" + "a" * 18000 + "-END"
        stderr = "ERR-" + "b" * 5000 + "-END"
        result = dict(request_id="req_" + "a" * 24, command_id="host.command",
                      state="FAIL", exit_code=1, stdout=stdout, stderr=stderr)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            poll.emit(result, {"html_url": "https://github.com/G-ACE-inc/server-core/issues/10"}, "OK")
        output = buf.getvalue()
        self.assertIn(stdout, output)
        self.assertIn(stderr, output)
        self.assertIn("CHAT_NEXT_ACTION=INSPECT_FAILURE_EVIDENCE_AND_REPLAN", output)


if __name__ == "__main__":
    unittest.main()
