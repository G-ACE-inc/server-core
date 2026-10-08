#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import github_mcp_editor_clients as mcp


class GitHubEditorClientsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def run_apply(self, clients=mcp.CLIENTS, token="not-a-real-token"):
        return mcp.run(home=self.home, clients=clients, apply=True,
                       environ={"GACE_GITHUB_MCP_TOKEN": token})

    def test_plan_read_only(self):
        result = mcp.run(home=self.home)
        self.assertEqual(result["status"], "PLAN_ONLY_NO_MUTATION")
        self.assertEqual(set(result["clients"].values()), {"ADD"})
        self.assertFalse(any(self.home.iterdir()))

    def test_cursor_clean_registration_without_secret(self):
        self.run_apply(("cursor",))
        parsed = json.loads((self.home / ".cursor/mcp.json").read_text())
        entry = parsed["mcpServers"]["github"]
        self.assertIn("${env:GACE_GITHUB_MCP_TOKEN}", entry["headers"]["Authorization"])
        self.assertNotIn("not-a-real-token", str(parsed))
        self.assertEqual(entry["headers"]["X-MCP-Readonly"], "true")

    def test_vscode_portable_global_uses_oauth(self):
        self.run_apply(("vscode",), token="")
        parsed = json.loads((self.home / ".copilot/mcp-config.json").read_text())
        entry = parsed["mcpServers"]["github"]
        self.assertEqual(entry["type"], "http")
        self.assertNotIn("Authorization", entry["headers"])

    def test_codex_preserves_form_and_no_secret(self):
        self.run_apply(("codex",))
        data = (self.home / ".codex/config.toml").read_text()
        self.assertNotIn("not-a-real-token", data)
        parsed = mcp.tomllib.loads(data)
        self.assertEqual(parsed["mcp_servers"]["github"]["bearer_token_env_var"],
                         "GACE_GITHUB_MCP_TOKEN")

    def test_all_three_idempotent(self):
        self.run_apply()
        before = {k: v.read_bytes() for k, v in mcp.target_paths(self.home).items()}
        again = self.run_apply()
        self.assertEqual(set(again["clients"].values()), {"MATCH"})
        self.assertEqual(before,
                         {k: v.read_bytes() for k, v in mcp.target_paths(self.home).items()})

    def test_missing_env_fails_without_files(self):
        with self.assertRaisesRegex(mcp.ClientConfigError, "TOKEN_ENV_ABSENT"):
            self.run_apply(("cursor",), token="")
        self.assertFalse(any(self.home.iterdir()))

    def test_collision_blocks_other_clients(self):
        path = mcp.target_paths(self.home)["cursor"]
        path.parent.mkdir()
        path.write_text('{"mcpServers":{"github":{"command":"my-custom-gh-mcp"}}}')
        with self.assertRaisesRegex(mcp.ClientConfigError, "COLLISION"):
            self.run_apply()
        self.assertFalse(mcp.target_paths(self.home)["codex"].exists())

    def test_existing_other_server_is_preserved_with_backup(self):
        p = mcp.target_paths(self.home)["vscode"]
        p.parent.mkdir()
        initial = '{"mcpServers":{"some-other-server":{"url":"https://example.test"}}}'
        p.write_text(initial)
        self.run_apply(("vscode",), token="")
        changed = json.loads(p.read_text())
        self.assertIn("some-other-server", changed["mcpServers"])
        self.assertIn("github", changed["mcpServers"])
        self.assertEqual(p.with_name("mcp-config.json.gace-backup").read_text(), initial)

    def test_symlink_config_rejected(self):
        target = self.home / "unrelated.json"
        target.write_text("{}")
        p = mcp.target_paths(self.home)["cursor"]
        p.parent.mkdir()
        p.symlink_to(target)
        with self.assertRaisesRegex(mcp.ClientConfigError, "SYMLINK"):
            mcp.run(home=self.home)

    def test_codex_preserves_existing_toml(self):
        p = mcp.target_paths(self.home)["codex"]
        p.parent.mkdir()
        p.write_text('model = "gpt-6"\n')
        self.run_apply(("codex",))
        config = mcp.tomllib.loads(p.read_text())
        self.assertEqual(config["model"], "gpt-6")
        self.assertIn("github", config["mcp_servers"])
        self.assertEqual(p.with_name("config.toml.gace-backup").read_text(),
                         'model = "gpt-6"\n')


if __name__ == "__main__":
    unittest.main()
