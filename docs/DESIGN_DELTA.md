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
- the initial implementation feature-probed the name-based `gh project item-edit --owner / --url / --field / --value` surface, but Fresh VPS evidence proved the installed `gh 2.52.0` does not support that contract; the Current compatibility correction removes that mutation dependency, resolves the exact Project field id/type through `gh api graphql`, uses `updateProjectV2ItemFieldValue` for bounded text/single-select updates, and fails closed on missing/ambiguous/unsupported field metadata;
- same-target execution uses a non-blocking lock;
- the current value is read before mutation for idempotency and the exact item/field is read back through GraphQL after mutation;
- `.github/workflows/github-project-control-request.yml` reuses the existing owner-only GitHub control-plane pattern: a `[GACE-PROJECT]` comment from `seigo-gace` is converted into a deterministic fixed-schema request, validated through the same Project contract, stored as one-day evidence, and commented back as `PROJECT_CONTROL_EXECUTION=NOT_RUN`;
- comment input cannot supply a request id, actor, operation, command, Project identity, arbitrary URL endpoint, or credential; unknown keys and secret-like values fail closed;
- Source contract tests use a mock `gh` binary and do not touch the live Project.

This does **not** introduce a generic Workspace executor and does not move DebugAI product logic into server-core.

### Reason / root cause
GitHub Project #1 and its control fields had already been created and verified, but the CHAT connector had no Projects v2 mutation surface. Current Project records therefore still showed final item-edit / `NOT_VERIFIED_FROM_CHAT` gaps, and Master remained in the execution loop. Workspace search found no existing shared GitHub→VPS **executor trigger** suitable for this Project operation. After Notion reconciliation, the existing TGserver ZERO Search Bridge is recognized as an owner-only `GitHub Issue -> GitHub Actions -> Cloudflare Access -> Server API` transport pattern. That path is now a mandatory reuse candidate, but it does not currently prove invocation of the server-core Project runner.

### Evidence
- server-core Issue #10 is the Task Issue for this Change Unit;
- GitHub CLI requires `project` scope for Project operations;
- prior Project #1 VPS read/write evidence already proved that the existing VPS credential can perform Project operations;
- current Source adds the bounded contract, one-shot helper and CI regression coverage.
- Fresh compatibility evidence: actual VPS `gh 2.52.0` rejects the original name-based item-edit contract, while GitHub's GraphQL `updateProjectV2ItemFieldValue` contract accepts explicit project/item/field ids and a typed field value; the helper already uses `gh api graphql` for exact readback, so the correction stays on the existing credential/tool path.

### Affected scope
- `operations/github-project-control.json`
- `scripts/github_project_control.py`
- `scripts/github_project_control_test.py`
- `scripts/github_project_request_from_comment.py`
- `scripts/github_project_request_from_comment_test.py`
- `.github/workflows/github-project-control-request.yml`
- `.github/workflows/server-core-behavior.yml`
- `.github/workflows/server-core-guard.yml`
- `docs/WORKSPACE_REGISTRY.md`
- `docs/STRUCTURE.md`
- this Design Delta

### Verification state
`SOURCE_IMPLEMENTED` on Issue #10 branch. Owner-only CHAT/GitHub comment→bounded request validation is implemented at Source/Test level, but `issue_comment` runtime activation requires the workflow to exist on the default branch. Automatic GitHub→VPS execution, current VPS credential readback, live Project mutation and full CHAT-originated E2E remain separate evidence and are **NOT_VERIFIED** until completed.

### Compatibility / approval boundary
No main merge, Production activation, service restart/recreate, Secret/Provider mutation or live Project mutation is implied by this Source change. The comparison copy of Notion「Notion活用の大原則」is not modified by this Change Unit.


## 2026-10-07 — Reuse Generic Internal Event API for Project Control transport

### Baseline design
The initial Issue #10 transport investigation considered external/provider webhook ingress and other GitHub-to-Server patterns. Fresh log-commonization evidence proved the Workspace already has a product-neutral trusted internal producer API in `seigo-gace/webhook-gateway`: `POST /internal/events`. G-ACE KB already uses that API to route bounded internal events without giving the producer TGserver URL or Cloudflare credentials.

