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
## 16. Tool capability B — common CHAT-to-Host controlled reflection (design contract, 2026-10-10)

### 16.1 Ownership, scope, and purpose

This is **Tool capability B**, one of the two co-primary delivery capabilities governed by server-core Control #10. Tool capability A is the Unified Development Log in §17. Neither is an optional afterthought, and neither is completed by writing the design alone. Source/Host and Log have independent acceptance gates; the overall G-ACE platform requires both.

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
| D5 Cross-surface proof | CHAT can request→track Actions run/job/Host operation→verify exact Source and applicable Runtime and record in owning Current; capability A's independent durable event/storage/search/recovery contract is §17, not a deferred optional add-on |

Minimum negative cases include: unregistered repository/Project item, forged or revoked issuer, stale branch/SHA, changed-path overflow, root-key pointing at wrong realpath, symlink or ../ traversal, dirty/other-owner PR39 checkout, divergent ancestry, incomplete paged file/changed hash, retry/replay, secret redaction, API 502 and failed Host job, false-green Actions, false PASS when only local main moved, and unadmitted Compose recreate. Execute deterministic/offline checks before any real Host mutation. Do not spend free Groq/Gemini provider quotas on transport/design tests.

### 16.8 Implementation ordering and handoff

1. **Design commit first in server-core #10** with Design Delta and a single owner; existing PR #36 documents/static validator are partial reuse input, not second Authority.
2. Reconcile confirmed consumer mapping and exact Host admission for READ_FILE; modify only the owning admitted reader/registry and bounded Actions target validation as separate qualified CUs, preserving current DebugAI product work and all existing negative guards. Actual installed Host source and policy readback required.
3. Prove positive canonical-parent Host read + negative denial through a real CHAT-triggered run.
4. Define/qualify a source-only reflection path distinct from Compose deployment under existing trusted authorization (with exact Branch/HEAD/dirty checkout gate), then real same-request before/after evidence.
5. Extend additional registered repositories only after per-target Project+Host enrollment and independent Runtime acceptance; expand ZERO event delivery under its owning integration contract.

**No activation by design publication.** D0 is a documented contract, D1–D5 require implementation/Host/Runtime evidence. Completion of the whole G-ACE platform additionally requires its fixed Unified Development Log acceptance; this section does not silently make that product complete.

### 16.9 Autonomous development operation coverage — design extension (2026-10-11)

**Purpose and non-goal.** Tool B must permit ordinary GPT CHAT to finish a registered development Change Unit as a continuous verified loop: restore Current/Design → inspect actual GitHub+Host prestate → diagnose → change owning Repository Source → run focused tests/CI → authorized Host reflect and applicable Compose operation → verify actual consumer/runtime → inspect failures and replan → emit correlated Tool A evidence. Existing §16.1–16.8, §17, Rule #17, Project #1 and current approval/Host admission remain authoritative. This extension defines capability contracts and acceptance, **not** granted permissions, newly installed commands, general shell execution or a claim of completed runtime.

**Required bounded capability families, separated from implementation:**

| Family | Required permitted operations / output contract | Safety and acceptance |
|---|---|---|
| Project/Host discovery | registered project inventory, canonical realpath and Git common-dir identity, active consumer path, bounded directory listing and filtered file content/hash/page, installed policy/version | exact registered target; no arbitrary ancestor scan, symlink/traversal, secret exposure; positive + deny evidence |
| Git diagnosis and recovery | remote identity, branch/HEAD, status and changed paths, log/diff bounded to allowed paths, fetch/compare and non-destructive owner-scoped checkout/staging where explicitly admitted | distinct REF_UPDATED/STAGED/ACTIVE; preserve dirty/other-owner checkout; no implicit force-reset/rebase; exact before/after and conflict rejection |
| Test and build | approved per-project test/build target selected from registered manifest, timeout/resource bound, stdout/stderr artifact and exit code, exact tested SHA | no requester arbitrary command; focused reproducible test→CI parity; negative test for unregistered script and mismatched SHA |
| Docker/Compose inspection | registered service ps/inspect, config identity, filtered logs, health, image digest/revision, dependencies and recent failure state | prohibit arbitrary container/project selection; redaction and bounded log; verify service/Compose mapping |
| Docker/Compose lifecycle | explicitly admitted per-service build, start, stop, restart/recreate, and rollback only when effect and downtime/data consequences pass existing Host delegation and impact gates | prestate, named service, Compose config digest, effect category, timeout, health/readback, recoverability; unknown/protected effect denies only mutation |
| Source/Runtime reflection | existing §16 SOURCE_REFLECT and COMPOSE_REFLECT with exact GitHub SHA, allowed paths/effects, installed checkout and active consumer proof | Host audit and single-use receipt; no false PASS for ref-only update or HTTP 202 |
| Evidence and controlled replan | correlate GitHub issue/PR/check with Actions run/job, Host command/GitOps ID, pre/post state, failure class, rollback and matching Tool A event | every result verifiable, missing ZERO remains LOG_NOT_VERIFIED; fail/deny does not end independent in-scope work |

