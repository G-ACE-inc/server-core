import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("deploy_bootstrap", SCRIPTS / "servercore_result_sink_host_bootstrap.py")
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
        (root / "scripts/servercore_result_sink.py").write_text("")
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
        self.assertIn("NoNewPrivileges=yes", m.UNIT_TEXT)
        self.assertIn("UMask=0117", m.UNIT_TEXT)
        self.assertNotIn("0.0.0.0", m.UNIT_TEXT)
        self.assertIn("WantedBy=default.target", m.UNIT_TEXT)

    def test_preflight_denials(self):
        self.check("BRANCH_NOT_MAIN", branch="feature")
        self.check("REMOTE_ORIGIN_DENIED", origin="file:///tmp/evil.git")
        self.check("SOURCE_HEAD_MISMATCH", head="b" * 40)
        self.check("RESULT_SINK_SOURCE_DIRTY", dirty=True)

    def test_expected_head_must_be_exact_sha(self):
        with self.assertRaisesRegex(m.AdmissionError, "EXPECTED_SHA_INVALID"):
            m.preflight("HEAD")

    def test_install_denied_when_preflight_fails(self):
        with patch.object(m, "preflight", side_effect=m.AdmissionError("SOURCE_HEAD_MISMATCH")), \
             patch.object(m, "systemctl_user") as ctl:
            with self.assertRaises(m.AdmissionError):
                m.install(HEAD)
        ctl.assert_not_called()

    def test_remount_skips_when_bounded_host_not_running(self):
        with patch.object(m.subprocess, "run") as run:
            run.return_value = type("R", (), {"returncode": 0, "stdout": "false"})()
            out = m.remount_bounded_host_consumer()
        self.assertEqual(out["state"], "BOUNDED_HOST_REMOUNT_SKIPPED")

    def test_remount_restarts_running_bounded_host(self):
        calls = []

        def fake_run(argv, **kw):
            calls.append(argv)
            if argv[:2] == ["docker", "inspect"]:
                return type("R", (), {"returncode": 0, "stdout": "true"})()
            return type("R", (), {"returncode": 0, "stdout": ""})()

        with patch.object(m.subprocess, "run", side_effect=fake_run):
            out = m.remount_bounded_host_consumer()
        self.assertEqual(out["state"], "BOUNDED_HOST_REMOUNTED")
        self.assertEqual(calls[-1][:2], ["docker", "restart"])


if __name__ == "__main__":
    unittest.main()
