"""Current shared Terminal host.command must not use retired DebugAI delegation grants."""
import inspect
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import servercore_service_deploy_socket as terminal


class CurrentTerminalAuthorityTests(unittest.TestCase):
    def test_registered_project_checkout_is_host_command_authority(self):
        source = inspect.getsource(terminal.run_host_command)
        self.assertIn('registered_repositories', source)
        self.assertIn('operations/github-project-bounded-host.json', source)
        self.assertNotIn('delegation_mode', source)
        self.assertNotIn('allowed_operations', source)

    def test_all_current_project_checkouts_have_a_host_command_root(self):
        contract = json.loads((ROOT / "operations/github-project-bounded-host.json").read_text())
        checkouts = contract["dev_job"]["registered_repositories"]
        self.assertEqual(len(checkouts), 11)
        for repository, info in checkouts.items():
            with self.subTest(repository=repository):
                self.assertTrue(info["root"].startswith("/home/admin1/"))
                self.assertTrue(info.get("allowed_branches"))


if __name__ == "__main__":
    unittest.main()
