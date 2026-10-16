# G-ACE WORKSPACE

Version: 2026-09-30
Role: G-ACE Workspaceでserver-core司令室を必ず起点にして作業するための正規運用契約。

## 1. Purpose

標準Workspace `/home/admin1/workspace/G-ACE.code-workspace` では、AI / Developerはserver-coreを共通Command Centerとして使用する。

server-coreはTask routing、共通Authority、shared capability discovery、GitHub work history、operations boundaryを管理する。Project固有Design / Source / Test / Runtime logicは各Projectが所有する。

## 2. Mandatory Entry

Workspace作業は必ず次から開始する。

```text
/home/admin1/server-core/README.md
  -> /home/admin1/server-core/docs/LOAD_SCOPE.md
  -> 今回必要なserver-core Authorityだけ
  -> 対象Project README
  -> 対象Projectの必要Authority / Source / Testだけ
```

server-core全正本の一括読込は禁止する。

## 3. Command-Center Dispatch

Taskを受けたAI / Developerは次を決める。

```text
PURPOSE
TARGET_PROJECT
TARGET_RESPONSIBILITY
REQUIRED_SERVER_CORE_AUTHORITY
REQUIRED_PROJECT_AUTHORITY
REUSE_CANDIDATES
VERIFY_PATH
APPROVAL_BOUNDARY
```

対象Projectや責務が不明な場合は `docs/WORKSPACE_REGISTRY.md` でownerを確認する。

既存ownerを確認せず新規Project / Module / Toolを作らない。

## 4. Workspace Folders

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

通常Workspace Contextへ含めない:
- `/home/admin1/workspace`
- `/home/admin1/kb`
- `/home/admin1/logs`
- `/home/admin1/backups`
- archive / build / dist / node_modules / cache / dumps

Task対象になった場合だけ必要範囲を開く。

## 4.1 Canonical parent Project and branch/worktree isolation (Master clarification 2026-10-09)

