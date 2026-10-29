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

## 2026-10-11 — Fix Tool B independent common execution ownership

### Baseline design
The §16.9–16.10 implementation wording assigned common route/dispatch to server-core but the Host runner/admission to DebugAI, and the CHAT Host route guide described the already-working DebugAI API as the reused path.

### Actual change
The final common CHAT/Work → GitHub Project → existing Actions → Host execution system is server-core-owned and independent of DebugAI product Repository and runtime. Existing DebugAI-specific route remains transitional and dedicated to DebugAI until common runtime verification passes. §16.9.1 defines required Host test, consumer, reflection, exact SHA and negative authorization evidence.

### Reason / root cause
Merely copying Actions/dispatch while retaining DebugAI product execution checkout was incorrectly accepted as shared execution separation despite Master's explicit instruction.

### Evidence
Master clarification 2026-10-11; Control #10; Rule #17/#16 corrected; PR #89/#90 and Run 38125987709 prove Actions tests only, not independent Host runtime. Current target/manifest still refer to DebugAI-owned execution paths.

### Affected scope
server-core common execution design and CHAT Host route interpretation only; no DebugAI product/source/runtime or deployed Host permission changes.

### Applied commit
Documentation branch `docs/tool-b-independent-common-runtime-20261011`; exact PR/merge SHA tracked at PR #92. Design readback confirmed on branch; runtime unmodified.

### Compatibility / migration / rollback considerations
Keep working DebugAI product route while constructing the independent common consumer. Continue to enforce existing Host admission, credentials and least privilege. Rollback reverts these documentation-only clarifications without touching runtime.

### Verification state
SOURCE_DOC=UPDATED; GITHUB_READBACK=PASS; CI=PENDING; HOST_INDEPENDENCE=NOT_VERIFIED; RUNTIME_PARITY=NOT_VERIFIED; COMPLETE=NO.

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

## Master Internal Persistent Delegation

Purpose is fixed: preserve the existing sales/customer full approval path and
extend only Master's own development to persistent delegation for verified
GitHub Project #1 repositories. Canonical Workspace registry/mapping:
`operations/master-internal-repositories.json`; routing:
`operations/github-project-debugai-routing.json`. This extends the existing
Workspace registry, not a new control plane. DebugAI owns validation/admission
implementation: `docs/MASTER_INTERNAL_PERSISTENT_DELEGATION.md` in its repository.

Each entry has verified GitHub repo numeric/node/owner/Project-item identity,
server project/path, default/allowed branches, operations/scopes, pinned Compose
runtime/services/private health/digest, effect/path policy, enabled/revoked state
and audit identity. Initial entry is DebugAI; other registered repos receive no
automatic grant. Trusted Host admission verifies and reads back an exact private
copy in the existing delegation trust root. Every execution rechecks GitHub
owner/admin/principal, Project item, mapping and exact target before a short
single-use receipt. Repo delegation has no expiry; disable/revoke is immediate.

Design delta: optional Master Internal registry lookup on the existing MCP/Host
lane. Legacy manual and finite Standing modes remain compatible; no Commercial,
licensing, Customer authentication, new executor/queue/transport/service or shell
endpoint. Source/CI and real Runtime qualification remain separate; this source
checkpoint does not claim live persistent-mode PASS. Protected product/spec/public/
provider/model/Secret/destructive persistent decisions remain Master-owned.

## 2026-10-10 — Fix the canonical CHAT-to-Host source reflection design under server-core #10

### Baseline design
The server-core command-center baseline (§§2.4, 2.5, 2.6, 3, 12) already assigned shared capability discovery, Project routing, approval and Source-to-Runtime state separation to server-core. Control #10 verified actual ordinary CHAT -> existing GitHub Actions -> Cloudflare Access -> DebugAI bounded Host reads. However the baseline did not specify how an exact registered Repo/Host parent, active consuming checkout, source-only reflection versus Docker Compose deployment, and subsequent evidence must be bound for **all** owned Projects. PR #36 contains a useful unmerged partial static routing catalog, not an activated host-wide implementation.

### Actual change
Extend the **existing** docs/SERVER_CORE_DESIGN.md with §16, Common CHAT-to-Host controlled reflection. Fix server-core / Control #10 as the **sole common design and current tool owner**; GitHub Project owns changing CU/Project purpose, DebugAI retains the existing authenticated transport/Host executor implementation, product repositories own their source/runtime, and TGserver owns durable log delivery. Introduce a logical request/evidence contract and D0–D5 acceptance gates; this is design authority, not a new runtime credential, transport, Rule Plane or separate development routine.

### Reason / root cause
Master-directed failure mode: GPT CHAT can progress GitHub Source/CI without changing the actual Server consumer. During the live 2026-10-10 audit, server-core local main was synced to remote main but active parent checkout remained on a divergent dirty feature branch. Existing Host read registry incorrectly declares server-core under /home/admin1/projects, whereas the actual canonical parent is /home/admin1/server-core. The existing Master Internal GitOps runner assumes DebugAI-specific Compose runtime and projects-root. Thus neither a Git ref move nor generic registry entry can prove safe cross-Repo reflection. Without a design, CHAT/Work might invent the next architecture/acceptance gate ad hoc.

### Evidence
- server-core #10 live execution checkpoint: https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-6096580570
- Actual CHAT Host inventory (3 pages/18 entries): https://github.com/seigo-gace/debug-ai/actions/runs/38044895527
- Actual installed 512-byte admission registry readback, matched to GitHub Source: https://github.com/seigo-gace/debug-ai/actions/runs/38045018446
- Existing static route Source, still unmerged: https://github.com/G-ACE-inc/server-core/pull/36; its stacked evidence correction merged into that PR branch: https://github.com/G-ACE-inc/server-core/pull/37
- Previously demonstrated 502 then recovery; no proof of new Server source reflection: https://github.com/seigo-gace/debug-ai/actions/runs/38044824474 and https://github.com/seigo-gace/debug-ai/actions/runs/38044856370

### Affected scope
Only server-core architecture/docs/dispatch reference on this design-only branch. No modification of DebugAI products, its live Host runner/admission, PR39 parent checkout/dirty paths, control plane Rules #16/#17, GitHub Project fields, credentials, Docker/Compose or TGserver Runtime.

### Applied commit
First design-source commit: 724a6c3e68d884e20f00a5a5069b7b254ad4d9a0. Track the final PR head/CI separately in the owning #10 Current; this history reference does not claim merge or runtime application.

### Compatibility / migration / rollback
Keep existing DebugAI-specific enrolled deployment semantics, external-customer approvals and secret boundaries unchanged. Reuse established Actions/DebugAI transport, route preflight from PR36/37 only after its owner integrates it, and require explicit limited realpath/root and per-Repo issuer/branch/path/effect admission before extending capabilities. Unmerging/reverting this design commit restores the earlier generic baseline but **must not** be interpreted as revoking an independently installed Host policy. No Host state changes are introduced here.

### Verification state
DESIGN_SOURCE_WRITTEN=YES on the isolated server-core design branch. REVIEW/CI/MAIN_MERGE=NOT_VERIFIED until actual checks and readback. D1–D5 real Host read, approved source-only reflection, target Runtime and full Development Log recovery are NOT_VERIFIED, regardless of this design commit.

## 2026-10-10 — Restore two co-primary tool capabilities under Control #10

### Baseline design
server-core main §16 (merged PR46, 1b55c904a947e11f177d618ff9b1dfd2579421b0) defined the CHAT→Host tool with a narrow Development Event mention and relegated TGserver ZERO delivery/search/recovery to a separate later lane. This misrepresented Master's actual tool priorities, which are **(A) unified development Log** and **(B) ordinary CHAT control of the Server**, both required for completing G-ACE Development Platform. Existing TGserver #44/#50 Source already has canonical event ingress, owner-only [DEVLOG] relay, mapping, central Reader and observable delivery gaps; it must not be reimplemented as another server-core transport.

### Actual change
Retain existing server-core baseline and §16 operations (retitled capability B), explicitly specify two **co-primary** tool capabilities and add §17 as capability A's complete **common integration/acceptance design**, including owner/reuse map, all registered Repo/execution-surface coverage, same-event-id receipt stages, raw Telegram/indexed Meilisearch/recovery distinctions, no new transport/token/service, observed Gateway configuration blocker and A0–A4 acceptance gates. Link §17 from README and task router. Common design/current/acceptance owner remains server-core #10; TGserver ZERO, webhook-gateway, DebugAI and product Repos retain implementation and trusted runtime authority. GitHub Project's fixed product purpose is unchanged.

### Reason/root cause
Master correction: an implementation-only Host design leaves the other required Tool capability undesigned, encouraging CHAT/Work to make arbitrary assumptions or treat a log success as a Host deploy and vice versa. In real TGserver #50 evidence, owner-only CHAT [DEVLOG] relay Actions run 37992536124 parsed the event and mapped P008 but failed on missing DEVLOG_GATEWAY_URL and shared URL config prior to send; no Gateway/Telegram raw/Meili same-event durability was verified. Existing ZERO searches cover some events but cannot prove this missing event was delivered.

### Evidence
- Tool B design merged: https://github.com/G-ACE-inc/server-core/pull/46
- Tool A Source/owner: https://github.com/seigo-gace/TGserver/issues/44 and https://github.com/seigo-gace/TGserver/issues/50
- Failed same-event CHAT relay: https://github.com/seigo-gace/TGserver/actions/runs/37992536124
- Existing TGserver ZERO Source: https://github.com/seigo-gace/TGserver/blob/main/README_ZERO.md and https://github.com/seigo-gace/TGserver/blob/main/docs/TGSERVER_ZERO_PROJECT_INTEGRATION.md
- Actual Host bounded read evidence: https://github.com/seigo-gace/debug-ai/actions/runs/38045018446

### Affected scope
Only server-core existing docs/SERVER_CORE_DESIGN.md, docs/DESIGN_DELTA.md, README.md and docs/LOAD_SCOPE.md. No changes to TGserver/DebugAI/Host/Secrets/GitHub Rules, existing PR36/PR39 ownership or runtime.

### Applied commit
The introducing design-correction commit/PR on branch design/dual-tool-log-and-chat-host-20261010, exact final SHA/CI to be recorded in owning Control #10. This entry does not itself claim main merge or runtime activation.

### Compatibility / migration / rollback
Preserve existing gace.development.event.v1, ZERO owner-only relay, Generic Internal Event API/Gateway, Telegram raw authority, Meilisearch rebuildable index and existing trust boundaries; product vNext and Catalog Knowledge Promotion remain independent. This extends the *same* baseline/Current contract rather than creating a third rule plane, another service or duplicated Tool design. Revert only the corrected design/entry references if the owners decide to withdraw it; no runtime data/policy was changed here.

### Verification state
A0/B0 Source/document consistency to be validated by exact PR head checks and main readback. A1–A4 real collection/durable search/recovery and B1–B5 authentic Host read/reflection/Runtime NOT_VERIFIED until their separate real tests. Presence of a design, successful CI or some indexed historical results does not establish end-to-end completion.

## 2026-10-10 — Execute CHAT-to-Server before remaining Log work

### Baseline design
server-core design §16 Tool B and §17 Tool A are both required for the fixed G-ACE platform purpose. The preceding §17 used "co-primary" to direct parallel execution, despite Master's original instruction that CHAT→Server is the unfinished operational enabler and existing CHAT/Log features already have substantial Source, Reader and historical runtime proof.

### Actual change
Prioritize **Tool B (ordinary CHAT→Server inspection/authorized Source reflection/active Runtime readback)** as the first active implementation track, with Tool A's existing TGserver ZERO producer/relay/Gateway/Reader Source and completed proofs maintained without repeated implementation. Preserve Tool A's independent completion gates and return to its evidence-proven remaining failures after Tool B's usable operating path. This changes scheduling, not product scope, event schema or technical trust policy.

### Reason / root cause
Master explicitly corrected the premature parallel Log implementation instruction. Diverging into Log when the normal CHAT still cannot reflect server-core's canonical checkout risks perpetuating GitHub-only progress without actual Server application.

### Evidence
- Design+current: https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-6096906247
- Log existing partial work: https://github.com/seigo-gace/TGserver/issues/50
- Live bounded Host reads, not Source reflection: https://github.com/seigo-gace/debug-ai/actions/runs/38045018446
- Existing PR36 static routing (separate owner): https://github.com/G-ACE-inc/server-core/pull/36

### Affected scope
docs/SERVER_CORE_DESIGN.md §17 implementation ordering, README entry, this Design Delta, and Control #10 Current only. No modification to GitOps registry/admission, PR36/PR39, TGserver, DebugAI product, Host, credentials or runtime.

### Applied commit
Recorded by this isolated server-core design-priority PR; exact final PR HEAD, CI and main SHA are authoritative in its GitHub evidence.

### Compatibility / migration / rollback
Keep A0–A4 and B0–B5 acceptance, all existing Log Source and Owner claims, policy/Secret boundary and vendor-free testing intact. This is an execution-order correction, not another Rule Plane or design owner.

### Verification state
Design entry/Delta/Source and same-head CI to be verified independently. Tool B Host canonical-path read and source reflection remain NOT_VERIFIED until live server evidence exists.

## 2026-10-11 — Align CHAT turn-decision checkpoints with actual execution surfaces

### Baseline and reason

The mandatory design-change routine in `docs/G_ACE_WORKSPACE.md` §6 requires comparing Source and Tests to the owning Design before each implementation, diff and PR, and recording intentional departures in this Design Delta. During CU #40 the existing `scripts/github_project_chat_turn_gate.py` and its tests were changed repeatedly after PRs #58–#61, while user-observed ordinary CHAT responses still ended prematurely following CI or Issue updates. Master uses ongoing work, formal report order, and command presentation as **behavioral symptoms**, not as the objective of a format-only validator.

### Architecture and implementation boundary

