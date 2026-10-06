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

## 2026-10-01 — Remove stale Project-specific Cloudflare/GPG operation assets from server-core

### Baseline
The 2026-09-30 Cloudflare ownership correction states that Project-specific Cloudflare implementation belongs to the owning Project, while server-core keeps only the Workspace command contract and shared access boundaries.

### Actual change
The remaining stale Astera-specific Cloudflare operation manifest and helper were removed from server-core:

- `operations/cloudflare.json`
- `scripts/cloudflare_ops.py`

The Cursor Cloudflare rule was rewritten as a Workspace-wide contract and no longer assumes Astera v8, GPG-Core, or a server-core Cloudflare runtime script.

### Reason / root cause
The previous ownership correction updated the documentation but left implementation assets that still encoded the former Astera-specific runtime and GPG-based credential path. Keeping those files would allow an AI to follow stale instructions despite the current Vault-based shared-secret architecture.

### Evidence
The removed manifest referenced `astera-v8-prod`, `api.asterav8.jp`, a Project-specific origin, and `GPG-Core`. The removed helper consumed that manifest and contained GPG-based secret handling. Current Workspace shared-secret authority is Libral Vault via `docs/WORKSPACE_SHARED_SECRETS.md` and `operations/cloudflare-account.json`.

### Affected scope
- `.cursor/rules/cloudflare-operations.mdc`
- `docs/CLOUDFLARE_OPERATIONS.md`
- `docs/STRUCTURE.md`
- `operations/cloudflare.json` (removed)
- `scripts/cloudflare_ops.py` (removed)
- `.github/workflows/server-core-guard.yml`

### Compatibility / rollback
No live Cloudflare resource or Secret was changed. Project-specific Cloudflare operations remain with the owning Project. Reintroducing the removed files as Current server-core assets would restore the stale ownership/credential boundary and is not compatible with the current Workspace contract.

### Verification state
The final branch/PR HEAD must pass `server-core-guard`. This change itself does not claim live Cloudflare, Vault, or Project runtime verification.

## Update rule

When a later architecture decision changes the server-core baseline, append a new section. Do not rewrite or delete prior accepted deltas merely because the current implementation changed.

## 2026-10-01 — Workspace-global MCP execution route

### Baseline
server-core already classified MCP / Cloudflare / Hugging Face as Workspace shared capabilities, but the executable Cursor route was still Project-dependent or only documented. This caused the known failure mode where one Project had an MCP registration/token path while another Project did not.

### Adopted design
Use Cursor User Global MCP (`~/.cursor/mcp.json`) as the Workspace-wide execution entry for shared remote MCPs. Project `.cursor/mcp.json` remains reserved for Project-owned or explicitly Project-scoped MCPs.

Source of truth:
- `operations/workspace-mcp.json` — shared MCP manifest without provider tokens;
- `scripts/install-workspace-mcp.sh` — safe merge into the user-global Cursor MCP config;
- `scripts/verify-workspace-mcp.sh` — config verification and optional Cursor CLI inspection;
- `docs/WORKSPACE_MCP.md` — contract and availability gate.

Current shared registrations:
- Cloudflare API MCP;
- Hugging Face official MCP.

### Security / ownership
- Provider credentials are not copied into Project repositories.
- OAuth-capable providers authenticate at the global MCP layer.
- Bearer-token providers must use the approved Workspace Secret / Libral Vault path; plaintext tokens remain outside Git and Project config.
- Existing unrelated user MCP servers are preserved.
- A name collision with a different definition fails closed rather than silently overriding an existing server.

### Initialization
`scripts/init-dev-workspace.sh` now invokes the shared MCP installer after establishing the common Workspace rules path. Therefore new Workspace initialization does not depend on each Project remembering to register the shared MCPs.

### Verification boundary
Source/CI verification confirms the manifest schema, installer shell syntax, documentation and registration contract. Actual server-side `~/.cursor/mcp.json`, OAuth authentication, transport, tool discovery and representative calls remain Runtime verification steps and are not claimed as complete until executed on the intended Cursor/Agent host.

### Deferred shared MCPs
DebugAI MCP and Deterministic Japanese Parser MCP are not globally registered yet because their intended live runtime/endpoint has not been verified. No path or endpoint is invented.

