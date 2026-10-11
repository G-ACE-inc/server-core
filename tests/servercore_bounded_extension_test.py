import importlib.util
import json
import os
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import servercore_bounded_host as bh  # noqa: E402
import servercore_bounded_host_receiver as receiver  # noqa: E402
import servercore_bounded_host_gateway_send as sender  # noqa: E402

spec = importlib.util.spec_from_file_location("servercore_docker_logs_socket", ROOT / "scripts" / "servercore_docker_logs_socket.py")
logs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logs)

CONTRACT = json.loads((ROOT / "operations" / "github-project-bounded-host.json").read_text())
RID = "req_" + "0123456789abcdef01234567"


def make_repo(tmp):
    root = Path(tmp)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run(["git", "init", "-q", str(root)], check=True, env=env)
    (root / "README.md").write_text("hello\n" + "x" * 3000 + "\ntoken=abc\n")
    (root / "docs").mkdir()
    (root / "docs" / "N.md").write_text("n")
    (root / "secret.txt").write_text("not registered")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "i"], check=True, env=env)
    sha = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    return root.resolve(), sha


class ContractTests(unittest.TestCase):
    def test_registered_files_exist_and_registry_is_excluded(self):
        files = CONTRACT["registered_files"]
        self.assertEqual(len(files), len(set(files)))
        for rel in files:
            self.assertTrue((ROOT / rel).is_file(), rel)
            self.assertNotIn("..", rel)
            self.assertFalse(rel.startswith("/"))
        self.assertNotIn("operations/master-internal-repositories.json", files)

    def test_new_commands_are_read_only_and_log_containers_are_server_core_owned(self):
        for command in ("project.file_inspect", "docker.logs"):
            self.assertIn(command, CONTRACT["allowed_command_ids"])
            self.assertEqual(CONTRACT["command_effects"][command], "read_only")
        self.assertEqual(CONTRACT["registered_log_containers"], ["server-core-bounded-host"])
        self.assertEqual(CONTRACT["result_return"]["stream_limit_chars"], 4000)


class FileInspectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root, self.sha = make_repo(self.tmp.name)

    def test_chunked_read_with_next_offset(self):
        first = bh.file_inspect(self.root, self.sha, "README.md", 0, ["README.md"])
        self.assertEqual(first["source_sha"], self.sha)
        self.assertEqual(first["next_offset"], bh.FILE_CHUNK_BYTES)
        second = bh.file_inspect(self.root, self.sha, "README.md", first["next_offset"], ["README.md"])
        self.assertIsNone(second["next_offset"])
        self.assertIn("token=abc", second["content"])

    def test_denials(self):
        reg = ["README.md"]
        for rel in ("secret.txt", "../x", "docs/../README.md", "/etc/passwd", "docs", None):
            with self.assertRaisesRegex(bh.BoundaryError, "FILE_NOT_REGISTERED"):
                bh.file_inspect(self.root, self.sha, rel, 0, reg)
        with self.assertRaisesRegex(bh.BoundaryError, "FILE_OFFSET_INVALID"):
            bh.file_inspect(self.root, self.sha, "README.md", -1, reg)
        with self.assertRaisesRegex(bh.BoundaryError, "SOURCE_SHA_MISMATCH"):
            bh.file_inspect(self.root, "b" * 40, "README.md", 0, reg)

    def test_symlink_denied(self):
        (self.root / "link.md").symlink_to(self.root / "secret.txt")
        with self.assertRaisesRegex(bh.BoundaryError, "FILE_MISSING"):
            bh.file_inspect(self.root, self.sha, "link.md", 0, ["link.md"])
        (self.root / "dirlink").symlink_to(self.root / "docs")
        with self.assertRaises(bh.BoundaryError):
            bh.file_inspect(self.root, self.sha, "dirlink/N.md", 0, ["dirlink/N.md"])


class RequestShapeTests(unittest.TestCase):
    def base(self, **kw):
        value = {"schema": CONTRACT["request_schema"], "id": RID, "command_id": "project.file_inspect",
                 "expected_sha": "a" * 40, "path": "README.md", "offset": 0}
        value.update(kw)
        return value

    def test_receiver_file_and_logs_shapes(self):
        self.assertEqual(receiver.validate_request(self.base(), CONTRACT)["path"], "README.md")
        for bad in (self.base(path="../x"), self.base(offset=-1), self.base(offset="0"), self.base(extra=1)):
            with self.assertRaises(receiver.ReceiverError):
                receiver.validate_request(bad, CONTRACT)
        logs_req = {"schema": CONTRACT["request_schema"], "id": RID, "command_id": "docker.logs",
                    "expected_sha": "a" * 40, "container": "server-core-bounded-host", "tail": 20}
        self.assertEqual(receiver.validate_request(logs_req, CONTRACT)["tail"], 20)
        for bad in ({**logs_req, "tail": 0}, {**logs_req, "tail": 201}, {**logs_req, "container": "a b"},
                    {**logs_req, "container": "x;y"}, {**logs_req, "tail": True}):
            with self.assertRaises(receiver.ReceiverError):
                receiver.validate_request(bad, CONTRACT)

    def test_sender_requires_exact_targets(self):
        ok = sender.validate_cli("project.file_inspect", "a" * 40, CONTRACT, path="README.md", offset=0)
        self.assertEqual((ok["path"], ok["offset"]), ("README.md", 0))
        with self.assertRaisesRegex(sender.SendError, "FILE_INSPECT_TARGET_INVALID"):
            sender.validate_cli("project.file_inspect", "a" * 40, CONTRACT, path="../x", offset=0)
        with self.assertRaisesRegex(sender.SendError, "UNEXPECTED_FILE_TARGET"):
            sender.validate_cli("project.git_head", "a" * 40, CONTRACT, path="README.md", offset=0)
        ok = sender.validate_cli("docker.logs", "a" * 40, CONTRACT, container="server-core-bounded-host", tail=50)
        self.assertEqual(ok["tail"], 50)
        with self.assertRaisesRegex(sender.SendError, "DOCKER_LOGS_TARGET_INVALID"):
            sender.validate_cli("docker.logs", "a" * 40, CONTRACT, container="c", tail=999)
        with self.assertRaisesRegex(sender.SendError, "UNEXPECTED_LOG_TARGET"):
            sender.validate_cli("project.git_head", "a" * 40, CONTRACT, container="c", tail=5)


