# Server Core — G-ACE Workspace Command Center

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
- DebugAI shared control route: all twelve bounded control completion gates PASS on reflected `4190f8701d989648e78c60400a9147cc6d4794ad`. Workspace registration, 13-tool discovery, health, real Server Command `QUEUED -> RUNNING -> PASS`, exact Host HEAD and 261 packaged source/image files are verified. Existing guarded GitOps deploy `gitops_0444c77ff07c828e1a835ee2` completed PASS with HTTP 200 and Docker healthy; missing Host approval is rejected. Workspace stdio uses the existing Compose container without Host Node. Remote ChatGPT direct connector registration remains NOT_VERIFIED.
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
