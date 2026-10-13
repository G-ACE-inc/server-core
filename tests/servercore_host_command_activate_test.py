"""Regression tests for the single-command Host activation helper."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

path = Path(__file__).resolve().parents[1] / "scripts/servercore_host_command_activate.py"
spec = importlib.util.spec_from_file_location("host_command_activate", path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class HostCommandActivationTests(unittest.TestCase):
    def test_registry_authority_is_unchanged_on_sha_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "server-core"
            root.mkdir()
            (root / ".git").mkdir()
            registry = root / "registry.json"
            source = {"repositories": [{"repository": "x/y"}]}
            registry.write_text(json.dumps(source))
            backup = Path(d) / "backup"
            with patch.object(m, "ROOT", root), patch.object(m, "REGISTRY", registry), \
                 patch.object(m, "BACKUP", backup), patch.object(m, "cmd", return_value=SimpleNamespace(stdout="a"*40, returncode=0)), \
                 patch("sys.argv", ["activate", "b"*40]):
                self.assertEqual(m.main(), 1)
            self.assertEqual(json.loads(registry.read_text()), source)
            self.assertFalse(backup.exists())

    def test_pinned_registered_repo_set(self):
        self.assertEqual(m.REPOS, {"seigo-gace/debug-ai", "G-ACE-inc/server-core",
                                  "seigo-gace/TGserver", "seigo-gace/webhook-gateway"})
        self.assertEqual(len(m.EXPECTED_BEFORE), 64)

if __name__ == "__main__":
    unittest.main()
