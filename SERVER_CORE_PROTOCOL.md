# SERVER CORE OPERATION PROTOCOL

Version: 2026-09-30
Role: G-ACE Workspace Command Centerの共通運用・承認・安全境界。

## Purpose

G-ACE Workspace全体で共通に適用するAuthority、変更権限、GitHub、Runtime、Secret、Storageの**共通境界だけ**を定める。

server-coreは司令室としてTaskをRouting/Dispatchするが、Project固有実装のownerにはならない。

開発方法論、Project構成、Context routing、Deploy、KB、Storage lifecycle等の詳細をここへ重複記載しない。作業は `README.md` -> `docs/LOAD_SCOPE.md` から必要Authorityだけ読む。

人間、AI、自動処理のすべてに適用する。

## Authority / Approval

最終決定者はMaster（Product目的・仕様・重要なUX・公開/Release・費用/Provider/Model方針・Secret権限・不可逆Data・最終受入）。AIは明示された目的・Scope・Current Rule内の通常技術判断と実行を担当する。質問・提案・説明は承認ではない。

### 明示的Master Gate（維持）
- main / PR merge、正式Release、Public exposure/公開範囲の拡大・切替
- Force push、Branch削除、destructive reset/rebase、不可逆/破壊的なpersistent-state変更
- Secret追加/削除/rotation、Provider resourceの作成/変更/削除やCost/Policy変更
- 新規Model download / Model方針変更（既存の明示承認Scope外）
- Current Project Ruleが明示的にMaster Gateとする操作

### Runtime委任の判定
Production deploy、restart/recreate、reflection、rollback等は操作名だけで無条件にMaster Gateとしない。ただし委任が未検証のProduction操作・稼働Service変更は既存Master承認を要求し、承認を推測しない。

Master Internalに限り、Current GitHub Project #1の登録に加えて operations/master-internal-repositories.json の明示entryとHost private admissionの一致、Repo immutable ID/owner/admin、Project item、server project/path、runtime/Compose、allowed branch/operation/scope/paths、enabled/unrevoked、Protected effectsの全検証が成立する場合にのみ MASTER_INTERNAL_PERSISTENT を認める。現在の登録はDebugAI 1 Repoだけ。他Repoは登録済みと仮定しない。

永続なのはRepo委任だけ。各実行でFresh exact SHA/remote/ancestry、Scope、request identity、target/healthを検証し、Hostが短命single-use receiptを発行・消費する。CHAT本文・human_approved=true・GitHub Project item単独はRuntime credentialではない。無効・不一致・未登録・失効・revokeはfail-closed。Registry変更・Repo追加は既存のreviewed registration/Host admission/readback/auditを通す。

旧manual完全承認経路と有限Standing Delegationを維持する。外部顧客・販売・License・Subscription・AsteraAPPへMaster Internal権限を継承しない。将来販売用の経路はこのChange Unitでは変更しない。Host実装のOwnerはDebugAI、server-coreは登録/経路/共通境界のみを所有する。

## Workspace Entry / Command Dispatch

```text
server-core/README.md
  -> server-core/docs/LOAD_SCOPE.md
  -> 今回必要なserver-core Authorityだけ
  -> 対象Project README
  -> 必要なProject Authority / Source / Testだけ
```

全正本を一括読込しない。

Workspace正規仕様: `docs/G_ACE_WORKSPACE.md`  
Discovery: `docs/WORKSPACE_REGISTRY.md`  
server-core Design: `docs/SERVER_CORE_DESIGN.md`  
Design差分: `docs/DESIGN_DELTA.md`

## Development Boundary

- 開発方法論・再利用・5段Architecture・Module判断: `CORE.md`
- Project構成、README / Design / Project Tree / Design Delta / System Document、Documentation Gate: `docs/PROJECT_TEMPLATE.md`
- DesignをCurrent実装へ合わせて履歴が消える形で上書きしない。
- Project固有の実装・Design・System仕様は各Project側に置く。
- 公開契約は可能な限りCode上のInterface / Type / Schemaを正本とする。

## Validation

必要範囲で確認する。
- Input
- execution condition
- expected output
- changed state
- state that must not change
- regression
- major failure cases
- Runtime / Provider readback when relevant

Process起動、Error無し、`True`、空配列、HTTP 200、Build成功、CI greenだけではPASSとしない。

未実行・未確認・未検証は `NOT_EXECUTED / UNKNOWN / NOT_VERIFIED` を維持する。

## Documentation / Work History

Current仕様Documentへ作業日誌を混在させない。

作業履歴の正本はGitHub commit / PR。Commitは実作業報告として扱う。

完成・検証状態、Project構造、Designとの差、完成System等が変わった場合はDocumentation Gateに従う。

Commit / Push / Remote Readbackは `docs/AUTO_COMMIT.md` を正とする。

