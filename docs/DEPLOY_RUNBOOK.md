# DEPLOY RUNBOOK

## Purpose

GitHub上で確認できるRevisionからServerへ反映し、Source開発、Deploy、Runtime verificationを分離して追跡する。

本RunbookはProject固有のrelease/runbookやProvider approval contractを置き換えない。

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
  -> required deploy / production approval
  -> Server deploy
  -> Runtime verification
```

Server上の直接編集を通常の修正経路にしない。Runtimeで修正必要性を発見した場合は原則Repository development loopへ戻す。

## 2. Preconditions

Deploy前にTaskに必要な範囲で確認する。
- target Project / repository
- target branch / tag / commit SHA
- GitHub remote readback
- required PR / CI state
- current Server checkout / deployed revision
- Project-specific deploy contract / runbook
- credential値を表示・転記・commitしない経路
- required deploy / production approval state
- rollback/recovery method when applicable

## 3. Server Readback Before Change

必要範囲で確認する。
1. target path / repository identity
2. current branch / revision
3. `git status --short --branch`
4. current Docker / Compose state
5. current health / endpoint state
6. local-only / uncommitted changes
7. Project-specific runtime configuration owner

Server側に未管理変更がある場合、それを破棄・上書きして進めない。

## 4. Deployment Revision

Deploy対象はGitHubでremote readback済みの具体的Revisionへ結び付ける。

`latest`、記憶上のbranch状態、Local-only commitをProduction Revisionの証拠にしない。

Project固有方式がある場合はそのRunbookを優先するが、最終的に「どのSource revisionを反映したか」を追跡可能にする。

## 5. Docker / Compose

本番常駐の標準RuntimeはDocker / Docker Compose。Project固有の正式例外がある場合は対象Project Authorityを優先する。

典型例:

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

実行Path / Compose file / profile / service nameをCurrent Project Authorityで確認してから使う。推測で作らない。

## 6. Runtime Verification

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

Build PASS / Deploy PASS / Runtime PASS / Production PASSを分離する。

## 7. Failure

DeployまたはRuntime Verifyに失敗した場合:
- success扱いしない
- 次のpublish/cutoverへ自動で進まない
- causal evidenceを保存する
- partial changeの有無を確認する
- rollbackが安全か判断する
- Source修正が必要ならGitHub development loopへ戻す

Server上で応急編集してRepository Sourceと恒久分岐させない。

## 8. Rollback

RollbackはProject固有Contractを優先する。

共通原則:
- rollback target revisionを特定
- Data / Schema compatibilityを確認
- rollback前後のRuntimeを検証
- rollback実施をSource修正完了と混同しない
- rollback不能/危険な場合はforward-fix routeを明示する

## 9. Mutation / Approval Boundary

次はread-only確認と別Operationとして扱う。
- Production deploy / publish / cutover
- active service stop / restart / recreate
- credential mutation
- Provider resource mutation

必要な承認主体と条件は対象Project / Provider / Repository Authorityを正とする。個人名・会話上の呼称をRunbook仕様へ固定しない。

## 10. Credential Boundary

- credential実値をGit / Source / Document / Logへ保存しない。
- credentialを表示することをverification方法にしない。
- deploy用Secretのowner/injection方法はProject/Workspace credential contractを正とする。

## 11. Completion Evidence

Deploy完了を主張する場合、Taskに応じて少なくとも次を追跡可能にする。

```text
SOURCE_REVISION
SERVER_REVISION
DEPLOY_ACTION
RUNTIME_VERIFY_RESULT
DEPENDENCY_VERIFY_RESULT when required
ROLLBACK_STATE
PRODUCTION_STATE when applicable
```

Project-specific release gateがより厳しい場合はそちらを優先する。
