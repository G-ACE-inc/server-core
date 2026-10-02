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

**server-coreは例外的に追加Gateを持つ。** `MUTATION_REPOSITORIES` に含まれているという自己申告だけでは不十分で、server-core自体の変更についてexplicit owner authorizationがあり、`SERVER_CORE_MUTATION_AUTHORIZED=YES` が成立している場合だけserver-coreへwrite / commit / pushできる。AI/Agent自身がこの値を推測でYESへ変更してはならない。

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
- **server-coreの場合は `SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示的に成立している**
- `git status --short --branch`
- intended diff
- credential / `.env`実値 / debug residue / unintended deletionが無い
- applicable test / verify
- documentation impact

## 7. server-core Commit Helper

`/home/admin1/server-core/scripts/ai-auto-commit.sh` は**server-core専用**。他Projectをcommitする汎用helperではない。

server-core自体の変更についてexplicit owner authorizationがあり、feature branch上である場合だけ使用する。

```bash
scripts/ai-auto-commit.sh --authorize-server-core-mutation --push
```

Message指定例:

```bash
scripts/ai-auto-commit.sh --authorize-server-core-mutation --push -m "fix: describe change"
```

Helperは次をfail-closedで確認する。
- `--authorize-server-core-mutation` が明示されている
- Script自身の所在から解決したRepositoryがserver-core canonical checkoutである
- current branchがdetached HEADではない
- `main` / `master` への直接auto-commitではない
- `.env`系Fileが含まれない
- secret-like patternの簡易検出
- `git diff --check`
- shell script syntax check

他Projectからabsolute pathでserver-core helperを呼んでも、呼出元Projectをcommit対象にしてはならない。Helperはcurrent working directoryではなく**Script自身のRepository**へ固定される。

`--authorize-server-core-mutation` は単なるCLI convenienceではなく、すでに成立しているexplicit owner authorizationを実行時に再確認するためのGateである。AI/Agentが自分の判断だけで付けてはならない。

対象Projectに独自helperが無い場合は、そのProjectのCurrent policyに従った通常Git操作を使う。server-core helperを代用しない。

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
- **server-coreで `SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示成立していない**
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
- server-coreはexplicit owner authorization無しにwrite/commit/pushしない。
- server-core helperを他Projectのcommit手段として使用しない。
