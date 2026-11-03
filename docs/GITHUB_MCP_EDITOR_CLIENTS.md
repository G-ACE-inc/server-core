# Shared GitHub MCP editor clients (Cursor / VS Code / VS Code Codex)

## Scope and ownership
One **server-core-owned** read-only GitHub MCP client definition:
`operations/github-mcp-editor-clients.json`. It is not a new Gateway, Host executor, queue, MCP server deployment, SSH tunnel or permissions authority. The official GitHub-hosted MCP already serves HTTPS at `https://api.githubcopilot.com/mcp/`; no new VPS service or paid subscription is introduced by this client registration.

**This is separate from server-private Phase A [Draft PR #33](https://github.com/G-ACE-inc/server-core/pull/33)**. Phase A's pinned self-hosted `gace-internal` service remains Source/CI-only and is not reachable from ordinary Windows editors without separately admitted transport. Do not substitute an invented publicly exposed URL or claim PR #33 is deployed.

## Common control boundary
- GitHub Project #1 and canonical Rule #16 (SERVER_AI) / #17 (GPT CHAT) remain authority. This MCP is **read-only** `projects,repos,issues,pull_requests,actions` for data/research/CI; GitHub Project field writes still go through the existing `scripts/github_project_control.py` with identity and readback. Server mutation stays with the existing authorized DebugAI MCP/Guarded GitOps.
- Do not copy all GitHub Project items or repo-specific MCP configuration into individual repository directories.
- Configured user clients are NOT `AUTHENTICATED`, `TOOLS_DISCOVERED`, or `E2E_PASS` merely because the configuration exists. A separate actual client read of Project #1 is needed.
- Existing same-name GitHub MCP registrations are **left untouched**. An incompatible definition causes `COLLISION` and aborts writes; it must be inspected and reconciled, not silently duplicated/overwritten.

## Client registration targets
| Client | User-global configuration | Authentication |
|---|---|---|
| Cursor Composer | `~/.cursor/mcp.json` (`mcpServers.github`) | per-process `GACE_GITHUB_MCP_TOKEN` environment variable; Cursor interpolates `${env:GACE_GITHUB_MCP_TOKEN}` |
| VS Code GitHub Copilot/Agent Host | `~/.copilot/mcp-config.json` (`mcpServers.github`) | VS Code's interactive OAuth for GitHub hosted MCP; no token persisted in JSON |
| VS Code Codex extension / Codex CLI | `~/.codex/config.toml` (`mcp_servers.github`) | `bearer_token_env_var = "GACE_GITHUB_MCP_TOKEN"`; IDE extension shares Codex CLI configuration |

Paths are **on the execution machine**: Windows PC user profile and Server Host user are different environments. Run an admitted local/Server-AI installation in each actual intended host context; writing an entry to a Linux Server home does NOT install an MCP into the Windows editor.

The `GACE_GITHUB_MCP_TOKEN` value must already exist through authorized machine Secret handling where used. The script never generates, reads, prints, persists or transfers its value; it only checks environment presence for Cursor/Codex before installation. Avoid writing bearer values to Git, Issue, artifact, history or chat. If the current Cursor `github` server already works, preserve it; reconcile its intended policy first rather than overriding.

## Single contract installation and readback
From an available checked-out `server-core` revision containing this change:

```text
python3 scripts/github_mcp_editor_clients.py plan
python3 scripts/github_mcp_editor_clients.py apply --client cursor
python3 scripts/github_mcp_editor_clients.py apply --client vscode
python3 scripts/github_mcp_editor_clients.py apply --client codex
```

Windows Python executable may be `py -3`; existing trusted SERVER_AI/Codex/Composer may run these directly on its own authenticated host. Plan is **read-only**. Apply safely merges unrelated user entries, backs up an existing file to `*.gace-backup`, refuses colliding GitHub entries and config symlinks, and never modifies the existing `operations/workspace-mcp.json` installer. Check for stored user config/Secret availability before apply. Repeated successful install is an idempotent `MATCH`.

**Acceptance sequence:** plan → no collision and approved actor/client profile → config apply → Cursor MCP available-tools discovery / VS Code MCP List Servers / Codex `codex mcp list` → read one authorized GitHub Project #1 item/repository via MCP → confirm actual field snapshot/CI → state `CLIENT_E2E=PASS`. Do not mark Source/CI tests as a real login or connected-client PASS.

## Official references
- https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md
- https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md
- https://prod.cursor.com/docs/mcp
- https://code.visualstudio.com/docs/agent-customization/mcp-servers
- https://developers.openai.com/learn/docs-mcp
