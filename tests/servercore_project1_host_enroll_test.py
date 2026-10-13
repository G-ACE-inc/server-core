"""Verify protected multi-repo enrollment boundaries; no actual Host mutation."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / "scripts/servercore_project1_host_enroll.py"
spec = importlib.util.spec_from_file_location("project1_host_enroll", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Project1HostEnrollmentTests(unittest.TestCase):
    def test_exact_verified_server_git_roots(self):
        self.assertEqual(m.NEW, {
            "seigo-gace/astera_v8": "/home/admin1/projects/astera_v8",
            "seigo-gace/astera-app": "/home/admin1/projects/astera-app",
            "seigo-gace/modular-catalog": "/home/admin1/projects/Catalog/modular-catalog",
            "seigo-gace/Deterministic-Japanese-Parser-MCP": "/home/admin1/projects/Deterministic-Japanese-Parser-MCP",
            "seigo-gace/Libral-Vault": "/home/admin1/projects/libral-vault",
        })
        self.assertNotIn("seigo-gace/ai-core", m.NEW)
        self.assertNotIn("seigo-gace/gace-dev-kb", m.NEW)
        self.assertEqual(len(m.EXPECTED_DIGEST), 64)

    def test_refuse_unverified_checkout(self):
        with self.assertRaisesRegex(ValueError, "CHECKOUT_NOT_READY"):
            m.verify_checkout("seigo-gace/astera_v8", "/a/path/which/does/not/exist")

if __name__ == "__main__":
    unittest.main()
