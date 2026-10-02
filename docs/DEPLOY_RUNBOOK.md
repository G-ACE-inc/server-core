# DEPLOY RUNBOOK

## Purpose

GitHub上で確認できるRevisionからServerへ反映し、Source開発、Deploy、Runtime verificationを分離して追跡する。

本RunbookはProject固有のrelease/runbookやProvider approval contractを置き換えない。

本Runbookがserver-core内に存在することを、server-core自身がDeploy対象である根拠にしない。Deploy targetは対象Project / Repository / Runtime Authorityで決定する。

## 1. Standard Source-to-Server Flow

```text
Development / Debug
  -> Test / Verify
  -> Documentation Gate
  -> Commit
  -> Push
  -> Remote Readback
  -> PR / CI when required
  -> confirmed GitHub revision
  -> target runtime identity lock
  -> required deploy / production approval
  -> target Project-owned deploy procedure
  -> Runtime verification
```

Server上の直接編集を通常の修正経路にしない。Runtimeで修正必要性を発見した場合は原則Repository development loopへ戻す。

## 2. Preconditions

Deploy前にTaskに必要な範囲で確認する。
- TARGET_PROJECT
- TARGET_REPOSITORY
- TARGET_RUNTIME / target path
- target branch / tag / commit SHA
- GitHub remote readback
- required PR / CI state
- current Server checkout / deployed revision
- Project-specific deploy contract / runbook
- exact deploy command source
- credential値を表示・転記・commitしない経路
- required deploy / production approval state
- rollback/recovery method when applicable

`TARGET_PROJECT` / `TARGET_REPOSITORY` / `TARGET_RUNTIME` / exact deploy procedureのいずれかが不明な場合、推測でDeployしない。

## 3. Target Identity Lock

Deploy commandを実行する前に、SourceとRuntimeのownerを一致させる。

```text
SOURCE_PROJECT
SOURCE_REPOSITORY
SOURCE_REVISION
SERVER_TARGET_PATH
RUNTIME_OWNER
PROJECT_DEPLOY_AUTHORITY
EXACT_DEPLOY_PROCEDURE
COMPOSE_PROJECT / SERVICE when applicable
EXPECTED_ENDPOINT / HEALTH when applicable
```

server-core、shared capability owner、別Projectを事前確認のために読んだことを、Deploy target変更の理由にしない。

複数Projectが同一Server上に存在しても、対象Project以外のcheckout / Compose / container / service / volumeを同じDeploy操作へ含めない。

## 4. Server Readback Before Change

必要範囲で確認する。
1. target path / repository identity
2. current branch / revision
3. `git status --short --branch`
4. current Docker / Compose state
5. current health / endpoint state
6. local-only / uncommitted changes
7. Project-specific runtime configuration owner
8. exact Project-owned deploy command / procedure

Server側に未管理変更がある場合、それを破棄・上書きして進めない。

Current working directoryだけでtargetを判断しない。対象Path / Repository identityを明示確認する。

## 5. Deployment Revision

Deploy対象はGitHubでremote readback済みの具体的Revisionへ結び付ける。

`latest`、記憶上のbranch状態、Local-only commitをProduction Revisionの証拠にしない。

Project固有手順がある場合も、最終的に「どのSource revisionをどのRuntimeへ反映したか」を追跡可能にする。

## 6. Docker Compose

本番常駐は **Docker Composeを正** とする。Host上の `node` / `python` / `npm start` / `pm2` / `nohup` / `screen` / `tmux` 等を本番常駐経路として採用しない。

**server-coreの共通Runbookはgeneric deploy commandを提供しない。** `docker compose build` / `up` / restart / recreate等の実行Commandは、対象ProjectのCurrent Authorityでexact path、Compose file、profile、service、revision、approval boundaryが確定している場合だけ使用する。

共通Runbookにありがちな例示Commandをcopyして実行する運用は禁止する。対象Project側にexact procedureが無ければ、先にそのProject AuthorityでDeploy手順を確定し、server-coreの存在だけを根拠にCommandを生成しない。

別ProjectのCompose directoryで同名commandを実行しない。Compose Project / service identityを対象Runtimeと照合する。

## 7. Runtime Verification

Container `up`だけでDeploy PASSとしない。

必要範囲で確認する。
- expected container/process state
- healthcheck
- endpoint / API result
- expected state change
- state that must not change
- dependent service behavior
- log/error evidence
- important failure condition
- deployed revisionとの対応
- unrelated Project/serviceが意図せず変化していないこと

Build PASS / Deploy PASS / Runtime PASS / Production PASSを分離する。

## 8. Failure

DeployまたはRuntime Verifyに失敗した場合:
- success扱いしない
- 次のpublish/cutoverへ自動で進まない
- causal evidenceを保存する
- partial changeの有無を確認する
- rollbackが安全か判断する
- Source修正が必要なら対象Repository development loopへ戻す

Server上で応急編集してRepository Sourceと恒久分岐させない。

Failure調査のため別Project/Shared Capabilityを確認しても、そのSourceへ自動的に修正を入れない。owner側変更が必要なら別mutation targetとして確定する。

## 9. Rollback

Rollbackは対象ProjectのData / Schema / Runtime契約を確認して行う。

共通原則:
- rollback target revisionを特定
- Data / Schema compatibilityを確認
- rollback前後のRuntimeを検証
- rollback実施をSource修正完了と混同しない
- rollback不能/危険な場合はforward-fix routeを明示する

Rollback targetもTARGET_PROJECT / TARGET_RUNTIME内に限定する。

## 10. Mutation / Approval Boundary

次はread-only確認と別Operationとして扱う。
- Production deploy / publish / cutover
- active service stop / restart / recreate
- credential mutation
- Provider resource mutation

必要な承認主体と条件は対象Project / Provider / Repository Authorityを正とする。個人名・会話上の呼称をRunbook仕様へ固定しない。

Read-only Server checkやSource syncを、service restart / recreate / provider mutationの承認として扱わない。

Deploy Commandを提示・実行できること自体を、実行承認済みと扱わない。

## 11. Credential Boundary

- credential実値をGit / Source / Document / Logへ保存しない。
- credentialを表示することをverification方法にしない。
- deploy用Secretのowner/injection方法はProject/Workspace credential contractを正とする。

## 12. Completion Evidence

Deploy完了を主張する場合、Taskに応じて少なくとも次を追跡可能にする。

```text
TARGET_PROJECT
TARGET_REPOSITORY
SOURCE_REVISION
SERVER_TARGET
SERVER_REVISION
PROJECT_DEPLOY_AUTHORITY
DEPLOY_ACTION
RUNTIME_VERIFY_RESULT
DEPENDENCY_VERIFY_RESULT when required
UNRELATED_TARGET_CHANGE=NONE
ROLLBACK_STATE
PRODUCTION_STATE when applicable
```

Project固有release gateがより厳しい場合はそちらを追加で満たす。
