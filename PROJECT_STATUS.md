# CURRENT SERVER STATUS

状態確認日: 2026-07-09

確認範囲: server-core / TGserver正本パス / Workspace入口 / Docker稼働状況

## 文書の役割
本ファイルは、現在有効なサーバー全体の状態と、主要ユニットの正本への入口だけを記載する。

作業履歴、詳細仕様、設計判断全文は記載しない。

管理者の明示的な変更指示がない限り、AI・作業者による書き換え・追記・削除・置換を禁止する。

## Server Core
- 配置先: `/home/admin1/server-core`
- 用途: 全Project共通の統治領域
- 更新権限: 管理者の明示指示がある場合のみ
- 作業履歴正本: GitHub commit / PR
- 構造正本: `/home/admin1/server-core/docs/STRUCTURE.md`

## Workspace
- 標準Workspace: `/home/admin1/workspace/G-ACE.code-workspace`
- Workspace folders: `/home/admin1/server-core`, `/home/admin1/projects`
- 既存の統合Workspace内で各ProjectをModuleとして扱う
- TGserver専用Workspaceは作成しない
- `/home/admin1/logs`, `/home/admin1/backups`, `/home/admin1/kb`, `/home/admin1/workspace` は通常Workspace folderに含めない

## TGserver
- 正式名称: TGserver
- 正本パス: `/home/admin1/projects/TGserver`
- 管理方法: 既存統合Workspace内のProject / Module
- Docker方針: Docker / Docker Composeで確定済み
- 現在フェーズ: Docker起動済み / 実装差分あり / 正本照合中
- 稼働確認済みコンテナ: `tgserver-tgs-1`, `tgserver-conversation-collector-1`, `tgserver-meilisearch-1`, `tgserver-redis-1`
- 注意: TGserverリポジトリには未コミット差分があるため、詳細状態はTGserver側の `git status` と正本文書を確認する。

## TGserver 要確認
- 正本文書と実ファイルの照合
- 環境変数と `.env.example` の照合
- Docker構成と実稼働コンテナの照合
- cache実装の現状確認
- 疎通試験結果の確認
- V8連結
- 本番運用

## TGserver 詳細正本
- `/home/admin1/projects/TGserver/PROJECT_INDEX.md`
- `/home/admin1/projects/TGserver/docs/STRUCTURE.md`
- `/home/admin1/projects/TGserver/docs/SPEC_v1.5.md`

## ログとキャッシュ
- 永続ログ正本: Telegram
- 検索インデックス: Meilisearch
- dedup / hot-cache: Redis
- サーバー共通分離ディスクキャッシュ: `/home/admin1/logs`
- VPS: 処理場。永続ログ保管庫ではない

`/home/admin1/logs` は、送信待ち、再送、処理途中、障害時一時退避などに限定する。

永続ログ、Telegram原本の長期複製、KB、仕様書、コードを置かない。

## V8
- 状態: 要確認
- 稼働確認済みコンテナ: `astera-v8`
- 開始条件: TGserver検証完了後
- ログ連携: 初回実装時からTGserverへ送信
- 注意: Server Core上ではV8実装詳細を正本管理しない。詳細は対象Project側の正本文書を確認する。

## KB
- 状態: 未実装
- TGserverからの直接送信: 禁止
- 生ログの直接投入: 禁止
- V8推論結果の自動投入: 禁止

## 次回作業
TGserverの正本文書、実ファイル、環境変数、Docker構成、cache実装の現状を照合する。

管理者の承認前に、本番起動、デプロイ、公開を行わない。