### Actual change
Project Control transport now adopts that existing internal contract at Source level:
- external/provider `/ingress/:slug` is not the Project Control transport;
- `scripts/github_project_internal_send.py` submits only validated `gace.github-project-control/v1` data to the fixed `server-core-project-control` destination through `/internal/events`;
- `scripts/github_project_internal_receiver.py` exposes only `/healthz` and `/internal/github-project-control`;
- delivery requires the fixed destination header plus the existing Webhook Gateway Standard Webhooks-style HMAC signature contract with timestamp tolerance;
- the receiver reuses `github_project_control.py` directly and does not accept arbitrary commands or target URLs;
- operational Project/GitHub failures return retryable 5xx status while malformed/auth-invalid delivery fails before mutation;
- `operations/github-project-control.json` records interface names and expected environment-variable names only, never credential values.

### Reuse evidence
- Webhook Gateway commit `b20364e5cc7fe62885833a07a5aef2d1c69cb2fa` added the Generic Internal Event API.
- Webhook Gateway PR #18 / main `5361ddde2342793716f0538e7d4c7986595be1be` preserves that API and registers the product-neutral TGserver ZERO bulk destination.
- G-ACE KB merge `da08bac504e8a66c7bb1e10a7b3d40d3f76c45c3` replaced direct TGserver transport with the Generic Internal Event API.
- Fresh TGserver ZERO Reader run `37604153196` proved the Reader path healthy but returned no P014 hits and `PRODUCER_VERIFIED=false`; therefore runtime delivery is not inferred from Source reuse.

### Remaining boundary
This Source change does not register the `server-core-project-control` destination in webhook-gateway, create/rotate a Secret, deploy a receiver, expose a Production endpoint, merge PR #11, or execute a live Project mutation. Those remain separate Current/approval/runtime gates. Existing internal API token availability for the server-core producer and receiver delivery-secret availability are `NOT_VERIFIED` until runtime readback.

### Verification state
Internal producer/receiver Source and focused tests are implemented on the Issue #10 branch. Exact-head CI must pass before this state is promoted. Runtime remains `NOT_VERIFIED`.


### 2026-10-07 result-evidence continuation
The Generic Internal Event API returns a durable asynchronous 202 receipt, which is not equivalent to Project mutation completion. The bounded receiver therefore publishes final execution evidence to the fixed canonical sink `G-ACE-inc/server-core#10` only after `github_project_control.py` returns PASS with exact field readback. Gateway delivery is acknowledged only after that GitHub result comment succeeds. A deterministic request-id marker suppresses duplicate result comments when Gateway retries an idempotent Project operation.

The owner-comment workflow now submits validated requests through `/internal/events` and reports `PENDING_SERVER_RESULT`; it no longer reports validation-only `NOT_RUN` once dispatch Source is active. Workflow failure after durable dispatch is explicitly treated as `PENDING_OR_UNKNOWN`, not as proof that no mutation occurred.

This remains Source/Test state only. GitHub Actions Gateway URL/token availability, Gateway destination deployment, receiver runtime, receiver delivery Secret, VPS `gh` issue-comment permission and live Project E2E remain runtime evidence gates.


## 2026-10-07 — Package Project Control receiver as Docker Compose runtime Source

### Baseline
server-core production-resident services must use Docker Compose. The internal Project Control receiver existed as tested Python Source but had no canonical container/runtime definition.

### Actual change
- `Dockerfile.project-control` packages only the Project Control contract, runner and bounded receiver with Python + GitHub CLI.
- image default is non-root; Compose overrides the numeric UID/GID from required runtime values so a read-only mount of the existing VPS `gh` config can preserve host file permissions without copying the credential.
- `GH_CONFIG_DIR=/run/gh` points GitHub CLI at that read-only credential mount.
- the delivery signing Secret is injected only as a read-only runtime file; no value is stored in Source.
- the receiver publishes no host port; only container port 8788 is exposed.
- the service joins its own default network for outbound GitHub API access and the external shared `gace-internal` network for Webhook Gateway worker delivery.
- `Dockerfile.project-control.dockerignore` restricts build context to the exact runner/receiver/contract inputs.
- CI builds the image and validates Compose interpolation with fixture paths; it does not create the external network or deploy the service.

### Runtime boundary
The external `gace-internal` Docker network, numeric runtime UID/GID, host `gh` config path, delivery Secret file, receiver deployment and health remain runtime facts and are NOT_VERIFIED until an approved server operation performs exact readback. No host path is hard-coded in Source.

### Approval boundary
This Source does not create the Docker network, register/inject any Secret, start/recreate a container, merge a PR or perform a live Project mutation.
