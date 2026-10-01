# SERVER CORE DESIGN DELTA

## Purpose

This document records intentional changes from `docs/SERVER_CORE_DESIGN.md` without turning the Design baseline into a chronological work log.

A Design Delta is required when server-core architecture, responsibility, authority routing, shared-capability boundary, or command-center behavior is formally changed.

GitHub commit / PR remains the chronological work-history authority.

## Required fields

Each accepted delta records, as applicable:
- Baseline design
- Actual change
- Reason / root cause
- Evidence
- Affected scope
- Applied commit / PR
- Compatibility / migration / rollback considerations
- Verification state

Transient session notes, personal instructions, temporary Branch/HEAD status and current-task progress are not Design Delta authority.

## 2026-09-30 — Formalize server-core as the G-ACE Workspace command center

### Baseline design
server-core was described primarily as the Workspace common development/operations control layer and common authority entry point.

### Actual change
The role is formally clarified as the **G-ACE Workspace command center**.

Command-center responsibilities:
- receive and route tasks;
- determine target Project / authority;
- control progressive context loading;
- dispatch work to the owning Project;
- expose shared MCP / Tool / credential / KB capabilities through explicit contracts;
- enforce common development, verification and documentation boundaries;
- preserve GitHub work history;
- govern Server/Provider mutation and runtime-operation boundaries.

server-core does not absorb Project-specific implementation or runtime internals.

### Reason / root cause
The earlier wording was compatible with the intended architecture but too weak and could be interpreted as a passive rule/document repository. The Workspace requires one stable routing and governance entry point.

### Evidence
README / LOAD_SCOPE / Workspace routing already followed server-core-first routing. The design change formalized that operational role rather than creating a second orchestration layer.

### Affected scope
- `README.md`
- `SERVER_CORE_PROTOCOL.md`
- `docs/SERVER_CORE_DESIGN.md`
- `docs/DESIGN_DELTA.md`
- `docs/LOAD_SCOPE.md`
- `docs/G_ACE_WORKSPACE.md`
- `docs/WORKSPACE_REGISTRY.md`
- related operation contracts and CI guards

### Applied commit
`d88e99273319dad1b27092e14085c7060710fc92`

### Compatibility / rollback
- Project implementations remain Project-owned.
- Project README-first dispatch remains valid.
- No runtime migration is implied by the wording change.
- Rolling back would reintroduce ambiguity about Workspace routing ownership.

### Verification state
Acceptance is verified by repository CI and applicable server readback; mutable CI result text is not copied into the Design baseline.

## 2026-09-30 — Return Project-specific Cloudflare implementation ownership to the owning Project

### Baseline design
server-core excludes Project-specific implementation bodies and runtime internals.

### Actual change
`docs/CLOUDFLARE_OPERATIONS.md` was changed from an application-specific Tunnel/Token/Container runbook into a Workspace-wide Cloudflare command contract.

server-core keeps:
- routing;
- shared access contracts;
- mutation/verification boundaries;
- credential contract linkage.

Project-specific hostnames, origins, Docker/Compose services, runtime credential injection and release procedures belong to the owning Project.

### Reason / root cause
A Workspace command center must not make one application's Cloudflare runtime details the Workspace-wide truth.

### Evidence
The former server-core document contained application-specific hostname, origin, tunnel, container and credential-path details while the Design assigns such implementation to the target Project.

### Applied commit
`af9abd3e9d402f73430d7c97f270463a62f75f18`

### Compatibility / rollback
No live Cloudflare resource was changed by the documentation ownership correction. Reintroducing Project-specific runtime values as server-core Current Authority would restore stale-runtime risk.

## 2026-09-30 — Separate Project Integration from Shared Capability control

### Baseline design
Shared capability control existed, but Project-owned integration services were not clearly separated from Workspace-shared capability contracts.

### Actual change
The architecture separates:
- Shared Capability contracts: reusable MCP/Tool interfaces, DebugAI access, reusable KB access, GitHub/provider/shared credential interfaces, monitoring/recovery interfaces where shared;
- Project Integration: Project-owned services such as TGserver and webhook gateway;
- Dual boundary: Libral Vault remains a Shared Capability while Project-specific consumer/injection/runtime usage is an integration concern.

`docs/PROJECT_INTEGRATION_RULES.md` is the common integration authority.

### Reason / root cause
Treating Project-owned systems as generic shared capabilities blurs owner, runtime and failure responsibility.

### Compatibility
No Project implementation moves. The change clarifies discovery/routing/contract ownership only.

## 2026-10-01 — Remove stale Project-specific Cloudflare/GPG operation assets from server-core

### Baseline
Project-specific Cloudflare implementation belongs to the owning Project; server-core keeps the common Cloudflare contract and shared access boundaries.

### Actual change
Stale Project-specific assets were removed:
- `operations/cloudflare.json`
- `scripts/cloudflare_ops.py`

The Cloudflare Cursor rule was rewritten as a Workspace-wide operation rule.

