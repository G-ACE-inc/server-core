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
