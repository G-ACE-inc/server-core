#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/init_dev_workspace_project_gate.py"


def run_gate(name: str, projects_dir: Path, registry: Path) -> dict:
    proc = subprocess.run(
        [
            "python3",
            str(GATE),
            "--name",
            name,
            "--projects-dir",
            str(projects_dir),
            "--registry-doc",
            str(registry),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    data = json.loads(line) if line.startswith("{") else {"result": "ERROR", "raw": proc.stdout, "err": proc.stderr}
    data["_exit"] = proc.returncode
    return data


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.projects = Path(self.temp.name) / "projects"
        self.projects.mkdir()
        self.registry = Path(self.temp.name) / "registry.md"
        self.registry.write_text(
            "| Project | Repository authority | Known Workspace / Server entry | X | Y |\n"
            "|---|---|---|---|---|\n"
            "| Demo | `seigo-gace/demo` | `/home/admin1/projects/demo` | a | b |\n",
            encoding="utf-8",
        )
        (self.projects / "demo").mkdir()

    def test_allow_existing_registered(self):
        out = run_gate("demo", self.projects, self.registry)
        self.assertEqual(out["result"], "ALLOW")
        self.assertEqual(out["_exit"], 0)

    def test_deny_unregistered(self):
        out = run_gate("evil-new", self.projects, self.registry)
        self.assertEqual(out["code"], "PROJECT_NOT_REGISTERED")
        self.assertEqual(out["_exit"], 1)

    def test_deny_traversal(self):
        out = run_gate("../escape", self.projects, self.registry)
        self.assertIn(out["code"], ("PROJECT_NAME_TRAVERSAL", "PROJECT_NAME_CHARSET_INVALID"))
        self.assertEqual(out["_exit"], 1)

    def test_deny_absolute(self):
        out = run_gate("/tmp/abs", self.projects, self.registry)
        self.assertIn(out["code"], ("PROJECT_NAME_CHARSET_INVALID", "PROJECT_NAME_TRAVERSAL"))
        self.assertEqual(out["_exit"], 1)

    def test_deny_not_existing_registered(self):
        out = run_gate("demo", Path(self.temp.name) / "empty_projects", self.registry)
        self.assertEqual(out["code"], "PROJECT_NOT_EXISTING")
        self.assertEqual(out["_exit"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
