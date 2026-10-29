#!/usr/bin/env python3
"""No Host mutation: fixture tests for symlink and Composer CU2 stub Workspace modes."""
import json
import tempfile
import unittest
import shutil
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
            "---\nalwaysApply: true\n---\n## G-ACE SERVER_AI\nLEAD_SELECTION=USER_SELECTED\nCONFIGURED_SUBAGENTS=AVAILABLE_WHEN_USEFUL\nGPT_CHAT_WORKFLOW=NOT_APPLICABLE\n",
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

    def test_legacy_workspace_payload_is_removed_without_touching_other_settings(self):
        self.install_stubs()
        file = self.root / 'workspace/G-ACE.code-workspace'
        data = json.loads(file.read_text())
        data['settings']['codex.serverCore.requiredStartFiles'] = ['missing/retired-design.md']
        data['settings']['user.preference'] = {'keep': True}
        file.write_text(json.dumps(data))
        self.assertIn('retired codex.serverCore', ' '.join(workspace.check(self.root)))
        workspace.repair(self.root)
        self.assertEqual(json.loads(file.read_text())['settings']['user.preference'], {'keep': True})
        self.assertEqual(workspace.check(self.root), [])

    def profile_fixture(self):
        actual = Path(__file__).resolve().parents[1]
        shutil.copytree(actual / '.cursor/templates', self.root / 'server-core/.cursor/templates')
        shutil.copy2(actual / '.cursor/rules/01_japanese_thinking.mdc', self.server_rules / '01_japanese_thinking.mdc')
        for name in ('composer.md', 'GPT-4.5Mini.md', 'gemini-flash.md', 'log.md'):
            target = self.root / '.cursor/agents' / name
            target.parent.mkdir(exist_ok=True)
            target.write_text('---\nmodel: user-selected-existing-model\n---\nold role\n')

    def test_profile_install_preserves_models_and_detects_installed_role_drift(self):
        self.install_stubs()
        self.profile_fixture()
        workspace.repair_profile(self.root)
        self.assertEqual(workspace.check(self.root), [])
        composer = self.root / '.cursor/agents/composer.md'
        self.assertIn('model: user-selected-existing-model', composer.read_text())
        composer.write_text(composer.read_text() + '\nold conflicting rule\n')
        self.assertIn('adapter drift: composer.md', ' '.join(workspace.check(self.root)))

    def test_missing_agent_model_cannot_be_silently_configured(self):
        self.install_stubs()
        self.profile_fixture()
        (self.root / '.cursor/agents/log.md').unlink()
        before = self.global_rule.read_text()
        with self.assertRaisesRegex(ValueError, 'EXISTING_AGENT_MODEL_CONFIGURATION_REQUIRED'):
            workspace.repair_profile(self.root)
        self.assertEqual(self.global_rule.read_text(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
