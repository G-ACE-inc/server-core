# WORKSPACE SHARED MCP

Version: 2026-10-01

## Purpose

Workspace共通MCPをProjectごとに複製せず、CursorのUser Global MCPを共通入口として利用するためのContract。

Cursor公式仕様では、Project `.cursor/mcp.json` とUser Global `~/.cursor/mcp.json` が別の設定源として存在し、Global設定は全Projectで利用できる。Project設定は必要なProject固有MCPだけを追加し、Workspace共通MCPを各Repositoryへコピーしない。

## Architecture

```text
G-ACE Workspace
      |
      v
server-core
      |
      +--> WORKSPACE_REGISTRY
      |
      +--> operations/workspace-mcp.json
      |
      v
~/.cursor/mcp.json
      |
      +-------------------------------+
      |                               |
Project A                         Project B
Project C                         Project D
      |                               |
      +---------------+---------------+
                      |
                Shared MCPs
```

## Current server-side configuration state

Server readback on 2026-10-01 confirmed that `/home/admin1/.cursor/mcp.json` contains the following global entries:

| Server | Ownership in server-core manifest | Configuration state | Live availability state |
|---|---|---|---|
| Cloudflare API | managed by `operations/workspace-mcp.json` | `CONFIG_REGISTERED`; installer/verify PASS | authentication / transport / tool discovery / representative call still `NOT_VERIFIED` |
| Hugging Face | managed by `operations/workspace-mcp.json` | `CONFIG_REGISTERED`; installer/verify PASS | authentication / transport / tool discovery / representative call still `NOT_VERIFIED` |
| GitHub | pre-existing global entry; preserved, not rewritten by current manifest | `CONFIG_PRESENT` | live Cursor-client verification remains separate |
| Deterministic Japanese Parser | pre-existing global entry; preserved, not rewritten by current manifest | `CONFIG_PRESENT` | live transport / tool discovery / representative call remain `NOT_VERIFIED` |

The installer preserves unrelated existing MCP servers. Therefore `CONFIG_PRESENT` for GitHub / Parser does not mean server-core has taken ownership of their runtime definition.

Current Server shell does not have Cursor Agent CLI installed. `agent mcp list` is therefore not used as the verification route on this host.

## Manifest-managed shared servers

| Server | Endpoint | Authentication | State |
|---|---|---|---|
| Cloudflare API | `https://mcp.cloudflare.com/mcp` | Cursor OAuth | `CONFIG_REGISTERED`; live connection pending |
| Hugging Face | `https://huggingface.co/mcp` | Provider/Client OAuth or generated client config | `CONFIG_REGISTERED`; live connection pending |

Cloudflare documents Cursor integration through its API MCP and OAuth authorization. Hugging Face provides an official MCP server for Cursor and other MCP-compatible clients.

## Why Global MCP

The previous failure mode was:

```text
Project A
  -> .cursor/mcp.json
  -> works

Project B
  -> no registration
  -> cannot use

Project C
  -> token/config missing
  -> cannot use
```

The common route is now:

```text
All Projects
   |
   v
Cursor User Global MCP
   |
   +--> Cloudflare API MCP
   +--> Hugging Face MCP
   +--> preserved pre-existing global MCP entries
```

Project-specific MCPs remain project-scoped.

## Secret / Token rule

Do not place Provider tokens in this repository or in the shared manifest.

For OAuth-capable remote MCPs, authenticate once at the global Cursor MCP layer. The Project repositories do not receive the token.

If a Provider requires a bearer token instead of OAuth, the token must come from the approved Workspace Secret Contract / Libral Vault path. Do not copy it into a Project `.cursor/mcp.json`.

## Installation

Run only from the canonical server-core checkout:

```bash
cd /home/admin1/server-core
scripts/install-workspace-mcp.sh
```

