import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("deploy_bootstrap", SCRIPTS / "servercore_dev_job_host_bootstrap.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
HEAD = "a" * 40


def fake_git(dirty=False, branch="main", origin="https://github.com/G-ACE-inc/server-core.git", head=HEAD):
    def run(*args):
        if args[:2] == ("rev-parse", "--abbrev-ref"):
            return branch
        if args[:2] == ("remote", "get-url"):
            return origin
        if args[:1] == ("rev-parse",):
            return head
        if args[:1] == ("status",):
            return " M scripts/x.py" if dirty else ""
        raise AssertionError(args)
    return run


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve() / "server-core"
        (root / ".git").mkdir(parents=True)
        (root / "scripts").mkdir()
        (root / "scripts/servercore_dev_job_socket.py").write_text("")
        run_dir = Path(self.tmp.name).resolve() / "run-gace"
        run_dir.mkdir()
        for name, value in (("ROOT", root), ("RUN_DIR", run_dir)):
            patcher = patch.object(m, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(m.os, "geteuid", return_value=1000)
        patcher.start()
        self.addCleanup(patcher.stop)

    def check(self, message, **kw):
        with patch.object(m, "git", side_effect=fake_git(**kw)):
            with self.assertRaisesRegex(m.AdmissionError, message):
                m.preflight(HEAD)

    def test_clean_preflight_passes(self):
        with patch.object(m, "git", side_effect=fake_git()):
            m.preflight(HEAD)

    def test_root_install_denied(self):
        with patch.object(m, "git", side_effect=fake_git()), patch.object(m.os, "geteuid", return_value=0):
            with self.assertRaisesRegex(m.AdmissionError, "ROOT_INSTALL_DENIED"):
                m.preflight(HEAD)

    def test_unit_is_user_level_without_root_or_network(self):
        self.assertNotIn("User=root", m.UNIT_TEXT)
        self.assertIn("NoNewPrivileges=no", m.UNIT_TEXT)  # sg is setuid; see UNIT_TEXT note
        self.assertIn("UMask=0117", m.UNIT_TEXT)
        self.assertNotIn("0.0.0.0", m.UNIT_TEXT)
        self.assertIn("WantedBy=default.target", m.UNIT_TEXT)

    def test_preflight_denials(self):
        self.check("BRANCH_NOT_MAIN", branch="feature")
        self.check("REMOTE_ORIGIN_DENIED", origin="file:///tmp/evil.git")
        self.check("SOURCE_HEAD_MISMATCH", head="b" * 40)
        self.check("DEV_JOB_SOURCE_DIRTY", dirty=True)

    def test_expected_head_must_be_exact_sha(self):
        with self.assertRaisesRegex(m.AdmissionError, "EXPECTED_SHA_INVALID"):
            m.preflight("HEAD")

    def test_install_denied_when_preflight_fails(self):
        with patch.object(m, "preflight", side_effect=m.AdmissionError("SOURCE_HEAD_MISMATCH")), \
             patch.object(m, "systemctl_user") as ctl:
            with self.assertRaises(m.AdmissionError):
                m.install(HEAD)
        ctl.assert_not_called()


class UnitUpgradeTests(unittest.TestCase):
    def test_unit_starts_through_sg_docker_without_root(self):
        self.assertIn('ExecStart=/usr/bin/sg docker -c "/usr/bin/python3 /home/admin1/server-core/scripts/', m.UNIT_TEXT)
        self.assertIn("NoNewPrivileges=no", m.UNIT_TEXT)
        self.assertIn("UMask=0117", m.UNIT_TEXT)
        self.assertNotIn("sudo", m.UNIT_TEXT)
        self.assertEqual(m.LEGACY_UNIT_TEXTS, ())
        self.assertIn("servercore_dev_job_socket.py", m.UNIT_TEXT)

    def run_install(self, existing):
        import tempfile, os, stat
        with tempfile.TemporaryDirectory() as tmp:
            unit = Path(tmp) / "x.service"
            if existing is not None:
                unit.write_text(existing)

            class FakeSocket:
                def is_socket(self):
                    return True

                def stat(self):
                    class S:
                        st_uid = os.getuid()
                        st_mode = stat.S_IFSOCK | 0o660
                    return S()
            with patch.object(m, "UNIT", unit), patch.object(m, "preflight"), \
                    patch.object(m, "systemctl_user"), patch.object(m, "SOCKET", FakeSocket()):
                try:
                    return m.install(HEAD), unit.read_text()
                except m.AdmissionError as exc:
                    return str(exc), unit.read_text()

    def test_unknown_unit_is_not_overwritten_and_current_unit_is_idempotent(self):
        result, text = self.run_install(m.UNIT_TEXT)
        self.assertIsInstance(result, dict)
        self.assertEqual(text, m.UNIT_TEXT)
        result, text = self.run_install("[Service]\nExecStart=/bin/true\n")
        self.assertEqual(result, "EXISTING_UNIT_CONFLICT")
        self.assertIn("/bin/true", text)
        self.assertEqual(self.run_install(None)[1], m.UNIT_TEXT)


if __name__ == "__main__":
    unittest.main()