- Authority: GitHub Project #1, Rule Plane #17, CU #40. Common shared routine: `docs/G_ACE_WORKSPACE.md` §6–§7. The five-item formal-report contract is in Rule #17 §7 and is applicable only when its **actual** formal-report trigger occurs; a normal interim explanation is not a formal report.
- Existing operational adapter: `.github/workflows/chatgpt-live-api-verify.yml` rejects **explicit Host requests** without a `START` checkpoint (PRs #60–#61), and `server-core-guard.yml` executes deterministic Gate tests. The shared Python Gate also evaluates supplied `FAILURE`/`STOP` data, but that is **not** a native GPT CHAT turn-send/response-termination interception.
- No existing ordinary-CHAT native response-send hook is shown in the server-core repository or available GitHub/Host entrypoints reviewed in CU #40. Therefore `STOP`/report gates that run **only** inside CI are not evidence that the user-facing assistant applied them before sending its reply.
- `manifest_verified`, `rule_full_read`, `next_action_evidence` and `completed_actions` are asserted fields supplied to a validator. Their passing does not independently establish real rule-reading, action execution, or truth of the final ChatGPT response. Keep normal user-observed behavior and source/CI/runtime evidence separate.

### Correction / required development decision

1. Do not create more stand-alone STOP/REPORT validators and present green CI as ordinary CHAT behavior remediation.
2. Identify and exercise an actual **supported** ordinary CHAT turn-response observation/interposition surface, if one is available. Only then bind the existing Rule #17 legitimate stop conditions and five-item report contract to that surface; explicitly prove an early termination would be rejected and a legitimate completion accepted.
3. Without such a surface, retain `NATIVE_CHAT_STOP_INTERCEPTION=NOT_VERIFIED`, preserve safe Host admission and continue independently executable authorized CU work. Do not fabricate a pre-send hook, add new MCP/workflows/tokens, or take another CHAT's Source ownership.
4. For future source-changing CU #40 commits, record exact Design baseline + affected clause, acceptance condition, actual caller path and execution observation **before implementation**, compare at diff/PR and require the usual Documentation Gate (README/Tree/Design Delta/System Doc) evidence. A static code test cannot replace this design review.

### Evidence, compatibility and rollback

Historical implementation: [PR #58](https://github.com/G-ACE-inc/server-core/pull/58), [PR #59](https://github.com/G-ACE-inc/server-core/pull/59), [PR #60](https://github.com/G-ACE-inc/server-core/pull/60), [PR #61](https://github.com/G-ACE-inc/server-core/pull/61).
Operational START positive: [Actions 38112125417](https://github.com/G-ACE-inc/server-core/actions/runs/38112125417). Missing checkpoint rejection: [Actions 38112102820](https://github.com/G-ACE-inc/server-core/actions/runs/38112102820). Incorrect-phase rejection: [Actions 38112242386](https://github.com/G-ACE-inc/server-core/actions/runs/38112242386).
Behavioral counterexamples: [CU #40 observation 6105707417](https://github.com/G-ACE-inc/server-core/issues/40#issuecomment-6105707417), [audit 6105722443](https://github.com/G-ACE-inc/server-core/issues/40#issuecomment-6105722443).

This is a **documentation correction** to design/application claims, not a change to existing Host permissions, credential flow, Code execution, native CHAT response handling, or the project purpose. Revert only this bounded Delta if design owner rejects it; historical Source and actual runtime boundaries are unaffected.

## 2026-10-11 — Catch missing CU #40 design reviews at existing PR execution boundary

### Baseline and motivation
The existing `docs/G_ACE_WORKSPACE.md` §6 design-alignment and §7 Documentation Gate are mandatory **before implementation**. The existing server-core guard previously checked only presence of documents and rule text, so a CU #40 Gate implementation could pass CI even if its PR omitted the Design baseline, affected requirements, diff review and four Documentation Gate decisions. This was observed retrospectively for the earlier CHAT Gate PR chain; it is not cured by formatting a final response.

### Intentional bounded enforcement change
In the existing `.github/workflows/server-core-guard.yml`, pull requests changing the CU #40 CHAT decision evaluator, its tests or the live Host request Workflow now require nonblank PR-body declarations for DESIGN_BASELINE_REF, DESIGN_REQUIREMENT, DESIGN_ALIGNMENT_EVIDENCE and all four standard Documentation Gate decisions. Missing declarations fail the existing Guard before PR merge. Unrelated owner CUs and direct push to main are not blocked by this PR-scoped step; old PRs are not retroactively reclassified. The contract still separates Master-visible continuation, final report format and command presentation from machine-verifiable Host/CI scope.

### Limits and evidence
The gate verifies declared process evidence is **present**, not independently that a GPT CHAT model actually read the Design or did not terminate early. An honest implementation still requires human/source/evidence review and native CHAT turn observability. Do not label this a real reply-send STOP interceptor. This is a focused Work Routine enforcement on the already-owned CU, not a new Workflow, token, rule plane or broad authorization. No existing Design Baseline text is rewritten.

Compatibility/rollback: remove only the added scoped existing-workflow PR check and corresponding README/Tree indexing to restore previous permissive PR behavior. Tests and Host operational routing stay unchanged; deployed workflows are not altered beyond the existing CI contract.

## 2026-10-11 — Verify declared Documentation Gate against actual Source diff

### Existing design and observed defect
`docs/G_ACE_WORKSPACE.md` §6 and §7 require design-first implementation and concrete README/Project Tree/Design Delta/System Document decisions. The first scoped CI implementation [PR #64](https://github.com/G-ACE-inc/server-core/pull/64) checked that decisions were nonblank in a PR body, but did not prove a `YES` declaration caused any required file to change. Thus the process could remain documentation-incomplete while CI passed.

### Bounded correction and acceptance
The **existing** `server-core-guard` CU #40 PR preflight now checks actual changed paths: `README_UPDATE_REQUIRED=YES` needs `README.md`, `PROJECT_TREE_UPDATE_REQUIRED=YES` needs `docs/STRUCTURE.md`, and `DESIGN_DELTA_REQUIRED=YES` needs `docs/DESIGN_DELTA.md`; invalid decisions fail. When the Design Delta changes, the original file must remain as an intact prefix, with only appended content. This is intentionally scoped to PRs touching CU #40 Gate implementation files; it does not silently impose a new approval model on other repositories or work owned by other CHATs.

### Limits and rollback
The scope does not independently prove model Design comprehension, quality or native CHAT final-answer interception. The `SYSTEM_DOCUMENT_REQUIRED=YES/UPDATE_EXISTING` declaration is not yet mapped to a definite system-document file; do not mislabel that gap as verified. Direct writes to main can evade PR-time checks if branch protection is absent (protection API readback was denied). No permanent Host authorization, runtime or product-source changes. Rollback can remove the bounded guard additions and corresponding navigation changes; prior architectural Design and historical entries remain unchanged.

## 2026-10-11 — Tool B autonomous development coverage (design-first extension; implementation pending)

### Existing baseline and gap
Baseline: `docs/SERVER_CORE_DESIGN.md` §16.1–16.8, §17, `docs/G_ACE_WORKSPACE.md` §6–7, GPT CHAT Rule #17 and server-core owner Control #10. Existing Tool B strongly specifies bounded READ_FILE/READ_STATUS, SOURCE_REFLECT and COMPOSE_REFLECT; §17 specifies durable Development Event recovery. Current registry and Actions dispatch expose fewer commands than the broader Host catalog. These do not constitute a complete ordinary-CHAT development loop: bounded Git diagnosis/recovery, registered test/build execution, per-service Compose lifecycle/rollback, cross-step failure→replan, and exact evidence-based cycle acceptance were not specified together.

### Intentional design extension
Appended `SERVER_CORE_DESIGN.md` §16.9 without rewriting or superseding §16.1–16.8/§17. It defines seven capability families; a common per-action capability/admission/evidence field contract; a continuous CU state machine and failure/replan branch; explicit test/negative/security/runtime acceptance. The distinction between listed, Actions-supported, Host-admitted and live-verified capabilities is mandatory. Final acceptance is a real ordinary CHAT-origin fault→diagnosis→Repository fix→test/CI→authorized Host reflection→runtime verification→GitHub Current plus independent Tool A correlation, not a green Workflow alone.

### Scope, responsibilities and safeguards
Owner: server-core Issue #10 / Project #1 for shared design and routing. Existing DebugAI owns Host runner and trusted authorization; target Repositories own project tests/Source; TGserver owns Event delivery and search. No additional tool plane, MCP, workflow, token, generic shell endpoint or top-level sibling Project. No granted host access, Source reflect, deployment, CI rerun, product change or protected admission alteration follows from a design change. Permission expansion remains separately reviewed and verified; commercial separation and existing negative tests are preserved.

### Verification status and next design gate
DESIGN_SOURCE=BRANCH_ONLY; DESIGN_REVIEW=NOT_YET_COMPLETED; IMPLEMENTATION=NOT_STARTED_THIS_CU; HOST_RUNTIME=NOT_CHANGED. Review §16.9 against the active #10 owner and existing capability/Host-source inventory, check no contradiction with §§16–17 and Rule #17, then establish an approved Design Gate before any runner/dispatcher implementation. Acceptance remains NOT_VERIFIED until implementation/test/CI/Host/Log evidence at each corresponding gate. Rollback is this append-only design addition and its §16.9 insertion only; preserve older design/history.

### 2026-10-11 review correction — Host gh CLI is optional, not generic CHAT GitHub access
The previously observed Host `github.actions_recent` result `GH_CLI_UNAVAILABLE` (Actions run 38021882940) does not imply GPT CHAT cannot use its connected GitHub API. Updated §16.9 Git contract to prefer native connected API for remote repository/PR/CI operations; Host-local git and `gh` are separate registered capabilities. If Host `gh` is indispensable, executable/auth/scope/admission preflight and actual E2E are mandatory; distinguish absent binary vs auth/scope/allowlist errors, reuse available equivalent API routes, do not introduce an unapproved token or treat a design statement as installation. DESIGN_ONLY; implementation/runtime unchanged.

### 2026-10-11 review addition — retained GitHub Actions Artifacts
Tool B §16.9 now explicitly requires existing GitHub API/connector-based Actions artifact list/download, safe bounded ZIP content inspection and original run/job/SHA/hash evidence linkage, with NO_ARTIFACT / EXPIRED / DOWNLOAD_DENIED / ZIP_UNSAFE / CONTENT_UNVERIFIED distinctions. Host `gh` CLI is unnecessary for these connector operations. Source verification: runs 38116946531 and 38110641849 returned empty artifact inventories; this confirms accessible listing but does not verify ZIP download or contents. No workflow change, artifact upload, Host install or mutation is authorized by this design. Real nonempty ZIP E2E is pending.

### 2026-10-11 — Final server development coverage audit before implementation
Appended SERVER_CORE_DESIGN §16.10 to cover registered workspace/disk/Git conflict inspection, bounded tests, Docker/Compose dependencies/resources/lifecycle/rollback, transport failure and artifact safety, Source-to-active-consumer parity and fresh-CHAT recovery. Each capability must distinguish catalog/source listing, Actions support, trusted Host admission and live proof. This is a design change only; Cursor agent delegation is expressly deferred by Master. Reuse existing DebugAI implementation/Actions without new Workflow, token, shell or MCP. Review and merge this design before owned implementation CUs; no Host entitlement is conferred.

## 2026-10-11 — Tool B first implementation CU: existing inventory command dispatch admission

Baseline: SERVER_CORE_DESIGN §16.9–16.10, Tool B §16.4–16.7 and common route registry. Prior live run 38109918095 rejected `system.projects_inventory` at the server-core idle preflight even though the existing bounded client and DebugAI Host runner include a read-only inventory command. This CU modifies only existing server-core dispatch allowlist, corresponding workflow-supported command registry and parity test to remove the identified SOURCE-level mismatch. It does **not** change Host runner, Host private admission, credentials, Workflow topology, Project registration or application product. Negative unsupported-command checks remain. The existing target remains idle; CI alone does not prove Host inventory runtime acceptance.

Verification required: same-HEAD CI test and guard, then a separate admitted CHAT-origin Actions inventory positive run + Host command request ID and safe page output; restore exact idle trigger. Do not claim full Tool B capability coverage from this single bounded addition. Rollback: revert the three CU source/test edits while preserving prior Design and this historical Delta.

## 2026-10-11 — Complete scoped System Document update verification

Baseline: `docs/G_ACE_WORKSPACE.md` §6/§7 and `docs/PROJECT_TEMPLATE.md` System / Feature-bundle Document contract. Existing CU #40 PR admission could accept `SYSTEM_DOCUMENT_REQUIRED=YES` or `UPDATE_EXISTING` without any named changed System Document. The existing `server-core-guard` now requires exactly one `SYSTEM_DOCUMENT_PATH=docs/*.md` in the PR body for these decisions, excludes the Workspace Rule/Tree/Design Delta authorities as substitutes, and verifies that exact path occurs in the PR Git diff. This adds no workflow, permission, authorization, or separate design authority.

Operational rejection evidence: [PR #68](https://github.com/G-ACE-inc/server-core/pull/68) [run 38117514290](https://github.com/G-ACE-inc/server-core/actions/runs/38117514290) failed with `CU40_SYSTEM_DOCUMENT_PATH_MISSING_OR_AMBIGUOUS`. The guard still does not prove document quality, actual GPT CHAT model reading, or native final response interception. System documents remain required only when the template criteria are actually met; avoid creating documentation without a system need. Existing baseline and prior Delta history are retained as a prefix. Rollback: revert the scoped existing Guard check and the README/Tree entries; no Host/runtime effects.

## 2026-10-11 — server-core Tool B bounded Host disk/Git diagnostics

Design baseline: `docs/SERVER_CORE_DESIGN.md` §16.9–16.10 and existing Tool B §16.1–16.8. Master confirmed common CHAT Actions execution entry must stay in `G-ACE-inc/server-core`; DebugAI is the reused backend, not this CU's development target. The Composer report of Host live evidence for `system.disk_usage` and `project.git_changed_paths` is prior adjacent-owner evidence only; this CU has not independently verified these through server-core Actions yet.

Scoped Source change: reuse the existing `chatgpt-live-api-verify.yml` workflow and `chatgpt-bounded-server-read.cjs` to add these two bounded read-only command IDs to source dispatch, common route catalog/workflow-supported intersection and test fixtures. Emit only disk percentage/blocks and Git changed-path COUNT, never raw private path names or files. Keep request arguments empty, target repository fixed to the existing bounded /workspace/debug-ai execution identity; no general shell, new Workflow, token, host registry or new sibling worktree. The Host source/actual installed admission is separate and must be checked with real CHAT-origin run.

Acceptance: targeted positive/negative client+dispatch tests, same-head GitHub CI/PR readback; an explicit START checkpoint on live trigger; Host command ID, read-only PASS, safe result markers and no deploy; restore exact prior idle blob. Do not imply canonical server-core parent read, source reflect, Docker lifecycle or Tool A delivery is solved. Rollback is source-only removal of these bounded IDs, client parsers and tests.

## 2026-10-11 — Main admission: GitHub Free private cannot enforce native protection

### Baseline and observed gap
CU #40 Work Routine enforcement in `server-core-guard` was scoped to `pull_request` events ([PR #64–#70](https://github.com/G-ACE-inc/server-core/pull/64)). Anyone with `push`/`admin` on `main` could bypass Design/Documentation Gate declarations by pushing directly. GitHub API readback: org `G-ACE-inc` plan `free`, repository private; branch protection and rulesets endpoints return **403**; GraphQL protection/ruleset lists are empty (`protected=false` at platform layer).

### Bounded correction (existing workflow only)
Append a `push`/`main`-scoped step to the existing `server-core-guard` (no new Workflow file): when a push changes CU #40 gate Source paths, require an associated **merged** pull request for the commit SHA via `GET /commits/{sha}/pulls`. Otherwise emit `CU40_MAIN_DIRECT_PUSH_BLOCKED` and fail the guard run. Merged PR paths continue to pass. This preserves other workflows, Actions permissions model, and non-gate main documentation hotfixes.

### Limits, evidence, rollback
Post-push CI failure does **not** revert Git history and is not equivalent to required status checks under branch protection. Hard pre-push block still needs GitHub Pro/Team private protection or a public-repository ruleset. Evidence: API 403 on protection/ruleset create; [Issue #40](https://github.com/G-ACE-inc/server-core/issues/40) CU scope. Rollback: remove the push admission step and restore prior README/`GITHUB_FREE_MAX` wording; PR-scoped guards from #64–#70 remain.

## 2026-10-11 — Main-push PR association must match exact main merge SHA

### Observed gap and baseline
Prior CU #40 main-push admission (PR #74) checked whether the pushed commit's `GET /commits/{sha}/pulls` response included **any** merged PR. That broad predicate did not explicitly bind the PR's base to `main` or the PR's `merge_commit_sha` to the actual pushed HEAD. The shared Work Routine in `docs/G_ACE_WORKSPACE.md` §6 requires immutable revision/branch evidence rather than an ambiguous association.

### Bounded implementation
Tighten the **existing** `server-core-guard` main push check for CU #40 gate-owned paths so a qualifying PR must have `merged_at`, `base.ref == main`, and `merge_commit_sha == pushed HEAD`. This does not add a workflow, transport, token or branch protection. README and Project Tree entries reflect the stricter implemented condition.

### Limits and rollback
The check runs **after** main has already been updated. It is a CI warning/failure signal, not native private GitHub Free branch protection. An associated merged PR alone no longer qualifies without exact SHA and target branch. A true direct-main negative push is not exercised because it would contaminate unprotected main. Rollback: revert only the stricter predicate and accompanying README/Tree description. Actual per-PR/source correctness and ordinary CHAT reply termination are separate.

## 2026-10-11 — Reconcile bounded Host logs dispatch on current main

Baseline: SERVER_CORE_DESIGN §16.9–16.10 and existing Tool B Control #10. PR #75 implemented service.debug_ai_logs on a stale branch, causing merge conflict with concurrent main changes. This CU reuses its bounded Source-only intent on current main: add service.debug_ai_logs to existing idle dispatch and registered workflow_supported intersection, retain allowed_command_ids/effects, and extend existing deterministic route test; do not copy stale route registry wholesale. The bounded client already validates log_service and log_lines, redacts output, and invokes the registered Host command. No new Workflow, MCP, token or Host entitlement. Real CHAT-origin Host log read is required after same-HEAD CI; only registered service and 1–20 lines are allowed. Preserve other denied commands and revert idle target after E2E. Historical PR #75 remains separately traceable; do not double-merge.

## 2026-10-11 — Tool B existing sandbox health and bounded Git recent commits

Design baseline: SERVER_CORE_DESIGN §16.9–16.10, Control #10. Reuse the existing Host `service.sandbox_state` and `project.git_recent_commits` commands, existing CHAT client ALLOWED set and bounded state/commit-subject validation. Add only these IDs to the existing common idle dispatch and route workflow-supported intersection; retain exact registered route policy and negative denial assertions. Git commit subjects are redacted for secret-looking/control-character text; command arguments stay empty. No new workflow/MCP/Token/Host permission or DebugAI product change. Same-head CI followed by independent CHAT-origin Actions host requests, receipt, read-only status, and exact idle restoration are required. Source/CI success alone is not Runtime success.

## 2026-10-11 — Tool B Host status HTTP failure classification

Evidence: exact ordinary CHAT Actions Run 38121975277 for bounded project.git_recent_commits reached Host request cmd_74cbbc22fa758c52d2d31eaf, then failed in server-core client after repeated status API non-200 responses (`STATUS_HTTP_NOT_200`); actual Host command terminal result UNKNOWN, not a Git history failure. The previous client retried permanent 4xx errors for the full polling horizon. This scoped CU classifies permanent 4xx (excluding retryable 408/429) and terminates the current Host status read immediately with an HTTP status code (no body or secret output), preserving bounded retries for 5xx/408/429 and existing source read-only admission. New focused test asserts 404 incurs one status request and safe classification. No change to Host runner, workflow, permissions, command list or runtime product. Retest must use an existing admitted read and distinguish readback faults from Host command faults. Design baseline §16.9–16.10; existing error recovery expectation; no E2E PASS claimed for recent Git history.

## 2026-10-11 — Enforce effective idle read admission on server-core

Design baseline: SERVER_CORE_DESIGN §16.9–16.10. Existing server-core dispatch independently checked an IDLE_READ_COMMANDS set but did not evaluate the actual route's catalog, workflow_supported_command_ids and read_only effect intersection at execution time. Static route parity tests are not a substitute for a fail-closed runtime preflight after registry changes. This bounded server-core-owned CU adds the effective three-way read-only admission check for any nonempty idle command. Focused tests reject a removed catalog command, removed workflow support or non-read effect while preserving registered positive and no-command idle modes. This is a Source preflight guard, not a claim of installed Host support or Runtime PASS. No DebugAI Repository/Host mutation, workflow, new token, MCP or protected delegation change. Rollback by reverting this narrowly scoped dispatch condition and its test.

## 2026-10-11 — Tool B common route registry evidence sync

Baseline: Control #10, `operations/github-project-chat-host-routes.json` route_debugai_live_read handoff note. Prior note still marked inventory, disk, Git changed-path, logs, and sandbox Host E2E as pending although ordinary CHAT Actions runs 38117859559, 38119011721, 38119034738, 38121803165, and 38121944210 already recorded PASS with Host receipts on main. This bounded CU updates only the registry handoff text to bind verified run IDs, records project.git_recent_commits as still pending post-#79 retest (38121975277 failure), and states the #80 three-way idle admission rule plus non-dispatch catalog-only commands. No workflow, Host, DebugAI product, token, or dispatch code change. Rollback: revert the handoff note and this Delta append only.

## 2026-10-11 — Tool B git_recent_commits Host E2E PASS after #79

Post-#79 retest via merged PR #81 triggered Actions run 38123852985 on main: Host request cmd_25935adb02776b64d6c1e46b, SERVER_COMMAND_STATE=PASS, SERVER_COMMAND_READ_ONLY=TRUE, bounded SERVER_GIT_LOG emitted. Follow-up chore PR restores idle target. Registry handoff updated to bind this run ID. No DebugAI Repository/Host mutation.

## 2026-10-11 — Tool B registered server-core Host test execution (manifest + existing python_unittest)

Baseline: SERVER_CORE_DESIGN §16.9–16.10, Control #10. Existing DebugAI Host already implements bounded `project.python_unittest` in isolated `.debugai-input/test-repos/*` checkouts; server-core had no manifest, Actions dispatch intersection, or client wiring to select approved tests and bind repo/SHA/exit-code evidence. This CU adds `operations/github-project-chat-host-test-manifest.json`, extends the existing bounded client and idle dispatch/route registry for manifest-selected `project.python_unittest` only, and adds deterministic tests. It does **not** modify DebugAI Repository/Host runner, expand `dlg_master_servercore_reflect_v1` allowed_paths into `scripts/`, add Workflow/MCP/token, or claim Host test-repo provisioning. Live E2E requires an existing Host test checkout at the manifest path; missing checkout remains `HOST_TEST_REPO_NOT_VERIFIED`. Actions run 38125411897 returned `REQUEST_HTTP_NOT_202` (Host/API rejected unittest request; test-repos checkout not verified). Auto docs-only source reflect on main now treats Host `SOURCE_REFLECT_NO_DIFF` as idempotent skip in the existing workflow (no new Workflow file).

## 2026-10-11 — Tool B existing Actions pre-Host route contract test

Owner server-core Control #10, design baseline §16.9–16.10. The active existing `chatgpt-live-api-verify.yml` job had run the CHAT turn gate and bounded Node client tests but not the already-existing Python route admission contract test in that very execution context. Reuse `scripts/github_project_chat_host_route_test.py` in the same pre-Host verification step to reject route/allowlist/effect drift before real requests. No new workflow, backend, token, route admission, or DebugAI mutation. The current Host test/build execution contract remains unimplemented separately; this test guards the existing Actions route and does not qualify as Host build/test support.

## 2026-10-11 — Explicit Master per-turn Rule read takes precedence over delta optimization

Master observed repeated GPT CHAT #17 adherence failures despite read receipts and CI. Existing `docs/LOAD_SCOPE.md` GPT CHAT item 7 said full rule issue bodies need fetching only on revision/incomplete read, and a generic context paragraph exempted unchanged authority from rereads. This conflicted with Master's current explicit instruction, held in owning Issue #40, to re-fetch Manifest, #17 **full body**, and Current every development turn, then apply them before action and STOP. This change narrows the reconciliation to the **existing read router** rather than changing #17 or the shared Work Routine owner Draft PR #39.

Per-turn full read becomes mandatory when explicitly directed by Master; normal optimized rereads remain the default otherwise. Reading alone does not demonstrate application or intercept ChatGPT final send. An observed premature stop remains failure. No native hook, new workflow/MCP, guard script, secret or Tool B functionality is claimed or introduced. Rollback by reverting this router delta; existing architectural Design and historical Delta retained.

## 2026-10-11 — Classify registered Host test request HTTP rejection without response disclosure

Owner: server-core #10, Tool B §16.9–16.10. Existing registered-test Actions E2E run 38125411897 aborted before Host request receipt with REQUEST_HTTP_NOT_202. This cannot establish a missing Host test checkout, Host authorization failure, or a missing project. Update the existing bounded CHAT client request handler to retain only numeric HTTP status for unsuccessful request responses, without reading or exposing the HTTP body. The executable CLI emits SERVER_COMMAND_REQUEST_HTTP=NNN followed by existing bounded class marker. A negative test covers 400 with a deliberately unreadable response body. No new workflow/MCP/token or any DebugAI repo/runtime change. Retest only after validating admission and known registered target prestate; no Runtime PASS claim.

## 2026-10-11 — Execute two server-core registered static tests on existing Actions runner

Owner: server-core #10, Tool B §16.9–16.10. Host registered-test request E2E 38125411897 was rejected before receipt; its cause remains UNKNOWN and it is not evidence that an isolated checkout exists or can be created safely. Independently reuse the existing `chatgpt-live-api-verify.yml` checkout (exact workflow GITHUB_SHA) to run the two preexisting static Python test scripts from the registered server-core manifest (`scripts/github_project_rule_plane_test.py` and `scripts/github_project_chat_host_route_test.py`), without DebugAI test-repo staging. Their successful completion emits SERVERCORE_REGISTERED_TEST_SHA and SERVERCORE_REGISTERED_TESTS=PASS, scoped to the Actions runner only. This is a SOURCE/CI execution proof, not Host test Runner admission or live consumer parity. The registered Host target manifest remains separately gated; no new workflow, MCP, token, or backend mutation.

## 2026-10-11 — Tool B independent server-core local bounded Host primitive (Source candidate)

Baseline: SERVER_CORE_DESIGN §16.9.1, §16.10, Control #10 and Rule #16/#17. DebugAI product also uses Cloudflare, but its product Repository/runtime must not be the common Host executor.

Change: server-core-owned Python-only `scripts/servercore_bounded_host.py` provides a *local*, no-listener, no-credential bounded execution primitive for canonical `/home/admin1/server-core`: exact Git HEAD, clean-status summary, two fixed registered Python tests; rejects non-registered commands, mismatched SHA, invalid root/symlink, missing tests, dirty test checkout. `tests/servercore_bounded_host_test.py` exercises negative boundaries and existing `github-project-control-verify.yml` runs it in CI. No generic shell API or DebugAI-specific path.

Reason: Actions/route copy is not independent Host execution. This isolates the core primitive under server-core ownership for later authorized entry/transport wiring and real Host verification.

Evidence: PR source tests, exact-head CI and Host readback are separately required. No claim of active canonical Host deployment, authorization, consumer, Cloudflare Account API Token runtime, production Source reflect, or end-to-end operation from this source addition.

Compatibility and rollback: Does not alter existing DebugAI product runner or working temporary DebugAI route. No new secret, token, workflow, MCP, listening service or Host policy. Remove candidate module/CI test to revert.

Verification at creation: SOURCE_ONLY; HOST_INSTALL=NOT_VERIFIED; NETWORK_AUTHENTICATION=NOT_IMPLEMENTED; HOST_E2E=NOT_VERIFIED; SOURCE_REFLECTION=NOT_EXECUTED; RUNTIME_PARITY=NOT_VERIFIED.

## 2026-10-11 — Wire server-core bounded Host primitive to existing Gateway delivery auth

Baseline: SERVER_CORE_DESIGN §16.9.1, merged PR #93 (`scripts/servercore_bounded_host.py`), Control #10. PR #93 isolated the local primitive; this CU connects it to the **same authenticated Generic Internal Event API pattern** as Project Control without extending `github_project_control.py` or Project field mutation authority.

Change: `operations/github-project-bounded-host.json` registers allowlisted commands and transport metadata (`server-core-bounded-host` destination). `scripts/gace_internal_delivery_auth.py`, `servercore_bounded_host_receiver.py`, and `servercore_bounded_host_gateway_send.py` implement HMAC-verified receiver + Gateway enqueue using existing `GACE_EVENT_GATEWAY_URL` / `GACE_EVENT_GATEWAY_TOKEN` contract names. `Dockerfile.bounded-host` and `docker-compose.project-control.yml` service `server-core-bounded-host` package the receiver on `gace-internal` with read-only canonical root bind. `chatgpt-source-reflect-dispatch.cjs` and existing `chatgpt-live-api-verify.yml` accept optional `bounded_host_request` (mutually exclusive with DebugAI server_command, gitops, and source_reflect). `project_control_runtime_readback.sh` emits local consumer `project.git_head` parity markers. Reference-only `operations/webhook-gateway-bounded-host-destination.reference.json` documents the webhook-gateway destination/route registration; **not** an activation.

Evidence: focused Python transport/runtime tests; Docker build `gace-server-core-bounded-host:ci`; VPS readback `SERVERCORE_BOUNDED_HOST_LOCAL=PASS` at consumer SHA `d454f7021c74ffb095297178b2af46fe57720a2a`. Gateway/receiver container deploy and CHAT-origin Gateway→Host terminal PASS remain gated on webhook-gateway destination registration and Host delivery secret provisioning (Host Policy; no new token assumed).

Compatibility: DebugAI transitional route unchanged. No DebugAI Repository/Runtime mutation, no Project Control receiver behavior change, no arbitrary shell API.

### Security adjustment — remote registered-test exclusion (2026-10-11)

During source integration review, `project.registered_tests` was found to execute repository Python code in the same receiver container as the mounted outbound HMAC delivery key and the internal network. This does not establish safe test isolation even if the checkout mount is read-only. Until a credential-free, network-isolated test worker is independently reviewed and admitted, the **Gateway/receiver command allowlist** permits only `project.git_head` and `project.git_status`. The local fixed-test capability and CI verification remain separate. Added explicit negative test for denied remote registered-tests request. No Host deployment or credential permission expansion. Completion remains SOURCE/CI only pending live gateway registration/Host admission and terminal readback.

## 2026-10-11 — Bounded Host container Git ownership compatibility

Baseline: §16.9.1 independent common executor, merged PR #94. The receiver runs unprivileged with canonical checkout mounted read-only. Git may reject different UID ownership as unsafe, even when host-local git tests passed. Change: fixed git read commands now set process-local `safe.directory` to the validated canonical root, disable fsmonitor and hooks per invocation. No global Git trust, no arbitrary shell, no Host policy or credential changes; unit test asserts exact scoped invocation. Verification: same-HEAD CI pending; container/Host parity remains NOT_VERIFIED until approved runtime deployment.

## 2026-10-11 — Deploy P0: exact-SHA canonical Source reflection, independent Host local primitive

Master acceptance is CHAT-authored GitHub Source → real VPS Source reflection/Deploy → runtime health/exact SHA readback. Historical READ E2E (Actions 38135212887) and repo checkout matching main do not qualify as generalized deploy.

First concrete Source unit: `scripts/servercore_source_reflect.py` pins canonical `/home/admin1/server-core`, branch `main`, explicit expected-before/target 40-hex SHA, clean tracked/untracked status, fetch of `origin/main`, remote SHA equality, ancestor fast-forward check, OS file lock, ff-only merge and exact post-reflect SHA. No arbitrary shell, no branch/repo supplied by caller, no reset/stash, no arbitrary hooks; rejects dirty files including outstanding `operations/master-internal-repositories.json` edits rather than overwriting them. Existing CI exercises positive/negative and dry-run cases.

**Deliberate separation:** this Source unit is NOT wired into the credential-bearing read-only bounded receiver or deployed as a privileged service. It needs an independently authorized write-capable Host executor/transport binding and safe runtime installation, followed by an actual target Source reflect and separate service deploy/health verification. `SOURCE_REFLECT_PASS` is not service `DEPLOY_PASS`. Do not bypass Host ownership checks or claim running instance parity from GitHub CI success. No new workflow, Token, MCP, DebugAI modification, sibling project/worktree.

### 2026-10-11 — Deploy P0 origin admission correction

Source-reflect candidate must reject a substituted `origin` before executing fetch: canonical Host pathname and branch alone do not establish repository identity. The local runner now permits only the literal official G-ACE-inc/server-core GitHub HTTPS or SSH remote URLs; missing or other origin fails closed, including local file URLs. Negative test added. This does not grant write authority to the existing read-only Host container, nor claim runtime Deploy. Host must inspect its configured origin and admit an alternate form by reviewed policy only if needed.

## 2026-10-11 — Deploy P0: independently authorized UNIX Host source reflection (Source candidate)

Reuses the verified CHAT→existing Actions→Gateway→bounded Receiver transport. Adds registered effect `project.source_reflect` with exact `expected_before` + target SHA; the sender, dispatch contract and existing Workflow refuse missing before-SHA and require explicit START receipt before mutation. The Gateway receiver remains with a read-only canonical checkout and no Docker socket or generic shell. For this one effect it forwards a fixed schema/repo/branch request through a local UNIX socket to `servercore_source_reflect_socket.py`, a separately Host-admitted writer which reuses `servercore_source_reflect.py`. Host socket uses strict local path, filesystem ACL and single-writer lock. Existing read requests stay local. Default Compose unchanged; optional `docker-compose.source-reflect.yml` only binds an explicitly approved Host UNIX socket, and should NOT be activated before installing the corresponding Host-local writer and ACL policy. No new token, MCP, Workflow, public port or DebugAI product mutation.

**Security and acceptance boundaries:** The existing Gateway Internal API token can submit bounded events; accepting `project.source_reflect` expands potential effects. Production activation requires explicit Master/Host policy authorization, protected source-of-request, and proof that only the intended receiver UID can access the UNIX socket. The Host-local service must not be run as an unrestricted root process. Validate current Host checkout dirty changes before any apply. Cloud Action 202 is not deployment success: terminal worker delivery, exact Host Source SHA and separately required running service/health readback must PASS. This PR contains SOURCE/CI only; HOST_SOCKET_INSTALL=NOT_VERIFIED, SOURCE_REFLECT_E2E=NOT_VERIFIED, SERVICE_DEPLOY=NOT_VERIFIED.

## 2026-10-11 — Deploy P0 Host-local executor installation contract

PR #100 merged the Source-only independent `project.source_reflect` adapter and optional UNIX-socket overlay. To minimize manual VPS commands without bypassing Host authority, `scripts/servercore_source_reflect_host_bootstrap.py` now supplies dry-run preflight (default) and explicit `--install` systemd admission. It verifies canonical checkout path, registered official Git origin, main branch, exact requested SHA, fully clean tree including untracked files, admin1 identity and existing receiver group. Installation is root-gated and refuses overwriting a pre-existing differently configured service unit. The generated service runs as admin1 and the approved receiver group with an AF_UNIX-only endpoint, no network listener, no Docker socket, no new token/workflow/MCP, and group-only UNIX socket permissions. Existing Compose read-only checkout remains unchanged; optional socket overlay requires separate authorized activation and exact Host E2E.

Blocked preconditions must not be silently 'fixed': Composer observed non-owned uncommitted edits in `operations/master-internal-repositories.json`, so preflight must reject until their owner reconciles them. Source-only CI success does not establish installation, GitOps/Deploy or running service evidence. Do not claim completion until exact Host SHA, gateway delivery terminal receipt, and target service health/readback PASS.

### 2026-10-11 — UNIX socket reconnect on Host executor restart

The optional Compose admission overlay now mounts the approved Host UNIX **directory** read-only instead of bind-mounting one socket inode. A file-level bind mount could retain a stale socket after systemd restarts and recreates the endpoint. The receiver still has no write mount for its canonical Source checkout and no Docker socket. The Host owner must set `GACE_HOST_SOURCE_REFLECT_SOCKET_DIR=/run/gace` or an equivalent explicitly admitted existing directory and verify group traversal/socket permissions; activation remains a separate Host gate. Static CI rejects reverting to a socket-file mount.

## 2026-10-11 — Tool B registered service Deploy admission baseline

Runtime evidence confirms independent exact-SHA server-core Source reflection but not Docker service deployment. `scripts/servercore_service_deploy_admission.py` therefore introduces a nonmutating deny-by-default authorization/preflight based on the existing `operations/master-internal-repositories.json`: exact registered repo/service, persistent active delegation, explicit deploy operation, fixed Host checkout path, pinned Compose SHA256, and exact Host Source SHA. The current registry authorizes only DebugAI's `debug-ai` and `sandbox-runner` deploy operation via its existing product executor; server-core and TGserver entries are **source-only** and must not be silently upgraded to Deploy. `docker ps` visibility is never used as authorization. No new MCP, Workflow, Token, Host command, Docker socket, generic command executor, or service restart is introduced. This is a Source+CI authorization component **only**. Next gate requires independent Host write authority for a fixed registered service, scoped Compose execution and runtime health/image readback, with the consumer/delivery policy expressly reviewed before any live service changes.

### 2026-10-11 — Tool B registered service Host-local executor (not remotely admitted)

`scripts/servercore_registered_service_deploy.py` consumes the fail-closed registry + exact source/Compose checks established above. The default invocation is read-only preflight. An explicit Host-local `--apply` can execute Docker Compose **only for the already-registered service** via fixed argv (`up --detach --no-deps --build SERVICE`) and inspects the resulting Compose service label, container running state and optional Docker health. An absent healthcheck is reported as `NONE` and is not evidence of application health. This module is **not wired** to the Gateway, HMAC Receiver or Host UNIX socket and grants no Docker socket to the Receiver. Current Registry has service deploy only for DebugAI's existing product-owned route; server-core and TGserver remain source-only. Independent common service deploy authorization/Host policy, actual runtime installation and live E2E are still NOT_VERIFIED. Preserve external app and other unrelated running containers.

## 2026-10-11 — Master scope correction: ALL actively developed Project #1 items

**Master decision (authoritative for Tool B):** All development projects registered in TGserver ZERO (using its existing project registration mechanism) are intended to be deployable from ordinary CHAT through the common server-core-owned GitHub→Actions→Host route. This means the common capability must ultimately support **every actively developed registered Project**, not only DebugAI, TGserver and server-core, and not only current `deploy` entries in a partial historical `master-internal-repositories.json`.

**Keep scope separate from permission:** TGserver ZERO registration determines **target coverage**, not unreviewed permission to restart every container. Per-project canonical repository, Host path, registered branch/SHA, runtime type (Compose, source-only, service, worker, non-container), permitted operation, component ownership, deploy/run command, dependencies, health evidence and rollback must be checked and registered. An UNKNOWN mapping is a coverage gap to close, not a reason to permanently exclude the Project or fabricate a runtime. Existing product-owned deploy logic should be reused where appropriate but the common route must not depend on the DebugAI product executor.

**Acceptance:** Use TGserver ZERO `storage-registry.json` for Project IDs and `.github/tgserver-zero-project-map.json` for repository/stream correspondence; reconcile these with live Host inventory and canonical per-Project operational mapping. P003 and P009 have incomplete/exceptional GitHub mappings, so mark mapping UNKNOWN rather than silently exclude. Do not treat registry enrollment alone as runtime authority. Produce a coverage matrix for **all TGserver ZERO registered Project IDs** showing `IMPLEMENTED`, `HOST_VERIFIED`, or `UNKNOWN/BLOCKED` and the missing next gate for each; implement and validate each missing bounded deploy binding; prove CHAT→GitHub→Host exact SHA, service/relevant runtime health and terminal delivery. Do not claim success from listing `docker ps`, SOURCE-only reflection, CI, or an isolated successful service deploy. Do not create new Workflow, Token, MCP, parent-sibling project/worktree. Previous PR #106/#107 only implement fixed-registration admission/execution baseline and **do not close this project-wide requirement**.

### 2026-10-11 — Repo vs TGserver log project/stream correction

Master clarified that **deployable units are actual development repositories, not 14 distinct TGserver ZERO log Project IDs**. For example DebugAI has P004 runtime and P005 KB streams but remains **one** repository; P003 is a personal log namespace; P009 ai-core has no verified GitHub repository mapping, and P014 is a KB namespace whose repo/deploy nature must be checked. Current TGserver reader mapping has 11 distinct GitHub repository keys, while the Master's visible local workspace shows 11 entries including GPG-Core (explicitly excluded), giving 10 required local repo entries. The sets **are not yet reconciled**: Catalog↔modular-catalog alias, ai-core repository identity, GPG-Core exclusion, server-core/gace-dev-kb registered but not pictured, and any others must be verified. Do not auto-deploy log modules or inflate repo count. `tgzero_deploy_coverage.py` now emits both log IDs and distinct mapped repositories; final deploy coverage must be audited by verified repository identities, modules/streams preserved beneath them, and GPG-Core excluded per Master.

### 2026-10-11 — Catalog contains gace-dev-kb

Master confirmed `gace-dev-kb` resides inside the `Catalog` development unit. Preserve TGserver's `P012` modular-catalog and `P014` gace-dev-kb log namespaces and distinct GitHub mapping; KB implementation/runtime is on PC, not a Catalog VPS container. They share workspace component ownership but **remain distinct execution/deployment locations**. The source audit preserves gace-dev-kb component_of Catalog and runtime_location=PC; its separate deployment unit must not be dispatched to the VPS Docker route. PC machine path and remote deploy route are UNKNOWN until separately verified. No cross-repository checkout, Docker restart, or authorization expansion is implied.

### 2026-10-11 — Common registered service Deploy pre-admission correction

Before connecting existing Host-local registered Compose deploy source to the shared Receiver/Host executor, require Host origin exactly matches the registered repository, Host branch is on the delegated branch allowlist, Host HEAD equals the requested exact SHA, and checkout is clean. Reject wrong remote/branch, dirty tree, wrong source SHA and mismatched Compose digest. This is an in-place correction to Tool B Host admission, **not** a new Deploy Workflow, registry, token, MCP or project-specific development task. CI validates registration fields; live Host validation and protected common dispatch remain separate pending gates.

### 2026-10-11 — Common Gateway to Host registered service Deploy route (separate writer)

Reuses the merged registry admission (#106/#112) and fixed Compose executor (#107) unchanged. New bounded commands `service.deploy` (effect `service_deploy`, fixed `repository`+`service`+explicit target SHA, never the workflow SHA alias) and `service.deploy_status` (read-only) travel the existing Actions -> Gateway -> HMAC Receiver path. The Receiver holds no Docker authority: it only forwards to the separately admitted Host UNIX socket `/run/gace/servercore-service-deploy.sock` served by `scripts/servercore_service_deploy_socket.py` (admin1 user-level systemd unit installed by `scripts/servercore_service_deploy_host_bootstrap.py`, no root, no new token/workflow/MCP). Gateway delivery timeout (30 s) is shorter than image builds, so the writer runs a dry-run admission synchronously, replies `SERVICE_DEPLOY_ACCEPTED`, deploys asynchronously, and persists a request-id keyed result (`QUEUED/RUNNING/SERVICE_DEPLOY_PASS/FAIL`) with before/after Compose container identity, `recreated`, Compose digest and registered loopback HTTP health. A duplicate request id never redeploys. Authority comes only from `operations/master-internal-repositories.json` deploy entries; this change adds none (no deploy delegation is self-granted by the executor). `SOURCE_PASS` here is not `DEPLOY_PASS`: DEPLOY_PASS requires a live registered service readback.

### 2026-10-11 — Source reflect keeps checkout file modes (service umask 0117 correction)

The Host source-reflect writer runs with `UMask=0117` for its socket. Its `git merge --ff-only` inherited that umask, so reflected files lost the exec bit and group/other read (dirty tree on the next clean-gated reflect, unreadable Receiver image contract). The git subprocess now runs with `umask=0o022`; the socket umask is unchanged. Fail-closed gates are unchanged.

### 2026-10-12 — Bounded Host command result return (request-id correlated, redacted, GitHub-readable)

Transport previously returned only the Gateway 202 receipt; Receiver HTTP responses never left the Gateway worker. Now **every** enabled `bounded_host_request` requires the CHAT START receipt (START Gate no longer limited to reflect/deploy). The low-privilege Receiver reports each authenticated terminal result (PASS / FAIL with exit code 0/1, Host SHA, stdout = bounded command result JSON, stderr = failure class) to the Host-local `servercore_result_sink.py` over UNIX socket `/run/gace/servercore-result.sock`. The sink redacts (secret-like keys, bearer/GitHub tokens, private keys, 48+ char opaque strings; sha256 digests kept) and bounds streams to 2000 chars, persists one 0600 record per request id (first terminal result wins; transient/5xx results are RETRYABLE, never published, and replaced by the later terminal result), and posts exactly one marker comment (`<!-- GACE_BOUNDED_HOST_RESULT request_id=... -->`) on the fixed control Issue #10 using the Host's existing GitHub CLI connection (crash-safe: it looks for an existing marker before posting). The existing Actions job then reads that comment with its own `GITHUB_TOKEN` (`issues: read`) and prints `SERVERCORE_BOUNDED_HOST_*` markers correlated to the request id, failing on Host FAIL, correlation mismatch or no result (`NOT_RETURNED`), so GPT CHAT reads the run log or the Issue through its existing GitHub connection. Read-only commands return 503 (Gateway retry) if the sink is down; mutating commands still execute exactly as before. No new MCP, workflow, token, listener, or deploy authority; registry and DebugAI untouched. `service.deploy` PASS means accepted; terminal deploy readback stays `service.deploy_status`.


### 2026-10-12 — Result sink resolves the GitHub CLI by fixed absolute path

The Host user systemd PATH has no `~/bin`, where the existing authenticated `gh` lives. The result sink now selects the first executable of fixed absolute candidates (`/home/admin1/bin/gh`, `/usr/local/bin/gh`, `/usr/bin/gh`) instead of PATH lookup, and logs a bounded failure class (never the body or credentials) when a publish attempt fails. No new credential.

### 2026-10-12 — Writer result directories stay traversable under UMask=0117

`mkdir(mode=0o700)` is masked by the writers' `UMask=0117`, producing a `0600` directory without the execute bit; the first live result write failed (`RESULT_SINK_UNAVAILABLE`, read-only command correctly returned 503 for Gateway retry). Both the result sink and the service-deploy writer now `chmod 0700` their result directory after creating it. Host directory was repaired in place (`chmod 0700`, no data change).

### 2026-10-12 — Registered file inspection and Docker log reading through the same START-gated, result-returning route

Two read-only bounded commands reuse the proven Actions -> Gateway -> Receiver -> result-sink -> GitHub path (no new MCP, workflow, token, listener or deploy authority). `project.file_inspect` reads ONE 2400-byte chunk (`offset`, `next_offset`) of an exactly registered canonical-checkout file (`registered_files` in the committed contract; no globs, traversal or symlinks; expected_sha must equal Host HEAD; the DebugAI-owned master-internal registry is deliberately not registered). `docker.logs` is served by a separate admin1 user-level UNIX-socket reader (`servercore_docker_logs_socket.py`, fixed `docker logs --tail N --timestamps <container>`, tail<=200, 16000-char cap) so the Receiver keeps no Docker authority; authority is the committed `registered_log_containers` (initially only `server-core-bounded-host`; a dirty or locally edited contract is denied). Adding another project's container needs an explicit reviewed contract change. Output is redacted (now also JSON-escaped `key: value` secrets) and bounded to 4000 chars by the result sink; stdout/stderr are returned by request id as before. `service.deploy` stays gated by registry delegation (PR #117 draft).


### 2026-10-12 — Docker-admitted user writers start through `sg docker`

Live rollout of the registered Docker log reader returned `DOCKER_LOGS_EXECUTION_FAILED`: the long-lived admin1 user systemd manager runs with groups `27 100 1000` (docker membership was added later), so its units cannot reach `/var/run/docker.sock`; an unprivileged unit cannot `setgroups`. The same latent defect applies to the registered service deploy writer. Both installers now emit a user-level unit that starts the fixed script through `/usr/bin/sg docker -c` (membership already granted to admin1; `sg` is setuid so `NoNewPrivileges=no`; still no root, no network listener, same UNIX socket and fixed-schema request). Existing installed legacy units are replaced atomically only if byte-identical to the previously shipped text; any other unit is an `EXISTING_UNIT_CONFLICT`. Alternative (root restart of `user@1000`) needs sudo and was not available.

### 2026-10-12 — Per-commit isolated CHAT Host request ownership

The legacy singleton `.github/chatgpt-live-api-target.json` caused conflicting GitHub updates between distinct CHAT and Server AI units, and risks re-dispatch on unrelated main changes. Retain compatibility while supporting one new immutable `.github/chat-host-requests/req_<24hex>.json` per triggering commit. The existing Actions workflow selects only a newly added request and materializes it only in the runner workspace before current START Gate/dispatch/result-return checks. Later commits cannot replay earlier request files. Reject mutation of a prior request, multiple request files per commit and combined legacy target mutation. Existing Gateway, server-core Host receiver, result sink, workflow and credentials are reused; no new MCP, token or workflow. The existing Actions concurrency group serializes runners, while distinct request files permit separate callers to submit without shared target write conflicts. Runtime E2E remains a separate gate.

### 2026-10-12 — Independent CHAT request concurrency groups

Following isolated CHAT request E2E success on existing Actions→Gateway→Host, a fixed workflow-level `concurrency.group` still allowed at most one running and one pending run per group, risking loss of intermediate independent requests when multiple callers submit close together. Use the triggering SHA as the concurrency group suffix for commits that add a per-request file; retain the singleton `legacy` group for all other triggers, including the existing shared target. `cancel-in-progress: false` remains. Per-commit request admission and result idempotency are unchanged. Legacy mutating requests remain serialized; independent request submissions can have distinct waiting/running slots without replacing one another. No new workflow, gateway endpoint, token or Host authority is added.

### 2026-10-12 — Tool B: bounded tracked Git diff summary (Control #10)

- **Purpose:** normal GPT CHAT needs a bounded Host-side change indicator while diagnosing Source/Runtime drift without exposing arbitrary Git diff paths or contents.
- **Design authority:** `docs/SERVER_CORE_DESIGN.md` §16.9.1, §16.9, §16.10. Reuse `servercore_bounded_host.py`, its existing Receiver and `operations/github-project-bounded-host.json`; no new transport, workflow, token or privilege.
- **Contract:** `project.git_diff_stat` takes the existing exact `expected_sha` and returns `changed` boolean plus a maximum 200-character tracked-diff aggregate (`git diff --shortstat HEAD --`). Unknown command, SHA mismatch and malformed/multiline output fail closed. It does **not** report untracked files; use existing `project.git_status` for checkout cleanliness. No repository paths, contents, or free-form shell arguments are returned.
- **Owner/rollout:** server-core Source; actual Host runtime remains independently gated on reviewed Source/CI, exact Host SHA reflection and same-SHA CHAT→Actions→Host→result E2E. This delta is not a runtime PASS claim. DebugAI legacy product route and PR #117 Draft are unchanged.


### 2026-10-12 — Master selection: OpenHands sandbox for Tool B

**Decision / scope.** Master selected the third OSS candidate, OpenHands, for the common GitHub Project #1 registered-repository development terminal. This supersedes continued one-command-at-a-time growth as the primary developer workflow; the existing signed CHAT→Actions→Gateway→Host route and bounded production operation path stay intact. Actual OpenHands installation, model configuration, Host admission and E2E remain **NOT VERIFIED** until direct Runtime evidence is recorded. This entry is not a generic production shell authorization.

**Reuse and component boundary.** Use upstream OpenHands V1's Docker sandbox / agent-server capability (official upstream OpenHands SDK/agent server; pin immutable image digest before installation). Prefer the sandbox execution capability as a worker behind server-core's existing signed route rather than a second public AI chat frontend. GPT CHAT remains the planner; do not start another paid AI agent or make provider calls for command execution. Existing DebugAI self-use route is preserved. OpenHands may require Docker to provision sandbox containers: Docker Engine control belongs to a separate Host-side provisioner, never to a code-executing sandbox. Public repository GitHub-hosted Actions continues as transport; never attach an unrestricted self-hosted Actions runner to the VPS.

**Registered repository contract.** Resolve requested Project ID and Repository against fresh GitHub Project #1 Current and existing Host registry. Bind exact allowed branch/base SHA, repo root, permitted operation/effects, owner, execution timeout and artifact budget. Create a per-request isolated worktree/checkout **inside existing canonical project** (never a new sibling Project under /home/admin1/projects), accessible only within its sandbox. Only project workspace is writable; exclude mounted Docker socket, Host secrets, production services, global credentials and unrelated projects. Shell command execution must be scoped to this non-production development sandbox, never production Host root. Terminal output and exit status are bounded and correlated by unique request ID.

**Execution lifecycle and rollback.** Preflight input SHA/cleanliness and snapshot important state; start an isolated sandbox; verify readiness by bounded polling; run Git inspection/edit/tests/builds inside sandbox; collect structured stdout/stderr, exit, changed files, artifacts and current SHA; stop/recreate worker cleanly on failure; replay only idempotent stages. Failed code changes are discarded within isolated worktree; accepted changes must be proposed as GitHub PR, pass exact SHA CI, then reflected/deployed by existing separately authorized Host writer with verified backup and restore. No claim that arbitrary external side effects can always be rolled back.

**Acceptance (must all be independently evidenced).** (1) existing registered Project selection PASS and unknown/unregistered repo DENY; (2) normal GPT CHAT originates signed request via existing Actions, receives correlated terminal result and artifact; (3) sandbox executes at least Git status and repository's existing test without any added command ID or Docker image rebuild; (4) test intentionally fails and isolate rollback/retry succeeds without master shell; (5) produce Source PR/CI evidence, separate authorized Source reflect/Runtime verification and TGserver ZERO log correlation; (6) no secret exposure, cross-repository access or production impact. Missing any entry = full CHAT autonomy NOT VERIFIED.

**Provenance.** Official upstream OpenHands documentation: https://github.com/OpenHands/docs/blob/main/openhands/usage/advanced/custom-sandbox-guide.mdx ; SDK source: https://github.com/OpenHands/software-agent-sdk ; current main has no OpenHands installation/integration files as of this decision. Before deploying, Server AI must verify VPS capacity/runtime/network and compatible pinned release, license/dependencies and any required provider/model policy. No new token, MCP, Actions workflow or paid provider calls are authorized by this delta.


### 2026-10-12 — Master revision: Docker-native Tool B and design-enforced execution

**Current decision (supersedes the OpenHands-specific selection directly above, not its preserved history).** The required outcome is an actually usable, zero-additional-paid-model GPT CHAT development terminal through existing Project #1 -> GitHub Actions -> Gateway -> server-core-owned Host receiver. OpenHands is NOT required or presently authorized as a dependency; reuse Docker Engine/Compose and existing server-core tooling before adding OSS. Do not introduce an additional server, Swarm/Kubernetes, MCP, workflow, token, independent root Project or DebugAI product-runtime dependency. This is a design checkpoint, not proof of implementation or Host admission. Separate future multi-server ideas are in Notion and out of this CU.

**Design-as-enforced-contract, not instructions-only.** Source design is human-readable in this existing section and the canonical `docs/SERVER_CORE_DESIGN.md` §§16.9.1/16.10; GitHub Project #1 Current is authoritative for active CU/Gate/owner; manifest -> Rule #17 (CHAT) or #16 (SERVER_AI) selects profile. BEFORE a Tool B source-mutating change or Host-executed development job, the existing guard/dispatcher MUST eventually check machine-verifiable inputs: project item + registered repo ID, owner, exact branch/base HEAD and active mutation owner, approved design baseline revision/digest, allowed changed-path/effect categories, project-local workspace realpath, target SHA, and explicit acceptance criteria. Unknown, stale or mismatch blocks that action; it does not halt unrelated read-only/current recovery. A mere PR description, agent acknowledgment, design file existence or successful CI is not proof of actual design-loading/enforcement. Implement/check through the existing server-core guard/receiver and its tests; do not create another rule plane or new workflow.

**Executable worker boundary.** The Host-controlled provisioner (not the sandbox) may request an ephemeral non-root Docker container with project-local isolated worktree strictly INSIDE the verified registered canonical parent. Restrict writable mounts to that workspace; deny Docker socket, Host credentials, other project roots, live production volumes and exposed ports; cap CPU/memory/pids/time/output/artifact size/network as needed. Container executes a bounded job's argv/script with explicit working directory, not a production Host root shell. Return correlated request/session/job IDs, stdout/stderr, exit status, changed files, before/after SHA and artifacts. Reuse existing independent immutable CHAT requests and actual Actions/Gateway receipts; no per-command-ID image rebuild for each Git/test invocation. Multiple request IDs must be isolated; same-worktree writers require ownership or serialization.

**Correction and promotion boundary.** Within sandbox, allow inspect -> edit -> focused tests -> failure analysis -> patch/retest without Master's routine VPS commands. Preserve rollback prestate and evidence; discard/recreate only the owned disposable workspace after verified scope. Source PR and CI exact SHA precede separately authorized guarded Host reflection; production data/volume rollback is independent, never assumed from source rollback. TGserver ZERO logs are separately verified with search/readback. Expected paths and design cannot be self-edited by a job to widen its own rights: enforce against approved base design/ref in the Host/CI gate, not unchecked files from the mutable workspace.

**Acceptance tests that guard the design.** Positive: registered repo / correct SHA / approved design digest / bounded Docker job runs Git status and existing test, one controlled failure is diagnosed and retried, results correlating CHAT -> Actions -> Gateway -> Host -> ZERO. Negative: missing/stale design digest, modified acceptance baseline, unregistered or cross-repo target, parent-sibling or symlink escape, Docker socket or Host secret mount, stale SHA, unauthorized effect, concurrently conflicting writer, runaway timeout/output, replay, missing runtime receipt. Explicitly show rejection at CI/Host; no PASS inferred from text review alone. Implement in the existing Tool B CU/PR #134 after direct Source/Host inventory and owner coordination. Actual guard implementation, tests, deploy and E2E are NOT VERIFIED at this design checkpoint.


### 2026-10-12 — Tool B Docker-native isolated terminal: Source implementation of §16.11 (generic `dev.job`)

- **Design authority:** `docs/SERVER_CORE_DESIGN.md` §16.11 (digest-bound, see below). Reuses the existing CHAT request file -> Actions dispatch -> Gateway -> Receiver -> Host UNIX-socket writer -> result sink -> `#10` marker route. No new workflow file, MCP, token, Project, server or paid AI.
- **One generic command, not one command ID per action:** `dev.job` carries `{repository, session, argv<=8, timeout_s<=15, fresh}` plus the existing exact `expected_sha` (Host HEAD). Receiver validates the exact key set; the Host provisioner `scripts/servercore_dev_job_socket.py` (new admin1 user unit via `servercore_dev_job_host_bootstrap.py`, UNIX socket only) owns all Docker authority. The Receiver and executed code never hold Docker authority.
- **Admission (fail closed, tested):** committed contract `operations/github-project-bounded-host.json` `dev_job` registry (only `G-ACE-inc/server-core`, owner/root/branch/project item); committed design section digest (`design_section_sha256`) must equal the digest of §16.11 at Host HEAD, so a design edit without the matching reviewed contract change is `DESIGN_NOT_VERIFIED`; exact Host HEAD == `expected_sha` and registered branch; executable allowlist `git|python3|sh`; strict ids; replay returns the stored result and never re-executes; per-session `flock` (conflicting writer -> `DEV_JOB_BUSY`, retryable); max 8 sessions, 24 h TTL.
- **Sandbox (one fixed docker argv shape, no input can add mounts/env/caps):** image `gace-server-core-bounded-host:gitdiff-20261012` (existing, no rebuild), `--network none`, non-root `1000:1000`, `--read-only`, `--cap-drop ALL`, `no-new-privileges`, memory 512m, 1 CPU, 128 pids, `--pull never`, tmpfs `/tmp` 64m, SINGLE bind mount: the per-session clone `<registered root>/.worktrees/dev-jobs/<session>` at `/work` (never the Docker socket, secrets, production volumes or other projects). Workspace is a `git clone --no-hardlinks` of committed objects checked out at `expected_sha`: dirty Host working-tree bytes (e.g. DebugAI registry) never enter. The Host never runs git inside a workspace after creation; inspection (`rev-parse`, `status`, `diff --shortstat`) runs in the sandbox too. Symlinked `.worktrees`, `dev-jobs` or session path is denied. Workspace budget 200 MiB, output capture 256 KiB (runaway writer killed), wall clock <=15 s (Gateway delivery timeout is 30 s), timed-out container killed by name.
- **Result:** correlated by `request_id` through the existing sink/poller. First `stdout` line is `GACE_DEV_JOB {meta}` (session, base/workspace SHA, job exit, timeout/limit flags, changed files, diff stat), then job stdout; `stderr` is job stderr. Job exit != 0, timeout or output-limit => state `FAIL` with the job exit code (Gateway still gets 200 + accepted so a failing test is a result, not an infrastructure retry).
- **Existing files touched (additive only):** `chatgpt-live-api-verify.yml` dispatch step gains one `dev.job` branch (the existing START Gate/active detection already covers every enabled `bounded_host_request`); `github-project-control-verify.yml` registers the new tests; `chatgpt-source-reflect-dispatch.cjs` shape/effect validation; `servercore_bounded_host_gateway_send.py`; Receiver. Work Routine, Rule Plane, gates and DebugAI product route are untouched.
- **Status:** Source + unit/CI tests only. Host admission, staging, CHAT-origin E2E and TGserver ZERO readback are NOT VERIFIED until recorded in `#10` with Runtime evidence.

### 2026-10-12 — Work Routine design-first gate implementation (PR #39 owner branch)

Integrated PR #135 design contract into the existing Work Routine §6 without a new rule plane, Project field or workflow. Added `scripts/work_routine_design_entry_gate.py` plus tests; wired optional `GACE_WORK_ROUTINE_TURN` receipt checking into `gace_mutation_rehydrate_check.py` and extended `github_project_chat_turn_gate.py` START receipts when `mutation_scope` / design evidence is supplied. CI runs the new unit tests via existing `server-core-guard`. Native ordinary-CHAT interception remains **NOT_IMPLEMENTED**; bounded mutation/START paths are the verified enforcement surface.

### 2026-10-12 — dev.job workspace creation survives the provisioner's UMask=0117

Live Host admission of the generic `dev.job` provisioner returned `WORKSPACE_CREATE_FAILED` (Receiver `503 DEV_JOB_EXECUTION_FAILED`). Reproduced: under the listener's `UMask=0117` (needed for the socket and private state), `git clone` creates `0660` directories, so `.git` cannot be entered. Fix in the existing owner `create_workspace()` only: its three fixed git children run with `umask=0o022` (subprocess applies it in the child; no process-wide umask swap in the threaded server, socket mode and `0600/0700` private state are unchanged, no recursive chmod). Regression `WorkspaceUnderRestrictiveUmask` runs a real git clone + checkout + remote removal under a `0117` process umask and asserts traversable directories, workspace `0755`, exact HEAD and that the process umask is unchanged. Source + unit tests only; Host re-admission and live E2E are NOT VERIFIED until recorded in `#10`.

### 2026-10-12 — A denied `SOURCE_SHA_MISMATCH` reports the real Host HEAD

The Host checkout is shared and its HEAD moves (owner branch work, source reflect), while every CHAT request pins `expected_sha`. A mismatch was recorded with `host_sha=""`, so CHAT could only guess the next SHA (observed: `SOURCE_SHA_MISMATCH` #6115554336, #6115924760, live-dogfood run 38212342842). The Receiver now fills the existing `host_sha` field of the failure record (and the 422 body) with the actual `git rev-parse HEAD` of the canonical checkout, **only** for an authenticated delivery whose denial is exactly `SOURCE_SHA_MISMATCH`; the existing poller prints it as `SERVERCORE_BOUNDED_HOST_SHA`. A commit id is not a secret and goes only to the HMAC-authenticated caller and the existing result record. All other denials, unauthenticated deliveries and an unreadable root still report `host_sha=""`. No new command, field, workflow, token or MCP. Tests: real-repo mismatch/match, other denials never disclose HEAD, unauthenticated mismatch discloses nothing. Source + unit tests only; Host image cutover and live readback are NOT VERIFIED until recorded in `#10`.

### 2026-10-12 — dev.job reclaims idle sessions at the cap instead of blocking until the 24 h TTL

Live Host use hit `DEV_JOB_DENIED_SESSION_LIMIT_REACHED` on a single day: every fresh session id keeps its workspace for 24 h, the cap is 8, so ordinary CHAT test runs (4 per verification) exhausted it and the next request was denied (8 workspaces, 137 MB, measured). §16.11 does not fix the cap; it is an implementation limit. Now, only when the cap is reached, `prune_sessions` reclaims the least recently used sessions that are idle for more than one hour (`SESSION_EVICT_IDLE_SECONDS`) **and** whose per-session lock is free, oldest first and only as many as needed. A session that is running (lock held), the requested session, and any session used within the last hour are never reclaimed; with nothing reclaimable the request is still denied `SESSION_LIMIT_REACHED`. Using an existing session now refreshes its workspace mtime, so the idle clock (and the unchanged 24 h TTL) measures real use. The cap (8), TTL (24 h), workspace budget, sandbox flags and admission checks are unchanged. Tests: reclaim-oldest-only-as-needed, recent work protected, running session protected, TTL/cap unchanged, use refreshes idle clock. Source + unit tests only; Host restart and live readback are NOT VERIFIED until recorded in `#10`.

### 2026-10-12 — CU #40: repair ineffective GPT_CHAT Work Routine turn receipts

**Observed gap:** `scripts/gace_work_routine_turn_receipt.py` emitted `purpose_verified=False` for `GPT_CHAT` (`profile != "GPT_CHAT"`) and defaulted `source_design_aligned=False` into JSON. `work_routine_design_entry_gate.evaluate_turn` then always returned `RULE_ENTRY_PURPOSE_NOT_VERIFIED` or `SOURCE_DESIGN_MISMATCH`, so `GACE_WORK_ROUTINE_TURN` + `GACE_WORK_ROUTINE_REQUIRED=1` on the existing `gace_mutation_rehydrate_check` / `ai-auto-commit.sh` path could never admit a GPT_CHAT-profile receipt despite green receipt generation.

**Change:** Set `purpose_verified=True` when emitting a receipt; omit `source_design_aligned` unless explicitly true/false; CLI `--source-design-aligned` defaults to unset (not false). Always run design evaluation on START in `github_project_chat_turn_gate.py` (defaults remain routine_fix / DESIGN_NOT_APPLICABLE). Added `scripts/gace_work_routine_turn_receipt_test.py`.

**Boundary unchanged:** Native ordinary ChatGPT answer pre-send interception remains **NOT_IMPLEMENTED**. This fixes only the bounded supplied-receipt consumer used when operators opt in via `GACE_WORK_ROUTINE_TURN`.

### 2026-10-13 — GPT CHAT development entry simplification (Master decision)

**Requirement:** Only `docs/G_ACE_WORKSPACE.md` §6 Work Routine governs ordinary CHAT development progression; `docs/MASTER_TERMINAL_COMMAND.md` governs any Master-facing terminal command. Maximize meaningful work within a turn; ask Master for an actual missing action rather than reporting after each CI/Issue checkpoint.

**Delta:** `docs/LOAD_SCOPE.md` routes CHAT to the existing §6 instead of requiring full Rule #17 every turn. The §6 development pre-dispatch no longer repeats a separate full Rule Plane/START/STOP prose sequence. GitHub Project Current remains the authoritative *task data*, not another development routine; SERVER_AI bootstrap, authenticated Host/CI guards, and approval boundaries remain in effect. Legacy Rule #17 source is preserved for migration history.

**Proof boundary:** This is an instruction-loading and documentation change, NOT a native ChatGPT response-final interceptor. CI checks repository compatibility; actual behavior must be assessed in ordinary Chat sessions. No additional workflow, receipt gate, MCP, token or Host mutation.


### 2026-10-13 — Tool B independent request scheduling and complete Project #1 repository mapping

Observed run 38285066565 returned TGserver dev.job PASS, but pending independent DebugAI run 38285068012 was cancelled when a third request arrived. Actions push payload omits changed-file lists; the old concurrency expression always selected legacy. Reuse the existing workflow with the documented `[isolated-host-request]` commit-message marker + exact SHA; leave unmarked legacy singleton admission unchanged. This is scheduling metadata, not a credential or effect grant. Add the two remaining Project #1 repositories (webhook-gateway / asteria) to the existing isolated dev.job contract after live canonical path, branch, HEAD, remote and Project-item checks. No change to protected master-internal registry, production operations, design digest, tokens, executors or product source. Revert this commit to restore the prior three-repository contract and scheduler. Source checks and real post-reflection runtime evidence remain distinct; evidence belongs to Control #10.

### 2026-10-13 — Master-controlled existing GitHub Host terminal (Tool B / #10)

**Purpose:** Existing isolated `dev.job` remains the registered-Repo Source/Test worker; it is not the production Host terminal. Master’s approved requirement is to use the *existing* authenticated GitHub Actions → Gateway → bounded receiver → Host UNIX writer path for real Host terminal commands including Docker/Compose, while GPT CHAT retains Source/PR/CI ownership. This is not an additional standalone terminal, MCP, workflow, token or Project.

**Source delta:** Add `host.command` to the existing bounded Host request contract, Actions sender, dispatcher, receiver and service-deploy UNIX writer. Resolve the working directory only from the protected registered Repository mapping. Verify exact Host SHA, require the existing Master-internal registry’s explicit `host.command` grant, reuse request-ID idempotency and durable result sink, report the actual shell exit code. No change to the isolated `dev.job` sandbox, its design digest, installed Docker socket access, existing service grants, or running production containers.

**Runtime boundary:** CI proves only Source compatibility. Protected Host registry currently lacks `host.command` grants; Host reflection plus in-place verified grant/readback is required before live commands. Do not replace the protected registry from Source, invent Runtime PASS, or conflate a test result with deployment. Existing Host rollback/provenance is used.

### 2026-10-17 — CHAT execution efficiency and capacity-safe handoff

**Baseline / scope:** `SERVER_CORE_DESIGN.md` §2.2/§2.5 (minimal context and verification), existing Work Routine §6, Rule #16/#17 and CU #40; Master commissioned an independent review and ordinary VS-side development. PR #302 already added evidence reuse and visible progress. Reuse those clauses and the existing poller rather than another harness, workflow or monitoring service.

**Verified gaps:** Work Routine repeated continuation/external-execution instructions and an additional six-step dispatch loop, plus a stale PR36/#37-specific restriction. Its "before each mutation, restore" wording could prompt full unchanged Current reads despite its own changed-only rule. The existing result waiter performed a logical Issue lookup every six seconds; each production lookup reads Issue metadata and up to two comment pages. These are avoidable server-side reads, not proof of ChatGPT's reported rate-limit cause.

**Change:** Consolidate the routine's execution, continuation and external handoff paragraphs; retain exact scope/admission, acceptance, design and evidence boundaries and the existing progress/reuse clauses. Refresh affected facts after initial Current restoration. Require a durable checkpoint before context/execution capacity is exhausted. A directly commissioned SERVER_AI uses normal available local tools rather than GPT CHAT's Host transport. Remove the duplicated dispatch loop and historical PR-specific operating restriction, retaining current ownership checks.

The existing `servercore_bounded_result_poll.py` now reads immediately then waits 6/12/24/30 seconds (default), capped at 30 thereafter, shortening the last sleep to the remaining deadline and performing a final read. Explicit intervals must be 1–60 seconds; a larger valid starting interval remains the cap. TimeoutExpired joins existing read-error recovery. Emit logical lookup/failure counts and elapsed wait on success/failure/timeout; preserve existing result markers, request/command/SHA correlation, output verification and exit statuses. No operation resubmission or Host policy/runtime change. This changes pending-result detection latency: after backoff, a new result can wait up to 30 seconds for the next default read instead of six.

**Verification / limits:** Deterministic fake-clock tests cover immediate/delayed PASS, Host FAIL, wrong SHA, transient API timeout, sustained API outage, short deadlines, invalid intervals and 240-second pending execution: 11 logical lookups versus the prior 41 (73% fewer for that scenario only). New tests run in the existing control-verify workflow. Native CHAT UI, actual CHAT tool counts, ZERO ingestion coverage and rate-limit/freeze causation remain NOT_VERIFIED. PR #293's authenticated original-digest work remains independently owned; this diff changes only the poller's waiting loop, not digest provenance. Historical discussions remain GitHub history rather than another default rule source.

**Compatibility / rollback:** No receipt schema, workflow, credential, service or runtime activation changes. Revert this change to restore fixed polling and previous prose. README/Tree/Delta updated; existing Work Routine is the system document. Actual PR/commit/CI/handoff evidence belongs in the owning GitHub Issue/PR.

### 2026-10-17 — Restore working, scoped Current recovery without duplicate body reads

**Baseline / observed gap:** `SERVER_CORE_DESIGN.md` §2.2/§2.5 and Work Routine §6 require scoped context, actual Current and evidence reuse. The existing read-only `gace_project_current_recovery.py` fetched every registered Issue body but returned only its hash, requiring another read for the planner to understand it. A real GitHub request additionally rejected its original GraphQL query (`Expected ... actual: RCURLY` at line 8): extra closing brace. Previous fixture-only tests did not exercise that syntax.

**Delta:** Repair and format the existing query. Add repeatable exact `--issue-url` selection; validate the complete Project registration and duplicate identities before any Current body fetch. A missing selected Issue fails closed without fetching even the present subset. Fetch each selected Issue once; preserve fresh Issue identity/state checks (including fresh closed state overriding cached Project state), writer/CU readiness and `dispatch_authorized=False`. `--include-body` returns the exact fetched text with the existing hash/update evidence only when explicitly scoped and live-read; no default bulk context dump. Return the existing inventory by default for compatibility, with additive `registered_issue_count`. Detect multi-cursor pagination cycles. No cache, new transport, workflow or credential. LOAD_SCOPE shows optional local usage and retains direct existing GitHub connector reads for ordinary CHAT.

**Evidence / limits:** Focused fixtures include eleven registered contexts with one selected Current, omitted bodies for ordinary inventory, later-page selection, duplicate selectors, incomplete/duplicate registration, invalid selectors, unregistered selection, body/hash parity, fresh state and pagination cycles. Real authenticated GitHub read recovered Control #15 as one Issue among nine registrations, with full body/hash/timestamp; actual #40 selection returned `SELECTED_ISSUE_NOT_REGISTERED` and no Issue body reads before enrollment. These are read-only CLI evidence, not native CHAT behavior or a runtime/Host permission grant. Project #1 identity was independently read as `PVT_kwHODOQFoM4BEJII`, owner `seigo-gace`, number 1, open. Any later #40 enrollment/field changes require separate exact write/readback evidence in its Current.

**Compatibility / rollback:** Existing CLI without selectors remains full inventory; existing consumers retain result keys. Scoped body output is opt-in. Revert this change to remove the selectors, but retain a syntactically valid query if restoring the old interface. README/Tree/Delta and existing LOAD_SCOPE updated; existing control-verify tests cover the changed tool. No production/Secret/Provider operation.

### 2026-10-17 — Keep the mandatory README bootstrap a compact router

**Baseline / gap:** `SERVER_CORE_DESIGN.md` §2.2 and §2.5, `LOAD_SCOPE.md` and Work Routine §6 designate README as entry/status index rather than another rule authority. The mandatory README had 319 lines / 19,246 bytes: document inventories repeated the Task Routing table; shared capability, documentation and delegation details repeated their owning contracts; old Runtime SHAs/test counts were called "current live exact" despite its own historical-evidence warning. Its blanket merge/restart approval list conflicted with the current canonical `SERVER_CORE_PROTOCOL.md` Authority/Approval section, which already distinguishes routine delegated operations from protected effects.

**Delta:** Retain the executor bootstrap, dual-profile separation, fixed Tool A/B purpose/priority, all needed authority routes, Documentation Gate and Source/CI/Runtime separation. Consolidate document navigation into one Task Routing table; link detailed development, capability, deployment and delegation rules to their existing owners. Remove past runtime/test-count snapshots and internal implementation checkpoint narratives from default context; their history remains in Git, owning Issues and the existing WORKSPACE_MCP historical section. Route approvals to the actual Protocol/Work Routine instead of maintaining a conflicting second list. Native CHAT limitations and protected Host/Secret/provider/public boundaries remain explicit. No owner document, guard, permission, service or effective consumer configuration is removed.

**Evidence / compatibility:** This is bootstrap context cleanup only: no new loading procedure, automatic client adoption or behavioral PASS. Existing Rule Plane/static routing checks, local link targets and current CI validate repository compatibility. Existing README anchors had no active in-repository inbound fragment references at inspection. Runtime facts must still be read back from their owners. File/path entry remains README.md, rollback is a normal revert. README, Project Tree, MCP/Registry owner documents and append-only Delta updated; no new System Document.

**Related dead-route correction:** Link validation found that `operations/github-project-debugai-routing.json` had been deliberately removed by `b1081a1` (2026-10-14) while README/MCP/Registry/Tree still dispatched current common work through it. Route these entries to the existing server-core bounded Host contract and common Host document; do not recreate the retired catalog. Keep product-specific DebugAI MCP ownership distinct. Replace copied delegation rules in navigation/registry with the existing Protocol and registry references. Retain the single dated persistent qualification section and mark finite qualification as historical; prior detailed snapshots remain in Git history. The legacy verification script is retained for consumer compatibility but now emits `LEGACY_DEBUGAI_ROUTE_RETIRED` with exit 2 before jq/Docker when its required retired contract is absent. This prevents meaningless missing-file retries; it does not verify or activate a replacement runtime. A direct local negative smoke check and bash syntax check verify that path without any container call.

**Canonical Protocol consistency:** The same review found Protocol text saying only DebugAI was enrolled and that DebugAI owned all Host implementation. The current Source registry contains eleven explicit entries, and adopted Design §16.9.1 assigns the common Host to server-core. Replace the stale fixed count and blanket owner statement with exact per-entry Source/private-Host verification and product/common ownership separation. No Registry or Host grant is changed; eleven Source entries are not proof that every operation is live-admitted. Preserve all existing identity, effect, expiry/revocation, single-use receipt and protected-impact checks.

**Entry-link compatibility:** README's existing native-CHAT fragment had no matching section in the Host route document; the historical MCP heading's automatic slug also differed from its published links. Restore the short native entry (using existing Work Routine and direct Current reads) and an explicit historical anchor alias. Preserve PR #293's independently owned digest/transport paragraphs. These fixes make the existing entry navigable; they do not create native conversations or prove adoption.

### 2026-10-17 — Keep LOAD_SCOPE focused on progressive context selection

**Baseline / gap:** Design §2.2 and the existing README/Work Routine assign routing, context depth and execution to their respective owners. LOAD_SCOPE repeated the README authority table, GPT CHAT continuation paragraphs, a second pre-dispatch field list and long formatting lists for reading levels/document roles. Two source-reflect probe comments remained as historical test artifacts in the mandatory entry.

**Delta:** Use README's single Task Routing/document-role tables; retain Tool A/B-specific target links, exact profile bootstrap, scoped Current recovery and task-owner references. Condense Level 0–4, reuse and reading-stop descriptions without changing expansion criteria. Preserve the complete canonical-parent/one-writer/nested-worktree preflight, design baseline/drift handling, exclusions, live runtime readback and UNKNOWN/failure boundaries. Execution/reporting/handoff still belongs solely to Work Routine §6 and the selected profile. Remove historical probe comments from active context, with history remaining in Git. No guard, adapter, permission, runtime or Rule payload change.

**Validation / compatibility:** Existing Rule Plane and progressive-scope CI contracts, local Markdown link/fragment targets and diff checks validate compatibility. Entry path and key heading/contract markers remain stable; no new tests mirroring prose or another procedure. README/Tree/system-unit roles are unchanged; only existing LOAD_SCOPE and append-only Delta updated. Native CHAT adoption and performance remain separate real-use acceptance. Rollback is a normal revert.

### 2026-10-17 — Surface native Project Status conflicts before Current recovery

**Actual failure:** #40 was reopened after the PR #303 completion-keyword correction, but native Project Status remained Done. A later checkpoint was followed by another closure whose actual `closer` was Project #1 (`PVT_kwHODOQFoM4BEJII`), not a PR. Live metadata showed Status Done and enabled `Auto-close issue` / `Item closed` workflows. The exact workflow conditions were not exposed by the queried workflow metadata; do not infer that Gate CI_PASS itself is a universal close trigger. Source/CI evidence did not satisfy this CU's native CHAT acceptance.

**Correction:** Align only the owned #40 item's existing native Status to In Progress using normal delegated GitHub owner tooling, restore Gate SOURCE_IN_PROGRESS through existing bounded Project Control and reopen the unfinished Issue. Exact independent readback showed OPEN + In Progress + unchanged CU/owner. No global workflow or permission/field allowlist was changed. Source CI results remain evidence in Current, not overall completion.

**Existing tool gap / change:** Current recovery already fetched native Status in the Project response but discarded it. Return additive `project_status` metadata and `PROJECT_STATUS_RECHECK_REQUIRED` advice when a fresh OPEN Issue is still Done in Project. Closed Issues retain CLOSED_NO_DISPATCH precedence; other statuses and missing owner/CU behavior remain unchanged. This is read-only advice, not another admission gate or automatic status writer; no extra API call, Project field or control write operation. Existing four-field contract stays intact.

**Verification / compatibility:** Twenty recovery tests cover the observed open/Done mismatch, actual single-select representation, text fixture representation, In Progress readiness, closed-state precedence and one-body-read scope. Live repaired #40 readback returned OPEN / In Progress / READY_FOR_OWNER_CURRENT_RECHECK with dispatch_authorized=false. Rule Plane/static, compile and diff checks apply; existing control-verify runs the suite. Source recovery and state repair do not prove native CHAT behavior or permanent immunity from later external changes. README role unchanged; Tree, existing LOAD_SCOPE and Delta updated. Normal revert removes the additive advice; retain consistent native Status/Issue state.

## 2026-10-17 — Reuse protected local Writer results for private Artifact recovery

- **Baseline:** `GPT_CHAT_PROJECT_AGENT_DESIGN.md` §4/§6/§9.6, `SERVER_CORE_DESIGN.md` §16.5–16.7; complete correlated Host output without public disclosure or command replay.
- **Actual change:** Add an explicit local Writer-ledger input to the existing private-output publisher. Reuse export/ZIP verification, existing gh authentication, private-repository verification and the already installed TGserver private CI release-to-Artifact lane. Preserve encrypted/Vault input and deny implicit fallback. Export plaintext files with exclusive 0600 creation. Checkpoint restoration routes known failures to original Run readback before asking for full output.
- **Reason:** Actual DebugAI development resorted to 303 candidate-commit hash comparisons because its result preview contained metadata only. The protected local Writer exists while the encrypted inbox is absent. Same-Host recovery need not require an encryption roundtrip. A failure with incomplete preview also incorrectly advertised payload recovery as its first action.
- **Scope:** Existing server-core publisher/export/checkpoint and tests; no Host registry, permission, workflow, service, token or DebugAI product change. Remote CHAT still requires its actual admitted Host/Artifact access.
- **Evidence / applied commit:** Owning CU #40, implementation PR/commit and runtime readbacks are recorded in GitHub work history. Source/CI/private Artifact transport/native CHAT consumption are separate qualifications.
- **Compatibility / rollback:** Existing encrypted CLI remains valid and still requires its Vault consumer/ref. Writer input is explicit and mutually exclusive with Vault consumer selection. Normal source revert removes the option; existing Writer results and original request IDs are preserved. A recovered output never promotes a failed or truncated original command to PASS.
- **Verification:** Focused positive/negative tests cover Unicode bytes/digests, ledger mismatch/change, absent results, recipient privacy, file modes, cleanup and known-failure routing. Live private handoff and native CHAT acceptance require their own evidence; no client-performance guarantee.

## 2026-10-17 — Connect existing private Artifact readback to CU continuation

- **Baseline:** `GPT_CHAT_PROJECT_AGENT_DESIGN.md` §4/§6/§9.6, `SERVER_CORE_DESIGN.md` §16.5–16.7; exact correlated output before acceptance and no unverified stage promotion.
- **Actual change:** Existing gh restoration reads one explicitly selected private CI Run and its request-named Artifact. Reuse the existing publisher's fixed destination, stable paginated listing, independent stream metadata admission and streaming ZIP verifier. Existing CU continuation accepts `--private-output-run-id` as an alternative to a local ZIP, checks the original Host Run first, then returns metadata-only proof and removes plaintext. No new transport/workflow/token/service.
- **Reason:** PR308 established private publication and authenticated recovery, but the consumer required a one-off download/unwrap command before continuation. Integrating the already verified route removes this manual handoff without treating metadata as payload.
- **Evidence / applied commit:** Owning CU #40 and implementation PR carry exact commit/CI. Actual original request `req_04470476d9ab5df3b96722bb` / Run38938744232 and private Run38943523980/Artifact12063644111 reached `VERIFY_CU_ACCEPTANCE` through the CLI; same Artifact was also obtained by the existing GitHub connector and verified from its file reference. This is executor/connector evidence, not fresh-native-CHAT acceptance or a browser fix.
- **Compatibility / rollback:** Existing local ZIP and discovery/checkpoint interfaces remain; payload inputs are mutually exclusive. The outer and inner archives retain explicit size/compression limits; oversized output is rejected, never silently truncated. Failed/unfinished/truncated original work cannot trigger private consumption or acceptance. Normal revert removes the optional input; no runtime migration or registry change.
- **Verification:** Positive/negative tests cover private recipient, event/workflow/Run/Artifact provenance, expiry/ambiguity, independent digests, Unicode payload, bounded streamed download, wrapper traversal/expansion and temporary-file cleanup. Main CI and native CHAT usage remain separately qualified in GitHub work history.

## 2026-10-17 — Resolve private output by the original request identity

- **Baseline:** Prior private Artifact→continuation delta; GPT_CHAT_PROJECT_AGENT_DESIGN §4/§6/§9.6. Original request identity and independent output digests remain the trust boundary.
- **Actual change / reason:** Explicit `--recover-private-output` filters the existing private recipient's Artifact collection by exact original request name and derives the private Run from one complete, unique, unexpired match. This removes the remaining manual private-Run-ID handoff without a new index or transport. Reuse that Artifact listing rather than fetch it again by Run.
- **Evidence:** Existing request filter returned one actual Artifact; nonexistent request filter returned zero. Owning CU40/implementation PR record tests and original-request CLI readback.
- **Scope / compatibility:** Existing reader/continuation and tests only. All subsequent private Run provenance, bytes/chars/digest and cleanup checks remain. Missing/expired/multiple candidates reject; explicit private Run remains available for ambiguity. No latest-result guessing, new Host execution or authority expansion. Normal revert removes the optional discovery flag.
- **Verification:** Stable pagination/duplicate candidates, absent/expired/malformed references, mutually exclusive CLI inputs and original-request recovery covered by focused tests; CI and native CHAT qualification remain separate.

## 2026-10-17 — Reuse verified private results before publishing again

- **Baseline:** Prior private recovery deltas and GPT_CHAT_PROJECT_AGENT_DESIGN §4/§6/§9.6; request identity, complete output, private boundaries and no blind replay.
- **Actual change / reason:** Retrying an export could start another private CI and create multiple live candidates for the same original result. Existing publisher now invokes the same authenticated reader with independent Writer-derived expectations and returns existing verified Run/Artifact IDs without creating a release/CI. This is the chosen bounded automation; no resident bot or new service.
- **Compatibility:** Only missing/all-expired results allow private republication from the already stored Writer result. Corruption, privacy/permission errors and multiple live candidates fail without new publication. Recovery ignores expired copies but never selects between multiple live copies by timestamp. Existing encrypted/local inputs and explicit Run selection remain.
- **Evidence / applied commit:** Owning CU40 and implementation PR record exact source/test/CI and read-only actual reuse proof. Local full payload consistency and remote original request identity remain separately verified. Normal source revert restores prior publication behavior without deleting stored results.
- **Verification:** Existing/new-result, reuse, ambiguity/corruption/unavailability, expiry and live-versus-expired candidate tests; actual reuse is tested with a runner that prohibits any GitHub mutation. Native CHAT continuity and browser symptoms remain separately unverified.

## 2026-10-17 — Deterministic command authoring before the existing Host lane

- **Baseline:** COMMAND_ROUTINE, Work Routine §6, GPT_CHAT_PROJECT_AGENT_DESIGN §4/§6/§9.6 and SERVER_CORE_DESIGN §16.5–16.7: exact admitted command/evidence and continue after concrete failures.
- **Actual change:** Reuse the existing isolated selector for nonexecuting Bash syntax and recognized literal Python-heredoc compilation. A small authoring helper compiles supplied Python, renders a quoted heredoc, serializes caller-provided draft metadata, generates a compliant unique filename and reuses selector diagnostics. It never dispatches, fabricates START/authority receipts or claims complete parsing of dynamic code. Existing request-file admission remains unchanged.
- **Reason / evidence:** Protected records contained nine stdin Python syntax failures and two Shell/EOF failures. All 100 stored request bodies passed local syntax; replay through installed Gateway sanitizer altered18 and made11 invalid. Therefore static authoring is one layer; lossless transmission is an independent real dependency tracked by webhook-gateway#28, not a solved issue by prose or compilation alone.
- **Scope / compatibility:** Existing Selector/verify workflow plus helper/tests/docs; ordinary fixed operations and Source-context admission retained. Generic Gateway preserve policy is destination-owned, retains default/audit sanitization and requires separately verified Source/CI/runtime. No new service/token/permission or paid agent. Source work uses owned nested worktrees to preserve shared canonical checkout.
- **Verification / rollback:** Focused syntax, quoting, Unicode, no-side-effect, incomplete-heredoc, unknown dynamic coverage, Source context and actual sender/receiver regressions; exact CI/readback in CU40/PR. Revert this Source diff normally; no irreversible data or runtime schema migration.

## 2026-10-17 — Keep the GPT app Agent Loop and Notion obligations out of server executors

Master clarified that the Agent Loop and Notion apply only to GPT app CHAT. The shared Work Routine/rule-plane ownership wording could imply that all agents must follow CHAT continuation, reporting and Notion recording. Clarify only the CHAT design, Work Routine scope and router: GPT CHAT owns Notion discussion/decision records; Cursor/Codex/server executors use their existing minimum profile and normal tools, returning Source/CI/Runtime evidence without a Notion prerequisite.

Canonical GPT CHAT Rule #17 was updated and read back. Server Rule #16, AGENTS/Cursor/Copilot adapters, Manifest, Notion pages and enforcement/runtime contracts are unchanged. Common authorization, Secret safety, owning Current and GitHub work history still apply. This is a scope correction, not another procedure, tracker or runtime activation. Revert these documentation changes if this clarified boundary is withdrawn; no runtime data rollback is involved.

## 2026-10-17 — Repair actual Notion evidence restoration without blocking GPT CHAT continuation

DebugAI #41 reported an OpenAI safety-check rejection of a Notion append; its later report repeated the same incident, not a proven second attempt. Current live fetch reproduced a separate Source defect: an over-escaped page-header regex rejected valid Notion pages. Four of 25 preexisting Notion tests failed; the existing CI had not run that suite. Fix the actual header match, normalize real MCP wrappers, reject explicit tool errors, and keep optional Notion failures from discarding an already verified Run/Host continuation. Add the existing suite to the existing verify workflow and focused negative/CLI recovery coverage.

Current authorized Bootstrap and DebugAI diagnostic updates used normal Notion page insertion, async completion and readback. This proves those new writes, not clearance of the earlier rejected payload or a general change in provider safety policy. No alternate-tool retry of a denied request, Token, workflow, server-profile or product code change. Rule applicability remains GPT app CHAT only. Four-project evidence is scoped in CU40; indexed IDE/Codex conversations must not be counted as independent native GPT chats, and incomplete ZERO coverage/failed time-filter queries do not prove absence. Existing minimal server-AI and Notion ownership boundaries remain.

## 2026-10-23 — Master-only AI delegation and persistent common Host transport

Baseline: CHAT could select an efficient AI delegate; common Receiver/Tunnel lacked a committed Compose recovery definition, and Sender did not bind command content across Gateway normalization.

Change: CHAT must obtain individual explicit Master permission before other-AI execution/review; ordinary shell/CI work continues under existing admission. Automatic AI PR reviews are prohibited. Retain the original Mission/acceptance instead of substituting intermediate tests/records. Add UTF-8 command digest validation before execution and a Compose definition for the existing Receiver/Tunnel with restart recovery. Keep compatibility command receivers separate from the normal CHAT menu.

Evidence/reason: CU40 audit 2026-10-23 found stopped Receiver/Tunnel, four Gateway HTTP530 failures, one invalid receipt enum and automatic Codex PR-open reviews. Prior Source/CI success did not establish native CHAT adoption.

Scope/rollback: GPT CHAT policy, common transport and existing infrastructure only; no SERVER_AI profile, product source or protected deploy authority change. Old authenticated deliveries remain compatible. Revert the Source change and restore the saved old Receiver if transport qualification fails; preserve Gateway destinations, existing DNS/config and all request IDs. Exact Source/CI/runtime outcomes and remaining external review-setting access are recorded in CU40 rather than inferred here.

## 2026-10-28 — Common Receiver socket readiness and bind recovery

Baseline: HTTP-only health returned200 even when Host Writer and Result Sink sockets were unavailable; unless-stopped alone did not repair a live Receiver's stale `/run/gace` directory bind.

Observed failure: the two original events reached Receiver, failed503 DEPLOY_EXECUTOR_UNAVAILABLE eight times and became dead. Host and Receiver had different directory inodes; Receiver saw an empty old directory. Refreshing the mount restored both sockets. Existing authenticated Admin replay of the same delivery IDs then produced first Host execution, published PASS results and delivered200, retaining all prior attempts.

Change: check both fixed local RPC listeners with an empty invalid-schema probe that dispatches/persists nothing; health returns503 when unavailable. After60seconds continuous loss, gracefully stop Receiver so its existing Compose policy remounts the current directory. Transient failures reset the grace window. Future Source-reflect installer units preserve the shared runtime directory. No additional listener, Docker authority in Receiver, model, agent, replay daemon or result store.

Verification and rollback: focused tests and staged directory-replacement qualification, exact Source/CI/runtime evidence in CU40/#10. Previous Receiver image/container is retained for rollback; deployment does not re-execute original commands. The existing root-owned unit's preservation flag is separate Host admission and not inferred applied from Source.

## 2026-10-29 — TGserver administration through server-core

Baseline: registration was owner-side manual editing plus read-only onboarding
audit; no command-center administration entry. Master requested central Project
and Group growth management. Added scripts/tgzero_admin.py as a thin structured
argv router to TGserver-owned plan/apply/recovery and its existing Topic provisioner.
No second registry, Bot, daemon, HTTP API, AI delegation or runtime auto-deploy.
Capacity and registration rules stay in TGserver ZERO Operations; current evidence
stays in owning Current#50 rather than a historical PR number. Source/CI/runtime
remain separate. Router regression tests qualify argument boundaries and reuse of
the actual running image. Removing this entry reverts routing only; preserve live
registry, Topics, pending/private recovery journals and all provider history.

### TGserver router CI ownership correction

The initial routing commit also inserted its regression into the CU40-protected
shared guard workflow. Main push admission rejected that workflow edit although
the new regression passed. Restore the shared guard to its prior bytes and run
TGserver owner-routing tests in a narrow, read-only dedicated workflow. This
correction itself uses the required PR design preflight and merge; no admission
checks are removed or weakened. The rejected run remains historical evidence.