The installer:
1. validates the server-core manifest;
2. creates `~/.cursor/mcp.json` if absent;
3. preserves unrelated existing MCP servers;
4. adds the Workspace shared entries;
5. refuses a name collision with a different runtime definition;
6. creates a timestamped backup before mutation;
7. preserves existing credential containers covered by the merge policy;
8. never writes a Provider token from the repository.

## Workspace initialization

The Workspace initializer is the canonical entry for rules + managed global MCP configuration:

```bash
cd /home/admin1/server-core
scripts/init-dev-workspace.sh
```

It must run from `/home/admin1/server-core`. A duplicate checkout such as `/home/admin1/projects/server-core` is rejected before mutation. After installing the managed MCP entries, the initializer also runs `scripts/verify-workspace-mcp.sh`; configuration verification failure therefore prevents a successful initialization result.

## Verification

```bash
scripts/verify-workspace-mcp.sh
```

The verification command checks:
- global MCP file exists;
- JSON is valid;
- required manifest-managed Workspace servers exist;
- runtime transport definition matches the manifest contract;
- no obvious plaintext token pattern is embedded;
- when Cursor CLI is installed, `agent mcp list` can be used as an additional live client-side check.

A valid config is not equivalent to a live connection.

```text
CONFIG_PRESENT / CONFIG_REGISTERED
  -> AUTHENTICATION_VERIFIED
  -> TRANSPORT_VERIFIED
  -> INTERFACE_DISCOVERY_VERIFIED
  -> REPRESENTATIVE_CALL=PASS
  -> AVAILABLE_VERIFIED
```

## Project boundary

Project repositories do not need to contain these shared MCP entries.

A Project may contain a `.cursor/mcp.json` only for Project-owned or explicitly Project-scoped MCPs.

If a Project has the same server name as a global shared MCP, the Project definition takes precedence in Cursor. Therefore manifest-managed shared server names are reserved unless an explicit Project override is approved.

## DebugAI / private MCP boundary

DebugAI MCP **is implemented**. Current DebugAI authority records stdio source/unit/real-protocol verification, 9 MCP tools, health, and durable continuation surfaces as PASS. Master also reports prior successful Codex use of DebugAI, so server-core must not classify DebugAI MCP as `NOT_IMPLEMENTED`, `NOT_REGISTERED`, or as having no usage history.

The remaining boundary is narrower: **current exact-head Server/Codex live re-verification is pending**. The active DebugAI work is still in progress, and its current authority explicitly delegates real Server readback, current Codex registration readback, and representative current-head live calls to the Codex-side verification phase.

Use the following distinction:

```text
MCP_IMPLEMENTATION=VERIFIED
MCP_PROTOCOL=VERIFIED
PRIOR_CODEX_USAGE=CONFIRMED_BY_MASTER
CURRENT_EXACT_HEAD_SERVER_READBACK=PENDING
CURRENT_EXACT_HEAD_CODEX_REGISTRATION_READBACK=PENDING
CURRENT_EXACT_HEAD_REPRESENTATIVE_CALL=PENDING
```

Do not downgrade an already implemented/previously used MCP to `NOT_IMPLEMENTED` merely because the latest exact HEAD has not yet been re-verified live. Conversely, prior use is not proof that the current in-progress HEAD is live and identical; current-head availability remains a separate verification state.

Do not invent a new local path or endpoint while DebugAI is being changed. server-core owns the discovery/registration/verification contract; DebugAI owns its implementation body.

## Deterministic Japanese Parser MCP

The Server global Cursor config now has a Deterministic Japanese Parser entry. This closes only the configuration-presence boundary.

The current server-core manifest does not own or rewrite that pre-existing entry. Before promoting it to `AVAILABLE_VERIFIED`, verify the actual client execution route, authentication when required, transport, tool discovery, and at least one representative parser call. Do not infer live availability from the JSON entry alone.

## Non-goals

- No Project code moved into server-core.
- No Provider credentials stored in Git.
- No automatic Provider mutation.
- No production deployment.
- No assumption that configuration equals runtime availability.
