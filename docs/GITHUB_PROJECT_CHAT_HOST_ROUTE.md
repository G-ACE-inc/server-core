# GPT CHAT 共通ServerTerminal入口

通常のCHATが使う実行経路は、既存の `G-ACE-inc/server-core` の `.github/chat-host-requests/req_*.json` → `chatgpt-live-api-verify.yml` → Gateway → Receiver → Host。AI自身がShellを構成して `host.command` に渡す。隔離作業だけ `dev.job` を使う。

コマンド作成時の軽い自己確認は `docs/COMMAND_ROUTINE.md`、Masterへ直接コマンドを提示する場合は `docs/MASTER_TERMINAL_COMMAND.md` を唯一の作成規則とする。このページに別のコマンド選択規則やゲートは設けない。

`host.command` の `expected_sha` は**共通Dispatcher（server-core Host checkout）の実測SHA**、`repo_sha` は**実行先の登録済みRepo checkoutの実測SHA**を示す。GitHub上の最新CommitやIssueに残った過去のHost SHAで両者を代用しない。同じ `G-ACE-inc/server-core` checkoutが実行対象なら両SHAは同一でなければならない。GitHubの先行CommitからHost反映を推定せず、相関済みHost結果のSHAを確認する。`SOURCE_SHA_MISMATCH` の場合は結果が返した実Host SHAを観測して原因・対象Repo HEADを再評価し、**新しいrequest_idと実測ピン**で再送する。照合無効化、事実確認なしの無限リトライ、古いRequestの再利用は行わない。

実行依頼のファイル形式、必要な署名・認証・SHA・登録Repo制約は既存の実装と `operations/github-project-bounded-host.json` に従う。結果は既存ActionsとHost返却で確認する。失敗時は原因を修正して作業を続ける。通常CHATでの新たなMaster承認は要求しない。
