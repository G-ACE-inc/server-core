# Server Core — G-ACE Workspace共通開発・運用基盤

`server-core` は、G-ACE Workspace内の全ProjectでAI・開発者が同じ入口、同じ開発ルール、同じGitHub履歴、同じ共有Tool/Secret契約、同じServer運用境界を使うための共通基盤である。

各Project固有の実装・Design・System仕様をserver-coreへ集約しない。server-coreは共通標準と共通入口を管理する。

## 作業開始 — 必ずここから

Workspace内で作業を開始するAI / Developerは、最初にこのREADMEを入口とする。

次に `docs/LOAD_SCOPE.md` を読み、**今回の作業に必要なserver-core正本だけ**を選ぶ。全正本を一括で読まない。

```text
server-core/README.md
  -> docs/LOAD_SCOPE.md
  -> 今回必要なserver-core正本だけ
  -> 対象Project README
  -> 必要なDesign / Project Tree / Design Delta / System Document
  -> 対象Source / 直接依存 / 関連Test
```

設計基準線: [`docs/SERVER_CORE_DESIGN.md`](docs/SERVER_CORE_DESIGN.md)

## Current Completed / Verified Scope

Source/CIで確認済み:
- server-core起点のWorkspace Routing
- progressive context loading
- README / Design / Tree / Delta / System Document運用
- Commit = work report
- confirmed GitHub revisionを起点にするDeploy contract
- shared Project / MCP / Tool / Secret-contract Discovery Registry
- F: 1 TB reusable-development KB Design Baseline
- Storage / Log / Cache / Backup / Recovery Design Baseline
- read-only Storage Lifecycle Audit source + deterministic self-test
- DebugAI MCP AdapterのSource / CI / stdio Protocol verification（DebugAI PR #22。Live Runtime/Workspace登録は未実施）

未実装 / 未Runtime検証:
- DebugAI MCPのContabo Live Runtime接続 / Workspace登録
- Reuse KB API/MCP bridge
- F: KB runtime/data store
- Storage cleanup mutation / automatic deletion
- latest Server storage audit実行

Source/CI PASSをServer Runtime PASSとして扱わない。

## 作業ルーティング

| 今回の作業 | 追加で読む正本 |
|---|---|
| 開発方法論 / 責務 / Module / 再利用 | `CORE.md` |
| 共通運用・禁止事項・Server運用境界 | `SERVER_CORE_PROTOCOL.md` |
| Context / 読込範囲 | `docs/LOAD_SCOPE.md` |
| Workspace運用 | `docs/G_ACE_WORKSPACE.md` |
| GitHub commit / push | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Project / Repository構成 | `docs/PROJECT_TEMPLATE.md` |
| Shared Project / MCP / Tool / Secret入口 | `docs/WORKSPACE_REGISTRY.md` |
| 再利用KB設計 | `docs/KB_REUSE_DESIGN.md` |
| Log / Cache / Cleanup / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| 用語 | `docs/GLOSSARY.md` |
| server-core構造 | `docs/STRUCTURE.md` |
| Current runtime / Project入口 | `PROJECT_STATUS.md`（内容の日付を確認し、実状態の代用にしない） |

## 共通開発ループ

```text
README
  -> 必要なDesign / Tree / Delta / System Document
  -> Repository / Branch / HEAD / Status
  -> Target Source / Dependency / Test
  -> 既存資産の再利用確認
  -> 実装 / Debug
  -> Diff
  -> Test / Verify
  -> Documentation Gate
  -> Commit = 作業報告
  -> Push
  -> Remote Readback
  -> 必要ならPR / CI
  -> Master承認が必要な境界を越えた後だけDeploy / Production
```

### Documentation Gate

作業完了前に必要性を判定する。

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

- Currentの完成・検証状態が変わった: README更新
- File/Directory/主要責務/Entry Pointが変わった: Project Tree更新
- Designとの差を正式採用した: Design Deltaへ差分・理由・Evidence・Commitを記録
- 完成したFeature束/System/再利用Moduleを説明なしで引き継ぐ必要がある: System/Module Documentを作成または更新

DesignはCurrent実装に合わせて履歴を消す形で上書きしない。

## GitHub = 作業履歴正本

Commitは単なる保存ではなく実作業報告として扱う。可能な範囲で、目的、主要変更、影響範囲、検証、文書更新、未完/未検証を後から追える状態にする。

Commit / Push / Remote Readback / PR / CI / Merge / Deploy / Runtime / Productionは別状態であり、1つのPASSから他を推測しない。

ファイル変更後の標準手順は `docs/AUTO_COMMIT.md` を正とする。

## LibralCore

開発時の共通方法論は `CORE.md` を正とする。

正式な論理構造:

```text
Part
  ↓
Feature
  ↓
Component
  ↓
System
  ↓
Application System
```

