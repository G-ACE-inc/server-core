# Server Core — 全Project共通統治基盤

## 目的
`Server Core`（`/home/admin1/server-core`）は、G-ACE環境内の全Projectへ適用する共通思想、運用規則、読込範囲、GitHub運用、Workspace方針を管理する統治領域である。

本リポジトリは、各Projectへ共通適用する規則と正本入口を保持する。

LibralCoreは、開発AIが再利用可能な設計とCodeを効率よく生成・修正するための開発方法論である。

## 管理者と変更権限
- 最終決定者は管理者である。
- AI・作業者は、管理者が明示した対象と範囲を変更する。
- 変更承認は、管理者の明示的な変更指示で確認する。
- 実装済み、検証済み、稼働中などの状態は、実ファイル、実行結果、対象Project正本で確認する。

## 最小読込
作業開始時は次を読む。

1. `README.md`
2. `docs/LOAD_SCOPE.md`
3. 指定された対象ファイルまたは対象Project入口

Architecture判断時は `CORE.md`、共通運用判断時は `SERVER_CORE_PROTOCOL.md`、確認済み判断は `KB.md`、現在状態は `PROJECT_STATUS.md` を読む。

読込範囲は `docs/LOAD_SCOPE.md` に従って段階的に拡張する。

## 正本
| ファイル | 役割 |
|---|---|
| `README.md` | Server Coreの入口と現行要約 |
| `docs/LOAD_SCOPE.md` | 最小読込と段階拡張条件 |
| `CORE.md` | LibralCore開発方法論、5段、Module、再利用、物理分離の正本 |
| `SERVER_CORE_PROTOCOL.md` | 全Project共通の運用規則 |
| `KB.md` | Server Coreで確認済みの判断Register |
| `PROJECT_STATUS.md` | 現在状態と各Project正本への入口 |
| `docs/GLOSSARY.md` | 正式名称と表記 |
| `docs/PROJECT_TEMPLATE.md` | 新規Projectの最小構成 |
| `docs/G_ACE_WORKSPACE.md` | G-ACE Workspaceの正規仕様 |
| `docs/CLOUDFLARE_OPERATIONS.md` | Astera v8 Cloudflare Tunnel統合設計・実運用正本 |
| `operations/cloudflare.json` | Astera v8 Cloudflare運用定義（認証情報なし） |

同じ情報は1つの正本へ集約する。Architecture定義は `CORE.md`、正式表記は `docs/GLOSSARY.md` を正とする。

`KB.md` は判断Registerとして使用する。

## 5段階層型モジュラーアーキテクチャ
正式順序は次とする。

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

5段は、完成物を理解、分解、再利用、再構成するための論理構造として使用する。

Moduleは、同一Project内または別Projectで再利用、交換、独立修正しやすいように責務をまとめた開発上の再利用単位とする。

物理構造は、対象Projectの規模、再利用範囲、変更範囲、依存、検証、運用上の実益に基づいて決定する。詳細は `CORE.md` を正とする。

## AIコンテキスト
通常変更は次を起点とする。

1. 目的と期待結果
2. 対象責務
3. 再利用候補
4. 入力・出力
5. 直接依存と制約
6. 関連テスト

対象Code、直接依存、関連テストから開始し、責務または影響範囲を特定できない場合だけ段階的に読込範囲を拡張する。

## Project作成
新規Projectの基本構成は、`README.md`、`.gitignore`、実装入口、および必要な場合の値なし `.env.example` とする。

追加文書は必要理由がある場合に作る。詳細は `docs/PROJECT_TEMPLATE.md` を正とする。

## Workspace
標準Workspace:

```text
/home/admin1/workspace/G-ACE.code-workspace
```

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

分離領域は、`/home/admin1/logs`、`/home/admin1/backups`、`/home/admin1/kb`、`/home/admin1/workspace` とする。

## Project正本入口
- TGserver: `/home/admin1/projects/TGserver`
- Astera v8: `/home/admin1/projects/astera_v8`

Project固有の構造、仕様、API、環境変数、テスト、デプロイ、運用状態は各Project側の正本を使用する。実在Path、Git状態、Docker状態は作業開始時に実環境で確認する。

## GitHubと検証
- 作業履歴の正本はGitHub commit / PRとする。
- ファイル変更を伴う作業完了時は、管理者が明示禁止した場合を除き、`SERVER_CORE_PROTOCOL.md` Git 節に従い commit / push まで行う。commit / push なしで終了した作業は未完了として扱う。
- ファイル変更は差分と検証結果を確認し、意味のある単位でcommit / pushする。
- mainへの直接pushは、管理者が許可した正本更新または小規模運用文書更新に使用する。
- 実装変更、複数Project変更、高Risk変更はPRを使用する。
- 本番起動、公開、切替、デプロイは管理者の明示承認後に行う。

検証は、具体例または実データを使用し、期待結果、状態変化、主要失敗条件、回帰結果を確認する。

## 最重要
- LibralCoreは、再利用、Code生成、局所修正の判断に使用する。
- 新規Code生成前に再利用候補を確認する。
- 状態は実ファイル、実行結果、正本で確認する。
- 完了は実行結果と検証結果で判定する。
- 5段は論理構造として使用する。
- Moduleは目的と効果が明確な責務単位にする。
- 同じ情報は1つの正本へ集約する。
- 期待結果が確認された時点で完了とする。
