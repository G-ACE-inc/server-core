# SERVER CORE DESIGN

Version: 2026-10-02
Status: Design Baseline

## 1. Purpose

`server-core` is the **G-ACE Workspace command center**.

Its role is not to implement every Project. Its role is to route work to the correct owner and authority, validate the selected execution route against technical boundaries, expose shared capabilities through explicit contracts, enforce common development and verification boundaries, preserve GitHub work history, and define the path from verified source to controlled runtime operation.

A worker starting from server-core must be able to determine:
- where the work belongs;
- what authority must be read;
- which repository may be mutated;
- which execution route has been selected by the Workspace top-level authority or Task Packet and whether it is technically valid;
- which shared capability may be reused;
- how the result is verified;
- what state is current vs historical;
- which mutation/approval boundary applies;
- how to hand an external Server operation off without inventing execution evidence.

Workspace-wide Bootstrap order outside server-core, executor selection priority, operator interaction policy and operator-facing command interface remain owned by the Workspace top-level operating authority. server-core does not duplicate or override those rules.

## 2. Command Center Responsibilities

### 2.1 Intake / Routing
- classify the task by purpose;
- identify the target Project / repository / runtime domain;
- identify the minimum server-core authority required;
- dispatch to the owning Project README and Project-specific authority.

### 2.2 Authority / Context Control
- `README.md` is the server-core command-center entry point after the Workspace top-level bootstrap;
- `docs/LOAD_SCOPE.md` is the server-core task router and context-loading authority;
- server-core authorities are loaded only when needed;
- Project work starts from the target Project README;
- archive, build output, dependency caches, logs, backups and unrelated repositories are excluded from normal context unless the task explicitly targets them.

### 2.3 Project Dispatch
server-core determines **where work belongs**. Project-specific source, design, tests and runtime logic remain in that Project.

server-core must not absorb Project implementation merely because the Workspace routes work through server-core.

### 2.4 Execution Route Validation
server-core does not own the Workspace-wide executor priority or operator interaction policy.

It validates the execution route already selected by the Workspace top-level authority or Task Packet against:
- route capability;
- target identity;
- mutation classification;
- authorization scope;
- technical safety prerequisites;
- verification path;
- unresolved blockers.

Execution capability and execution authorization are independent states. A worker may prepare an exact operation up to the pre-execution boundary without claiming that the operation ran.

Canonical field names / execution routes / mutation classes are machine-readable in `operations/pre-execution-schema.json`. Workspace pre-execution semantics are owned by `docs/G_ACE_WORKSPACE.md`. Server technical execution safety and evidence boundaries are owned by `docs/SERVER_COMMAND_CONTRACT.md`. Operator-facing command presentation remains outside server-core under the Workspace top-level operating authority.

### 2.5 Shared Capability Control
server-core provides the discovery and use contract for Workspace-shared capabilities such as MCP, developer tools/skills, DebugAI, reusable KB access, GitHub operations, shared credential broker contracts, Provider contracts, and shared monitoring/backup/recovery interfaces.

The implementation body stays with its owning Project/runtime. server-core owns discovery, owner, connection contract, permission/change boundary and verification method.

Here, `owns` means **authority/responsibility ownership**, not unconditional write permission.

### 2.6 Development / Verification Governance
server-core defines Workspace-wide rules for reuse-first development, documentation responsibilities, verification/failure-case requirements, GitHub work history, and state separation between Source, Test, Commit, Push, PR, CI, Merge, Deploy, Runtime and Production.

### 2.7 Runtime / Operations Governance
server-core governs the common technical operational boundary for deployment from a confirmed GitHub revision, Docker / Docker Compose production residency as the default, runtime verification, storage lifecycle, backup/recovery, provider mutation and credential safety.

Project-specific runtime implementation remains owned by the target Project.

### 2.8 server-core Mutation Authority
server-core is a reference/routing authority by default, not an implicitly writable repository.

Reading server-core, using its Runbooks, investigating a Workspace-common issue, finding an inconsistency in a common contract, or modifying another Project does **not** authorize server-core mutation.

Source, Document, Config, branch or commit mutation in server-core requires explicit owner authorization for **server-core itself**. The operational representation is `SERVER_CORE_MUTATION_AUTHORIZED=YES`; it may not be inferred from adjacent instructions, ownership labels, dependency impact or a worker's assessment.

Authorization is scoped to the current Task/change unit/target operation. A permission established for an earlier or adjacent Task is not automatically current permission.

## 3. Command Flow

After the Workspace top-level bootstrap and executor-policy evaluation:

```text
server-core/README.md
  -> docs/LOAD_SCOPE.md
  -> classify task / target / required authority
  -> lock mutation/read-only ownership
  -> load only required server-core authority
  -> target Project README / required Project Authority
  -> reuse check
  -> validate selected execution route
  -> implementation / debug or exact pre-execution preparation
  -> verification
  -> documentation gate
  -> GitHub work history
  -> push / remote readback / PR / CI as required
  -> required mutation / approval boundary
  -> deploy / runtime verification when applicable
```

A later state must never be inferred from an earlier PASS.

## 4. Authority Model

### README
README is the current command entry. It is not the design baseline and not a chronological work log.

