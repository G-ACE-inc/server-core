# G-ACE WORKSPACE REGISTRY

Version: 2026-09-30
Role: Workspace内のAI / Developerが共有Project・Tool・MCP・Secret Contract・Runtime入口を探し回らず発見するための軽量Registry。

この文書は実Runtimeの証明ではない。Container / Port / Domain / Deploy / Provider状態は必要時に実readbackする。
Secret / Token実値は記録しない。

## 1. Projects

| Project | Repository / Authority | Workspace / Server entry | Status boundary |
|---|---|---|---|
| server-core | `G-ACE-inc/server-core` | `/home/admin1/server-core` | Workspace共通開発・運用Authority |
| TGserver | Project README / repository authority | `/home/admin1/projects/TGserver` | Project固有状態はTGserver側README/Runtimeで確認 |
| Astera v8 | Project README / repository authority | `/home/admin1/projects/astera_v8` | Project固有状態はAstera v8側README/Runtimeで確認 |
| Astera App | Project README / repository authority | `/home/admin1/projects/astera-app` | Project固有状態はAstera App側README/Runtimeで確認 |
| DebugAI | `seigo-gace/debug-ai` | independent Project/runtime | CLI / HTTP verified by DebugAI authority; MCP source+CI+stdio protocol verified on PR #22, live Workspace/runtime not registered |

Project追加時は、実在するRepository / Path / Authorityを確認してから追加する。

## 2. Shared MCP Registry

実設定の正本はWorkspace側MCP設定。文書だけで利用可能と判断しない。

| MCP | Config authority | Purpose | Current state |
|---|---|---|---|
| Cloudflare API MCP | `.cursor/mcp.json` | Cloudflare操作入口 | REGISTERED_IN_CONFIG |
| DebugAI MCP | `seigo-gace/debug-ai` PR #22 / `docs/MCP_ADAPTER.md` | DebugAIをMCP経由で利用 | SOURCE_CI_STDIO_VERIFIED / LIVE_DEBUGAI_RUNTIME_NOT_VERIFIED / WORKSPACE_NOT_REGISTERED |
| Reuse KB MCP | future KB bridge implementation | Master PC F: KB検索・登録 | NOT_IMPLEMENTED |

DebugAI MCP verified implementation boundary before its later documentation-only commits:

```text
implementation_sha = 078203e61073be99a48444ba0c3467a7143102f4
Verify             = SUCCESS
Core Verify        = SUCCESS
Public Readiness   = SUCCESS
repository tests   = 286/286 PASS
stdio handshake    = PASS
tools/list         = 9 expected tools
health tool call   = PASS
approve/apply MCP  = ABSENT
```

これはCI内の実MCP stdio protocol verificationであり、Contabo上のlive DebugAI runtime deploymentやWorkspace MCP登録を意味しない。

新規MCPをこの表に書くだけでは利用可能にならない。実設定・認証・疎通・Tool discoveryを検証してから `AVAILABLE_VERIFIED` とする。

## 3. Shared Tool / Skill Registry

| Capability | Authority | Use | Current state |
|---|---|---|---|
| GitHub work report / auto commit | `docs/AUTO_COMMIT.md`, `scripts/ai-auto-commit.sh` | 作業後のDiff確認・Commit・Push | IMPLEMENTED |
| GitHub skill resolver | `docs/GITHUB_SKILL.md`, resolver scripts | GitHub skill path解決 | IMPLEMENTED |
| Deploy routine | `docs/DEPLOY_RUNBOOK.md` | GitHub confirmed revisionから承認後Deploy | DOCUMENTED / RUNTIME_BY_TARGET |
| Cloudflare operations | `docs/CLOUDFLARE_OPERATIONS.md`, `operations/` | Cloudflare運用契約 | IMPLEMENTED_CONTRACT |
| Shared secret broker | `docs/WORKSPACE_SHARED_SECRETS.md` | Secret値をProjectへ複製せず利用 | IMPLEMENTED_CONTRACT |
| DebugAI | DebugAI repo / CLI / HTTP / MCP branch authority | specialized debugging sub-agent | CLI_HTTP_VERIFIED; MCP_SOURCE_CI_STDIO_VERIFIED; LIVE_MCP_NOT_VERIFIED |
| Storage lifecycle audit | `scripts/storage_lifecycle_audit.py`, `operations/storage-lifecycle.json` | Disk/log/backup/Docker状態のread-only監査 | IMPLEMENTED_SOURCE / SERVER_RUNTIME_NOT_VERIFIED |
| Storage cleanup mutation | future implementation | safe deletion/rotation | NOT_IMPLEMENTED |

Tool追加条件: Workspace内で反復利用する実益があり、所有者・Interface・権限・失敗時動作が明確であること。

## 4. Shared Secret Contract Registry

値は保存しない。

| Provider / purpose | Contract identifier | Consumer / boundary |
|---|---|---|
| Hugging Face | `hf-token` | `g-ace-workspace`; Vault action経由 |
| Cloudflare Account API | `cf-account-api` | Workspace共有契約; Vault action経由 |

利用方法・allowlist・request contractは `docs/WORKSPACE_SHARED_SECRETS.md` を正とする。

## 5. Knowledge / Reuse Registry

Target reusable-development KB:

```text
Storage target: Master PC F: 1 TB drive
Data authority: KB implementation side
server-core role: access / registration / lifecycle / safety contract only
VPS direct filesystem access: forbidden assumption
Bridge: verified API / MCP or equivalent explicit interface required
```

Design authority: `docs/KB_REUSE_DESIGN.md`。

## 6. Runtime Registry Rule

Runtime情報を登録する場合は最低限次を分離する。

- Project
- repository revision source
- server path
- compose project / service
- port / domain ownership
- health/readback method
- last verified timestamp / revision when recorded

古いRuntime値をCurrentとして扱わない。Current判定はDocker / Provider / Endpoint等の実readbackを優先する。

## 7. Registry Update Gate

次の場合に更新要否を判定する。

- Project追加 / 削除 / rename
- shared MCP / Tool追加・削除・Interface変更
- Secret Contract identifier / consumer / access path変更
- Workspace共通Runtime入口変更
- KB bridge実装・Interface変更

実装されていないCapabilityを `AVAILABLE` と記録しない。UNKNOWN / NOT_IMPLEMENTED / NOT_VERIFIEDを保持する。