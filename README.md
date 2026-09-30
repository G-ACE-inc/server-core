# Server Core — G-ACE Workspace Command Center

`server-core` は、G-ACE Workspace全体の**司令室**である。

各Projectの実装本体を抱え込む場所ではない。Workspaceで作業するAI / Developerが、**どのProjectで、何を読み、どの共通Tool/MCP/Secret/KBを使い、どう検証し、どうGitHubへ残し、どのApproval Boundaryまで進めるか**を決める共通Command Centerである。

## 必ずここから開始

Workspace内の作業開始順は固定する。

```text
server-core/README.md
  -> docs/LOAD_SCOPE.md
  -> 今回必要なserver-core Authorityだけ
  -> 対象Project README
  -> 必要なDesign / Project Tree / Design Delta / System Document
  -> 対象Source / 直接依存 / 関連Test
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
- `docs/G_ACE_WORKSPACE.md` — Workspace正規運用
- `docs/STRUCTURE.md` — server-core Project Tree / Navigation

### Development / GitHub
- `CORE.md` — LibralCore開発方法論
- `SERVER_CORE_PROTOCOL.md` — 共通運用・禁止・Approval Boundary
- `docs/PROJECT_TEMPLATE.md` — Project/Document標準
- `docs/AUTO_COMMIT.md` — Commit = Work Report / Push / Remote Readback
- `docs/DEPLOY_RUNBOOK.md` — confirmed GitHub revisionからRuntime verificationまでの共通Deploy境界

### Shared Platform
- `docs/WORKSPACE_REGISTRY.md` — Project / MCP / Tool / Secret Contract / Runtime discovery
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
| Workspace運用 | `docs/G_ACE_WORKSPACE.md` |
| Git / Commit / Push | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Project / Document構成 | `docs/PROJECT_TEMPLATE.md` |
| Project / MCP / Tool / DebugAI / Secret / Runtime発見 | `docs/WORKSPACE_REGISTRY.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| 再利用KB | `docs/KB_REUSE_DESIGN.md` |
| Log / Cache / Cleanup / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| 用語 | `docs/GLOSSARY.md` |
| server-core構造 | `docs/STRUCTURE.md` |
| server-core設計判断 / 差分 | `docs/SERVER_CORE_DESIGN.md` + `docs/DESIGN_DELTA.md` |

## Workspace Mechanical Enforcement

server-core-firstを文書だけで要求せず、Workspace配線をSource/CIで検証する。

```text
scripts/init-dev-workspace.sh
  -> G-ACE.code-workspace生成
  -> server-coreを第1Folderへ固定
  -> projectsを第2Folderへ固定
  -> heavy/generated context除外
  -> projects/.cursor/rules -> server-core/.cursor/rules
  -> workspace_command_center_check.py
```

Authority: `docs/G_ACE_WORKSPACE.md`。

Source/CI verification済み:
- deterministic Workspace generation
- correct Folder order
- shared Agent-rule symlink
- invalid WorkspaceをverifierがFAILするnegative gate
- non-symlink rules pathを破壊せずfail-closed

Live `/home/admin1` Workspaceへの反映・readbackはServer Runtime状態であり、Source/CI PASSとは別に扱う。

## Documentation Contract

### README
Current completed / verified stateと入口を示す。Design正本にはしない。

### Design
Architecture / Contract / Boundary / ResponsibilityのBaseline。

Current実装へ合わせて履歴を消す上書きを禁止する。

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
- MCP;
- DebugAI;
- GitHub tools;
- reusable KB;
- Cloudflare / Hugging Face;
- Vault経由Secret / Token;
- shared development tools / skills。

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
- Workspace command-center wiring initializer/verifier: SOURCE / CI verified
- read-only Storage Audit source: SOURCE / CI verified
- DebugAI MCP source: DebugAI mainへmerge済み、source-side CI verified; Workspace registration / live runtimeは別状態
- F: reusable KB bridge/runtime: NOT_IMPLEMENTED
- generic storage cleanup mutation: NOT_IMPLEMENTED
- current server storage audit: NOT_VERIFIED
- live `/home/admin1` Workspace command-center wiring: NOT_VERIFIED after this source change

これらのRuntime pendingを理由にMD設計を未完成扱いにはしない。逆にMDが完成していてもRuntime PASSとはしない。

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