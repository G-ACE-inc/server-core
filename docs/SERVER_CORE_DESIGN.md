# SERVER CORE DESIGN

Version: 2026-10-03
Status: Design Baseline

## 1. Purpose

`server-core` is the **G-ACE Workspace command center**.

Its role is not to implement every Project. Its role is to receive a task, determine the correct Project and authority, control what information must be loaded, expose shared capabilities safely, enforce common development and verification rules, preserve GitHub work history, and govern the path from verified source to approved runtime operation.

Every AI / developer working inside the G-ACE Workspace must be able to start from server-core and determine **where to work, what to read, what may be reused, what must be verified, what must be recorded, and which approval boundary must not be crossed**.

The command center is specifically designed so that **a non-technical Master does not have to repeatedly make routine Server, resource, development-procedure, or verification judgments for the AI**. Workspace AI must obtain the durable Server/Workspace information, available-resource discovery routes, operating rules, development method and fixed work routine from server-core, then apply them without silently replacing them with conventional generic development practice or dropping required steps.

Workspace work must also be recoverable from server-core without depending on temporary conversation history or session-only state.

The design assumes a fixed, repeatable workflow so work does not drift merely because the worker changes.

## 2. Command Center Responsibilities

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

The implementation body stays with its owning Project/runtime. server-core owns discovery, connection contract, owner, permission boundary and availability / verification state.

Project-owned services such as TGserver / webhook gateway remain Project integrations unless ownership is formally changed. Common integration rules are defined by `docs/PROJECT_INTEGRATION_RULES.md`.

### 2.5 Development / Verification Governance
server-core defines Workspace-wide rules for:
- reuse-first development;
- README / Design / Project Tree / Design Delta / System Document responsibilities;
- verification and failure-case requirements;
- documentation gate;
- GitHub work-report commits;
- state separation between Source, Test, Commit, Push, PR, CI, Merge, Deploy, Runtime and Production.

### 2.6 Repository Mutation Ownership
server-core distinguishes the task repository from repositories opened only for reference.

```text
TARGET_REPOSITORY
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
SERVER_CORE_MUTATION_AUTHORIZED
```

Reading a repository, using its Runbook, or discovering an integration dependency does not grant write permission.

server-core itself is read-only unless server-core mutation is explicitly authorized for the current task/change unit.

### 2.7 Runtime / Operations Governance
server-core governs the common operational boundary for:
- deployment from confirmed GitHub revision;
- Docker Compose production residency;
- runtime verification;
- log / cache / temporary-state lifecycle;
- cleanup safety;
- backup / recovery;
- resource-pressure policy;
- Server command technical safety.

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

This is the default fixed routine. A required step is not skipped merely because a worker believes it is probably unnecessary; omission needs a task-specific reason consistent with the applicable authority.

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

### System / Feature-bundle Documents
Create or update technical documentation only when README alone cannot hand the completed unit to another AI/developer reliably.

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

## 6. DebugAI Reuse Boundary

DebugAI is a shared debugging capability with its implementation owned by the DebugAI Project.

When a Task uses DebugAI, existing verified evidence, prior tool results and prior verified state are reused before repeating the same investigation through Server AI.

This rule is specific to avoiding duplicate DebugAI investigation. It is not a generic Workspace executor-selection or AI-cost policy.

## 7. Verification Contract

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

Configuration presence, registration, authentication, transport, interface discovery, representative call and current availability remain separate evidence states where relevant.

## 8. Documentation Gate

Before work is documentation-complete, determine:

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Required documentation that is not updated keeps the work incomplete.

Documentation belongs to the target Project unless the task explicitly authorizes server-core changes.

## 9. GitHub Work Report / Concurrency

Commit / PR is the chronological work-history authority.

Where applicable, a commit must allow later readers to identify purpose, material changes, affected scope, verification, documentation updated, and remaining / unverified work.

Multiple Projects/agents/change units may be active concurrently. A helper must not stage or overwrite unrelated working-tree changes. Same-target writers must serialize or fail closed when the shared state cannot safely accept concurrent mutation.

Commit text does not replace Design Delta when a design difference must be preserved.

## 10. Shared Capability Registry

`docs/WORKSPACE_REGISTRY.md` is the command-center discovery registry.

Registry entries are navigation and contract data, not proof that the current runtime is healthy and not mutation permission.

## 11. Knowledge Base

Reusable-development KB data lives outside server-core. server-core owns only access, registration, lifecycle and safety contracts. KB data itself is not stored in this repository.

Server-side or Workspace access must use an explicit verified bridge such as API/MCP; never assume the VPS can directly read a PC drive.

Authority: `docs/KB_REUSE_DESIGN.md`.

## 12. Secret / Token Boundary

Secret / Token values are never a server-core document or Git authority.

server-core may own provider/purpose identifiers, consumer, broker route, allowlist/use contract, verification/failure behavior and change boundary.

Authority: `docs/WORKSPACE_SHARED_SECRETS.md`.

## 13. Server Operations

The server is a runtime / processing environment, not a replacement for GitHub source history.

Production-resident services use **Docker Compose as the canonical production residency path**. Host-resident `node`, `python`, `npm start`, `pm2`, `nohup`, `screen`, `tmux`, or equivalent processes are not adopted as production residency paths.

Common lifecycle boundaries are defined by `docs/STORAGE_LIFECYCLE.md`; deployment by `docs/DEPLOY_RUNBOOK.md`; Server command technical safety by `docs/SERVER_COMMAND_CONTRACT.md`.

Automated cleanup is fail-closed. Active state, unshipped data, retry state, recovery data, unknown ownership and active/persistent volumes are not generic deletion targets.

Read-only inspection may still have I/O cost and is bounded where appropriate. Reversible local Git operations such as fetch/temporary checkout/switch are not called pure read-only merely because final state is restored.

## 14. Command-Center Invariants

The following must always remain true:
- Workspace work starts from server-core and follows the fixed development routine;
- Workspace work can start and recover from server-core without temporary conversation history or session-only state;
- routine technical decisions are derived from server-core so the non-technical Master is not required to restate Server information, resource locations, development method or verification steps for every task;
- server-core determines routing but does not take ownership of Project internals;
- the fixed development routine is not replaced by ad-hoc worker preference;
- the same fact has one intended authority;
- context loading is progressive;
- shared capabilities have explicit owner and availability / verification state;
- Project-owned services are not reclassified as Shared Capabilities merely because they have multiple consumers;
- authority/responsibility ownership is not mutation permission;
- server-core is read-only without explicit server-core mutation authorization;
- concurrent change units are not mixed;
- Secret values never enter Git/docs/logs;
- design history is not erased to match implementation;
- work history is retained in GitHub;
- unverified states are not promoted to PASS;
- approval boundaries are not crossed implicitly;
- external execution is not claimed without returned evidence.

## 15. Explicit Non-Goals

server-core does not own:
- Project-specific implementation bodies;
- Project-specific Design bodies;
- DebugAI internal orchestration;
- application-specific internals;
- KB data;
- runtime log/cache data;
- Secret/Token values.

## 16. Design Change Rule

This file is the server-core architecture baseline.

Do not silently rewrite it to follow implementation drift. Formal changes require rationale, evidence and an entry in `docs/DESIGN_DELTA.md`, plus a traceable commit.
