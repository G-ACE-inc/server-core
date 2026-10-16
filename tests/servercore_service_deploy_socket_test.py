import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("service_deploy_socket", SCRIPTS / "servercore_service_deploy_socket.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

SHA = "a" * 40
REQ = {"schema": m.DEPLOY_SCHEMA, "id": "req_" + "1" * 24, "repository": "seigo-gace/webhook-gateway",
       "service": "api", "target_sha": SHA}
ENTRY = {"repository": "seigo-gace/webhook-gateway", "server_project_path": "/home/admin1/projects/webhook-gateway",
         "runtime_target": {"compose_file": "docker-compose.yml", "compose_digest": "b" * 64,
                            "health_url": "http://127.0.0.1:7373/healthz"}}
REGISTRY = {"repositories": [ENTRY]}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name) / "results"
        self.registry = Path(self.tmp.name) / "registry.json"
        self.registry.write_text(json.dumps(REGISTRY))
        self.lock = Path(self.tmp.name) / "lock"

    def accept(self, request=REQ, threaded=False):
        return m.accept_request(request, registry_path=self.registry, lock_path=self.lock,
                                result_dir=self.dir, threaded=threaded)


class PreflightAttestationTests(unittest.TestCase):
    def test_original_stdout_is_lossless_and_cannot_spoof_a_preflight_failure(self):
        clean, failed = m.attest_source_preflight(
            m.SOURCE_PREFLIGHT_OK + "日本語Ω🙂\n", "", 0, True)
        self.assertEqual(clean, "日本語Ω🙂\n")
        self.assertFalse(failed)
        clean, failed = m.attest_source_preflight(
            m.SOURCE_PREFLIGHT_OK,
            "CHAT_SOURCE_SHA_MISMATCH\n", 74, True)
        self.assertEqual(clean, "")
        self.assertFalse(failed)

    def test_actual_preflight_failure_and_regular_unbound_error(self):
        clean, failed = m.attest_source_preflight(
            "", "CHAT_SOURCE_SHA_MISMATCH\n", 74, True)
        self.assertEqual(clean, "")
        self.assertTrue(failed)
        self.assertFalse(m.attest_source_preflight(
            "", "CHAT_SOURCE_SHA_MISMATCH\n", 74, False)[1])
        self.assertFalse(m.attest_source_preflight(
            "some output", "CHAT_SOURCE_SHA_MISMATCH\n", 74, True)[1])


class ValidationTests(unittest.TestCase):
    def test_rejects_extra_keys_shell_and_wildcards(self):
        with self.assertRaisesRegex(m.AdmissionError, "REQUEST_KEYS_DENIED"):
            m.validate({**REQ, "shell": "docker run --privileged"})
        for bad in ("../x", "api;rm", "", "API", "*"):
            with self.assertRaisesRegex(m.AdmissionError, "SERVICE_INVALID"):
                m.validate({**REQ, "service": bad})
        with self.assertRaisesRegex(m.AdmissionError, "TARGET_SHA_INVALID"):
            m.validate({**REQ, "target_sha": "main"})
        with self.assertRaisesRegex(m.AdmissionError, "REPOSITORY_INVALID"):
            m.validate({**REQ, "repository": "../../etc"})
        with self.assertRaisesRegex(m.AdmissionError, "REQUEST_ID_DENIED"):
            m.validate({**REQ, "id": "req_free"})

    def test_fixed_socket_only(self):
        with self.assertRaisesRegex(m.AdmissionError, "SOCKET_PATH_DENIED"):
            m.serve("/tmp/open-deploy.sock")

    def test_status_keys(self):
        with self.assertRaisesRegex(m.AdmissionError, "STATUS_KEYS_DENIED"):
            m.validate_status({"schema": m.STATUS_SCHEMA, "id": REQ["id"], "extra": 1})


