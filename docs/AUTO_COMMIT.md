# AUTO COMMIT / GITHUB WORK HISTORY

## Purpose

Source/config/document changesをGitHubへ追跡可能な形で残し、後から目的・変更・検証・未完状態を確認できるようにする。

## 1. State Separation

```text
SOURCE
LOCAL_TEST
COMMIT
PUSH
REMOTE_READBACK
PR
CI
MERGE
DEPLOY
RUNTIME
PRODUCTION
```

前段の成功から後段の成功を推測しない。

## 2. Commit / Push Policy

Commit / Pushは対象RepositoryのCurrent policyとTaskのchange boundaryに従う。

- File変更がある場合、GitHub履歴へ残すことを標準とする。
- Pushが許可されているRepository/Branchではremote readbackまで行う。
- Branch保護、review/PR、merge approval等はRepository policyを優先する。
- 一時的なセッション指示や個別作業ルールをRepository共通仕様として固定しない。

## 3. Commit = Work History

Commit件名は変更の目的・内容が分かる形にする。

複雑な変更では本文に必要な範囲で残す。

```text
Purpose:
- why

Changed:
- material changes

Affected:
- affected scope

Verified:
- test / verification actually executed

Docs:
- authority/docs updated when required

Remaining:
- pending / blocked / unknown
```

単純な変更へ不要な定型文を強制しない。

Design変更理由をCommit本文だけに閉じ込めず、Architecture/Responsibility baselineが変わる場合はDesign Deltaを更新する。

## 4. Commit Message Types

Repositoryに正式Conventionがある場合はそちらを優先する。

一般例:
- `feat:` new capability
- `fix:` defect fix
- `docs:` documentation only
- `chore:` tooling/config/maintenance
- `refactor:` behavior-preserving structure change
- `test:` test/verification change

## 5. Before Commit

最低限確認する。
- target repository / branch / HEAD
- `git status --short --branch`
- intended diff
- credential / `.env`実値 / debug residue / unintended deletionが無い
- applicable test / verify
- documentation impact

## 6. Standard Script

Repositoryに `scripts/ai-auto-commit.sh` がありCurrent運用で有効な場合のみ利用する。

```bash
scripts/ai-auto-commit.sh --push
```

Message指定例:

```bash
scripts/ai-auto-commit.sh --push -m "fix: describe change"
```

Scriptの存在だけで安全性やPush権限を推測しない。Current ScriptとRepository policyを確認する。

server-core scriptの責務:
- changed file確認
- `.env`系commit拒否
- secret-like patternの簡易検出
- `git diff --check`
- shell script syntax check
- stage / commit
- `--push` 指定時のcurrent branch push

## 7. Remote Readback

Push成功だけでGitHub反映済みとしない。

必要な作業ではremote branch / commit SHA / changed file / PR head等を再取得して確認する。

## 8. Multiple Repositories

複数Repositoryを変更した場合はRepositoryごとに履歴を分離する。

各RepositoryのSHA、branch、verification stateを追跡できる状態にする。

## 9. Stop / Exception Conditions

次の場合は自動Commit/Pushを止め、対象RepositoryのCurrent boundaryを確認する。
- credential / `.env`実値がDiffへ混入
- target外Fileの変更
- Branch / Repository identityが不明
- 他作業の未commit差分と分離できない
- repository policyがPush/PR routeを要求している
- failing/incomplete stateをremoteへ残す理由とscopeが不明

Production publish/deployはCommit/Pushとは別のchange boundary。

## 10. Invariants

- 未実行TestをPASSと記録しない。
- failure / unverified stateを隠さない。
- Current仕様Documentをchronological work logの代替にしない。
- credential実値をCommit message / Diff / Documentへ書かない。
- Design BaselineをCurrent実装へ追従させるだけの履歴消しをしない。
