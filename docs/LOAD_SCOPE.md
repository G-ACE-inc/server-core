# SERVER CORE LOAD SCOPE / COMMAND ROUTER

Version: 2026-10-17
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

このProfileのAgent LoopとNotion参照・記録はGPTアプリのチャットに限定する。サーバーAIへこのCHAT手順をロード・適用せず、委任先にNotion記録を要求しない。詳細の適用範囲はWork Routine §6を参照する。

**Development procedure owner:** `docs/G_ACE_WORKSPACE.md` §6. Use the owning GitHub Project/CU Current and the necessary Source, design and evidence; reload changed information, not the entire active Rule #17 profile each turn. Master owns product intent and material protected-impact decisions; AI owns routine technical choices and execution. Verify against Mission and adopted design at meaningful change points; record substantive decisions in existing Notion minutes and executable state in GitHub Current only when needed for accurate continuation. Neither verification nor recording is a completion or stopping gate.

**Server execution:** the existing server-core CHAT → Actions → Gateway → Receiver → Host `host.command` path with AI-authored commands, subject to actual Issue #10 admission. `dev.job` is for isolated tests. Do not assume all repositories have deploy admission. For a genuinely necessary Master terminal handoff use `docs/MASTER_TERMINAL_COMMAND.md`.

### Integrated G-ACE mission routing

Treat Tool B, TGserver and other capability inspections as dependencies of the commissioned Mission, not new work objectives. Project acceptance C01–C09 is owned by `docs/GITHUB_PROJECT_RULE_PLANE.md`; authority remains #15 (integration), #40 (CHAT continuity), #10 (common Host), TGserver #50 (ZERO). Preserve each CU's mutation owner and resume the original Mission after dependency checks. Execution/blocked-step decisions follow Workspace §6; Source or CI evidence alone does not prove runtime acceptance.

For GPT app CHAT formal Master reports, follow Rule #17's Master-facing communication contract. Its execution loop, continuation and capacity-safe handoff belong to Work Routine §6; this router adds no independent procedure. Do not apply this CHAT/Notion procedure to server AI, default-load GPT_CHAT rules into SERVER_AI or bulk-read other server-core authority at task start.

同一Taskで一度確認済みの安定Authority全文は通常、変更・矛盾・情報不足が無い限り再読込しない。GPTアプリCHATの開発進行はWork Routine §6に一本化し、毎ターンのRule Plane全文読込を独立した前提条件としない。読み込んだ事実だけで適用PASSにせず、選択したAction・継続・終了判断へ照合する。ただし開発の各ターンでは関連するGitHub Project/IssueのCurrentと対象HEAD/PR/CI等の変化を軽量に再同期し、対象変更・新規Gate・競合時だけ必要なAuthority/Source範囲を再取得する。古い履歴・別Project・GPT CHAT拡張RuleをSERVER_AIへまとめて渡さない。

対象CUが分かっている場合、全ProjectのIssue本文を列挙しない。既存GitHub connectorでは対象Currentを直接一度読む。ローカルの`gh`を利用できる場合は、既存`python3 scripts/gace_project_current_recovery.py --project-id PVT_kwHODOQFoM4BEJII --issue-url https://github.com/G-ACE-inc/server-core/issues/15 --include-body`で指定Issueだけの本文・更新時刻・ハッシュを同時取得できる（例はControl #15。実作業では所有CUの正確なURLを使う）。Project登録を全ページ照合し、未登録は`SELECTED_ISSUE_NOT_REGISTERED`として拒否する。返された本文を同じ判断のために再取得せず、更新・矛盾・実行時の独立照合が必要な場合だけ読み直す。ツールの存在や登録一致は実行権限を付与しない。通常CHATにこのCLIやHost操作を必須化しない。

復元結果の`project_status`は取得済みの既存Statusを示す。IssueがOPENでもStatusがDoneなら`PROJECT_STATUS_RECHECK_REQUIRED`として、所有Current・Project表示・自動化を確認する。ツールはStatusを自動修正せず、既存4項目の書込契約も拡張しない。Source/CIの合格だけで未完了CU全体をDoneにしない。

## 2. Command Routing