### Compatibility
Project-specific MCPs remain supported. Cursor project-level configuration may override a global server name; such overrides are prohibited by Workspace policy unless explicitly approved.

## 2026-10-01 — Separate durable capability state from transient live-verification progress

### Baseline design
Earlier wording mixed durable implementation facts, historical usage, current client configuration and current exact-revision live verification.

### Actual change
Capability documentation separates implementation/source verified, config present/registered, historical live use, current runtime/client readback, current representative call and available verified.

### Reason / root cause
Implementation existence, past successful usage, current registration and current runtime health are different facts with different authorities and lifetimes.

### Compatibility / migration / rollback
No capability implementation body, server service, provider setting or credential is changed by this documentation correction.

### Verification state
Repository CI verifies the state-separation contract. Current live availability remains task-time evidence.

## 2026-10-01 — Remove transient and personal policy from server-core operational authority

### Baseline design
Some server-core documents and Cursor rules had accumulated session-specific wording, personal approval labels, temporary project status, device-specific assumptions, and reasoning/language instructions unrelated to durable Workspace operation.

### Actual change
server-core Current Authority is limited to durable Workspace/Server operation contracts: Project/owner routing, context loading, development/reuse boundary, verification contract, GitHub work history, Server/Provider mutation boundary, credential safety, shared capability discovery/registration/availability semantics, and storage/deploy/recovery contracts.

### Reason / root cause
Transient instructions and short-lived work state are not stable server-core operating contracts.

### Compatibility / migration / rollback
Durable safety properties remain and Project-specific details remain with owning Project authority.

### Verification state
Retired/client-local/session-only material is excluded by repository guard checks.

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

### Compatibility / migration / rollback
Project work continues to read server-core as common routing authority. Existing Project ownership does not change.

### Verification state
Repository guard/behavior CI checks the explicit mutation gates and helper fail-closed behavior.

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
- generic executor-selection schema and UI/client execution routes are not part of server-core;
- Chat UI, conversation formatting, Notion operation and external application interaction rules are outside server-core;
- Server command safety remains in `docs/SERVER_COMMAND_CONTRACT.md` and does not become a general executor-policy layer;
- production residency remains Docker Compose; host-resident production paths are not introduced as Project-specific exceptions;
- useful PR #8 safety work is retained: explicit mutation ownership, server-core read-only default, concurrent change-unit isolation, same-target writer locks, partial-apply reporting, bounded diagnostics, state separation, MCP config hardening, Skill full-read/glob rejection and bounded storage audit;
- DebugAI-specific efficiency is narrow: reuse existing evidence/tool results before repeating the same investigation through Server AI. This is not a generic Workspace AI cost policy.

### Reason / root cause
server-core exists to make a non-expert-operated development environment repeatable and resistant to drift. Generalizing it into a conventional flexible executor-policy layer weakens that purpose and introduces rules that were not part of the original requirement.

### Evidence
Master required restoration of the original command-center purpose and rejected the generic executor/UI/operator interpretation. Reverse audit compared the current PR against the accepted baseline and restored removed routing/operation requirements while retaining safety hardening.

### Affected scope
- `README.md`
- `CORE.md`
- `SERVER_CORE_PROTOCOL.md`
- `.cursor/rules/00_agent_runtime.mdc`
- `docs/SERVER_CORE_DESIGN.md`
- `docs/G_ACE_WORKSPACE.md`
- `docs/LOAD_SCOPE.md`
- `docs/SERVER_COMMAND_CONTRACT.md`
- `docs/DEPLOY_RUNBOOK.md`
- `operations/pre-execution-schema.json`
- `.github/workflows/server-core-guard.yml`
- `.github/workflows/server-core-behavior.yml`

### Applied commit / PR
PR #8 corrective commits on `docs/post-merge-state-cleanup-20261001`.

### Compatibility / migration / rollback
Project ownership, Shared Capability contracts, MCP hardening, helper safety, State Semantics and Runtime boundaries remain in place. The correction removes only the over-generalized authority layer and UI/client concepts that were not part of server-core's intended scope.

### Verification state
Repository guard and behavior CI must pass at the exact corrected branch HEAD. Current live Server/provider state remains a separate evidence domain.

## 2026-10-03 — Make automatic server-core entry a Workspace AI requirement

