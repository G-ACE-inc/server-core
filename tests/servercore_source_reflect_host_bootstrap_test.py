import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "servercore_source_reflect_host_bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap", MODULE)
boot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boot)
SHA = "a" * 40


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / ".git").mkdir()
        (self.root / "scripts").mkdir()
        (self.root / "scripts/servercore_source_reflect_socket.py").write_text("# host-local\n")

    def verify(self, *, dirty=False, head=SHA, remote=None, branch="main"):
        def git(*args):
            if args == ("rev-parse", "--abbrev-ref", "HEAD"):
                return branch
            if args == ("remote", "get-url", "origin"):
                return remote or sorted(boot.APPROVED_ORIGINS)[0]
            if args == ("rev-parse", "HEAD"):
                return head
            if args == ("status", "--porcelain", "--untracked-files=all"):
                return " M operations/master-internal-repositories.json" if dirty else ""
            return ""
        with patch.object(boot, "ROOT", self.root), patch.object(boot, "git", side_effect=git), \
             patch.object(boot.grp, "getgrgid", return_value=types.SimpleNamespace(gr_name="gace")), \
             patch.object(boot.pwd, "getpwnam", return_value=types.SimpleNamespace(pw_uid=1000)):
            return boot.preflight(SHA, "10001")

    def test_shared_runtime_directory_survives_source_executor_restart(self):
        self.assertIn("RuntimeDirectoryPreserve=yes", boot.unit_text("gace"))

    def test_preflight_pass(self):
        self.assertEqual(self.verify(), "gace")

    def test_unowned_dirty_changes_block_install(self):
        with self.assertRaisesRegex(boot.AdmissionError, "DIRTY_CHECKOUT_DENIED"):
            self.verify(dirty=True)

    def test_head_mismatch(self):
        with self.assertRaisesRegex(boot.AdmissionError, "SOURCE_HEAD_MISMATCH"):
            self.verify(head="b" * 40)

    def test_origin_switch(self):
        with self.assertRaisesRegex(boot.AdmissionError, "REMOTE_ORIGIN_DENIED"):
            self.verify(remote="file:///tmp/attacker.git")

    def test_wrong_branch(self):
        with self.assertRaisesRegex(boot.AdmissionError, "BRANCH_NOT_MAIN"):
            self.verify(branch="feature")

    def test_installer_requires_explicit_root(self):
        with patch.object(boot, "preflight", return_value="gace"), \
             patch.object(boot.os, "geteuid", return_value=1000):
            with self.assertRaisesRegex(boot.AdmissionError, "HOST_ADMIN_REQUIRED"):
                boot.install(SHA, "10001")

    def test_unit_has_no_root_exec_or_network_listener(self):
        unit = boot.unit_text("gace")
        self.assertIn("User=admin1", unit)
        self.assertIn("Group=gace", unit)
        self.assertIn("NoNewPrivileges=yes", unit)
        self.assertNotIn("0.0.0.0", unit)
        self.assertNotIn("docker.sock", unit)

    def test_injected_group_denied(self):
        with self.assertRaisesRegex(boot.AdmissionError, "SERVICE_GROUP_INVALID"):
            boot.unit_text("root\nExecStart=/bin/sh")


if __name__ == "__main__":
    unittest.main()
