# GPT CHAT Project Agent — 採用済み設計（2026-10-15）
Status: DESIGN ADOPTED (PR #246) / IMPLEMENTATION IN PROGRESS
Owner: G-ACE-inc/server-core / GitHub Project #1 / Control #10
Baseline: docs/SERVER_CORE_DESIGN.md §16.11 and §17. This document refines these existing contracts; it neither supersedes them nor authorizes additional Host privileges.

## 1. 開発目的・完成の姿
通常のGPTアプリCHATから、既存のGitHub Project/Repository/Actionsとserver-coreの共通Hostターミナルを介し、Cursor、Codex、IDE内Agentのように**登録済みProjectの開発Change Unit (CU)を継続遂行**する。Rule記述だけで継続を期待するのでなく、実際の状態保存・結果観測・再判断・再実行の連鎖を組み立てる。Masterは要求・製品上の採否を行い、通常のコマンド・実装・テスト・CI・マージの技術判断はCHATへ委任する。

Masterの追加要件は **design-first**: 着手時・再開時・主要変更前・完了判定時に採用済み設計revisionと受入条件へ照合し、脱線を検出すること。設計を読んだという自己申告は合格条件にならない。

これはCodex/Cursorのソースを取り込むプロジェクトではない。公開されているAgent Loop / Tool contract / Observation / Context management / Recoveryの**動作設計を研究し、既存G-ACE部品で独自に再現**する。既存機能を優先し、新たなAgentプロセス・MCP・Token・Workflow・無関係なRepo/worktreeを増設しない。

## 2. 公開Agent概念と既存部品の対応（参考概念でありコード移植ではない）

| 参考概念 | G-ACEでの実体 | 現状の確認結果 | 必要なギャップ |
|---|---|---|---|
| Agent instruction / task context | GPT CHAT、GitHub Project #1 Current、Issue #10、Rule #17、Manifest | 既存 | Chat変更時に同一CUの設計・未完了状態を漏れなくrehydrateする契約 |
| Plan / design guard | `SERVER_CORE_DESIGN.md` §16.11、設計差分、`work_routine_design_entry_gate.py` | Source契約あり | 承認済み設計SHAとCU範囲を機械的に照合した証拠 |
| Tool dispatch | 既存GitHub API → 共通Actions → Gateway → Receiver → `host.command` / `dev.job` | Source実装あり | 登録Project毎の実Host E2E・権限・結果返却 |
| Tool observation | Result Sink、Issue #10 request receipt、Host ledger、`servercore_bounded_result_poll.py` | Source実装あり | 長文stdout/stderrの欠損なし取得と再判断への引渡し |
| Iterative policy / next action | `github_project_chat_turn_gate.py` の next_action / observations、GPT CHAT自身の次Tool呼出 | 部分的Sourceあり | 観測→次Tool実行→再観測の実連続E2E、単なるNEXT報告と区別 |
| Workspace / execution isolation | `dev.job`、登録済みDocker隔離Worker（§16.11） | 設計・部分Source、Host 未照合 | 登録Repo/本物のHEADでGit編集・テスト・失敗修正 |
| Durable event log / handoff | GitHub Project Current・Issue/PR/CI、TGserver ZERO Development Events、Notion設計経緯 | 個別経路あり | 相関IDでCU進捗を復元できる横断readback |
| Acceptance & recovery | design acceptance, CI SHA, Host active consumer verification | 契約あり | STOPを実機証拠と設計達成だけに限定、再開時に止まった箇所から続行 |

**境界**: GPT CHATは判断とTool実行の主体。GitHub Actionsは伝達・CI、Host/Dockerは実行器。結果から次判断を下す独立した有料AIサービスは導入しない。CHAT自体の自動送信やセッション永続化をプラットフォームが保証しないなら、保証したと主張しない。

## 3. CU（Project単位の継続開発）契約
開発作業の単位は都度のコマンドやIssueコメントではなく、**登録済みProjectに所属する一つのChange Unit**。

各CUのdurable currentに最低限保持する: project_id / project_item / repo / CU Issue、固定目的、採用設計URIとrevision、受入条件、owner、branchと変更対象、base/tested SHA、直近の実行request_id・Actions run/job・Host receipt/exit/status/output digest・Runtime evidence、完了/未完了、次の実行可能な行動、既知のBLOCKEDと独立工程、更新時点・証拠URL。

持続化先は既存GitHub Project Current + owning Issue/PRの運用に合わせる。Notionは設計の議論/採否/HandoffでありSource/Runtime Authorityではない。TGserver ZEROは相関された実行イベントの保存・検索であり、Project Currentの代替ではない。保存不能の場合に「保存した」と回答しない。

## 4. 正常・異常・中断時のAgent Loop
1. **REHYDRATE**: Manifest→#17→Project Current→CU→採用設計/受入条件→最新Source/CI/Host/ZERO evidence。前回からの差分を読む。異なるCHAT/Workerでも同じ入力で同じCUを特定する。
2. **PLAN**: 未完了受入条件を分解し、既存Toolで実行可能な最小の有意な作業群を選択する。Rule追記/診断だけを完成目的に格上げしない。ここで作業選択をMasterへ返さない。
3. **ACT**: 登録Repoの正確なSHAと設計一致を確認し、既存GitHub APIまたは`host.command`/`dev.job`で実行。現行経路のみ使用。特定されたOwner/権限範囲は維持。
4. **OBSERVE**: 完了をHTTP 202/送信成功/Sourceの存在だけで判定しない。request-idとCI/Host exit、結果本文または欠損なしArtifact、変更SHA、影響範囲を読む。出力部分欠損は`OUTPUT_PARTIAL`として扱い診断完了にしない。
5. **DECIDE**: 受入条件に照らし、成功なら次の未完了条件へ、失敗なら原因仮説を検証して**別の具体的Tool actionへ遷移**。再試行に合理的な意味がない場合は同一エラーを反復せず調査手法を替える。故障した手段と独立している作業は継続。
6. **VERIFY & PROMOTE**: 対象RepoのPR、exact-SHA CI、必要なら登録Host反映と稼働中consumer確認、関連ZERO event readback。製品要求の受入条件を満たした証拠を揃える。
7. **CHECKPOINT**: 每ターンの無用な全文コメントではなく、採用設計の変更、重要判断、実装状態/失敗原因/次回復元点の変化を既存Current・Notion議事録・ZEROへ記録。CHAT境界でも復元可能なリンクを残す。
8. **STOP**: MASTER_INTERRUPT、保護されたMaster決定、実証された受入条件すべて達成、または**すべて**の実行可能ActionがBLOCKEDの場合のみ。報告送信、単独のCI成功、一つの失敗、時間区切りはSTOP根拠ではない。

重要: ルール／Python gateはChatGPT送信前Hookではなく、CHATの次Tool自動呼出を強制できない。この制約を隠さない。実環境で保証可能な連続操作の境界をLive E2Eで測定する。

## 5. 設計優先のドリフト防止
- 調査時は採用設計URL/SHA・Current purpose・CU acceptanceを対照し、要求外の実装を弾く。設計変更が必要なら既存設計PRと議事録に変更理由・代替・影響を残し、確定してから実装。
- `work_routine_design_entry_gate.py`、`github_project_chat_turn_gate.py`は既存契約の候補。新Gateを量産せず、Source上の実際の使われ方を検証して必要な不足だけ補修。
- CHAtの自己申告は証拠にならない。具体的Source diff / verified SHA / Host result / consumer readbackを証拠とする。

## 6. 検証と段階的受入（偽の「完成」を防ぐ）
A. **Source baseline**: 今日の既存コミット（例: `28ca07d`、`a4f6a52`、PR #238-245）を照合し、重複実装を避ける。変更箇所・owner/branchを特定。
B. **Output roundtrip**: Unicodeを含む長いstdout/stderrについて、Host ledger→既存経路→Actions→CHATでbyte長/hash/終端一致を確認。TXT/ZIP作成のみでは合格しない。
C. **Single-CU continuity**: 採用設計/受入条件を与えた一つの実Projectで、故意の失敗を含む2回以上の `ACT→OBSERVE→DECIDE→ACT` をMasterのコマンド手貼りなしで実行し、exact SHAと相関requestを残す。
D. **Cross-CHAT restore**: 別CHATにおいて、元の全文会話の再説明なしに同じCU、設計、次Action、失敗原因、直近証拠を復元し、有意な次操作を実行する。
E. **End-to-end acceptance**: PR/CI成功だけでなく、必要なHost reflect/稼働consumer/回復、TGserver ZERO保存→検索のreadbackを同一CUに紐付ける。未接続Repoは明示的`NOT_QUALIFIED`。
F. **No-regression**: 旧固定コマンドの使用、新規Token/MCP/Workflow/親兄弟ディレクトリ、他Owner編集、無限リトライ、未検証完了宣言を防ぐ。

## 7. 設計段階の実装優先順
1. **既存機能の棚卸しと断線点確定**: 既存設計/変更/CI/Host登録を見て、作るべき箇所を最小化。
2. **観測データの欠損を解消**: Issueに全文を投稿するのでなく、保存済みHost ledgerと既存経路で完全な結果をCHATへ渡す。出力アセンブル/ZIPだけで終了しない。
3. **結果に基づく反復処理をE2E化**: 実Tool呼出を伴う連続CU、FAIL→別Action→再観測を実証。
4. **Project継続性と設計照合を確認**: Chat切替時にCurrent/設計/次Actionを確実に復元する。
5. **登録Project拡張・実機検証・ZERO検索**: 範囲・owner・Host権限を確認して段階展開。

## 8. 現時点の厳密な結論
既存SourceにはRule Plane、設計Entry Gate、CHAT checkpoint/next_action、Host経路、Host result ledger、ログ復元スクリプト等が存在する。しかし**Codex/Cursor型の一貫した自律開発機能が通常CHATからLiveで完成**した証拠はない。実装済み部品の重複開発を避け、つなぎ込みとProject/CU単位の実証を行う。Source PASS、CI PASS、Host Live PASS、ZERO readback、Cross-CHAT continuityは別々に報告する。


## 9. 企画・Project/Task管理と記録処理をAgent Loopへ組み込む（2026-10-15採用検討）
**起点:** MasterはNotionの毎ターン議事録、Notion検討のまとめ、Repo設計正本、Issue、設計Branch/PR/Commit、GitHub Project Current、TGserverを既に運用している。障害は「Toolが存在しない」ことではなく、AIが実作業中にこれらを忘却・省略し、CHAT変更で目的と次作業を再発掘すること。新しいProject管理製品の導入やRuleの追加だけでは解決しない。

### 9.1 公開技術を仕組みとして参照する範囲
- **CodexのAgent Loop:** Action→Tool Observation→次Actionという反復構造を、通常CHATと既存GitHub/Host Toolの間に適用する。参照: https://openai.com/index/unrolling-the-codex-agent-loop/ 、https://github.com/openai/codex 。Codex本体のコピー/移植、別常駐Agentは目的外。
- **OpenHandsのイベント・State/復元:** Checkpoint、事実のイベント化、停滞検出、復元後の整合性検査を参考にする。参照: https://github.com/OpenHands/software-agent-sdk 。別のState DBやRunner導入は不要。
- **OpenProject型の作業項目連携:** 企画→Workstream/Epic→Change Unit→Task→PR/CI/Runtime Evidenceの対応を既存GitHub Project/Issueで表す。参照: https://www.openproject.org/docs/system-admin-guide/integrations/github-integration/ 。OpenProject/Taigaをインストールしない。
- **採用単位**は一般論・状態遷移・観測点・結合方式であり、OSSソースコードやサービスの丸ごと導入ではない。

### 9.2 最小CU Current/Checkpointの情報契約（既存Issue/Projectで運用）
一つのCUに対し、次を一箇所で見つけられるようにする。不要な新Storeは設けない。GitHub Project #1/owning IssueがCurrent、Notionが議論採否、Repo設計mainが採用仕様、Draft設計PRが提案、TGserver ZEROが実行Eventの検索面。
- `project, repo, cu_issue, owner, goal, acceptance[], design_uri, adopted_design_sha, branch, source_head_sha`
- `last_action, last_result, actions_run_id, host_request_id, host_result_url, host_exit, host_sha, stdout/stderr_hash_and_complete, runtime_evidence_url`
- `decision_reason, notion_minutes_url, outstanding[], blocked[], next_executable_action, checkpoint_version, updated_at`
ログ全文・会話全文をCurrentに複製せず、証拠URL/SHAだけを保持する。更新者・版・並列CU Ownerを明示し、直近HEAD/設計Revisionと異なる情報はSTALEとしてFresh Readbackする。Projects v2 Item Fieldが接続Toolから取得不能なら`UNKNOWN`、閲覧できるIssue/PR証拠から復元し、架空の値で埋めない。

### 9.3 記録忘れを軽減するイベント→更新対応
| 起点 | 必須の記録・同期 | 機械化できる境界 |
|---|---|---|
| Masterの企画/要件/採否決定 | CHATが当該ターンでNotion議事録に背景・比較・採否・未決事項を記録。CU受入条件へ反映、書込Receipt確認 | CHAT側Notion Toolが実行できる範囲。通常CHAT送信Hook不在で完全自動保証は不可 |
| 設計方針変更 | 既存設計Branch/PRに仕様・差分・根拠・影響・受入条件。採用main設計とは区別 | GitHub SourceとPRの更新/CI差分検査 |
| 実装Commit/PR/CI | SHA、差分、Check、次の未達条件をCUに紐付け。Statusが古ければSTALEと判定 | 既存GitHub API/Actions |
| Host `host.command` / `dev.job` | request/run ID、exit、Host SHA、出力完整性、観測と次Action | 既存Result Sink / PR #247観測Artifact。CHAT再読込は要E2E |
| Runtime/ログ | active consumer証拠とTGserver ZEROイベントの実検索readback | 既存Host/API/Collector/Readerの範囲 |
| CHAT切替/中断 | Currentと最新のNotion採否・採用設計・Host Observationから未達CUと次Toolを復元 | 新しいCHATが現存するToolで明示的に読込・次Toolを実行する必要あり |

「毎ターンNotion議事録」の運用要求は維持する。ただし同一事項の全文複写で作業を妨げず、そのターンの決定/作業差分・参照先・次Actionを短く記す。書込が失敗すれば`MINUTES_NOT_RECORDED`として残し、保存成功を装わない。**自動化可能なGitHub/Host実行事実**と、**CHAT内でのみ把握できる議論の意味付け**を混同しない。

### 9.4 実際の実行順序と軽量チェック
1. Rehydrate: Current/Owner/目的/採用設計SHA/Acceptance/最終Commit・Host観測/Notion最新決定を必要範囲で読む。Issueコメント全件や過去CHAT全文の走査は禁止。
2. Plan: 未完了Acceptanceに直結するActionを決定。企画/調査/設計/実装のいずれにも同じCU単位を適用。
3. Act: 既存GitHub/Actions/Host/Notion Toolで実行し、結果・相関ID/shaを観測。
4. Checkpoint: 重要な意思決定、実行証拠、失敗原因、実行可能な次Actionが変われば既存Issue/Notionの適切な場所へ記録・readback。**記録は開発完了の合図ではなく次Actionへの入力**。
5. Decide and repeat: Partial outputは不完全扱い、失敗は再診断して異なる有意味なAction、設計との不一致は該当mutationだけ停止してread-only調査は継続。
6. Stop: 実際のAcceptance全達成、Master明示中断、Master専有判断、または全独立Action遮断時のみ。一般の報告/CI緑/Issue記録だけで終了しない。

実行選択時のチェックは**現在地/設計が整合するか、受入条件へ進むか、不可逆の保護影響はないか、次Actionが具体的か**の4点に限定し、複数の重複Gate・Masterへの通常技術承認を追加しない。

### 9.5 GPTアプリの限界と到達可能な保証
通常CHATはCodex CLIのようなユーザー管理の永続プロセスではない。CHAT送信前後Hookや、次Turn/次Toolを外部から強制できると仮定しない。ユーザー操作がない状態で何時間も無制限に開発すること、会話全文を自動収集すること、毎ターンNotion書込みを機械的に100%強制することは保証不能。
実現可能な最善策は、**同一Turnで可能なTool操作を連続実行し、実行の都度GitHub/Hostが持つ事実を再利用可能なArtifact・Currentへ記録し、次Turn/別CHATで短時間に復元して続きを実行できるようにする**こと。限界を理由に既存Toolでできる作業をMasterへ返さない。

### 9.6 実装優先度と検証条件（部分完成を完成としない）
- **P0 Observation readback:** PR #247のHost観測ArtifactをRun/Request IDで検索し、ダウンロード/整合検証して次CHATの決定へ使用する。Artifact名の同一SHA衝突や有効期限も扱う。Source設置のみでは不可。
- **P0 Lossless Host result:** 既存Host ledger/分割出力/export/assembleを実Actions→CHAT取得へ接続。Unicode stdout/stderrの順序・bytes/hash/completeを厳密一致。Issueコメントへ全文は戻さない。
- **P1 CU State:** 登録ProjectでCurrent/設計/Notion判断/最新Observationを読み、別CHATから元会話手貼りなしで少なくとも1つ次のTool actionを実行。
- **P1 Missing record detection:** GitHubイベントに対してCurrent evidence、Notion decision URL、design revisionの欠落を検知・復旧候補へ。存在しないCHAT Hookを機械強制したと報告しない。
- **P2 Management:** 企画・調査・設計・開発のCU階層と成果EvidenceをGitHub Project/Issue/PRで運用。タスク消化件数でなくAcceptance充足を進捗とする。
- **P2 Registered Repo/Live/ZERO:** Source/CI/Merge/Host Live/consumer/ZERO検索を別々に証明し、11Repoの読み取り登録をすべての反映資格と誤認しない。

設計採用後のSource実装は既存Ownerや他CHATの変更と衝突しない小さな差分に限定。本文は設計であり、Runtime合格やNotion自動記録の完成宣言ではない。

### 9.7 採用根拠・現状証拠（設計案の検証入口）
Notion検討: https://app.notion.com/p/3facdcf128e4816793c7c611228e9dad
本日のMaster構想復元: https://app.notion.com/p/3facdcf128e481ba9899d003cac95e5c
既存設計: `docs/SERVER_CORE_DESIGN.md` §16.11 / §17
PR #247 Source/CI/Merge: https://github.com/G-ACE-inc/server-core/pull/247 （merge `ec982f86bccbfe0771bb216d24ea60b2e7c3374b`）


## 10. GitHubの機能を正しく組み合わせる具体設計（2026-10-15再調査）

### 10.1 現状の問題と責務再配分
Issue #10には大量のHost結果・履歴が集中しており、Issue #40にもCHATルール・引継ぎ履歴が蓄積する。IssueコメントをログDB、Current、計画、タスク、議事録の代用にしない。他CHATがIssue出力・ページングの不具合を修正中であり、この設計では当該実装に並行変更をかけない。

| GitHub機能 | 正しい責務 | G-ACEの既存状態 / 差分 |
|---|---|---|
| **Projects v2** | Portfolio内のEpic/CU/Task一覧、進捗・優先度・Owner・阻害・受入条件を俯瞰するCurrent | Project #1は存在。Items/Fieldの実readbackと更新権限を確認できた範囲で使う。見えない値はUNKNOWN。GitHub Projectが実際の司令塔になっていることは未証明 |
| **Issue** | 企画目的、CU、要求/受入条件、Blocking、決定の現行スナップショット（短い本文・リンク） | #10は共通Terminal owner、#40はCHAT継続 owner。数百コメントの全取得は禁止。結果本文/巨大ログをIssueコメントへ書かない |
| **Sub-issues / dependencies** | Epic→CU→Taskの親子関係、BLOCKED BY・阻害解除 | GitHubネイティブ機能を優先。既存Issueを関係付け、新しい巨大な管理Issueや独自タスクリスト基盤を増やさない。API対応は連携権限を確認 |
| **Issue types / Labels / Milestones** | Feature/Bug/Task、実行状態や波次の分類 | GitHub標準の設定がProject #1で実際に利用可能か確認。無理に新Label体系を量産しない |
| **Branch/Commit** | 変更隔離、exact SHA、実証可能なSource履歴 | 設計Branch/PRと実装Branch/PRを分離し、CommitをCU/Issue/設計Revisionにリンク |
| **PR** | Design proposal採否とSource変更審査、CI・影響・証拠、Owner競合回避 | 設計PR #246はDraft（採用前）、実装PR #247はmerge済み。採用済み設計(main)とDraftを取り違えない |
| **Actions** | 既存CI・承認済みHost request実行とStatus observation | 現行共通Workflowを流用する。Status=successは受入条件完了ではない。実Host、active consumer、ZEROを別確認 |
| **Artifacts** | stdout/stderr全文、TXT/ZIP、検証材料、観測JSON | PR #247観測ArtifactはSource完成。Run ID / artifact ID / request ID / digestを保持。保持期間切れ・権限・ダウンロード未確認はNOT_VERIFIED |
| **Releases/Deployments** | 採用済み反映・リリース証拠（実運用がある場合） | 既存の受入資格・反映経路が確認できた場合のみリンク。新しいDeploymentフローは作らない |

GitHub自身の公開推奨パターンを採用する。Docs: https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/planning-and-tracking-work-for-your-team-or-project 、https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues.md 。旧Tasklist blocksは廃止方向であるため、現在サポートされるSub-issuesを優先（https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/about-tasklists）。

### 10.2 GitHub標準機能をReuse Firstで適用する順序
1. **Projects built-in automationを監査**: 既存Project #1 のItem追加・Issue close・PR merge→Status変化の設定をFresh readbackし、採用条件と一致したものだけ利用。GitHubの既定自動化は「PR merged→Done」などを行うが、**CUのRuntime受入完了とは別**。実行完了に偽装する設定があれば無効化/Statusの意味を分離。公開仕様: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-built-in-automations
2. **Issueの親子・依存を整理**: 巨大なComment連鎖はTask分解と無関係。既存#10/#40をControl ownerのまま使い、実作業CUと必要なSub-issuesをProject#1へ関連付ける。新Issueは明確な受入条件とOwnerがある時のみ。
3. **PR連動**: 設計PRは採用の検討・設計差分、実装PRはSource変更/CI、IssueはそのCUの要求・受入・阻害状態を保持。PR本文にDesign SHA、CU/Issue、変更範囲、証拠、残課題を短く記載し、各連携URLで追跡できるようにする。通常の技術判断をMasterへ差戻さない。
4. **Actions evidence**: 既存Workflowのrun/job/check、exact HEAD、Host request_id、結果SHA/状態を構造化し、CUのCurrentへリンク。Actions成功とHost/Runtime実機合格を混同しない。
5. **Artifact result contract**: GitHub RESTでrun artifact一覧→特定IDを取得→ダウンロード→manifest SHAを照合し、その観測に基づく次Tool actionを実行。GitHub RESTではArtifact Downloadの短命Redirectと権限が必要（https://docs.github.com/en/rest/actions/artifacts）。コネクタに取得Toolが不足していれば、既存認可済みGitHub Actions/Host routeを使って範囲を埋め、新Tokenを作らない。
6. **最小Current同期**: Project Item Fieldを読めるToolがある場合はネイティブ項目を更新し、不可ならowning Issueの短いCurrent項目とPR/Actionsへのリンクで補う。Project v2を「運用できる」と主張するには、対象Itemへのread/write/readbackの証拠が要る。

### 10.3 Statusを区別し、GitHubネイティブ自動化による偽完了を防ぐ
GitHubのPR Merge/Issue Closeに連動するProjects built-in Status=Doneは、**作業項目のGitHub状態**であってMasterの製品要求の受入達成ではない。Source/CI PASS、Merged、Host-Reflected、Live-Verified、TGserver-ZERO-Verifiedは各々独立証拠で表す。既存Status値に過剰な新規フィールドを作らず、既存CU acceptanceとEvidence URLの集合で総合判定する。

### 10.4 GitHub Projectの操作不足と軽量回復
- 通常GPT CHATでGitHub Project v2 Item/Fieldを操作できるか、既存Plugins/ConnectorとGitHub APIのread/write capabilityを確認。未露出の場合は「GitHub自体ができない」ではなく**このCHATの接続可能Toolが不足**と分類。
- 代替は既存GitHub Repo/Issue/PRの最小CheckpointとRun Artifact URL。GitHubの組み込みProject自動化が使える場合はそれを優先する。
- Issue全コメントのページング、巨大全文コメント、同一診断の反復や別Repoへの勝手なWriteを禁止する。Failure時はRepo/CI/Run IDで直接Evidenceへ到達し、下一Actionを明示する。
- 他CHATがIssue I/Oを担当しているため、このCUではOwner境界を越えない。

### 10.5 公開部品を再利用する場合の採否条件
**採用**: 既存プロジェクトから直接利用できるGitHub標準機能（sub-issues, dependencies, built-in Projects automation, Issue Forms, Actions artifacts）と、GitHub REST/CLI・既存SDKで提供される操作。API/CLIの成熟したクライアント機能は既存接続Toolができないところに限定して再利用してよい。

**追加実装が必要な時だけ**: 現存Tool/APIを先に動作確認し、同じRepo/CU/Design revisionでSource gap・必要なinput/output・検証可能な受入条件が証明された小部品のみ追加。外部のProjectサーバーやAgentエンジン全体を新設せず、採用元ライセンス/依存/メンテ費をその部品についてだけ評価する。

### 10.6 現場での完成テスト（GitHubの使い方そのものを検証）
- Project #1の実Itemを1件、Field/関連Issue/Owner/Acceptanceを読取り、CUと設計PR/実装PR/Commit/Check/Host/Artifact/TGserverへの正しいリンクを再構成する。
- 実CUに既存IssueのSub-issue/Dependencyを使えることと、Status automationが受入条件を誤判定しないことを確認する。
- 設計PR→実装PR→CI→Hostの各段階で、Project CurrentとIssueに最新状態とNext Actionを残し、別CHATで取得できる。
- GitHub Actions Artifactが、一覧→識別→ダウンロード→SHA照合→次のCHAT Tool実行までつながる。期限切れ・権限不足・部分欠損でも偽PASSにしない。
- Notionには議論の採否・設計背景、GitHubにはSourceとCurrent、TGserverには実行イベントを置き、同一の巨大ログを複数箇所へコピーしない。

以上を含む§9までの設計に対する追加章であり、設計提案であって新機能のLive完成を意味しない。


## 11. 実用版アーキテクチャと接続契約 — 近似Codex/Cursor運用の設計完了基準（2026-10-15）

**決定:** 100%同一のIDE/常駐Agentを実現するのではない。MasterがCHATを変更しても説明をやり直さず、既存Toolの組合せで企画・設計・開発の一つのCUを継続できる状態を**実用的な近似完成**と定義する。この章で曖昧な概念を実装可能な入力/出力/失敗経路へ落とす。§16.11/§17のAuthorityおよび既存Ownerを変更しない。

### 11.1 二層制御：CHATとGitHub/Hostの責務
- **判断層＝通常GPT CHAT**: Project Currentと採用設計を読み、ユーザーの目的・制約から実行手順を選択し、Toolを呼び、結果を読み次のActionを決定。Notion Toolが使用可能な場合、当該ターンの議論差分を保存する。自動的な次CHAT起動、非公開CHAT履歴の収集は担当させない。
- **耐久制御層＝既存GitHub Project/Issues/PRs/Actions/Artifacts＋TGserver ZERO**: 実行事実（SHA、Run、Result、Status、Artifact）と最小Checkpoint、Owner、受入条件を管理する。既存ActionsはTool送信・検証・観測記録、Hostは任意コマンド/隔離dev.job実行。反復をCHAT側の次Tool呼出とつなぐ。
- **議論/設計層＝Notion＋Repo設計**: Notionに要求・採否・理由、Repo mainに採用設計、設計PRに未採用の改訂。どちらもHostログDBの代用品にしない。
- 常駐Agentを新設せず、既存イベントが確定した時点で耐久Checkpointを更新する。CHATが応答を終えても少なくとも次のCHATがSource/Artifactから再開できる。

### 11.2 Tool能力表と実行アダプタの最小契約
各Toolを同じ巨大なインターフェースに包まず、**実際に公開される既存Toolを呼ぶだけの選択表**をCurrentに置く。
| 動作 | 第1選択（既存） | 代替/制限 | 記録すべき応答 |
|---|---|---|---|
| 現在地読込 | GitHub Projects Item/Issue/PR/Commit API | Projects Field API未露出ならIssueの小さなCurrent | canonical issue URL / design SHA / owner / head SHA |
| 企画・意思決定 | Notion fetch/create/update | Notion API不可なら`MINUTES_NOT_RECORDED`をCurrentに記載 | Notion page URL + write receipt |
| 設計変更 | 設計Branch/PR/GitHub API | Draftは採用済みmainを上書きしない | PR URL, diff, proposed SHA |
| Source変更 | owning Repo GitHub API / admitted dev.job | 別Owner/Repoへの横断書込不可 | commit SHA, paths, PR URL |
| テスト・Host読取 | 既存Actions→Gateway→Receiver→host.command/dev.job | 旧固定コマンド経路使用禁止 | request_id, run_id, result locator, Host exit |
| Host長大出力 | Host ledger read/export と既存Artifact/ZIP復元 | Issueコメントにはメタデータのみ | 完全性/bytes/hash/Artifact ref |
| 進捗証拠 | PR Check Run/Actions Job | 成功をRuntime完成とみなさない | test SHA, conclusion, consumer evidence |
| 横断ログ | TGserver ZERO既存Reader | Producer不在ならUNKNOWN | event ID, storage/search readback |

**実行前提**: Tool接続の有無を実測して分岐する。Toolが存在してもAPI権限/対象Repo承認/実Host反映資格が無いなら`CAPABILITY_UNVERIFIED`。MASTERに通常のTool選択を求めない。

### 11.3 Checkpoint schema v1（置き場は既存GitHub CU Current）
これを**最小の論理スキーマ**として固定し、GitHub Issueの既存Currentまたは既存Project Itemで実体化する。新DB、新Workflowを設けない。巨大な履歴はappendせず、現行版を更新し、イベントへの参照だけを残す。

```json
{
  "schema": "gace.chat.cu.current.v1",
  "cu": {"project": "G-ACE Development Platform", "issue_url": "<canonical CU URL>", "repo": "<owner/repo>", "owner": "<owner-id>"},
  "goal": {"purpose": "<fixed user outcome>", "acceptance": [{"id": "A1", "state": "OPEN|EVIDENCED|BLOCKED", "evidence_url": null}]},
  "design": {"adopted_url": "<main design URL>", "adopted_sha": "<40-char SHA>", "draft_pr_url": null},
  "source": {"branch": "<branch>", "head_sha": "<40-char SHA>", "pr_url": null, "ci_url": null},
  "execution": {"request_id": null, "run_id": null, "artifact_id": null, "result_url": null, "host_sha": null, "result_status": "UNKNOWN", "output_complete": false},
  "decisions": {"notion_minutes_url": null, "minutes_state": "RECORDED|MISSING|NOT_APPLICABLE", "reason": "<brief>"},
  "continuation": {"phase": "RESTORE|PLAN|ACT|OBSERVE|DECIDE|VERIFY|CHECKPOINT|STOP", "next_action": {"tool": "<available existing tool>", "target": "<verified target>", "reason": "<linked acceptance>"}, "blockers": []},
  "version": 1,
  "updated_at": "<ISO timestamp>"
}
```

注意: これは**サンプルの値**でありGitHub Project Itemの取得済み値ではない。Secret/生ログを入れない。採用設計SHAはmainに採用された実コミットのみ。更新競合はProject/CU Ownerと直前version/readbackを照合し、競合時に書込を中止して再読込。新しいCHATは最新CU CurrentとGitHub SHAをFresh比較する。

### 11.4 状態遷移・障害対処（判断表）
| 現在状態/観測 | 許す次状態 | 復旧動作 |
|---|---|---|
| RESTORE / Current一致 | PLAN | Adopted design・Owner・Source HEAD・未完了Acceptanceを選択読込 |
| RESTORE / stale SHAまたはOwner衝突 | RESTORE/読取調査 | Source/PR Fresh readback。異なるOwner checkoutを保護 |
| PLAN / 実行可能Taskあり | ACT | Next Actionに具体的Tool、target、目的、Expected evidenceを設定 |
| ACT / result queued | OBSERVE | 既存run/request IDで結果を追跡。別のHost Requestを重複送信しない |
| OBSERVE / full PASS | DECIDE | exitとSHA/出力完全性を確認。Acceptance達成は別VERIFY |
| OBSERVE / output partial | OBSERVE | Host ledger/Artifact全ページ回収。PartialをPASS扱いしない |
| OBSERVE / API outage, timeout | OBSERVEまたはDECIDE | 送信受理の有無と結果未着を区別し、request IDで安全に再取得 |
| OBSERVE / FAIL | DECIDE | 原因から別の観測/修正Actionを決める。無意味な同一retry禁止 |
| DECIDE / 残Acceptanceあり | ACTまたはPLAN | 未達条件へ連続実行。報告/Check成功でSTOPしない |
| VERIFY / exact CI, live, ZEROが必要な範囲で一致 | CHECKPOINT | 各Evidence URLを別Statusで保存 |
| CHECKPOINT / Notion失敗 | DECIDE | 失敗をMISSINGとしてCurrentに保持し、独立開発は継続 |
| STOP / verified acceptance or explicit interrupt or all blocked | STOP | 完成と未完成、復元用next actionと理由を保存 |

**Replay防止**: 既存Request ID / Actions run / committed source SHAから「送信済み」「結果不明」「完了」を識別し、API outageを即座に新規同内容Dispatchへ変えない。独立CUの進行を停止しない。

### 11.5 会話/作業中に管理が抜ける問題の実用策
1. **発生元で事実を拾う**: GitHub CIとActions Host Resultを既存Workflowが記録。Notionへ無制限の新Tokenを渡さない。
2. **CHAT側では議論差分だけを追記**: 毎ターンNotion書込の既存ルールは尊重し、採否・判断変更・実行証拠リンク・次Actionを短く保存。記録結果を確認できなければ欠落としてCheckpointへ。
3. **漏れ検知は次回復元時に行う**: Last PR/Run/HostとCurrent version/Notion URLを比較し、イベントが進んでいるのにCurrentや議事録が古いときだけ必要箇所を補修する。無理な遡及的捏造禁止。
4. **短い自律Loop**: 可能な限り同一Turnで複数Actionを実施。CHATアプリが一旦停止・中断しても、次TurnでCurrentとEvidenceを読み復帰。ChatGPTが自分自身に将来の任意Turnを送信できると仮定しない。
5. **タスク進行**: 企画・調査・設計・実装・検証のどの種類も、Purpose・Acceptance・Owner・Current・Next Actionを持つCUとして扱う。

### 11.6 「近いものができた」の判定（100%再現ではなく使い勝手）
**採用設計の完成**: §11.1〜11.5の契約が既存Toolへ一対一で対応し、実装順・失敗・再開を判断できること。新規Agent製品の導入が不要であり、各段階に実測可能な成果物があること。

**使える運用の最小合格シナリオ**:
1. **企画→Task**: 一つのProjectの目的・採否をNotionへ記録し、GitHub Issue/CUと設計PRに関連付け、次作業を取り出せる。
2. **設計→実装**: 採用済み設計SHAを読込んでから、GitHubで変更→CI→Host command→Observation→少なくとももう1回の異なるTool Actionを同一CUで実行できる。
3. **失敗→継続**: 故意の失敗/巨大ログ/Host API障害のどれかで、実行済みRequestの結果を見失わず、次の有意味なActionへ移れる。
4. **CHAT引継ぎ**: 別CHATが前CHATの全文やMasterの手書き説明なしに、Current→Notion決定→設計→最新Observation→次Actionを読んで実際に一つ作業を進める。
5. **事実に基づく完成**: Source/CI/PR mergeとRuntime/consumer/ZEROを対象要求に応じて区別し、完成していないものを完成と言わない。

**運用改善の定量的指標**: 人間による過去CHAT再説明回数、手動コマンド転記回数、Current/Notionの更新欠落数、観測→次Actionまでの実Tool呼出数、設計逸脱による差戻し数、失敗したToolの同一理由再試行回数。比較用Baselineを実測してから改善を判定し、未実測値を捏造しない。

**実装優先**: P0: 現在ある#247〜#249・Host ledger/ZIP結果をCHATへ読戻す。P1: Current schemaを既存Project/Issueで実運用、次CHAT復元、記録漏れ検知。P2: 企画/Task/依存/StatusのネイティブGitHub Projects運用に拡張。各段階で実用テストし、完成を全フェーズ達成まで先延ばしにせず、先に使える最小機能を提供する。

**安全と最小実装**: 製品丸ごと移植や導入はしない。実際のSourceで見つかった不足がGitHub標準機能、既存Plugin、OSSライブラリの小部品で埋まるなら優先的に再利用する。オープンソースのコード流用が必要な場合だけ該当部品のライセンス・更新負担・互換性を確認。既存Issue I/O修正の他CHAT所有領域には手を出さない。


## 12. GitHub Issue大量情報の改善を既存Agentに取り込む（2026-10-15）
**今回のユーザー決定は「Issueの大量本文・コメントを、GPT CHAT側からTXT/ZIPファイルとしてダウンロードして扱える運用機能を採用する」こと。** Action Artifactをサーバー側で作るだけでは要件を満たさない。Agent側で既存GitHub ConnectorのArtifactダウンロード機能を使用し、必要時だけZIP内のTXT/JSONL/manifestを読んで判断する。変更対象はAgent側の取得選択・CU継続であり、他CHATが完成させたIssue I/O自体は再開発しない。 Project主目的と§11のAgent Loopを変更しない。

### 12.0 採用済みIssue運用の優先順位（§10を正本とする）
**基本は§10のGitHub Project→Issue→PR→Actions→Artifactsの責務分担。** IssueはCUの目的・受入条件・未解決事項・短いCurrentと証拠URLを保持し、Projectが全体進捗を管理する。Notionは議論の意味、PRはSource変更、Actions/Artifactsは実行事実と大容量データを担当。TXT/ZIP導入を理由にIssueをログDBに戻したり、Agentの目的・Owner・Next Actionの決定順序を変えない。

**通常の読み取り:** Project/CU Currentと採用設計→必要なIssue本文/既知コメントURLの限定取得→PR/Run/Artifactの関連証拠→次Action。この範囲で足りればTXT/ZIPは呼ばない。

**追加の取得手段:** コメントが大きい、全文が必要、部分API取得が欠損する場合のみ、既存のIssue Export TXT/JSONL/ZIPをCHAT側にダウンロード。既存Artifact優先、新規Exportは不足時のみ。全文を会話へ貼らず、必要箇所の検証後、CUの同じ受入条件に戻る。

**例外と継続:** Issue #10への全コメント走査は日常運用禁止。特定Run/Artifactを知っていれば直接使用し、取得障害でも独立したGitHub Source/設計/Notion/Tool操作を続行。大量資料取得は目的ではなく判断の補助手段である。

### 12.1 実装済みのReuse First
- PR #250: 既存の`.github/workflows/chatgpt-live-api-verify.yml` の`[issue-export]`要求を使用し、任意の対象`owner/repo#Issue`についてUTF-8全文TXT・JSONL・ZIPを既存Actions Artifactとして発行。Issue本文と全コメント、件数、bytes、SHA-256、重複ID/ページ整合性をmanifest化する。**ただしこの全量ページングはActions内の明示的Exportだけ**。出力したArtifactのIDとRunをCHATが取得し、既存GitHub Connectorの`download_workflow_artifact`からCHAT側へZIPをダウンロードできる方式として利用する。通常CHATのIssueコメントAPI全件呼び出しやIssue本文への巨大な再投稿はしない。
- PR #253: GitHub TokenのRepo間Issue書込制限を尊重し、Artifact locatorを認可済みProjectのControl Issue #10へ登録。登録先のProject制御Issueと、実際にExportした対象Repo/Issueを混同しない。対象Issueへの横断コメント作成権限を増設しない。
- Issue #10はHostの制御/Indexとして維持。最新メタデータ/Project Current/Run ID/Request IDを優先し、Issue #10の約1000件コメントを日常処理で再読込しない。
- 既存PR #247, #251, #252, #254, #255, #256: Host observation／Actions Artifact／run-specific restore／CU next-action handoffが別系統で存在。**Issue全文Export ArtifactとHost Observation Artifactを混同しない**。

### 12.2 データ種類に応じた選択方式
| Need | 最小読み取り経路 | 大量時/失敗時 | Agentの次Action |
|---|---|---|---|
| 現在の目的・Acceptance/Owner/最新設計 | Project Item、Issue本文の最新Current、PR/Commit | 対象の最小範囲だけfetch、見えないFieldはUNKNOWN | 次のToolへ直接進む |
| 一つの変更に関連する特定Issueコメント | ID/URLまたは新しいコメントの短い範囲を選択 | サイズ/件数が過大なら既存Issue Exportを要求 | エクスポートを実行・Artifactを取得 |
| Issue全文の意味分析・歴史的な経緯 | 既存[issue-export] Runのmanifestを確認 | 対象IssueのTXT/JSONL/ZIPをGitHub ArtifactからDLし、必要な部分だけ意味的に検討 | 文書中の具体的意思決定をNotionに要約、Currentへ成果を反映 |
| Host任意コマンドの状態・失敗 | Request ID→GitHub Run→host observation Artifact | Host Ledgerへ切替、欠損の無い全文が要る時のみExport | `continuation_checkpoint`から次Toolを選択 |
| リポジトリ横断の文脈 | Project#1 registered repoと各CUのURL | Unauthorizedは既存許可範囲を調査。独自Token追加や権限拡張なし | 取得できたSourceの範囲で独立作業を継続 |

### 12.3 ArtifactとCUの結合契約
- Issue Exportは`target_repo`, `target_issue`, `actions_run_id`, `artifact_id`, `artifact_url`, `manifest.text_sha256`, `manifest.exported_comments`, `snapshot_at`を証拠としてCUへリンク。Host Observationは`host_request_id`, `actions_run_id`, `artifact_id`, `source_sha`, `result_url`, `next_action`を別フィールドに保持。
- **全量Export=必要に応じて再利用可能な証拠**。同じIssueを毎CHAT移行で必ず全量Exportしない。新しいコメントが追加された時はスナップショットの鮮度を表示し、必要箇所だけFresh取得する。
- Issue ExportについてはRun/Artifactを持っているだけで`CONTENT_ANALYZED`を主張しない。ダウンロード・manifest件数/bytes/hash一致の後に実際に資料を読んだ範囲と判断を示す。
- Cross-repo Indexに記録された`Issue #10`は**artifactの登録場所**。内容の所有者はmanifestのTarget Issue。対応付けを変えない。
- API障害、Artifact期限切れ、Permission不足は`UNVERIFIED`として扱い、誤った新規DispatchやIssue全文再取得を連打しない。

### 12.4 CHAT側での具体的な操作契約
1. CHATが対象Issueを最小メタデータで特定し、必要なら既存Project Controlに記録済みの `Issue Export Run ID / Artifact ID / target_repo#issue` を取得する。
2. 既存Artifactがなく全文が必要な場合のみ、既存 `[issue-export]` Requestを使う。生成済みなら再Exportしない。
3. **CHATからGitHub Connector `fetch_workflow_run_artifacts` → `download_workflow_artifact` を呼んでZIPファイルを取得**する。ここが今回の利用可能範囲拡張の中心であり、Actions Upload成功だけではCHATで取得成功とは判定しない。
4. ZIPの `manifest.json` と `issue-comments.txt` / `issue-comments.jsonl` のTarget、byte数、SHA-256、件数を確認する。ダウンロードした大容量ファイルをGPT CHATへ文字列全量貼付しない。必要箇所を分割して分析・要約し、元の意味/証拠を保持する。
5. 結果は既存CUの目的・採用設計・Next Actionへ反映してAgent Loopを続行する。TXTとZIPは**追加の資料取得手段**であり、プロジェクト目的も優先順位も変えない。
6. Connector側の返却がファイル参照に留まる場合は、利用できる既存ファイル読取経路で内容を検証する。ファイル実体を読めていない状態で `CHAT_DOWNLOADED_AND_ANALYZED` を宣言しない。

### 12.5 受入条件
1. 既存のIssue Exportを再利用し、GitHub Project登録Repoの特定IssueをTXT/ZIPで取得。stdout巨大貼付をせずmanifest照合する。
2. Target IssueとControl Index #10が異なるケースでも、誤ったSourceに意思決定を関連付けない。
3. IssueメタデータとHost Observationを別Artifact契約でCUに結び、次CHATがCurrentから目的/設計/次Toolを復元し実行する。
4. Issue Export作業の成功だけでAgent CU/Host Runtimeが完成したとは判定しない。必要な他作業は同一Turnで継続する。


## 13. 採用設計：Notion無料枠の文脈DB活用（2026-10-16）

### 13.1 最上位の決定と既存資産
Masterが「Notionを議事録を含む判断・設計・知識・引継ぎ・関連タスクのDBとして効率的に利用する」を採用。ただし**すべてをNotionに寄せる指示ではない**。既存GitHub Project/Issueの正式なOwner・進捗・Acceptance、Repoの正式設計/Source、CI/Host/Runtimeの実証、TGserverのRaw Log、VaultのSecretを**変更・移管・廃止しない**。新DB・有料プラン・自動化・Token・Workflowは必須条件にしない。

既存Notion PageをReuse First：`01 議事録・Continuity Log`、`02 Architecture・Authority`、`03 Lifecycle`、`05 Current State`、`06 並列CHAT Ownership`、`07 新CHAT Handoff`。古いNotion SnapshotのStatusはLive正本ではなくGitHub Project Currentへの参照とする。運用前に既存データベースと属性を探索し、同等のものを追加作成しない。

### 13.2 責務分担と二重管理禁止
| データ | Authority | Notionでの扱い |
|---|---|---|
| Project Task Status / CU Owner / Acceptance | GitHub Project/Issue | URLと判断理由、依存関係の表示のみ。独立した可変Statusを重複管理しない |
| 正式設計 / 実装 / 採用SHA | GitHub Repository / PR | 判断の採否理由・設計比較・影響Project・Source permalinkを索引 |
| Raw Host結果 / CI / Runtime PASS | Actions Artifact / Host / TGserver | 証拠URLと最終照合時刻、検証不足・次に確認すべき事項 |
| 議事録・意思決定・研究比較・既知失敗の意味 | Notion | Notionを主管理先として構造化・検索可能にする |
| 大容量PDF/参考資料・長期保管ZIP | GitHub ArtifactまたはGoogle Drive（容量・保持期間・用途で選択） | ファイル本体を複製せず、Drive/Artifactの実URLとhash、対象CUへの関係を表示 |
| Secrets / Credentials | 既存Vault | 記録しない |

### 13.3 初期データモデル（概念契約）
Notion側の最初の候補は**既存議事録の再利用＋最小の『Decision/Context Index』**。DB新設前に既存Notion構造で検索・Relationが不足することを確認する。必要属性：
- `context_id`（Notion側識別子）・`cu_url`（GitHub正本の照合キー）・`project`・`topic`・`summary`
- `record_kind`（DECISION / DESIGN_RATIONALE / RISK / DEPENDENCY / FAILURE_LESSON / RESEARCH / HANDOFF）
- `decision_state`（PROPOSED / ADOPTED / REJECTED / SUPERSEDED）と`decision_reason`、決定した人・日時
- `github_design_url` / `design_sha` / `pr_url` / `issue_url` / `run_url` / `artifact_url`
- `depends_on`（関連CU URL）・`next_action_rationale`・`last_checked_at`・`evidence_confidence`（VERIFIED / STALE / UNKNOWN）
採用/却下の履歴は削除・上書きせず、後続決定からSUPERSEDEDを示す。Notionの多重Relation/巨大全文は設計上の必須条件にしない。CurrentやNext Actionの**実行可否**は最新GitHub/Runtimeの読戻しで決める。

### 13.4 Agent Loop統合手順
1. `Manifest→Rule #17→GitHub Project Current/Issue CU→採用Repo Design SHA` の現行起動順を維持。
2. 現在のCU URL／Project／設計変更テーマをキーにNotionから**必要範囲だけ**判断記録を検索。最新レコードの日付だけでなく、採否・正本リンク・更新元を確認。全議事録や全DBを毎回読み込まない。
3. `RESTORE`: GitHub CurrentのOwner/Acceptance/Next ActionとNotionの採用理由・依存・既知失敗を併記。競合時は自動上書きしない。Notion古いSnapshotはSTALEとして扱う。
4. `PLAN→ACT→OBSERVE→VERIFY`: 既存のGitHub/Host/TGserver Toolを実行し、SHA/Run/ResultのFresh evidenceを得る。
5. `CHECKPOINT`: 採否理由・未解決リスク・新たな学びのみNotionに増分記録。正式タスク状態とCIはGithub、Raw LogはTGserver/Artifactへ。NotionにRunの巨大本文を貼らない。
6. 次CHATはCurrentから最小Notion文脈レコードを復元し、**少なくとも一つ実際のTool Action**を続行。Issue #10の全コメント取得を前提にしない。

### 13.5 無料プラン制約とGoogle Drive補完
- Notion Free：DBと基本属性は利用可、ファイル1個最大5MB、個人利用のページ/ブロックは原則無制限、複数Memberはブロック上限が適用され得る。公式 https://www.notion.com/pricing 。現在の実ワークスペース人数・接続権限は未確認のため`UNKNOWN`。
- Notion有料のDB自動化、Notion AI常用、Custom Agentや有料同期を**依存機能にしない**。既存CHAT/Pluginから必要時に読書き、連続実行可能な範囲で対応。
- 5MB超ファイルはMasterが指定した `asterav8@gmail.com` 側Google Driveを**利用候補として許可**。ただし対象接続アカウント・実アクセス権・空き容量・保存フォルダが確認できた場合に限る。ユーザー指定外アカウントへ誤保存しない。
- Storage routing：一時CI証拠→Actions Artifact、Raw開発Log→TGserver、正式Source→GitHub、長期研究PDF/参照ZIP→Drive優先候補、Notion→小さなContext Index・リンク。不要な重複コピー・自動全量同期は行わない。権限/秘匿性が担保できないものは移さず既存場所に残す。

### 13.6 比較評価と導入順
優先度A（採用して詳細化）：決定・採否理由、設計変更の影響、CHAT引継ぎの文脈、障害原因/再発防止、DependencyとAcceptance未実証の**索引**。既存議事録と正本リンクを使用。
優先度B（実測後に判断）：技術比較・研究文献の索引、日報の理由付け、横断リポジトリ資産台帳。管理増加が上回るなら拡張しない。
不採用：NotionへGitHub Task Statusを移管、二重設計Source、Raw Log全文とCI Artifactのコピー、Vault Secretsの保存、Notion Freeにない自動化に依存、既存DBの破壊的移行。

段階的受入：
- `DESIGN`: 責務境界・保存先・検索キー・無料枠・失敗時Fallbackを合意してGitHub設計PRへ記録（この段階）。
- `PILOT`: 既存CU 1件の議事録→採用理由→設計Source URL→証拠リンクをNotion検索で復元。GitHubのCurrentと突合し、実Toolを1回以上継続。DB新設は検索不能が確認できたときのみ。
- `MEASURE`: ベースラインと比較して、新CHAT復元時の読取件数・検索回数・再調査回数・重複/矛盾数・記録失敗数・呼出回数・無料枠負担を記録。改善率を測定前に宣言しない。
- `EXPAND`: 効果が確認された種類だけ対象Projectへ広げる。現状を壊す移行は行わない。

この節の反映は**設計採用**であり、Notion DB新設、Google Drive移動、Host反映、CHAT引継ぎの本番E2E達成を意味しない。


### 13.7 Master開発方式における議事録の完全な対象範囲（最優先）
Masterは非技術の企画・要求・優先順位・最終完成判断を担当し、GPT CHATが**アイデア創出、問題発見、選択肢生成、外部調査、比較、反証、採否提案、詳細設計、実装、必要検証、障害解析・再設計、Host反映、実利用確認、引継ぎまで一貫して起点・担当**する。したがってNotion議事録は会議決定の要約でもPR/CIの日報でもない。**アイデア発生から開発完成までを意味と根拠を保ったまま再開できる開発思考・行動・判断の連続記録**である。

各有意味Checkpointで記録する最低契約：
1. `IDEA / PURPOSE`：Masterの元の要求、GPT提案とその発想元、解こうとする本質的課題、期待結果、変えてはならない条件。
2. `DISCOVERY / RESEARCH`：調べた資料・実装・ログ・事実とSource URL、判明事項と不明事項、推測/実測の区別。
3. `ALTERNATIVES / REASONING`：比較案（不採用案含む）、評価基準、長短、制約、代償、判断を覆す条件。次CHATが同じ比較を再実施しない水準まで。
4. `DECISIONS / DESIGN`：Masterの採用決定とGPTの技術判断を区別し、理由・影響範囲・設計の採用版SHA/PR、未確定事項と依存関係。
5. `IMPLEMENTATION / OBSERVATION`：実際に変更した対象、PR/Commit/Actions/Host/TGserverの証拠URL、期待と実結果、不具合の原因仮説と修正理由。生ログ全文はNotionへコピーしない。
6. `VERIFICATION / ACCEPTANCE`：必要なテスト、実利用上の達成条件、Source/CI/Merge/Host/Consumer/ZEROそれぞれの達成/未実証、Master完成判断との関係。
7. `CONTINUITY / NEXT`：現在位置、未完成の機能・未解決障害、次の具体的Tool Action、再開に必要なURL、他CHATのOwnerと衝突防止条件。

記録は**作業を毎回1件で止めるGateではない**。同一Turnで可能な限り実作業を進め、意味のある設計変更・判断変更・失敗原因・完成単位の都度Notionへ増分追記する。通常のツール出力や重複ログを逐語的に貼り付けないが、Masterの訂正やGPTの却下案・設計の理由を意図的に削らない。メモの記録だけではタスク完了にしない。

**復元の完成条件**：別CHATがGitHub Currentを正本として読み、Notionのアイデア→比較→採否→設計→実装履歴→未実証→次Actionを再構成して、Masterに前提説明を求めず、実際の異なるTool Actionを1件以上続けられること。記録が欠けている場合、過去の判断を推測で補完せず欠落として追記対象にする。
