# G-ACE WORKSPACE REGISTRY

Version: 2026-10-01
Role: server-core司令室から、Workspace内のProject・Repository・MCP・Tool・Secret Contract・KB・Runtime確認先へ最短で到達するためのDiscovery Registry。

この文書は**発見・所有・接続契約の正本**であり、Live Runtime健康状態の証明ではない。Container / Port / Domain / Deploy / Provider状態は必要時に実readbackする。

Secret / Token実値は絶対に記録しない。

## 1. Registry State Model

Capability / Project状態は次を区別する。

```text
DISCOVERED
SOURCE_VERIFIED
CONFIG_REGISTERED
RUNTIME_VERIFIED
AVAILABLE_VERIFIED
NOT_IMPLEMENTED
NOT_REGISTERED
NOT_VERIFIED
UNKNOWN
```

`SOURCE_VERIFIED` や `CONFIG_REGISTERED` を `RUNTIME_VERIFIED` と同一視しない。また、Current exact-headの再検証待ちを理由に、既に実装済み・過去利用実績ありのCapabilityを `NOT_IMPLEMENTED` / `NOT_REGISTERED` へ降格しない。

## 2. Project Registry

GitHub Repositoryが確認できる主要G-ACE Projectを記録する。Server Path / Runtimeは確認済み情報のみ記載し、未確認は推測しない。

| Project | Repository authority | Known Workspace / Server entry | Command-center role | Runtime boundary |
|---|---|---|---|---|
| server-core | `G-ACE-inc/server-core` | `/home/admin1/server-core` | Workspace Command Center | main/source authority; runtime copyは必要時readback |
| TGserver | `seigo-gace/TGserver` | `/home/admin1/projects/TGserver` | log / delivery / storage integration Project | Current runtimeはProject README + Docker/readback |
| Astera v8 | `seigo-gace/astera_v8` | `/home/admin1/projects/astera_v8` | judgment-material processing Project | Current runtimeはProject README + Docker/readback |
| Astera App | `seigo-gace/astera-app` | `/home/admin1/projects/astera-app` | application/web Project | Provider/runtime readback required |
| DebugAI | `seigo-gace/debug-ai` | independent Project/runtime | specialized debugging capability | MCP implementation/protocol verified; prior Codex use exists; current exact-head live re-verification separate |
| Webhook Gateway | `seigo-gace/webhook-gateway` | UNKNOWN until server readback | webhook/gateway Project | NOT_VERIFIED here |
| Astera KB | `seigo-gace/astera-kb` | UNKNOWN until target readback | Astera evidence/search knowledge Project | NOT_VERIFIED here |
| Astera HP | `seigo-gace/astera-hp` | Provider/runtime specific | public HP Project | Provider readback required |
| Astera Admin | `seigo-gace/astera-admini` | UNKNOWN until target readback | admin/operations application Project | NOT_VERIFIED here |
| Astera Customer AI | `seigo-gace/astera-customerAI` | Provider/runtime specific | customer guidance AI Project | NOT_VERIFIED here |
| Deterministic Japanese Parser MCP | `seigo-gace/Deterministic-Japanese-Parser-MCP` | runtime-specific | shared deterministic parser/MCP Project | availability must be checked from actual registration/runtime |
| Libral Vault | `seigo-gace/Libral-Vault` | Vault runtime contract | shared Secret broker owner | use contract is `docs/WORKSPACE_SHARED_SECRETS.md` |
| KB System | `seigo-gace/kb-system` | UNKNOWN until target readback | existing KB-related Project | do not confuse with future F: reusable-development KB without explicit integration |
| G-ACE Dev KB | `seigo-gace/gace-dev-kb` | UNKNOWN until target readback | development-KB related Repository | current implementation state requires Project readback |

Project追加時は、Repository / owner / path / responsibility / authorityを確認してから追加する。

## 3. Dispatch Rule

司令室はTaskを次のように振り分ける。

```text
Task arrives
  -> identify responsibility
  -> find owning Project in this Registry
  -> open owning Project README
  -> load required Project authority only
  -> perform work in owning Project
  -> return result through GitHub work history
```

責務が不明な場合、既存Projectを確認する前に新規Project/Moduleを作らない。

### 3.1 Shared Capability Classification

server-coreがWorkspace共通Capabilityとして管理する対象:

```text
DebugAI
MCP
KB
GitHub
Cloudflare
Hugging Face
Runtime確認
Libral Vault
Workspace Registry
Monitoring
Backup / Recovery
Search / Index
```

TGserver / webhook gatewayはShared Capabilityではなく、Project導入時のIntegration Ruleとして扱う。Libral VaultはShared Capabilityとして管理し、Project利用契約は `docs/PROJECT_INTEGRATION_RULES.md` を正とする。

### 3.2 Project Integration Contract

ProjectへTGserver / webhook gateway / Libral Vault / MCP / Toolを導入・変更するときは `docs/PROJECT_INTEGRATION_RULES.md` を確認する。

