# SERVER CORE GLOSSARY

## 正式表記
- Server Core: 全Projectに適用する共通統治領域
- LibralCore: 再利用、分離、着脱、蓄積、継承を重視する開発思想
- Project: Module集合体として扱う単位
- Module: 1責務を持つ着脱可能な構成要素
- TGserver: Telegramログの受付、仕分け、配送、保存制御、検索を担当するProject
- V8: TGserver検証完了後にログ連携する対象Projectまたは実行系
- KB: 確認済み知識を将来蓄積する領域。現時点では未実装

## 表記ルール
- `TGserver` を正式表記とする。
- `TGServer` は旧表記として扱い、新規文書では使わない。
- `GitHub` を正式表記とする。
- `commit`, `push`, `PR` はGit操作の文脈で使用する。
- `.env` は秘密情報を含み得る実環境ファイルとして扱う。
- `.env.example` は値を含まない共有用サンプルとして扱う。

## 責務の境界
- Telegram: 生ログの永続正本
- Meilisearch: 再構築可能な検索インデックス
- Redis: dedup / hot-cache
- `/home/admin1/logs`: サーバー共通の分離ディスクキャッシュ
- VPS: 処理場。永続ログ保管庫ではない
- GitHub commit / PR: 作業履歴の正本
- `PROJECT_STATUS.md`: 現在状態と正本入口
