# G-ACE WORKSPACE REGISTRY

Version: 2026-10-01
Role: server-coreからWorkspace内のProject・Repository・MCP・Tool・Credential Contract・Runtime確認先へ到達するためのDiscovery Registry。

この文書は**発見・所有・接続契約の正本**であり、Live Runtime健康状態の証明でもMutation permissionでもない。Current RuntimeがTask判断に必要な場合は実readbackする。

Credential実値は記録しない。

## 1. Registry Semantics

Registry entryは次を示す。
- owner / repository authority
- known discovery path
- role / responsibility
- config or runtime readback authority

Registry entryを見つけたことは、そのRepository / Runtime / Providerを変更してよいという意味ではない。

Project Taskでは、Registryからownerを特定した後に `TARGET_REPOSITORY`、`MUTATION_REPOSITORIES`、`READ_ONLY_REPOSITORIES` を分離する。owner Repositoryは、利用・接続・検証だけなら原則read-onlyとする。

## 2. State Model

```text
DISCOVERED
SOURCE_VERIFIED
CONFIG_PRESENT
CONFIG_REGISTERED
RUNTIME_VERIFIED
AVAILABLE_VERIFIED
NOT_IMPLEMENTED
NOT_VERIFIED
UNKNOWN
```

状態の意味:
- `SOURCE_VERIFIED`: Source / contractが検証済み。
- `CONFIG_PRESENT`: 設定が存在することを確認済み。server-core ownershipは意味しない。
- `CONFIG_REGISTERED`: server-core管理Contractとして登録済み。
- `RUNTIME_VERIFIED`: 対象Runtimeで実動作を確認済み。
- `AVAILABLE_VERIFIED`: Taskに必要なowner/config/transport/interface/representative callまで確認済み。

過去のRuntime実績とCurrent Runtime状態は分離する。Current再検証待ちだけを理由に実装済みCapabilityを `NOT_IMPLEMENTED` へ降格しない。

Stateはavailability evidenceであり、write permissionではない。

## 3. Project Registry

| Project | Repository authority | Known Workspace / Server entry | Role | Runtime readback authority |
|---|---|---|---|---|
| server-core | `G-ACE-inc/server-core` | `/home/admin1/server-core` | Workspace Command Center | repository + server readback |
| TGserver | `seigo-gace/TGserver` | `/home/admin1/projects/TGserver` | Project-owned log/delivery/storage service | Project README + Docker/readback |
| Astera v8 | `seigo-gace/astera_v8` | `/home/admin1/projects/astera_v8` | judgment-material processing Project | Project README + Docker/readback |
| Astera App | `seigo-gace/astera-app` | `/home/admin1/projects/astera-app` | application/web Project | Project/provider readback |
| DebugAI | `seigo-gace/debug-ai` | resolve from Project/runtime authority | specialized debugging capability | DebugAI authority + current runtime/client readback |
| Webhook Gateway | `seigo-gace/webhook-gateway` | readback required | Project-owned event gateway | Project README + runtime readback |
| Astera KB | `seigo-gace/astera-kb` | readback required | Astera evidence/search Project | Project authority |
| Astera HP | `seigo-gace/astera-hp` | provider/runtime specific | public HP Project | Project/provider readback |
| Astera Admin | `seigo-gace/astera-admini` | readback required | admin/operations application | Project authority |
| Astera Customer AI | `seigo-gace/astera-customerAI` | provider/runtime specific | customer guidance AI | Project/provider readback |
| Deterministic Japanese Parser MCP | `seigo-gace/Deterministic-Japanese-Parser-MCP` | resolve from actual config/runtime | deterministic parser/MCP Project | config + client/runtime readback |
| Libral Vault | `seigo-gace/Libral-Vault` | Vault contract/runtime | shared credential broker owner | Vault/provider verification |
| KB System | `seigo-gace/kb-system` | readback required | KB-related Project | Project authority |
| G-ACE Dev KB | `seigo-gace/gace-dev-kb` | readback required | development-KB Project | Project authority |

