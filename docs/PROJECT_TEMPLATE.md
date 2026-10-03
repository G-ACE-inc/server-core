# PROJECT TEMPLATE

## Purpose

新規Projectまたは既存Projectを整備するときに、server-coreを共通入口として、再利用優先・引継ぎ可能・過剰Documentを作らないRepository構造を定義する。

このTemplateは大量のDocument作成を要求しない。実際の責務・運用・保守に必要なAuthorityだけを作る。

## Workspace Integration

```text
server-core README / LOAD_SCOPE / G_ACE_WORKSPACE fixed routine
  -> Project README
  -> Current GitHub state / Commit / PR
  -> Project固有Authority
  -> Source / Test
```

Project固有情報をserver-coreへコピーしない。

Project-owned service / Libral Vault / MCP / Toolを導入する場合は `server-core/docs/PROJECT_INTEGRATION_RULES.md` を共通契約として確認する。

## Documentation Ownership

READMEと、そのREADMEからリンクするDesign / Tree / Delta / System / Operations / Contract等のDocumentは、**そのREADMEを所有するProject Repository側のDocument**である。

対象Projectで次のような指示を受けた場合:
- READMEを更新する
- READMEに付属するDocumentを更新する
- 各種Documentを更新する
- READMEから必要なDocumentを作成してリンクする

更新対象は対象Project Repository内とする。server-coreのREADMEやDocumentへ自動的に読み替えない。

server-core Documentは、**server-core自体の変更についてexplicit owner authorizationがある場合だけ**変更する。Workspace共通Routing / Authority / Shared Capability / Project Template / 共通運用Contractに影響がありそうという理由だけでは、server-core変更理由にならない。

## Mutation Ownership

Project Taskでは、参照したRepositoryと変更してよいRepositoryを分離する。

```text
TARGET_PROJECT = 主対象Project
TARGET_REPOSITORY = 主対象Repository
MUTATION_REPOSITORIES = 今回write/commit可能なRepository
READ_ONLY_REPOSITORIES = Authority/Reuse/Integration確認だけのRepository
SERVER_CORE_MUTATION_AUTHORIZED = server-core変更の明示許可状態
```

