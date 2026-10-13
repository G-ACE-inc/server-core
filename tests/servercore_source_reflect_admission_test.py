import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "servercore_source_reflect_admission.py"
spec = importlib.util.spec_from_file_location("reflect_admission", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SHA = "a" * 40


def entry(**over):
    base = {
        "repository": "G-ACE-inc/server-core",
        "enabled": True,
        "revoked": False,
        "delegation_mode": "MASTER_INTERNAL_PERSISTENT",
        "allow_production": True,
        "allowed_operations": ["reflect"],
        "allowed_branches": ["main"],
        "server_project_path": "/home/admin1/server-core",
        "remote": "https://github.com/G-ACE-inc/server-core.git",
        "runtime_target": {"id": "servercore.source", "kind": "source_only"},
    }
    base.update(over)
    return base


class ReflectAdmissionTests(unittest.TestCase):
    def test_registered_reflect_repo(self):
        admitted = mod.require_reflect({"repositories": [entry()]}, "G-ACE-inc/server-core", "main", SHA)
        self.assertEqual(admitted["root"], Path("/home/admin1/server-core"))

    def test_compose_runtime_cannot_reflect(self):
        bad = entry(runtime_target={"id": "debugai.compose", "compose_file": "compose.yaml"})
        with self.assertRaisesRegex(mod.AdmissionError, "REFLECT_RUNTIME_NOT_SOURCE_ONLY"):
            mod.require_reflect({"repositories": [bad]}, "G-ACE-inc/server-core", "main", SHA)

    def test_branch_must_be_registered(self):
        with self.assertRaisesRegex(mod.AdmissionError, "BRANCH_NOT_ALLOWED"):
            mod.require_reflect({"repositories": [entry()]}, "G-ACE-inc/server-core", "develop", SHA)


if __name__ == "__main__":
    unittest.main()
