# WORKSPACE SHARED MCP

Version: 2026-10-01

## Purpose

Workspace共通MCPをProjectごとに複製せず、Cursor User Global MCPを共通入口として利用するためのContract。

Project `.cursor/mcp.json` はProject-owned / Project-scoped MCPに限定し、Workspace共通MCPはuser-global configへ集約する。

## Architecture

```text
G-ACE Workspace
      |
      v
server-core
      |
      +--> docs/WORKSPACE_REGISTRY.md
      +--> operations/workspace-mcp.json
      +--> scripts/install-workspace-mcp.sh
      +--> scripts/verify-workspace-mcp.sh
      |
      v
~/.cursor/mcp.json
      |
      +--> Workspace-managed shared MCPs
      +--> preserved pre-existing client MCP entries
```

server-coreが管理するのはWorkspace共通MCPのmanifest / install / verify contractであり、各MCP implementation bodyではない。

## Managed Shared MCPs

Current machine-readable manifest authority: `operations/workspace-mcp.json`。

Current managed entries:
- Cloudflare API MCP
- Hugging Face MCP

Provider credential値はmanifestへ入れない。

## Existing Non-managed Entries

Installerはserver-core管理外の既存MCP entryを保持する。

既存entryがglobal configに存在しても、それだけでserver-core ownership、Current runtime availability、authentication successを意味しない。

Project-owned MCPのowner / runtime / client registrationは対象Project authorityを正とする。

## Installation

Canonical server-core checkoutから実行する。

```bash
cd /home/admin1/server-core
scripts/install-workspace-mcp.sh
```

Installer contract:
1. manifestを検証する;
2. `~/.cursor/mcp.json` が無ければ作成する;
3. server-core管理外の既存entryを保持する;
4. managed shared entryを追加/整合する;
5. 同名で異なるruntime definitionとの衝突はfail closedする;
6. mutation前にbackupを作る;
7. credential containerをmerge policyに従って保持する;
8. Provider tokenをRepositoryから書き込まない。

## Workspace Initialization

```bash
cd /home/admin1/server-core
scripts/init-dev-workspace.sh
```

Initializerはcanonical checkoutからのみ実行する。Workspace rules、workspace file、managed MCP configを整合し、検証に失敗した場合は成功扱いにしない。

## Configuration Verification

```bash
scripts/verify-workspace-mcp.sh
```

確認項目:
- global MCP file exists
- valid JSON
- required managed servers exist
- managed runtime transport definition matches manifest
- obvious plaintext credential pattern is absent
- available client CLIがある場合はclient-side registrationを追加確認可能

## State Semantics

MCP状態は分離する。

```text
IMPLEMENTATION_VERIFIED
CONFIG_PRESENT / CONFIG_REGISTERED
AUTHENTICATION_VERIFIED
TRANSPORT_VERIFIED
INTERFACE_DISCOVERY_VERIFIED
REPRESENTATIVE_CALL_PASS
AVAILABLE_VERIFIED
```

`CONFIG_PRESENT` や過去利用実績だけでCurrent `AVAILABLE_VERIFIED` としない。

逆に、Current live再検証待ちを理由に、実装済みMCPを `NOT_IMPLEMENTED` へ降格しない。

## DebugAI MCP Boundary

DebugAI MCP implementation/protocolはDebugAI Project Authorityが所有する。server-coreはそのowner、利用入口、registration/readback方法、availability semanticsだけを管理する。

Durable stateとして保持する区別:

```text
IMPLEMENTATION = verified by DebugAI authority
PROTOCOL / TOOL SURFACE = verified by DebugAI authority
HISTORICAL_LIVE_USE = recorded
CURRENT_SERVER / CLIENT AVAILABILITY = readback when required
```

個別Branch/HEAD、作業中の検証手順、会話上の報告をWorkspace共通Contractへ固定しない。

## Deterministic Japanese Parser MCP Boundary

Deterministic Japanese Parser MCPはProject-owned implementation。

Global/client configでentry presenceが確認される場合でも、server-core manifest ownershipとは別状態として扱う。Current availabilityが必要なTaskでは、client registration、transport、tool discovery、representative parser callを必要範囲で確認する。

## Credential Rule

OAuth-capable remote MCPはclient/global layerの正式認証経路を使う。

Bearer token等が必要な場合は `docs/WORKSPACE_SHARED_SECRETS.md` のapproved broker contractを利用し、Project configやRepositoryへ実値を複製しない。

## Project Boundary

Project repositoryはWorkspace shared MCP entryを複製しない。

同名Project-level MCP overrideが必要な場合は、owner、理由、scope、verificationを対象Project側で明確化する。

## Runtime Verification

Current live availabilityがTask判断に必要な場合は、必要な範囲で次を確認する。
- actual client registration
- authentication
- transport connection
- tool/interface discovery
- representative call
- failure behavior

Config検証とLive availability検証を混同しない。

## Non-goals

- Project codeをserver-coreへ移さない。
- Provider credential実値をGitへ保存しない。
- Project固有endpoint/pathを推測して登録しない。
- ConfigだけでCurrent runtime healthyと断定しない。
- 個別Taskの進捗ログを本Documentへ蓄積しない。
