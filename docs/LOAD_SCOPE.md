# SERVER CORE LOAD SCOPE / COMMAND ROUTER

Version: 2026-10-05
Role: G-ACE Workspace司令室がTaskを正しいProject / Authorityへ振り分け、必要情報だけを段階的に読ませるためのRouter。

## 1. Executor Profile / Mandatory Start

最初に実行主体を分ける。Rule payloadを混ぜない。

### SERVER_AI

```text
1. server-core/README.md
2. server-core/docs/LOAD_SCOPE.md
3. operations/github-project-rule-plane.json
4. canonical Rule Plane #16 / GitHub Project #1 Current when accessible
5. 対象Repository Current
6. 今回必要なserver-core / Project Authority・Source・Testだけ
```

### GPT_CHAT / ChatGPT Work (Master-facing orchestrator)

```text
1. Fetch operations/github-project-rule-plane.json from verified GitHub main and select GPT_CHAT profile (also ChatGPT Work coordinator)
2. Fetch the COMPLETE canonical Issue #17 body, checking beginning/end and required sections; recover truncated/missing content before treating as loaded
3. GitHub Project #1 / Control #15 / target Project owning Current; find literal PROJECT_PURPOSE_CANONICAL and active CU / mutation owner / exact next gate
4. Target repository README-linked active Design Authority + Definition of Complete (Current Task is NOT the whole-project goal)
5. Workspace/server controlが必要なTaskだけserver-coreを読む; do not pass #17 to SERVER_AI/Composer/Codex (they load #16)
6. Target Repository/CU Source/Test/CI/Runtime Evidence, check #17 pre-action gate and execute NEXT to the safe gate
7. Every development turn: fetch fresh Manifest, full applicable GPT CHAT #17 body, and owning Current before action when Master explicitly requires per-turn full readback (Current #40); otherwise revision/delta optimization applies. progress messages do not end work; Current comments also do not end work.
```

**Work routing is a selection of the existing GPT_CHAT profile, not a third rule plane or automatic Work-session injection.** When ChatGPT Work leads planning, coding, research or reports on Master's behalf, it must actually load #17 and the target product Design/Current first and distinguish `PROJECT_PURPOSE_CANONICAL` from `CURRENT_WORK_PURPOSE`; no rewrite of the whole product purpose as the active PR/module/Host issue. A delegated Work-run terminal/server Codex/Composer executor uses the existing SERVER_AI #16 and only the task-specific purpose/acceptance excerpt. Fresh readback of the active Work session and its actual actions is required to say the rule was applied.

### Master-commissioned integrated development: mission-first dispatch (existing §6)

When Master commissions improvement of the **ChatGPT-first G-ACE development platform as one task**, a request to inspect Tool B, TGserver or another capability is a **dependency check within that task**, not a new owner CU or permission to abandon the original commission. The approved project-level outcome and the unsatisfied acceptance rows C01–C09 in `docs/GITHUB_PROJECT_RULE_PLANE.md` remain the reference. Use the existing authority map: #15 owns overall migration/client acceptance, #40 owns ordinary CHAT continuity, #10 owns Tool B and common Host, TGserver #50 owns ZERO. Inspection of another owner's evidence does not transfer their mutation ownership.

After each dependency inspection, **return to the commissioned CU's next executable improvement in the same turn**, rather than reporting that the dependency exists, creating a parallel implementation, or giving Master a redundant Server AI assignment. If a dependency already has a known owner action, record its actual latest result; improve independently owned source/design/test work in the commissioned CU. Never claim an E2E acceptance stage from Project registration, a Source merge, Gateway 202, or search 0 alone.

For a genuine missing access needed to complete the commissioned CU, first exhaust currently available GitHub-native edits/PR/CI/readback; then supply **one** tightly scoped complete Server AI or Master command covering only the inaccessible step and its evidence return. Do not demand a new infrastructure install, arbitrary Host shell, broader registration, or new GPT-side UI hook. A terminal command is an exception, not the default work delegation. This is existing §6 dispatch/iterate semantics applied to the commissioned Mission; it is **not** a separate Work Routine or permission to override owner authorization.

### GPT CHAT logical work batching (within the existing Work Routine)

For an owned Change Unit, first inspect the affected design requirements, existing callers, tests, documentation decisions and expected CI conditions as **one impact set** before the first write. Plan the complete smallest coherent source-and-test diff, including positive/negative regression cases. Do not commit after each tool action, file edit, passing individual test, progress message or gate; these are intermediate checkpoints, not independent Change Units. Prefer a logical commit covering the verified cohesive change and related tests/docs. Multiple commits are appropriate when they form independently reviewable, revertible or risky steps, or preserve an intentional recovery point; do not impose a numerical cap or rewrite an active branch merely to cosmetically reduce count.

