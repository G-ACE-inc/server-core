# G-ACE WORKSPACE REGISTRY

Version: 2026-10-03
Role: server-core司令室から、Workspace内のProject・Repository・MCP・Tool・Secret Contract・KB・Runtime確認先へ最短で到達するためのDiscovery Registry。

この文書は**発見・所有・接続契約の正本**であり、Live Runtime健康状態の証明でもMutation permissionでもない。Current RuntimeがTask判断に必要な場合は実readbackする。

Secret / Token / Credential実値は記録しない。

## 1. Registry Semantics

Registry entryは次を示す。
- owner / repository authority
- known discovery path
- role / responsibility
- config or runtime readback authority

Registry entryを見つけたことは、そのRepository / Runtime / Providerを変更してよいという意味ではない。

Project Taskでは、Registryからownerを特定した後に `TARGET_REPOSITORY`、`MUTATION_REPOSITORIES`、`READ_ONLY_REPOSITORIES` を分離する。owner Repositoryは、利用・接続・検証だけなら原則read-onlyとする。

server-core自体の変更についてMasterの明示許可があり、`SERVER_CORE_MUTATION_AUTHORIZED=YES` が成立した場合だけserver-coreをmutation対象にできる。

## 2. State Model

```text
DISCOVERED
SOURCE_VERIFIED
CONFIG_PRESENT
CONFIG_REGISTERED
CLIENT_REGISTRATION_VERIFIED
AUTHENTICATION_VERIFIED
TRANSPORT_VERIFIED
INTERFACE_DISCOVERY_VERIFIED
REPRESENTATIVE_CALL_PASS
RUNTIME_VERIFIED
AVAILABLE_VERIFIED
NOT_IMPLEMENTED
NOT_REGISTERED
NOT_VERIFIED
UNKNOWN
```

状態の意味:
- `SOURCE_VERIFIED`: Source / contractが検証済み。
- `CONFIG_PRESENT`: 設定が存在することを確認済み。
- `CONFIG_REGISTERED`: server-core管理Contractとして登録済み。
- `CLIENT_REGISTRATION_VERIFIED`: Current clientがentryを認識していることをreadback済み。
- `AUTHENTICATION_VERIFIED`: Current task経路で認証成功を確認済み。
- `TRANSPORT_VERIFIED`: Current task経路でMCP transport接続を確認済み。
- `INTERFACE_DISCOVERY_VERIFIED`: Current clientから必要なtool/interfaceを確認済み。
- `REPRESENTATIVE_CALL_PASS`: Task目的に対応する無害な代表callが成功。
- `RUNTIME_VERIFIED`: 対象Runtimeで必要な実動作を確認済み。
- `AVAILABLE_VERIFIED`: Taskに必要なowner/config/authentication/transport/interface/representative callまで確認済み。

過去のRuntime実績とCurrent Runtime状態は分離する。Current再検証待ちだけを理由に実装済みCapabilityを `NOT_IMPLEMENTED` / `NOT_REGISTERED` へ降格しない。

Stateはavailability evidenceであり、write permissionではない。

## 3. Project Registry

GitHub Repositoryが確認できる主要G-ACE Projectを記録する。Server Path / Runtimeは確認済み情報のみ記載し、未確認は推測しない。

