import importlib.util
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("result_local_lookup", SCRIPTS / "servercore_result_local_lookup.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

RID = "req_" + "a" * 24


class LocalResultTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "sink.sock"

    def fake_sink(self, payload):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.path))
        server.listen(1)
        self.addCleanup(server.close)
        received = []
        def handler():
            with server.accept()[0] as conn:
                incoming = b""
                while not incoming.endswith(b"\n"):
                    incoming += conn.recv(4096)
                received.append(json.loads(incoming.decode("utf-8")))
                conn.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        th = threading.Thread(target=handler, daemon=True)
        th.start()
        self.addCleanup(lambda: th.join(timeout=3))
        return received

    def test_one_request_no_reexecution_or_issue_dependency(self):
        record = {"request_id": RID, "command_id": "host.command", "state": "PASS",
                  "exit_code": 0, "host_sha": "b" * 40,
                  "recorded_at": "2026-11-12T00:00:00Z",
                  "published": None,
                  "stdout": "token=sensitive-data-do-not-return",
                  "stderr": "private"}
        received = self.fake_sink({"ok": True, "found": True, "record": record})
        result = module.lookup(RID, socket_path=self.path)
        self.assertEqual(result["state"], "PASS")
        self.assertFalse(result["published"])
        self.assertEqual(received, [{"schema": module.SCHEMA, "request_id": RID}])
        self.assertNotIn("token=", json.dumps(result))
        self.assertNotIn("private", json.dumps(result))

    def test_missing_is_not_mislabeled_success(self):
        self.fake_sink({"ok": True, "found": False, "record": None})
        self.assertEqual(module.lookup(RID, socket_path=self.path)["status"], "NOT_RECORDED")

    def test_mismatched_result_is_rejected(self):
        self.fake_sink({"ok": True, "found": True, "record": {
            "request_id": "req_" + "c" * 24, "state": "PASS", "exit_code": 0,
            "host_sha": "b" * 40}})
        with self.assertRaisesRegex(module.ResultQueryError, "SINK_RECORD_MISMATCH"):
            module.lookup(RID, socket_path=self.path)

    def test_failed_result_keeps_exit(self):
        self.fake_sink({"ok": True, "found": True, "record": {
            "request_id": RID, "state": "FAIL", "exit_code": 75, "host_sha": ""}})
        result = module.lookup(RID, socket_path=self.path)
        self.assertEqual((result["state"], result["exit_code"]), ("FAIL", 75))

    def test_bad_id_denied_before_connect(self):
        with self.assertRaisesRegex(module.ResultQueryError, "REQUEST_ID_INVALID"):
            module.lookup("../secrets", socket_path=self.path)

    def test_no_socket_denies_without_creating_service(self):
        with self.assertRaisesRegex(module.ResultQueryError, "SINK_SOCKET_UNAVAILABLE"):
            module.lookup(RID, socket_path=self.path)

    def test_invalid_host_result_is_rejected(self):
        self.fake_sink({"ok": True, "found": True, "record": {
            "request_id": RID, "state": "PASS", "exit_code": "0", "host_sha": ""}})
        with self.assertRaisesRegex(module.ResultQueryError, "SINK_RECORD_INVALID"):
            module.lookup(RID, socket_path=self.path)


if __name__ == "__main__":
    unittest.main()
