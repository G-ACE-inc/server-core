# Server Core — 全Project共通開発・運用基盤

## 目的
`Server Core`（`/home/admin1/server-core`）は、G-ACE環境内の全Projectへ適用する共通の開発思想、AI読込規則、作業手順、GitHub運用、Workspace方針を管理する統治領域である。

本リポジトリはApplication Systemを実行・接続するRuntimeではない。各Projectの実装詳細や実行制御を集約せず、開発時の共通方針と正本入口だけを保持する。

## LibralCore
LibralCoreは、開発AIが再利用可能な設計とCodeを効率よく生成・修正するための開発方法論である。

目的は、再利用によって次を減らすことである。
- 開発時間
- AIコンテキストとToken
- 新規Code生成量
- 重複実装
- 修正範囲
- 検証と手戻りコスト

LibralCoreは次ではない。
- アプリ接続基盤
- 共通Runtime
- Plugin Framework
- Module登録・起動・停止機構
- アプリ共通の必須SDK
- 全Application Systemを一元実行する中央Core

各Application Systemは単独で成立し、LibralCoreへの接続、登録、常駐、通信、依存を一切前提としない。詳細は `CORE.md` を正とする。

## 管理者と変更権限
- 最終決定者は管理者である。
- AI・作業者は、管理者が明示した対象と範囲だけを変更する。
- 質問、疑問、検討、提案、操作説明は変更承認として扱わない。
- 実装済み、検証済み、稼働中などの状態は、実ファイル、実行結果、対象Project正本で確認する。

## 最小読込
作業開始時は次だけを読む。

1. `README.md`
2. `docs/LOAD_SCOPE.md`
3. 指定された対象ファイルまたは対象Project入口

開発方針判断時だけ `CORE.md`、共通運用判断時だけ `SERVER_CORE_PROTOCOL.md`、確認済み判断の照合時だけ `KB.md` を読む。

最初からリポジトリ全体を読まない。詳細は `docs/LOAD_SCOPE.md` を正とする。

## 正本
| ファイル | 役割 |
|---|---|
| `README.md` | Server Coreの入口と現行要約 |
| `docs/LOAD_SCOPE.md` | 最小読込と段階拡張条件 |
| `CORE.md` | LibralCore開発方法論と5段の正本 |
| `SERVER_CORE_PROTOCOL.md` | 全Project共通の作業・運用規則 |
| `KB.md` | 管理者が確定した判断Register |
| `PROJECT_STATUS.md` | 現在状態と各Project正本への入口 |
| `docs/GLOSSARY.md` | 正式名称と表記 |
| `docs/PROJECT_TEMPLATE.md` | 新規Projectの最小開発構成 |
| `docs/G_ACE_WORKSPACE.md` | G-ACE Workspaceの正規仕様 |

同じ情報を複数ファイルへ重複記載しない。

## 5段階層型モジュラーアーキテクチャ
開発AIが設計とCodeを組み立てる論理順序は次とする。

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

5段は再利用と局所修正のための論理構造であり、Runtime階層、アプリ接続順序、物理ディレクトリ構造ではない。

Moduleは、同一Project内または別Projectで再利用、交換、独立修正しやすいように責務をまとめた開発上の再利用単位である。LibralCoreへの登録や起動・停止を意味しない。

## AIコンテキスト
通常変更は次を起点とする。

1. 目的と期待結果
2. 対象責務
3. 再利用候補
4. 入力・出力
5. 直接依存と制約
6. 関連テスト

対象Code、直接依存、関連テストから開始し、責務または影響範囲を特定できない場合だけ段階的に読込範囲を拡張する。

## 再利用優先順位
```text
既存資産をそのまま利用
  ↓
設定・引数・型の調整
  ↓
薄いAdapter
  ↓
共通部分の抽出
  ↓
目的を満たさない場合だけ新規実装
```

既存資産を利用しない場合は、複雑化、性能、品質、依存、互換性などの具体的理由を確認する。

## Project作成
新規Projectで一律に必須とするのは、`README.md`、`.gitignore`、実装入口、および必要な場合の値なし `.env.example` だけとする。

追加文書や追加構造は、開発、再利用、検証、運用コストを実際に下げる場合だけ作る。詳細は `docs/PROJECT_TEMPLATE.md` を正とする。

## Workspace
標準Workspace:

```text
/home/admin1/workspace/G-ACE.code-workspace
```

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

`/home/admin1/logs`、`/home/admin1/backups`、`/home/admin1/kb`、`/home/admin1/workspace` は通常作業Folderに含めない。

## Project正本入口
- TGserver: `/home/admin1/projects/TGserver`
- Astera v8: `/home/admin1/projects/astera_v8`

Project固有の構造、仕様、API、環境変数、テスト、デプロイ、運用状態は各Project側の正本を使用する。

## GitHubと検証
- 作業履歴の正本はGitHub commit / PRとする。
- ファイル変更は差分と検証結果を確認し、意味のある単位でcommit / pushする。
- mainへの直接pushは、管理者が許可した正本更新または小規模運用文書更新に限る。
- 実装変更、複数Project変更、高Risk変更はPRを優先する。
- 本番起動、公開、切替、デプロイは管理者の明示承認後に行う。

検証はプロセス起動、エラーなし、`True`、空配列、HTTP 200だけで合格にしない。具体例または実データで期待結果と回帰を確認する。

## 最重要
- LibralCoreをRuntimeまたはアプリ連結基盤として扱わない。
- 既存Application SystemへLibralCore依存を追加しない。
- 再利用候補を確認せずに同じ責務をゼロから生成しない。
- 5段を物理構造へ変換しない。
- Moduleを実行時管理単位として共通定義しない。
- 同じ情報とCodeを重複管理しない。
- 期待結果が確認されるまで完了扱いにしない。