## GitHub / Deploy

GitHub revisionとServer Runtimeを別状態として扱う。

```text
implementation / fix
 -> verify
 -> documentation gate
 -> commit as work report
 -> push
 -> remote readback
 -> PR / CI when required
 -> confirmed GitHub revision
 -> Current impact / delegation / Master Gate check
 -> Master approval if gated; otherwise verified Host authorization
 -> bounded Server deploy / runtime operation
 -> exact Runtime verification
```

Deploy詳細は `docs/DEPLOY_RUNBOOK.md`。

Server上の直接Source修正を正式開発履歴の代替にしない。Runtime修正が必要でも原則Repository開発Loopへ戻す。

## Shared Capability Boundary

server-coreは共有Capabilityの実装本体を抱え込まず、Discovery・接続契約・所有者・権限境界・Availability stateを管理する。

Discovery Authority: `docs/WORKSPACE_REGISTRY.md`

Registry記載だけでCurrent Runtimeを証明しない。必要時は実設定・Provider・Endpoint・Docker・GitHub等をreadbackする。

### DebugAI

DebugAIは独立Project/runtime。Sourceのmain、開発feature、実稼働runtimeは別状態として扱う。

既存DebugAI MCPの13 tools、bounded Server Command、guarded GitOps、exact HEAD/health readbackは指定されたLive Revisionで検証済み。Master Internal Persistent DelegationもDebugAI 1 RepoでRuntime E2E済み。正確な最新稼働Revision・enrollment/allowed scopeはOwner Current #41、`operations/master-internal-repositories.json` と実Host readbackで確認する。Registryの過去成功を将来のRuntime PASSとしない。

Workspace/server作業ではこの既存のbounded経路を優先する。ChatGPTアプリ直接remote MCP connectorは未検証、他RepoのHost登録も未検証。DebugAI製品全体・統合開発Log完成を推定しない。旧manual approvalを販売用途へ変更しない。

### Reusable KB

再利用開発KBのDesign Baselineは `docs/KB_REUSE_DESIGN.md`。

Target storageはMaster PC `F:` 1 TB drive。server-coreはKB data本体を保持せずAccess / Registration / Lifecycle / Safety Contractだけを管理する。

VPSからPC filesystemを直接読める前提を置かず、実装・検証済みAPI/MCP等のBridgeを使う。

禁止:
- 生ログの直接KB化
- 判定基準なしの自動知識化
- 未検証AI出力をvalidated assetとして登録
- Secret / Token / credentialのKB保存
- 未実装Bridgeを利用可能として扱う

## Log / Cache / Cleanup / Backup

詳細Design Baselineは `docs/STORAGE_LIFECYCLE.md`。

共通境界:
- Telegram: owning Project contractで定義されたdurable raw-log authority
- Meilisearch: rebuildable search index
- Redis: dedup / hot-cache
- `/home/admin1/logs`: temporary operational disk state
- VPS: processing/runtime environment
- `/home/admin1/backups`: backup area。generic cleanup対象ではない

Generic automatic cleanupはfail-closed。

次を自動削除しない。
- owner不明
- active use
- 未送信 / retry pending
- recovery required
- active transaction / lock
- restore/rebuild path不明
- Docker volumeを含むpersistent state

`docker system prune -a --volumes` の汎用定期実行は禁止する。

## Docker / Runtime

本番常駐の標準経路はDocker / Docker Compose。

Hostのnode / python / pm2 / nohup / screen / tmux等を新しい本番常駐経路として追加しない。短時間の診断・検証Commandとは区別する。

Container起動だけでRuntime PASSとせず、必要なEndpoint / Output / State / side effectまで確認する。

## Secret / Token

Secret / Token / password / session / credentialをGit / Chat / Log / Documentへ保存しない。

`.env` はcommit禁止。共有が必要なkey名は値なし `.env.example` に記載できる。

Workspace共有Secretは `docs/WORKSPACE_SHARED_SECRETS.md` を正とし、各Projectへ実値を複製しない。

## Archive

旧版・退避は `archive/YYYY-MM-DD/` を基本とする。

- Secretをarchiveへ保存しない
- archiveをCurrent state / Design / Ruleとして扱わない
- 通常Contextへ入れない

## Absolute Prohibitions

- 推測を事実として扱う
- 未実行を実行済み、未検証をPASSにする
- Testをskip/deleteして完成扱いにする
- Design履歴を消す上書き
- 作業履歴をCurrent仕様文書へ混在
- 目的のないFile / Document / Module追加
- Secret / Token実値の保存・commit
- 未実装Capabilityを利用可能として扱う
- `/home/admin1/logs` を永続保管庫として使う
- KBへの無判定直接投入
- Server cleanupでowner不明・active・recovery dataを削除
- server-coreへProject固有実装を司令室都合だけで移す
