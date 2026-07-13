# SERVER CORE GLOSSARY

## 正式表記
- Server Core: 全Projectに適用する共通統治領域。
- LibralCore: 再利用、分離、着脱、蓄積、継承を重視する開発思想。
- Project: 目的を持つ実装・運用単位。Module集合体であることを必須としない。
- Part: 1つの変更理由を持つ最小責務。
- Feature: Partを組み合わせ、1つの機能結果を提供する論理単位。
- Component: Featureをまとめ、明確な入出力境界を持つ論理機能ブロック。
- System: Componentを制御し、状態または処理フローを管理する論理単位。
- Application System: Systemを統合し、目的または業務を完結させる最上位の論理構造。
- Module: Coreが登録、有効化、停止、依存解決、状態確認、交換、更新、復旧を管理するLifecycle単位。5段の階層名ではない。
- Core: ModuleのLifecycle、依存、公開契約、Health・Readiness、縮退・復旧を管理する領域。
- Required Module: Application Systemの成立に必要なModule。
- Optional Module: 停止しても他機能を継続できる追加機能Module。
- 公開契約: ModuleまたはComponentが外部へ公開するInterface、型、Schema、入出力条件。
- Single Source of Truth: 同じ情報を複数箇所へ重複管理せず、1つの正本へ集約する原則。
- TGserver: Telegramログの受付、仕分け、配送、保存制御、検索を担当するProject。
- V8: TGserver検証完了後にログ連携する対象Projectまたは実行系。
- KB: 確認済み知識を将来蓄積する領域。現時点では未実装。

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

5段は論理分類であり、ファイル、ディレクトリ、パッケージ、Module、リポジトリ、プロセス、コンテナ、デプロイ単位とは一対一対応させない。

## 表記ルール
- 最上位表記は必ず `Application System` とする。
- `ApplicationSystems`、`Application Systems`、`Application`、`App` を5段の最上位名称として使用しない。
- `Module` と `Core` は固有の設計用語として英語表記を維持する。
- `TGserver` を正式表記とする。
- `TGServer` は旧表記として扱い、新規文書では使わない。
- `GitHub` を正式表記とする。
- `commit`, `push`, `PR` はGit操作の文脈で使用する。
- `.env` は秘密情報を含み得る実環境ファイルとして扱う。
- `.env.example` は値を含まない共有用サンプルとして扱う。

## 責務の境界
- Telegram: 生ログの永続正本。
- Meilisearch: 再構築可能な検索インデックス。
- Redis: dedup / hot-cache。
- `/home/admin1/logs`: サーバー共通の分離ディスクキャッシュ。
- VPS: 処理場。永続ログ保管庫ではない。
- GitHub commit / PR: 作業履歴の正本。
- `PROJECT_STATUS.md`: 現在状態と正本入口。
