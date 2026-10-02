# WORKSPACE SHARED MCP

Version: 2026-10-02

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

## Operation / Mutation Routing

MCP関連Taskを次に分離する。

```text
USE / CALL MCP
VERIFY CONFIG ONLY
VERIFY CLIENT REGISTRATION
VERIFY LIVE AVAILABILITY
REGISTER PROJECT-SCOPED MCP
CHANGE WORKSPACE-GLOBAL REGISTRATION
CHANGE MCP IMPLEMENTATION
```

これらは別Operationである。

- `USE / CALL MCP`: 原則mutationなし。MCP owner Repositoryもserver-coreもread-only。
- `VERIFY CONFIG ONLY`: `~/.cursor/mcp.json` のread-only validation。外部client commandを実行しない。
- `VERIFY CLIENT REGISTRATION`: 明示的にclient readbackが必要な場合だけCursor CLI等へ問い合わせる。
- `VERIFY LIVE AVAILABILITY`: TaskでCurrent利用可能性が必要な場合に、そのTaskを実行するclient/provider経路でauthentication / transport / interface discovery / representative callを確認する。server-core verifierのconfig/client-registration結果だけでは代用しない。
- `REGISTER PROJECT-SCOPED MCP`: consumer Project側Config/Documentがmutation候補。server-coreやMCP owner実装は原則read-only。
- `CHANGE WORKSPACE-GLOBAL REGISTRATION`: user-global MCP configのmutation。server-core Repositoryのmanifest/Document/Script変更を自動的には許可しない。server-core側Contract変更が必要なら、server-core自体の変更についてexplicit owner authorizationがあり `SERVER_CORE_MUTATION_AUTHORIZED=YES` が成立した場合だけmutation対象にする。
- `CHANGE MCP IMPLEMENTATION`: owning MCP Projectだけをmutation対象とし、server-coreは共通Contract変更が必要でも explicit owner authorization が無い限りread-only。

「MCPを使う」「MCPを検証する」「MCPをProjectへ接続する」「Workspace-global registrationを整合する」だけでserver-coreのmanifest/document/scriptやMCP owner Sourceを書き換えない。

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

Non-managed entryを確認しただけでserver-core manifestへ取り込まない。

## Installation

Workspace-global registration自体の変更が明示的に対象の場合だけ、canonical server-core checkoutから実行する。

```bash
cd /home/admin1/server-core
scripts/install-workspace-mcp.sh --apply-workspace-mcp-mutation
```

`--apply-workspace-mcp-mutation` が無い場合、Installerは変更せずfail closedする。

これは `~/.cursor/mcp.json` のruntime/client config mutation authorizationであり、server-core Repositoryへのwrite permissionではない。

Project固有MCP利用TaskやMCP実装TaskのたびにこのInstallerを実行しない。

Installer contract:
1. explicit mutation flagを要求する;
2. manifestを検証する;
3. `~/.cursor/mcp.json` が無ければ作成する;
4. server-core管理外の既存entryを保持する;
5. managed shared entryを追加/整合する;
6. 同名で異なるruntime definitionとの衝突はfail closedする;
7. mutation前にbackupを作る;
8. credential containerをmerge policyに従って保持する;
9. Provider tokenをRepositoryから書き込まない。

## Workspace Initialization

通常確認ではInitializerをread-onlyで使う。

```bash
cd /home/admin1/server-core
scripts/init-dev-workspace.sh --check
```

引数なしもread-only checkとして扱う。Workspace file、rules wiring、global MCP configを検証するが変更しない。

Workspace wiring / global MCP configを実際に修復・整合するTaskだけ、明示的にmutation modeを使う。

```bash
scripts/init-dev-workspace.sh --apply-workspace-mutation
```

Project directory作成まで含む場合は、さらにProject作成を明示する。

```bash
scripts/init-dev-workspace.sh --apply-workspace-mutation --project PROJECT_NAME --create-project
```

Project名はTaskで確定した実名を使用し、推測値を入れない。

Initializer mutation modeはWorkspace rules symlink、Workspace file、managed global MCP configを変更し得る。実行許可とserver-core Repository書換え許可は別である。

Project Source/Document更新Taskの通常手順としてInitializer mutation modeを実行しない。

## Configuration Verification

Configのみのread-only verification:

```bash
scripts/verify-workspace-mcp.sh
```

確認項目:
- global MCP file exists
- valid JSON
- required managed servers exist
- managed runtime transport definition matches manifest
- obvious plaintext credential pattern is absent

このVerifierは成功時でも `CONFIG_REGISTERED` 相当までしか証明しない。authentication / transport / interface discovery / representative call / `AVAILABLE_VERIFIED` をPASSへ昇格させない。

Client-side registration readbackがTask上必要な場合だけ:

```bash
scripts/verify-workspace-mcp.sh --client-readback
```

このoptionは利用可能なCursor CLIへread-only問い合わせを行う。Default verificationは外部client commandを起動しない。Client readbackが成功しても証明範囲はregistration stateまでであり、live availabilityではない。

