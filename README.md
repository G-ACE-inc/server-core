# Server Core — G-ACE Workspace Command Center

## Master Internal Persistent Delegation — Runtime verified (2026-10-08)

Fixed purpose: preserve sales/customer legacy full approval and extend only Master's
own development to persistent delegation for formally registered, verified GitHub
Project repositories. Current qualified runtime branch:
`master-internal-runtime-20261008`; exact live Source/Host/Server HEAD:
`2695a0d3714d25593de16dd0f0a21deba7c29f43`. Owner PR51/52/53 merged; exact runtime
head all six CI checks SUCCESS, canonical499/499 and real Host83/83, zero skip;
real isolated Sandbox full-suite499/499 PASS. Combined focused checks89/89 PASS.

Only `seigo-gace/debug-ai` is currently enrolled. Host entry
`dlg_master_debugai_v1` is enabled/unrevoked/no expiry and exactly matches the
canonical `operations/master-internal-repositories.json`. Mapping binds immutable
repo1386844196/nodeR_kgDOUqmQJA, Project itemPVTI_lAHODOQFoM4BEJIIzg-sWS8/control#41,
actual `/home/admin1/projects/debug-ai`, pinned Compose/services/private health and
runtime `debugai.compose`. Trusted admission/readback/audit is verified; repository
addition is available through the documented reviewed registry/admission flow.

Real automatic-receipt MCP bootstrap `gitops_74630292ae3dcf53619daa54` and explicit
persistent operation `gitops_aef98099c653326e2f702a59` both completed
QUEUED -> RUNNING -> PASS at the exact head, HTTP200 and running|healthy. Both used
Host-issued/consumed <=5-minute single-use receipts; no manual per-operation receipt
was created. Status binds Master issuer/authority/audit identity, repository/Project/
server mapping/runtime/branch/SHA/scope and consumption timestamp. Duplicate replay
was rejected with original terminal status and container unchanged. Packaged source
parity266/266; thirteen tools and bounded Server Command remain verified.

The existing finite `dlg_debugai_reflect_v1` remains byte-identical. Legacy manual
receipt consumption, publish and publish-file validation remain byte-identical and
valid/invalid compatibility tests pass. No Commercial authorization, licensing,
subscription, Customer authentication or Astera sales path changed. Existing named
volumes, private exposure and watcher/oneshot are preserved. No new executor, queue,
transport, service, shell endpoint, Host Node/Python installation or credential.

Concurrent shared-feature unified-product/telemetry work was preserved and excluded
from this reflection. PR40 remains open/draft/unmerged into
`feat/pre-server-benchmark-gates-20261001`; its newer shared source is a separate
qualification/deployment state. Direct remote ChatGPT app connector remains
NOT_VERIFIED. Master Internal CU is complete; future operations require fresh
owner/Project/mapping/branch/SHA/path/effect/status verification. Other unmapped or
unenrolled repositories fail closed. Product/spec/user-visible/public/cost/provider/
model/Secret-authority/destructive persistent decisions remain Master-owned.

Earlier Standing/source-checkpoint snapshots below are historical and do not
supersede this runtime qualification. Latest canonical Current/audit:
https://github.com/seigo-gace/debug-ai/issues/41 .


`server-core` は、G-ACE Workspace全体の**司令室**である。

Current運用の最上位Control PlaneはGitHub Project #1へ移行する。server-coreは両AI用Rule全文を抱える場所ではなく、**GitHub Projectを運用するためのbootstrap / router / control room**として、Workspace/serverの安定した入口・安全境界・shared capability・bounded runtimeを提供する。

Rule Planeは二つに分離する。
- Server AI Minimal Kernel: `G-ACE-inc/server-core#16`
- GPT CHAT Orchestrator Kernel: `G-ACE-inc/server-core#17`

Machine contract: [`operations/github-project-rule-plane.json`](operations/github-project-rule-plane.json)  
Design / loading contract: [`docs/GITHUB_PROJECT_RULE_PLANE.md`](docs/GITHUB_PROJECT_RULE_PLANE.md)

各Projectの実装本体は所有Repositoryに残す。

## 必ずここから開始

Workspace内の作業開始順は固定する。

```text
SERVER_AI
  -> server-core/README.md
  -> docs/LOAD_SCOPE.md
  -> operations/github-project-rule-plane.json
  -> Rule Plane #16 / GitHub Project Current
  -> target Repository Current
  -> 必要なAuthority / Source / Testだけ

GPT_CHAT
  -> Rule Plane #17
  -> GitHub Project Current
  -> server-core only when Workspace/server control is required
  -> target Repository Current / Evidence
```

