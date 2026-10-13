import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOUNDED = ROOT / "operations/github-project-bounded-host.json"
REGISTRY = ROOT / "operations/master-internal-repositories.json"

SOURCE_ONLY = {
    "G-ACE-inc/server-core",
    "seigo-gace/TGserver",
}
COMPOSE_RUNTIME = {
    "seigo-gace/debug-ai",
    "seigo-gace/webhook-gateway",
}


class RegisteredRepositoryContractTests(unittest.TestCase):
    def test_dev_job_and_master_internal_cover_same_eleven_repos(self):
        bounded = json.loads(BOUNDED.read_text(encoding="utf-8"))
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        dev = set(bounded["dev_job"]["registered_repositories"])
        master = {e["repository"] for e in registry["repositories"]}
        self.assertEqual(dev, master)
        self.assertEqual(len(dev), 11)

    def test_every_dev_job_root_matches_registry_path(self):
        bounded = json.loads(BOUNDED.read_text(encoding="utf-8"))
        registry = {e["repository"]: e for e in json.loads(REGISTRY.read_text())["repositories"]}
        for repo, entry in bounded["dev_job"]["registered_repositories"].items():
            self.assertEqual(entry["root"], registry[repo]["server_project_path"])

    def test_source_only_and_compose_runtime_classification(self):
        registry = {e["repository"]: e for e in json.loads(REGISTRY.read_text())["repositories"]}
        for repo in SOURCE_ONLY:
            self.assertEqual(registry[repo]["runtime_target"]["kind"], "source_only")
            self.assertIn("reflect", registry[repo]["allowed_operations"])
        for repo in COMPOSE_RUNTIME:
            self.assertIn("compose_file", registry[repo]["runtime_target"])
        for repo, entry in registry.items():
            if repo not in SOURCE_ONLY | COMPOSE_RUNTIME:
                self.assertEqual(entry.get("allowed_operations"), ["host.command"])


if __name__ == "__main__":
    unittest.main()
