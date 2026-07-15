# SERVER CORE GLOSSARY

## 正式表記
- Server Core: 全Projectに適用する共通の開発・運用統治領域。
- LibralCore: 開発AIが再利用可能な設計とCodeを効率よく生成・修正するための開発概念、設計方針、開発スタイル。開発時にのみ適用し、各Application Systemの実行構造には関与しない。
- Project: 目的を持つ開発・実装・運用単位。
- Part: 1責務を持つ最小の再利用可能部品。
- Feature: 1つ以上のPartを組み合わせ、1つの機能結果を提供する論理単位。
- Component: 関連Featureをまとめ、明確な入出力と依存境界を持つ論理単位。
- System: Componentを組み合わせ、まとまった処理、状態、業務領域を成立させる論理単位。
- Application System: 必要なSystemを統合して利用目的を完結させる完成物。
- Module: 同一Project内または別Projectで再利用、交換、独立修正しやすいように、1つの目的と責務へまとめた開発上の再利用単位。
- 再利用候補: 現在の目的と同じ、または調整によって利用可能な既存の設計、Code、Module、型、Schema、テスト、Template。
- Adapter: 既存資産を変更せず、入出力、型、設定、呼出方式の差だけを吸収する薄い変換境界。
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

5段は、開発AIが完成物を理解、分解、再利用、再構成するための論理構造である。各Application Systemの実行構造や物理構造を指定しない。

## 表記ルール
- 最上位表記は必ず `Application System` とする。
- `ApplicationSystems`、`Application Systems`、`Application`、`App` を5段の最上位名称として使用しない。
- `LibralCore`、`Module`、`Part`、`Feature`、`Component`、`System`、`Application System` は固有の設計用語として英語表記を維持する。
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