Project-owned MCPのCurrent availability確認は、そのProject/client/runtime Authorityに従う。server-core verifierで代用しない。

## State Semantics

MCP状態は分離する。

```text
IMPLEMENTATION_VERIFIED
CONFIG_PRESENT / CONFIG_REGISTERED
CLIENT_REGISTRATION_VERIFIED
AUTHENTICATION_VERIFIED
TRANSPORT_VERIFIED
INTERFACE_DISCOVERY_VERIFIED
REPRESENTATIVE_CALL_PASS
AVAILABLE_VERIFIED
```

`CONFIG_PRESENT` や過去利用実績だけでCurrent `AVAILABLE_VERIFIED` としない。

逆に、Current live再検証待ちを理由に、実装済みMCPを `NOT_IMPLEMENTED` へ降格しない。

## Live Verification Responsibility

server-coreが所有するのは、Workspace共通MCPについて「どの状態を分離し、何を確認すれば利用可能と判定できるか」というverification contractである。

Current live status自体をserver-core DocumentやRegistryへ恒久的な健康状態として固定しない。Task実行時に必要なCurrent状態は、そのTaskで実際にMCPを利用するclient/provider経路からreadbackする。

Managed remote MCP（Cloudflare API / Hugging Face）のCurrent `AVAILABLE_VERIFIED` は、必要なTaskで次を満たした場合だけ成立する。

```text
CONFIG_REGISTERED=YES
CLIENT_REGISTRATION_VERIFIED=YES when client registration is relevant
AUTHENTICATION_VERIFIED=YES
TRANSPORT_VERIFIED=YES
INTERFACE_DISCOVERY_VERIFIED=YES
REPRESENTATIVE_CALL=PASS
```

代表callはTask目的に対して無害なread-only callを優先する。live verificationのためだけにProvider resource、credential、server-core Repository、consumer Projectを変更しない。

live verification failureはfailure evidenceであり、server-core修正・credential rotation・MCP implementation変更の自動許可ではない。原因ownerを特定してから対象境界へ戻す。

## DebugAI MCP Boundary

DebugAI MCP implementation/protocolはDebugAI Project Authorityが所有する。server-coreはそのowner、利用入口、registration/readback方法、availability semanticsだけを管理する。

Durable stateとして保持する区別:

```text
IMPLEMENTATION = verified by DebugAI authority
PROTOCOL / TOOL SURFACE = verified by DebugAI authority
HISTORICAL_LIVE_USE = recorded
CURRENT_SERVER / CLIENT AVAILABILITY = readback when required
```

DebugAI MCPのSource/README/付属Document更新TaskはDebugAI Repository側で行う。server-coreを先に読んだことを理由にserver-core Documentへ書かない。

個別Branch/HEAD、作業中の検証手順、セッション内の一時報告をWorkspace共通Contractへ固定しない。

## Deterministic Japanese Parser MCP Boundary

Deterministic Japanese Parser MCPはProject-owned implementation。

Global/client configでentry presenceが確認される場合でも、server-core manifest ownershipとは別状態として扱う。Current availabilityが必要なTaskでは、client registration、transport、tool discovery、representative parser callを必要範囲で確認する。

Parser implementation/Document変更はParser Project側で行う。config presence確認だけでserver-core ownershipへ移さない。

## Credential Rule

OAuth-capable remote MCPはclient/global layerの正式認証経路を使う。

Bearer token等が必要な場合は `docs/WORKSPACE_SHARED_SECRETS.md` のapproved broker contractを利用し、Project configやRepositoryへ実値を複製しない。

Credential Contract参照をcredential registration/rotation permissionと扱わない。

## Project Boundary

Project repositoryはWorkspace shared MCP entryを複製しない。

同名Project-level MCP overrideが必要な場合は、owner、理由、scope、verificationを対象Project側で明確化する。

Project-level usage/documentationをWorkspace-global contract更新へ自動昇格しない。

server-coreのWorkspace MCP contract自体を変更する必要が見つかった場合も、`SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示成立するまではread-onlyで報告・提案に留める。

## Runtime Verification

Current live availabilityがTask判断に必要な場合は、必要な範囲で次を確認する。
- actual client registration
- authentication
- transport connection
- tool/interface discovery
- representative call
- failure behavior

Config検証とLive availability検証を混同しない。

検証でfailureを発見した場合も、原因ownerを確定する前にserver-core / MCP owner / consumer Projectのいずれかへ推測修正しない。

## Non-goals

- Project codeをserver-coreへ移さない。
- Provider credential実値をGitへ保存しない。
- Project固有endpoint/pathを推測して登録しない。
- ConfigだけでCurrent runtime healthyと断定しない。
- 個別Taskの進捗ログを本Documentへ蓄積しない。
- MCP利用TaskをMCP実装変更Taskへ自動変換しない。
- explicit owner authorization無しにserver-core Repositoryを変更しない。