Project追加時はRepository / owner / path / responsibility / authorityを確認してから追加する。

Known pathを見つけたことだけで、そのpathへ `cd` / write / deploy / restartを行わない。Task ownerとmutation boundaryを先に確定する。

## 4. Dispatch Rule

```text
Task arrives
  -> identify responsibility
  -> find owning Project in this Registry
  -> classify owning/adjacent repositories as mutation or read-only
  -> open owning Project README
  -> load required Project authority
  -> perform work only in approved mutation repository
  -> record source/config changes in that Repository's GitHub history
```

責務が不明な場合、既存Projectを確認する前に新規Project / Moduleを作らない。

Registryに複数関連Projectが出ても、Task scopeが複数Repository mutationを要求しているとは限らない。

## 5. Shared Capability Classification

server-coreがWorkspace共通のDiscovery / Contractを管理する対象例:
- DebugAI
- MCP
- reusable KB access
- GitHub operations
- Cloudflare / Hugging Face shared access
- Libral Vault / shared credential contracts
- monitoring / backup / recovery interfaces
- search / index interfaces when shared

TGserver / webhook gateway等のProject-owned serviceはProject Integrationとして扱う。Project導入契約は `docs/PROJECT_INTEGRATION_RULES.md`。

Shared Capability ownerをRegistryで発見したことと、そのimplementation owner Repositoryを変更することを分離する。

## 6. Shared MCP Registry

Workspace共通MCPのserver-core管理設定は `operations/workspace-mcp.json`、導入は `scripts/install-workspace-mcp.sh`、設定検証は `scripts/verify-workspace-mcp.sh`。

| MCP | Owner / authority | Config authority | Purpose | Current registry boundary |
|---|---|---|---|---|
| Cloudflare API MCP | Cloudflare + Workspace contract | `operations/workspace-mcp.json` -> user global MCP | Cloudflare API access | `CONFIG_REGISTERED`; live availability readback when needed |
| Hugging Face MCP | Hugging Face + Workspace contract | `operations/workspace-mcp.json` -> user global MCP | Hugging Face access | `CONFIG_REGISTERED`; live availability readback when needed |
| DebugAI MCP | `seigo-gace/debug-ai` | DebugAI runtime/client registration | parent AIからDebugAI利用 | implementation/protocol verified; prior live use recorded; current availability must be read back |
| Deterministic Japanese Parser MCP | `seigo-gace/Deterministic-Japanese-Parser-MCP` | existing client/global config when present | deterministic parser | config presence has been observed; ownership remains Project/client-specific; current availability readback required |
| Reusable KB bridge | owning KB Project/runtime | owning KB authority | reusable asset search/fetch | implementation/registration/availability stateはowning KB authorityで確認 |

MCP availabilityは、文書やJSON entryだけでは成立しない。TaskでCurrent availabilityが必要なら、必要範囲でauthentication、transport、tool discovery、representative callを確認する。

MCPを利用・検証するTaskを、MCP owner implementation変更やWorkspace-global registration変更へ自動昇格しない。

### DebugAI state semantics

DebugAI MCPについてserver-coreが保持するのは次の区別だけ。

```text
IMPLEMENTATION = VERIFIED by DebugAI authority
PROTOCOL_SURFACE = VERIFIED by DebugAI authority
HISTORICAL_LIVE_USE = RECORDED
CURRENT_RUNTIME / CLIENT_REGISTRATION = READBACK_REQUIRED when needed
```

個別Branch/HEAD、作業中の検証手順、一時的なセッション報告はRegistryへ固定しない。

DebugAI Project TaskでREADME/Document/Sourceを変更する場合、DebugAI Repository側をmutation対象とする。Registry参照だけでserver-coreを変更しない。

## 7. Shared Tool / Operation Registry