新規Code生成前に既存資産を確認し、原則として次の順に再利用を判断する。

```text
そのまま利用
  -> 設定・引数・型の調整
  -> 薄いAdapter
  -> 共通部分抽出
  -> 目的を満たさない場合だけ新規実装
```

## Workspace

標準Workspace:

```text
/home/admin1/workspace/G-ACE.code-workspace
```

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

通常Contextから除外:
- `/home/admin1/logs`
- `/home/admin1/backups`
- `/home/admin1/kb`
- `/home/admin1/workspace`
- `archive`
- build / dist / node_modules / cache等

Workspace仕様は `docs/G_ACE_WORKSPACE.md` を正とする。

## Shared Platform

server-coreは共有Capabilityの**入口・契約・所有関係**を管理し、Capability本体を吸収しない。

共有Capabilityの発見入口は [`docs/WORKSPACE_REGISTRY.md`](docs/WORKSPACE_REGISTRY.md)。

対象例:
- MCP
- GitHub
- DebugAI
- KB
- shared tools / skills
- Cloudflare / Hugging Face
- Vault経由のToken / Secret利用

Secret / Token実値はChat・Git・文書・Logへ保存しない。

DebugAIは独立Project/runtimeとして扱う。CLI / HTTPに加え、MCP AdapterはDebugAI PR #22でSource / CI / stdio Protocolまで検証済み。Contabo上のLive DebugAI Runtime接続とWorkspace MCP登録は未実施なので `AVAILABLE_VERIFIED` とは扱わない。詳細状態は `docs/WORKSPACE_REGISTRY.md` を正とする。

再利用開発KBはMaster PCの `F:` 1TB領域を実データ置場候補とし、server-coreにはデータ本体ではなくアクセス・登録・安全契約だけを持たせる。設計は `docs/KB_REUSE_DESIGN.md`。VPSからPC driveへ直接アクセスできるものとして扱わない。

## Server / Runtime

VPSは処理・Runtime環境であり、Project SourceやDocumentの正本保存場所として扱わない。

本番常駐は原則Docker / Docker Compose。

標準の反映経路は、検証済みRepository変更をGitHubへ履歴化し、対象revisionを確認したうえで、必要なMaster承認後にServerへ反映する。

Log / Cache / Cleanup / Backup / Recoveryの共通設計は `docs/STORAGE_LIFECYCLE.md` を正とする。

read-only Storage Audit:
- policy: `operations/storage-lifecycle.json`
- source: `scripts/storage_lifecycle_audit.py`
- Source self-test: CIで検証
- Server Runtime audit: NOT_VERIFIED
- delete / prune / volume delete: NOT_IMPLEMENTED / DISALLOWED BY CURRENT POLICY

共通境界:
- Telegram: 対象Project契約で定義された永続raw-log正本
- Meilisearch: 再構築可能な検索Index
- Redis: dedup / hot-cache
- `/home/admin1/logs`: 一時disk state
- VPS: 処理場であり長期Log保管庫ではない

Cleanupは安全性を優先し、未送信、再送待ち、Recovery中、所有者不明、Active volume等を自動削除対象にしない。

## 主要正本

| File | Responsibility |
|---|---|
| `README.md` | Workspace共通入口 / Current概要 |
| `docs/SERVER_CORE_DESIGN.md` | server-core設計基準線 |
| `docs/LOAD_SCOPE.md` | Task routing / Context loading |
| `CORE.md` | LibralCore開発方法論 |
| `SERVER_CORE_PROTOCOL.md` | 共通運用規則 |
| `docs/G_ACE_WORKSPACE.md` | Workspace正規仕様 |
| `docs/WORKSPACE_REGISTRY.md` | Project / MCP / Tool / Secret Contract発見入口 |
| `docs/KB_REUSE_DESIGN.md` | F:再利用開発KBの設計基準線 |
| `docs/STORAGE_LIFECYCLE.md` | Log / Cache / Cleanup / Backup / Recovery設計基準線 |
| `docs/AUTO_COMMIT.md` | GitHub作業履歴化 |
| `docs/DEPLOY_RUNBOOK.md` | Deploy境界と手順 |
| `docs/PROJECT_TEMPLATE.md` | Project構成とDocument作成条件 |
| `docs/WORKSPACE_SHARED_SECRETS.md` | Shared Secret / Token契約 |
| `docs/STRUCTURE.md` | server-core構造 |
| `PROJECT_STATUS.md` | Current状態の補助Registry。実Runtime readbackを代替しない |

## Approval Boundary

Masterの明示指示なしに、main/PR merge、Production deploy/公開/切替、Force push、Branch削除、破壊的reset/rebase、既存Service停止/再作成、Secret変更、外部Resource作成・変更・削除を行わない。

未確認・未実行・未検証は推測で埋めず、`UNKNOWN / NOT_EXECUTED / NOT_VERIFIED`として扱う。