### Baseline design
Cursor had an always-applied server-core runtime rule, but equivalent automatic entry for VS Code/Copilot and other compatible agents was not proven as a durable Workspace-wide contract.

### Actual change
A new chat/task in the G-ACE Workspace must enter through server-core without requiring Master to repeat the instruction each time.

The durable entry surfaces are:
- Cursor: `.cursor/rules/00_agent_runtime.mdc` with `alwaysApply: true`;
- VS Code / GitHub Copilot: `.github/copilot-instructions.md`;
- cross-agent compatible entry: `AGENTS.md`;
- `/home/admin1/projects` receives the shared Cursor/Copilot/AGENTS entry points through the canonical Workspace wiring;
- `scripts/workspace_command_center_check.py` verifies the links/settings and can repair them only under explicit Workspace-mutation authorization.

### Reason / root cause
The Workspace command-center purpose is not satisfied if Master must manually tell each new AI chat to read server-core. The command-center entry must be durable and automatic at the client/Workspace layer.

### Evidence
Master explicitly required Cursor/VS AI to check server-core at chat start even when no reminder is given. Source/config/CI can prove the intended wiring contract, while actual live client instruction consumption remains a separate Runtime/client evidence item.

### Affected scope
- `.cursor/rules/00_agent_runtime.mdc`
- `.github/copilot-instructions.md`
- `AGENTS.md`
- `docs/G_ACE_WORKSPACE.md`
- `docs/STRUCTURE.md`
- `scripts/init-dev-workspace.sh`
- `scripts/workspace_command_center_check.py`
- `.github/workflows/server-core-guard.yml`
- `.github/workflows/server-core-behavior.yml`

### Applied commit / PR
PR #8 corrective commits on `docs/post-merge-state-cleanup-20261001`.

### Compatibility / migration / rollback
Cursor's existing automatic rule remains. The change adds equivalent durable entry surfaces for VS/Copilot and cross-agent use without moving Project implementation into server-core.

### Verification state
Repository CI verifies the instruction files, Workspace wiring contract and regression guards. Current exact-head VPS wiring and actual Cursor/VS instruction consumption remain `NOT_VERIFIED` until live readback is performed.

## Update rule

When a later architecture decision changes the server-core baseline, append a new section. Do not rewrite or delete prior accepted deltas merely because the current implementation changed. Editorial correction, wording cleanup and current-runtime refresh belong in normal Git history unless they change the Design contract.

## 2026-10-03 — Unify fixed routine ownership and execution-cost routing

### Baseline design
server-core already contained the required development stages, but the executable routine was repeated across README, LOAD_SCOPE, Workspace, Protocol, Project Template and GitHub documents. CORE could be routed only when a task was explicitly classified as development-methodology work. DebugAI had discovery/state semantics, but its operational responsibility and cost priority were not fixed strongly enough. PR state existed separately from Commit/Push, but PR body freshness was not a completion gate.

### Actual change
The command-center contract is tightened without creating a new framework or new document owner:
- `docs/G_ACE_WORKSPACE.md` is the single owner of the fixed Workspace development routine;
- `docs/LOAD_SCOPE.md` always routes Workspace development through that routine and requires `CORE.md` for Source/Config/Test/API/Bug/connection/Feature/Debug changes;
- target Project startup is fixed as Project README -> Current GitHub state/Commit/PR -> required Design/history -> Source/Test;
- executor cost routing prefers existing verified evidence and deterministic checks first, then DebugAI for iterative design-check/investigation/test/verification/debug/retest work, then Workspace/Server AI, with high-cost AI reserved for unresolved special judgment;
- cost reduction may not remove required evidence, tests or workflow stages;
- Project Design keeps the original design text and appends formal change history below it; Design Delta supplements rather than replaces that preserved history;
- Open PRs must be checked and synchronized to the Current HEAD after Push/Remote Readback before GitHub work-history completion.

### Reason / root cause
A correct rule distributed across multiple documents can still be skipped when an AI decides only one document is relevant. The command center must make the execution path deterministic enough for a non-technical Master while retaining progressive context loading and avoiding unnecessary AI cost.

### Evidence
Master's server-core audit identified six concrete weaknesses: routine fragmentation, CORE bypass risk, Project startup ordering mismatch, DebugAI responsibility ambiguity, weak AI-cost routing, partial Design-history semantics and weak PR-current synchronization. Current exact-head readback confirmed each gap in the existing documents before this change.

