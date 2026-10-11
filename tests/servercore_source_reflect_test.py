import importlib.util
import tempfile
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "servercore_source_reflect.py"
spec = importlib.util.spec_from_file_location("servercore_source_reflect", SCRIPT)
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
A, B, C = "a" * 40, "b" * 40, "c" * 40


class ReflectTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".git").mkdir()

    def execute(self, *, before=A, remote=B, dirty=False, branch="main", ancestor=A, dry_run=False):
        commands = []
        def fake_git(root, *argv):
            commands.append(argv)
            if argv == ("rev-parse", "--abbrev-ref", "HEAD"):
                return branch
            if argv == ("rev-parse", "HEAD"):
                return B if any(c[:1] == ("merge",) for c in commands) else before
            if argv == ("status", "--porcelain", "--untracked-files=all"):
                return " M operations/master-internal-repositories.json" if dirty else ""
            if argv == ("rev-parse", "FETCH_HEAD"):
                return remote
            if argv == ("merge-base", before, B):
                return ancestor
            return ""
        with patch.object(source, "CANONICAL_ROOT", self.root.resolve()):
            with patch.object(source, "git", side_effect=fake_git):
                return source.reflect(self.root, A, B, dry_run=dry_run), commands

    def test_exact_fast_forward(self):
        result, commands = self.execute()
        self.assertEqual(result["state"], "SOURCE_REFLECT_PASS")
        self.assertIn(("merge", "--ff-only", "--no-commit", B), commands)

    def test_dry_run_no_merge(self):
        result, commands = self.execute(dry_run=True)
        self.assertEqual(result["state"], "PREFLIGHT_PASS")
        self.assertFalse(any(c[0] == "merge" for c in commands))

    def test_existing_dirty_file_preserved(self):
        with self.assertRaisesRegex(source.ReflectError, "DIRTY_CHECKOUT_DENIED"):
            self.execute(dirty=True)

    def test_wrong_expected_before_denied(self):
        with self.assertRaisesRegex(source.ReflectError, "BEFORE_SHA_MISMATCH"):
            self.execute(before=C)

    def test_remote_main_mismatch_denied(self):
        with self.assertRaisesRegex(source.ReflectError, "REMOTE_MAIN_SHA_MISMATCH"):
            self.execute(remote=C)

    def test_diverged_denied(self):
        with self.assertRaisesRegex(source.ReflectError, "NON_FAST_FORWARD_DENIED"):
            self.execute(ancestor=C)

    def test_wrong_branch_denied(self):
        with self.assertRaisesRegex(source.ReflectError, "BRANCH_NOT_MAIN"):
            self.execute(branch="develop")

    def test_wrong_root_denied(self):
        with self.assertRaisesRegex(source.ReflectError, "CANONICAL_ROOT_DENIED"):
            source.reflect(self.root, A, B)

    def test_invalid_sha_denied(self):
        with self.assertRaisesRegex(source.ReflectError, "SHA_INVALID"):
            source.reflect(self.root, "HEAD", B)


if __name__ == "__main__":
    main()