Use the single [README Task Routing table](../README.md#task-routing) to select common Authority. Combine only the rows needed for this task; do not fetch the whole table's documents.

For the integrated platform only: Tool B's common Host / isolated `dev.job` design is `docs/SERVER_CORE_DESIGN.md` §16/§16.11 and owning #10 Current; Tool A's collection→TGserver ZERO→search/restore design is §17 and `docs/PROJECT_INTEGRATION_RULES.md`, then the target TGserver `README_ZERO.md` / integration document and owning #44/#50 Current. Consult relevant Gateway/Host evidence only when that dependency is needed. DebugAI's product route is a separate authorization scope.

## 3. Dispatch Decision

Before entering a target, identify its purpose/expected result, Project/Repository/owner, responsibility, required Authority, reuse candidates (`REUSE_CANDIDATES`), verification path and approval boundary. If ownership is unknown, use `docs/WORKSPACE_REGISTRY.md`; do not create another Project/Module/Tool/Document before checking existing ownership and assets. Mission/CU/pre-dispatch detail belongs to Work Routine §6.

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

Read the target README's actual Current, Design/Tree/Delta/unit-document links and run/test entry. Do not invent missing documents.

### Level 1: Target Boundary

Read target Source, input/output, direct dependencies, relevant tests and named reuse candidates. Stop expansion if this bounds the change.

### Level 2: Adjacent Boundary

Expand only for required callers/callees, config/state ownership, interface/schema contracts or adjacent reuse comparison.

### Level 3: Reuse Unit

Expand to a module/component only to compare the same responsibility, assess an adapter/shared contract, or resolve mixed responsibility/cycles.

### Level 4: System / Repository

Expand only for cross-component impact, uncertainty that cannot be bounded locally, or Master's explicit whole-system audit.

### 4.1 Project Integration Routing

For TGserver / webhook gateway / Vault / Project-level MCP or Tool integration changes, read the relevant `docs/PROJECT_INTEGRATION_RULES.md` contract, then the target README and required Source/tests. Do not treat integration as shared capability ownership.

### Design baseline / anti-drift routing

For a source-changing CU, resolve the owning repository's canonical Design/Specification link from its Current/README before editing, fetch only relevant sections and prior Design Delta, and check proposed Source/Test against CU acceptance. Recheck at diff/PR and on scope changes using the existing `docs/G_ACE_WORKSPACE.md` §6 Design-alignment step. An inaccessible baseline is `DESIGN_BASELINE_NOT_VERIFIED`; a conflicting change is `DESIGN_DRIFT_REVIEW_REQUIRED`. Do not improvise a substitute design, claim compliance without reading, or create another design tracker. Continue independent read-only work while the affected mutation awaits resolution.

## 5. Reuse Search Order

Before new Code/Module/Tool/Document: target Project → shared discovery in `docs/WORKSPACE_REGISTRY.md` → existing Workspace assets → AVAILABLE_VERIFIED KB/Tool/MCP → official external authority only when needed. KB-specific access/lifecycle is `docs/KB_REUSE_DESIGN.md`.

Prefer unchanged reuse → configuration/arguments/types → thin adapter → shared extraction → new implementation. A Registry entry is not current runtime health or permission.

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

Use [README's document responsibility table](../README.md#documentation-contract): entry/status, architecture baseline, intentional Delta, Tree navigation, unit handoff and chronological Commit/PR history are distinct. Do not overwrite Design history to fit incidental Source.

## 8. Runtime / Registry Rule

READMEや `docs/WORKSPACE_REGISTRY.md` のRuntime記載はDiscovery metadata。

Current状態がTask判断に必要なら対象Provider / Docker / Endpoint / GitHub revision等をreadbackする。

未確認値をcarry-forwardしてCurrent扱いしない。

## 9. Stop Reading Condition

Stop expanding context when purpose/outcome, target owner/responsibility, relevant Design, input/output, direct dependencies/constraints, reuse, tests, affected scope and approval boundary are understood. Read the next level only for a concrete missing fact. This is a reading limit, not a development stop.

## 10. Router Failure Rule

Task owner、Authority、Runtime state、Secret contract等が不明な場合は推測で補完しない。

`UNKNOWN / NOT_VERIFIED / NOT_IMPLEMENTED` を維持し、必要なAuthority/readbackだけ追加取得する。
