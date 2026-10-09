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

### Master-specific operating roles (single routine, no new control plane)

This is **Master's individual nontechnical development environment**, not a generic engineering-team approval flow. The authority boundaries already defined by Rule Plane #17 (GPT CHAT), #16 (SERVER_AI), and `SERVER_CORE_PROTOCOL.md` remain in force. No tool or executor may promote a routine technical choice into a new Master approval gate merely because it is a commit, deploy, test, rollback or command.

| Actor | Accountable for | May decide/execute within verified Current | Must not |
|---|---|---|---|
| **Master (product owner, nontechnical)** | Product outcome, priority, intended user-visible behavior, explicit exceptional intent/impact decisions and final product acceptance | Correct intended outcome and authorize real protected boundary when required | Be asked to choose SHA, branch, command, patch approach, test, tooling or routine execution method |
| **GPT CHAT (#17, single technical lead)** | Preserve Mission/CU, plan and carry out available direct work, select the minimal executor, judge Source/CI/Host/Log evidence, resume next gate | Direct GitHub Project/Issue/Repo/PR/CI/log/evidence work through actually available tools; delegate only the unavailable Host step; pursue same CU through retest and readback | Invent tool connectivity, assign overlapping mutation owners, use costly agents by default, hand routine technical decisions back to Master |
| **SERVER_AI (#16, constrained implementer)** | Complete assigned existing-CU implementation/Host investigation/verification and return exact evidence to GPT CHAT | Source/debug/test/readback and admitted Host operations only for the given repo/branch/SHA/scope/effects; choose routine technical details | Redefine Master Mission, create another controlling Project, bypass Host admission, escalate routine technical choices to Master |
| **Composer / Codex (optional executors)** | Narrowly delegated IDE edits or review inside the same CU and single-writer boundary | Composer only for beneficial multi-file work or necessary Host UI relay; Codex only where separately available and worth included quota | Automatically fan out paid subagents, alter a different CHAT's branch/PR, create top-level derived sibling checkout |
| **DebugAI / TGserver / GitHub Actions / Host** | Specialized facts, tests, logs and admitted execution | Perform the exact bounded action and return machine-verifiable receipt | Decide a new Mission, grant own authority, or treat a green Action as proof of deployed Runtime |

**Decision/dispatch order (GPT CHAT owns the result):**
1. Rehydrate the owning Current and test whether the proposed action matches Mission, existing CU, owner, Scope, acceptance and next gate.
2. Use verified existing evidence, code, APIs, deterministic checks and **GPT CHAT's directly available tools first**. Do not assign Composer a task CHAT can finish with comparable or lower cost/latency.
3. Delegate only the specific missing execution step to the **already-authorized** SERVER_AI / DebugAI / Host path. Composer is optional, not the default controller; Codex is not an automatic next hop. Keep one mutation owner and exact target. Never replace a missing Host connection with an unverified shell bridge.
4. Independently read back actual Source/CI/Runtime/Log outcome, diagnose and repair within the same CU, then advance its Exact Next Gate. A completed subtask is not completed product acceptance.
5. **Routine technical decisions are AI-owned.** If the verified Host authorization exists and the action is within the existing approved purpose/scope and reversible authorized effects, do not invent another per-action Master approval. Real protected effects (product semantics, material scope/cost changes, irreversible protected data, credentials/permissions, exposure or explicitly reserved authority) still require a valid user-intent decision and actual Host admission. Never fabricate an approval receipt or Secret.
6. If a protected action cannot proceed, stop **that action only**; continue independent authorized analysis/tests/source improvements. Tell Master the user-visible decision and impact, not technical steps. Never leave a technical failure as an open-ended instruction for Master to debug.

**No detour rule:** A missing log, Host file, route or tool is a *dependency investigation within the current Mission*, not permission to create a new bridge, Project, MCP or Architecture. Check existing owner/route, repair only the bounded dependency when it belongs to the current CU, otherwise record the dependency for its owning CHAT without taking over its work.

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
  -> approval boundary
  -> deploy/runtime only when authorized
```

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