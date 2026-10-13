# Project #1 — 既存Repo追加・再登録の実行手順

Owner: server-core / Control [Issue #10](https://github.com/G-ACE-inc/server-core/issues/10)
Scope: **Repo登録の手順**のみ。通常CHATの運用ルール（定型コマンド・Host terminal・ログ）の正本ではない。そちらは `docs/G_ACE_WORKSPACE.md` §6 と担当CHATの変更を参照。

## 目的・完了条件

追加する既存GitHub Repoを、通常CHATから既存GitHub Actions→Gateway→Receiver→Host Writer経路で使えるようにする。既存のRepo登録と稼働サービスを保持する。**GitHubで登録変更しただけでは完了ではない。Host保護Registryと新Repoの実機コマンドによる認証付きreadbackまで完了条件とする。**

追加対象はGitHub RepoとVPS実体を一致させられるものに限る。新しいProject/Workflow/MCP/Tokenは作らない。Master PCへの操作・接続・同期は対象外。既存RepoがなければMasterのProject意思決定を別途必要とする。コマンド実行の技術手順はCHATが担当する。

## 登録に必要な事実（推測禁止）

1. GitHub正本の `owner/repo`、repo ID、default branch、HEAD SHAをGitHub APIで実測。
2. VPS既存checkoutの絶対パス、`realpath`、`git rev-parse --show-toplevel`、`remote get-url origin`、`branch --show-current`、`HEAD`を既存 `host.command` の**読取Request**で実測。GitHub側とremote・HEAD/branchを照合。パス名からRepo名を推定しない。
3. 対象が実際に `.git` のあるGit checkoutか確認。Git checkoutでない稼働ディレクトリへ `git init` / `clone` / `checkout` / `reset --hard` を勝手に行わない。
4. 実行したい操作を明示：`dev.job`（隔離開発）と `host.command`（実Host操作）は**別々の登録面**。一方を登録してももう一方には効かない。
5. 実行対象Container・ComposeとGit Repoは別。既存 `docker.operation` / `service.deploy` の権限や設定は別の既存Runtime contractに従い、Repo登録だけで無条件に広げない。
6. 保護Registryの現行SHA-256、既存エントリ数、バックアップの有無、Writer socket/serviceを実機読取で確認。GitHub上の `operations/master-internal-repositories.json` はHostのdirty保護Registryとは一致しないことがある。**絶対にGitHub版で上書きしない**。

## 既存実装のどこを更新するか

| 機能 | 正本・実体 | 作業 |
|---|---|---|
| 隔離開発のRepo登録 | `operations/github-project-bounded-host.json` → `dev_job.registered_repositories` | 既存項目を残して新しい `owner`・`root`・`branch` を1件追加 |
| dev.job検証 | `tests/servercore_dev_job_test.py` | 登録集合と正確なroot/branch、除外対象の回帰検証 |
| Host実コマンド権限 | **Host protected** `operations/master-internal-repositories.json` | 現行digest・既存エントリを保持し、必要なRepoの `host.command` 権限だけ追加 |
| Host反映Script | `scripts/servercore_project1_host_enroll.py` / `scripts/servercore_ai_core_host_enroll.py` | **過去の実行用1回限りHelper**。Digestと登録数が固定されているので再実行せず、今回の対象/実測digest用に最小の新しい登録CUを実装 |
| 現行実行経路 | 既存 `.github/chat-host-requests/req_*.json` と Actions、Receiver、Host Writer | **新しい経路を作らず**独立request IDで証拠を照合 |
| 議事録 | Issue #10と既存Notion | GitHubは操作Current/証拠、Notionは判断・引継ぎ |

`registered_files`、`registered_log_containers`、`docker.operation`、`service.deploy` の追加は**必要なときだけ**その対象の実体・権限を別途調査する。Repoを追加したからといって全権限を一律付与しない。

## 安全な標準工程（同じChange Unit内で連続実施）

1. **Discover:** GitHub正本とHost既存checkoutを比較し、非Git Runtime・同名alias・nested checkout・PC上の消費側を区別する。
2. **Plan one CU:** 正確な新Repo・root・branch、要求する `dev.job` / `host.command`、変更範囲・既存Registry digestを特定。既存登録があれば**追加せず検証へ**。
3. **Source:** server-core内のBranchで既存 `dev_job.registered_repositories` に追記し回帰テストを追加。Host書込が必要なら**Host保護Registryの現行digestを固定し、既存エントリ数、Git origin、絶対root、既存Repoの重複を検査するMerge-only Helper**を作る。
4. **CI:** 対象テストと同一PR SHAの全必要CIを確認。PASSでマージ。失敗は修正して再実行。CIだけを完成とは扱わない。
5. **Host Source reflect:** 既存認可済みのGitHub→Actions→Host terminal経路から `ff-only` で反映。前後HEADを照合し、Host protected Registryのバイト列digest、stash・その他dirty変更が維持されることを検証。勝手に `reset --hard` しない。
6. **Host grants:** Helperによる保護Registry**追記**のみ。事前digest不一致・Git origin不一致・既存エントリ重複・backup競合時は**fail-closed**。0600バックアップ・atomic replace・既存Writer再起動・失敗時restoreを実行。自身のHost writerを停止し得るため、再起動を伴う処理は既存Writer内部から安易に起動しない。必要な場合だけMasterに**1行の検証済み完成コマンド**を提示（`docs/MASTER_TERMINAL_COMMAND.md`）。
7. **Runtime E2E:** 新規独立requestを登録し、対象 `repository`、対象 `repo_sha`、Host `expected_sha` を**別々に指定**。必ずIssue #10の同一request receiptまで追い、`PASS`、`EXIT_CODE=0`、対象Checkoutの `HEAD` を照合する。Actions SUCCESSのみではRuntime成功にならない。
8. **Readback & record:** 登録数、対象Repoと権限、Registry変更後digest、Backup、Writer socket、Actions URL、Issue receipt、Notionを記録。実機未検証は `UNKNOWN`、拒否は理由を残し修正→再検証。

### よくある間違いと回避

- **Source RegistryとHost protected Registryを混同**: Host registryは保護されたdirtyファイル。GitHubで更新したら自動的にHost認可された、とは判定しない。
- **Repo名とディレクトリ名が一致しない**: 例：`seigo-gace/Libral-Vault` のVPS checkoutは `/home/admin1/projects/libral-vault`。
- **Catalogの親フォルダはRepoではない**: `/home/admin1/projects/Catalog/modular-catalog` が `seigo-gace/modular-catalog` のRepo。隣の `Catalog/gace-dev-kb` は別のKB consumer。既存KB配送を勝手に起動したりPCへ接続しない。
- **Server先行開発のai-core**: 稼働ディレクトリ `/home/admin1/projects/ai-core` 自体はGit checkoutでない。既存の `/home/admin1/projects/ai-core/.worktrees/source-import-20261013` がGitHub `seigo-gace/ai-core` のsource checkout。Gitオペレーションは後者に限定し、稼働Containerは変更しない。
- **Repo SHAとHost SHAを混同**: `host.command` の `repo_sha` は対象Git checkout HEAD、`expected_sha` はserver-core Host HEAD。
- **既存定型コマンドを廃止しない**: 小さな繰返し操作は既存定型コマンド、登録されているRepoに対するその他の操作は共通Host terminal。ログ取得・TGserverの規約はルール担当CHATが別途所有。
- **Root数で完了宣言しない**: server-core自身も1 Repoとして数える。要件と現行登録数、実機readbackを突合。

## 2026-10-13の根拠となった実例

- [PR #194](https://github.com/G-ACE-inc/server-core/pull/194) 隔離開発の5→10登録、[PR #195](https://github.com/G-ACE-inc/server-core/pull/195) Host側追加Helper、[PR #196](https://github.com/G-ACE-inc/server-core/pull/196) `asteria`の漏れ補完。
- [PR #197](https://github.com/G-ACE-inc/server-core/pull/197) ai-core既存Git checkoutの `dev.job`登録、[PR #198](https://github.com/G-ACE-inc/server-core/pull/198) ai-core Host追加Helper。
- [Issue #10 実測まとめ](https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-6142586540)：11 Git Repo登録とai-coreの実機 `host.command` PASS。
- [ai-core checkout readback](https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-6142575695)：対象Repo SHAの一致、実機PASS。

**引継ぎ時の即時開始条件**: 対象GitHub RepoのURLか名前だけ受け取れば、CHATが上記Discoveryを実行して必要な登録面を決める。MasterへGitコマンドの選択やSHA判断を求めない。
