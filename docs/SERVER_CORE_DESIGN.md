# SERVER CORE DESIGN

Version: 2026-10-01
Status: Design Baseline

## 1. Purpose

`server-core` is the **G-ACE Workspace command center**.

Its role is not to implement every Project. Its role is to route work to the correct owner and authority, expose shared capabilities through explicit contracts, enforce common development and verification boundaries, preserve GitHub work history, and define the path from verified source to controlled runtime operation.

A worker starting from server-core must be able to determine:
- where the work belongs;
- what authority must be read;
- which shared capability may be reused;
- how the result is verified;
- what state is current vs historical;
- which mutation/approval boundary applies.

## 2. Command Center Responsibilities

### 2.1 Intake / Routing
- classify the task by purpose;
- identify the target Project / repository / runtime domain;
- identify the minimum server-core authority required;
- dispatch to the owning Project README and Project-specific authority.

### 2.2 Authority / Context Control
- `README.md` is the command-center entry point;
- `docs/LOAD_SCOPE.md` is the task router and context-loading authority;
- server-core authorities are loaded only when needed;
- Project work starts from the target Project README;
- archive, build output, dependency caches, logs, backups and unrelated repositories are excluded from normal context unless the task explicitly targets them.

### 2.3 Project Dispatch
server-core determines **where work belongs**. Project-specific source, design, tests and runtime logic remain in that Project.

server-core must not absorb Project implementation merely because the Workspace routes work through server-core.

### 2.4 Shared Capability Control
server-core provides the discovery and use contract for Workspace-shared capabilities such as:
- MCP;
- developer tools / skills;
- DebugAI;
- reusable KB access;
- GitHub operations;
- shared Secret / credential broker contracts;
- Provider contracts such as Cloudflare / Hugging Face;
- monitoring / backup / recovery interfaces where shared.

The implementation body stays with its owning Project/runtime. server-core owns discovery, owner, connection contract, permission/change boundary and verification method.

### 2.5 Development / Verification Governance
server-core defines Workspace-wide rules for:
- reuse-first development;
- README / Design / Project Tree / Design Delta / System Document responsibilities;
- verification and failure-case requirements;
- documentation gate;
- GitHub work-history commits;
- state separation between Source, Test, Commit, Push, PR, CI, Merge, Deploy, Runtime and Production.

### 2.6 Runtime / Operations Governance
server-core governs the common operational boundary for:
- deployment from a confirmed GitHub revision;
- Docker / Docker Compose production residency as the default;
- runtime verification;
- log / cache / temporary-state lifecycle;
- cleanup safety;
- backup / recovery;
- provider mutation and credential safety contracts.

Project-specific runtime implementation remains owned by the target Project.

## 3. Command Flow

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
  -> GitHub work-history commit
  -> push / remote readback / PR / CI as required
  -> required mutation / approval boundary
  -> deploy / runtime verification when applicable
