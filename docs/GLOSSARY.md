# SERVER CORE GLOSSARY

## 正式表記
- Server Core: 全Projectに適用する共通統治領域。
- LibralCore: 開発AIが再利用可能な設計とCodeを効率よく生成・修正するための開発概念、設計方針、開発スタイル。
- Project: 目的を持つ実装・運用単位。Module集合体であることを必須としない。
- Part: 1つの変更理由を持つ最小責務。
- Feature: Partを組み合わせ、1つの機能結果を提供する論理単位。
- Component: Featureをまとめ、明確な入出力境界を持つ論理機能ブロック。
- System: Componentを制御し、状態または処理フローを管理する論理単位。
- Application System: Systemを統合し、目的または業務を完結させる最上位の論理構造。
- Module: 同一Project内または別Projectで再利用、交換、独立修正しやすいように、1つの目的と責務へまとめた開発上の再利用単位。
- 公開契約: ModuleまたはComponentが外部へ公開するInterface、型、Schema、入出力条件。
- 再利用候補: 現在の目的と同じ、または調整によって利用可能な既存の設計、Code、Module、型、Schema、テスト、Template。
- Adapter: 既存資産を変更せず、入出力、型、設定、呼出方式の差だけを吸収する薄い変換境界。
- Single Source of Truth: 同じ情報を複数箇所へ重複管理せず、1つの正本へ集約する原則。
- Workspace Registry: Project / MCP / Tool / Secret Contract / Runtime入口を発見する軽量Registry。Current Runtimeの証明ではない。
- Reusable Development KB: 検証済みの再利用Code / Module / Pattern / Schema / Interface / Test / Template / Procedure / Development Knowledgeを蓄積する外部KB。
- TGserver: Telegramログの受付、仕分け、配送、保存制御、検索を担当するProject。
- V8: TGserver検証完了後にログ連携する対象Projectまたは実行系。

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

5段は、開発AIが完成物を理解、分解、再利用、再構成するための論理構造である。

物理構造は、対象Projectの規模、再利用範囲、変更範囲、依存、検証、運用上の実益に基づいて決定する。

## 表記ルール
- 最上位表記は必ず `Application System` とする。
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
- `/home/admin1/logs`: サーバー共通の分離ディスク一時領域。
- VPS: 処理場。永続ログ保管庫ではない。
- GitHub commit / PR: 作業履歴の正本。
- `docs/WORKSPACE_REGISTRY.md`: Workspace共有Project / MCP / Tool / Secret Contract / Runtime入口のDiscovery Authority。
- `docs/KB_REUSE_DESIGN.md`: Reusable Development KBのDesign Baseline。
