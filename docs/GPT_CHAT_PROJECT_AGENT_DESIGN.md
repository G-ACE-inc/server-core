# GPT CHAT Project Agent — 設計案（2026-10-15）
Status: DESIGN PROPOSAL / NOT IMPLEMENTATION COMPLETE
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
