# AUTO COMMIT / GITHUB WORK REPORT

## 目的

AI / Developerの作業結果をGitHubへ確実に残し、Commitだけでも実作業の目的・変更・検証・未完状態を後から追えるようにする。

## Completion Rule

ファイル変更を伴う完成作業は、Masterが明示的に禁止した場合を除き、対象Repositoryの標準に従ってcommit / pushする。

ただし次を分離する。

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

CommitやPushが成功しても、CI / Deploy / Runtime / Productionを推測でPASSにしない。

## Commit = Work Report

Commitは単なる保存点ではなく、実作業報告として扱う。

件名は変更の目的・内容が一文で分かる形にする。

必要な場合は本文へ次を残す。

```text
Purpose:
- なぜこの作業をしたか

Changed:
- 主要変更

Affected:
- 影響範囲

Verified:
- 実行したTest / Verifyと結果

Docs:
- README / Tree / Delta / System Document等の更新

Remaining:
- 未完 / 未検証 / Blocked / Unknown
```

全項目を毎回埋める必要はない。単純な変更は簡潔にし、複雑な変更・Debug・設計差分・部分完了では必要な情報を残す。

Designとの差・変更理由をCommit本文だけに閉じ込めない。Design Deltaが必要な変更では正式Deltaも更新する。

## Commit Message Types

推奨:
- `Feat:` 新機能・新定義
- `Fix:` Bug / defect修正
- `Docs:` 文書のみ
- `Chore:` 設定・Tool・運用
- `Refactor:` 外部動作を変えない構造改善
- `Test:` Test / verification変更

既存Repositoryに正式Conventionがある場合はそちらを優先する。

## Before Commit

最低限確認する。
- 対象Repository / Branch / HEAD
- `git status --short --branch`
- Diff
- Secret / credential / debug残骸 / 意図しない削除が無い
- 必要なTest / Verify
- Documentation Gate

Documentation Gate:

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Requiredなのに未更新ならDocumentation Completeとしない。

## Standard Script

Repositoryに `scripts/ai-auto-commit.sh` があり、そのRepositoryのCurrent運用で有効な場合:

```bash
scripts/ai-auto-commit.sh --push
```

Message指定:

```bash
scripts/ai-auto-commit.sh --push -m "Fix: xxxxxx"
```

Scriptの存在だけで安全性を推測しない。対象RepositoryのCurrent Scriptを確認する。

server-core既存scriptの主な責務:
- 変更File確認
- `.env` 系commit拒否
- secretらしい値の簡易検出
- `git diff --check`
- shell script `bash -n`
- stage / commit
- `--push` 時のcurrent branch push

## Remote Readback

Push/write成功だけでGitHub反映済みとしない。

必要な作業ではremote branch / commit SHA / changed file / PR head等を再取得して確認する。

## Multiple Repositories

複数Repositoryへ変更した場合はRepositoryごとに履歴を分離する。

1つのCommitで別Repositoryの変更を表現しない。

各Repositoryで対象SHAと状態を報告できるようにする。

## Stop / Exception Conditions

次の場合は自動Commit/Pushを継続せず、Current Taskの安全境界に従う。
- Secret / `.env` 実値がDiffへ混入
- 対象外Fileの変更
- 未検証の壊れた途中状態をRemoteへ載せる合理的理由がない
- Masterがcommit / push禁止を明示
- Branch / Repository identityが不明
- 他作業者の未commit差分と分離できない

Production起動・公開・切替を含むかどうかはCommit/Pushとは別Approval Boundaryとして扱う。

## Prohibitions

- 未実行TestをPASSとCommit本文へ書く
- 失敗や未検証を隠す
- Current仕様Documentを時系列作業日誌の代替にする
- Secret値をCommit message / Diff / Documentへ書く
- DesignをCurrent実装へ上書きして差分履歴を消す