**Capability registry requirements.** For each concrete action, the existing registry and implementation owner must bind `capability_id`, `operation_class`, `owner_repository`, `target_project_item`, `canonical_host_target`, `accepted_parameters`, `bounded_effects`, `allowed_paths_or_services`, `required_branch_sha_ci`, `delegation_scope`, `timeout_and_output_limits`, `idempotency`, `prestate_and_rollback`, `result_markers`, `positive_and_negative_tests`, and `verified_runtime_revision` where applicable. Unsupported, unadmitted and Source-only are three different states. Tool B must not advertise a catalog command as executable when the Actions dispatch and Host policy intersection excludes it. No new parallel registry is authorized by this specification.

**Continuous development state machine.** `CURRENT_RESTORED → TARGET_AND_OWNER_VERIFIED → HOST_PRESTATE_VERIFIED → ROOT_CAUSE_EVIDENCED → SOURCE_PATCHED → FOCUSED_TEST_PASS → CI_EXACT_SHA_PASS → HOST_AUTHORIZED → ACTIVE_REFLECTION_VERIFIED → RUNTIME_CHECKED_OR_N_A → EVIDENCE_RECORDED → CU_ACCEPTED`. Each arrow requires its own direct evidence or explicit not-applicable ruling, not an invented aggregate PASS. A failure transitions to `FAILURE_CLASSIFIED → REPLAN → NEXT_AUTHORIZED_ACTION`; protected admission denial blocks only that effect, while source diagnostics, tests and other safe CU actions continue. If runtime differs from source, diagnose version drift before new reflection. Never run model-provider test calls merely to qualify transport.

**Design acceptance matrix (not implementation claims).** One enrolled target must demonstrate (1) real canonical Host path + bounded source/file read; (2) Git dirty/conflict observation and safe rejection; (3) approved test with exact input SHA, captured exit/artifact and failing-test evidence; (4) registered Docker status/log, plus safely admitted lifecycle operation with prestate/health/rollback when applicable; (5) Source-only reflect and a distinct Compose reflect for a suitable already enrolled target, with exact active consumer proof; (6) negative unregistered repo, operation, path, service, stale SHA, missing CI, overlap, policy revocation, replay, unauthorized effects and secret redaction; (7) actual CHAT-origin request→Actions run/job→Host terminal status→readback→GitHub Current plus separately evidenced §17 ZERO event. Completion requires an actual **fault→diagnosis→repo fix→test/CI→authorized reflection→runtime verify→log/Current** cycle without Master copying server commands. Merely passing static CI or adding a command name is insufficient.

**Ownership and rollout.** server-core #10 owns common contract/dispatch/evidence, existing DebugAI Host owner owns runner and admission, target Repositories own tests and product Source, and TGserver owns log durability/search. First inventory existing commands and admitted operations; add only missing bounded capability to those owners, preserving security and commercial isolation. Stage implementation per owned CU after this design is reviewed; update append-only Design Delta, README/Tree only when needed. No Host/credential/runtime permission is changed by this design commit.

## 17. Tool capability A — Unified Development Log: collect, persist, search and restore (2026-10-10)

### 17.1 Fixed tool priorities, purpose and owner

**Two co-primary tool capabilities (neither subordinate to the other):**
- **A — Development Log:** the Master can obtain and recover verifiable development activity across ordinary GPT CHAT, ChatGPT Work, VS Code Codex, Cursor/Composer, server agents, GitHub Actions, actual Host/Runtime and registered repositories in **TGserver ZERO** without copying VPS logs or whole old chats.
- **B — CHAT→Server:** ordinary GPT CHAT can use the existing authorized bounded GitHub Actions→Cloudflare Access→DebugAI Host route to inspect, operate, safely reflect a verified Source revision and confirm the actual active Server state (§16).

