# PROJECT TEMPLATE

## 目的

新規Projectまたは既存Projectの整備時に、server-coreを共通入口として、低Context・再利用優先・引継ぎ可能なRepository構造を作る。

このTemplateは大量のDocument作成を要求するものではない。必要な正本だけを作る。

## Workspace Integration

ProjectはG-ACE Workspace内ではserver-core共通ルールに従う。

```text
server-core README / LOAD_SCOPE
  -> Project README
  -> Project固有Authority
  -> Source / Test
```

Project固有情報をserver-coreへコピーしない。

## 開発開始前の確認

新規Code生成前に確認する。

1. 目的と期待結果
2. 同じ責務を持つ既存Design / Code / Module / Type / Schema / Test / Template
3. そのまま利用可能か
4. 設定・引数・型調整で利用可能か
5. 薄いAdapterで利用可能か
6. 共通部分を抽出できるか
7. 新規実装が本当に必要か

既存資産を利用しない場合は、複雑化、性能、品質、依存、互換性等の具体的理由を確認する。

## 最小必須構成

- `README.md`
- `.gitignore`
- 技術Stackに対応する実装入口
- 環境変数が必要な場合だけ値なし `.env.example`

Design / Tree / Delta / System Documentは必要条件を満たした場合だけ追加する。

## Single Source of Truth

同じ情報を複数Documentへ重複管理しない。

基本責務:
- Code上のInterface / Type / Schema / Test: executable contract
- Design: architecture / responsibility / boundary baseline
- README: current completed / verified entry point
- Project Tree: navigation index
- Design Delta: intentional difference / rationale
- Commit / PR: chronological work history

## README Contract

READMEはProjectのCurrent State Entry Pointとする。

最低限:
- Project名 / Purpose
- Current completed / verified state
- main entry point
- run / test / verify方法
- Designへのリンク（存在する場合）
- Project Treeへのリンク（存在する場合）
- Design Deltaへのリンク（存在する場合）
- completed System / Feature-bundle documentsへのリンク（存在する場合）
- Production / Runtime状態を記載する場合は確認境界を明確化

READMEをDesign正本として使わない。

## Design Contract

DesignはArchitecture / Contract / Boundary / ResponsibilityのBaselineを保存する。

Current実装に合わせて履歴を消す上書きをしない。

Architecture自体を正式変更する場合は、旧Baseline、変更理由、新しいDecision、適用Commitを追跡できる状態にする。

## Project Tree

次の場合に作成する。
- RepositoryがREADMEだけでは主要構造を辿りにくい
- 複数のentry point / module / systemがある
- AIが対象Source探索で不要なRepository全読込を繰り返す可能性がある

Treeは単なるPath一覧ではなく、主要File/Directoryの責務、Entry Point、関連Design、関連Testを記録する。

更新条件:
- File/Directory追加・削除・移動
- 主要責務変更
- Entry Point変更
- 構造変更

build / dist / dependency / cache等は通常載せない。

## Design Delta

実装がDesign Baselineと意図的に異なる場合に使用する。

最低項目:
- Baseline design
- Actual change
- Reason / root cause
- Evidence
- Affected scope
- Applied commit
- Compatibility / migration / rollback considerations

Design DeltaをDesignのCurrent化に使わない。

## System / Feature-bundle Document

次の場合に作成または既存Documentを更新する。
- 複数Featureが1つのSystem責務を形成した
- reusable Moduleとして完成した
- 安定した内部/外部Interfaceを持つ
- State/Data ownershipが複雑
- Runtime / Failure / Recovery / Security / Operation理解が保守に必要
- READMEだけでは別AI / Developerへ説明なしで引継げない

Document内容は対象Systemに必要なものだけ選ぶ。

候補項目:
- Purpose / Scope
- Architecture / Component / Module
- Entry points
- Interface / Contract
- Dependencies
- State / Data ownership
- Processing flow
- Failure / Recovery
- Security boundary
- Configuration
- Runtime / Deployment
- Tests / Verification
- Current verified state
- Design / Delta relationship
- Source / Test map
- Extension / compatibility constraints

不要な空セクションをTemplate充足のためだけに作らない。

## Specialized Documents

以下は条件がある場合だけ分離する。

- Contract: API / CLI / MCP / Event / Webhook等の安定契約が複雑
- Data/State Ownership: 永続状態や複数Systemの所有境界が複雑
- Operations / Recovery: 常駐Serviceや障害復旧が必要
- Security: Secret/Auth/Permission/Public endpoint/User data等の境界が重要
- Verification / Acceptance: 完成条件・E2E・Provider検証を独立管理する価値がある
- Migration / Compatibility: Schema/API/Storage/Runtime移行がある
- ADR: 重要なTradeoffを伴うArchitecture decisionを後から説明する必要がある

## Documentation Gate

作業完了前に判定する。

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

判定:
- Current completed / verified state変更 -> README YES
- File/Directory/主要責務/Entry Point変更 -> Tree YES
- Designとの差を正式採用 -> Delta YES
- 説明なし引継ぎが困難な完成System/Feature bundle/Module -> System Document YES/UPDATE_EXISTING

Requiredなのに未更新ならDocumentation Completeではない。

## 5段階層型モジュラーアーキテクチャ

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

5段は論理分類であり、各段を必ず別File/Directoryにする規則ではない。

## Module化判定

Moduleは再利用、交換、独立修正の実益がある責務単位とする。

新規Moduleの目安:
- 目的/責務を一文で説明可能
- Public contractを定義可能
- Input/Output/Dependency/State ownerが明確
- Application固有値をConfig/Adapterへ分離可能
- 単独または境界単位でTest可能
- 再利用時のContextを限定可能
- 追加保守Costより効果が大きい

条件を満たさない場合は既存Module内のPart/Feature/Componentとして実装する。

## AIへ渡す最小情報

通常TaskでAIへ渡す起点:
- 目的と期待結果
- 対象責務
- 再利用候補
- Input / Output
- 直接依存と制約
- 関連Test

不足した時だけLOAD_SCOPEに従って広げる。

## Test / Verification

変更内容に応じて確認する。
- Input
- execution condition
- expected output
- changed state
- state that must not change
- regression
- important failure cases
- Runtime / Provider readback when relevant

合格は、期待出力、状態変化、既存機能回帰、主要失敗条件を必要範囲で確認して判定する。

Process起動、Error無し、HTTP 200、Build成功、CI greenだけではPASSとしない。

## GitHub

Commit / PRを実作業履歴の正本とする。

Commitは必要に応じてPurpose、material changes、affected scope、verification、documentation、remaining/unverified workを追える作業報告にする。

Commit / Push / Remote Readback / PR / CI / Merge / Deploy / Runtime / Productionを別状態として扱う。

## Secret / Environment

共有が必要なkey名は値なし `.env.example` に記載可能。

Secret / Token実値をGitへ保存しない。Workspace共有Secret契約がある場合はserver-core側の契約を利用し、Projectへ実値を複製しない。

## 実行順序

```text
目的と期待結果
  -> server-core routing
  -> Project README
  -> 必要なBaseline / Source / Test
  -> reuse check
  -> implementation / debug
  -> verification
  -> documentation gate
  -> GitHub work report
  -> remote verification
```
