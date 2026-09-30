# G-ACE WORKSPACE

## 目的

`/home/admin1/workspace/G-ACE.code-workspace` を、Workspace内の全Projectで **server-coreを必ず共通入口として使う** 開発・運用Workspaceとして定義する。

Projectごとの実装・Designは各Project側に置き、server-coreは共通開発標準、GitHub運用、共有Tool/MCP/Secret契約、Server運用境界を提供する。

## Authority Entry

Workspace作業は必ず次から開始する。

```text
/home/admin1/server-core/README.md
  -> /home/admin1/server-core/docs/LOAD_SCOPE.md
  -> 今回必要なserver-core正本だけ
  -> 対象Project README
  -> 対象Projectの必要範囲だけ
```

全server-core正本の一括読込を禁止する。

## Workspace Folders

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

通常Folderに含めない:
- `/home/admin1/workspace`
- `/home/admin1/kb`
- `/home/admin1/logs`
- `/home/admin1/backups`

理由:
- server-coreを共通Authority入口にする
- projectsを実作業対象集合として扱う
- logs / backups / kb / workspaceを通常検索・誤編集・Context肥大から隔離する

## Project Entry

対象ProjectではREADMEを入口にする。

READMEから、存在する場合は次へ直接到達できる状態を標準とする。
- Design
- Project Tree
- Design Delta
- completed System / Feature-bundle / Module documents
- run / test / verify entry points

対象Code、直接依存、関連Testから開始し、必要な時だけ `docs/LOAD_SCOPE.md` のLevelに従って範囲を拡張する。

## Development Routine

```text
server-core entry
  -> target Project README
  -> required Design / Tree / Delta / System Document
  -> repository / branch / HEAD / status
  -> Source / direct dependencies / tests
  -> reuse check
  -> implementation / debug
  -> diff
  -> verification
  -> documentation gate
  -> GitHub commit as work report
  -> push / remote readback
  -> PR / CI if required
```

Master承認が必要なMerge / Production / Provider変更等は自動で越えない。

## Documentation Gate

作業完了時に最低限次を判定する。

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Requiredなのに未更新ならDocumentation Completeとしない。

DesignはCurrent実装へ合わせて履歴が消える形で上書きしない。

## GitHub Work History

GitHub commit / PRは作業履歴の正本とする。

Commitは可能な範囲で、目的・主要変更・影響範囲・検証・Document更新・残作業を後から追える作業報告にする。

標準commit/pushは `docs/AUTO_COMMIT.md` を正とする。

Commit / Push / Remote Readback / PR / CI / Merge / Deploy / Runtime / Productionは別状態として扱う。

## Shared Tools / MCP

Workspace共通Tool/MCPはserver-coreを発見入口とする。

server-coreが管理するのは **接続契約・用途・所有先・権限境界** であり、各Tool本体をserver-coreへ移植しない。

現在 `.cursor/mcp.json` に存在するMCPは実設定を正とし、未登録MCPを利用可能として扱わない。

DebugAIは独立Project/runtime。現在確認済みの共通利用経路はCLI / HTTP。MCP AdapterはDebugAI側で実装・検証された後にWorkspace共通Registryへ登録する。

## Workspace Shared Secrets

Secret / Token値を各Projectへ複製しない。

既存共有契約:
- Hugging Face: Vault `POST /internal/v1/actions/http`、`secret_id=hf-token`、`consumer=g-ace-workspace`
- Cloudflare Account API: Vault `POST /internal/v1/actions/http`、`secret_id=cf-account-api`

Token値を読み出し、Chat / Git / Log / Documentへ保存しない。

詳細は `docs/WORKSPACE_SHARED_SECRETS.md` を正とする。

## Knowledge Base

再利用開発KBの実データはserver-coreへ置かない。

Target:
- Master PC `F:` 1TB storage
- 用途: validated reusable code/module/pattern/schema/interface/test/template/procedure/development knowledge

server-coreはKB access / registration / lifecycle / safety contractのみを管理する。

VPS / Workspace AIから利用するには、実装・検証済みAPI/MCP等のbridgeを使用する。PC driveへの直接アクセスを前提にしない。

## Server / Runtime

本番常駐は原則Docker / Docker Compose。

ServerはRuntime/処理環境であり、Project Source履歴・Design・Documentの正本をServerだけに置かない。

Deployは、GitHub上で対象revisionを確認し、必要なMaster承認後に対象Project Runbookに従う。

## Logs / Cache / Cleanup

Common boundary:
- Telegram: owning Project contractで定義されたdurable raw log authority
- Meilisearch: rebuildable search index
- Redis: dedup / hot cache
- `/home/admin1/logs`: temporary disk state
- VPS: processing environment

自動Cleanupでは、未送信、再送待ち、Recovery中、所有者不明、Active volume等を削除しない。

Retention / cleanup / backup / recoveryはServer運用標準で管理し、Project固有条件がある場合はProject側契約を優先する。

## Normal Context Exclusions

通常検索・Context・watcherから原則除外:
- `.git`
- `.github`（GitHub Task時を除く）
- `.tgs-state`
- `archive`
- `backups`
- `build`
- `coverage`
- `dist`
- `logs`
- `node_modules`
- cache / dumps

## Workspace Tasks

Workspaceには少なくとも次の入口を維持する。
- server-core routing / load scope確認
- server-core auto commit and push

Tool追加はTask数を増やすこと自体を目的にせず、全Projectで反復利用する実益がある場合だけ行う。

## Current-state Warning

Workspace文書、`PROJECT_STATUS.md`、registryの記載は探索入口であり、Current Runtimeの証明ではない。

Container / Port / Domain / Provider / Deploy状態を判断する場合は必ず実状態をreadbackする。