| Project | Repository authority | Known Workspace / Server entry | Role | Runtime readback authority |
|---|---|---|---|---|
| server-core | `G-ACE-inc/server-core` | `/home/admin1/server-core` | Workspace Command Center | repository + server readback |
| TGserver | `seigo-gace/TGserver` | `/home/admin1/projects/TGserver` | Project-owned log/delivery/storage service | Project README + Docker/readback |
| Astera v8 | `seigo-gace/astera_v8` | `/home/admin1/projects/astera_v8` | judgment-material processing Project | Project README + Docker/readback |
| Astera App | `seigo-gace/astera-app` | `/home/admin1/projects/astera-app` | application/web Project | Project/provider readback |
| DebugAI | `seigo-gace/debug-ai` | independent Project/runtime | specialized debugging capability | DebugAI authority + current runtime/client readback |
| Webhook Gateway | `seigo-gace/webhook-gateway` | readback required | Project-owned event gateway | Project README + runtime readback |
| Astera KB | `seigo-gace/astera-kb` | readback required | Astera evidence/search Project | Project authority |
| Astera HP | `seigo-gace/astera-hp` | provider/runtime specific | public HP Project | Project/provider readback |
| Astera Admin | `seigo-gace/astera-admini` | readback required | admin/operations application | Project authority |
| Astera Customer AI | `seigo-gace/astera-customerAI` | provider/runtime specific | customer guidance AI | Project/provider readback |
| Deterministic Japanese Parser MCP | `seigo-gace/Deterministic-Japanese-Parser-MCP` | resolve from actual config/runtime | deterministic parser/MCP Project | config + client/runtime readback |
| Libral Vault | `seigo-gace/Libral-Vault` | Vault contract/runtime | shared Secret broker owner | Vault/provider verification |
| KB System | `seigo-gace/kb-system` | readback required | KB-related Project | Project authority |
| G-ACE Dev KB | `seigo-gace/gace-dev-kb` | readback required | development-KB Project | Project authority |

Project追加時はRepository / owner / path / responsibility / authorityを確認してから追加する。

Known pathを見つけたことだけで、そのpathへwrite / deploy / restartを行わない。Task ownerとmutation boundaryを先に確定する。

## 4. Dispatch Rule

```text
Task arrives
  -> identify responsibility
  -> find owning Project in this Registry
  -> classify owning/adjacent repositories as mutation or read-only
  -> if server-core would be a mutation target, verify Master approval for server-core mutation
  -> open owning Project README
  -> load required Project authority
  -> perform work only in approved mutation repository
  -> return result through GitHub work history
```

責務が不明な場合、既存Projectを確認する前に新規Project / Moduleを作らない。

Registryに複数関連Projectが出ても、Task scopeが複数Repository mutationを要求しているとは限らない。

## 5. Shared Capability Classification

server-coreがWorkspace共通Capabilityとして管理する対象:

```text
DebugAI
MCP
KB
GitHub
Cloudflare
Hugging Face
Runtime check
Libral Vault
Workspace Registry
Monitoring
Backup / Recovery
Search / Index
```

ここでserver-coreが管理するのは、discovery、owner、connection/config contract、permission/change boundary、verification method、availability semanticsである。Capability本体はowning Project/runtimeに残す。

TGserver / webhook gatewayはShared CapabilityではなくProject-owned Integrationとして扱う。複数Projectで利用されても自動的にShared Capabilityへ分類変更しない。

Libral VaultはShared Capabilityとして管理し、Project利用契約は `docs/PROJECT_INTEGRATION_RULES.md` を正とする。

Shared Capability ownerをRegistryで発見したことと、そのimplementation owner Repositoryを変更することを分離する。

## 6. Shared MCP Registry

Workspace共通MCPのserver-core管理設定は `operations/workspace-mcp.json`、導入は `scripts/install-workspace-mcp.sh`、設定検証は `scripts/verify-workspace-mcp.sh`。

MCPの利用可能性は「文書にある」「configにある」だけでは成立しない。TaskでCurrent availabilityが必要なら、必要範囲でauthentication、transport、tool discovery、representative callを確認する。