### Design
Design preserves architecture, contract, responsibility and boundary baseline. A formal architecture change requires rationale and a Design Delta.

### Design Delta
When architecture or responsibility intentionally differs from the baseline Design, record baseline design, actual change, reason/root cause, evidence, affected scope, applied commit/PR, compatibility/migration/rollback considerations and verification state.

### Project Tree
Project Tree is a navigation index, not a raw file dump.

### System / Feature-bundle Documents
Create or update technical documentation when README alone cannot reliably hand the completed unit to another worker. Avoid empty template sections or transient work history.

## 5. Shared Capability vs Project Integration

Workspace-shared capability control includes reusable interfaces such as MCP, DebugAI, KB access, GitHub operations, Cloudflare/Hugging Face shared access, Vault/credential broker contracts, monitoring and recovery interfaces.

Project-owned systems such as TGserver or webhook gateway remain Project integrations unless ownership is formally changed. Common adoption rules are in `docs/PROJECT_INTEGRATION_RULES.md`.

Libral Vault is a Shared Capability; Project-specific consumers/injection/runtime usage are integration concerns.

## 6. Development and Reuse

LibralCore methodology is defined by `CORE.md`.

Reuse priority:

```text
use existing asset as-is
  -> configuration / argument / type adjustment
  -> thin adapter
  -> common extraction
  -> new implementation only when necessary
```

## 7. Verification Contract

PASS is based on the evidence required by the task, including as applicable input, execution condition, expected output, state change, state that must not change, regression, important failure cases and runtime/provider readback.

Process start, no error, HTTP 200, build success or CI green alone is not sufficient unless that is the actual acceptance contract.

Unverified state remains `UNKNOWN / NOT_EXECUTED / NOT_VERIFIED`.

A command being issued or a `PRE_EXECUTION_COMPLETE=YES` handoff is not execution evidence.

## 8. Documentation Gate

Update only documentation required by the actual change: README Current entry, Project Tree/navigation, Design/Design Delta, or existing/new stable System/Module documentation.

## 9. GitHub Work History / Concurrency

Commit / PR is chronological work-history authority.

Multiple Projects/agents/change units may be active concurrently. A commit helper must not stage unrelated working-tree changes. Intended repository, branch, diff and explicit file/change unit must remain separable.

Same-target writers must serialize or fail closed. The server-core auto-commit helper serializes same-checkout helper commits; the Workspace MCP installer serializes global Cursor config mutation.

Commit text does not replace Design Delta when a design difference must be preserved.

## 10. Shared Capability Registry

`docs/WORKSPACE_REGISTRY.md` is the discovery registry. Registry entries are navigation/contract data, not proof of current runtime health and not write permission.

## 11. Reusable Knowledge Boundary

Reusable-development KB data lives outside server-core. server-core owns only discovery, access/bridge contract, registration contract, lifecycle/safety rules and availability semantics.

Authority: `docs/KB_REUSE_DESIGN.md`.

## 12. Secret / Credential Boundary

Secret / Token / credential values are never server-core document or Git authority. server-core may own identifiers, consumers, broker routes, allowlists, verification/failure behavior and rotation/change boundaries.

Authority: `docs/WORKSPACE_SHARED_SECRETS.md`.

## 13. Server Operations

The server is a runtime / processing environment, not a replacement for GitHub source history.

Production-resident services use Docker / Docker Compose unless a formally defined Project exception exists.

Common lifecycle boundaries are defined by `docs/STORAGE_LIFECYCLE.md`; deployment by `docs/DEPLOY_RUNBOOK.md`; Server technical execution safety/evidence by `docs/SERVER_COMMAND_CONTRACT.md`.

Read-only inspection may still have I/O or client-side impact and must be bounded. Reversible local Git operations such as fetch/temporary checkout/switch are not labelled pure read-only merely because final state is restored.

## 14. Command-Center Invariants

The following must remain true:
- Workspace work can enter server-core after the Workspace top-level bootstrap using repository/runtime authorities;
- server-core determines routing but does not take ownership of Project internals;
- executor priority and operator-facing interface are not redefined inside server-core;
- selected execution routes are technically validated before use;
- execution capability is not authorization;
- authority/responsibility ownership is not mutation permission;
- server-core remains read-only without explicit server-core mutation authorization;
- authorization is task/change-unit scoped;
- same operational fact has one intended authority;
- context loading is progressive;
- concurrent change units are not mixed in commits;
- same-target writers serialize or fail closed;
- credential values do not enter Git, Source, Document or Log;
- design history is not erased to match implementation;
- unverified states are not promoted to PASS;
- external execution is not claimed without returned evidence.

## 15. Explicit Non-Goals

server-core does not own Project-specific implementation/Design bodies, DebugAI internal orchestration, application-specific internals, reusable-KB data body/device layout, runtime log/cache data bodies, Secret/Token values, Workspace top-level bootstrap policy, executor-priority policy, operator-facing command interface, or worker-specific UI/session preferences that do not affect durable Server/Workspace operation.

## 16. Design Change Rule

This file is the server-core architecture baseline.

Formal changes require rationale, evidence, a traceable commit and an entry in `docs/DESIGN_DELTA.md`. Editorial cleanup belongs in normal Git history unless it changes the Design contract.
