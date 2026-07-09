# Current Server Status
最終更新: 2026-06-16

## サーバー情報
VPS: 3 Core / 4GB RAM / 50GB SSD
Docker運用

## 現在稼働
- entrybot2-production
- gatebot-app
- gatebot-postgres

## 確認済事項
Docker稼働正常 / メモリ余裕あり / ディスク余裕あり

## 構想中プロジェクト
LibralCore / KAGURA / KAGRRA / TGAXIS / AEGIS / KB

## 現在の課題
サーバー共通ルール整備 / KB整備 / Module標準化 / プロジェクト構造統一

## TODO
- [x] server-core構築
- [x] CORE.md整備
- [x] KB.md整備
- [x] PROJECT_STATUS運用開始

## 作業履歴
### 2026-06-16
- 内容: Server共通憲法作成
- 結果: 初版作成完了
- 次回: server-core運用開始

### 2026-06-16

- **内容:** server-core v1.0 必須5ファイルを配置しGitHub管理下へ登録
- **変更ファイル:** README.md / SERVER_CORE_PROTOCOL.md / CORE.md / KB.md / PROJECT_STATUS.md
- **結果:** 正常完了
- **懸念事項:** AI作業時の読込・追記ルールの徹底が必要
- **次回作業:** 各プロジェクトへserver-core参照ルールを適用

### 2026-06-16 17:05
- **内容:** PROJECT_STATUS.md の誤追記ブロックを整理し、add-status.sh による追記運用へ移行。
- **変更ファイル:** PROJECT_STATUS.md / add-status.sh
- **結果:** add-status.sh は正常。PROJECT_STATUS.md の末尾を正常な作業履歴へ差し替え。
- **懸念事項:** 手入力でヒアドキュメントやMarkdownを直接貼るとシェルに誤投入されるため、今後は必ず add-status.sh を使用する。
- **次回作業:** git diff で内容確認後、commit/push する。

### 2026-06-17
- **内容:** プロジェクト別 構成・ドキュメント・報告ルール（PROJECT STRUCTURE / DOC / REPORT RULE）を server-core v1.1 へ統合。
- **変更ファイル:** SERVER_CORE_PROTOCOL.md / CORE.md / KB.md / PROJECT_STATUS.md
- **結果:** 各プロジェクト共通で PROJECT_INDEX.md、docs/STRUCTURE.md、docs/DOC_INDEX.md、docs/WORK_REPORT.md を必須化。不要・重複ファイルは削除せず archive/YYYY-MM-DD/ へ退避する方針を追加。GitHub push は許可、本番デプロイは人間確認後のみと定義。
- **懸念事項:** PROJECT_STATUS.md は追記専用のため、今後も上書き更新禁止。
- **次回作業:** 各実プロジェクトへ PROJECT_INDEX.md / docs/STRUCTURE.md / docs/DOC_INDEX.md / docs/WORK_REPORT.md を適用する。

### 2026-06-20 12:14

- **内容:** TGserverをprojects配下へ配置し専用Workspaceを作成
- **変更ファイル:** projects/TGserver logs/TGserver workspace/TGserver.code-workspace
- **結果:** GitHub clone成功、logs分離、Workspace作成完了
- **懸念事項:** 本番デプロイ未実行。Codex確認後にDocker方針確定
- **次回作業:** VS CodeでTGserver.code-workspaceを開きCodexへ正本読込
