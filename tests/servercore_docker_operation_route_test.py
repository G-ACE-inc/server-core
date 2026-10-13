"""Regression coverage for the existing CHAT → Host registered Docker operation lane."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

writer = load("servercore_service_deploy_socket")
receiver = load("servercore_bounded_host_receiver")
sender = load("servercore_bounded_host_gateway_send")
SHA = "a"*40
REPO = "seigo-gace/debug-ai"
SESSION = "req_" + "1"*24
REQUEST = {
    "schema": writer.DOCKER_OP_SCHEMA, "id": SESSION, "repository": REPO,
    "service": "debug-ai", "target_sha": SHA, "operation": "restart",
    "argv": [], "tail": 100
}
CONTRACT = {"request_schema": "gace.servercore-bounded-host.request/v1",
            "allowed_command_ids": ["docker.operation"]}

class DockerRouteTests(unittest.TestCase):
    def test_writer_validates_exact_request(self):
        self.assertEqual(writer.validate_docker_operation(REQUEST), REQUEST)
        with self.assertRaisesRegex(writer.AdmissionError, "KEYS"):
            writer.validate_docker_operation({**REQUEST, "shell": "docker rm -f everything"})
        with self.assertRaisesRegex(writer.AdmissionError, "OPERATION_DENIED"):
            writer.validate_docker_operation({**REQUEST, "operation": "down"})
        with self.assertRaisesRegex(writer.AdmissionError, "EXEC_ARGS_DENIED"):
            writer.validate_docker_operation({**REQUEST, "operation": "exec"})
        with self.assertRaisesRegex(writer.AdmissionError, "TAIL_INVALID"):
            writer.validate_docker_operation({**REQUEST, "tail": 0})

    def test_sender_gateway_payload_and_rejections(self):
        record = sender.validate_cli("docker.operation", SHA, CONTRACT,
                                     repository=REPO, service="debug-ai",
                                     argv=["python3", "-V"], tail=100,
                                     docker_operation="exec")
        self.assertEqual(record["operation"], "exec")
        self.assertEqual(record["argv"], ["python3", "-V"])
        self.assertEqual(record["repository"], REPO)
        with self.assertRaisesRegex(sender.SendError, "DOCKER_OPERATION_INVALID"):
            sender.validate_cli("docker.operation", SHA, CONTRACT, repository=REPO,
                                service="debug-ai", argv=[], docker_operation="rm")
        with self.assertRaisesRegex(sender.SendError, "TARGET_INVALID"):
            sender.validate_cli("docker.operation", SHA, CONTRACT, repository="../../root",
                                service="debug-ai", argv=[], docker_operation="ps")

    def test_receiver_schema_and_no_unregistered_operation(self):
        payload = {
            "schema": CONTRACT["request_schema"], "id": SESSION,
            "command_id": "docker.operation", "expected_sha": SHA,
            "repository": REPO, "service": "debug-ai",
            "operation": "restart", "argv": [], "tail": 100,
        }
        self.assertEqual(receiver.validate_request(payload, CONTRACT)["operation"], "restart")
        with self.assertRaisesRegex(receiver.ReceiverError, "UNSUPPORTED"):
            receiver.validate_request({**payload, "operation": "down"}, CONTRACT)
        with self.assertRaisesRegex(receiver.ReceiverError, "KEYS_INVALID"):
            receiver.validate_request({**payload, "docker_socket": "/var/run/docker.sock"}, CONTRACT)

    def test_writer_idempotent_registered_operation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            registry.write_text(json.dumps({"repositories": [{
                "repository": REPO, "server_project_path": "/home/admin1/projects/debug-ai",
                "runtime_target": {"compose_file": "compose.yaml", "services": ["debug-ai"]}
            }]}))
            lock, result_dir = root / "lock", root / "results"
            with patch.object(writer, "require_registered", return_value={}), \
                 patch.object(writer, "check_registered_compose_path", return_value=None), \
                 patch.object(writer, "operate", return_value={
                     "service": "debug-ai", "operation": "restart", "exit_code": 0,
                     "stdout": "ok", "stderr": ""
                 }) as operation:
                first = writer.run_docker_operation(REQUEST, registry_path=registry,
                                                    lock_path=lock, result_dir=result_dir)
                second = writer.run_docker_operation(REQUEST, registry_path=registry,
                                                     lock_path=lock, result_dir=result_dir)
            self.assertEqual(first["state"], "DOCKER_OPERATION_PASS")
            self.assertEqual(second["state"], "DOCKER_OPERATION_DUPLICATE")
            self.assertEqual(operation.call_count, 1)
            self.assertEqual(writer.read_result(SESSION, result_dir)["state"], "DOCKER_OPERATION_PASS")

    def test_writer_admission_denied_before_docker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            registry.write_text(json.dumps({"repositories": []}))
            with patch.object(writer, "require_registered",
                              side_effect=writer.DeployAdmissionError("SERVICE_NOT_REGISTERED")), \
                 patch.object(writer, "operate") as operation:
                with self.assertRaises(writer.DeployAdmissionError):
                    writer.run_docker_operation(REQUEST, registry_path=registry,
                                                lock_path=root/"lock", result_dir=root/"result")
                operation.assert_not_called()

    def test_registered_compose_digest_and_path_rechecked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            compose = root / "compose.yaml"
            compose.write_text("services: {}\\n")
            admitted = {"root": str(root), "compose_file": "compose.yaml",
                        "compose_digest": hashlib.sha256(compose.read_bytes()).hexdigest()}
            self.assertEqual(writer.check_registered_compose_path(admitted), root)
            compose.write_text("services: {other: {}}\\n")
            with self.assertRaisesRegex(writer.AdmissionError, "DOCKER_COMPOSE_DIGEST_CHANGED"):
                writer.check_registered_compose_path(admitted)

    def test_receiver_requires_correlated_host_receipt(self):
        request = {
            "id": SESSION, "command_id": "docker.operation",
            "expected_sha": SHA, "repository": REPO,
            "service": "debug-ai", "operation": "ps", "argv": [], "tail": 100
        }
        reply = {
            "ok": True, "request_id": SESSION, "state": "DOCKER_OPERATION_PASS",
            "repository": REPO, "service": "debug-ai", "operation": "ps",
            "source_sha": SHA, "stdout": "running", "stderr": "", "exit_code": 0
        }
        with patch.object(receiver.bounded_host, "checked_root", return_value=Path("/x")), \
             patch.object(receiver.bounded_host, "head_sha", return_value=SHA), \
             patch.object(receiver, "deploy_socket_call", return_value=reply):
            result = receiver.dispatch_docker_operation(request, Path("/x"))
        self.assertEqual(result["stdout"], "running")
        self.assertTrue(result["read_only"])

if __name__ == "__main__":
    unittest.main()