| Capability | Authority | Purpose | Boundary |
|---|---|---|---|
| GitHub work history | `docs/AUTO_COMMIT.md`, repository scripts | Commit / Push / Remote Readback | repository policy applies |
| Deploy routine | `docs/DEPLOY_RUNBOOK.md` | confirmed revision -> deploy -> runtime verify | target runtime specific |
| Cloudflare operations | `docs/CLOUDFLARE_OPERATIONS.md` | Cloudflare common contract | Project-specific resource state readback required |
| Shared credential broker | `docs/WORKSPACE_SHARED_SECRETS.md` | use shared credentials without Project copies | broker/provider runtime verification required |
| Storage lifecycle audit | `scripts/storage_lifecycle_audit.py`, `operations/storage-lifecycle.json` | read-only disk/storage audit | source implemented; current server result task-time readback |

Tool追加条件:
- ownerが明確;
- Interfaceが明確;
- permission / mutation boundaryが明確;
- failure behaviorが明確;
- verification methodが定義可能。

Tool/Runbook entryを発見したことは、そのToolがmutating actionを実行してよいという意味ではない。

## 8. Shared Credential Contract Registry

| Provider / purpose | Contract identifier | Consumer | Broker / machine contract | Runtime verification |
|---|---|---|---|---|
| Hugging Face | `hf-token` | `g-ace-workspace` | Libral Vault / `operations/huggingface.json` | Vault + provider identity/representative call |
| Cloudflare Account API | `cf-account-api` | `g-ace-workspace` | Libral Vault / `operations/cloudflare-account.json` | Vault + provider identity/representative call |

Secret値、Token値、Vault internal credential値はRegistryへ入れない。

Contract discoveryとcredential registration/rotationを別Operationとして扱う。

## 9. Reusable Development KB Registry

server-coreはKB data/device/pathをCurrent Authorityとして固定しない。

```text
Data authority: owning KB implementation/runtime
server-core role: discovery / access contract / registration / lifecycle / safety
Bridge: explicit verified API / MCP or equivalent interface
Current availability: owning KB authority + live bridge readback
```

複数のKB Project/runtimeを自動的に同一Authority扱いしない。統合する場合はowner・data model・bridge・migration・authorityを正式に決める。

Design authority: `docs/KB_REUSE_DESIGN.md`。

KBを検索/取得するTaskとKB implementation/data/bridgeを変更するTaskを分離する。

## 10. Runtime Discovery Contract

Runtime情報を確認する場合は最低限次を分離する。
- Project
- repository / revision source
- server / provider entry
- compose project / service / container where applicable
- port / domain ownership
- health/readback method
- last verified timestamp when persisted
- verified revision
- deploy state
- known failure / recovery boundary

Current判定の優先順:

```text
actual Provider / Docker / Endpoint / repository readback
  -> target Project runtime authority
  -> Registry discovery metadata
  -> historical record
```

Runtime discovery/readbackを行ったことをdeploy/restart/provider mutation permissionと扱わない。

## 11. Availability Gate

Capabilityを `AVAILABLE_VERIFIED` とする条件はCapabilityごとに定義するが、通常は次を必要範囲で確認する。

```text
OWNER_KNOWN=YES
AUTHORITY_KNOWN=YES
CONFIG_PRESENT=YES when required
AUTHENTICATION_VERIFIED=YES when required
TRANSPORT_VERIFIED=YES when required
INTERFACE_DISCOVERY_VERIFIED=YES
REPRESENTATIVE_CALL=PASS
MUTATION_BOUNDARY_KNOWN=YES
FAILURE_BEHAVIOR_KNOWN=YES
```

`AVAILABLE_VERIFIED` は利用可能性の状態であり、Source/Config/Provider mutation権限ではない。

## 12. Registry Update Gate

次の場合は更新要否を判定する。
- Project追加 / 削除 / rename / ownership変更
- Repository authority変更
- shared MCP / Tool追加・削除・Interface変更
- credential Contract identifier / consumer / broker変更
- Workspace共通Runtime入口変更
- KB bridge Interface変更
- capabilityのdurableなavailability/ownership boundaryが変わった

Registryは作業日誌ではない。Branch/HEAD単位の作業経過はGitHub commit / PRへ残す。

Project固有のSource/Document変更だけではRegistry更新を必須にしない。