### Affected scope
- `README.md`
- `docs/LOAD_SCOPE.md`
- `docs/G_ACE_WORKSPACE.md`
- `docs/PROJECT_TEMPLATE.md`
- `docs/AUTO_COMMIT.md`
- `docs/DESIGN_DELTA.md`

### Applied commit / PR
Applied by the same PR #8 change unit that introduces this delta. Exact commit is the GitHub commit containing this section.

### Compatibility / migration / rollback
- No Project implementation, Runtime, provider, Secret, service or production resource is changed.
- Existing specialized authorities remain owners of their domains; only routing and completion gates are strengthened.
- Progressive loading remains; this does not require loading all server-core documents.
- DebugAI availability still requires Current runtime/client evidence when needed and is never assumed from documentation alone.
- main merge and production operations remain separate Master approval boundaries.

### Verification state
Repository CI must pass on the exact resulting PR head. Live Workspace wiring was previously verified at `e7b7b700...`; because Source changes after that revision, exact-new-head live client instruction consumption and any runtime-dependent capability state remain separate evidence and are not implied by this documentation commit.


## 2026-10-06 — Add bounded GitHub Project #1 control operation

### Baseline design
server-core already owns Workspace GitHub operation governance, shared-capability discovery, mutation boundaries and Server command safety. The Current CHAT operating model moved development control toward GitHub Project #1, but the CHAT GitHub connector could not mutate Projects v2 fields. The only verified Project write path remained the VPS `gh project` credential, which forced Master to act as a manual command runner.

### Actual change
server-core now contains a narrowly scoped GitHub Project control operation:
- `operations/github-project-control.json` fixes the target to Personal Project #1 `G-ACE Development Platform`, owner `seigo-gace`, node ID `PVT_kwHODOQFoM4BEJII`;
- only Issue/PR items under `seigo-gace` or `G-ACE-inc` are accepted;
- only `Wave / Gate / Change Unit / Mutation Owner` may be changed;
- the helper accepts a structured `gace.github-project-control/v1` request, never an arbitrary shell command;
- the existing VPS `gh` authentication is the intended credential source; no GitHub Actions PAT is introduced by this Source change;
- same-target execution uses a non-blocking lock;
- the current value is read before mutation for idempotency and the exact item/field is read back through GraphQL after mutation;
- Source contract tests use a mock `gh` binary and do not touch the live Project.

This does **not** introduce a generic Workspace executor and does not move DebugAI product logic into server-core.

### Reason / root cause
GitHub Project #1 and its control fields had already been created and verified, but the CHAT connector had no Projects v2 mutation surface. Current Project records therefore still showed final item-edit / `NOT_VERIFIED_FROM_CHAT` gaps, and Master remained in the execution loop. Workspace search found no existing shared GitHub→VPS **executor trigger** suitable for this Project operation. After Notion reconciliation, the existing TGserver ZERO Search Bridge is recognized as an owner-only `GitHub Issue -> GitHub Actions -> Cloudflare Access -> Server API` transport pattern. That path is now a mandatory reuse candidate, but it does not currently prove invocation of the server-core Project runner.

### Evidence
- server-core Issue #10 is the Task Issue for this Change Unit;
- GitHub CLI requires `project` scope for Project operations;
- prior Project #1 VPS read/write evidence already proved that the existing VPS credential can perform Project operations;
- current Source adds the bounded contract, one-shot helper and CI regression coverage.

### Affected scope
- `operations/github-project-control.json`
- `scripts/github_project_control.py`
- `scripts/github_project_control_test.py`
- `.github/workflows/server-core-behavior.yml`
- `.github/workflows/server-core-guard.yml`
- `docs/WORKSPACE_REGISTRY.md`
- `docs/STRUCTURE.md`
- this Design Delta

### Verification state
`SOURCE_IMPLEMENTED` on Issue #10 branch. Exact-head CI, automatic GitHub→VPS trigger, current VPS credential readback, live Project mutation and CHAT-originated E2E remain separate evidence and are **NOT_VERIFIED** until completed.

### Compatibility / approval boundary
No main merge, Production activation, service restart/recreate, Secret/Provider mutation or live Project mutation is implied by this Source change. The comparison copy of Notion「Notion活用の大原則」is not modified by this Change Unit.
