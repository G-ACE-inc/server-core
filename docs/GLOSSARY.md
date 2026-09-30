# SERVER CORE GLOSSARY

## 正式表記
- Server Core: G-ACE Workspace全体のCommand Center。Task routing、Authority control、Project dispatch、shared capability discovery、共通開発/検証/GitHub/operations boundaryを統括する。各Project実装本体は所有しない。
- Command Center: Workspace作業の開始点。どのProjectで、何を読み、何を再利用し、どう検証し、どのApproval Boundaryまで進めるかを決める共通司令室。
- Authority: 特定のDesign / Contract / Current State / Registry / Operation Ruleについて正本として扱うSource。
- Routing: TaskのPurpose・責務・owner・必要Authorityを判定し、正しいProject/Contextへ振り分けること。
- Dispatch: server-coreがTask ownerを決め、実作業を対象Projectへ送ること。server-coreがProject固有実装を吸収する意味ではない。
- LibralCore: 開発AIが再利用可能な設計とCodeを効率よく生成・修正するための開発概念、設計方針、開発スタイル。
- Project: 目的を持つ実装・運用単位。Module集合体であることを必須としない。
- Part: 1つの変更理由を持つ最小責務。
- Feature: Partを組み合わせ、1つの機能結果を提供する論理単位。
- Component: Featureをまとめ、明確な入出力境界を持つ論理機能ブロック。
- System: Componentを制御し、状態または処理フローを管理する論理単位。
- Application System: Systemを統合し、目的または業務を完結させる最上位の論理構造。
- Module: 同一Project内または別Projectで再利用、交換、独立修正しやすいように、1つの目的と責務へまとめた開発上の再利用単位。
- Public Contract: Module / Component / Systemが外部へ公開するInterface、型、Schema、Input/Output条件。
- Reuse Candidate: 現在の目的と同じ、または調整によって利用可能な既存Design / Code / Module / Type / Schema / Test / Template / KB asset。
- Adapter: 既存資産を変更せず、Input/Output、Type、Config、Call方式の差だけを吸収する薄い境界。
- Single Source of Truth: 同じ情報を複数箇所へ重複管理せず、責務ごとに意図した正本へ集約する原則。
- README: ProjectのCurrent completed / verified stateとAuthority入口。Design正本ではない。
- Design: Architecture / Contract / Responsibility / BoundaryのBaseline。
- Design Delta: Baseline Designとの差を正式採用するときに、差分・理由・Evidence・影響範囲・適用Commit・Compatibility/Rollbackを記録する正本。
- Project Tree: AI / Developerが主要Source / Entry Point / Design / Testへ最短で到達するNavigation Index。
- Documentation Gate: 作業完了前にREADME / Tree / Delta / System Document更新要否を判定するGate。
- Work Report Commit: 実作業のPurpose / Changed / Affected / Verified / Docs / Remainingを必要範囲で追跡可能にするCommit。
- Workspace Registry: Project / Repository / MCP / Tool / Secret Contract / KB / Runtime確認先を発見する軽量Registry。Current Runtimeの健康証明ではない。
- Availability State: DISCOVERED / SOURCE_VERIFIED / CONFIG_REGISTERED / RUNTIME_VERIFIED / AVAILABLE_VERIFIED / NOT_IMPLEMENTED / NOT_REGISTERED / NOT_VERIFIED / UNKNOWN 等のCapability状態。
- Reusable Development KB: 検証済みの再利用Code / Module / Pattern / Schema / Interface / Test / Template / Procedure / Development Knowledgeを蓄積する外部KB。
- TGserver: Telegramログの受付、仕分け、配送、保存制御、検索を担当するProject。
- Astera v8: 判断材料生成等を担当するProject。詳細責務はAstera v8側Authorityを正とする。

## 5段階層型モジュラーアーキテクチャ
正式順序:

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

5段は開発AIが完成物を理解、分解、再利用、再構成するための論理構造。

物理構造はProject規模、再利用範囲、変更範囲、依存、検証、運用上の実益に基づいて決定する。

## 表記ルール
- 最上位表記は必ず `Application System`。
- `LibralCore`、`Module`、`Part`、`Feature`、`Component`、`System`、`Application System` は固有設計用語として英語表記を維持。
- `TGserver` を正式表記とする。
- `TGServer` は旧表記。新規文書では使わない。
- `GitHub` を正式表記とする。
- `commit`, `push`, `PR` はGit操作文脈で使用。
- `.env` はSecretを含み得る実環境File。
- `.env.example` は値を含まない共有用sample。

## 責務の境界
- server-core: Workspace Command Center。
- 各Project: Project固有Design / Source / Test / Runtime logicのowner。
- GitHub commit / PR: chronological work history authority。
- `docs/WORKSPACE_REGISTRY.md`: shared discovery authority。
- `docs/KB_REUSE_DESIGN.md`: Reusable Development KB Design Baseline。
- `docs/STORAGE_LIFECYCLE.md`: Storage / Log / Cache / Backup / Recovery Design Baseline。
- `docs/WORKSPACE_SHARED_SECRETS.md`: Shared Secret / Token use contract。
- Telegram: owning Project契約で定義されたdurable raw-log authority。
- Meilisearch: rebuildable search index。
- Redis: dedup / hot-cache。
- `/home/admin1/logs`: temporary operational disk state。
- VPS: processing/runtime environment。GitHub/Design正本ではない。