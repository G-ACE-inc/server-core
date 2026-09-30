# DEPLOY RUNBOOK

## 目的

GitHub上で確認できる対象RevisionからServerへ反映し、DeployとRuntime検証をSource開発から分離する。

本RunbookはMasterのProduction承認を代替しない。

## Standard Source-to-Server Flow

```text
Development / Debug
  -> Test / Verify
  -> Documentation Gate
  -> Commit
  -> Push
  -> Remote Readback
  -> PR / CI when required
  -> confirmed GitHub revision
  -> Master approval when required
  -> Server deploy
  -> Runtime verification
```

Server上の直接編集を通常の修正経路にしない。Runtime上で修正必要性を発見した場合は、原則Repository開発Loopへ戻してGitHub履歴を作る。

## Preconditions

Deploy前に必要範囲で確認する。
- target Project / repository
- target branch / tag / commit SHA
- GitHub remote readback
- required PR / CI state
- current Server checkout / deployed revision
- Project-specific deploy contract / runbook
- `.env` / Secret実値を表示・転記・commitしない
- Master承認が必要なProduction / 公開 / 切替で承認済みである

## Server Readback Before Change

必要範囲で確認する。
1. 対象Path / Repository identity
2. current branch / revision
3. `git status --short --branch`
4. current Docker / Compose state
5. current health / endpoint state
6. uncommitted / local-only changesの有無

Server側に未管理変更がある場合、それを破棄・上書きして進めない。

## Deployment Revision

Deploy対象は、可能な限りGitHubでremote readback済みの具体的Revisionへ結び付ける。

`latest`、記憶上のbranch状態、LocalだけのCommitをProduction Revisionの証拠にしない。

Project固有方式がある場合はそのRunbookを優先するが、最終的に「どのSource revisionを反映したか」を追跡可能にする。

## Docker / Compose

本番常駐の標準RuntimeはDocker / Docker Compose。

Project固有手順がある場合はそちらを優先する。

典型例:

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

これらのCommandはProject固有Path / Compose file / profileを確認した後に使う。推測で実行場所やFile名を作らない。

## Runtime Verification

Container `up`だけでDeploy PASSとしない。

必要な範囲で確認する。
- expected container/process state
- healthcheck
- endpoint / API result
- expected state change
- state that must not change
- dependent service behavior
- log/error evidence
- major failure condition
- deployed revisionとの対応

Build PASS / Deploy PASS / Runtime PASS / Production PASSを分離する。

## Failure

DeployまたはRuntime Verifyに失敗した場合:
- 成功扱いしない
- 自動で次の公開/切替へ進まない
- causal evidenceを保存する
- rollbackが安全か判断する
- Source修正が必要ならGitHub development loopへ戻す

Server上で応急編集して正本と分岐させない。

## Rollback

RollbackはProject固有Contractを優先する。

共通原則:
- rollback対象revisionを特定
- Data / Schema compatibilityを確認
- rollback前後のRuntimeを検証
- rollback実施をGitHub Sourceの修正完了と混同しない

## Prohibitions

Masterの明示承認なしに:
- Production deploy / 公開 / 切替
- 既存Serviceのstop / restart / recreate（診断と分離）
- Secret変更
- Provider Resource変更

常時禁止:
- Secret実値のChat / Git / Log / Document出力
- 未検証状態をPASS報告
- Server直編集をGitHub Sourceへ反映済みと扱う
- 別Projectをついでに変更する