class AcceptTests(Fixture):
    def test_admission_denial_creates_no_result_and_no_mutation(self):
        with patch.object(m, "deploy", side_effect=m.DeployAdmissionError("SERVICE_NOT_REGISTERED")) as run:
            with self.assertRaises(m.DeployAdmissionError):
                self.accept()
        self.assertEqual(run.call_count, 1)  # dry-run only, never apply
        self.assertIsNone(m.read_result(REQ["id"], self.dir))

    def test_pass_records_before_after_and_recreated(self):
        ids = iter([{"container_id": "c" * 12, "created_image": "t1|i1"},
                    {"container_id": "d" * 12, "created_image": "t2|i2"}])
        with patch.object(m, "deploy", return_value={"state": "SERVICE_DEPLOY_RUNTIME_RUNNING",
                                                       "container_id": "d" * 12, "health": "healthy"}) as run, \
             patch.object(m, "runtime_identity", side_effect=lambda *a: next(ids)), \
             patch.object(m, "http_health", return_value="HTTP_200"):
            self.assertEqual(self.accept()["state"], "SERVICE_DEPLOY_ACCEPTED")
        applies = [c for c in run.call_args_list if c.kwargs.get("apply")]
        self.assertEqual(len(applies), 1)
        result = m.read_result(REQ["id"], self.dir)
        self.assertEqual(result["state"], "SERVICE_DEPLOY_PASS")
        self.assertTrue(result["recreated"])
        self.assertEqual(result["http_health"], "HTTP_200")
        self.assertEqual(result["compose_digest"], "b" * 64)

    def test_unchanged_identity_is_not_reported_as_recreated(self):
        same = {"container_id": "c" * 12, "created_image": "t1|i1"}
        with patch.object(m, "deploy", return_value={"state": "x"}), \
             patch.object(m, "runtime_identity", return_value=same), \
             patch.object(m, "http_health", return_value="HTTP_200"):
            self.accept()
        self.assertFalse(m.read_result(REQ["id"], self.dir)["recreated"])

    def test_http_health_failure_is_recorded_fail_closed(self):
        with patch.object(m, "deploy", return_value={"state": "x"}), \
             patch.object(m, "runtime_identity", return_value=None), \
             patch.object(m, "http_health", return_value="UNREACHABLE"):
            self.accept()
        result = m.read_result(REQ["id"], self.dir)
        self.assertEqual(result["state"], "FAIL")
        self.assertEqual(result["failure_class"], "SERVICE_HTTP_HEALTH_NOT_READY")

    def test_duplicate_request_id_never_redeploys(self):
        with patch.object(m, "deploy", return_value={"state": "x"}) as run, \
             patch.object(m, "runtime_identity", return_value=None), \
             patch.object(m, "http_health", return_value="HTTP_200"):
            self.accept()
            calls = run.call_count
            again = self.accept()
        self.assertEqual(again["state"], "SERVICE_DEPLOY_DUPLICATE")
        self.assertEqual(run.call_count, calls)

    def test_status_readback_and_unknown(self):
        with patch.object(m, "deploy", return_value={"state": "x"}), \
             patch.object(m, "runtime_identity", return_value=None), \
             patch.object(m, "http_health", return_value="HTTP_200"):
            self.accept()
        status = m.status_request({"schema": m.STATUS_SCHEMA, "id": REQ["id"]}, result_dir=self.dir)
        self.assertEqual(status["state"], "SERVICE_DEPLOY_PASS")
        with self.assertRaisesRegex(m.AdmissionError, "DEPLOY_REQUEST_UNKNOWN"):
            m.status_request({"schema": m.STATUS_SCHEMA, "id": "req_" + "2" * 24}, result_dir=self.dir)

    def test_lock_busy_is_rejected_without_result(self):
        import fcntl
        import os
        fd = os.open(self.lock, os.O_WRONLY | os.O_CREAT, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        self.addCleanup(os.close, fd)
        with patch.object(m, "deploy", return_value={"state": "x"}):
            with self.assertRaises(BlockingIOError):
                self.accept()
        self.assertIsNone(m.read_result(REQ["id"], self.dir))



class HostCommandUmaskTests(unittest.TestCase):
    def test_socket_umask_does_not_mask_host_child_directories(self):
        import subprocess
        from unittest.mock import patch
        # Verify the child shell behavior without touching another repository.
        with tempfile.TemporaryDirectory() as directory:
            child = Path(directory) / "created"
            script = "umask 0117; umask 0022; mkdir " + str(child)
            subprocess.run(["/bin/bash", "-lc", script], check=True)
            self.assertEqual(child.stat().st_mode & 0o777, 0o755)
        source = (SCRIPTS / "servercore_service_deploy_socket.py").read_text()
        self.assertIn('"umask 0022; " + command_text', source)
        self.assertIn("old = os.umask(0o117)", source)

if __name__ == "__main__":
    unittest.main()
