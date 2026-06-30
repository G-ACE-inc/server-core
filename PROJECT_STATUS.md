# CURRENT SERVER STATUS

最終更新: 2026-06-30

## 文書の役割
本ファイルは、現在有効なサーバー全体の状態と、主要ユニットの正本への入口だけを記載する。

作業履歴、詳細仕様、設計判断全文は記載しない。

管理者の明示的な変更指示がない限り、AI・作業者による書き換え・追記・削除・置換を禁止する。

## Server Core
- 配置先: `/home/admin1/server-core`
- 用途: 全Project共通の統治領域
- 更新権限: 管理者の明示指示がある場合のみ

## Workspace
- 配置領域: `/home/admin1/workspace`
- 既存の統合Workspace内で各ProjectをModuleとして扱う
- TGServer専用Workspaceは作成しない
- 存在未確認のWorkspaceファイルを記載しない

## TGServer
- 正式名称: TGServer
- 正本パス: `/home/admin1/projects/TGserver`
- 管理方法: 既存統合Workspace内のProject / Module
- Docker方針: Docker / Docker Composeで確定済み
- 現在フェーズ: コード配置後 / 初期セットアップ前 / 起動前確認

## TGServer 未実施
- 依存導入
- 環境設定
- build
- Docker起動
- 疎通試験
- デバッグ
- V8連結
- 本番運用

## TGServer 詳細正本
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
- 状態: 未実装
- 開始条件: TGServer検証完了後
- ログ連携: 初回実装時からTGServerへ送信

## KB
- 状態: 未実装
- TGServerからの直接送信: 禁止
- 生ログの直接投入: 禁止
- V8推論結果の自動投入: 禁止

## 次回作業
TGServerの正本文書、実ファイル、環境変数、Docker構成、cache実装の現状を照合する。

管理者の承認前に、本番起動、デプロイ、公開を行わない。