**Owner of the common tool specification, routing, cross-surface evidence and two-capability acceptance: G-ACE-inc/server-core, Control #10 under Project #1 / Control #15.** Separate, non-duplicated implementation owners remain: TGserver ZERO for canonical event ingest/raw/index/search, webhook-gateway for the existing authenticated generic event transport, DebugAI for actual Server Command/guarded GitOps and bounded Host execution, and each product Repo for its own event producer and source/runtime facts. The owning GitHub Project Current records project purpose, Change Unit, mutation owner and next gate; it does not replace product implementation authority.

G-ACE platform purpose is GitHub Development Control **integrated with** Unified Development Log. This is not a new Knowledge Base or Knowledge Promotion feature: promotion remains Catalog-owned. Do not re-label DebugAI-bound Host commands as a mandatory delivery path for events from all projects; independent admitted event producers may use the existing Generic Internal Event API.

### 17.2 Canonical events and mandatory coverage

Reuse the **existing gace.development.event.v1** event and TGserver ZERO project/stream mapping, not another event schema/store/queue/reader. Require identity and bounded observability data sufficient to correlate:
- source surface (CHAT, Work, Codex, Cursor/Composer, Server agent, Actions or Runtime), source instance/session, occurred_at, stable event_id/sequence and provenance;
- registered repository + stream and its owning Project/CU/Issue; branch and exact commit SHA/PR/check run/workflow IDs where applicable;
- operation class, observed result (including failure, retry, block, rollback), concise user-safe summary, evidence references to source/CI/Host/Runtime, and policy/authorization outcome when applicable;
- processing timestamps, producer correlation/transport receipts and the observed final storage/search location;
- redacted metadata only: no transcript dumps, chain of thought, credential values, private file contents, or unrelated data.

Required coverage is across **all registered repositories and execution surfaces**, with explicit per-surface producer owner, ingress route, tested capabilities, gap and last proven timestamp. Absence of a producer must appear as PRODUCER_NOT_VERIFIED/NOT_CONNECTED, not "no events". Never fabricate older CHAT/Host records that were never captured. Recovery must distinguish collected historical evidence from gaps in coverage.

Canonical stable event_id, identical payload on retry, duplicate recognition and same-ID/different-payload rejection remain TGserver-owned. Use the already-defined TGserver v1 event contract and its authenticated CHAT [DEVLOG] comment adapter where applicable; validate actor, repo+stream map, bounded fields, redaction and event type. No requester-controlled arbitrary URL, shell, Project ID or TGserver internal destination.

### 17.3 Existing end-to-end lanes: no new transport

**Runtime / Server / product producer:** Target-owned observable event/log -> existing durable producer/outbox and redaction when available -> existing authenticated Generic Internal Event API in webhook-gateway -> configured registered TGserver development-event destination -> ZERO existing canonical ingress/ingest -> Telegram raw + Meilisearch searchable index. A Gateway 202 receipt is a *transport receipt* only; it does not prove raw Telegram persistence or indexed search.

**Ordinary CHAT:** Distilled observable event with evidence -> existing owner-only TGserver issue comment relay [DEVLOG] -> existing GitHub Actions -> admitted shared Gateway and same registered destination -> ZERO. The existing source contract may require DEVLOG_GATEWAY_URL and DEVLOG_GATEWAY_TOKEN (or existing configured shared equivalents); when absent, fail closed without echoing secrets, setting credentials from CHAT or inventing a direct fallback.

**Read and recovery:** Existing TGserver ZERO GitHub-central Reader/search, scoped by registered repo+stream, indexed event_id, source instance/session, Issue/PR/commit and event time as actually supported -> retrieve evidence references -> independently verify live Source/CI/Host when current-state decisions require it. The Reader returns indexed evidence; search zero is NOT proof Telegram raw contains no event. Query/pagination/time-filter accuracy and coverage must be measured against actual stored events.

Retain TGserver ZERO v1.5 Telegram-as-raw-authority and Meilisearch-as-rebuildable-index semantics; do **not** merge in TGserver vNext/PostgreSQL/service changes. Treat each linked Project mapping and producer installation separately. No new public endpoint, MCP client, workflow, token, token propagation or hidden cross-repository credentials.

### 17.4 Receipt chain and anti-fabrication state machine

