# SERVER CORE OPERATION PROTOCOL
Version: 1.0

## 目的
本サーバーは単一プロジェクト専用ではない。複数プロジェクトを長期運用するための共通基盤である。本ルールは人間・AI問わず適用される。

## AI作業開始手順
作業開始直後に必ず以下の確認コマンドを実行し、現在の環境を把握すること。
- pwd
- docker ps
- git status

## AI作業終了手順
作業終了時は必ず `PROJECT_STATUS.md` へ追記すること。
- 上書き禁止。
- 削除禁止。
- 追記のみ。

## Docker運用
本番運用はDockerのみ。
### 禁止事項
- node直接実行
- python直接実行
- pm2
- nohup
- screen
- tmux常駐

## Server定義
Serverは保管庫ではない。処理場である。
### 役割
- 実行
- 処理
- キャッシュ
- 一時保存

## 保存優先順位
KB ➔ Telegram ➔ Drive ➔ Server

## ディレクトリ構造
/home/admin1/
├── projects/
├── kb/
├── logs/
├── backups/
├── workspace/
└── server-core/

## 完了条件
1. 修正完了
2. テスト完了
3. ログ確認完了
4. PROJECT_STATUS.md更新完了

## 禁止事項
- CORE未確認作業
- KB未確認作業
- STATUS未確認作業
- 履歴削除
- KB削除
- data削除
- .env変更
- 勝手な再起動
- 勝手なデプロイ

記録されていない作業は存在しないものとして扱う。