### Reason / root cause
Those files still encoded a former application-specific runtime and credential path, contradicting the current ownership and shared-credential architecture.

### Evidence
The removed manifest/helper contained application-specific runtime identifiers and obsolete credential handling. Current Workspace Account API contract is `operations/cloudflare-account.json`; Project-specific Tunnel credential ownership remains with the owning Project.

### Compatibility
No live Cloudflare resource or credential was changed. Git history retains the removed implementation as historical evidence.

## 2026-10-01 — Workspace-global MCP execution route

### Baseline
MCP was a Workspace shared capability, but the executable client route could vary by Project.

### Adopted design
Use Cursor User Global MCP (`~/.cursor/mcp.json`) as the Workspace-wide execution entry for server-core-managed shared remote MCPs. Project `.cursor/mcp.json` remains for Project-owned / Project-scoped MCPs.

Source of truth:
- `operations/workspace-mcp.json` — managed manifest without provider credentials;
- `scripts/install-workspace-mcp.sh` — safe merge into the user-global config;
- `scripts/verify-workspace-mcp.sh` — configuration verification;
- `docs/WORKSPACE_MCP.md` — state semantics and live-verification contract.

Current server-core-managed entries:
- Cloudflare API MCP;
- Hugging Face MCP.

Existing non-managed user/client MCP entries are preserved and are not automatically adopted into server-core ownership.

### Security / ownership
- Provider credential values are not copied into Project repositories or the manifest.
- Credential use follows the appropriate OAuth or Workspace broker contract.
- A managed-name collision with a different runtime definition fails closed.

### Verification boundary
Configuration verification and Live availability are separate. `CONFIG_PRESENT` / `CONFIG_REGISTERED` is not equivalent to authentication, transport, interface discovery or representative-call PASS.

Project-owned MCPs such as DebugAI or Deterministic Japanese Parser remain owned by their Projects even if a client/global entry exists.

## 2026-10-01 — Separate durable capability state from transient live-verification progress

### Baseline
Earlier wording mixed durable implementation facts, historical usage, current client configuration and current exact-revision live verification. That made an implemented capability appear absent when only a fresh live check was pending.

### Actual change
Capability documentation now separates at least these concepts:

```text
IMPLEMENTATION / SOURCE VERIFIED
CONFIG PRESENT / REGISTERED
HISTORICAL LIVE USE
CURRENT RUNTIME / CLIENT READBACK
CURRENT REPRESENTATIVE CALL
AVAILABLE VERIFIED
```

For DebugAI MCP, server-core records that implementation/protocol verification and historical live use exist, while Current availability is read back when a Task requires it. server-core does not freeze a changing Project Branch/HEAD or per-task verification sequence into the Workspace Design.

### Reason / root cause
Implementation existence, past successful usage, current registration and current runtime health are different facts with different authorities and lifetimes.

### Evidence
`docs/WORKSPACE_MCP.md` and `docs/WORKSPACE_REGISTRY.md` now use separate state semantics and assign current runtime/client readback to the owning Project/client path.

### Compatibility
No DebugAI implementation body, server service, provider setting or credential is changed by this documentation correction.

## 2026-10-01 — Remove transient and personal policy from server-core operational authority

### Baseline
Some server-core documents and Cursor rules had accumulated session-specific wording, personal approval labels, temporary project status, device-specific assumptions, and reasoning/language instructions unrelated to durable Workspace operation.

### Actual change
server-core Current Authority is limited to durable Workspace/Server operation contracts:
- Project/owner routing;
- context loading;
- development/reuse boundary;
- verification contract;
- GitHub work history;
- Server/Provider mutation boundary;
- credential safety;
- shared capability discovery/registration/availability semantics;
- storage/deploy/recovery contracts.

Removed or generalized:
- personal names/titles as approval-policy identifiers;
- session-specific completion or prohibition wording;
- reasoning/language instructions unrelated to server operation;
- per-task/branch progress copied into durable docs;
- device-specific KB storage path as a server-core invariant;
- Project-specific storage products presented as Workspace-wide storage authorities.

### Reason / root cause
Transient instructions and short-lived work state are not stable server-core operating contracts. Keeping them in always-applied rules or Current Authority causes scope creep, stale facts and over-interpretation.

### Evidence
Repository-wide audit of README, Protocol, Design, Load Scope, Workspace, Registry, MCP, Secret, Deploy, Storage, KB, Structure and Cursor rules identified these categories and corrected them on the post-merge documentation cleanup branch.

### Compatibility / migration
- Server runtime implementation is unchanged by this documentation/rule hygiene change.
- Durable safety properties remain: no credential persistence, no inferred PASS, explicit ownership, explicit mutation boundary, verified source/runtime separation.
- Project-specific details remain available from the owning Project authority.

## Update Rule

Append a new section only for an actual architecture/responsibility/authority change. Editorial correction, wording cleanup and current-runtime refresh belong in normal Git history unless they change the Design contract.
