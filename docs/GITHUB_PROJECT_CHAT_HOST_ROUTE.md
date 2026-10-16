# GPT CHAT 共通ServerTerminal入口

通常のCHATが使う実行経路は、既存の `G-ACE-inc/server-core` の `.github/chat-host-requests/req_*.json` → `chatgpt-live-api-verify.yml` → Gateway → Receiver → Host。AI自身がShellを構成して `host.command` に渡す。隔離作業だけ `dev.job` を使う。

コマンド作成時の軽い自己確認は `docs/COMMAND_ROUTINE.md`、Masterへ直接コマンドを提示する場合は `docs/MASTER_TERMINAL_COMMAND.md` を唯一の作成規則とする。このページに別のコマンド選択規則やゲートは設けない。

**2026-10-16 横断Repoの結果未着を修正した条件**：`Host Writer ledger.source_sha` は**実行対象Repo**の`repo_sha`であり、`Result Sink receipt.host_sha` は共通**Dispatcher/server-core**の`expected_sha`である。別Repo（例：`seigo-gace/ai-core`）なら異なるのが正常。以前のSink Sourceはこの2値を同一と誤判断して、Writer/Sinkの保存が完了していてもIssue #10への公開を失敗させ、Actionsが240秒待っていた。[PR #296](https://github.com/G-ACE-inc/server-core/pull/296)で、Receiverの既存「実Writer request ID＋対象Repo＋target SHA照合」を維持し、SinkではWriterの実Repo/target SHAを形式検証した上で同Request ID・exit・stateを照合する。同一Repo server-coreを実行した場合は引き続きDispatcher SHAとも完全一致を要求する。別Repoの古い`expected_sha`/古いRequest JSONをテンプレとして再送しない。SHA整合に失敗したら**その時の実Hostと対象Repo HEAD**を独立取得し、新規requestで正しく指定する。過去Requestは履歴証拠でありSelectorは新規追加された単一Requestだけを実行する。Source Merge後も既存Sinkの稼働プロセス更新と未公開結果の実回収を別途検証する。

**複数Repo／PR worktreeの診断コマンド（Agent Pool継続実装）**：既存の `bounded_host_request` に任意の `source_context` を付けると、共通Terminal SelectorがFreeformコマンドの先頭へ実行Source照合を自動追加する。形式：`{"repository":"seigo-gace/ai-core","workdir":"/home/admin1/projects/ai-core/.worktrees/<既存PR作業環境>","source_sha":"<実際に確認した40桁SHA>","required_files":["tests/test_model_gate.py"]}`。**記載値は構造例であり、実行用SHAではない。** `source_context.repository` はHostの登録先Repoに一致し、既存の登録checkoutまたはその既存worktreeのみを指定できる。実Host上の `git rev-parse --show-toplevel`、`git rev-parse HEAD`、指定ファイルの存在を検査してから同ディレクトリで元の自由コマンドを実行する。不一致なら `CHAT_SOURCE_ROOT_MISMATCH`、`CHAT_SOURCE_SHA_MISMATCH`、`CHAT_SOURCE_REQUIRED_FILE_MISSING` を区別し、存在しないテストを「テスト失敗」と誤認しない。元の `repo_sha` は登録checkout、`source_sha` は実際に使うPR worktreeの別SHAであり両者を混同しない。任意指定を持たない従来のFreeformコマンドは**挙動を変えない**。新しいToken、Workflow、承認Gate、worktree作成、固定コマンドメニューはない。共有server-coreの補助スクリプトは別Repoの相対pathでは動かないため、必要に応じて実行Repo/ディレクトリを明示する。既にWriterへ到達せず拒否されたSHA不一致RequestはWriterの出力が存在せず、Result Sinkのメタデータで診断する。

`host.command` の `expected_sha` は**共通Dispatcher（server-core Host checkout）の実測SHA**、`repo_sha` は**実行先の登録済みRepo checkoutの実測SHA**を示す。GitHub上の最新CommitやIssueに残った過去のHost SHAで両者を代用しない。同じ `G-ACE-inc/server-core` checkoutが実行対象なら両SHAは同一でなければならない。GitHubの先行CommitからHost反映を推定せず、相関済みHost結果のSHAを確認する。`SOURCE_SHA_MISMATCH` の場合は結果が返した実Host SHAを観測して原因・対象Repo HEADを再評価し、**新しいrequest_idと実測ピン**で再送する。照合無効化、事実確認なしの無限リトライ、古いRequestの再利用は行わない。

## 観測から次Actionまで（既存CU継続処理）

Actions Runの存在確認はPR限定のcommit→run検索ではなく、`GET /repos/{owner}/{repo}/actions/runs?head_sha=<commit>&per_page=100` の**全イベント検索**で行う。既存 `scripts/chat_cu_continuation.py --repository G-ACE-inc/server-core --discover-head-sha <40文字SHA>` で実行する（`gh`認証を流用）。一覧不足や重複はUNKNOWNとして扱い、0件だけでイベント未発火を原因確定しない。

Run一覧とArtifact一覧は全ページを読み、件数変動・重複ID・途中欠落を検出した場合は再読込が必要となる。Artifactは一覧全体から一意性と期限を確認し、Run ID・Workflow・Repository・head SHAを照合してから**検証済みArtifact ID**でZIPを取得する。復元ZIPは既存validatorで単一の観測JSONとrequest IDを検証する。メタデータArtifactの取得成功だけでstdout/stderr全文取得済みにはしない。成功Runで `HOST_LEDGER_RECOVERY_REQUIRED` が返る場合は、既存Host ledgerのpayload復元が残っている。

