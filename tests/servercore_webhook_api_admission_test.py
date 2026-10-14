import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts/servercore_webhook_api_admission.py"
spec = importlib.util.spec_from_file_location("webhook_api_admission", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def baseline():
    return {"repositories": [
        {"repository": "other/repo", "allowed_operations": ["read"], "protected": {"keep": True}},
        {"repository": "seigo-gace/webhook-gateway", "enabled": True, "revoked": False,
         "allow_production": True, "delegation_mode": "MASTER_INTERNAL_PERSISTENT",
         "server_project_path": "/home/admin1/projects/webhook-gateway",
         "remote": "https://github.com/seigo-gace/webhook-gateway.git",
         "allowed_branches": ["main"], "allowed_operations": ["docker.operation", "host.command"],
         "allowed_scopes": ["gace.docker.operation"], "effects": {"secrets": False, "destructive": False},
         "runtime_target": {
             "id": "webhook-gateway.compose", "compose_file": "docker-compose.yml",
             "compose_digest": mod.COMPOSE_DIGEST, "services": ["api", "worker", "postgres"]
         }}]}


class ProtectedWebhookAdmissionTests(unittest.TestCase):
    def test_two_step_grant_exactly_one_existing_repo(self):
        initial = baseline()
        reflected = mod.upgrade(initial, "reflect")
        self.assertEqual(initial["repositories"][1]["allowed_operations"],
                         ["docker.operation", "host.command"])
        self.assertEqual(reflected["repositories"][0], initial["repositories"][0])
        e = reflected["repositories"][1]
        self.assertEqual(e["allowed_operations"], ["docker.operation", "host.command", "reflect"])
        self.assertTrue(e["runtime_target"]["source_reflect"])
        self.assertNotIn("deploy", e["allowed_operations"])
        deployed = mod.upgrade(reflected, "deploy")
        self.assertEqual(deployed["repositories"][1]["runtime_target"]["deploy_services"], ["api"])
        self.assertIn("deploy", deployed["repositories"][1]["allowed_operations"])
        self.assertEqual(mod.upgrade(deployed, "deploy"), deployed)
        self.assertEqual(deployed["repositories"][0], initial["repositories"][0])
        self.assertFalse(deployed["repositories"][1]["effects"]["secrets"])

    def test_never_grant_deploy_before_reflect(self):
        with self.assertRaisesRegex(mod.AdmissionError, "SOURCE_REFLECT_NOT_ENABLED"):
            mod.upgrade(baseline(), "deploy")

    def test_deny_changed_identity_and_secret_authority(self):
        for key, value in [("remote", "https://github.com/evil/evil.git"),
                           ("server_project_path", "/tmp/other"), ("allow_production", False)]:
            x = baseline()
            x["repositories"][1][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(mod.AdmissionError, "TARGET_IDENTITY_CHANGED"):
                mod.upgrade(x, "reflect")
        x = baseline()
        x["repositories"][1]["effects"]["secrets"] = True
        with self.assertRaisesRegex(mod.AdmissionError, "TARGET_IDENTITY_CHANGED"):
            mod.upgrade(x, "reflect")

    def test_invalid_service_scope_fails_closed(self):
        x = mod.upgrade(baseline(), "reflect")
        x["repositories"][1]["runtime_target"]["deploy_services"] = ["api", "worker"]
        with self.assertRaisesRegex(mod.AdmissionError, "DEPLOY_SERVICES_CHANGED"):
            mod.upgrade(x, "deploy")

    def test_exact_digest_backup_and_no_other_repo_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "registry.json"
            backup = root / "backups"
            backup.mkdir()
            data = baseline()
            path.write_text(json.dumps(data) + "\n")
            original = path.read_bytes()
            digest = mod.sha256(original)
            kwargs = {"backup_dir": backup, "lock_path": root / "lock"}
            planned = mod.activate(path, digest, "reflect", **kwargs)
            self.assertTrue(planned["dry_run"])
            self.assertEqual(path.read_bytes(), original)
            result = mod.activate(path, digest, "reflect", apply=True, **kwargs)
            self.assertFalse(result["dry_run"])
            self.assertEqual(list(backup.iterdir())[0].read_bytes(), original)
            updated = json.loads(path.read_text())
            self.assertEqual(updated["repositories"][0], data["repositories"][0])
            self.assertTrue(updated["repositories"][1]["runtime_target"]["source_reflect"])
            with self.assertRaisesRegex(mod.AdmissionError, "REGISTRY_SHA_MISMATCH"):
                mod.activate(path, digest, "deploy", apply=True, **kwargs)
            self.assertEqual(json.loads(path.read_text()), updated)
            next_digest = mod.sha256(path.read_bytes())
            mod.activate(path, next_digest, "deploy", apply=True, **kwargs)
            final = json.loads(path.read_text())
            self.assertEqual(final["repositories"][1]["runtime_target"]["deploy_services"], ["api"])


if __name__ == "__main__":
    unittest.main()
