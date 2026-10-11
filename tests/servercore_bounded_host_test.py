import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "servercore_bounded_host.py"
spec = importlib.util.spec_from_file_location("bounded_host", SCRIPT)
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)
SHA = "a" * 40


class BoundedHostTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "scripts").mkdir()
        for test in host.TESTS:
            (self.root / test).write_text("print('ok')\n")

    def run_with(self, command, sha=SHA, clean=True):
        def fake_run(argv, root, timeout=35):
            if argv[:3] == ["git", "rev-parse", "HEAD"]:
                return SHA + "\n"
            if argv[:3] == ["git", "status", "--porcelain"]:
                return "" if clean else " M README.md\n"
            return "ok\n"
        with patch.object(host, "_run", side_effect=fake_run):
            return host.execute(command, self.root, sha)

    def test_git_invocation_scoped_to_canonical_directory(self):
        calls = []
        class Result:
            returncode = 0
            stdout = SHA + "\\n"
        def capture(argv, **kwargs):
            calls.append((argv, kwargs))
            return Result()
        with patch.object(host.subprocess, "run", side_effect=capture):
            host._run(["git", "rev-parse", "HEAD"], self.root)
        args, kwargs = calls[0]
        self.assertEqual(args[0:3], ["git", "-c", "safe.directory=" + str(self.root.resolve())])
        self.assertIn("core.fsmonitor=false", args)
        self.assertIn("core.hooksPath=/dev/null", args)
        self.assertNotIn("--global", args)
        self.assertEqual(kwargs["cwd"], self.root)

    def test_exact_head(self):
        self.assertEqual(self.run_with("project.git_head")["source_sha"], SHA)

    def test_git_recent_commits_fixed_sha_only(self):
        with patch.object(host, "_run", side_effect=[SHA + "\\n", SHA + "\\n" + "b" * 40 + "\\n"]):
            result = host.execute("project.git_recent_commits", self.root, SHA)
        self.assertEqual(result["commits"], [SHA, "b" * 40])

    def test_git_recent_commits_rejects_invalid_output(self):
        with patch.object(host, "_run", side_effect=[SHA + "\\n", "a commit subject\\n"]):
            with self.assertRaisesRegex(host.BoundaryError, "GIT_HISTORY_INVALID"):
                host.execute("project.git_recent_commits", self.root, SHA)

    def test_unregistered_fails_closed(self):
        with self.assertRaisesRegex(host.BoundaryError, "COMMAND_NOT_REGISTERED"):
            self.run_with("system.shell")

    def test_sha_mismatch_fails_closed(self):
        with self.assertRaisesRegex(host.BoundaryError, "SOURCE_SHA_MISMATCH"):
            self.run_with("project.git_head", "b" * 40)

    def test_status_no_raw_paths(self):
        result = self.run_with("project.git_status", clean=False)
        self.assertFalse(result["clean"])
        self.assertNotIn("README", str(result))

    def test_registered_tests_fixed(self):
        result = self.run_with("project.registered_tests")
        self.assertEqual(result["count"], 2)

    def test_dirty_tests_denied(self):
        with self.assertRaisesRegex(host.BoundaryError, "TEST_CHECKOUT_DIRTY"):
            self.run_with("project.registered_tests", clean=False)

    def test_missing_test_denied(self):
        (self.root / host.TESTS[0]).unlink()
        with self.assertRaisesRegex(host.BoundaryError, "REGISTERED_TEST_MISSING"):
            self.run_with("project.registered_tests")

    def test_root_symlink_denied(self):
        link = self.root.parent / (self.root.name + "-symlink")
        link.symlink_to(self.root)
        self.addCleanup(link.unlink)
        with self.assertRaisesRegex(host.BoundaryError, "CANONICAL_ROOT_INVALID"):
            host.checked_root(link)


if __name__ == "__main__":
    unittest.main()