非SHA障害の診断引継ぎ：公開Issueはstderr全文を返さないので、結果は`result_verified`、Host `state`、`exit_code`、`host_sha` と `expected_sha` および相関Runの**実際の失敗Job Step**で分類する。Host非ゼロ終了を単なるstdout preview partialと誤認しない。Hostの`FAIL`は `HOST_OPERATION_FAILED`、再試行可能状態は `HOST_OPERATION_RETRYABLE`、Host SHA不一致は`HOST_SOURCE_SHA_MISMATCH`として区別する。Actionsの相関Result未着は `HOST_RESULT_NOT_RETURNED`とし、**新しいHost実行を無条件発行せず**元request IDでGateway/Receiver/Result Sinkを追跡する。ステップが実際に失敗していない場合や総Job件数が一致しない場合は因果断定を避ける。既存の `next_action` は次に行う操作の指針であり、Tool実行そのものの証拠ではない。

Hostの大容量出力でReceiverが`GACE_HOST_OUTPUT_STORED`という短いlocatorへ変換したとき、Result Sinkのpublic Issueに書く`stdout_sha256`/`stderr_sha256`と文字数はlocatorから計算してはならない。Result Sinkは同一Request ID、Host Source SHA、exit/stateを照合した既存Host Writer ledger（`servercore-service-deploy`）の**元のstdout/stderr**からbyte・文字数・SHA-256のみを計算して公開する。ledger未存在（Host admission前失敗）は従来のResult Sinkの短いデータとして扱う。相関異常は安全に失敗し、秘匿原文をIssue/Actionsの標準出力へ表示しない。これはHost全文ZIPの輸送そのものではなく、§6Bの独立照合用メタデータ信頼元を修正する作業。

Host観測の `streams[].complete` はIssue/Jobに見える**プレビューの完全性**であり、Host ledger本文の完全性ではない。`HOST_LEDGER_RECOVERY_REQUIRED` や `HOST_OUTPUT_PARTIAL` でも、SHA-256・UTF-8文字数の根拠があれば照合用メタデータとして保持するが、`output_complete=false` は維持する。旧Hostが全量の小さいプレビューだけを返しハッシュを持たないときは、欠損・truncatedでない場合に限ってそのプレビューからSHA-256と文字数を計算する。`stdout_bytes` 等でledgerを示す空プレビューを空出力と誤認してハッシュ化しない。成功RunかつHost exit0でZIPの全バイト照合が成立した場合のみ次のAcceptance確認へ進む。未反映Host RuntimeはSourceの新ロジックで稼働しているとは推測しない。

完全なHost出力ZIP（既存 `servercore_host_output_artifact_assemble.py` が生成する `stdout.txt`・`stderr.txt`・`manifest.json`）をCHAT側へ取得できた場合は、`chat_cu_continuation.py` に `--host-output-zip <取得済みローカルZIP>` を渡す。小さな観測Artifactから受け取ったrequest IDとSHA-256・Unicode文字数を、ZIP内全バイト・manifestのbyte長・SHAと照合した場合**のみ**、新鮮なGitHub Runの再照合を経て `VERIFY_CU_ACCEPTANCE` へ遷移する。元の会話/Checkpoint内の `output_complete=true` やZIP内manifestだけでは合格にしない。結果の証拠にはbytes/chars/SHAのみを含め、stdout/stderr本文・秘匿情報を自動出力しない。なお、このCLI追加は **Host ledgerからActions Artifactへの実輸送や実CHATがArtifactを取得できた証明ではない**。設計§6B受入には既存Host→Actions→CHAT実機の往復証拠が別途必要。

観測済み `request_id` がある場合は、同じコマンドに `--request-id <実ID> --cu-issue-url https://github.com/G-ACE-inc/server-core/issues/40` を付け、既存Run→Artifact→Checkpoint→実Run再読込へ進む。Host失敗の相関と実Host SHAが検証されれば、Actions全体がfailureでも一般的な「Actions障害」へ戻さず、対象RepoのHost Checkout SHAを再確認して**異なる有意な修正Action**を選択する。失敗が継続した理由を恣意的に推測せず、失敗StepのGitHub再読込も行う。このスクリプト自身はHost実行やCHAT自動送信を強制せず、次の実Tool呼出は通常CHATが担う。これを実際の同一CUの複数回のACT→OBSERVE→DECIDE→ACT受入完了とはみなさない。

大容量Host結果でWriterの保存は完了していても、ReceiverからResult Sinkへの記録が失敗すればGitHub Issue/Actionsに結果が戻らない。`host.command`も他のRequestと同様に**Sink未記録をHTTP 503として返し、Gatewayは元のevent/request IDを保持して再配送**する。Host writerの同一Request ID重複検知で実コマンドを再実行しない。Gatewayの受理HTTP 202、Host Writer ledger PASS、Sinkへの記録、Issueへのpublish、Actionsのpollを別の状態として扱い、片方のPASSから他方を推測しない。旧Host runtimeが新しいSourceを使用しているとはMergeだけで推測しない。

実行依頼のファイル形式、必要な署名・認証・SHA・登録Repo制約は既存の実装と `operations/github-project-bounded-host.json` に従う。結果は既存ActionsとHost返却で確認する。失敗時は原因を修正して作業を続ける。通常CHATでの新たなMaster承認は要求しない。
