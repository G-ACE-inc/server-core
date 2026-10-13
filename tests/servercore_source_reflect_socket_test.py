import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "servercore_source_reflect_socket.py"
import sys
sys.path.insert(0, str(MODULE.parent))
spec = importlib.util.spec_from_file_location("socket_reflect", MODULE)
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)
A, B = "a" * 40, "b" * 40
REQUEST = {
    "schema": target.SCHEMA,
    "id": "req_" + "1" * 24,
    "repository": "G-ACE-inc/server-core",
    "branch": "main",
    "expected_before": A,
    "target_sha": B,
}


class SocketReflectTests(unittest.TestCase):
    def test_registered_request_calls_admitted_host(self):
        admission = {"root": Path("/home/admin1/server-core"), "branch": "main", "allowed_origins": frozenset()}
        with patch.object(target, "require_reflect", return_value=admission), \
                patch.object(target, "load_registry", return_value={}), \
                patch.object(target, "reflect", return_value={"state": "SOURCE_REFLECT_PASS"}) as run:
            result = target.execute_request(REQUEST)
        self.assertEqual(result["state"], "SOURCE_REFLECT_PASS")
        run.assert_called_once_with(admission["root"], A, B, branch="main", allowed_origins=admission["allowed_origins"])

    def test_rejects_unregistered_repo(self):
        with patch.object(target, "load_registry", return_value={"repositories": []}), \
                patch.object(target, "require_reflect", side_effect=target.ReflectAdmissionError("REFLECT_OPERATION_NOT_REGISTERED")):
            with self.assertRaises(target.ReflectAdmissionError):
                target.execute_request({**REQUEST, "repository": "seigo-gace/debug-ai"})

    def test_rejects_unregistered_branch(self):
        with patch.object(target, "load_registry", return_value={"repositories": []}), \
                patch.object(target, "require_reflect", side_effect=target.ReflectAdmissionError("BRANCH_NOT_ALLOWED")):
            with self.assertRaises(target.ReflectAdmissionError):
                target.execute_request({**REQUEST, "branch": "feature/unbounded"})

    def test_rejects_extra_keys_and_effects(self):
        with self.assertRaisesRegex(target.AdmissionError, "REQUEST_KEYS_DENIED"):
            target.validate({**REQUEST, "shell": "rm -rf /"})

    def test_rejects_symbolic_sha(self):
        with self.assertRaisesRegex(target.AdmissionError, "TARGET_SHA_INVALID"):
            target.validate({**REQUEST, "target_sha": "HEAD"})

    def test_rejects_invalid_id(self):
        with self.assertRaisesRegex(target.AdmissionError, "REQUEST_ID_DENIED"):
            target.validate({**REQUEST, "id": "req_noncanonical"})

    def test_fixed_socket_only(self):
        with self.assertRaisesRegex(target.AdmissionError, "SOCKET_PATH_DENIED"):
            target.serve("/tmp/open-executor.sock")


if __name__ == "__main__":
    unittest.main()
