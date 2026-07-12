# SERVER CORE GLOSSARY

## 正式表記
- Server Core: 全Projectに適用する共通統治領域
- LibralCore: 再利用、分離、着脱、蓄積、継承を重視する開発思想
- Project: Module集合体として扱う単位
- Module: 1責務を持つ着脱可能な構成要素
- TGserver: Telegramログの受付、仕分け、配送、保存制御、検索を担当するProject
- V8: TGserver検証完了後にログ連携する対象Projectまたは実行系
- KB: 確認済み知識を将来蓄積する領域。現時点では未実装

## 5層アーキテクチャ
- Layer 1 / 部品: 小さな共通処理を担う最小部品。例: Hash生成、時刻正規化、秘密情報除去。
- Layer 2 / Module: 単独で意味のある最小機能。例: 重複判定、Source検証、正本保存。
- Layer 3 / 機能束: 複数Moduleを順序統合する単位。例: KB登録Pipeline、検索Pipeline。
- Layer 4 / System: astera-kbサービス全体。
- Layer 5 / Application: 管理UI、利用画面、外部向け製品。
- 依存方向: Layer 5→Layer 4→Layer 3→Layer 2→Layer 1 の一方向のみ。
- 違反: 低層が高層をimportすること、または循環依存を作ること。

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
