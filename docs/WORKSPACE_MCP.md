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
- `VERIFY CONFIG ONLY`: `~/.cursor/mcp.json` のread-only contract validation。外部client commandを実行しない。
- `VERIFY CLIENT REGISTRATION`: Task上必要な場合だけCursor CLI等へ問い合わせる。
- `VERIFY LIVE AVAILABILITY`: Taskを実行するclient/provider経路でauthentication / transport / interface discovery / representative callを確認する。
- `REGISTER PROJECT-SCOPED MCP`: consumer Project側Config/Documentがmutation候補。
- `CHANGE WORKSPACE-GLOBAL REGISTRATION`: user-global MCP configのmutation。server-core Repository mutationとは別。
- `CHANGE MCP IMPLEMENTATION`: owning MCP Project側の実装Task。

「MCPを使う」「MCPを検証する」「MCPをProjectへ接続する」だけでserver-coreやMCP owner Sourceを書き換えない。

## Managed Shared MCPs

Machine-readable manifest authority: `operations/workspace-mcp.json`。

Current managed entries:
- Cloudflare API MCP
- Hugging Face MCP

Provider bearer token/password/secret値はmanifestへ入れない。

## Existing Non-managed Entries / Client Credential Containers

Installerはserver-core管理外の既存MCP entryを保持する。

Client-global configでは、client/OAuth/providerが生成・保持した `auth` / `headers` / `env` credential containerが存在し得る。これは**client-local runtime state**でありRepository Authorityではない。

server-coreのInstaller/Verifierは:
- 既存credential containerをmerge policyに従って保持できる;
- credential値をstdout/stderrへ表示しない;
- credential値をRepository manifestへ複製しない;
- credential containerの存在だけで`AUTHENTICATION_VERIFIED`へ昇格しない。

したがってVerification Contractは「global client configにcredential文字列が一切存在しない」ことを要求しない。要求するのは、**Repository-managed manifestがprovider secret値を持たず、client configが適切なfile permissionで保護され、値を漏洩させずにmanaged transport contractを検証できること**である。

## Installation / Permission / Backup / Concurrency

Workspace-global registration自体の変更が明示的に対象の場合だけ実行する。

```bash
cd /home/admin1/server-core
scripts/install-workspace-mcp.sh --apply-workspace-mcp-mutation
```

`--apply-workspace-mcp-mutation` が無い場合は変更せずfail closedする。

Installer contract:
1. explicit mutation flagを要求;
2. manifestを検証;
3. managed entryを追加/整合;
4. unrelated existing entryを保持;
5. runtime-definition collisionはfail closed;
6. client configをowner-only permission（0600相当、既存がより厳しい場合はそれを維持）へ整合;
7. mutation前backupも同等のsecure modeで作成;
8. backup retentionはmachine contractの`backup_keep`へ制限（Current: 3）;
9. backupにはclient-local credential containerが含まれ得るため、Current Authorityとして読込・表示・commitしない;
10. Provider tokenをRepositoryから書き込まない;
11. Cursor global config directoryをsingle-writer lock scopeとし、別Installer mutationと競合した場合は待機・上書きせずfail closedする;
12. backup名とtemporary config名は同一秒・同一Host上の再実行でも衝突しない識別子を持つ。

これはWorkspace/client mutationであり、server-core Repositoryへのwrite permissionではない。

## Workspace Initialization

通常確認ではInitializerをread-onlyで使う。

```bash
cd /home/admin1/server-core
scripts/init-dev-workspace.sh --check
```

Workspace wiring / global MCP configを実際に修復するTaskだけmutation modeを使う。

```bash
scripts/init-dev-workspace.sh --apply-workspace-mutation
```

Project directory作成まで含む場合は、Taskで確定したsingle-directory Project名を指定する。

```bash
scripts/init-dev-workspace.sh --apply-workspace-mutation --project PROJECT_NAME --create-project
```

Project Source/Document更新Taskの通常手順としてInitializer mutation modeを実行しない。

## Configuration Verification

```bash
scripts/verify-workspace-mcp.sh
```

確認範囲:
- global MCP file exists;
- JSON valid;
- file permissionにgroup/other accessが無い;
- required managed servers exist;
- managed runtime transport definition matches manifest;
- Repository manifestがclient credential containerを埋め込んでいない;
- client-local credential containerは値を表示せず保持可能。

成功しても証明するのは`CONFIG_REGISTERED`相当まで。authentication / transport / interface discovery / representative call / `AVAILABLE_VERIFIED`へ昇格しない。

Client registration readbackが必要な場合だけ:

```bash
scripts/verify-workspace-mcp.sh --client-readback
```

成功しても証明範囲はclient registrationまで。

## State Semantics

```text
IMPLEMENTATION_VERIFIED
CONFIG_PRESENT
CONFIG_REGISTERED
CLIENT_REGISTRATION_VERIFIED
AUTHENTICATION_VERIFIED
TRANSPORT_VERIFIED
INTERFACE_DISCOVERY_VERIFIED
REPRESENTATIVE_CALL_PASS
AVAILABLE_VERIFIED
```

前段の存在/成功から後段を推測しない。Current live再検証待ちを理由にSource/implementation/protocolの既検証状態を未実装へ降格しない。

## Live Verification Responsibility

server-coreは「何を確認すればCurrent利用可能と判定できるか」を定義する。Current live statusそのものはTask実行時に実client/provider経路からreadbackする。

Managed remote MCPの`AVAILABLE_VERIFIED`はTaskに必要な範囲で次を満たした場合だけ成立する。

```text
CONFIG_REGISTERED=YES
CLIENT_REGISTRATION_VERIFIED=YES when applicable
AUTHENTICATION_VERIFIED=YES
TRANSPORT_VERIFIED=YES
INTERFACE_DISCOVERY_VERIFIED=YES
REPRESENTATIVE_CALL_PASS=YES
```

代表callはharmless/read-only operationを優先する。verificationのためだけにProvider resource、credential、server-core Repository、consumer Projectを変更しない。

## DebugAI / Deterministic Japanese Parser Boundary

Project-owned MCP implementationはそれぞれowning Project Authorityが所有する。server-coreはowner、利用/registration/readback入口、availability semanticsだけを管理する。

Durableに区別する。

```text
IMPLEMENTATION / PROTOCOL VERIFIED
HISTORICAL LIVE USE when recorded by owning authority
CURRENT CLIENT REGISTRATION
CURRENT LIVE AVAILABILITY
```

Global config entry presenceだけでserver-core ownershipやCurrent availabilityへ昇格しない。Source/README/付属Document変更はowning Project側で行う。

## Credential Rule

OAuth-capable remote MCPはclient/global layerの正式認証経路を使う。Bearer token等が必要な場合は `docs/WORKSPACE_SHARED_SECRETS.md` のapproved broker contractを利用し、Project Repositoryへ実値を複製しない。

Credential Contract参照をregistration/rotation permissionと扱わない。

## Project Boundary

Project repositoryはWorkspace shared MCP entryを複製しない。同名Project overrideが必要な場合はowner、理由、scope、verificationを対象Project側で明確化する。

server-core Workspace MCP contract自体の変更は、server-coreへのexplicit owner authorizationが成立した場合だけ行う。

## Non-goals

- Project codeをserver-coreへ移さない。
- Provider credential実値をGitへ保存しない。
- Project固有endpoint/pathを推測して登録しない。
- ConfigだけでCurrent runtime healthyと断定しない。
- 個別Task進捗を本Documentへ蓄積しない。
- MCP利用TaskをMCP実装変更Taskへ自動変換しない。
