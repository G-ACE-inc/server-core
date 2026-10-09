#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("gace_mutation_rehydrate_check.py")
ROOT = Path(__file__).resolve().parents[1]


def git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def run(mode: str, repo: Path, env: dict | None = None, paths: list[str] | None = None) -> dict:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    paths_file = None
    if paths is not None:
        tmp = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        tmp.write("\n".join(paths))
        tmp.close()
        paths_file = tmp.name
    cmd = ["python3", "-B", str(SCRIPT), "--mode", mode, "--repo-root", str(repo)]
    if paths_file:
        cmd.extend(["--paths-file", paths_file])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env=merged)
    if paths_file:
        os.unlink(paths_file)
    return json.loads(proc.stdout.strip())


class RehydrateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "server-core"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        git(self.repo, "remote", "add", "origin", "https://github.com/G-ACE-inc/server-core.git")
        (self.repo / "f.txt").write_text("x\n", encoding="utf-8")
        git(self.repo, "add", "f.txt")
        git(self.repo, "commit", "-q", "-m", "init")
        git(self.repo, "checkout", "-q", "-b", "fix/cu")

    def test_readonly_always_allow(self):
        out = run("readonly", self.repo)
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "READONLY_BYPASS")

    def test_mutate_baseline_without_binding(self):
        out = run("mutate", self.repo)
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "BASELINE_REPOSITORY_VERIFIED")

    def test_deny_wrong_repository_binding(self):
        binding = json.dumps({"repository": "G-ACE-inc/other", "branch": "fix/cu"})
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding})
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WRONG_MISSION_OR_CU")

    def test_deny_wrong_branch_binding(self):
        binding = json.dumps({"repository": "G-ACE-inc/server-core", "branch": "main"})
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding})
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WRONG_MISSION_OR_CU")

    def test_allow_matching_binding(self):
        head = subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"], text=True
        ).strip()
        binding = json.dumps(
            {
                "repository": "G-ACE-inc/server-core",
                "branch": "fix/cu",
                "head": head,
                "change_unit": "CU39",
                "mutation_owner": "composer",
            }
        )
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding})
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "MUTATION_REHYDRATE_VERIFIED")

    def test_deny_scope_drift(self):
        binding = json.dumps(
            {
                "repository": "G-ACE-inc/server-core",
                "in_scope_path_prefixes": ["scripts/"],
            }
        )
        out = run(
            "mutate",
            self.repo,
            env={"GACE_MUTATION_BINDING": binding},
            paths=["README.md"],
        )
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "SCOPE_DRIFT_BLOCKED")

    def test_emit_checkpoint(self):
        binding = json.dumps({"change_unit": "CU39", "exact_next_gate": "CI readback"})
        env = os.environ.copy()
        env["GACE_MUTATION_BINDING"] = binding
        proc = subprocess.run(
            ["python3", "-B", str(SCRIPT), "--emit-checkpoint", "--repo-root", str(self.repo)],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        self.assertIn("gace-current-checkpoint:v1", proc.stdout)
        self.assertIn("CU39", proc.stdout)


if __name__ == "__main__":
    unittest.main()
