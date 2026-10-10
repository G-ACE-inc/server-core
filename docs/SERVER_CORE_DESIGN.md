# SERVER CORE DESIGN

Version: 2026-09-30
Status: Design Baseline

## 1. Purpose

`server-core` is the **G-ACE Workspace command center**.

Its role is not to implement every Project. Its role is to receive a task, determine the correct Project and authority, control what information must be loaded, expose shared capabilities safely, enforce common development and verification rules, preserve GitHub work history, and govern the path from verified source to approved runtime operation.

Every AI / developer working inside the G-ACE Workspace must be able to start from server-core and determine **where to work, what to read, what may be reused, what must be verified, what must be recorded, and which approval boundary must not be crossed**.

## 2. Command Center Responsibilities

server-core owns the Workspace-wide command functions below.

### 2.1 Intake / Routing
- classify the current task by purpose;
- identify the target Project / repository / runtime domain;
- route to only the server-core authority required for that task;
- then dispatch work to the target Project README and target-specific authority.

### 2.2 Authority / Context Control
- `README.md` is the command-center entry point;
- `docs/LOAD_SCOPE.md` is the task router and context-loading authority;
- server-core authorities are loaded only when needed;
- Project work starts from the target Project README;
- unnecessary archive, build, cache, logs, backups and unrelated repositories are excluded from normal context.

### 2.3 Project Dispatch
server-core tells an AI/developer **where the work belongs**. Project-specific source, design, tests and runtime logic remain in that Project.

server-core must not absorb Project implementation merely because the Project is controlled from the Workspace.

### 2.4 Shared Capability Control
server-core provides the discovery and use contract for Workspace-shared capabilities:
- MCP;
- developer tools / skills;
- DebugAI;
- reusable KB;
- GitHub operations;
- shared Secret / Token broker contracts;
- Provider contracts such as Cloudflare / Hugging Face.

The implementation body stays with its owning Project/runtime. server-core owns discovery, connection contract, owner, permission boundary and availability state.

### 2.5 Development / Verification Governance
server-core defines Workspace-wide rules for:
- reuse-first development;
- README / Design / Project Tree / Design Delta / System Document responsibilities;
- verification and failure-case requirements;
- documentation gate;
- GitHub work-report commits;
- state separation between Source, Test, Commit, Push, PR, CI, Merge, Deploy, Runtime and Production.

### 2.6 Runtime / Operations Governance
server-core governs the common operational boundary for:
- deployment from confirmed GitHub revision;
- Docker / Docker Compose production residency;
- runtime verification;
- log / cache / temporary-state lifecycle;
- cleanup safety;
- backup / recovery;
- resource-pressure policy.

Project-specific runtime implementation remains owned by the target Project.

## 3. Command Flow

The standard command path is:

```text
REQUEST
  -> server-core/README.md
  -> docs/LOAD_SCOPE.md
  -> classify task / target / required authority
  -> load only required server-core authority
  -> target Project README
  -> required Project Design / Tree / Delta / System Doc / Source / Test
  -> reuse check
  -> implementation / debug
  -> verification
  -> documentation gate
  -> GitHub work-report commit
  -> push / remote readback / PR / CI as required
  -> approval boundary
  -> deploy / runtime verification only when authorized
```

A later state must never be inferred from an earlier PASS.

## 4. Authority Model

### README
README is the current-state command entry. It is not the design baseline.

It must make the following reachable when they exist:
- Design;
- Project Tree;
- Design Delta;
- completed System / Feature-bundle / Module documents;
- run / test / verification entry points.

README reports only completed / verified current state and clearly separates pending / not-verified work.

### Design
Design preserves architecture, contract, responsibility and boundary baseline.

Do not rewrite Design merely to make it match later implementation. A formal architecture change requires traceable rationale and a Design Delta.

### Design Delta
When implementation or architecture intentionally differs from the baseline Design, record at least:
- baseline design;
- actual change;
- reason / root cause;
- evidence;
- affected scope;
- applied commit;
- compatibility / migration / rollback considerations.

### Project Tree
Project Tree is a navigation index, not a raw file dump. It records meaningful files/directories, responsibility, entry points, related Design and related Tests.

Update when files/directories are added, deleted or moved, or when major responsibility / entry-point structure changes.

### System / Feature-bundle Documents
Create or update technical documentation only when README alone cannot hand the completed unit to another AI/developer reliably.

