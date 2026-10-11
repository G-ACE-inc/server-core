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

This G-ACE workspace serves one **nontechnical Master**, not a generic team approval workflow. **Master owns product purpose, priority, user-visible behavior and genuine protected-impact decisions; routine technical implementation choices are AI-owned.** GPT CHAT's complete orchestration, included-capacity/cost routing and delegation instructions have one owner: [GPT CHAT Rule #17](https://github.com/G-ACE-inc/server-core/issues/17). SERVER_AI's minimal executor and tool-routing profile has one owner: [SERVER_AI Rule #16](https://github.com/G-ACE-inc/server-core/issues/16). Shared safety and exact authorization remain in `SERVER_CORE_PROTOCOL.md`; GitHub Project Current owns each changing Mission/CU.

GPT CHAT leads technical work it can actually perform, delegates only a bounded missing step, and independently verifies results. SERVER_AI / Composer / Codex execute only their assigned CU; DebugAI, TGserver, Actions and Host remain bounded tools. Do not ask Master to select commands, SHAs, debugging or routine CI fixes. An approved reversible technical operation must use existing Host admission without invented additional human gates; never fake an approval receipt or bypass protected effects. Finding a missing tool/log/Host route does not authorize starting another Project or platform.

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
  -> existing GitHub Actions -> authenticated DebugAI bounded Server Command / admitted GitOps (when Host work is needed)
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
| Reject unregistered derivative sibling while allowing nested worktrees and registered independent parents | Shared §4.1 and `LOAD_SCOPE.md` | Existing workspace initializer and owning Host filesystem admission | Existing `init-dev-workspace.sh --project` still creates an unverified top-level directory; mechanical coverage **NOT_VERIFIED** |
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

At **every development turn** (including consecutive turns in the same CU), re-fetch the fresh main `operations/github-project-rule-plane.json`, read the applicable canonical Rule Plane (#17 for GPT CHAT / Work orchestrator; #16 for SERVER_AI / Composer / Codex), and retrieve owning Project Current before choosing an action. Compare fixed `PROJECT_PURPOSE_CANONICAL`, adopted Design, owning CU acceptance and the intended diff. Classify design state as `DESIGN_VERIFIED`, `DESIGN_NOT_FOUND`, `DESIGN_NOT_VERIFIED`, `DESIGN_DRIFT`, or `DESIGN_NOT_APPLICABLE`; distinguish `ADOPTED_MAIN` from `PROPOSED_PR` using existing README/Current/PR evidence only (no new Project fields). Block only the affected design-changing mutation when design is absent; report concrete missing decisions to Master without inventing design. Treat inaccessible readback as `DESIGN_NOT_VERIFIED` (UNKNOWN), never as proven absence. Do not treat an unmerged design PR as adopted baseline for product-intent changes. Routine fixes fully inside an adopted design may proceed without a new design PR or per-turn branch when scope stays aligned.

Mechanical receipts for supported entry points use `scripts/work_routine_design_entry_gate.py` (deterministic JSON evidence) and the existing START checkpoint gate; this does **not** intercept ordinary live CHAT answer submission.

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

**当面のGPT CHAT→Host単一実行経路:** 既存のGitHub Actions（DebugAI `ChatGPT Live Dogfood`）からCloudflare Access経由で既存のDebugAI bounded Server Command / 認可済みGitOpsを利用する。直接MCPがCHATに表示されなくてもHost操作全体を不可と判定しない。Push起動のRunをPR専用のcommit-run検索だけで判定せず、既存GitHub APIのActions Run一覧→Job→生Logから対象HEAD・Request ID・実結果を照合する。Trigger設定は元のhealth-only Blobへ復元してReadbackする。対象Repoが未登録、Host契約にないCommand、現行Runtime Source不足なら、その操作だけを正確な理由で保留し他の安全作業を継続する。新しいMCP・Workflow・Token・RunnerやRepo別Transportを作らない。実装と認可の正本はDebugAIとserver-coreの既存Registryであり、この文書には複製しない。

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

本番常駐は原則Docker / Docker Compose。

ServerはRuntime/Processing環境であり、Project Source履歴・Design・Documentの正本をServerだけに置かない。

Deployはconfirmed GitHub revisionを起点にし、必要なMaster承認後に対象Project/共通Runbookへ従う。

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