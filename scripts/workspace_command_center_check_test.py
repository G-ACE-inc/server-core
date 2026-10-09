#!/usr/bin/env python3
"""No Host mutation: fixture tests for symlink and Composer CU2 stub Workspace modes."""
import json
import tempfile
import unittest
from pathlib import Path

import workspace_command_center_check as workspace


class WorkspaceRuleModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.server_rules = self.root / "server-core/.cursor/rules"
        self.server_rules.mkdir(parents=True)
        (self.server_rules / "00_agent_runtime.mdc").write_text(
            "---\nalwaysApply: true\n---\nPROFILE=SERVER_AI\n", encoding="utf-8"
        )
        (self.root / "server-core/README.md").write_text("entry\n", encoding="utf-8")
        (self.root / "server-core/docs").mkdir()
        (self.root / "server-core/docs/LOAD_SCOPE.md").write_text("router\n", encoding="utf-8")
        self.rules = self.root / "projects/.cursor/rules"
        self.rules.parent.mkdir(parents=True)
        wf = self.root / "workspace/G-ACE.code-workspace"
        wf.parent.mkdir(parents=True)
        wf.write_text(
            json.dumps(workspace.expected_workspace(self.root / "server-core", self.root / "projects")),
            encoding="utf-8",
        )
        self.global_rule = self.root / ".cursor/rules/00_agent_language_router.mdc"
        self.global_rule.parent.mkdir(parents=True)
        self.global_rule.write_text(
            "---\nalwaysApply: true\n---\n## G-ACE SERVER_AI\nCOMPOSER\n",
            encoding="utf-8",
        )

    def install_stubs(self):
        self.rules.mkdir()
        for name in workspace.STUB_NAMES:
            (self.rules / name).write_text(
                "---\nalwaysApply: false\n---\nserver-core authoritative rule redirect\n",
                encoding="utf-8",
            )

    def test_legacy_canonical_symlink_still_allowed(self):
        self.rules.symlink_to(self.server_rules, target_is_directory=True)
        self.assertEqual(workspace.check(self.root), [])

    def test_verified_multi_root_stubs_allowed(self):
        self.install_stubs()
        self.assertEqual(workspace.check(self.root), [])

    def test_inactive_stubs_without_global_router_fail(self):
        self.install_stubs()
        self.global_rule.unlink()
        self.assertIn("G-ACE user-global router missing", " ".join(workspace.check(self.root)))

    def test_global_router_without_gace_profile_fails(self):
        self.install_stubs()
        self.global_rule.write_text("---\nalwaysApply: true\n---\nother workspace\n", encoding="utf-8")
        self.assertIn("required profile/activation missing", " ".join(workspace.check(self.root)))

    def test_reactivated_project_stub_fails(self):
        self.install_stubs()
        (self.rules / "00_agent_runtime.mdc").write_text(
            "---\nalwaysApply: true\n---\nserver-core redirected\n", encoding="utf-8"
        )
        self.assertIn("is active", " ".join(workspace.check(self.root)))

    def test_missing_or_added_stub_fails(self):
        self.install_stubs()
        (self.rules / "cloudflare-operations.mdc").unlink()
        self.assertIn("stubs mismatch", " ".join(workspace.check(self.root)))
        (self.rules / "cloudflare-operations.mdc").write_text(
            "---\nalwaysApply: false\n---\nserver-core redirected\n", encoding="utf-8"
        )
        (self.rules / "bad-agent.mdc").write_text("---\nalwaysApply: true\n---\n", encoding="utf-8")
        self.assertIn("stubs mismatch", " ".join(workspace.check(self.root)))

    def test_stub_symlink_rejected(self):
        self.install_stubs()
        (self.rules / "00_agent_runtime.mdc").unlink()
        (self.rules / "00_agent_runtime.mdc").symlink_to(self.server_rules / "00_agent_runtime.mdc")
        self.assertIn("is not a regular file", " ".join(workspace.check(self.root)))

    def test_invalid_symlink_target_rejected(self):
        self.rules.symlink_to(self.root / ".cursor/rules", target_is_directory=True)
        self.assertIn("rules link target mismatch", " ".join(workspace.check(self.root)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