class DockerLogsWriterTests(unittest.TestCase):
    def test_authority_is_the_contract_and_requests_are_exact(self):
        registered = frozenset(["server-core-bounded-host"])
        good = {"schema": logs.SCHEMA, "id": RID, "container": "server-core-bounded-host", "tail": 10}
        self.assertEqual(logs.validate(good, registered)["tail"], 10)
        for bad in ({**good, "container": "webhook-gateway-api-1"}, {**good, "tail": 0}, {**good, "tail": 201},
                    {**good, "extra": 1}, {**good, "id": "x"}, {**good, "schema": "y"}):
            with self.assertRaises(logs.LogsError):
                logs.validate(bad, registered)

    def test_registered_containers_from_contract_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            op = Path(tmp) / "operations"
            op.mkdir()
            (op / "github-project-bounded-host.json").write_text(json.dumps({"registered_log_containers": ["a-1", "b_2"]}))
            self.assertEqual(logs.registered_containers(Path(tmp)), frozenset(["a-1", "b_2"]))
            (op / "github-project-bounded-host.json").write_text(json.dumps({"registered_log_containers": ["a b"]}))
            with self.assertRaises(logs.LogsError):
                logs.registered_containers(Path(tmp))

    def test_fixed_argv_and_bounds(self):
        seen = {}

        class Done:
            returncode = 0
            stdout = "x" * 20000
            stderr = "err"

        def runner(argv, **kw):
            seen["argv"] = argv
            return Done()

        out = logs.read_logs({"container": "server-core-bounded-host", "tail": 7}, runner=runner, binary="/usr/bin/docker")
        self.assertEqual(seen["argv"], ["/usr/bin/docker", "logs", "--tail", "7", "--timestamps", "server-core-bounded-host"])
        self.assertTrue(out["truncated"])
        self.assertEqual(len(out["logs"]), logs.MAX_LOG_CHARS)

    def test_docker_failure_is_reported_not_leaked(self):
        class Bad:
            returncode = 1
            stdout = ""
            stderr = "secret detail"
        with self.assertRaisesRegex(logs.LogsError, "^DOCKER_LOGS_FAILED$"):
            logs.read_logs({"container": "c", "tail": 1}, runner=lambda *a, **k: Bad(), binary="/usr/bin/docker")


class ReceiverDockerLogsDispatchTests(unittest.TestCase):
    def serve(self, replies):
        tmp = tempfile.mkdtemp(prefix="gl")
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", tmp]))
        path = str(Path(tmp) / "s.sock")

        class H(socketserver.StreamRequestHandler):
            def handle(self_inner):
                self_inner.rfile.readline()
                self_inner.wfile.write((json.dumps(replies.pop(0)) + "\n").encode())

        server = socketserver.ThreadingUnixStreamServer(path, H)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return path

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root, self.sha = make_repo(self.tmp.name)
        self.request = {"id": RID, "command_id": "docker.logs", "expected_sha": self.sha,
                        "container": "server-core-bounded-host", "tail": 5}

    def test_success_returns_host_sha_and_logs(self):
        path = self.serve([{"ok": True, "request_id": RID, "container": "server-core-bounded-host", "tail": 5,
                            "logs": "line", "truncated": False}])
        result = receiver.dispatch_docker_logs(self.request, self.root, path)
        self.assertEqual((result["source_sha"], result["logs"], result["read_only"]), (self.sha, "line", True))

    def test_denial_is_terminal_and_execution_failure_is_retryable(self):
        path = self.serve([{"ok": False, "error": "CONTAINER_NOT_REGISTERED"}])
        with self.assertRaises(receiver.ReceiverError) as ctx:
            receiver.dispatch_docker_logs(self.request, self.root, path)
        self.assertEqual(ctx.exception.status, 422)
        path = self.serve([{"ok": False, "error": "DOCKER_LOGS_FAILED"}])
        with self.assertRaises(receiver.ReceiverError) as ctx:
            receiver.dispatch_docker_logs(self.request, self.root, path)
        self.assertEqual(ctx.exception.status, 503)

    def test_unavailable_socket_and_sha_mismatch_fail_closed(self):
        with self.assertRaises(receiver.ReceiverError) as ctx:
            receiver.dispatch_docker_logs(self.request, self.root, "/nonexistent/s.sock")
        self.assertEqual(ctx.exception.status, 503)
        with self.assertRaises(bh.BoundaryError):
            receiver.dispatch_docker_logs({**self.request, "expected_sha": "b" * 40}, self.root, "/nonexistent/s.sock")

    def test_result_mismatch_rejected(self):
        path = self.serve([{"ok": True, "request_id": "req_" + "f" * 24, "container": "server-core-bounded-host",
                            "tail": 5, "logs": "", "truncated": False}])
        with self.assertRaises(receiver.ReceiverError):
            receiver.dispatch_docker_logs(self.request, self.root, path)


if __name__ == "__main__":
    unittest.main()
