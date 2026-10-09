#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts/gace_shell_workspace_command_guard.py"
REGISTRY = ROOT / "docs/WORKSPACE_REGISTRY.md"


def run(cmd: str, projects: Path, worktrees: Path, cwd: str = "/home/admin1") -> dict:
    proc = subprocess.run(
        [
            "python3",
            str(GUARD),
            "--command",
            cmd,
            "--cwd",
            cwd,
            "--projects-root",
            str(projects),
            "--worktrees-root",
            str(worktrees),
            "--registry-doc",
            str(REGISTRY),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return json.loads(proc.stdout.strip())


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.projects = Path(self.temp.name) / "projects"
        self.worktrees = Path(self.temp.name) / "worktrees"
        self.projects.mkdir()
        self.worktrees.mkdir()
        (self.projects / "TGserver").mkdir()

    def test_allow_readonly(self):
        out = run("git status", self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")

    def test_deny_unregistered_mkdir(self):
        out = run(f"mkdir -p {self.projects}/brand-new-cu", self.projects, self.worktrees)
        self.assertEqual(out["result"], "DENY")

    def test_allow_registered_nested_worktree(self):
        parent = self.projects / "TGserver"
        out = run(
            f"git worktree add {parent}/.worktrees/cu1 main",
            self.projects,
            self.worktrees,
            cwd=str(parent),
        )
        self.assertEqual(out["result"], "ALLOW")

    def test_deny_worktrees_root(self):
        out = run(f"git worktree add {self.worktrees}/debug-ai-quality main", self.projects, self.worktrees)
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WORKTREES_ROOT_PERSISTENT_CHECKOUT_FORBIDDEN")

    def test_deny_traversal_clone(self):
        out = run(f"git clone https://example.com/r.git {self.projects}/evil-sibling", self.projects, self.worktrees)
        self.assertEqual(out["result"], "DENY")



    def test_allow_gh_issue_comment_heredoc_mkdir_in_body(self):
        cmd = (
            "gh issue comment 15 --body $(cat <<\'EOF\'\nmkdir evil\nEOF\n)"
        )
        out = run(cmd, self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")

    def test_allow_echo_quoted_mkdir(self):
        out = run('echo "mkdir foo"', self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")

    def test_allow_gh_api_get(self):
        out = run("gh api GET repos/octocat/Hello-World", self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")

    def test_deny_bash_c_mkdir_unregistered(self):
        out = run(
            f"bash -c 'mkdir -p {self.projects}/brand-new-cu'",
            self.projects,
            self.worktrees,
        )
        self.assertEqual(out["result"], "DENY")

    def test_deny_gh_repo_clone_unregistered(self):
        out = run(
            f"gh repo clone https://github.com/o/r.git {self.projects}/new-cu",
            self.projects,
            self.worktrees,
        )
        self.assertEqual(out["result"], "DENY")



    def test_allow_git_diff_and_log(self):
        out = run("git diff --stat", self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")
        out = run("git log -1 --oneline", self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")

    def test_allow_gh_api_post_evidence(self):
        out = run(
            "gh api -X POST repos/G-ACE-inc/server-core/issues/15/comments -f body=evidence",
            self.projects,
            self.worktrees,
        )
        self.assertEqual(out["result"], "ALLOW")

    def test_deny_mv_unregistered(self):
        out = run(
            f"mv /tmp/source {self.projects}/brand-new-cu",
            self.projects,
            self.worktrees,
        )
        self.assertEqual(out["result"], "DENY")

    def test_deny_cp_without_flags_unregistered(self):
        out = run(
            f"cp /tmp/source {self.projects}/brand-new-cu/file",
            self.projects,
            self.worktrees,
        )
        self.assertEqual(out["result"], "DENY")

    def test_deny_python_c_mkdir_unregistered(self):
        target = f"{self.projects}/brand-new-cu"
        out = run(
            "python3 -c 'import os; os.makedirs(\'" + str(target) + "\')'",
            self.projects,
            self.worktrees,
        )
        self.assertEqual(out["result"], "DENY")

    def test_deny_path_traversal(self):
        out = run(
            f"mkdir -p {self.projects}/../projects/traversal-evil",
            self.projects,
            self.worktrees,
        )
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "PATH_TRAVERSAL")

if __name__ == "__main__":
    unittest.main(verbosity=2)