**The only prohibited proliferation is a derivative Project directory at the same level as a registered parent Project.** Do not mistake Git branches or an isolated worktree *inside* its parent directory for a new Project. Rule Plane [SERVER AI #16](https://github.com/G-ACE-inc/server-core/issues/16) and [GPT CHAT #17](https://github.com/G-ACE-inc/server-core/issues/17) are the authoritative executor-specific requirements.

```text
PROJECT_LIST_ROOT=/home/admin1/projects
CANONICAL_PARENT=/home/admin1/projects/<existing-registered-project>
ALLOWED_IN_PARENT=/home/admin1/projects/<existing-registered-project>/.worktrees/<change-unit>
DENIED_AS_SIBLING=/home/admin1/projects/<existing-registered-project>-fix
DENIED_AS_SIBLING=/home/admin1/projects/<existing-registered-project>-current-YYYYMMDD
DENIED_AS_SIBLING=/home/admin1/projects/<existing-registered-project>-prNN
NEW_TOP_LEVEL_PARENT_PROJECT=MASTER_EXPLICIT_PROJECT_APPROVAL_ONLY
```

For existing registered owners elsewhere (e.g. `/home/admin1/server-core`), the *verified actual existing canonical parent* is authoritative; do not assume every Project is under `/home/admin1/projects`. Distinct already registered repositories in the top-level list are independent parents, not derivatives.

- **Allowed without per-branch Master approval:** a normal Git branch in the existing parent; an owned linked `git worktree` nested *strictly inside* the parent for an independent CU, concurrent agent or dirty-checkout isolation; routine temporary files inside that parent. Use an ignored/excluded dedicated folder such as `.worktrees/` so worktrees are not accidentally staged or packaged by the primary checkout. Record branch/CU, owner, common Git directory, path and cleanup owner. Reuse an already owned worktree first.
- **Forbidden by default:** a sibling top-level `*-fix`, `*-current`, `*-research`, `*-forensic`, `*-evidence`, `*-prNN`, task-named `debug-ai-*` etc. checkout, worktree, clone, directory copy or `git init` next to the parent. Also forbidden: moving that same persistent duplicate to another top-level scratch folder as a workaround. Filename similarity alone is not the criterion; actual verified parent/ownership/destination determines the decision.
- Before executing any workspace-creating command, inspect canonical parent and actual resolved destination (not string prefix alone); verify containment using real path + separator, with symlink and `..` escape rejected. On conflict, choose parent-local branch/worktree or wait for owner; NEVER silently make a sibling. An unknown parent/path blocks *only the creation*, using `TOP_LEVEL_CHILD_PROJECT_BLOCKED`.
- **CHAT -> SERVER AI -> Codex / Composer delegation:** every prompt must state both permitted nested isolation and forbidden sibling placement, plus require `OWNER_REPO`, `CANONICAL_PARENT_REALPATH`, `ACTUAL_WORKTREE_REALPATH`, `GIT_COMMON_DIR`, `BRANCH/HEAD`, `CREATED_NEW_TOP_LEVEL_SIBLING=NO` readback. Do not pass an older generic "all worktrees forbidden" instruction.
- The other CHAT currently owns reconciliation of existing stray children. This rule is for prevention and does not authorize automatic deletion, move, rename or consolidation. Existing Project/source/Host approval and execution boundaries remain intact.

## 4.2 Mandatory work location and reuse handoff gate (Master decision 2026-10-09)

This is an extension of **the existing** Work Routine and GitHub Project Current, not a new registry, workflow, task tracker, or AI rule plane. The owning Current Issue is the SINGLE mutable record for the active work location and next gate.

**Before any new branch/worktree/module/feature/source mutation**, GPT CHAT and delegated executors must resolve and verify:

```text
OWNER_PROJECT / OWNER_REPOSITORY / CANONICAL_PARENT_REALPATH
CURRENT_ISSUE / MISSION / CHANGE_UNIT / MUTATION_OWNER
REUSE_CANDIDATES: active CU + Issue/PR + branch + existing source/module
WORK_BRANCH / WORKTREE_PATH (if any) / EXACT_HEAD / PR
OWNED_PATHS / DIRTY_STATE (UNKNOWN if Host was not read) / EXACT_NEXT_GATE
```

1. Obtain the owning Project Current and its checkpoints, then search its existing Branch/PR/CU for matching purpose and file ownership. Compare direct GitHub HEAD/PR and, when actually accessible, Host canonical root/worktree/status. A Project Current record does not establish uncommitted Host state.
2. If the same work exists, **resume the verified existing location** or hand off to its current owner. Do not copy sources, create a sibling Project, silently take over another CU, or call a new branch a fresh Project. A separately justified owned CU may use a new nested worktree strictly inside the verified canonical parent. Existing parent-local worktrees remain allowed.
3. A missing/contradictory OWNER, CURRENT_ISSUE, canonical parent, active CU or competing file owner is **PREFLIGHT_LOCATION_UNVERIFIED**: deny only creation or mutation whose safe location/ownership cannot be established. Read-only discovery and other independently authorized work may continue. Do not invent HEAD, path or PR.
4. On commit/push, update the SAME owning Current Issue/checkpoint with actual branch, exact remote HEAD, PR and changed owned paths. At pause/handoff, record Host dirty/stash/rebase status when verified (otherwise UNKNOWN), open blockers, evidence URLs and EXACT_NEXT_GATE. The next CHAT must rehydrate and cross-check this checkpoint, not restart the implementation.
5. The existing initializer project-selection gate, shell Hook and authorized Host admission should reject provably invalid destinations or scopes; GitHub SHA compare-and-swap/CI catches stale Source. These mechanisms are **not** universal: Cursor Hook does not intercept Codex/SSH; semantic duplicate design cannot be proved by filename matching; GitHub Issue prose is not a Host credential. New universal denial claims require actual negative tests on each covered executor.

Mandatory operational distinction: `PREFLIGHT=PASS` only when the checked Current and source/Host evidence support it. `HANDOFF_RECORDED` is not `NEW_SESSION_RULE_LOADED`; `SOURCE_CI_PASS` is not `HOST_GUARD_ACTIVE`. No automatic cleanup or merger of existing sibling directories owned by other CHATs.

## 5. Project Entry

対象ProjectではREADMEを入口にする。

READMEから、存在する場合は次へ直接到達できる状態を標準とする。
- Design
- Project Tree
- Design Delta
- completed System / Feature-bundle / Module documents
- run / test / verify entry points

対象Source、直接依存、関連Testから開始し、必要時だけ `docs/LOAD_SCOPE.md` のLevelに従ってContextを広げる。

## 6. Development Routine

### Execution responsibility (common boundary; profile detail stays in its owner)

This G-ACE workspace serves one **nontechnical Master**, not a generic team approval workflow. **Master owns product purpose, priority, user-visible behavior and genuine protected-impact decisions; routine technical implementation choices are AI-owned.** GPT CHAT development progression is owned solely by this Work Routine §6; [GPT CHAT Rule #17](https://github.com/G-ACE-inc/server-core/issues/17) is the active GPT CHAT profile for decision responsibilities, not a second development runbook. SERVER_AI's minimal executor and tool-routing profile has one owner: [SERVER_AI Rule #16](https://github.com/G-ACE-inc/server-core/issues/16). Shared safety and exact authorization remain in `SERVER_CORE_PROTOCOL.md`; GitHub Project Current owns each changing Mission/CU.

GPT CHAT leads technical work it can actually perform, delegates only a bounded missing step, and independently verifies results. SERVER_AI / Composer / Codex execute only their assigned CU; DebugAI, TGserver, Actions and Host remain bounded tools. Do not ask Master to select commands, SHAs, debugging or routine CI fixes. An approved reversible technical operation must use existing Host admission without invented additional human gates; never fake an approval receipt or bypass protected effects. Finding a missing tool/log/Host route does not authorize starting another Project or platform.

### Purpose-led verification, durable records and communication (distinct responsibilities)

**Verification keeps development aligned:** At a new task/CU, a material change of purpose/design/scope, a conflicting instruction, and before consequential mutations, compare the proposed work with the owning GitHub Current, adopted design and Master's latest intent. Do not repeat unchanged checks for every command. Correct drift before it spreads; do not create a separate audit project or stop after a check.

**Records preserve necessary decisions and resumability:** GitHub Current records meaningful changes to Mission/CU, owner, actual completed acceptance, exact Source/CI/Host evidence, risks and the next unfinished action at material checkpoints or handoff. Notion records substantive discussion, decisions, reasons, design changes and important unresolved conflicts in the existing owning minutes. Routine commands, repetitive investigations, each failed test, intermediate explanations and each CHAT turn do **not** independently require an additional Notion entry. Preserve enough actual evidence to avoid drift and accurately resume; batch related material into the existing record, without duplicating GitHub Current or fabricating write success. If a necessary record write fails, retain the content and continue independent authorized development; do not call the write failure completion.

**Reporting communicates to Master:** A user-visible status or formal report is separate from verification, records and development completion. Do not infer any reporting schedule, required report per block, or stop condition from a recording checkpoint. Follow Master's specific request and Rule #17 communication contract when a formal report is actually warranted. Neither making a record nor sending a report completes or suspends an unfinished Mission. End conditions are owned by the existing continuation rule below, not this section.

**Visible in-flight progress (without exposing private reasoning):** During a substantial continuous CU, give Master concise, factual, nonterminal work-in-progress notes at meaningful transitions: initial actual action/target; confirmed new evidence or decision change; failure with the narrowed cause and corrective next action; and a genuinely lengthy interval without other visible progress. Identify the existing repo/CU and exact Run/PR/request ID only when useful. Explicitly distinguish PLANNED, EXECUTING, OBSERVED and UNKNOWN. Show *why the next operation follows the result*, not a repetitive stream of tool names, "Actions ran", or a fabricated internal Thinking trace. The notes do not pause work, trigger authorization, require Master response, or replace actual evidence. Do not expose raw confidential logs, credentials or hidden reasoning. A client may not be able to display updates *during* a single blocking Tool call; never promise guaranteed real-time UI or instant interruption.

### Default execution ownership and mandatory continuation (Master current)

**Standard route for this Master-directed development:** GPT CHAT designs, implements and verifies in the owning GitHub repository and its available CHAT-local working environment; commits/pushes and checks CI itself. For Server reflection, CHAT **first uses the existing server-core-owned common terminal** (the common Host entrypoint and AI-authored shell command via admitted `host.command`; `dev.job` is reserved for isolated development/tests) and independently reads back the exact Host result. A Master terminal command is a last resort **only when the actual existing direct route is unavailable or explicitly denies the required authorized operation**, after recording the precise blocker and exhausting independently executable work. Do not turn a stale per-repo branch registration or missing Deploy admission into a claim that the entire terminal is unavailable; treat that as an owning Issue #10 registration/execution defect. Master is not a routine copy/paste operator. CHAT then analyzes actual container/Host logs, repairs repository Source and repeats tests and reflection until the owned acceptance is reached. **Master is not the investigator, debugger, command author or technical decision-maker.** Do not treat a Source commit, CI success, a report, or handing off a command as completion.

**Executor selection:** (1) GPT CHAT direct repository/local work first, including GitHub Commit/CI and evidence analysis; (2) existing verified authorized direct runtime transport when it is truly available and appropriate, otherwise a complete Master terminal command for bounded Server execution; (3) Server AI / Cursor Composer only when CHAT cannot do the task or actual delegation is materially more efficient. **Default Server AI usage is zero**; do not impose a fixed multi-agent chain, transfer CHAT-owned work wholesale, or create a sibling Project. This is execution-routing policy, not a grant to bypass Host/Secret/protected-effect admission.

**Evidence-efficient Tool execution (preserve the Agent Loop):** Before another Tool call, identify the *new* fact or effect needed and reuse the exact in-turn Issue/PR/commit SHA, Run ID, returned data and correlated Host result already obtained. A Run's existence, state and conclusion are separate evidence: once its ID is known, read that Run directly; inspect only failed/relevant Jobs and bounded log ranges, not repeated global scans or full Issue histories. Re-read rules/Source/Current when revisions, scope, ownership or material facts change; unchanged sections do not need repeated full fetching within the same CU. Batch independent reads when safe and prefer one coherent Source diff and targeted CI verification to a succession of cosmetic commits/rapid status polls. One commit legitimately spawning multiple different Workflow Runs is not evidence of duplicate tool calls. When a Tool reports rate limits, timeout or transport failure, retain the original request/Run correlation and inspect that outcome before attempting any resubmission; never blindly create new Host requests or rerun successful work. Do not set a numerical Tool-call quota, skip required checks or reduce genuine multi-repository coverage: optimize **useful progress per call**, not the total number of calls alone.

**Failure is not a work boundary (no block-as-stop):** A section, block, step, test run, command, PR, CI check, documentation update or report is an internal work grouping, never an independent permission to stop. A failed test means diagnose its evidence, repair the cause and rerun relevant verification within the same Mission/CU; repeat while authorized feasible work remains. A passed test only closes that test, not the Mission. Do not conclude `TEST_FAILED -> REPORT -> STOP`, `ONE_BLOCK_DONE -> REPORT -> STOP`, or `NEXT -> WAIT_FOR_MASTER`. After a failure, inspect the real error and affected design/source/dependency/runtime, choose the next feasible corrective action and execute it without soliciting routine permission. When the specific path is unavailable, work on other in-scope branches and return to the blocked path when possible. End only on the user's explicit stop/pause, proven acceptance of the commissioned outcome, an actual protected Master decision that prevents all further in-scope work, or exhaustion of all safe executable avenues in the current environment; give exact evidence and a usable continuation artifact for genuine tool/environment limits. Do not claim that prose can prevent model or platform execution limits. This is part of §6's existing iterate loop, not a new gate or a fixed retry count.

**Mandatory nonterminal action rule:** Before sending any final answer, check whether the same CU has executable work remaining. If yes, continue the next action rather than converting a progress explanation or five-part report into STOP. When only external execution can advance the CU, the response must contain **the finished, immediately usable next artifact**: an exact syntax-checked copy/paste command under `docs/MASTER_TERMINAL_COMMAND.md`, or a bounded paste-ready Server AI instruction if that is the justified route. Supply target terminal/agent, verified repo/branch/HEAD/operation boundaries, expected evidence and exact return format. Do not merely say “NEXT”, “ask Composer”, “run on Server”, or promise to draft instructions later. If required preconditions cannot be verified, never invent paths or claim syntax validation; continue safe work and provide the precise safe handoff that can actually be supported.

**Server incident loop:** CHAT chooses the minimal Docker/Compose-aware diagnostic command, Master executes only if direct authorized readback is unavailable, CHAT diagnoses the returned unedited evidence and performs Source-level fixes, tests/CI and subsequent bounded Server verification. Runtime truth remains distinct from Source/CI. Stop without a command/instruction only for an actual protected Master decision or proven absence of any safe route, after exhausting independent authorized work; state the concrete blocker.

### Master approval and delegated technical authority (single shared contract)

- **Master decides intent and protected impact:** product purpose, requirements, priorities, user-visible behavior, material scope/architecture changes, new or materially increased spend/provider/model use, irreversible protected data changes, substantial security/credential or permission expansion, external/customer/public exposure, and explicit canonical Master-only gates. Present actual outcome, user impact, cost/risk, reversibility and the recommended option; never ask Master to make an implementation choice.
- **AI decides and executes routine technical work inside the approved Mission/CU:** investigation, design-consistent implementation, Branch/owned nested Worktree choice, Commit/Push/PR, focused tests/CI repair, debugging, evidence readback and authorized reversible Host reflection/restart/rollback. These operation names do not independently create new Master approval gates. Do not ask repeatedly for permission already delegated.
- **Decision delegation is not execution authorization:** apply exact GitHub/Host Registry, owner, branch, SHA, changed-path, effect, credential/Secret and runtime checks through the existing authorized mechanism. Never invent a receipt, forge an approval flag or widen Host permission based on CHAT text; a new independent top-level Project still needs explicit Master project approval under §4.1.
- **Blocked action does not stop the Mission:** identify the exact denied action, responsible authorized writer, smallest safe correction and readback; keep other owned Source/Test/CI work moving. If the executor truly cannot take another action, give Master one complete copy-ready command or bounded Composer instruction using the existing command contract, rather than an open-ended technical question.
- **No silent intent changes:** if Source/Design work would alter Master-owned functionality or cross a protected-impact boundary, prepare the evidence and alternatives before seeking the specific intent/impact decision. Suspend only that action, not independent authorized work. Consent to discuss, a progress response or a GitHub comment is not a Runtime credential.

Before executing an AI-authored server command, apply the lightweight AI-only self-check in `docs/COMMAND_ROUTINE.md`; it never requests routine Master confirmation or suspends the development CU.

### Executable direction when this CHAT cannot perform an action

If an authorized action truly cannot be executed here, identify the exact blocker and choose the existing appropriate executor; issue a **complete, immediately usable task instruction** with owning Mission/CU, verified target, intended change, test and evidence to return. Provide a Master terminal command only if direct execution is unavailable and that relay is genuinely needed; follow `docs/MASTER_TERMINAL_COMMAND.md`. Do not ask Master for routine technical approvals, invent access, start unrelated workaround work, or treat the instruction as Mission completion. Record the handoff and continue other relevant executable work where useful. Actual protected-impact decisions and Host authorization remain in force.

### Mission / Change Unit pre-dispatch (same Current for GPT CHAT and SERVER_AI)

The single mutable authority for a task's mission is **GitHub Project #1 Current plus the owning Project/CU Current**. This document owns the stable Work Routine, **not** another copy of the task's changing status. Use the selected executor profile (#17 for GPT CHAT; #16 for SERVER_AI), never both as default context.

Before each new Change Unit, delegated agent dispatch or source/Host mutation, restore from the owning Current and exact Source/Evidence:

```text
MISSION                 = approved outcome, not the newly discovered obstacle
IN_SCOPE / OUT_OF_SCOPE = task boundary, including which other CHAT owns adjacent work
CURRENT_CHANGE_UNIT     = exact already owned CU
MUTATION_OWNER          = single writer responsible for that CU
ACCEPTANCE              = observed result needed to finish the mission
EXACT_NEXT_GATE         = earliest uncompleted gate, not a guessed new project
TARGET_REPO / BRANCH    = verified owning checkout and revision
CURRENT_REFERENCE       = canonical Issue/Project item and readback timestamp/revision
```

Use existing Project fields (`Wave`, `Gate`, `Change Unit`, `Mutation Owner`) and the owning canonical Issue for the other mission fields. **Do not invent GitHub Project fields** or treat another CHAT's checkpoint as this CU's authorization. Compare the **proposed action's files, owner, destination and effects** with Mission, Scope, Next Gate, permissions and existing verified capabilities. When they match, proceed through the existing Routine without further technical approval relay to Master. When they differ, **block only that mismatched mutation/delegation**, record `SCOPE_DRIFT_BLOCKED`, retain the original Mission, and continue independent read-only or in-scope work. Discovering a tool/log/Host defect is not authorization to start a new project or transport.

A fresh chat or agent rehydrates the same Current before its first mutation; chat memory, old prompts, README snapshots and previous CI success are not replacement Current. After executing, compare actual changed files/effects, Source/CI/Runtime evidence and acceptance to the original Mission; record the exact next unfinished gate. The real executable dispatch path must eventually verify this comparison: a documentation instruction or CI keyword test **alone is not mechanical runtime enforcement**.

```text
server-core command center
  -> target Project README
  -> required Design / Tree / Delta / System Document
  -> repository / branch / HEAD / status
  -> Source / direct dependency / tests
  -> reuse check
  -> implementation / debug
  -> diff
  -> verification
  -> documentation gate
  -> GitHub commit as work report
  -> push / remote readback
  -> PR / CI when required
  -> approval boundary / verified Host admission
  -> existing server-core CHAT -> GitHub Actions -> Gateway -> Receiver -> Host `host.command` (when Host work is needed and admitted)
  -> exact Actions run/job/request ID and actual Host result readback
  -> restore the existing health-only target after bounded requests
  -> record Source / CI / Deploy / Runtime separately
```

### Rule versus System — enforcement allocation

A rule describing a **judgment** remains in its owning profile or this single shared routine. A rule describing an **objective machine predicate** must be enforced at the existing component that owns the corresponding effect. Do not create a parallel router, workflow, MCP or control-plane schema merely to relocate prose.

| Required outcome | Policy/decision owner | Existing machine enforcement location | Current verification boundary |
|---|---|---|---|
| Preserve Master Mission, Scope and acceptance across CHAT/agents | Project #1 + owning Current Issue; #17 orchestration | Existing pre-dispatch admission of the owning executor/Host, after an exact Current read | **NOT_VERIFIED** for a real Mission/CU mismatch denial across all routes; static routine test is not admission |
| One CU, one mutation writer; exact Repository/Branch/HEAD/effect | Owning Current + shared Work Routine | Existing bounded Host/DebugAI admission and existing GitHub Project Control transport | The latter validates only Wave, Gate, Change Unit and Mutation Owner; it does **not** validate the full Mission |
| Protect actual GitHub/Host/Runtime authorization and approval | `SERVER_CORE_PROTOCOL.md` and canonical registry | Existing approved execution/receipt guards and CI; never trust user-supplied `human_approved` | Enrollment and real runtime evidence are repository-specific, not universal |
| Reject unregistered derivative sibling while allowing nested worktrees and registered independent parents | Shared §4.1 and `LOAD_SCOPE.md` | Existing workspace initializer and owning Host filesystem admission | Current `scripts/init-dev-workspace.sh --project` calls the existing `scripts/init_dev_workspace_project_gate.py` first; that gate requires an existing registered canonical Git checkout and rejects unregistered names, missing paths, aliases/symlinks and mismatched origins before initialization. **Source-level selector checks VERIFIED; actual installed Host coverage and other workspace creation entry points NOT_VERIFIED.** Do not repeat the already-implemented initializer fix or infer universal containment from this selector |
| Verify adapter/profile version and prevent stale duplicate rule injection | #16/#17 + Rule Plane owner | Existing `server-core-guard` static checks, then actual Cursor/Codex/Copilot session loader | Source checks cannot prove live active rules; per-consumer runtime readback required |
| Report Source/CI/Deploy/Runtime truthfully and avoid premature DONE | Owning Current + shared completion contract | Existing exact SHA CI/readback and Host runtime status; persist evidence in canonical Issue | Any missing layer remains UNKNOWN/NOT_VERIFIED, never inferred from a green CI |
| Prevent unsafe file/Secret/destructive operations | `SERVER_CORE_PROTOCOL.md`, shared Secret/Registry contracts | Existing effect/path/permission admission at the operation boundary | Never reduce the current protected operation set or expand permanent delegation |

**Revised shared routine (retains all necessary gates, removes duplicated decision loops):**

```text
1. REHYDRATE: manifest/profile -> owning GitHub Current -> exact repo/branch/HEAD/owner.
2. DISPATCH PREFLIGHT: Mission, In/Out Scope, CU, writer, acceptance, next gate; check real effect admission.
3. EXECUTE: reuse first; GPT CHAT handles accessible work, bounded Server AI/Composer/Codex only for a needed owned action.
4. VERIFY: diff/effects -> focused tests -> exact-SHA CI -> Host/Runtime only when applicable and authorized.
5. RECORD: commit/PR and canonical Current evidence, outstanding gates, readback; never convert UNKNOWN to PASS.
6. ITERATE: correct the same CU until its acceptance or an actual protected/ownership blocker; avoid a second work routine.
```

**Implementation boundary:** prefer improving the existing guard at the owning command/dispatch point with negative tests (`WRONG_MISSION_OR_CU` deny, unrelated path/effect deny, symlink escape deny, approved nested worktree allow, separately registered new independent parent allow). Avoid a schema expansion of the four GitHub Project fields before real registration, and do not modify PR36/#37's active Host route under this governance CU. No removal of old policy copies before all identified consumers have actual loading/compatibility evidence. An unknown effective loader or Host ownership blocks that specific machine mutation, not independent documentation or CI work.

### Design-alignment checks within the existing Work Routine

Before implementation, identify the **owning Project's actual Design/Specification baseline** from its Current/README links and fetch the relevant section, plus Design Delta and prior decisions when applicable. Record the document ID/path/revision and the design requirements affected by this CU in the existing Current checkpoint; a title or a stale summary is not evidence of reading the design. Avoid full-document rereads when the unchanged section has already been verified.

At the initial diff, before PR/merge, and whenever the work changes behavior or scope, compare changed Source/Tests with those identified design requirements and the Current CU acceptance criteria. If baseline cannot be read, report `DESIGN_BASELINE_NOT_VERIFIED`; if implementation diverges, report `DESIGN_DRIFT_REVIEW_REQUIRED` with exact design section, code paths and proposed disposition. Suspend only design-changing mutation whose authorization is unresolved. Do not rewrite design to match incidental code, override Master-owned intent or fabricate conformance. A legitimate correction must be recorded at the owning Design/Current authority before resuming.



#### Per-turn rule entry and design-first classification (existing Work Routine §6)

At a new task/CU, and whenever material Current/Source state changes, read the owning GitHub Project Current and required exact Source/Design. Work Routine §6 is the sole CHAT development procedure; avoid repeat-loading full Rule Plane #17 or separate per-turn START/STOP checklists. SERVER_AI retains any profile-specific minimal execution bootstrap required at its actual entry.  Compare fixed `PROJECT_PURPOSE_CANONICAL`, adopted Design, owning CU acceptance and the intended diff. Classify design state as `DESIGN_VERIFIED`, `DESIGN_NOT_FOUND`, `DESIGN_NOT_VERIFIED`, `DESIGN_DRIFT`, or `DESIGN_NOT_APPLICABLE`; distinguish `ADOPTED_MAIN` from `PROPOSED_PR` using existing README/Current/PR evidence only (no new Project fields). Block only the affected design-changing mutation when design is absent; report concrete missing decisions to Master without inventing design. Treat inaccessible readback as `DESIGN_NOT_VERIFIED` (UNKNOWN), never as proven absence. Do not treat an unmerged design PR as adopted baseline for product-intent changes. Routine fixes fully inside an adopted design may proceed without a new design PR or per-turn branch when scope stays aligned.

Existing machine effect-admission checks remain where they actually execute. Their receipts do **not** control ordinary ChatGPT response submission and must not be treated as a second CHAT development procedure.

This is a **readback/review step of existing Work Routine**, not a second design authority or an automatic semantic-code equivalence assertion. Targeted CI may enforce evidence fields when actually available, but cannot prove semantic design alignment from prose alone.

## 7. Documentation Gate

作業終了前に必ず判定する。

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Requiredなのに未更新ならDocumentation Completeではない。

DesignをCurrent実装へ合わせて履歴が消える形で上書きしない。

## 8. GitHub Work History

GitHub commit / PRは実作業履歴の正本。

Commitは必要に応じて目的、主要変更、影響範囲、検証、Document更新、残作業を後から追えるWork Reportにする。

Authority: `docs/AUTO_COMMIT.md`。

次を別状態として扱う。

```text
SOURCE
TEST
COMMIT
PUSH
REMOTE_READBACK
PR
CI
MERGE
DEPLOY
RUNTIME
PRODUCTION
```

## 9. Shared MCP / Tool / DebugAI

共有Capabilityの発見入口は `docs/WORKSPACE_REGISTRY.md`。

server-coreが管理するのは接続契約・owner・permission boundary・availability stateであり、Capability本体ではない。

`.cursor/mcp.json` 等の実設定とRegistry文書を分離する。文書記載だけでMCP利用可能とは扱わない。

DebugAIは独立Project/runtime。Source mainへのMCP実装反映とWorkspace Live登録/Runtime verificationは別状態として扱う。


### 共通Terminal

コマンド作成ルールは `docs/COMMAND_ROUTINE.md` と `docs/MASTER_TERMINAL_COMMAND.md` の二つのみ。共通経路の実行認証・権限境界は既存実装に従う。

## 10. Project Integration

ProjectへTGserver / webhook gateway / Libral Vault / MCP / Toolを導入するときは `docs/PROJECT_INTEGRATION_RULES.md` を確認する。TGserver / webhook gatewayはProject Integration、Libral VaultはShared Capability + Project利用契約として扱う。

## 10.1 Shared Secrets

Secret / Token実値を各Projectへ複製しない。

共有契約は `docs/WORKSPACE_SHARED_SECRETS.md`、発見入口は `docs/WORKSPACE_REGISTRY.md`。

ProjectはShared Secretが必要な場合、既存Contractを確認してBroker経由で利用する。既存Contractが無ければ勝手なtoken copy/helperを作らない。

## 11. Reusable Development KB

再利用開発KBのTarget data storageはMaster PC `F:` 1TB。

server-coreはAccess / Registration / Lifecycle / Safety Contractを持ち、data本体は持たない。

VPS / Workspace AIからPC filesystemを直接読める前提は禁止。実装・検証済みAPI/MCP等のbridgeを使う。

Authority: `docs/KB_REUSE_DESIGN.md`。

## 12. Server / Runtime

本番常駐・サーバー側のアプリケーション実行環境は Docker / Docker Compose を原則とする。**Node.js、Python等のアプリケーションランタイム、依存パッケージ、プロセスは対象Projectのコンテナ内で運用する。** サーバーHostへ Node.js/Python や各Projectの依存ライブラリを直接インストール・更新したり、Hostでアプリを常駐起動したりする手順をデフォルトで選ばない。

開発・調査・テスト・修正・反映時は、対象Projectの既存 Compose 定義、サービス名、Image、コンテナ内作業ディレクトリ、Volume と認可された実行経路を先に確認し、既存コンテナ／イメージの範囲で操作する。新しい Docker Compose 構成、Host ランタイム、Port公開、永続Volume操作を勝手に作らない。Host側で必要となる Docker Engine/Compose・systemd・Gateway・許可済みHost補助処理などの管理はアプリ実行と区別し、既存の設計・権限・保護操作境界に従う。

Node/Python のコマンドをMasterへ提示する場合、Host直実行を想定せず、実測した対象コンテナと既存認可に基づく実行経路を使用し、`docs/MASTER_TERMINAL_COMMAND.md` を厳守する。例外的なHost直接実行が必要なら、実在する正式な運用契約・理由・影響を確認し、推測で例外を作らない。コンテナ内での実行成功と本番反映・Host状態は分けて検証する。

ServerはRuntime/Processing環境であり、Project Source履歴・Design・Documentの正本をServerだけに置かない。

Deployはconfirmed GitHub revisionを起点にし、対象Project/共通Runbookと実際のHost認可に従う。Master判断が必要なのは現行の保護対象に該当する場合だけであり、通常の反映に新たな承認手順を追加しない。

Authority: `docs/DEPLOY_RUNBOOK.md`。

## 13. Logs / Cache / Cleanup / Backup

Authority: `docs/STORAGE_LIFECYCLE.md`。

Common boundary:
- Telegram: owning Project contractで定義されたdurable raw-log authority
- Meilisearch: rebuildable search index
- Redis: dedup / hot cache
- `/home/admin1/logs`: temporary operational disk state
- `/home/admin1/backups`: backup area; generic cleanup対象ではない
- VPS: processing/runtime environment

未送信、retry、recovery、unknown ownership、active/persistent volumeをgeneric auto-deleteしない。

## 14. Normal Context Exclusions

通常検索・Context・watcherから原則除外:
- `.git`
- `.github`（GitHub Task時を除く）
- `.tgs-state`
- `archive`
- `backups`
- `build`
- `coverage`
- `dist`
- `logs`
- `node_modules`
- cache / dumps

## 15. Runtime Readback Rule

README / Registry / historical reportをCurrent Runtimeの代用にしない。

Container / Port / Domain / Provider / Deploy状態がTask判断に必要なら、対象Provider / Docker / Endpoint / Repositoryを実readbackする。

未確認は `UNKNOWN / NOT_VERIFIED / NOT_EXECUTED` を維持する。

## 16. Completion Rule

Workspace Taskが完了と言えるのは、Taskに必要な範囲で次が閉じた場合だけ。
- correct Project/authority routing;
- implementation or requested work;
- required verification;
- Documentation Gate;
- GitHub work history;
- required remote/CI/runtime evidence;
- approval boundary compliance。

司令室の役割は「何でも実装すること」ではなく、**Workspace全体の作業を正しいowner・正しいAuthority・正しいEvidenceへ導くこと**である。