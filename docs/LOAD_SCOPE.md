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

**Development procedure owner:** `docs/G_ACE_WORKSPACE.md` §6. Use the owning GitHub Project/CU Current and the necessary Source, design and evidence; reload changed information, not the entire active Rule #17 profile each turn. Master owns product intent and material protected-impact decisions; AI owns routine technical choices and execution. Verify against Mission and adopted design at meaningful change points; record substantive decisions in existing Notion minutes and executable state in GitHub Current only when needed for accurate continuation. Neither verification nor recording is a completion or stopping gate.

**Server execution:** the existing server-core CHAT → Actions → Gateway → Receiver → Host `host.command` path with AI-authored commands, subject to actual Issue #10 admission. Old fixed-command DebugAI routing is not a GPT CHAT fallback; `dev.job` is for isolated tests. Do not assume all repositories have deploy admission. For a genuinely necessary Master terminal handoff use `docs/MASTER_TERMINAL_COMMAND.md`.

**Efficiency:** Keep the approved Mission and design fixed; reuse verified history, choose sensible work grouping, and continue while relevant actions remain. Intermediate checks, records and reports are not independent work objectives. If this CHAT cannot execute a required step, provide the complete authorized execution instruction to the appropriate operator without inventing unnecessary detours, extra approvals, or new gates. Ownership/project containment: Workspace §4.1–§4.2; runtime/evidence: §9/§12.

### Integrated G-ACE mission routing

Treat Tool B, TGserver and other capability inspections as dependencies of the commissioned Mission, not new work objectives. Project acceptance C01–C09 is owned by `docs/GITHUB_PROJECT_RULE_PLANE.md`; authority remains #15 (integration), #40 (CHAT continuity), #10 (common Host), TGserver #50 (ZERO). Preserve each CU's mutation owner and resume the original Mission after dependency checks. Execution/blocked-step decisions follow Workspace §6; Source or CI evidence alone does not prove runtime acceptance.

### GPT CHAT work continuity

The owning work procedure is `docs/G_ACE_WORKSPACE.md` §6. Keep the approved Mission fixed; choose efficient task grouping and reuse existing evidence without introducing another checklist, report trigger or stopping boundary. For formal Master reports, follow Rule #17's Master-facing communication contract. This router adds no independent execution procedure.

GPT_CHAT拡張RuleをSERVER_AIへdefault loadしない。

README以外のserver-core Authorityを新Task開始時に一括読込しない。

同一Taskで一度確認済みの安定Authority全文は通常、変更・矛盾・情報不足が無い限り再読込しない。開発進行はWork Routine §6に一本化し、毎ターンのRule Plane全文読込を独立した前提条件としない。読み込んだ事実だけで適用PASSにせず、選択したAction・継続・終了判断へ照合する。ただし開発の各ターンでは関連するGitHub Project/IssueのCurrentと対象HEAD/PR/CI等の変化を軽量に再同期し、対象変更・新規Gate・競合時だけ必要なAuthority/Source範囲を再取得する。古い履歴・別Project・GPT CHAT拡張RuleをSERVER_AIへまとめて渡さない。

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
