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
- govern Server/Provider technical mutation and runtime-operation boundaries.

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

## 2026-09-30 — Return Project-specific Cloudflare implementation ownership to the owning Project

### Baseline design
server-core excludes Project-specific implementation bodies and runtime internals.

### Actual change
`docs/CLOUDFLARE_OPERATIONS.md` was changed from an application-specific Tunnel/Token/Container runbook into a Workspace-wide Cloudflare command contract.

server-core keeps routing, shared access contracts, mutation/verification boundaries and credential contract linkage. Project-specific hostnames, origins, Docker/Compose services, runtime credential injection and release procedures belong to the owning Project.

### Reason / root cause
A Workspace command center must not make one application's Cloudflare runtime details the Workspace-wide truth.

### Compatibility / rollback
No live Cloudflare resource or credential was changed by the documentation ownership correction.

## 2026-09-30 — Separate Project Integration from Shared Capability control

### Baseline design
Shared capability control existed, but Project-owned integration services were not clearly separated from Workspace-shared capability contracts.

### Actual change
The architecture separates Shared Capability contracts, Project-owned services such as TGserver/webhook gateway, and dual-boundary Libral Vault usage. `docs/PROJECT_INTEGRATION_RULES.md` is the common integration authority.

### Reason / root cause
Treating Project-owned systems as generic shared capabilities blurs owner, runtime and failure responsibility.

### Compatibility
No Project implementation moves. The change clarifies discovery/routing/contract ownership only.

## 2026-10-01 — Remove stale Project-specific Cloudflare/GPG operation assets from server-core

### Baseline
Project-specific Cloudflare implementation belongs to the owning Project; server-core keeps the common Cloudflare contract and shared access boundaries.

### Actual change
Stale Project-specific assets `operations/cloudflare.json` and `scripts/cloudflare_ops.py` were removed. The Cloudflare Cursor rule was rewritten as a Workspace-wide operation rule.

### Reason / root cause
Those files encoded a former application-specific runtime and credential path, contradicting current ownership and shared-credential architecture.

### Compatibility
No live Cloudflare resource or credential was changed. Git history retains the removed implementation.

## 2026-10-01 — Workspace-global MCP execution route

### Baseline
MCP was a Workspace shared capability, but the executable client route could vary by Project.

### Adopted design
Use Cursor User Global MCP (`~/.cursor/mcp.json`) as the Workspace-wide execution entry for server-core-managed shared remote MCPs. Project `.cursor/mcp.json` remains for Project-owned / Project-scoped MCPs.

Source of truth:
- `operations/workspace-mcp.json` — managed manifest without provider credential values;
- `scripts/install-workspace-mcp.sh` — gated merge into user-global config;
- `scripts/verify-workspace-mcp.sh` — scoped configuration verification;
- `docs/WORKSPACE_MCP.md` — state/permission/credential semantics.

Existing non-managed client entries and client-local credential containers may be preserved but are not adopted into server-core ownership or treated as live-auth evidence.

### Security / ownership
Client config and backups are protected with owner-only permissions and bounded backup retention. Credential values are not printed or copied into repository authority.

### Verification boundary
Configuration verification and Live availability are separate. `CONFIG_PRESENT` / `CONFIG_REGISTERED` is not equivalent to authentication, transport, interface discovery or representative-call PASS.

## 2026-10-01 — Separate durable capability state from transient live-verification progress

### Baseline
Earlier wording mixed durable implementation facts, historical usage, current client configuration and current exact-revision live verification.

### Actual change
Capability documentation separates implementation/source verified, config present/registered, historical live use, current runtime/client readback, current representative call and available verified.

### Reason / root cause
Implementation existence, past successful usage, current registration and current runtime health are different facts with different authorities and lifetimes.

### Compatibility
No capability implementation body, server service, provider setting or credential is changed by this documentation correction.

## 2026-10-01 — Remove transient and personal policy from server-core operational authority

### Baseline
Some server-core documents and Cursor rules had accumulated session-specific wording, personal approval labels, temporary project status, device-specific assumptions, and reasoning/language instructions unrelated to durable Workspace operation.

### Actual change
server-core Current Authority is limited to durable Workspace/Server operation contracts: Project/owner routing, context loading, development/reuse boundary, verification contract, GitHub work history, Server/Provider mutation boundary, credential safety, shared capability discovery/registration/availability semantics, and storage/deploy/recovery contracts.