For **each same event_id**, carry and distinguish:
1. OBSERVED_SOURCE — a real occurrence (CHAT/worker/Actions/Host/runtime) with direct source evidence;
2. VALIDATED_EVENT — schema, repo/stream mapping, actor, provenance, redaction and payload accepted;
3. PRODUCER_QUEUED — durable local outbox or owner-only relay submission observed, if that producer supports it;
4. GATEWAY_ACCEPTED — authenticated Gateway request + server-generated request/transport id, accepted to its existing durable delivery mechanism;
5. ZERO_INGEST_ACCEPTED — canonical ingress/pipeline accepted the exact event_id and same payload;
6. TELEGRAM_RAW_DURABLE — independent durable raw message/source pointer confirmed;
7. INDEXED_SEARCH_VERIFIED — Meilisearch/Reader actually finds the same event_id and relevant evidence;
8. RESTORE_VERIFIED — in a fresh CHAT/Work session, a bounded search reconstructs the Issue/branch/PR/CI/Host/Runtime evidence and explicit remaining work without manual pasted old logs.

Do not collapse stages into a single PASS. Different surfaces/projects may be at different states, and transport delivery, raw durability and index coverage have different authorities. Duplicated submissions must not multiply raw events. Timeout/502/retry, missing env/Secret, invalid mapping, disabled producer, reader filter/pagination defects and unindexed raw are independent failure classes; continue safe read-only diagnosis while preserving failed events/idempotency.

### 17.5 Integration with capability B, not circular dependency

Every accepted CHAT→Host operation in §16 must be eligible to produce an observable Development Event with matching repository, CU, source SHA, run/job ID, Host command/GitOps ID and terminal outcome. Conversely, lack of a healthy log sink must never *silently* mark a Host deployment healthy or authorize it. For write operations with an owner-required audit boundary, the existing authorization/audit requirement remains in force; missing optional log sink is LOG_UNVERIFIED and owned for repair, not an excuse to bypass approval.

Log collection must also function for projects not admitted for DebugAI Host mutation (e.g. through a verified independent existing Gateway producer). Source/CI/Host actuals always come from the appropriate owning evidence, not from a log summary.

### 17.6 Two-lane acceptance, precedence and executable next gates

| Lane/gate | Concrete acceptance evidence |
|---|---|
| A0 DESIGN | server-core main design §17 and Design Delta/routing readback; TGserver ZERO existing contracts linked; canonical owner and cross-project mapping explicit |
| A1 PRODUCERS | Per-surface and per-registered-repository producer/integration inventory, real Source/CI/Runtime availability, ownership and exact gaps, no duplicate implementation |
| A2 DELIVERY | Same event_id from at least the current normal CHAT and one independent Server/Actions/Runtime surface, across the existing authenticated Gateway to ZERO; emitted/accepted/retry/negative receipts traced |
| A3 RAW_AND_INDEX | Actual Telegram raw durability and indexed Reader search return the **same** event_id and evidence; bounded negative/pagination/date/duplicate tests |
| A4 REHYDRATION | New CHAT/Work can retrieve a real prior CU's latest verified Issue/branch/PR/CI/Runtime state and recover blockers/exact next action without manual VPS or past-chat log paste |
| B0–B5 HOST | §16's independent design, admitted canonical-parent read, exact Source reflection and applicable Runtime verification; integrated with A via correlated event receipts, not proxy success |

**Master execution priority (2026-10-10; latest intent): Tool B, ordinary CHAT→Server, FIRST.** The fixed platform requires both B and A, but equal completion importance is **not** a mandate to alternate tasks or split the current owner's attention equally. The existing TGserver ZERO log/Reader/Gateway/CHAT relay Source and verified historical Log coverage are PRESERVED and REUSED; do not redesign or reimplement them while Tool B is the current active CU. Execute B1 existing-route reconciliation → B2 authorized canonical-parent Host read → B3 actual bounded source-only reflection → B4 applicable Runtime readback and B5 correlation as far as proven permissions allow. Continue independent safe evidence/readback and do not pause B just to report. After the CHAT→Server operational path is usable, return to A's *verified remaining gaps* (including the previously failed Gateway-configured CHAT relay and same-event durable/index/fresh-CHAT recovery). Work on A earlier only if a distinct existing owner is independently executing it without conflicting with B. The priority change does not revoke existing A implementations, eliminate A0–A4 acceptance, grant Host authority or classify either lane as Runtime PASS.

**Last verified Log gap at design time:** TGserver #50 owner's actual [DEVLOG] relay Actions 37992536124 parsed a valid server-core event but reported both Gateway URL configuration options absent, failed before HTTP transport, and did not reach ZERO. Other ZERO Reader searches have shown indexed results for some projects, but are not evidence that that failed event was durably sent or indexed. Preserve this as a separate delivery blocker until an independent same-event retest. Avoid spending Groq/Gemini free daily/monthly calls on transport or Log tests.

