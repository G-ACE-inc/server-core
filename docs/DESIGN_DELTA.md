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


## 2026-10-07 — Split GitHub Project operating rules into SERVER_AI and GPT_CHAT planes

### Master intent
server-core was originally created so server-side AI could enter the Workspace through one control room and reproduce the same server/development operation without Master having to remember or restate rules. Server-side AI has variable usage cost, so its always-loaded rule payload must stay minimal. GPT CHAT is the primary orchestrator and needs a richer rule set that historically lived in GPT-only Notion operating principles.

The target operating authority is GitHub Project #1, not a single oversized server-core rule payload.

### Architecture change
- GitHub Project #1 becomes the Current operating control plane.
- Control Issue #15 owns the dual-plane migration.
- Issue #16 owns the SERVER_AI Minimal Kernel.
- Issue #17 owns the GPT_CHAT Orchestrator Kernel.
- `operations/github-project-rule-plane.json` fixes those identities and the loading contract.
- `docs/GITHUB_PROJECT_RULE_PLANE.md` defines authority ownership and cutover gates.
- server-core remains the stable bootstrap/router/control room for Workspace/server operations and bounded Project control; it does not store both complete AI rule sets.
- Project Current stays in GitHub Project; Source/CI evidence stays in the owning repository; Runtime state stays in runtime readback.
- historical Notion GPT-only principles remain migration source/history until GitHub loading/readback/cutover is verified.

### Cost reduction
The previous always-applied Cursor runtime rule embedded a broad operating contract. It is replaced with a small SERVER_AI bootstrap that routes to the machine contract and Rule Plane #16. Matching minimal entry files are added for Codex-compatible agents (`AGENTS.md`) and GitHub Copilot (`.github/copilot-instructions.md`).

CI enforces maximum bootstrap line counts and verifies that SERVER_AI entry points route through #16 while GPT_CHAT #17 is not default-loaded.

### Compatibility / safety
Shared invariants are preserved: Fresh Current, reuse-first, minimum context, evidence/state separation, approval boundaries, Secret safety, Docker Compose production residency and GitHub work reports. Detailed GPT CHAT reporting/conversation rules are intentionally not copied into server AI bootstrap context.

This Source change does not register Issues #15/#16/#17 as Projects v2 items, mutate Project fields, delete Notion history, deploy runtime, rotate Secrets or merge itself. Those remain separate verified gates.

### Migration state
```text
RULE_ITEMS_CREATED=YES
MACHINE_CONTRACT_SOURCE=IMPLEMENTED_ON_BRANCH
SERVER_AI_BOOTSTRAP_SOURCE=IMPLEMENTED_ON_BRANCH
GPT_CHAT_KERNEL_ISSUE=CREATED
PROJECT_ITEM_REGISTRATION=NOT_VERIFIED
RULE_LOADING_RUNTIME=NOT_VERIFIED
NOTION_CUTOVER=NOT_RUN
```


## 2026-10-08 — Run shared DebugAI stdio in its existing container

The previous direct Host entry depended on a Node interpreter absent from the
verified Host execution path. The shared manifest now invokes the same existing
DebugAI MCP through `docker exec -i` in its existing Compose container. This is a
registration correction, with no new server transport, executor, queue or public
endpoint. The installer migrates only the exact declared old transport, backs up
the config, preserves covered auth fields and rejects unknown collisions.

Rollback restores the prior config backup, but the direct entry still requires a
verified Host interpreter; rollback is not an availability claim. Source parity,
Server Command execution, guarded GitOps and remote CHAT connection remain
separate verification gates. Work-report commit records the applied revision.

## 2026-10-07 — Register existing DebugAI MCP as GitHub Project server-operation backend

### Correction
Master clarified the already-working execution boundary:

```text
GPT CHAT / parent AI
  -> existing DebugAI MCP
  -> existing bounded Server Command / guarded GitOps
  -> existing Host runner
  -> VPS
```

The unfinished work is not a new executor. It is the Workspace/common-control layer that lets GitHub Project #1 use that existing DebugAI MCP across Projects.

The later PR #20 extraction idea duplicated the executor responsibility into server-core and is not the adopted architecture for this Change Unit.

### Adopted ownership
- GitHub Project #1: Current / control surface.
- server-core: Workspace registration, routing, permission/approval contract, discovery and verification state.
- DebugAI: MCP implementation, Server Command, GitOps, Host runner, queue/status execution body.
- Project repositories: own their implementation and Current evidence.

### Source change
- add existing DebugAI stdio MCP entry to `operations/workspace-mcp.json`;
- add `operations/github-project-debugai-routing.json` fixing Project #1 -> DebugAI MCP routing and the four existing control tools;
- adjust server-core Guard so Workspace MCP supports either HTTPS remote servers or absolute local stdio commands;
- update Workspace MCP/Registry authority without copying DebugAI implementation.

### Safety boundary
```text
DEBUGAI_IMPLEMENTATION_COPIED_TO_SERVER_CORE=NO
DEBUGAI_REPOSITORY_MUTATION=NO
NEW_EXECUTOR=NO
NEW_HOST_RUNNER=NO
NEW_QUEUE=NO
ARBITRARY_SHELL_BRIDGE=NO
SERVER_CORE_ROLE=CONTROL_ROUTING_ONLY
DEBUGAI_ROLE=EXECUTION_BACKEND
```

Read-only server operations route through `debugai_server_read/status`.
Protected GitOps routes through `debugai_gitops_request/status` and retains the existing DebugAI approval/exact-SHA/Host-runner gates.

### Runtime boundary
This Source registration is not a live representative-call claim. Actual Workspace config installation/readback and a representative DebugAI MCP call remain runtime verification gates.

PR #20 remains separate/paused and must not be merged as the active solution merely because it exists.

## 2026-10-08 — Route verifiable Standing Delegation to existing DebugAI

Baseline: shared guarded GitOps routing requires exact-SHA Host approval but has no
machine-verifiable delegated-authority reference. Master delegation decisions in
CHAT cannot themselves be Runtime credentials.

Change: shared route metadata references DebugAI's existing deploy/status tools and
its Host-only Standing Delegation contract for `debugai.compose.reflect`. The owner
verifies issuer/validity/revocation, scope/target/identity and issues the existing
single-use receipt mechanism's bound v2 extension. server-core owns dispatch and
decision boundaries only; no project policy engine is copied.

Reason/evidence: explicit Master implementation instruction; fresh #16 decision
authority; existing live shared route PASS; SHA-only manually created receipts are
the remaining delegation handoff gap. DebugAI PR #50 carries source/tests/design.

Affected: routing manifest, protocol, README, existing MCP and structure docs.
Applied commit: the introducing commit/PR in repository GitHub work history.
Compatibility/rollback: existing manual route remains available; revoke/expire
Host policy to disable auto-issuance. No credential/provider/exposure mutation.
Verification: routing/doc CI and owner exact-head CI; actual delegated production
E2E remains a separate gate recorded in canonical Current.