| MCP | Owner / authority | Config authority | Purpose | Current registry boundary |
|---|---|---|---|---|
| Cloudflare API MCP | Cloudflare + Workspace contract | `operations/workspace-mcp.json` -> user global MCP | Cloudflare API access | `CONFIG_REGISTERED`; current live availability is task-time client/provider readback |
| Hugging Face MCP | Hugging Face + Workspace contract | `operations/workspace-mcp.json` -> user global MCP | Hugging Face access | `CONFIG_REGISTERED`; current live availability is task-time client/provider readback |
| DebugAI MCP | `seigo-gace/debug-ai` | DebugAI runtime/client registration | DebugAIを親AIからMCP利用 | implementation/protocol verified; prior live use recorded; current exact-head live availability is separate readback |
| Deterministic Japanese Parser MCP | `seigo-gace/Deterministic-Japanese-Parser-MCP` | actual client/global config when present | deterministic Japanese parser | config/registration/runtime stateをTask時にreadback |
| Reuse KB MCP | F: reusable-development KB bridge owner | future verified config | reusable-development KB検索/登録 | bridge/runtime verificationが成立するまで `NOT_IMPLEMENTED` / `NOT_VERIFIED` を維持 |

`scripts/verify-workspace-mcp.sh` のdefault結果はconfig-level evidence、`--client-readback` はregistration-level evidenceであり、どちらも単独では `AVAILABLE_VERIFIED` にしない。

MCPを利用・検証するTaskを、MCP owner implementation変更やWorkspace-global registration変更へ自動昇格しない。

### DebugAI state semantics

```text
IMPLEMENTATION = VERIFIED by DebugAI authority
MCP_PROTOCOL = VERIFIED by DebugAI authority
9_TOOLS = VERIFIED by DebugAI authority
HISTORICAL_LIVE_USE = RECORDED
CURRENT_EXACT_HEAD_LIVE_REVERIFY = PENDING / READBACK_REQUIRED when needed
```

Current exact-head live再検証待ちは `NOT_IMPLEMENTED` / `NOT_REGISTERED` と同義ではない。過去利用実績だけでCurrent changing HEADをfresh live verifiedとも扱わない。

DebugAIを使うTaskでは、既に取得済みのEvidence / Tool結果 / prior verified stateを再利用し、同じ調査をServer AIへ重複実行させない。

## 7. Shared Tool / Skill Registry

| Capability | Authority / owner | Purpose | Current boundary |
|---|---|---|---|
| GitHub work report / auto commit | `docs/AUTO_COMMIT.md`, `scripts/ai-auto-commit.sh` | Diff確認・Commit・Push | source implemented; Repository policy applies |
| GitHub skill resolver | `docs/GITHUB_SKILL.md`, resolver scripts | GitHub skill path resolution | source implemented |
| GitHub Project Control | `operations/github-project-control.json`, `scripts/github_project_control.py`, `.github/workflows/github-project-control-request.yml` | owner-only CHAT/GitHub commentをbounded requestへ変換・検証し、Personal Project #1の4 Control Fieldを既存VPS `gh`認証で更新・exact readback | request-validation source implemented / automatic GitHub→VPS execution and runtime E2E `NOT_VERIFIED` |
| Deploy routine | `docs/DEPLOY_RUNBOOK.md` | confirmed revision -> approved deploy -> runtime verify | target runtime specific |
| Cloudflare operations | `docs/CLOUDFLARE_OPERATIONS.md`, `operations/` | Cloudflare common contract | Project-specific resource state readback required |
| Shared Secret broker | `docs/WORKSPACE_SHARED_SECRETS.md` | Secret値をProjectへ複製せず利用 | broker/provider runtime verification required |
| DebugAI | `seigo-gace/debug-ai` | specialized debugging sub-agent | implementation/protocol verified; current live state separate |
| Storage lifecycle audit | `scripts/storage_lifecycle_audit.py`, `operations/storage-lifecycle.json` | disk/log/backup/Docker read-only audit | source implemented; current server result task-time readback |
| Storage cleanup mutation | future approved implementation | safe deletion/rotation | NOT_IMPLEMENTED |