```

A later state must never be inferred from an earlier PASS.

## 4. Authority Model

### README
README is the current command entry. It is not the design baseline and not a chronological work log.

It should provide direct navigation to applicable Design, Tree, Delta, System documentation, run/test/verify entry points and Current operational boundaries.

### Design
Design preserves architecture, contract, responsibility and boundary baseline.

A formal architecture change requires rationale and a Design Delta; implementation drift alone is not a reason to rewrite the baseline silently.

### Design Delta
When architecture or responsibility intentionally differs from the baseline Design, record:
- baseline design;
- actual change;
- reason / root cause;
- evidence;
- affected scope;
- applied commit;
- compatibility / migration / rollback considerations;
- verification state.

### Project Tree
Project Tree is a navigation index, not a raw file dump. It records meaningful files/directories, responsibility, entry points and related authority.

### System / Feature-bundle Documents
Create or update technical documentation when README alone cannot reliably hand the completed unit to another worker. Documentation should describe operationally relevant architecture, interfaces, dependencies, state ownership, failure/recovery, security, runtime and verification as needed—without empty template sections or transient work history.

## 5. Shared Capability vs Project Integration

Workspace-shared capability control includes reusable interfaces such as MCP, DebugAI, KB access, GitHub operations, Cloudflare/Hugging Face shared access, Vault/credential broker contracts, monitoring and recovery interfaces.

Project-owned systems such as TGserver or webhook gateway remain Project integrations unless their ownership is formally changed. Common adoption rules are in `docs/PROJECT_INTEGRATION_RULES.md`.

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

New code, module, tool or document should not be created before the relevant existing asset is checked.

## 7. Verification Contract

PASS is based on the evidence required by the task, including as applicable:
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

## 8. Documentation Gate

Before work is documentation-complete, determine whether the change affects:
- README Current entry;
- Project Tree / navigation;
- Design / Design Delta;
- an existing or new System/Module document.

Only documentation required by the actual change should be updated. The gate is not a requirement to generate extra documents.

## 9. GitHub Work History

Commit / PR is the chronological work-history authority.

Where applicable, a commit should allow later readers to identify purpose, material changes, affected scope, verification, documentation impact and remaining/unverified work.

Commit text does not replace Design Delta when a design difference must be preserved.

## 10. Shared Capability Registry

`docs/WORKSPACE_REGISTRY.md` is the discovery registry.

It records:
- Project -> repository -> known Workspace/server entry;
- shared MCP / tools;
- Secret Contract identifiers, never values;
- capability owner;
- connection/config authority;
- verification/readback method;
- runtime-discovery boundary.

Registry entries are navigation and contract data, not proof that the current runtime is healthy.

## 11. Reusable Knowledge Boundary

Reusable-development KB data lives outside server-core.

server-core owns only discovery, access/bridge contract, registration contract, lifecycle/safety rules and availability state. The storage implementation, device/path and data body belong to the KB owner/runtime and are not server-core invariants.

Authority: `docs/KB_REUSE_DESIGN.md`.

## 12. Secret / Credential Boundary

Secret / Token / credential values are never server-core document or Git authority.

server-core may own:
- provider / purpose;
- secret identifier;
- consumer;
- broker / Vault route;
- allowlist and use contract;
- verification and failure behavior;
- rotation/change boundary.

Authority: `docs/WORKSPACE_SHARED_SECRETS.md`.

## 13. Server Operations

The server is a runtime / processing environment, not a replacement for GitHub source history.

Production-resident services use Docker / Docker Compose unless a formally defined Project exception exists.

Common lifecycle boundaries are defined by `docs/STORAGE_LIFECYCLE.md`; deployment boundary is defined by `docs/DEPLOY_RUNBOOK.md`.

Automated cleanup is fail-closed. Active state, unshipped/retry data, recovery data, unknown ownership and persistent volumes are not generic deletion targets.

## 14. Command-Center Invariants

The following must remain true:
- Workspace work can start from server-core using repository/runtime authorities;
- server-core determines routing but does not take ownership of Project internals;
- the same operational fact has one intended authority;
- context loading is progressive;
- shared capabilities have explicit owner, connection and verification boundaries;
- credential values do not enter Git, Source, Document or Log;
- design history is not erased to match implementation;
- work history is retained in GitHub;
- unverified states are not promoted to PASS;
- mutation boundaries are explicit and authority-based.

## 15. Explicit Non-Goals

server-core does not own:
- Project-specific implementation bodies;
- Project-specific Design bodies;
- DebugAI internal orchestration;
- application-specific internal specifications;
- reusable-KB data body or device-specific storage layout;
- runtime log/cache data bodies;
- Secret/Token values;
- worker-specific interface/session preferences that do not affect Server or Workspace operation.

## 16. Design Change Rule

This file is the server-core architecture baseline.

Formal changes require rationale, evidence, a traceable commit and an entry in `docs/DESIGN_DELTA.md`. Editorial cleanup that does not change architecture belongs in normal Git history rather than a new architecture decision.