Typical triggers:
- multiple Features form one System responsibility;
- a reusable Module is completed;
- a stable internal/external Interface exists;
- state/data ownership is non-trivial;
- runtime/recovery/security/operations understanding is required;
- another AI/developer should be able to continue without verbal explanation.

### 4.1 Shared Capability vs Project Integration Boundary

server-coreがWorkspace共通Capabilityとして管理する対象は、DebugAI / MCP / KB / GitHub / Cloudflare / Hugging Face / Runtime確認 / Libral Vault / Workspace Registry / Monitoring / Backup / Recovery / Search / Index とする。

TGserver / webhook gatewayはShared CapabilityではなくProject Integration。共通導入契約は `docs/PROJECT_INTEGRATION_RULES.md`、実装本体は各Projectが所有する。

Libral VaultはShared Capabilityとしてserver-coreがSecret契約・安全境界を管理し、Project側ではconsumer / injection / runtime usageをIntegration Ruleで定義する。Secret実値はProjectへ複製しない。

## 5. Development and Reuse

LibralCore methodology is defined by `CORE.md`.

Reuse priority:

```text
use existing asset as-is
  -> configuration / argument / type adjustment
  -> thin adapter
  -> common extraction
  -> new implementation only when necessary
```

New code, module, tool or document must not be created before the relevant existing asset is checked.

## 6. Verification Contract

PASS must be based on the evidence required by the task, including as applicable:
- input;
- execution condition;
- expected output;
- state change;
- state that must not change;
- regression;
- important failure cases;
- runtime / provider readback.

Process start, no error, HTTP 200, build success or CI green alone is not sufficient unless that is the actual acceptance contract.

Unverified state remains `UNKNOWN / NOT_EXECUTED / NOT_VERIFIED`.

## 7. Documentation Gate

Before work is documentation-complete, determine:

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Required documentation that is not updated keeps the work incomplete.

## 8. GitHub Work Report Contract

Commit / PR is the chronological work-history authority.

Where applicable, a commit must allow later readers to identify:
- purpose;
- material changes;
- affected scope;
- verification and result;
- documentation updated;
- remaining / unverified work.

Commit text does not replace Design Delta when a design difference must be preserved.

## 9. Shared Capability Registry

`docs/WORKSPACE_REGISTRY.md` is the command-center discovery registry.

It records:
- Project -> repository -> Workspace/server entry;
- shared MCP / tools;
- Secret Contract identifiers, never values;
- capability owner;
- availability / verification boundary;
- runtime-discovery method.

Registry entries are navigation and contract data, not proof that the current runtime is healthy.

## 10. Knowledge Base

Reusable-development KB data lives outside server-core. Current target storage is Master PC `F:` (1 TB).

server-core owns only the access, registration, lifecycle and safety contract. KB data itself is not stored in this repository.

Server-side or Workspace access must use an explicit verified bridge such as API/MCP; never assume the VPS can directly read the PC drive.

Authority: `docs/KB_REUSE_DESIGN.md`.

## 11. Secret / Token Boundary

Secret / Token values are never a server-core document or Git authority.

server-core may own:
- provider / purpose;
- secret identifier;
- consumer;
- broker / Vault path;
- allowlist and use contract;
- verification and failure behavior.

Authority: `docs/WORKSPACE_SHARED_SECRETS.md`.

## 12. Server Operations

The server is a runtime / processing environment, not a replacement for GitHub source history.

Production-resident services use Docker / Docker Compose unless a formally approved Project exception exists.

Common lifecycle boundaries are defined by `docs/STORAGE_LIFECYCLE.md`; deployment boundary is defined by `docs/DEPLOY_RUNBOOK.md`.

Automated cleanup is fail-closed. Active state, unshipped data, retry state, recovery data, unknown ownership and active/persistent volumes are not generic deletion targets.

## 13. Command-Center Invariants

The following must always remain true:
- Workspace work can start from server-core without ChatGPT-only or Notion-only state;
- server-core determines routing but does not take ownership of Project internals;
- the same fact has one intended authority;
- context loading is progressive;
- shared capabilities have explicit owner and availability state;
- Secret values never enter Git/Chat/docs/logs;
- design history is not erased to match implementation;
- work history is retained in GitHub;
- unverified states are not promoted to PASS;
- approval boundaries are not crossed implicitly.

## 14. Explicit Non-Goals