GitHub Project Controlの`SOURCE_IMPLEMENTED`はContract/Runner/owner-only Comment→Request validation Workflow/TestのSource状態だけを示す。Issue Commentからのrequest検証はProject mutationではない。GitHub→VPS execution、VPS Current credential、実Project mutation/readbackは別Evidenceであり、E2E成立前に`AVAILABLE_VERIFIED`へ昇格しない。

Tool追加条件:
- Workspace内で反復利用する実益がある;
- ownerが明確;
- Interfaceが明確;
- permission / mutation boundaryが明確;
- failure behaviorが明確;
- availability / verification methodが定義可能。

Tool/Runbook entryを発見したことは、そのToolがmutating actionを実行してよいという意味ではない。

## 8. Shared Secret Contract Registry

値は保存しない。

| Provider / purpose | Contract identifier | Consumer | Broker / authority | Runtime boundary |
|---|---|---|---|---|
| Hugging Face | `hf-token` | `g-ace-workspace` | Libral Vault / `operations/huggingface.json` | use via Vault action; live availability Task時確認 |
| Cloudflare Account API | `cf-account-api` | `g-ace-workspace` | Libral Vault / `operations/cloudflare-account.json` | use via Vault action; live availability Task時確認 |

利用・allowlist・failure contractは `docs/WORKSPACE_SHARED_SECRETS.md` を正とする。

Secret値、Token値、Vault internal token値はRegistryへ入れない。Contract discoveryとcredential registration/rotationを別Operationとして扱う。

## 9. Reusable Development KB Registry

Target architecture:

```text
Storage target: Master PC F: 1 TB
Data authority: external KB implementation/runtime
server-core role: access / registration / lifecycle / safety contract
Direct VPS -> PC filesystem assumption: FORBIDDEN
Bridge: verified API / MCP or equivalent explicit interface required
Current bridge/runtime: NOT_IMPLEMENTED until verified
```

Design authority: `docs/KB_REUSE_DESIGN.md`。

既存 `astera-kb` / `kb-system` / `gace-dev-kb` をF: reusable-development KBと自動的に同一視しない。統合する場合はowner・data model・bridge・migration・authorityを正式に決める。

KBを検索/取得するTaskとKB implementation/data/bridgeを変更するTaskを分離する。

## 10. Runtime Discovery Contract

Runtime情報を記録または確認する場合は最低限次を分離する。
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

共有Capabilityを `AVAILABLE_VERIFIED` とするには、そのCapabilityに必要な範囲で次を満たす。

```text
OWNER_KNOWN=YES
AUTHORITY_KNOWN=YES
CONFIG_PRESENT=YES when required
CLIENT_REGISTRATION_VERIFIED=YES when required
AUTHENTICATION_VERIFIED=YES when required
TRANSPORT_VERIFIED=YES when required
INTERFACE_DISCOVERY_VERIFIED=YES
REPRESENTATIVE_CALL=PASS
MUTATION_BOUNDARY_KNOWN=YES
FAILURE_BEHAVIOR_KNOWN=YES
```

未確認項目を推測でYESにしない。`AVAILABLE_VERIFIED` は利用可能性の状態であり、Source/Config/Provider mutation権限ではない。

Current live evidenceには確認時点と確認経路が必要であり、過去の成功を無期限のCurrent状態として再利用しない。ただしCurrent再検証待ちを理由に、Source/implementation/protocolの既検証状態まで否定しない。

## 12. Registry Update Gate

次の場合は更新要否を判定する。
- Project追加 / 削除 / rename / ownership変更
- Repository authority変更
- shared MCP / Tool追加・削除・Interface変更
- Secret Contract identifier / consumer / broker変更
- Workspace共通Runtime入口変更
- KB bridge実装・Interface変更
- capabilityのdurableなavailability/ownership boundaryが変わった

Registryは作業日誌ではない。Branch/HEAD単位の作業経過はGitHub commit / PRへ残す。

Project固有のSource/Document変更だけではRegistry更新を必須にしない。