## 4. Shared MCP Registry

Workspace共通MCPはProjectごとの `.cursor/mcp.json` へ複製せず、Cursor User Global `~/.cursor/mcp.json` を共通実行入口とする。配布元は `operations/workspace-mcp.json`、導入は `scripts/install-workspace-mcp.sh`、確認は `scripts/verify-workspace-mcp.sh`。

MCPの利用可能性は「文書にある」だけでは成立しない。

最低限、実設定・認証・transport疎通・tool discovery・代表callを必要範囲で確認する。

| MCP | Owner / authority | Config authority | Purpose | Current boundary |
|---|---|---|---|---|
| Cloudflare API MCP | Cloudflare / Workspace config | `~/.cursor/mcp.json` via `operations/workspace-mcp.json` | Cloudflare操作入口 | GLOBAL_CONFIG_SOURCE_VERIFIED; live use pending |
| DebugAI MCP | `seigo-gace/debug-ai` | implementation/runtime=`seigo-gace/debug-ai`; Workspace registration/routing=`operations/workspace-mcp.json` + `operations/github-project-debugai-routing.json` | GitHub Project / 親AIから既存DebugAI MCP経由でbounded Server Command / guarded GitOpsを共通利用 | Workspace config, 13 tools, health and real bounded Server Command PASS at reflected revision; guarded deploy completion and broader DebugAI qualification remain separate |
| Reuse KB MCP | future F: KB bridge owner | future verified global config | F: reusable-development KB検索/登録 | NOT_IMPLEMENTED |
| Deterministic Japanese Parser MCP | `seigo-gace/Deterministic-Japanese-Parser-MCP` | global MCP after runtime readback | deterministic Japanese parser | repository DISCOVERED; GLOBAL_REGISTRATION_PENDING / LIVE availability NOT_VERIFIED |

### Workspace-global provider MCPs

Cloudflare API and Hugging Face official MCP are registered in the Workspace-global manifest. Project repositories should not copy these entries. OAuth/token state remains outside Git. Live availability is only promoted after discovery + representative call.

### DebugAI source / usage boundary

Current DebugAI authority records MCP stdio source/unit/real-protocol, 9 tools, health, and durable continuation surface as PASS. Master also reports prior successful Codex use of DebugAI MCP. Therefore the Capability is already implemented and has usage history.

Current distinction:

```text
repository = seigo-gace/debug-ai
MCP implementation = VERIFIED
MCP stdio / protocol = VERIFIED
MCP tool surface = 13 tools (9 original + 4 bounded control tools)
prior Codex usage = CONFIRMED_BY_MASTER
reflected Server head = 4190f8701d989648e78c60400a9147cc6d4794ad
packaged source/image parity = PASS (261 files)
Workspace configuration readback = PASS
bounded Server Command MCP request/status/Host HEAD = PASS
guarded deploy completion = PASS (gitops_0444c77ff07c828e1a835ee2)
bounded control E2E = PASS (cmd_803e4df00579d8697dda3181)
missing exact-SHA Host approval = rejected (gitops_3ede30a4f460f4d2e909a0ee)
remote ChatGPT direct MCP connector = NOT_VERIFIED
```

Current-head re-verification pending is **not** equivalent to `NOT_IMPLEMENTED` or `NOT_REGISTERED`. Historical successful use is also **not** sufficient to claim the current changing HEAD as freshly live-verified. Preserve both facts.

GitHub Project #1のserver操作は、server-coreで別executorを複製せず、`operations/github-project-debugai-routing.json` に従い既存DebugAI MCPへdispatchする。server-coreはCurrent/control/routing/approval契約を所有し、DebugAIはMCP/Server Command/GitOps実装本体を所有する。

Workspace stdio uses the existing Compose container, as specified by
`operations/workspace-mcp.json`. `scripts/verify-debugai-project-route.sh` is a
bounded verification client: it checks discovery/health, unapproved GitOps
rejection and exact Host git-head readback through the existing MCP request/status
path. It never performs a deploy or creates another executor. Cursor registration
does not by itself establish a remote ChatGPT connector.

## 5. Shared Tool / Skill Registry

