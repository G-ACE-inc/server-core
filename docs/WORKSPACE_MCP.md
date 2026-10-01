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

## Current shared servers

| Server | Endpoint | Authentication | State |
|---|---|---|---|
| Cloudflare API | `https://mcp.cloudflare.com/mcp` | Cursor OAuth | CONFIG_SOURCE_VERIFIED; live connection pending |
| Hugging Face | `https://huggingface.co/mcp` | Provider/Client OAuth or generated client config | CONFIG_SOURCE_VERIFIED; live connection pending |

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
   |
   +--> Hugging Face MCP
```

Project-specific MCPs remain project-scoped.

## Secret / Token rule

Do not place Provider tokens in this repository or in the shared manifest.

For OAuth-capable remote MCPs, authenticate once at the global Cursor MCP layer. The Project repositories do not receive the token.

If a Provider requires a bearer token instead of OAuth, the token must come from the approved Workspace Secret Contract / Libral Vault path. Do not copy it into a Project `.cursor/mcp.json`.

## Installation

Run from the server-core checkout:

```bash
scripts/install-workspace-mcp.sh
```

The installer:
1. validates the server-core manifest;
2. creates `~/.cursor/mcp.json` if absent;
3. preserves unrelated existing MCP servers;
4. adds the Workspace shared entries;
5. refuses a name collision with a different definition;
6. creates a timestamped backup before mutation;
7. never writes a Provider token.

## Verification

```bash
scripts/verify-workspace-mcp.sh
```

The verification command checks:
- global MCP file exists;
- JSON is valid;
- required Workspace servers exist;
- no plaintext token is embedded;
- when Cursor CLI is installed, `agent mcp list` can be used as the live client-side check.

A valid config is not equivalent to a live connection.

```text
CONFIG_PRESENT
  -> AUTHENTICATION_VERIFIED
  -> TRANSPORT_VERIFIED
  -> INTERFACE_DISCOVERY_VERIFIED
  -> REPRESENTATIVE_CALL=PASS
  -> AVAILABLE_VERIFIED
```

## Project boundary

Project repositories do not need to contain these shared MCP entries.

A Project may contain a `.cursor/mcp.json` only for Project-owned or explicitly Project-scoped MCPs.

If a Project has the same server name as a global shared MCP, the Project definition takes precedence in Cursor. Therefore shared server names are reserved by the Workspace manifest unless an explicit Project override is approved.

## DebugAI / private MCP boundary

DebugAI MCP is not added to the global manifest yet because its repository proves source/stdio protocol but does not yet prove the intended live DebugAI runtime or Workspace registration.

Do not invent a local path or endpoint.

Once the live runtime endpoint is verified, add it to the same global manifest/installer path and verify discovery + representative call.

## Deterministic Japanese Parser MCP

The Parser MCP supports stdio and Streamable HTTP, but the Workspace runtime registration has not yet been verified. Its Project/runtime endpoint must be read back before global registration.

## Non-goals

- No Project code moved into server-core.
- No Provider credentials stored in Git.
- No automatic Provider mutation.
- No production deployment.
- No assumption that configuration equals runtime availability.
