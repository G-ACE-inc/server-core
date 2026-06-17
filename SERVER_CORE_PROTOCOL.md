# SERVER CORE OPERATION PROTOCOL
Version: 1.1

## 目的
本サーバーは単一プロジェクト専用ではない。複数プロジェクトを長期運用するための共通基盤である。本ルールは人間・AI問わず適用される。

## AI作業開始手順
作業開始直後に必ず以下の確認コマンドを実行し、現在の環境を把握すること。
- pwd
- docker ps
- git status

## プロジェクト別 構成・ドキュメント・報告ルール
すべてのプロジェクトは、最初に構成図を作成し、その構成図通りにファイルを配置する。AIが勝手にファイルを増やすこと、重複ファイルを放置すること、ドキュメントを散らかすことを禁止する。

### 必須ディレクトリ構造
各プロジェクト直下に必ず以下の階層を設けること。
- `docs/` : ドキュメント群
- `archive/` : 不要・重複・旧版ファイルの退避先（`archive/YYYY-MM-DD/`）
- `scripts/` : スクリプト群
- `src/` : ソースコード群
- `data/` : データ群
- `logs/` : ログ群

### プロジェクト直下の必須ファイル
- **PROJECT_INDEX.md**
  - 役割：プロジェクト全体の入口、構成図、各ドキュメントへのリンク、作業報告へのリンク、現在の稼働状態、GitHub/デプロイ状況。

### docs配下の必須ファイル
- **docs/STRUCTURE.md** : 構成図専用。ファイル配置はこの構成図に絶対従う。
- **docs/DOC_INDEX.md** : ドキュメント一覧。各階層に散らばる説明書・仕様書をすべて統合。
- **docs/WORK_REPORT.md** : 作業報告ファイル。作業後は必ず追記（削除・上書き禁止）。

## 変更・終了時のルール
ファイル変更を行った際は、必ず以下を更新すること。
1. PROJECT_INDEX.md
2. docs/STRUCTURE.md
3. docs/DOC_INDEX.md
4. docs/WORK_REPORT.md

作業終了時は必ずサーバー共通の `PROJECT_STATUS.md` へ追記するとともに、プロジェクト固有の `docs/WORK_REPORT.md` へも追記すること。

## GitHub・デプロイ運用
Cursorのコミットボタン等を使用した自動化を許可する。作業終了時は以下を自動で行ってよい。
1. git status確認
2. 変更内容確認
3. WORK_REPORT.md追記
4. commit作成
5. GitHubへpush
※ただし、**本番デプロイの自動実行は絶対禁止**とする。

## Docker運用
本番運用はDockerのみ。
- 【禁止】node直接実行 / python直接実行 / pm2 / nohup / screen / tmux常駐

## Server定義と保存優先順位
Serverは処理場であり、保管庫ではない。
- 保存優先順位: KB ➔ Telegram ➔ Drive ➔ Server
- ディレクトリ: `/home/admin1/` 配下に `projects/`, `kb/`, `logs/`, `backups/`, `workspace/`, `server-core/` を厳守。

## 完了条件
1. 修正完了
2. テスト完了
3. ログ確認完了
4. ドキュメント群（PROJECT_INDEX, STRUCTURE, DOC_INDEX, WORK_REPORT, サーバー側の PROJECT_STATUS）更新完了
5. GitHubへのpush完了

## 絶対禁止事項
- 構成図なしでの開発着手
- ルート直下への雑ファイル作成
- 重複ファイルの放置
- 不要ファイルの即削除（必ずarchiveへ移動すること）
- ドキュメント未更新・作業報告未記入での終了
- pushなしでの作業終了
- デプロイの勝手な実行
- CORE/KB/STATUS未確認での作業
- 過去履歴・KB・dataの削除、.envの無断変更

記録されていない作業は存在しないものとして扱う。