server-core does not own:
- Project-specific implementation bodies;
- Project-specific Design bodies;
- DebugAI internal orchestration;
- Astera / TGserver internal specifications;
- KB data;
- runtime log/cache data;
- Secret/Token values;
- ChatGPT-only continuity;
- per-AI private prompts or reasoning.

## 15. Design Change Rule

This file is the server-core architecture baseline.

Do not silently rewrite it to follow implementation drift. Formal changes require rationale, evidence and an entry in `docs/DESIGN_DELTA.md`, plus a traceable commit.
## 16. Common CHAT-to-Host controlled reflection (design contract, 2026-10-10)

### 16.1 Ownership, scope, and purpose

**Canonical owner: G-ACE-inc/server-core, Control Issue #10, under Control #15 and GitHub Project #1.** This section is the stable *cross-repository tool design*; #10 records changing Change Units, owner, evidence and next gate. It is not another AI rule plane, a separate Current tracker, an authorization credential, or a new executor.

The complete G-ACE Development Platform purpose remains GitHub Development Control **and** Unified Development Log with cross-CHAT/Work/Codex/Cursor/Server/Actions/Runtime traceability and TGserver search/recovery. This tool is an enabling capability: **ordinary GPT CHAT must be able to take an authorized, verified GitHub revision through an existing bounded Host route to actual Server files/services and return independent Host evidence**. A GitHub commit, PR, CI success, updated local main ref, or green Actions job alone is not completion.

Responsibility separation:

