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
        with patch.object(host, "_run", side_effect=[SHA + chr(10), SHA + chr(10) + "b" * 40 + chr(10)]):
            result = host.execute("project.git_recent_commits", self.root, SHA)
        self.assertEqual(result["commits"], [SHA, "b" * 40])

    def test_git_recent_commits_rejects_invalid_output(self):
        with patch.object(host, "_run", side_effect=[SHA + chr(10), "a commit subject" + chr(10)]):
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

    def test_file_inspect_pagination_exact_byte_offsets(self):
        target = self.root / "docs" / "LOAD_SCOPE.md"
        target.parent.mkdir()
        content = b"A" * host.FILE_CHUNK_BYTES + b"B" * 31
        target.write_bytes(content)
        with patch.object(host, "_run", return_value=SHA + "\\n"):
            first = host.file_inspect(self.root, SHA, "docs/LOAD_SCOPE.md", 0, ["docs/LOAD_SCOPE.md"])
            second = host.file_inspect(self.root, SHA, "docs/LOAD_SCOPE.md", first["next_offset"], ["docs/LOAD_SCOPE.md"])
        self.assertEqual(first["offset"], 0)
        self.assertEqual(first["next_offset"], host.FILE_CHUNK_BYTES)
        self.assertEqual(len(first["content"]), host.FILE_CHUNK_BYTES)
        self.assertEqual(second["offset"], host.FILE_CHUNK_BYTES)
        self.assertEqual(second["content"], "B" * 31)
        self.assertIsNone(second["next_offset"])
        self.assertEqual(first["size"], len(content))
        self.assertEqual(second["size"], len(content))

    def test_file_inspect_rejects_unregistered_target(self):
        target = self.root / "README.md"
        target.write_text("safe")
        with patch.object(host, "_run", return_value=SHA + "\\n"):
            with self.assertRaisesRegex(host.BoundaryError, "FILE_NOT_REGISTERED"):
                host.file_inspect(self.root, SHA, "README.md", 0, ["docs/LOAD_SCOPE.md"])

    def test_file_inspect_rejects_invalid_offset(self):
        target = self.root / "README.md"
        target.write_text("safe")
        with patch.object(host, "_run", return_value=SHA + "\\n"):
            with self.assertRaisesRegex(host.BoundaryError, "FILE_OFFSET_INVALID"):
                host.file_inspect(self.root, SHA, "README.md", -1, ["README.md"])

    def test_root_symlink_denied(self):
        link = self.root.parent / (self.root.name + "-symlink")
        link.symlink_to(self.root)
        self.addCleanup(link.unlink)
        with self.assertRaisesRegex(host.BoundaryError, "CANONICAL_ROOT_INVALID"):
            host.checked_root(link)


if __name__ == "__main__":
    unittest.main()
