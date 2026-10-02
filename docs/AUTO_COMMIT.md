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

Commit / Pushは対象RepositoryのCurrent policyとTask/change unitのboundaryに従う。

- File変更がある場合、GitHub履歴へ残すことを標準とする。
- Pushが許可されているRepository/Branchではremote readbackまで行う。
- Branch保護、review/PR、merge approval等はRepository policyを優先する。
- 一時的なセッション指示や個別作業ルールをRepository共通仕様として固定しない。

## 3. Repository / Change-unit Lock

Commit / Pushの対象は今回の `MUTATION_REPOSITORIES` に含まれるRepositoryだけ。

server-coreやShared Capability owner RepositoryをAuthority確認のために読んだだけなら、そのRepositoryをCommit対象にしない。

server-coreは追加Gateを持つ。server-core自体の変更についてexplicit owner authorizationがあり、`SERVER_CORE_MUTATION_AUTHORIZED=YES` がCurrent Task/change unitで成立している場合だけwrite / commit / pushできる。

Commit前に一致させる。

```text
INTENDED_REPOSITORY
CURRENT_GIT_TOPLEVEL
CURRENT_BRANCH
INTENDED_DIFF
INTENDED_FILES
```

複数Task/Agentが同一Repositoryで並行する可能性を前提とし、**今回のchange unitに属さないuncommitted diffをstageしない。** Repository全体を暗黙stageするhelperを標準にしない。

同一server-core checkoutでhelper commitが同時実行された場合、先にlockを取得したchange unitだけを進める。lock取得に失敗したhelperは待機・上書き・再試行を自動化せずfail closedし、Current HEAD / working treeを再確認してから別change unitとして再開する。

別RepositoryのScriptをabsolute pathで呼んだこと、別Repositoryへ一時的に`cd`したこと、共通Authorityを読んだことをCommit対象変更の根拠にしない。

## 4. Commit = Work History

Commit件名は変更の目的・内容が分かる形にする。複雑な変更では必要な範囲でPurpose / Changed / Affected / Verified / Docs / Remainingを残す。

未実行Testや未確認状態をPASSとして書かない。Architecture/Responsibility baselineが変わる場合はDesign Deltaも更新する。

## 5. Before Commit

最低限確認する。
- target repository / branch / HEAD
- current Git top-level
- repositoryが `MUTATION_REPOSITORIES` に含まれる
- server-coreの場合 `SERVER_CORE_MUTATION_AUTHORIZED=YES`
- Current authorizationが同じTask/change unitへscopeされている
- `git status --short --branch`
- intended files / intended diff
- unrelated working-tree changesの有無
- credential / `.env`実値 / debug residue / unintended deletionが無い
- applicable test / verify
- documentation impact

他作業の差分と今回の差分を安全に分離できない場合は自動Commitを行わない。

## 6. server-core Commit Helper

`/home/admin1/server-core/scripts/ai-auto-commit.sh` はserver-core専用。server-core自体へのexplicit owner authorizationがあり、feature branch上である場合だけ使用する。

**1件以上の`--file PATH`が必須**であり、指定Fileだけをchange unitとしてstageする。

```bash
scripts/ai-auto-commit.sh --authorize-server-core-mutation --file docs/example.md --push
```

複数File:

```bash
scripts/ai-auto-commit.sh --authorize-server-core-mutation --file README.md --file docs/example.md --push -m "docs: update execution contract"
```

Helperはfail-closedで確認する。
- explicit server-core mutation flag
- Script所在地から解決したcanonical server-core repository
- non-detached feature branch
- direct `main` / `master`拒否
- `flock`による同一checkoutのcommit change-unit直列化。lock競合時はcommitを実行しない
- safe repository-relative `--file` path
- intended Fileが実際にchangedであること
- `.env`系File拒否
- secret-like patternの簡易検出
- secret検出時は値ではなく`path:line`だけを出力
- commit messageのcredential-like value検査
- `git diff --check`
- staged setが指定File集合と一致
- changed shell scriptのsyntax check

Helperは`git add -A`を使用しない。指定していない他Taskの変更をstageしない。

`--authorize-server-core-mutation` はpermissionを新規作成するflagではなく、すでにCurrent Taskで成立しているauthorizationを実行時に再確認するGateである。

対象Projectに独自helperが無い場合は、そのProjectのCurrent policyに従う。server-core helperを他Project commitへ代用しない。

## 7. Credential Output Safety

Secret scanは完全なcredential detectorではないため、Source/Provider contract上のSecret boundary確認を置き換えない。

検出したcredential-like value自体をTerminal/CI/Commit messageへ出力しない。検出位置だけを示してfail closedする。

Binary/読取不能Fileを「安全」と推測しない。credential-bearing可能性があるFileはそのAuthorityに従って別途確認する。

## 8. Remote Readback

Push成功だけでGitHub反映済みとしない。必要な作業ではremote branch / commit SHA / changed file / PR head等を再取得して確認する。

## 9. Multiple Repositories / Workers

複数Repositoryを変更した場合はRepositoryごとに履歴を分離する。複数workerが同一Repositoryへ関与する場合もchange unitを混在させない。

各RepositoryのSHA、branch、verification state、変更理由を追跡できる状態にする。

## 10. Stop / Exception Conditions

次の場合は自動Commit/Pushを止める。
- credential / `.env`実値がDiffへ混入
- target外Fileの変更しかない
- Branch / Repository identityが不明
- Repositoryが `MUTATION_REPOSITORIES` に含まれない
- server-core authorizationがCurrent Task/change unitで成立していない
- 同一checkoutのserver-core auto-commit lockを別change unitが保持中
- 他作業のuncommitted差分と分離できない
- staged setがintended filesと一致しない
- repository policyが別Routeを要求
- failing/incomplete stateをremoteへ残す理由とscopeが不明

Production publish/deployはCommit/Pushとは別のchange boundary。

## 11. Invariants

- 未実行TestをPASSと記録しない。
- failure / unverified stateを隠さない。
- credential実値をCommit message / Diff / Document / diagnostic outputへ書かない。
- Authorityを読んだだけのRepositoryへwrite/commitしない。
- server-core helperを他Projectのcommit手段として使用しない。
- unrelated diffをrepository-wide stagingへ巻き込まない。
- concurrent helper commitを同じcheckoutで並行実行しない。
