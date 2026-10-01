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

## 3. Repository Lock

Commit / Pushの対象は、今回の `MUTATION_REPOSITORIES` に含まれるRepositoryだけ。

server-coreやShared Capability owner RepositoryをAuthority確認のために読んだだけなら、そのRepositoryをCommit対象にしない。

Commit前に最低限次を一致させる。

```text
INTENDED_REPOSITORY
CURRENT_GIT_TOPLEVEL
CURRENT_BRANCH
INTENDED_DIFF
```

Local Gitでは必要に応じて `git rev-parse --show-toplevel` を使い、TaskのTARGET_REPOSITORYと一致していることを確認する。

別RepositoryのScriptをabsolute pathで呼んだこと、別Repositoryへ一時的に `cd` したこと、共通Authorityを読んだことを、Commit対象変更の根拠にしない。

複数Repositoryを変更した場合はRepositoryごとにCommit / Push / Remote Readbackを分離する。1つのRepositoryのCommitへ別Projectの変更を混在させない。

## 4. Commit = Work History

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

## 5. Commit Message Types

Repositoryに正式Conventionがある場合はそちらを優先する。

一般例:
- `feat:` new capability
- `fix:` defect fix
- `docs:` documentation only
- `chore:` tooling/config/maintenance
- `refactor:` behavior-preserving structure change
- `test:` test/verification change

## 6. Before Commit

最低限確認する。
- target repository / branch / HEAD
- current Git top-level
- repositoryが `MUTATION_REPOSITORIES` に含まれる
- `git status --short --branch`
- intended diff
- credential / `.env`実値 / debug residue / unintended deletionが無い
- applicable test / verify
- documentation impact

## 7. Standard Script

**対象Repository自身に** `scripts/ai-auto-commit.sh` がありCurrent運用で有効な場合のみ利用する。

```bash
scripts/ai-auto-commit.sh --push
```

Message指定例:

```bash
scripts/ai-auto-commit.sh --push -m "fix: describe change"
```

server-coreに同名Scriptがあることを理由に、他Projectの変更をserver-coreからCommitしない。対象Projectが独自helperを持たない場合は、そのProjectの通常Git運用を使う。

Scriptの存在だけで安全性やPush権限を推測しない。Current ScriptとRepository policyを確認する。

server-core scriptの責務:
- server-core自身を対象としたときのchanged file確認
- `.env`系commit拒否
- secret-like patternの簡易検出
- `git diff --check`
- shell script syntax check
- stage / commit
- `--push` 指定時のcurrent branch push

## 8. Remote Readback

Push成功だけでGitHub反映済みとしない。

必要な作業ではremote branch / commit SHA / changed file / PR head等を再取得して確認する。

Remote readbackも対象Repositoryごとに行う。

## 9. Multiple Repositories

複数Repositoryを変更した場合はRepositoryごとに履歴を分離する。

各RepositoryのSHA、branch、verification state、変更理由を追跡できる状態にする。

1つのTaskに複数Repositoryが登場することと、複数Repositoryへwriteが必要であることは同義ではない。

## 10. Stop / Exception Conditions

次の場合は自動Commit/Pushを止め、対象RepositoryのCurrent boundaryを確認する。
- credential / `.env`実値がDiffへ混入
- target外Fileの変更
- Branch / Repository identityが不明
- current Git top-levelが意図したRepositoryと一致しない
- Repositoryが `MUTATION_REPOSITORIES` に含まれない
- 他作業の未commit差分と分離できない
- repository policyがPush/PR routeを要求している
- failing/incomplete stateをremoteへ残す理由とscopeが不明

Production publish/deployはCommit/Pushとは別のchange boundary。

## 11. Invariants

- 未実行TestをPASSと記録しない。
- failure / unverified stateを隠さない。
- Current仕様Documentをchronological work logの代替にしない。
- credential実値をCommit message / Diff / Documentへ書かない。
- Design BaselineをCurrent実装へ追従させるだけの履歴消しをしない。
- Authorityを読んだだけのRepositoryへwrite/commitしない。
