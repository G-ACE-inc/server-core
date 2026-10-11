#!/usr/bin/env python3
"""Isolated real-Git fixtures for canonical parent admission."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

GATE = Path(__file__).resolve().with_name("init_dev_workspace_project_gate.py")


def git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def invoke(name: str, projects: Path, registry: Path, master: Path) -> dict:
    p = subprocess.run(
        ["python3", "-B", str(GATE), "--name", name, "--projects-dir", str(projects),
         "--registry-doc", str(registry), "--master-registry", str(master)],
        capture_output=True, text=True, check=False,
    )
    out = json.loads(p.stdout.strip())
    out["_exit"] = p.returncode
    assert (out["result"] == "ALLOW") == (p.returncode == 0), out
    return out


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.projects = Path(self.tmp.name) / "projects"
        self.projects.mkdir()
        self.registry = Path(self.tmp.name) / "registry.md"
        self.registry.write_text(
            "| Project | Repository authority | Known Workspace / Server entry | Other |\n"
            "|---|---|---|---|\n"
            "| Demo | \x60seigo-gace/demo\x60 | \x60/home/admin1/projects/demo\x60 | x |\n"
            "| TGserver | \x60seigo-gace/TGserver\x60 | \x60/home/admin1/projects/TGserver\x60 | x |\n",
            encoding="utf-8",
        )
        self.master = Path(self.tmp.name) / "master.json"
        self.master.write_text(json.dumps({"repositories": [
            {"repository": "seigo-gace/debug-ai", "server_project_path": "/home/admin1/projects/debug-ai"}
        ]}))
        self.demo = self.make_repo("demo", "https://github.com/seigo-gace/demo.git")

    def make_repo(self, name, origin):
        p = self.projects / name
        p.mkdir()
        git(p, "init", "-q")
        if origin:
            git(p, "remote", "add", "origin", origin)
        return p

    def check(self, name, expected):
        out = invoke(name, self.projects, self.registry, self.master)
        self.assertEqual(out["code"], expected, out)
        self.assertEqual(out["_exit"], 0 if expected == "PROJECT_SELECT_VERIFIED" else 1)
        return out

    def test_allow_exact_registered_existing_git(self):
        self.check("demo", "PROJECT_SELECT_VERIFIED")

    def test_allow_registered_master_internal_debugai(self):
        self.make_repo("debug-ai", "git@github.com:seigo-gace/debug-ai.git")
        self.check("debug-ai", "PROJECT_SELECT_VERIFIED")

    def test_allow_registered_tgserver(self):
        self.make_repo("TGserver", "https://github.com/seigo-gace/TGserver.git")
        self.check("TGserver", "PROJECT_SELECT_VERIFIED")

    def test_deny_sibling(self):
        self.check("debug-ai-worktrees.bak-deploy-20261009", "PROJECT_NOT_REGISTERED")

    def test_deny_unregistered(self):
        self.check("evil-cu", "PROJECT_NOT_REGISTERED")

    def test_deny_missing_registered(self):
        self.check("TGserver", "PROJECT_NOT_EXISTING")

    def test_deny_traversal(self):
        self.check("../escape", "PROJECT_NAME_TRAVERSAL")

    def test_deny_plain_directory(self):
        (self.projects / "TGserver").mkdir()
        self.check("TGserver", "PROJECT_GIT_IDENTITY_UNKNOWN")

    def test_deny_missing_origin(self):
        self.make_repo("TGserver", None)
        self.check("TGserver", "PROJECT_GIT_ORIGIN_INVALID")

    def test_deny_wrong_origin(self):
        self.make_repo("TGserver", "https://github.com/other/TGserver.git")
        self.check("TGserver", "PROJECT_REPOSITORY_IDENTITY_MISMATCH")

    def test_deny_invalid_origin(self):
        self.make_repo("TGserver", "https://github.com/seigo-gace/TGserver.git.evil")
        self.check("TGserver", "PROJECT_REPOSITORY_IDENTITY_MISMATCH")

    def test_deny_symlink_to_other_registered_parent(self):
        (self.projects / "TGserver").symlink_to(self.demo, target_is_directory=True)
        self.check("TGserver", "PROJECT_PATH_ALIAS_OR_SYMLINK")

    def test_deny_symlink_outside_root(self):
        (self.projects / "TGserver").symlink_to(self.tmp.name, target_is_directory=True)
        self.check("TGserver", "PROJECT_PATH_ALIAS_OR_SYMLINK")

    def test_deny_registry_collision(self):
        self.master.write_text(json.dumps({"repositories": [
            {"repository": "other/demo", "server_project_path": "/home/admin1/projects/demo"}
        ]}))
        self.check("demo", "REGISTRY_INVALID")

    def test_deny_corrupt_registry(self):
        self.master.write_text("{bad json")
        self.check("demo", "REGISTRY_INVALID")

    def test_no_side_effects_for_denied_path(self):
        before = sorted(x.name for x in self.projects.iterdir())
        self.check("evil-cu", "PROJECT_NOT_REGISTERED")
        self.assertEqual(before, sorted(x.name for x in self.projects.iterdir()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
