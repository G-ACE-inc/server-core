#!/usr/bin/env python3
"""Regression: terminal streams must not be silently clipped by the CHAT path."""
import contextlib
import io
import json
import tempfile
from pathlib import Path
import unittest
from scripts import servercore_bounded_result_poll as poll


class TerminalOutputTests(unittest.TestCase):
    def test_legacy_complete_preview_fills_missing_hash_without_text_leak(self):
        import hashlib
        rid = "req_" + "e" * 24
        text = "日本語Ω🙂\\n"
        record = {"request_id": rid, "command_id": "host.command",
                  "state": "PASS", "exit_code": 0, "expected_sha": "a" * 40,
                  "stdout": text, "stderr": "",
                  "stdout_truncated": False, "stderr_truncated": False}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "observation.json")
            poll.write_observation(str(path), rid, record, {"html_url": "https://github.com/G-ACE-inc/server-core/issues/10"}, "OK")
            output = path.read_text()
            receipt = json.loads(output)
            self.assertEqual(receipt["streams"]["stdout"]["sha256"], hashlib.sha256(text.encode()).hexdigest())
            self.assertEqual(receipt["streams"]["stdout"]["chars"], len(text))
            self.assertEqual(receipt["streams"]["stderr"]["chars"], 0)
            self.assertNotIn(text, output)
        # A metadata-only publisher must NEVER hash its empty preview.
        pointer = {**record, "stdout": "", "stdout_bytes": 1000,
                   "stdout_preview_truncated": True}
        self.assertIsNone(poll.stream_receipt_metadata(pointer, "stdout")["sha256"])
        # Full-ledger source hashes are preserved even if the preview is hidden.
        pointer["stdout_sha256"] = "b" * 64
        pointer["stdout_chars"] = 777
        self.assertEqual(poll.stream_receipt_metadata(pointer, "stdout")["sha256"], "b" * 64)
        self.assertFalse(poll.stream_receipt_metadata(pointer, "stdout")["complete"])

    def test_clipped_preview_requires_lossless_chunk_readback(self):
        import contextlib
        import io
        partial = dict(request_id="req_" + "b" * 24, command_id="host.command",
                       state="PASS", exit_code=0, stdout="start",
                       stdout_preview_truncated=True, stdout_chars=9000,
                       stdout_sha256="a" * 64, stderr="")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            poll.emit(partial, {"html_url": "https://github.com/G-ACE-inc/server-core/issues/10"}, "OK")
        out = buf.getvalue()
        self.assertIn("CHAT_HOST_OBSERVATION=HOST_OUTPUT_PARTIAL", out)
        self.assertIn("CHAT_NEXT_ACTION=READ_STORED_HOST_OUTPUT_CHUNKS_AND_CONTINUE", out)
        self.assertIn("CHAT_HOST_STDOUT_COMPLETE=FALSE", out)
        self.assertIn("CHAT_HOST_STDOUT_CHARS=9000", out)
        self.assertIn("CHAT_HOST_STDOUT_SHA256=" + "a" * 64, out)

    def test_persisted_observation_is_recoverable_without_output_leak(self):
        record = dict(request_id="req_" + "c" * 24, command_id="host.command",
                      state="FAIL", exit_code=1, expected_sha="a" * 40,
                      stdout="PRIVATE_OUTPUT", stderr="PRIVATE_ERROR",
                      stdout_chars=14, stdout_sha256="b" * 64,
                      stdout_preview_truncated=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.json"
            poll.write_observation(str(path), record["request_id"], record,
                                   {"html_url": "https://github.com/G-ACE-inc/server-core/issues/10"}, "OK")
            raw = path.read_text(encoding="utf-8")
            receipt = json.loads(raw)
            self.assertEqual(receipt["next_action"], "READ_STORED_HOST_OUTPUT_CHUNKS_AND_CONTINUE")
            self.assertEqual(receipt["observation"], "HOST_OUTPUT_PARTIAL")
            self.assertFalse(receipt["streams"]["stdout"]["complete"])
            self.assertNotIn("PRIVATE_OUTPUT", raw)
            self.assertNotIn("PRIVATE_ERROR", raw)
            poll.write_observation(str(path), record["request_id"])
            self.assertFalse(json.loads(path.read_text())["result_verified"])
            self.assertEqual(json.loads(path.read_text())["observation"], "HOST_RESULT_NOT_RETURNED")

    def test_ledger_pointer_requires_payload_recovery(self):
        record = dict(request_id="req_" + "d" * 24, command_id="host.command",
                      state="PASS", exit_code=0, expected_sha="a" * 40,
                      stdout_bytes=10000, stderr_bytes=0,
                      stdout_sha256="b" * 64)
        observation, next_action = poll.continuation_observation(record, "OK")
        self.assertEqual(observation, "HOST_LEDGER_RECOVERY_REQUIRED")
        self.assertEqual(next_action, "READ_STORED_HOST_OUTPUT_CHUNKS_AND_CONTINUE")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "receipt.json"
            poll.write_observation(str(dest), record["request_id"], record,
                                   {"html_url": "https://github.com/G-ACE-inc/server-core/issues/10"}, "OK")
            receipt = json.loads(dest.read_text())
            self.assertFalse(receipt["streams"]["stdout"]["complete"])
            self.assertFalse(receipt["streams"]["stderr"]["complete"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            poll.emit(record, {"html_url": "https://github.com/G-ACE-inc/server-core/issues/10"}, "OK")
        self.assertIn("CHAT_HOST_STDOUT_COMPLETE=FALSE", buf.getvalue())
        self.assertIn("CHAT_HOST_OUTPUT_TRANSPORT=HOST_LEDGER_ONLY", buf.getvalue())

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