| Owner | Owns | Does not acquire |
|---|---|---|
| server-core / #10 | Common dispatch/authorization interface, Project–Repo–canonical Host path and consumer mapping, branch/checkout governance, acceptance states, cross-Repo evidence schema | Product-specific code or permanent Secret values |
| GitHub Project #1 / owning Current | Master intent, canonical Project purpose, Change Unit, mutation owner, authorized scope, next gate | Host credential or runtime truth |
| GPT CHAT / Work coordinator (#17) | Design/Current rehydrate, technical decisions, GitHub Source/CI, request dispatch and exact evidence reconciliation | Right to bypass trusted Host admission |
| SERVER_AI / Composer / Codex (#16) | Bounded delegated implementation/Host work, minimal evidence receipt | GPT CHAT full rule payload or independent authority expansion |
| Existing DebugAI implementation owner | Existing Actions-triggered Cloudflare Access, bounded Server Command and guarded GitOps API/Host executor code | Whole-project Source/Design authority or arbitrary new target admission |
| Target Repository / Host | Product Source/Tests and actual active checkout, containers, health, operation status | Permission inferred from a GitHub Issue comment |
| TGserver ZERO owner | Durable Development Event transport, indexing/search/recovery | Authorization for Host writes or Source/Deploy PASS |

**Reuse first:** Existing prior partial cross-Project route work in server-core PR #36 (docs/GITHUB_PROJECT_CHAT_HOST_ROUTE.md, route registry and validator) and merged stacked PR #37 provides static dispatch/evidence parsing only. PR #36 remains outside main and must not be misrepresented as installed/live routing. Reuse its validated constraints and logic when its owner reconciles it; do not create competing workflow, MCP, token, queue or adapter. The authenticated live transport is the existing DebugAI ChatGPT Live Dogfood Actions lane.

### 16.2 Mandatory design-before-mutation preflight

Before any source/Host/registry/reflection mutation, resolve and record:

1. Project #1 and target owning Current, fixed Project purpose and target active Design/Definition of Complete, Master latest intent, exact Change Unit and single mutation owner.
2. Exact requested operation class, effect, target repository and verified GitHub remote identity, branch, expected full 40-character SHA, changed paths and required tests/CI.
3. Canonical parent realpath, Git common directory, intended consumer checkout/path, active HEAD/branch, index + working-tree dirty paths, existing linked worktrees and PR owners, and observed Host-installed admission revision. Unknown is NOT_VERIFIED.
4. Existing transport/runner/route applicability, separately from Host-authorized Repo/Project item/actor/branch/path/effect scope. Static config and prior PASS do not establish active Host authorization.
5. Required operation-specific rollback/prestate and independent evidence for Source, CI, Host, Deploy, Runtime and Development Log.

If the baseline Design cannot be resolved, mark DESIGN_BASELINE_NOT_VERIFIED; if an intended operation conflicts with the Design, mark DESIGN_DRIFT_REVIEW_REQUIRED and resolve at the owning Design before design-changing implementation. A gate failure blocks only the affected operation; other independently safe read-only/evidence work continues.

### 16.3 Canonical Host location and Branch/consumer invariants

A repository is mapped by **exact verified identity**, not a matching folder name or a Project membership claim. The mapping must bind GitHub repository ID/owner, Project item and Control Issue, permitted canonical Host parent realpath, permitted logical root, Git common directory, expected remote, allowed branch/SHA/paths, permitted command/effects, and (only if relevant) explicit Compose runtime target. Host admission is a separate trusted write/readback.

The current actual server-core parent is /home/admin1/server-core, **not** /home/admin1/projects/server-core. The existing DebugAI host-workspace reader supports only projects and worktrees roots and its installed registry maps server-core to projects; that mapping is **incorrect for the canonical parent**. A future precisely named root/entry for this canonical path must be implemented only through the existing owner-authorized allowlist, with exact realpath containment, no symlink/parent traversal, no broad /home/admin1 scanning and no free-form path or shell input. Reject unknown, stale, mismatched and ambiguous roots. Never create a duplicate server-core sibling or relocate the parent as a shortcut.

Allowed isolation: a branch or owned linked worktree *inside the existing canonical parent* if useful and verified. Forbidden: a derivative sibling at /home/admin1/projects, an unregistered top-level clone, automatic cleanup of another owner's work, or inferring that moving refs changes the active consumer. Existing PR #39 branch and its uncommitted operations/master-internal-repositories.json remain owned and protected. **Moving local main to origin/main is REF_UPDATED only, not ACTIVE_FILES_UPDATED.** A worktree carrying new Source is STAGED, not ACTIVATED until the actual loader/consumer path selects it and reads back the exact content. On divergent or dirty active checkouts: stop that write, preserve them, determine same-CU owner integration strategy, and never use hard reset/forced checkout or blind merge/rebase.

### 16.4 Existing execution path and logical request contract

Transport remains: ordinary CHAT authorized GitHub file update on existing bounded trigger branch and exact JSON target → existing GitHub Actions run/job → Cloudflare Access → existing DebugAI authenticated bounded command/GitOps API → admitted Host executor → final request status and source/health evidence → owning GitHub Current and (in its separately approved lane) TGserver ZERO.

The common dispatch decision is **logical**, not a claim that this JSON schema is already implemented. An implementation must bind these fields without inventing a second trigger:

| Field | Required validation |
|---|---|
| request identity | Unique request/operation ID; operation class and idempotency/replay policy |
| actor + authority | Verified Master development owner, target Project item/Control Issue, installed issuer/policy digest and enable/revoke state |
| exact target | GitHub repository owner/ID, remote, canonical Host parent identity and explicit consumer target |
| immutable Source | Branch, exact remote 40-character SHA, expected active HEAD/precondition, changed-path allowlist and CI gate |
| bounded effect | READ_FILE / READ_STATUS / SOURCE_REFLECT / COMPOSE_REFLECT, allowed scope, effects, timeouts and rollback |
| result correlation | Trigger SHA, Actions run/job ID, Host command/GitOps request ID, installed policy digest, before/after active revision and observed file/health state |

**No direct generic shell API.** Existing Host admission must authenticate each request and recheck after queueing, prior to effect, and at readback. An editor/CHAT instruction or a checked true flag is never a token. Production exposure, destructive/persistent data/Secret/provider/cost effects keep their existing protected approval gates.

### 16.5 Distinct operations and their evidence

- **READ_FILE / READ_STATUS:** inspect only admitted exact registered entries and filtered safe file paths, bounded offset/page limits, SHA-256 and size consistency, positive result plus negative path/traversal/redaction tests. GitHub Source blobs are not a substitute for installed Host file identity.
- **SOURCE_REFLECT:** only for a repository with an admitted *source-only* operation contract, a verified exact remote SHA, clean/compatible target or isolated owned staging, admitted paths/effects and a proven active consumer switch/integration. Preserve existing active checkout ownership and modifications. No automatic Docker rebuild if runtime inputs are unchanged. Output must include before ref + active HEAD, after ref + active HEAD, read files' hashes and actual consumer path. If the current DebugAI master-internal verifier requires a projects-root compose.yaml/app runtime, it **cannot be reused unmodified** for a server-core source-only parent; a narrower legitimate source-reflection policy/type and approved Host implementation are required before write.
- **COMPOSE_REFLECT:** distinct project-specific runtime contract with actual compose path, services, health, config/secret injection and rollback. Current DebugAI compose-oriented runner applies only to its enrolled repository and validated scope; no automatic cross-project entitlement. Only an authorized installed target may build/recreate services. Do not infer server-core project-control is running merely from Source.
- **Development Event:** correlate attempted and completed operations, branch/SHA, actor, CI, request/status, failure/rollback and Runtime readback with the existing TGserver ZERO producer where separately configured; missing event delivery is LOG_NOT_VERIFIED, not a fabricated PASS or automatic permission to deploy.

### 16.6 Deterministic states and fail-closed failures

Separate states explicitly: DESIGN_APPROVED, SOURCE_READY, CI_PASS, TRIGGER_ACCEPTED, HOST_ADMITTED, STAGED_SOURCE, ACTIVE_FILES_REFLECTED, DEPLOY_PASS, RUNTIME_PASS, LOG_DURABLE. A stage is NOT_VERIFIED until its own real evidence exists; no later status retroactively supplies an earlier gate. COMPOSE_REFLECT is NOT_APPLICABLE only for verified source-only changes without runtime effect.

A 502/5xx from the API entrance is TRANSPORT_UNAVAILABLE; preserve the run/result ID and distinguish it from Host denial or Source failure. Retry once only after observed recovery, with idempotency checked. A denied root/branch/path/policy is AUTHORIZATION_BLOCKED and must not be bypassed by a different path. A dirty/divergent consumer checkout is CHECKOUT_CONFLICT and must not be overwritten. A passed request with unchanged active files is REF_ONLY_NO_ACTIVATION, not reflection PASS. Partial Host action must retain prestate, operation ID, failure details and tested rollback plan.

### 16.7 Acceptance and verification gates

| Gate | Required directly read evidence |
|---|---|
| D0 Design | This baseline and Design Delta linked from server-core #10, explicit ownership, exact supported operations, approved non-goals, concrete test matrix |
| D1 Existing route/source | Reuse inventory, reviewed Source/changed paths, deterministic positive and negative tests, same-head CI; PR #36 and #37 integration state verified rather than assumed |
| D2 Host read | Live ordinary CHAT-origin Actions run/job and command ID; exact canonical /home/admin1/server-core file positive SHA-256 read; wrong entry, root alias, path escape/symlink, secret and unregistered Repo negative checks |
| D3 Source reflection | Per-Repo installed delegated authorization, prestate and dirty/PR ownership checks, confirmed remote SHA, exact active target after authorized switch, real readback of changed files, no unrelated services touched |
| D4 Runtime | Only for applicable runtime change: exact service revision/compose, running+healthy or defined endpoint behavior, logs, rollback/negative evidence. No Runtime PASS from GitHub checks |
| D5 Cross-surface proof | CHAT can request→track Actions run/job/Host operation→verify exact Source and applicable Runtime and record in owning Current; ZERO event durable/search/restore is its separately owned acceptance gate |

Minimum negative cases include: unregistered repository/Project item, forged or revoked issuer, stale branch/SHA, changed-path overflow, root-key pointing at wrong realpath, symlink or ../ traversal, dirty/other-owner PR39 checkout, divergent ancestry, incomplete paged file/changed hash, retry/replay, secret redaction, API 502 and failed Host job, false-green Actions, false PASS when only local main moved, and unadmitted Compose recreate. Execute deterministic/offline checks before any real Host mutation. Do not spend free Groq/Gemini provider quotas on transport/design tests.

### 16.8 Implementation ordering and handoff

1. **Design commit first in server-core #10** with Design Delta and a single owner; existing PR #36 documents/static validator are partial reuse input, not second Authority.
2. Reconcile confirmed consumer mapping and exact Host admission for READ_FILE; modify only the owning admitted reader/registry and bounded Actions target validation as separate qualified CUs, preserving current DebugAI product work and all existing negative guards. Actual installed Host source and policy readback required.
3. Prove positive canonical-parent Host read + negative denial through a real CHAT-triggered run.
4. Define/qualify a source-only reflection path distinct from Compose deployment under existing trusted authorization (with exact Branch/HEAD/dirty checkout gate), then real same-request before/after evidence.
5. Extend additional registered repositories only after per-target Project+Host enrollment and independent Runtime acceptance; expand ZERO event delivery under its owning integration contract.

**No activation by design publication.** D0 is a documented contract, D1–D5 require implementation/Host/Runtime evidence. Completion of the whole G-ACE platform additionally requires its fixed Unified Development Log acceptance; this section does not silently make that product complete.
