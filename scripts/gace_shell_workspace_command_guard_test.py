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


    def test_deny_git_branch_rename_as_non_readonly(self):
        out = run("git branch -M evil-main", self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "NOT_WORKSPACE_MUTATION_COMMAND")

    def test_deny_git_remote_add_as_non_readonly(self):
        out = run("git remote add origin https://example.com/r.git", self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "NOT_WORKSPACE_MUTATION_COMMAND")

    def test_deny_gh_unknown_subcommand(self):
        out = run("gh mystery-do-thing", self.projects, self.worktrees)
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "GH_UNKNOWN_SUBCOMMAND")

    def test_deny_git_clone_inside_registered_parent(self):
        parent = self.projects / "TGserver"
        dest = parent / "nested-clone"
        out = run(
            f"git clone https://example.com/r.git {dest}",
            self.projects,
            self.worktrees,
            cwd=str(parent),
        )
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "DERIVED_REPO_INSIDE_PARENT")

    def test_deny_relative_mkdir_unregistered_from_projects_cwd(self):
        out = run(
            "mkdir -p sibling-evil",
            self.projects,
            self.worktrees,
            cwd=str(self.projects),
        )
        self.assertEqual(out["result"], "DENY")

    def test_allow_relative_mkdir_inside_registered_parent(self):
        parent = self.projects / "TGserver"
        out = run(
            "mkdir -p .worktrees/cu9",
            self.projects,
            self.worktrees,
            cwd=str(parent),
        )
        self.assertEqual(out["result"], "ALLOW")

    def test_deny_tree_copy_outside_parent(self):
        outside = "/tmp/gace-pr39-tree-copy"
        parent = self.projects / "TGserver"
        samples = (
            (" ".join(["cp", "-r", str(parent), outside]), "PERSISTENT_COPY_OUTSIDE_PARENT"),
            (" ".join(["rsync", "-a", f"{parent}/", f"{outside}/"]), "PERSISTENT_COPY_OUTSIDE_PARENT"),
            (" ".join(["mv", str(parent), outside]), "PERSISTENT_COPY_OUTSIDE_PARENT"),
        )
        for command, code in samples:
            out = run(command, self.projects, self.worktrees)
            self.assertEqual(out["result"], "DENY", command)
            self.assertEqual(out["code"], code, command)

    def test_allow_single_file_copy_to_tmp(self):
        src = self.projects / "TGserver" / "README.md"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("probe", encoding="utf-8")
        out = run(f"cp {src} /tmp/gace-pr39-readme-copy.md", self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")
        Path("/tmp/gace-pr39-readme-copy.md").unlink(missing_ok=True)

    def test_allow_copy_within_registered_parent(self):
        parent = self.projects / "TGserver"
        parent.mkdir(parents=True, exist_ok=True)
        out = run(f"cp -r {parent}/.worktrees {parent}/backup-copy", self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")

    def test_deny_persistent_checkout_outside_parent(self):
        outside = "/tmp/gace-pr39-outside-parent"
        samples = (
            (" ".join(["git", "clone", "https://example.invalid/r.git", outside]), "PERSISTENT_CHECKOUT_OUTSIDE_PARENT"),
            (" ".join(["git", "init", outside]), "PERSISTENT_CHECKOUT_OUTSIDE_PARENT"),
            (" ".join(["git", "worktree", "add", outside, "HEAD"]), "PERSISTENT_CHECKOUT_OUTSIDE_PARENT"),
        )
        for command, code in samples:
            out = run(command, self.projects, self.worktrees)
            self.assertEqual(out["result"], "DENY", command)
            self.assertEqual(out["code"], code, command)

    def test_allow_tmp_scratch_mkdir(self):
        out = run(" ".join(["mkdir", "-p", "/tmp/gace-pr39-scratch"]), self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")

    def test_allow_worktree_inside_server_core(self):
        dest = "/home/admin1/server-core/.worktrees/cu39-coverage-probe"
        out = run(" ".join(["git", "worktree", "add", dest, "HEAD"]), self.projects, self.worktrees)
        self.assertEqual(out["result"], "ALLOW")
        self.assertFalse(Path(dest).exists())

    def test_deny_clone_inside_server_core_outside_worktrees(self):
        dest = "/home/admin1/server-core/nested-clone-probe"
        out = run(" ".join(["git", "clone", "https://example.invalid/r.git", dest]), self.projects, self.worktrees)
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "DERIVED_REPO_INSIDE_PARENT")
        self.assertFalse(Path(dest).exists())

    def test_concurrent_classifier_isolation(self):
        import concurrent.futures

        cmds = ["git status"] + [f"mkdir -p {self.projects}/evil-{i}" for i in range(6)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(
                pool.map(
                    lambda c: run(c, self.projects, self.worktrees),
                    cmds,
                )
            )
        self.assertEqual(results[0]["result"], "ALLOW")
        for r in results[1:]:
            self.assertEqual(r["result"], "DENY")


HOOK = ROOT / ".cursor/hooks/before-shell-workspace-guard.sh"


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.projects = Path(self.temp.name) / "projects"
        self.worktrees = Path(self.temp.name) / "worktrees"
        self.projects.mkdir()
        self.worktrees.mkdir()
        (self.projects / "TGserver").mkdir()

    def run_hook(self, payload: str) -> dict:
        proc = subprocess.run(
            ["bash", str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0 if json.loads(proc.stdout).get("permission") == "allow" else 2)
        return json.loads(proc.stdout.strip())

    def test_hook_deny_empty_command(self):
        out = self.run_hook('{"command":""}')
        self.assertEqual(out["permission"], "deny")

    def test_hook_deny_invalid_json(self):
        out = self.run_hook('not-json')
        self.assertEqual(out["permission"], "deny")

    def test_hook_allow_git_status(self):
        out = self.run_hook('{"command":"git status","cwd":"/home/admin1/server-core"}')
        self.assertEqual(out["permission"], "allow")

    def test_hook_uses_cwd_for_relative_path(self):
        payload = json.dumps(
            {
                "command": "mkdir -p sibling-evil-cu8-test",
                "cwd": "/home/admin1/projects",
            }
        )
        out = self.run_hook(payload)
        self.assertEqual(out["permission"], "deny")

    def test_hook_concurrent_no_shared_tmp(self):
        import concurrent.futures

        payloads = [
            json.dumps({"command": "git status", "cwd": "/home/admin1/server-core"}),
            json.dumps({"command": "mkdir -p /home/admin1/projects/evil-concurrent-cu8", "cwd": "/home/admin1/projects"}),
        ] * 4
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            outs = list(pool.map(self.run_hook, payloads))
        self.assertTrue(any(o.get("permission") == "allow" for o in outs))
        self.assertTrue(any(o.get("permission") == "deny" for o in outs))
        hook_src = (ROOT / ".cursor/hooks/before-shell-workspace-guard.sh").read_text(encoding="utf-8")
        self.assertNotIn("gace-shell-guard-last.json", hook_src)

    def test_hook_denies_outside_parent_checkout_and_allows_scratch(self):
        denied = self.run_hook(
            json.dumps(
                {
                    "command": " ".join(["git", "clone", "https://example.invalid/r.git", "/tmp/gace-pr39-outside-parent"]),
                    "cwd": "/home/admin1/server-core",
                }
            )
        )
        self.assertEqual(denied["permission"], "deny")
        allowed = self.run_hook(
            json.dumps({"command": " ".join(["mkdir", "-p", "/tmp/gace-pr39-scratch"]), "cwd": "/tmp"})
        )
        self.assertEqual(allowed["permission"], "allow")
        nested = self.run_hook(
            json.dumps(
                {
                    "command": " ".join(["git", "worktree", "add", "/home/admin1/server-core/.worktrees/cu39-coverage-probe", "HEAD"]),
                    "cwd": "/home/admin1/server-core",
                }
            )
        )
        self.assertEqual(nested["permission"], "allow")
        self.assertFalse(Path("/tmp/gace-pr39-outside-parent").exists())
        self.assertFalse(Path("/tmp/gace-pr39-scratch").exists())
        self.assertFalse(Path("/home/admin1/server-core/.worktrees/cu39-coverage-probe").exists())


    def _full_binding_json(self, **overrides):
        head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        branch = subprocess.check_output(["git", "-C", str(ROOT), "branch", "--show-current"], text=True).strip()
        doc = {
            "repository": "G-ACE-inc/server-core",
            "branch": branch,
            "head": head,
            "change_unit": "CU39",
            "mutation_owner": "composer",
            "exact_next_gate": "CI",
            "in_scope_path_prefixes": ["scripts/"],
        }
        doc.update(overrides)
        import json as _json
        return _json.dumps(doc)

    def test_deny_bound_git_commit_wrong_branch(self):
        import os
        binding = self._full_binding_json(branch="wrong-on-purpose")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                "git commit -m test",
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WRONG_MISSION_OR_CU")

    def test_allow_bound_git_status_readonly(self):
        import os
        binding = self._full_binding_json(branch="wrong-on-purpose")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                "git status",
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "ALLOW")

    def test_deny_bound_git_dash_c_commit_wrong_branch(self):
        import os
        binding = self._full_binding_json(branch="wrong-on-purpose")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                f"git -C {ROOT} commit -m test",
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WRONG_MISSION_OR_CU")

    def test_allow_bound_git_dash_c_status_readonly(self):
        import os
        binding = self._full_binding_json(branch="wrong-on-purpose")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                f"git -C {ROOT} status",
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "ALLOW")


    def test_bound_quoted_c_commit_denied_not_allowed_fallthrough(self):
        import os
        import tempfile
        space_repo = Path(tempfile.mkdtemp(prefix="repo space ", dir=str(self.temp.name)))
        binding = self._full_binding_json(branch="main")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        cmd = f'git -C "{space_repo}" commit -m test'
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                cmd,
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "DENY")
        self.assertNotEqual(out["code"], "NOT_WORKSPACE_MUTATION_COMMAND")

    def test_bound_quoted_c_status_readonly_allow(self):
        import os
        import tempfile
        space_repo = Path(tempfile.mkdtemp(prefix="repo space ", dir=str(self.temp.name)))
        binding = self._full_binding_json(branch="wrong-branch")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        cmd = f'git -C "{space_repo}" status'
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                cmd,
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "GIT_READONLY_INVOCATION")

    def test_bound_git_dir_equals_commit_denied(self):
        import os
        binding = self._full_binding_json()
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                "git --git-dir=/tmp/other.git commit -m x",
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "GIT_ALTERNATE_REPOSITORY_SPEC")

    def test_bound_work_tree_equals_commit_denied(self):
        import os
        binding = self._full_binding_json()
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                "git --work-tree=/tmp/other commit -m x",
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "GIT_ALTERNATE_REPOSITORY_SPEC")

    def _bound_command_result(self, command):
        import os
        binding = self._full_binding_json()
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3", str(GUARD), "--command", command,
                "--cwd", str(ROOT), "--projects-root", str(self.projects),
                "--worktrees-root", str(self.worktrees),
                "--registry-doc", str(REGISTRY),
            ],
            capture_output=True, text=True, check=False, env=env,
        )
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return json.loads(proc.stdout.strip())

    def test_bound_complex_shell_and_interpreter_denied_as_one_gate(self):
        for cmd, expected in (
            ("git status | git commit -m unsafe", "COMPOUND_SHELL_PARSE_AMBIGUOUS"),
            ("git status" + chr(10) + "git commit -m unsafe", "GIT_SHELL_SYNTAX_UNVERIFIED"),
            ("git status $(git commit -m unsafe)", "COMPOUND_SHELL_PARSE_AMBIGUOUS"),
            ("bash -c 'git commit -m unsafe'", "GIT_INTERPRETER_COMMAND_UNVERIFIED"),
            ("sh -c 'git status && git commit -m unsafe'", "GIT_INTERPRETER_COMMAND_UNVERIFIED"),
            ("env GIT_DIR=/tmp/fake.git git commit -m unsafe", "GIT_WRAPPED_COMMAND_UNVERIFIED"),
            ("cd /tmp && git commit -m unsafe", "GIT_SHELL_CONTEXT_UNVERIFIED"),
            ("git status && cd /tmp && git commit -m unsafe", "GIT_SHELL_CONTEXT_UNVERIFIED"),
            ("git fetch origin", "GIT_SUBCOMMAND_UNVERIFIED_UNDER_BINDING"),
        ):
            with self.subTest(cmd=cmd):
                out = self._bound_command_result(cmd)
                self.assertEqual(out["result"], "DENY", cmd)
                self.assertEqual(out["code"], expected, cmd)

    def test_bound_quoted_paths_keep_compound_git_write_binding(self):
        binding = self._full_binding_json(branch="wrong-on-purpose")
        import os
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        cmd = f'git -C "{ROOT}" status && git -C "{ROOT}" commit -m unsafe'
        proc = subprocess.run(
            ["python3", str(GUARD), "--command", cmd, "--cwd", str(ROOT),
             "--projects-root", str(self.projects), "--worktrees-root", str(self.worktrees),
             "--registry-doc", str(REGISTRY)],
            capture_output=True, text=True, check=False, env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WRONG_MISSION_OR_CU")
        self.assertNotEqual(out["code"], "NOT_WORKSPACE_MUTATION_COMMAND")

    def test_bound_quoted_literal_and_readonly_are_uninterrupted(self):
        for command in (
            "echo 'git commit -m literal'",
            'echo "git commit; not an execution"',
            "git status && git log -1",
            f'git -C "{ROOT}" status && git -C "{ROOT}" log -1',
        ):
            with self.subTest(cmd=command):
                out = self._bound_command_result(command)
                self.assertEqual(out["result"], "ALLOW", command)

    def test_bound_compound_status_and_commit_denied(self):
        import os
        binding = self._full_binding_json(branch="main")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        for cmd in (
            "git status && git commit -m test",
            "git status; git commit -m test",
            f"git -C {ROOT} status && git -C {ROOT} commit -m test",
        ):
            proc = subprocess.run(
                [
                    "python3",
                    str(GUARD),
                    "--command",
                    cmd,
                    "--cwd",
                    str(ROOT),
                    "--projects-root",
                    str(self.projects),
                    "--worktrees-root",
                    str(self.worktrees),
                    "--registry-doc",
                    str(REGISTRY),
                ],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            out = json.loads(proc.stdout.strip())
            self.assertEqual(out["result"], "DENY", cmd)
            self.assertNotEqual(out["code"], "NOT_WORKSPACE_MUTATION_COMMAND", cmd)
            self.assertNotEqual(out["code"], "GIT_READONLY_INVOCATION", cmd)

    def test_bound_compound_readonly_git_chain_allow(self):
        import os
        binding = self._full_binding_json(branch="wrong-branch")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                "git status && git log -1 --oneline",
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "GIT_READONLY_INVOCATION")

    def test_bound_compound_hook_stdin_denies_commit_chain(self):
        import os
        binding = self._full_binding_json(branch="main")
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        payload = json.dumps({"command": "git status && git commit -m hook", "cwd": str(ROOT)})
        proc = subprocess.run(
            ["bash", str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["permission"], "deny")

    def test_hook_strict_partial_turn_without_binding_denies_write(self):
        import os
        payload = json.dumps({"command": "git commit -m test", "cwd": str(ROOT)})
        env = os.environ.copy()
        env.pop("GACE_MUTATION_BINDING", None)
        env["GACE_WORK_ROUTINE_TURN"] = "/nonexistent/turn.json"
        proc = subprocess.run(
            ["bash", str(HOOK)], input=payload, capture_output=True,
            text=True, check=False, env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["permission"], "deny")
        self.assertIn("WORK_ROUTINE_MUTATION_BINDING_REQUIRED", out["user_message"])

    def test_hook_strict_partial_binding_without_turn_denies_write(self):
        import os
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = self._full_binding_json()
        env.pop("GACE_WORK_ROUTINE_TURN", None)
        payload = json.dumps({"command": "git commit -m test", "cwd": str(ROOT)})
        proc = subprocess.run(
            ["bash", str(HOOK)], input=payload, capture_output=True,
            text=True, check=False, env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["permission"], "deny")
        self.assertIn("BINDING_INCOMPLETE", out["user_message"])

    def test_echo_quoted_git_commit_not_compound_blocked(self):
        import os
        binding = self._full_binding_json()
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            [
                "python3",
                str(GUARD),
                "--command",
                "echo 'git commit -m fake'",
                "--cwd",
                str(ROOT),
                "--projects-root",
                str(self.projects),
                "--worktrees-root",
                str(self.worktrees),
                "--registry-doc",
                str(REGISTRY),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "NOT_WORKSPACE_MUTATION_COMMAND")

if __name__ == "__main__":
    unittest.main()