### Reason / root cause
Transient instructions and short-lived work state are not stable server-core operating contracts.

### Compatibility / migration
Durable safety properties remain and Project-specific details remain with owning Project authority.

## 2026-10-02 — Make server-core mutation explicitly opt-in

### Baseline design
server-core already separated read-only inspection from mutation but did not state strongly enough that server-core itself requires a separate explicit authorization before any write.

### Actual change
server-core is formally read-only by default. Source, Document, Config, branch and commit mutation in server-core requires explicit owner authorization for server-core itself.

Operationally:
- `SERVER_CORE_MUTATION_AUTHORIZED=YES` is required before server-core enters `MUTATION_REPOSITORIES`;
- reading server-core or using its Runbooks does not authorize writes;
- finding a common-contract inconsistency does not authorize self-directed repair;
- another Project's work, failure investigation or Shared Capability use does not authorize server-core mutation.

### Reason / root cause
A command-center repository is consulted by many Project tasks. Reference scope and mutation scope must be independently locked.

### Compatibility / migration
Project work continues to read server-core as common routing authority. Existing Project ownership does not change.

## 2026-10-03 — Restore fixed server-workflow scope after execution-policy over-generalization

### Baseline design
The original command-center design required Workspace work to start from server-core and follow a repeatable routine through Project routing, required Authority, reuse, implementation/debug, verification, Documentation Gate, GitHub work history, approval boundary and optional Deploy/Runtime verification.

It explicitly did not depend on ChatGPT-only or Notion-only state.

### Problem found
PR #8 temporarily generalized this into a separate "Workspace top-level" execution-policy layer and introduced concepts such as GPT/operator interface ownership and generic UI/client execution routes.

That interpretation was broader than the server-core requirement and risked replacing the fixed server-side development routine with an abstract executor-policy architecture.

### Corrected design
The command center is restored to the original scope:
- server-core itself is the Workspace command entry for Server/Workspace workers;
- the fixed development routine remains `route -> authority -> Project -> reuse -> implement/debug -> verify -> documentation -> GitHub -> approval -> deploy/runtime when applicable`;
- technical execution routes are limited to Server/Workspace work: `DETERMINISTIC_LOCAL_OR_CI`, `SERVER_COMMAND`, `SERVER_AI`, `PROJECT_RUNTIME`;
- Chat UI, conversation formatting, Notion operation and external application interaction rules are not server-core execution routes;
- Server command safety remains in `docs/SERVER_COMMAND_CONTRACT.md`;
- useful PR #8 safety work is retained: explicit mutation ownership, server-core read-only default, concurrent change-unit isolation, same-target writer locks, partial-apply reporting, bounded diagnostics, state separation, MCP config hardening, Skill full-read/glob rejection and bounded storage audit;
- DebugAI-specific efficiency is narrow: reuse existing evidence/tool results before repeating the same investigation through Server AI. This is not a generic Workspace AI cost policy.

### Reason / root cause
server-core exists to make a non-expert-operated development environment repeatable and resistant to drift. Generalizing it into a conventional flexible executor-policy layer weakens that purpose and introduces rules that were not part of the original requirement.

### Affected scope
- `README.md`
- `.cursor/rules/00_agent_runtime.mdc`
- `docs/SERVER_CORE_DESIGN.md`
- `docs/G_ACE_WORKSPACE.md`
- `docs/LOAD_SCOPE.md`
- `docs/SERVER_COMMAND_CONTRACT.md`
- `operations/pre-execution-schema.json`
- `.github/workflows/server-core-guard.yml`
- `.github/workflows/server-core-behavior.yml`

### Applied commit / PR
PR #8, corrective commits on `docs/post-merge-state-cleanup-20261001`.

### Compatibility / migration / rollback
Project ownership, Shared Capability contracts, MCP hardening, helper safety, State Semantics and Runtime boundaries remain in place. The correction removes only the over-generalized authority layer and UI/client concepts that were not part of server-core's intended scope.

### Verification state
Repository guard and behavior CI must pass at the exact corrected branch HEAD. Current live Server/provider state remains a separate evidence domain.

## Update Rule

Append a new section only for an actual architecture/responsibility/authority change. Editorial correction, wording cleanup and current-runtime refresh belong in normal Git history unless they change the Design contract.