During a block/section boundary, give a short nonterminal progress explanation if useful and continue the next executable same-CU action. After a failed test or CI, inspect the exact failure and its impact before deciding whether a follow-up commit is necessary; consolidate fixes **before first commit where possible**, without hiding real recovery history after push. Treat GitHub Commit/PR/CI/Issue record as evidence milestones, not stop triggers. At the end, compare the whole CU acceptance, remaining independent actions and legitimate #17 stop criteria before any formal Master report. Do not repeatedly reload unrelated authority or start a new branch/PR for each correction. 

**Ongoing explanations are not Master reports (#17 §5/§7):** For both GPT CHAT and ChatGPT Work, concise progress/analysis/CI/PR notices are nonterminal; after explaining, execute the next safe owned-CU action. Reserve the **formal five-part report** for Master-requested pause/report, genuinely required Master-only operation/decision, major design/product-impact choice, proven Mission completion, or a verified full same-CU stop after independent work is exhausted. **NEXT is mandatory visibility for Master inside a legitimate report, never permission to end the turn or defer a runnable CHAT action.** If Master must act, supply the complete directly executable instruction. An Issue comment, CI result or progress explanation is not a reporting trigger. Do not claim this repository text can intercept live CHAT/Work responses.

GPT_CHAT拡張RuleをSERVER_AIへdefault loadしない。

README以外のserver-core Authorityを新Task開始時に一括読込しない。

同一Taskで一度確認済みの安定Authority全文は通常、変更・矛盾・情報不足が無い限り毎ターン再読込しない。ただしMasterが現在のCHATに毎ターンのManifest・適用Rule Plane全文・owning CurrentのFresh取得を明示している場合は、その要求を優先して実際に再取得する。読み込んだ事実だけで適用PASSにせず、選択したAction・継続・終了判断へ照合する。ただし開発の各ターンでは関連するGitHub Project/IssueのCurrentと対象HEAD/PR/CI等の変化を軽量に再同期し、対象変更・新規Gate・競合時だけ必要なAuthority/Source範囲を再取得する。古い履歴・別Project・GPT CHAT拡張RuleをSERVER_AIへまとめて渡さない。

## 2. Command Routing

| Task | 追加で読むserver-core Authority |
|---|---|
| server-core自身の設計/司令室責務 | `docs/SERVER_CORE_DESIGN.md` + 必要なら `docs/DESIGN_DELTA.md` |
| 開発方法論 / 責務 / 5段 / Module / 再利用 | `CORE.md` |
| 共通運用 / 禁止 / Approval Boundary | `SERVER_CORE_PROTOCOL.md` |
| Master Terminal Command / Copy&Paste / GACE_RESULT / Shell Safety / Syntax Validation | `docs/MASTER_TERMINAL_COMMAND.md` |
| Workspace運用 / dispatch | `docs/G_ACE_WORKSPACE.md` |
| Project / Repository / shared Capability / MCP / Tool / DebugAI / Runtime discovery | `docs/WORKSPACE_REGISTRY.md` |
| Tool B: GPT CHATからの既存Actions→Gateway→server-core receiver→隔離Docker開発ターミナル `dev.job`、Host読取・GitOps・Source反映 | `docs/SERVER_CORE_DESIGN.md` §16.11と§16（B0–B5）+ owning #10 Current + 必要なHost/Registry実測。DebugAI製品経路とは認可を混同しない |
| Tool A: 統合Development Logの収集・送信・TGserver ZERO保存・検索・CHAT間復元 | `docs/SERVER_CORE_DESIGN.md` §17（A0–A4）+ `docs/PROJECT_INTEGRATION_RULES.md` + TGserver `README_ZERO.md` / `docs/TGSERVER_ZERO_PROJECT_INTEGRATION.md` / #44/#50 + 関連Gateway Producer/Runtime Evidence |
| Project Integration（TGserver / webhook gateway / Vault / MCP / Tool） | `docs/PROJECT_INTEGRATION_RULES.md` |
| Git / Commit / Push / work report | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Project / Document構成 | `docs/PROJECT_TEMPLATE.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| Reusable KB / F: storage / KB bridge | `docs/KB_REUSE_DESIGN.md` |
| Log / Cache / Cleanup / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| GitHub無料枠 | `docs/GITHUB_FREE_MAX.md` |
| GitHub skill resolver | `docs/GITHUB_SKILL.md` |
| 用語 | `docs/GLOSSARY.md` |
| GitHub Project Rule Plane / executor profile | `docs/GITHUB_PROJECT_RULE_PLANE.md` + `operations/github-project-rule-plane.json` |
| server-core構造 | `docs/STRUCTURE.md` |

複合作業では必要Authorityだけ組み合わせる。

## 3. Dispatch Decision

対象Projectへ入る前に、Taskに必要な範囲で次を確定する。

```text
PURPOSE
EXPECTED_RESULT
TARGET_PROJECT
TARGET_RESPONSIBILITY
TARGET_REPOSITORY
AUTHORITY_REQUIRED
REUSE_CANDIDATES
VERIFY_PATH
APPROVAL_BOUNDARY
```

対象Project / ownerが不明なら `docs/WORKSPACE_REGISTRY.md` を読む。

既存owner / reusable assetを確認する前に新規Project / Module / Tool / Documentを作らない。

### 3.1 Project-list containment gate (mandatory for GPT CHAT / SERVER_AI / Codex / Composer)

Before authoring, approving, or executing any server workspace creation (`git worktree add`, `git clone`, copy, task-named `mkdir`, checkout, agent workspace bootstrap), first establish `OWNER_REPO`, the Registry/Host-verified `CANONICAL_PARENT_REALPATH`, the resolved `PROPOSED_DESTINATION_REALPATH`, existing CU/Branch/PR and the action's ownership.

```text
ALLOWED: existing canonical parent branch and owned nested isolation
  /home/admin1/projects/debug-ai/.worktrees/<owned-cu>/
FORBIDDEN: new derivative sibling occupying a top-level Project list entry
  /home/admin1/projects/debug-ai-<cu>/
  /home/admin1/projects/tgserver-current-<date>/
```

A nested linked Git worktree is **permitted** and must not be mistaken for a new parent Project; no additional Master approval is needed solely because an owned CU needs an isolated branch/worktree inside its parent. Another top-level independent Project requires explicit Master intent/approval. Reject sibling destinations regardless of name (including `/tmp` or other persistent alternate roots). Validate directory containment via resolved paths with a path-separator boundary, not a name prefix; reject symlink/relative escape and unknown actual parent as `TOP_LEVEL_CHILD_PROJECT_BLOCKED`. Existing registered parents like `/home/admin1/server-core` retain their own verified canonical root.

Each delegated prompt must carry the **nested allowed / sibling denied** rule, check path/branch/Git-common-dir after execution, and report `CREATED_NEW_TOP_LEVEL_SIBLING=NO`. Do not ask another worker to create a denied sibling instead. Do not change/move/delete existing orphan locations during the other CHAT's parent consolidation; keep its mutation ownership exclusive. Executor Rules [#16](https://github.com/G-ACE-inc/server-core/issues/16), [#17](https://github.com/G-ACE-inc/server-core/issues/17) and detailed Workspace [§4.1](G_ACE_WORKSPACE.md#41-canonical-parent-project-and-branchworktree-isolation-master-clarification-2026-10-09) control this gate.

### 3.2 Current/work-location preflight before new source or workspace (mandatory)

Route every new CU, Branch, worktree, Module or same-purpose reimplementation through the **existing** `docs/G_ACE_WORKSPACE.md` §4.2 handoff gate. Read the owning GitHub Project Current/Issue and verify active CU, mutation owner, existing PR/branch, exact HEAD, canonical parent and reuse candidates **before** selecting a mutation location. Missing or conflicting ownership/location means `PREFLIGHT_LOCATION_UNVERIFIED`: suspend only the unsafe creation/mutation; continue read-only research or independent authorized tasks. Never create a top-level sibling as a substitute. Before handing work to Codex/Composer, supply the checked location, owned paths, active CU and Exact Next Gate; record and read back actual branch/HEAD, dirty/stash status (or UNKNOWN), and `EXACT_NEXT_GATE` on handoff. Do not create another tracker or duplicate the Current Issue.

## 4. Target Repository Loading

対象Projectへ入った後はREADMEを入口とする。

### Level 0: Repository Entry
- README Current State
- Designへのリンク
- Project Treeへのリンク
- Design Deltaへのリンク
- completed System / Feature-bundle / Module Documentへのリンク
- run / test / verify entry

存在しないDocumentを推測で作成済み扱いしない。

### Level 1: Target Boundary
最初に読む。
- 対象Source
- Input / Output
- 直接依存
- 関連Test
- 明示された再利用候補

通常変更がLevel 1で閉じられるならそこで止める。

### Level 2: Adjacent Boundary
次の場合だけ拡張する。
- 呼出元 / 呼出先が必要
- Config / State ownerが不明
- Interface / Schema契約確認が必要
- 近接再利用候補の比較が必要

### Level 3: Reuse Unit
次の場合だけModule / Component範囲へ拡張する。
- 同じ責務の既存実装比較が必要
- Adapter / shared contract検討が必要
- 責務混在 / 循環依存の可能性がある

### Level 4: System / Repository
次の場合だけSystem / Repository全体へ拡張する。
- 複数Component / Moduleへ影響
- 局所情報で影響範囲を閉じられない
- Masterが全体監査 / 全コード確認 / 横断調査を明示

### 4.1 Project Integration Routing

TGserver / webhook gateway / Libral Vault / Project-level MCP・Tool integrationを変更または追加するときは、`docs/PROJECT_INTEGRATION_RULES.md` を必要範囲で確認する。

```text
server-core README
  -> LOAD_SCOPE
  -> PROJECT_INTEGRATION_RULES
  -> target Project README
  -> target Project authority / Source / Test
```

### Design baseline / anti-drift routing

For a source-changing CU, resolve the owning repository's canonical Design/Specification link from its Current/README before editing, fetch only relevant sections and prior Design Delta, and check proposed Source/Test against CU acceptance. Recheck at diff/PR and on scope changes using the existing `docs/G_ACE_WORKSPACE.md` §6 Design-alignment step. An inaccessible baseline is `DESIGN_BASELINE_NOT_VERIFIED`; a conflicting change is `DESIGN_DRIFT_REVIEW_REQUIRED`. Do not improvise a substitute design, claim compliance without reading, or create another design tracker. Continue independent read-only work while the affected mutation awaits resolution.

## 5. Reuse Search Order

新規Code / Module / Tool / Document作成前に必要範囲で確認する。

```text
対象Project内
  -> docs/WORKSPACE_REGISTRY.md の共有Capability
  -> Workspace内の既存共有資産
  -> AVAILABLE_VERIFIEDなKB / Tool / MCP
  -> 必要な場合だけ公式外部Authority
```

Reuse priority:

```text
そのまま利用
  -> 設定 / 引数 / 型調整
  -> 薄いAdapter
  -> 共通部分抽出
  -> 新規実装
```

Registry entryはCurrent Runtime健康状態の証明ではない。

## 6. Normal Context Exclusions

通常Contextへ入れない。
- `archive/`
- `.github/`（GitHub Task時を除く）
- `scripts/`（Script Task時を除く）
- `.git/`
- `node_modules/`
- `dist/` / `build/` / `.next/`
- logs / dumps / cache
- backups
- Secret / credential実値

Task対象の場合だけ必要Fileへ限定して読む。

## 7. Documentation Read Rule

- README = Current completed / verified entry
- Design = architecture baseline
- Design Delta = intentional difference / rationale
- Project Tree = navigation index
- System/Module Document = completed unit handoff
- Commit / PR = chronological work history

DesignとCurrent実装が違う場合、DesignをCurrentへ合わせて履歴を消さない。

## 8. Runtime / Registry Rule

READMEや `docs/WORKSPACE_REGISTRY.md` のRuntime記載はDiscovery metadata。

Current状態がTask判断に必要なら対象Provider / Docker / Endpoint / GitHub revision等をreadbackする。

未確認値をcarry-forwardしてCurrent扱いしない。

## 9. Stop Reading Condition

作業開始に必要な読込は、次を説明・確認できた時点で止める。
- purpose / expected result;
- target Project / responsibility;
- Design baseline when relevant;
- input / output;
- direct dependencies / constraints;
- reuse candidates;
- related tests / verification path;
- affected scope;
- approval boundary。

不足した場合だけ次Levelへ進む。

## 10. Router Failure Rule

Task owner、Authority、Runtime state、Secret contract等が不明な場合は推測で補完しない。

`UNKNOWN / NOT_VERIFIED / NOT_IMPLEMENTED` を維持し、必要なAuthority/readbackだけ追加取得する。
<!-- Tool-B source_reflect E2E evidence line 2026-10-10T17:25:00+09:00 -->

<!-- Tool-B source_reflect E2E evidence line 2026-10-10T17:30:00+09:00 round-2 -->
