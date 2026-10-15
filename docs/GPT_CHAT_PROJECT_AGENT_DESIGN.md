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
