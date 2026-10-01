# SERVER CORE DESIGN DELTA

## Purpose

This document records intentional changes from the `docs/SERVER_CORE_DESIGN.md` baseline without erasing the previous design history.

A Design Delta is required when server-core architecture, responsibility, authority routing, shared-capability boundary, or command-center behavior is formally changed.

It is not a daily work log. Chronological work history remains in GitHub commit / PR.

## Required fields

Each accepted delta records:
- Baseline design
- Actual change
- Reason / root cause
- Evidence
- Affected scope
- Applied commit
- Compatibility / migration / rollback considerations
- Verification state

## 2026-09-30 — Formalize server-core as the G-ACE Workspace command center

### Baseline design
server-core was described primarily as the Workspace common development/operations control layer and common authority entry point.

### Actual change
The role is formally clarified as the **G-ACE Workspace command center**.

The command-center responsibility is explicitly defined as:
- receive and route tasks;
- determine target Project / authority;
- control progressive context loading;
- dispatch work to the owning Project;
- expose shared MCP / Tool / Secret / KB capabilities through explicit contracts;
- enforce common development, verification and documentation rules;
- preserve GitHub work history;
- govern approval and runtime-operation boundaries.

server-core still does not absorb Project-specific implementation or runtime internals.

### Reason / root cause
The earlier wording was technically compatible but too weak: it could be interpreted as a passive rule/document repository. The intended architecture requires server-core to be the active common command point from which Workspace AI/developer work is routed and governed.

### Evidence
- Master explicitly clarified that server-core's role is equivalent to a command room / command center for the Workspace.
- Existing README / LOAD_SCOPE / Workspace routing already implemented server-core-first routing, so the formal design wording strengthens and formalizes the intended responsibility rather than creating a second orchestration layer.

### Affected scope
- `README.md`
- `SERVER_CORE_PROTOCOL.md`
- `docs/SERVER_CORE_DESIGN.md`
- `docs/DESIGN_DELTA.md`
- `docs/LOAD_SCOPE.md`
- `docs/G_ACE_WORKSPACE.md`
- `docs/WORKSPACE_REGISTRY.md`
- `docs/WORKSPACE_SHARED_SECRETS.md`
- `docs/KB_REUSE_DESIGN.md`
- `docs/STORAGE_LIFECYCLE.md`
- `docs/GLOSSARY.md`
- `docs/STRUCTURE.md`
- `.github/workflows/server-core-guard.yml`

### Applied commit
Formal Design baseline change commit:

```text
d88e99273319dad1b27092e14085c7060710fc92
```

Supporting consistency updates are tracked by the same branch/PR and GitHub history.

### Compatibility / migration / rollback
- No Project implementation is moved into server-core.
- Existing Project README-first entry remains valid after routing.
- Existing LibralCore, GitHub, Secret, KB and Storage authorities remain valid.
- The change strengthens responsibility wording and command flow; it does not require a runtime migration.
- Rollback would restore weaker control-layer wording but would reintroduce ambiguity about Workspace ownership/routing.

### Verification state
The acceptance gate is `server-core-guard` on the final branch/PR HEAD. The CI result is the verification evidence; this Design Delta does not copy a mutable CI status into the architecture baseline.

## 2026-09-30 — Return Project-specific Cloudflare implementation ownership to the owning Project

### Baseline design
`docs/SERVER_CORE_DESIGN.md` defines server-core as the Workspace command center and explicitly excludes Project-specific implementation bodies and runtime internals.

### Actual change
`docs/CLOUDFLARE_OPERATIONS.md` is changed from an Astera v8-specific Tunnel/Token/Container runbook into a Workspace-wide Cloudflare command contract.

server-core keeps only:
- routing;
- shared access paths;
- approval boundary;
- provider verification contract;
- Secret boundary;
- common tooling entry.

Project-specific hostnames, origins, Docker/Compose services, runtime secret paths and release procedures belong to the owning Project.

### Reason / root cause
The old document made server-core the authority for a specific Application's Cloudflare runtime details. That contradicted the command-center responsibility boundary and could cause stale Project runtime facts to be treated as Workspace-wide truth.

### Evidence
The previous file contained Astera-specific hostname, origin port, tunnel name, container, token path and release gates while the server-core baseline says Project-specific runtime implementation remains owned by the target Project.

### Affected scope
- `docs/CLOUDFLARE_OPERATIONS.md`
- `docs/WORKSPACE_REGISTRY.md`
- Cloudflare task routing through `docs/LOAD_SCOPE.md`

### Applied commit
Cloudflare authority correction commit:

```text
af9abd3e9d402f73430d7c97f270463a62f75f18
```

### Compatibility / migration / rollback
- Git history retains the former Astera-specific runbook as historical evidence.
- No live Cloudflare resource is changed by this documentation correction.
- Astera-specific live values must be read from the owning Project/current provider state before use.
- Restoring the old server-core file as Current Authority would reintroduce ownership ambiguity and stale-runtime risk.

### Verification state
The final branch/PR must pass `server-core-guard`. Live Cloudflare runtime is not modified or claimed verified by this documentation change.

## 2026-09-30 — Separate Project Integration Contracts from Shared Capability Registry

### Baseline design
The command-center baseline defined shared capability control but did not explicitly distinguish Project-owned integration services from Workspace-shared capabilities.

### Actual change
The architecture now explicitly separates:

- Shared Capability: DebugAI, MCP, KB, GitHub, Cloudflare, Hugging Face, Runtime確認, Libral Vault, Workspace Registry, Monitoring, Backup / Recovery, Search / Index.
- Project Integration: TGserver and webhook gateway.
- Dual boundary: Libral Vault remains a Shared Capability while Project-specific consumer / injection / runtime usage is governed by the Project Integration contract.

`docs/PROJECT_INTEGRATION_RULES.md` is the common integration authority for TGserver / webhook gateway / Vault / MCP / Tool adoption by a Project.

### Reason / root cause
TGserver and webhook gateway are existing Project-owned systems. Treating them as generic shared capabilities would blur service ownership. Vault must remain centrally governed because Secret safety is Workspace-wide while usage is Project-specific.

### Evidence
- server-core Design requires Project-specific implementation to remain with the owning Project.
- The Workspace Registry identifies TGserver and webhook gateway as Projects.
- A separate integration contract is therefore required for common adoption rules.

### Affected scope
- `README.md`
- `docs/SERVER_CORE_DESIGN.md`
- `docs/LOAD_SCOPE.md`
- `docs/G_ACE_WORKSPACE.md`
- `docs/STRUCTURE.md`
- `docs/WORKSPACE_REGISTRY.md`
- `docs/PROJECT_TEMPLATE.md`
- `docs/PROJECT_INTEGRATION_RULES.md`

### Applied commit
This delta is applied by the synchronization commit that updates the command-center documentation set.

### Compatibility / migration / rollback
- No TGserver or webhook gateway implementation is moved.
- No Vault Secret value or live Secret registration is changed.
- Existing Project integrations remain Project-owned.
- The change clarifies discovery/routing/contract ownership only.

### Verification state
The branch/PR must pass `server-core-guard` and documentation synchronization checks. Runtime availability remains separate from documentation completion.

## Update rule

When a later architecture decision changes the server-core baseline, append a new section. Do not rewrite or delete prior accepted deltas merely because the current implementation changed.