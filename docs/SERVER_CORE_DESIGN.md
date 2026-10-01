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