server-coreの全正本を一括読込しない。

設計基準線: [`docs/SERVER_CORE_DESIGN.md`](docs/SERVER_CORE_DESIGN.md)  
ツール開発の**２つの必須機能／実行順：先に② CHAT→Server、既存Log成果を維持して後に①残課題**（共通設計・Current責任＝[server-core Control #10](https://github.com/G-ACE-inc/server-core/issues/10)）：**① 統合Development Log（収集→TGserver ZERO保存→検索→CHAT間復元）**は [`SERVER_CORE_DESIGN` §17](docs/SERVER_CORE_DESIGN.md#17-tool-capability-a--unified-development-log-collect-persist-search-and-restore-2026-10-10)、**② CHAT→Serverの調査・操作・安全なSource反映・Runtime証拠**は [`SERVER_CORE_DESIGN` §16](docs/SERVER_CORE_DESIGN.md#16-tool-capability-b--common-chat-to-host-controlled-reflection-design-contract-2026-10-10)。いずれもGitHub Project #1の固定目的に従う。**設計のmain反映やCIのみではLog保存・Server反映の実E2Eは未完**。
設計差分: [`docs/DESIGN_DELTA.md`](docs/DESIGN_DELTA.md)

## 司令室としての役割

server-coreはWorkspace全体について次を担当する。

1. **Task Intake / Routing**
   - 依頼内容を分類し、対象Project・Authority・必要Contextを決める。
2. **Authority / Context Control**
   - 必要な正本だけを段階的に読ませる。
3. **Project Dispatch**
   - 実作業を所有Projectへ送る。Project固有実装をserver-coreへ吸収しない。
4. **Shared Capability Control**
   - MCP / Tool / Skill / DebugAI / KB / Secret Contract / Provider Contractの発見入口を持つ。
5. **Development / Verification Governance**
   - 再利用、Design、Delta、Tree、Test、Documentation Gate、PASS条件を統一する。
6. **GitHub Work History**
   - Commit / PRを実作業履歴として残す。
7. **Runtime / Operations Governance**
   - confirmed GitHub revisionからのDeploy、Docker、Log/Cache/Cleanup、Backup/Recovery、安全境界を統一する。

## Command Flow

```text
REQUEST
  -> ROUTE
  -> LOAD REQUIRED AUTHORITY
  -> DISPATCH TO PROJECT
  -> REUSE CHECK
  -> IMPLEMENT / DEBUG
  -> VERIFY
  -> DOCUMENTATION GATE
  -> COMMIT = WORK REPORT
  -> PUSH / REMOTE READBACK / PR / CI
  -> APPROVAL BOUNDARY
  -> DEPLOY / RUNTIME VERIFY only when authorized
```

Source / Test / Commit / Push / PR / CI / Merge / Deploy / Runtime / Productionは別状態として扱う。

## Current Documentation State

司令室MDとして現在の正本セットは以下。

### Command / Routing
- `README.md` — Workspace共通Command Center入口
- `docs/SERVER_CORE_DESIGN.md` — server-core設計基準線
- `docs/DESIGN_DELTA.md` — 設計差分と理由
- `docs/LOAD_SCOPE.md` — Task routing / progressive context loading
- `docs/GITHUB_PROJECT_RULE_PLANE.md` — GitHub Project上のSERVER_AI / GPT_CHAT二層Rule運用
- `docs/MASTER_TERMINAL_COMMAND.md` — Master Terminal Copy&Paste Command / Syntax Validation / GACE_RESULT / Shell Safety契約
- `docs/G_ACE_WORKSPACE.md` — Workspace正規運用
- `docs/STRUCTURE.md` — server-core Project Tree / Navigation

### Development / GitHub
- `CORE.md` — LibralCore開発方法論
- `SERVER_CORE_PROTOCOL.md` — 共通運用・禁止・Approval Boundary
- `docs/PROJECT_TEMPLATE.md` — Project/Document標準
- `docs/AUTO_COMMIT.md` — Commit = Work Report / Push / Remote Readback
- `docs/DEPLOY_RUNBOOK.md` — confirmed GitHub revisionからRuntime verificationまでの共通Deploy境界

### Shared Platform
- `docs/WORKSPACE_REGISTRY.md` — Project / shared Capability / MCP / Tool / Secret Contract / Runtime discovery
- `docs/WORKSPACE_MCP.md` — Workspace-global MCP registration / authentication / verification
- `docs/PROJECT_INTEGRATION_RULES.md` — TGserver / webhook gateway / Vault / MCP / Tool Project導入契約
- `docs/WORKSPACE_SHARED_SECRETS.md` — Vault経由Shared Secret / Token契約
- `docs/KB_REUSE_DESIGN.md` — F: 1TB reusable-development KB設計
- `docs/STORAGE_LIFECYCLE.md` — Log / Cache / Cleanup / Backup / Recovery設計
- `docs/CLOUDFLARE_OPERATIONS.md` — Cloudflare固有運用

### Support
- `docs/GLOSSARY.md` — 正式用語
- `docs/GITHUB_FREE_MAX.md` — GitHub無料枠Task時のみ
- `docs/GITHUB_SKILL.md` — GitHub Skill resolver利用時のみ

## Task Routing

| Task | 追加で読むAuthority |
|---|---|
| 開発方法論 / 責務 / Module / 再利用 | `CORE.md` |
| 共通運用 / 禁止 / Approval Boundary | `SERVER_CORE_PROTOCOL.md` |
| Context / 読込範囲 | `docs/LOAD_SCOPE.md` |
| Master Terminal Command / Copy&Paste / GACE_RESULT / Shell Safety / Syntax Validation | `docs/MASTER_TERMINAL_COMMAND.md` |
| Workspace運用 | `docs/G_ACE_WORKSPACE.md` |
| Git / Commit / Push | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Project / Document構成 | `docs/PROJECT_TEMPLATE.md` |
| Project / shared Capability / MCP / Tool / DebugAI / Secret / Runtime発見 | `docs/WORKSPACE_REGISTRY.md` |
| Workspace共通MCPの登録 / Cursor Global MCP / 検証 | `docs/WORKSPACE_MCP.md` |
| GitHub Projectからの共通server操作routing | `operations/github-project-debugai-routing.json` + `docs/WORKSPACE_MCP.md` |
| Project導入（TGserver / webhook gateway / Vault / MCP / Tool） | `docs/PROJECT_INTEGRATION_RULES.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| 再利用KB | `docs/KB_REUSE_DESIGN.md` |
| Log / Cache / Cleanup / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| 用語 | `docs/GLOSSARY.md` |
| GitHub Project Rule Plane / AI profile routing | `docs/GITHUB_PROJECT_RULE_PLANE.md` + `operations/github-project-rule-plane.json` |
| server-core構造 | `docs/STRUCTURE.md` |
| server-core設計判断 / 差分 | `docs/SERVER_CORE_DESIGN.md` + `docs/DESIGN_DELTA.md` |

## Documentation Contract

### README
Current completed / verified stateと入口を示す。Design正本にはしない。

### Design
Architecture / Contract / Boundary / ResponsibilityのBaseline。

Current実装へ合わせて履歴が消える上書きを禁止する。

### Design Delta
Designとの差を正式採用する場合、差分・理由・Evidence・影響範囲・適用Commit・Compatibility/rollbackを残す。

### Project Tree
主要File/Directoryの責務、Entry Point、関連Design/Testを示すNavigation Index。

### System / Module Document
READMEだけでは別AI/Developerへ説明なしで引継げない完成単位のみ作成/更新する。

## Documentation Gate

作業完了前に必ず判定する。

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Requiredなのに未更新ならDocumentation Completeではない。

## GitHub = Work History Authority

Commitは単なる保存点ではなく作業報告として扱う。

必要に応じて次を後から追える状態にする。
- Purpose
- Changed
- Affected
- Verified
- Docs
- Remaining / Unverified

詳細は `docs/AUTO_COMMIT.md`。

## Shared Workspace Capabilities

共有Capabilityの発見入口は `docs/WORKSPACE_REGISTRY.md`。

server-coreが管理するのは:
- discovery;
- connection contract;
- owner;
- permission / safety boundary;
- availability / verification state;
- Workspace共通利用Rule。

Capability本体は所有Project/runtimeへ残す。

対象:
- Workspace-global MCP;
- MCP;
- DebugAI;
- GitHub tools;
- reusable KB;
- Cloudflare / Hugging Face;
- Vault経由Secret / Token;
- shared development tools / skills。

## Project Integration Contracts

Projectへ共通基盤を導入する際の標準契約は `docs/PROJECT_INTEGRATION_RULES.md` を正とする。

- TGserver / webhook gateway = Project Integration（Shared Capabilityではない）
- Libral Vault = Shared Capability + Project利用契約
- MCP / Tool = Owner / Interface / Permission / Mutation / Verification boundary

## Knowledge Base

再利用開発KBの実データTargetはMaster PC `F:` 1TB。

server-coreにはデータ本体を置かず、Access / Registration / Lifecycle / Safety Contractのみを置く。

Authority: `docs/KB_REUSE_DESIGN.md`。

## Server / Runtime

VPSはRuntime / Processing環境であり、GitHub Source履歴・Design・Documentの代替正本にしない。

本番常駐は原則Docker / Docker Compose。

Deploy Authority: `docs/DEPLOY_RUNBOOK.md`  
Storage Authority: `docs/STORAGE_LIFECYCLE.md`

Runtime値はRegistryや古い報告から推測せず、必要時に実readbackする。

## Current Source-Verified / Runtime-Pending Boundary

Source/CIで確認されているものとLive Runtimeを分離する。

- server-core command-center routing / documentation contracts: SOURCE / CI verified
- read-only Storage Audit source: SOURCE / CI verified
- DebugAI shared control route / Master Internal Persistent Delegation: current live exact `2695a0d3714d25593de16dd0f0a21deba7c29f43`, automatic MCP receipt E2E PASS, canonical499/499 / Host83/83, thirteen tools, Server Command and packaged parity266/266 verified. Prior finite Standing E2E at `cc3462d...` is retained as historical evidence; its policy remains unchanged. Remote ChatGPT direct connector remains NOT_VERIFIED.
- F: reusable KB bridge/runtime: NOT_IMPLEMENTED
- generic storage cleanup mutation: NOT_IMPLEMENTED
- current server storage audit: NOT_VERIFIED

これらのRuntime pendingを理由にMD設計を未完成扱いにはしない。逆にMDが完成していてもRuntime PASSとはしない。

## Standing Delegation

既存DebugAIのbounded Compose反映へ、Host専用Standing Delegation Policy参照をroutingする。
委任Scope内の通常技術判断はAIが完結し、Hostが既存single-use receiptを安全に発行する。
詳細は `docs/WORKSPACE_MCP.md` とowner側 `docs/GITOPS_STANDING_DELEGATION.md`。
委任Scope外のMaster-owned boundaryと直接ChatGPT connectorのavailabilityは別に維持する。

## Approval Boundary

Masterの明示指示なしに次を越えない。
- main / PR merge
- Production deploy / 公開 / 切替
- Force push / Branch削除
- destructive reset / rebase
- 既存Service停止 / recreate
- Secret変更
- Provider resource作成・変更・削除

未確認・未実行・未検証は `UNKNOWN / NOT_EXECUTED / NOT_VERIFIED` を維持する。

## Master Internal Persistent Delegation

Purpose is fixed: preserve the existing sales/customer full approval path and
extend only Master's own development to persistent delegation for verified
GitHub Project #1 repositories. Canonical Workspace registry/mapping:
`operations/master-internal-repositories.json`; routing:
`operations/github-project-debugai-routing.json`. This extends the existing
Workspace registry, not a new control plane. DebugAI owns validation/admission
implementation: `docs/MASTER_INTERNAL_PERSISTENT_DELEGATION.md` in its repository.

Each entry has verified GitHub repo numeric/node/owner/Project-item identity,
server project/path, default/allowed branches, operations/scopes, pinned Compose
runtime/services/private health/digest, effect/path policy, enabled/revoked state
and audit identity. Initial entry is DebugAI; other registered repos receive no
automatic grant. Trusted Host admission verifies and reads back an exact private
copy in the existing delegation trust root. Every execution rechecks GitHub
owner/admin/principal, Project item, mapping and exact target before a short
single-use receipt. Repo delegation has no expiry; disable/revoke is immediate.

Design delta: optional Master Internal registry lookup on the existing MCP/Host
lane. Legacy manual and finite Standing modes remain compatible; no Commercial,
licensing, Customer authentication, new executor/queue/transport/service or shell
endpoint. Source/CI and real Runtime qualification remain separate; this source
checkpoint does not claim live persistent-mode PASS. Protected product/spec/public/
provider/model/Secret/destructive persistent decisions remain Master-owned.