server-coreは `SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示的に成立しない限りread-only。Shared Capability owner、Provider integration owner等も参照しただけでは、そのRepositoryを `MUTATION_REPOSITORIES` に追加しない。

「MCPを使う」「TGserverへ接続する」「Vaultを使う」「Cloudflareを使う」等の利用Taskは、原則としてconsumer Project側の変更で閉じる。owner側Source変更が必要と確認された場合だけ、別mutation対象として明示する。

Commit前にはcurrent Git top-levelと対象Repositoryを照合し、別Projectの差分を混在させない。server-coreへのCommitは追加でexplicit owner authorizationを確認する。

## 開発開始前の確認

新規Code生成前に確認する。
1. 目的と期待結果
2. Project README
3. Current branch / HEAD / latest commit / Open PR / CI（Taskに必要な範囲）
4. 同じ責務を持つ既存Design / Code / Module / Type / Schema / Test / Template
5. そのまま利用可能か
6. 設定・引数・型調整で利用可能か
7. 薄いAdapterで利用可能か
8. 共通部分を抽出できるか
9. 新規実装が必要か

既存資産を利用しない場合は、複雑化、性能、品質、依存、互換性等の具体的理由を確認する。

## 最小必須構成

- `README.md`
- `.gitignore`
- 技術Stackに対応する実装入口
- 環境変数が必要な場合だけ値なし `.env.example`

Design / Tree / Delta / System Documentは必要条件を満たした場合だけ追加する。

## Single Source of Truth

- Code Interface / Type / Schema / Test: executable contract
- Design: architecture / responsibility / boundary baseline **and preserved formal change history**
- README: current completed / verified entry point
- Project Tree: navigation index
- Design Delta: intentional architecture/responsibility differenceの詳細・理由・Evidence・適用Commit
- System Document: stable operational/technical handoff
- Commit / PR: chronological work history

同じCurrent factを複数Documentへ重複管理しない。

## README Contract

READMEはProjectのCurrent Entry Point。

最低限:
- Project名 / Purpose
- Current completed / verified state
- main entry point
- run / test / verify方法
- Design / Tree / Delta / System Documentへのリンク（存在する場合）
- Runtime状態を記載する場合はlast-knownとCurrent readbackを区別

READMEをDesign正本や作業日誌として使わない。

READMEからリンクするProject Documentは、そのProjectの継続開発・運用・保守に必要な情報を持つ。server-core側の共通Documentを、Project固有Documentの代用品として使わない。

## Design Contract

DesignはArchitecture / Contract / Boundary / ResponsibilityのBaselineを保存する。

**元の設計を消さない。Current実装に合わせて既存Design記述を書き換えて過去の意図を失わせない。正式な変更は、元のDesign記述を保持したまま、その下へ変更履歴として追記する。**

各正式変更履歴では必要な範囲で次を残す。
- 変更前の設計 / baseline
- 変更点
- 理由 / root cause
- Evidence
- 影響範囲
- 適用Commit / PR
- Compatibility / migration / rollback
- verification state

Design Deltaはこの変更を横断的に説明・参照するために使えるが、元Design側の履歴保存を置き換えるものではない。Design Deltaだけに変更を残して元DesignをCurrent状態へ上書きする運用は禁止する。

## Project Tree

次の場合に作成/更新する。
- READMEだけでは主要構造を辿りにくい
- 複数entry point / module / systemがある
- AIが対象Source探索で不要なRepository全読込を繰り返す可能性がある
- File/Directory/主要責務/Entry Pointが変わった

Treeは単なるPath一覧ではなく、主要File/Directoryの責務、Entry Point、関連Authority/Testを記録する。

Generated/dependency/cache outputは通常載せない。

## Design Delta

Design BaselineとArchitecture/Responsibilityが意図的に変わる場合に使用する。

最低項目:
- Baseline design
- Actual change
- Reason / root cause
- Evidence
- Affected scope
- Applied commit
- Compatibility / migration / rollback considerations

単なる文言修正、Current runtime refresh、作業進捗、Bug fixだけでDesign Deltaを作らない。

Design Deltaは「元Designを残したまま履歴を積む」Contractの補助記録である。Deltaがあることを理由に元Design履歴を削除・置換しない。

## System / Feature-bundle Document

次の場合に作成または既存Documentを更新する。
- 複数Featureが1つのSystem責務を形成する
- reusable Moduleとして安定した
- stable internal/external Interfaceを持つ
- State/Data ownershipが複雑
- Runtime / Failure / Recovery / Security / Operation理解が保守に必要
- READMEだけでは別のworkerが安全に継続できない

必要項目だけ選ぶ。
- Purpose / Scope
- Architecture / Components
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

空SectionをTemplate充足のためだけに作らない。

## Specialized Documents

必要な場合だけ分離する。
- Contract: API / CLI / MCP / Event / Webhook契約が複雑
- Data/State Ownership: 永続状態や複数Systemの所有境界が複雑
- Operations / Recovery: 常駐Serviceや障害復旧が必要
- Security: Auth/Permission/Public endpoint/User data境界が重要
- Verification / Acceptance: 完成条件/E2E/Provider検証を独立管理する価値がある
- Migration / Compatibility: Schema/API/Storage/Runtime移行がある
- ADR: 重要Tradeoffを伴うArchitecture decisionを後から説明する必要がある

## Documentation Gate

変更後に次を判定する。

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

判定基準:
- Current completed / verified state変更 -> README
- File/Directory/主要責務/Entry Point変更 -> Tree
- Architecture/Responsibility baseline正式変更 -> 元Designへの履歴追記 + Delta要否判定
- stable System/ModuleをREADMEだけでは安全に引継げない -> System Document

判定対象は原則として**現在作業している対象Project**である。server-coreのDocumentation Gateは、server-core自体の変更についてexplicit owner authorizationがある場合だけ適用する。

Requiredなのに未更新ならDocumentation Completeではない。RequiredでないDocumentは追加しない。

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

Moduleは再利用、交換、独立修正、権限/障害分離等の実益がある責務単位とする。

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

通常Taskの起点:
- 目的と期待結果
- Current GitHub state
- 対象責務
- 再利用候補
- Input / Output
- 直接依存と制約
- 関連Test / verify path

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

Process起動、Error無し、HTTP 200、Build成功、CI greenだけでは、Task全体のPASSとしない。

## GitHub

Commit / PRを実作業履歴の正本とする。

Commitは必要に応じてPurpose、material changes、affected scope、verification、documentation、remaining/unverified workを追える作業報告にする。

Commit / Push / Remote Readback / PR / PR Current Sync / CI / Merge / Deploy / Runtime / Productionを別状態として扱う。

Open PRが存在する場合は、Push/Remote Readback後にPR head/bodyをCurrent HEADへ同期し、古いPR本文を残したままGitHub履歴完了としない。詳細は `docs/AUTO_COMMIT.md`。

## Credential / Environment

共有が必要なkey名は値なし `.env.example` に記載可能。

Credential実値をGitへ保存しない。Workspace shared credential contractがある場合はBroker contractを利用し、Projectへ実値を複製しない。

## 実行順序

```text
目的と期待結果
  -> server-core routing / fixed routine
  -> Project README
  -> Current GitHub state / Commit / PR
  -> mutation/read-only repository lock
  -> Project内のREADME-linked Design / Tree / Delta / System Document
  -> Source / Test
  -> reuse check
  -> executor / cost routing
  -> implementation / debug
  -> verification
  -> Project documentation gate
  -> GitHub work history
  -> PR Current sync when PR exists
  -> remote/runtime verification when required
```
