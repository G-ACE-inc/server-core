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


def full_binding(repo: Path, **overrides: object) -> str:
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    branch = subprocess.check_output(
        ["git", "-C", str(repo), "branch", "--show-current"], text=True
    ).strip()
    doc = {
        "repository": "G-ACE-inc/server-core",
        "branch": branch,
        "head": head,
        "change_unit": "CU39",
        "mutation_owner": "composer",
        "exact_next_gate": "CI",
        "in_scope_path_prefixes": ["scripts/", "f.txt"],
    }
    doc.update(overrides)
    return json.dumps(doc)


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
        self.assertEqual(out.get("current_mission_verified"), "NO")

    def test_strict_mode_denies_missing_binding_at_mutation_entry(self):
        out = run("mutate", self.repo, env={
            "GACE_WORK_ROUTINE_REQUIRED": "1",
            "GACE_MUTATION_BINDING": "",
            "GACE_WORK_ROUTINE_TURN": "",
        })
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WORK_ROUTINE_MUTATION_BINDING_REQUIRED")

    def test_strict_mode_readonly_still_allowed(self):
        out = run("readonly", self.repo, env={
            "GACE_WORK_ROUTINE_REQUIRED": "1",
            "GACE_MUTATION_BINDING": "",
            "GACE_WORK_ROUTINE_TURN": "",
        })
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "READONLY_BYPASS")

    def test_strict_mode_binding_without_turn_receipt_denied(self):
        out = run("mutate", self.repo, env={
            "GACE_WORK_ROUTINE_REQUIRED": "1",
            "GACE_MUTATION_BINDING": full_binding(self.repo),
            "GACE_WORK_ROUTINE_TURN": "",
        })
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WORK_ROUTINE_TURN_RECEIPT_REQUIRED")

    def test_deny_malformed_binding_json(self):
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": "{invalid"})
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "BINDING_INVALID")

    def test_deny_empty_binding_object(self):
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": "{}"})
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "BINDING_INCOMPLETE")

    def test_deny_partial_binding_missing_head(self):
        binding = json.dumps({"repository": "G-ACE-inc/server-core", "branch": "fix/cu"})
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding})
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "BINDING_INCOMPLETE")

    def test_deny_wrong_repository_binding(self):
        binding = full_binding(self.repo, repository="G-ACE-inc/other")
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding})
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WRONG_MISSION_OR_CU")

    def test_deny_wrong_branch_binding(self):
        binding = full_binding(self.repo, branch="main")
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding})
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "WRONG_MISSION_OR_CU")

    def test_allow_matching_binding_identity_bound(self):
        binding = full_binding(self.repo)
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding})
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "IDENTITY_BOUND")
        self.assertEqual(out.get("current_mission_verified"), "NO")

    def test_deny_scope_drift(self):
        binding = full_binding(self.repo, in_scope_path_prefixes=["scripts/"])
        out = run(
            "mutate",
            self.repo,
            env={"GACE_MUTATION_BINDING": binding},
            paths=["README.md"],
        )
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "SCOPE_DRIFT_BLOCKED")

    def test_deny_traversal_path_normalized_as_in_scope(self):
        binding = full_binding(self.repo, in_scope_path_prefixes=["scripts/"])
        out = run(
            "mutate",
            self.repo,
            env={"GACE_MUTATION_BINDING": binding},
            paths=["../scripts/x.py"],
        )
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "SCOPE_PATH_TRAVERSAL")

    def test_deny_sibling_prefix_not_boundary(self):
        binding = full_binding(self.repo, in_scope_path_prefixes=["src"])
        out = run(
            "mutate",
            self.repo,
            env={"GACE_MUTATION_BINDING": binding},
            paths=["src-unauthorized/x.py"],
        )
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "SCOPE_DRIFT_BLOCKED")

    def test_deny_empty_paths_file_when_scope_required(self):
        binding = full_binding(self.repo)
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding}, paths=[])
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "SCOPE_PATHS_REQUIRED")

    def _load_mod(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("rh", SCRIPT)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_strict_work_routine_requires_turn_receipt(self):
        from unittest.mock import patch

        mod = self._load_mod()
        with patch.dict(os.environ, {"GACE_WORK_ROUTINE_REQUIRED": "1"}, clear=True):
            verdict = mod.evaluate_work_routine_turn_receipt()
        self.assertEqual(verdict["result"], "DENY")
        self.assertEqual(verdict["code"], "WORK_ROUTINE_TURN_RECEIPT_REQUIRED")

    def test_legacy_work_routine_receipt_optional_without_strict_mode(self):
        from unittest.mock import patch

        mod = self._load_mod()
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(mod.evaluate_work_routine_turn_receipt())

    def test_git_c_commit_is_write(self):
        mod = self._load_mod()
        self.assertTrue(mod.is_git_write_command("git -C /tmp/repo commit -m x"))

    def test_git_c_status_is_not_write(self):
        mod = self._load_mod()
        self.assertFalse(mod.is_git_write_command("git -C /tmp/repo status"))

    def test_emit_checkpoint(self):
        binding = full_binding(self.repo)
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
        self.assertIn("CURRENT_MISSION_VERIFIED: NO", proc.stdout)



    def test_parse_porcelain_rename_two_paths(self):
        from gace_mutation_rehydrate_check import parse_porcelain_v1_z  # noqa: PLC0415

        data = b"R  scripts/new.py\0scripts/old.py\0"
        self.assertEqual(parse_porcelain_v1_z(data), ["scripts/new.py", "scripts/old.py"])

    def test_parse_porcelain_rename_with_spaces(self):
        from gace_mutation_rehydrate_check import parse_porcelain_v1_z  # noqa: PLC0415

        data = "R  scripts/new name.py\0scripts/old name.py\0".encode()
        self.assertEqual(
            parse_porcelain_v1_z(data),
            ["scripts/new name.py", "scripts/old name.py"],
        )

    def test_deny_binding_prefix_traversal(self):
        binding = full_binding(self.repo, in_scope_path_prefixes=["../private"])
        out = run("mutate", self.repo, env={"GACE_MUTATION_BINDING": binding}, paths=["scripts/x.py"])
        self.assertEqual(out["result"], "DENY")
        self.assertEqual(out["code"], "BINDING_SCOPE_PREFIX_INVALID")

    def test_allow_rename_paths_under_scripts_binding(self):
        binding = full_binding(self.repo, in_scope_path_prefixes=["scripts/"])
        out = run(
            "mutate",
            self.repo,
            env={"GACE_MUTATION_BINDING": binding},
            paths=["scripts/new.py", "scripts/old.py"],
        )
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["code"], "IDENTITY_BOUND")

    def test_git_c_config_not_repo_root(self):
        mod = self._load_mod()
        root, err = mod.git_repo_root_for_command(
            "git -c core.color=false status", self.repo
        )
        self.assertIsNone(err)
        self.assertEqual(root.resolve(), self.repo.resolve())

    def test_git_multiple_c_uses_last(self):
        mod = self._load_mod()
        other = self.repo.parent / "other"
        other.mkdir(exist_ok=True)
        root, err = mod.git_repo_root_for_command(
            f"git -C {self.repo} -C {other} status", self.repo
        )
        self.assertIsNone(err)
        self.assertEqual(root.resolve(), other.resolve())

if __name__ == "__main__":
    unittest.main()