| Capability | Authority / owner | Purpose | Current boundary |
|---|---|---|---|
| GitHub work report / auto commit | `docs/AUTO_COMMIT.md`, `scripts/ai-auto-commit.sh` | Diff確認・Commit・Push | IMPLEMENTED_SOURCE |
| GitHub skill resolver | `docs/GITHUB_SKILL.md`, resolver scripts | GitHub skill path resolution | IMPLEMENTED_SOURCE |
| GitHub Project Control | `operations/github-project-control.json`, Project Control scripts / workflow | owner-only CHAT/GitHub commentをbounded requestへ変換し、Generic Internal Event API経由でProject-Control専用receiverへ配送し、Personal Project #1の4 Control Fieldを更新・exact readback | Source/Test + Docker Compose runtime packaging implemented; Gateway destination Source tracked separately; Runtime network/credential/deploy/live E2E remain NOT_VERIFIED |
| Deploy routine | `docs/DEPLOY_RUNBOOK.md` | confirmed revision -> approved deploy -> runtime verify | DOCUMENTED; target runtime specific |
| Cloudflare operations | `docs/CLOUDFLARE_OPERATIONS.md`, `operations/` | Cloudflare common contract | IMPLEMENTED_CONTRACT |
| Shared Secret broker | `docs/WORKSPACE_SHARED_SECRETS.md` | Secret値をProjectへ複製せず利用 | IMPLEMENTED_CONTRACT; runtime availability must be checked |
| DebugAI | `seigo-gace/debug-ai` | specialized debugging sub-agent | source/CLI/HTTP/MCP implemented; 13 tools and shared bounded control E2E live PASS on explicitly reflected 4190f87 |
| Storage lifecycle audit | `scripts/storage_lifecycle_audit.py`, `operations/storage-lifecycle.json` | disk/log/backup/Docker read-only audit | SOURCE_VERIFIED / SERVER_RUNTIME_NOT_VERIFIED |
| Storage cleanup mutation | future approved implementation | safe deletion/rotation | NOT_IMPLEMENTED |

GitHub Project Controlの`SOURCE_IMPLEMENTED`は、固定Contract/Runner、owner-only Comment→Request、Generic Internal Event API producer、署名付きbounded receiver、final Issue result sink、Docker Compose runtime Source/Testまでを示す。Gateway destination登録、consumer token / delivery SecretのCurrent injection、receiver Runtime、VPS Current `gh` credential、実Project mutation/readbackは別Evidenceであり、E2E成立前に`AVAILABLE_VERIFIED`へ昇格しない。

Tool追加条件:
- Workspace内で反復利用する実益がある;
- ownerが明確;
- Interfaceが明確;
- permission / mutation boundaryが明確;
- failure behaviorが明確;
- availabilityを検証可能。

## 6. Shared Secret Contract Registry

値は保存しない。

| Provider / purpose | Contract identifier | Consumer | Broker / authority | Runtime boundary |
|---|---|---|---|---|
| Hugging Face | `hf-token` | `g-ace-workspace` | Libral Vault / `operations/huggingface.json` | use via Vault action; live availability Task時確認 |
| Cloudflare Account API | `cf-account-api` | `g-ace-workspace` | Libral Vault / `operations/cloudflare-account.json` | use via Vault action; live availability Task時確認 |

利用・allowlist・failure contractは `docs/WORKSPACE_SHARED_SECRETS.md` を正とする。

Secret値、Token値、Vault internal token値はRegistryへ入れない。

## 7. Reusable Development KB Registry

Target architecture:

```text
Storage target: Master PC F: 1 TB
Data authority: external KB implementation/runtime
server-core role: access / registration / lifecycle / safety contract
Direct VPS -> PC filesystem assumption: FORBIDDEN
Bridge: verified API / MCP or equivalent explicit interface required
Current bridge/runtime: NOT_IMPLEMENTED
```

Design authority: `docs/KB_REUSE_DESIGN.md`。

既存 `astera-kb` / `kb-system` / `gace-dev-kb` をF: reusable-development KBと自動的に同一視しない。統合する場合は、owner・data model・bridge・migration・authorityを正式に決める。

## 8. Runtime Discovery Contract

Runtime情報を記録または確認する場合は最低限次を分離する。

- Project
- repository / revision source
- server / provider entry
- compose project / service / container where applicable
- port / domain ownership
- health/readback method
- last verified timestamp
- verified revision
- deploy state
- known failure / recovery boundary

古いRuntime値をCurrentとして扱わない。

Current判定の優先順:

```text
actual Provider / Docker / Endpoint / repository readback
  -> target Project runtime authority
  -> Registry discovery metadata
  -> historical reports only as history
```

## 9. Availability Gate

共有Capabilityを `AVAILABLE_VERIFIED` とするには、そのCapabilityに必要な範囲で次を満たす。

```text
OWNER_KNOWN=YES
AUTHORITY_KNOWN=YES
CONFIG_PRESENT=YES when required
AUTHENTICATION_VERIFIED=YES when required
TRANSPORT_VERIFIED=YES
INTERFACE_DISCOVERY_VERIFIED=YES
REPRESENTATIVE_CALL=PASS
MUTATION_BOUNDARY_KNOWN=YES
FAILURE_BEHAVIOR_KNOWN=YES
```

未確認項目を推測でYESにしない。

## 10. Registry Update Gate

次の場合は更新要否を判定する。
- Project追加 / 削除 / rename / ownership変更
- Repository authority変更
- shared MCP / Tool追加・削除・Interface変更
- Secret Contract identifier / consumer / broker変更
- Workspace共通Runtime入口変更
- KB bridge実装・Interface変更
- capability availability stateが変わった

Registryは作業日誌ではない。時系列履歴はGitHub commit / PRへ残す。
