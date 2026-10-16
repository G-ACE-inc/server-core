# GPT CHAT 共通ServerTerminal入口

## 通常CHATの開始・別CHAT実測手順

開発手順の正本は [Work Routine §6](G_ACE_WORKSPACE.md#6-development-routine)。新しい通常CHATでも、所有Project/CU Current・適用Profile・対象Sourceをそこで復元する。古い会話の停止指示やNotion議論全文を起動指示として持ち込まない。Current取得は既存GitHub connectorの対象Issue読取で足りる。ローカルCLIが実際に使える場合だけ [対象を絞った復元](LOAD_SCOPE.md)を利用し、取得した同じ本文を読み直さない。

Host経路の別CHAT実測では、**実際の新しい2会話**が、それぞれ自分のCurrent参照・実作業のrequest/session/Run/resultを示す。Sourceだけの作業に不要なHost requestを作らず、成功済み操作を測定のために再送しない。server executorの合成sessionや同じ実行の再表示を、新しい通常CHATの採用証拠にしない。

作業中は、確認できた事実・修正内容・結果から次の操作につながる短い説明と、その後の実作業を観測する。ツール表示の件数、CHATの呼出し、Actions Run、サーバー側lookupは別に扱う。アプリ内部の計測がなければ、制限やフリーズの原因は未確認のままにする。実測結果と次の未完作業は既存Currentへ残し、途中説明を停止条件にしない。

## 共通Host実行経路

通常のCHATが使う実行経路は、既存の `G-ACE-inc/server-core` の `.github/chat-host-requests/req_*.json` → `chatgpt-live-api-verify.yml` → Gateway → Receiver → Host。AI自身がShellを構成して `host.command` に渡す。隔離作業だけ `dev.job` を使う。

コマンド作成時の軽い自己確認は `docs/COMMAND_ROUTINE.md`、Masterへ直接コマンドを提示する場合は `docs/MASTER_TERMINAL_COMMAND.md` を唯一の作成規則とする。このページに別のコマンド選択規則やゲートは設けない。

**2026-10-16 横断Repoの結果未着を修正した条件**：`Host Writer ledger.source_sha` は**実行対象Repo**の`repo_sha`であり、`Result Sink receipt.host_sha` は共通**Dispatcher/server-core**の`expected_sha`である。別Repo（例：`seigo-gace/ai-core`）なら異なるのが正常。以前のSink Sourceはこの2値を同一と誤判断して、Writer/Sinkの保存が完了していてもIssue #10への公開を失敗させ、Actionsが240秒待っていた。[PR #296](https://github.com/G-ACE-inc/server-core/pull/296)で、Receiverの既存「実Writer request ID＋対象Repo＋target SHA照合」を維持し、SinkではWriterの実Repo/target SHAを形式検証した上で同Request ID・exit・stateを照合する。同一Repo server-coreを実行した場合は引き続きDispatcher SHAとも完全一致を要求する。別Repoの古い`expected_sha`/古いRequest JSONをテンプレとして再送しない。SHA整合に失敗したら**その時の実Hostと対象Repo HEAD**を独立取得し、新規requestで正しく指定する。過去Requestは履歴証拠でありSelectorは新規追加された単一Requestだけを実行する。Source Merge後も既存Sinkの稼働プロセス更新と未公開結果の実回収を別途検証する。

**Source Context失敗の継続判断（Agent Pool）**：Source照合付き自由コマンドは、実Hostで失敗した場合に終了コード70～76と固定短文エラーを返す。既存Result Sinkは保護Writer ledgerの認証済み`source_preflight=true`と`exit_code`・実`stderr`が完全に一致した**許可済み診断コードだけ**を`diagnostic_hint`として公開Issue・観測Artifactへ渡す。原本のstderr／stdoutや任意診断文字列は公開しない。読取器はHintとexitの対応を再検査する。新しいCHATのContinuationは、同一Request/RunとHost Result Stepの失敗をFresh確認後、`CHAT_SOURCE_SHA_MISMATCH`なら `REFRESH_TARGET_PR_HEAD_AND_REPLAN_EXISTING_WORKTREE`、必要ファイルやworkdir不足なら `CHECK_TARGET_WORKTREE_AND_REQUIRED_FILES` を選ぶ。単なる `exit 74` や信頼できないHintだけでSourceの根本原因を断定しない。元RunのSHA、Source、Issue証拠を維持して別の有意なToolを選び、誤った診断コマンドを自動再発行しない。

**複数Repo／PR worktreeの診断コマンド（Agent Pool継続実装）**：既存の `bounded_host_request` に任意の `source_context` を付けると、共通Terminal SelectorがFreeformコマンドの先頭へ実行Source照合を自動追加する。形式：`{"repository":"seigo-gace/ai-core","workdir":"/home/admin1/projects/ai-core/.worktrees/<既存PR作業環境>","source_sha":"<実際に確認した40桁SHA>","required_files":["tests/test_model_gate.py"]}`。**記載値は構造例であり、実行用SHAではない。** `source_context.repository` はHostの登録先Repoに一致し、既存の登録checkoutまたはその既存worktreeのみを指定できる。実Host上の `git rev-parse --show-toplevel`、`git rev-parse HEAD`、指定ファイルの存在を検査してから同ディレクトリで元の自由コマンドを実行する。不一致なら `CHAT_SOURCE_ROOT_MISMATCH`、`CHAT_SOURCE_SHA_MISMATCH`、`CHAT_SOURCE_REQUIRED_FILE_MISSING` を区別し、存在しないテストを「テスト失敗」と誤認しない。元の `repo_sha` は登録checkout、`source_sha` は実際に使うPR worktreeの別SHAであり両者を混同しない。任意指定を持たない従来のFreeformコマンドは**挙動を変えない**。新しいToken、Workflow、承認Gate、worktree作成、固定コマンドメニューはない。共有server-coreの補助スクリプトは別Repoの相対pathでは動かないため、必要に応じて実行Repo/ディレクトリを明示する。既にWriterへ到達せず拒否されたSHA不一致RequestはWriterの出力が存在せず、Result Sinkのメタデータで診断する。

`host.command` の `expected_sha` は**共通Dispatcher（server-core Host checkout）の実測SHA**、`repo_sha` は**実行先の登録済みRepo checkoutの実測SHA**を示す。GitHub上の最新CommitやIssueに残った過去のHost SHAで両者を代用しない。同じ `G-ACE-inc/server-core` checkoutが実行対象なら両SHAは同一でなければならない。GitHubの先行CommitからHost反映を推定せず、相関済みHost結果のSHAを確認する。`SOURCE_SHA_MISMATCH` の場合は結果が返した実Host SHAを観測して原因・対象Repo HEADを再評価し、**新しいrequest_idと実測ピン**で再送する。照合無効化、事実確認なしの無限リトライ、古いRequestの再利用は行わない。

## 観測から次Actionまで（既存CU継続処理）

Actions Runの存在確認はPR限定のcommit→run検索ではなく、`GET /repos/{owner}/{repo}/actions/runs?head_sha=<commit>&per_page=100` の**全イベント検索**で行う。既存 `scripts/chat_cu_continuation.py --repository G-ACE-inc/server-core --discover-head-sha <40文字SHA>` で実行する（`gh`認証を流用）。一覧不足や重複はUNKNOWNとして扱い、0件だけでイベント未発火を原因確定しない。

Run一覧とArtifact一覧は全ページを読み、件数変動・重複ID・途中欠落を検出した場合は再読込が必要となる。Artifactは一覧全体から一意性と期限を確認し、Run ID・Workflow・Repository・head SHAを照合してから**検証済みArtifact ID**でZIPを取得する。復元ZIPは既存validatorで単一の観測JSONとrequest IDを検証する。メタデータArtifactの取得成功だけでstdout/stderr全文取得済みにはしない。成功Runで `HOST_LEDGER_RECOVERY_REQUIRED` が返る場合は、既存Host ledgerのpayload復元が残っている。

非SHA障害の診断引継ぎ：公開Issueはstderr全文を返さないので、結果は`result_verified`、Host `state`、`exit_code`、`host_sha` と `expected_sha` および相関Runの**実際の失敗Job Step**で分類する。Host非ゼロ終了を単なるstdout preview partialと誤認しない。Hostの`FAIL`は `HOST_OPERATION_FAILED`、再試行可能状態は `HOST_OPERATION_RETRYABLE`、Host SHA不一致は`HOST_SOURCE_SHA_MISMATCH`として区別する。Actionsの相関Result未着は `HOST_RESULT_NOT_RETURNED`とし、**新しいHost実行を無条件発行せず**元request IDでGateway/Receiver/Result Sinkを追跡する。ステップが実際に失敗していない場合や総Job件数が一致しない場合は因果断定を避ける。既存の `next_action` は次に行う操作の指針であり、Tool実行そのものの証拠ではない。

Hostの大容量出力でReceiverが`GACE_HOST_OUTPUT_STORED`という短いlocatorへ変換したとき、Result Sinkのpublic Issueに書く`stdout_sha256`/`stderr_sha256`と文字数はlocatorから計算してはならない。Result Sinkは同一Request ID、Host Source SHA、exit/stateを照合した既存Host Writer ledger（`servercore-service-deploy`）の**元のstdout/stderr**からbyte・文字数・SHA-256のみを計算して公開する。ledger未存在（Host admission前失敗）は従来のResult Sinkの短いデータとして扱う。相関異常は安全に失敗し、秘匿原文をIssue/Actionsの標準出力へ表示しない。これはHost全文ZIPの輸送そのものではなく、§6Bの独立照合用メタデータ信頼元を修正する作業。

Host観測の `streams[].complete` はIssue/Jobに見える**プレビューの完全性**であり、Host ledger本文の完全性ではない。`HOST_LEDGER_RECOVERY_REQUIRED` や `HOST_OUTPUT_PARTIAL` でも、SHA-256・UTF-8文字数の根拠があれば照合用メタデータとして保持するが、`output_complete=false` は維持する。旧Hostが全量の小さいプレビューだけを返しハッシュを持たないときは、欠損・truncatedでない場合に限ってそのプレビューからSHA-256と文字数を計算する。`stdout_bytes` 等でledgerを示す空プレビューを空出力と誤認してハッシュ化しない。成功RunかつHost exit0でZIPの全バイト照合が成立した場合のみ次のAcceptance確認へ進む。未反映Host RuntimeはSourceの新ロジックで稼働しているとは推測しない。

完全なHost出力ZIP（既存 `servercore_host_output_artifact_assemble.py` が生成する `stdout.txt`・`stderr.txt`・`manifest.json`）をCHAT側へ取得できた場合は、`chat_cu_continuation.py` に `--host-output-zip <取得済みローカルZIP>` を渡す。小さな観測Artifactから受け取ったrequest IDと**独立したWriter元出力の期待バイト数・SHA-256・Unicode文字数**を、ZIP内全バイト・manifestのbyte長・SHAと照合した場合**のみ**、新鮮なGitHub Runの再照合を経て `VERIFY_CU_ACCEPTANCE` へ遷移する。元の会話/Checkpoint内の `output_complete=true` やZIP内manifestだけでは合格にしない。結果の証拠にはbytes/chars/SHAのみを含め、stdout/stderr本文・秘匿情報を自動出力しない。なお、このCLI追加は **Host ledgerからActions Artifactへの実輸送や実CHATがArtifactを取得できた証明ではない**。設計§6B受入には既存Host→Actions→CHAT実機の往復証拠が別途必要。

観測済み `request_id` がある場合は、同じコマンドに `--request-id <実ID> --cu-issue-url https://github.com/G-ACE-inc/server-core/issues/40` を付け、既存Run→Artifact→Checkpoint→実Run再読込へ進む。Host失敗の相関と実Host SHAが検証されれば、Actions全体がfailureでも一般的な「Actions障害」へ戻さず、対象RepoのHost Checkout SHAを再確認して**異なる有意な修正Action**を選択する。失敗が継続した理由を恣意的に推測せず、失敗StepのGitHub再読込も行う。このスクリプト自身はHost実行やCHAT自動送信を強制せず、次の実Tool呼出は通常CHATが担う。これを実際の同一CUの複数回のACT→OBSERVE→DECIDE→ACT受入完了とはみなさない。

大容量Host結果でWriterの保存は完了していても、ReceiverからResult Sinkへの記録が失敗すればGitHub Issue/Actionsに結果が戻らない。`host.command`も他のRequestと同様に**Sink未記録をHTTP 503として返し、Gatewayは元のevent/request IDを保持して再配送**する。Host writerの同一Request ID重複検知で実コマンドを再実行しない。Gatewayの受理HTTP 202、Host Writer ledger PASS、Sinkへの記録、Issueへのpublish、Actionsのpollを別の状態として扱い、片方のPASSから他方を推測しない。旧Host runtimeが新しいSourceを使用しているとはMergeだけで推測しない。


**2026-10-16 Agent Pool Source照合・診断の整合修正（PR #299）**：任意の`source_context`を含む依頼について、Selectorは既存登録checkoutのGit common directoryと指定先worktreeの実Git common directoryを`realpath`で比較する。名称やworktreeの位置だけが一致する無関係なGit cloneを拒否する。HEAD一致だけではソースが同一といえないため、実行先worktreeで`git status --porcelain --untracked-files=all`が空であることを検査し、変更・未追跡ファイルが残る場合は`CHAT_SOURCE_DIRTY_WORKTREE`（exit76）を返して**コマンドは実行しない**。既存の許可範囲を広げたり、別RepoのSourceを書き換えたりはしない。

同Source照合が有効なRequestでは、Selectorだけが生成できる`source_preflight=true`を既存Actions/Gateway/Receiver/Host Writerへ伝え、Writer ledgerへ相関付きで保存する。Result Sinkはその記録があり、かつWriterが既知の終了コード70～76と完全一致する診断マーカーを返した場合**だけ**、短い`diagnostic_hint`を公開する。通常`host.command`が同じ文字列をstderrへ返してもSource障害と認定しない。`cd`エラーのシェル本文は抑止し、欠落時の単一診断マーカーを保つ。別CHATから既存checkpointを復元するときも、観測種別／終了コード／マーカーが整合しない組合せはSource固有の次Actionを選択しない。GitHub Workflowの正当な`...yml@main`等のref接尾辞はパス本体を照合して受け入れる。これらはSource/CI実装に関する契約であり、**Host稼働中Writer・Sink反映、機密ZIP全文輸送、Agent Loop全体の完了証拠ではない**。


**完全ZIP検証の安全境界（2026-10-16）**：GitHubの古い自動レビューで、真のHost出力であることを照合せず大きなZIPを展開すると圧縮爆弾により検証器のCPU/メモリを消費し得る点が指摘された。既存`verify_artifact_zip`ではZIP内の自己申告とは独立した**Writer由来の期待byte数＋SHA256＋Unicode文字数**を必須とし、実ZIPのメンバー宣言値と突き合わせた上で64KiBのストリーミング検証を行う。検証器の保護上限は現在、各ストリーム512MiB／合計1GiB／ZIPファイル512MiB。超過を切り詰めてPASSにはせず`HOST_OUTPUT_UNCOMPRESSED_SIZE_LIMIT`等で明示拒否する。Host Writerの原文完全保存・受信の再設計とは別の保護であり、大容量の真正ログ受入をこの上限で完了扱いしてはいけない。短い予告なく異なる条件での運用をしない。Sourceで元から途切れた出力も`source_truncated=true`を引き継ぎ、ZIP自己整合が成立してもVERIFYへ昇格させない。Host Writerが実行前障害でstdout/stderr不明の場合も空SHAを捏造しない。

**機密ZIPの公開境界（P0未達）**：このGitHub Repoは現時点で`public`であり、公開RepoのActions ArtifactにHost原文の完全ZIPを無加工でアップロードしてはいけない。GitHub ActionsのArtifactはRepoにread accessを持つGitHubユーザーへダウンロード可能（https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts）。既存WorkflowのmetadataのみのArtifactは原文とは異なる。秘匿性のある完全payloadをCHATへ戻す承認済み認証・公開防止・権限分離の経路は引き続き未確認で、Artifactを増量するだけでは解決しない。今回の受信検証改善は輸送を完成させず、要求Source/CIとHostの実運用を別ゲートで確認する。

**既存Writerからの明示的な機密回収（2026-10-17）**：保護Ledgerを既に読めるSERVER_AI、または同じ読取が実際にadmitされた通常CHATのHost操作は、既存`servercore_host_output_private_artifact_publish.py <元request_id> --writer-ledger`で、元の結果を再実行せずZIP化して既存private TGserver CIへ渡せる。`--verify-only`はローカル整合検証だけでGitHubへ送らない。Writer本文から独立取得した期待bytes/chars/SHAとZIPを照合し、宛先Repositoryがprivateであることを再確認してから、一時private release→既存CIの1日Artifactを利用する。平文の一時ZIP/TXTは0600、処理後の一時ディレクトリは削除する。Vault入力は従来どおりであり、Vault失敗からの自動fallbackや新しいHTTP公開口は追加しない。Host実行・Ledger読取の権限をこのCLIの存在から推測しない。

受取側はprivate Run/Artifact/request IDと独立した元出力メタデータを照合し、既存`--host-output-zip`で継続判断へ渡す。正常・失敗の分類をexit codeに埋めて再実行を重ねたり、候補コミットを総当たりして本文の代わりにしない。相関済みのHost失敗は本文が未取得でもまず元Run/失敗Stepを再確認し、その後に必要な範囲の回収・修正へ進む。回収ZIPの自己整合やprivate CI成功は、元Hostコマンドの成功・Source truncation不存在・実CHATの受信成功を証明しない。ブラウザの接続断・フリーズ解消も別途未検証。

**private Artifact→継続判断の接続（2026-10-17）**：CLIを使用できる実行面では、既存`chat_cu_continuation.py`の元の`--repository / --run-id / --request-id / --cu-issue-url`に`--private-output-run-id <回収済みprivate CIの実Run ID>`を加える。元Host Runの成功と出力検証状態をFresh確認してから、固定private宛先のRepository・releaseイベント・既存CI Workflow・Run SHA・Artifact ID/期限/request名を照合する。全ページ一覧の一意性を確認し、ZIPをメモリ一括取得せず一時privateファイルへ受信する。外側は`output.zip`だけを許容し、内側の全bytes/chars/SHAを独立した元Host観測と照合した場合だけ`VERIFY_CU_ACCEPTANCE`へ進む。一時ファイルは成功・失敗の両方で削除し、Receiptには相関IDと検証メタデータだけを残す。ローカル`--host-output-zip`とは排他的であり、期限切れからの新Host実行や自動再発行はしない。

通常CHATの既存GitHubコネクタには`download_workflow_artifact`がある。このセッションではprivate Artifact `12063644111`を取得し、返されたファイル参照から同一の41-byte出力を検証できた。自然言語の「Action completed」だけで本文取得済みと判断せず、構造化されたファイル参照と実バイトを確認する。コネクタのRun/Artifact一覧が先頭ページだけの場合は、完全性を推測せず既存APIのページング可能な取得経路を使う。短命のdownload URLをCurrent/Issue/Receiptへ保存しない。これは現セッションのコネクタ取得証拠であり、新しい通常CHATのCU継続やブラウザ症状の改善証拠ではない。

private CIのRun IDが未取得なら、同じ元Host識別子に`--recover-private-output`を付ける。固定private宛先のArtifact名を元request IDで絞り込んで全ページを確認し、一意で未期限切れの結果の`workflow_run.id`から既存private Runを復元する。全Runの探索やArtifact一覧の重複取得はしない。0件・複数・期限切れは明示拒否し、最新版の恣意選択や元Host実行の再送をしない。複数回のprivate exportがある場合は、相関済みの`--private-output-run-id`で曖昧さを解消する。元Host Runとprivate Runは異なる証拠としてReceiptに残す。自動回収・明示Run・ローカルZIPは排他的。

実行依頼のファイル形式、必要な署名・認証・SHA・登録Repo制約は既存の実装と `operations/github-project-bounded-host.json` に従う。結果は既存ActionsとHost返却で確認する。失敗時は原因を修正して作業を続ける。通常CHATでの新たなMaster承認は要求しない。
