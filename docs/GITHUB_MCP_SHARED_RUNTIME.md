# Shared official GitHub MCP — source-only deployment gate

**Owner**: `G-ACE-inc/server-core#10`. Executor: existing G-ACE/DebugAI guarded
Host path, not a new shell proxy. The existing GitHub Projects mutation owner
remains `scripts/github_project_control.py` (GraphQL + exact readback).

## What this adds

`docker-compose.github-mcp-readonly.yml` describes the official
`ghcr.io/github/github-mcp-server` image in native HTTP mode, with only the
`projects` toolset and **global read-only** policy. It joins the same
`gace-internal` network already required by Project Control.

This file is **source-only**: it has not downloaded an image, installed an
MCP client, created a network, changed permissions, created a token, or started
a container. The existing `operations/workspace-mcp.json` is unchanged:
only advertise the shared capability as available once the real runtime is
healthy and its permitted caller-specific authentication is demonstrated.

Official upstream:
- https://github.com/github/github-mcp-server
- https://github.com/github/github-mcp-server/blob/main/docs/streamable-http.md

## Reused bounded Project Current reader (source only)

`scripts/github_project_read_current.py --item-url <approved GitHub Issue or PR URL>`
reads one known item. `scripts/github_project_read_current.py --all-registered`
reads the **actual registered** Project #1 Issue/PR items (maximum 25)
by reusing the existing `gh project item-list` + four existing GraphQL
field readers. Duplicate IDs/URLs fail closed; foreign-owner or draft items
are counted as excluded, making the result `PARTIAL` rather than claiming
an exhaustive/current authority for unsupported items. Missing canonical control/rule-plane
Issues #10/#15/#16/#17 are derived from the existing Rule Plane manifest
and Project Control result sink and explicitly returned under
`unregistered_control_issue_urls` with `status=PARTIAL`. No fake Project
items or fields are generated. Both modes
reuse the **existing** `github_project_control.py` Project identity, item lookup,
field-read GraphQL and error contracts. It reads **only** `Wave`, `Gate`,
`Change Unit` and `Mutation Owner` for Project #1 and emits sanitized JSON;
unassigned fields stay `null` and return `PARTIAL`. Invalid targets and missing
GitHub permissions fail closed. No second mutation engine, generic GraphQL
forwarder, new transport, token, runtime permission or additional repository
registration is created. Its source tests run in existing Project Control CI.

This is a bounded diagnostic/readback helper for an **already authorized**
Server AI/Host execution context, not proof that GPT CHAT can execute it or
that real GitHub Project field values have been retrieved. Do not deploy it
through a new uncontrolled shell path. The official MCP remains the adopted
shared Project read capability; these existing GraphQL readers are reused,
not a replacement for the official MCP Server-AI/CHAT E2E acceptance.

## Independent Host ephemeral runtime evidence (2026-10-08)

The existing authorized Server AI executor (Composer) has **separately** tested
the exact official digest on the actual VPS in a *temporary, non-production*
container with loopback-only binding. The evidence is in
[server-core #10 / comment 6059563905](https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-6059563905):

- Host `x86_64` pulled image RepoDigest exactly matched the pinned SHA.
- No token: HTTP 401; malformed Bearer: HTTP 400.
- A permitted **per-request Host gh credential** (secret value never recorded)
  yielded MCP initialize HTTP 200, `tools/list` containing exactly the two
  read-only Project tools `projects_get` / `projects_list`, and a live
  `projects_list` result identifying Project #1.
- The ephemeral container was removed; no production Compose stack, public
  listener, new Secret, network, Project field mutation or client registration.
  Existing 13-tool DebugAI MCP remained operational.

**Do not promote this evidence to persistent Host Runtime verification.**
`gace-internal` and the Project Control receiver were absent on the Host
during preflight; `server-core` checkout was still `main`, not this PR.
Persistent private-network installation, authorized client registration and
full shared Server AI/GPT CHAT E2E remain separate admission gates.

Independently, Codex performed read-only authenticated Project #1 item/field
readback: [Issue #10 / comment 6059550077](https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-6059550077).
All 8 registered items and four exact fields per item were retrieved and
unchanged, with some `Wave` values `null`; controlling Issues #10 and #15
were **not registered** in the Project. This is an actual observation, not
authorization to add items, invent missing field values, or update any Gate.

The diagnostic helper is not an enrollment tool: actual Project item-add is
a separate authenticated, single-writer mutation carried out only by the
authorized owner. It is never inferred from a comment, a registry file, or
an absent Issue ID.

## Activation prerequisites — must be demonstrated, not assumed

1. The Source image is now pinned to the **official GitHub GHCR v1.11.0
   multi-architecture manifest** by immutable SHA256 digest
   `fbec75de11c255213fa08d80fb166abe73d851fff631c51c0079872967720699`.
   Source: https://github.com/github/github-mcp-server/pkgs/container/github-mcp-server/1170256861
   CI checks the registry manifest instead of inserting a dummy digest.
   The tag is provenance metadata, **never** a mutable pull reference.
   The Host must still independently read back the actual pulled digest,
   compatible platform, runtime argv, process identity and allowed caller
   before runtime admission. The current PR CI also runs the exact pinned
   image as nonroot/read-only with a loopback-only port on an ephemeral
   GitHub-hosted runner, then performs an unauthenticated MCP JSON-RPC
   initialize request; HTTP 401 and the Bearer authentication challenge
   are mandatory. This test uses no GitHub credential and performs no
   Host deployment, so it proves **missing-token rejection**, not authorized
   Project tool discovery, permitted credential scope or Host E2E.
   Evidence: https://github.com/G-ACE-inc/server-core/actions/runs/37775172247
   (`GITHUB_MCP_EPHEMERAL_HTTP_NO_TOKEN_DENIED=PASS`).
2. Verify the intended consumer, authorization and actual GitHub Projects
   credential scopes. HTTP accepts a **per-request** bearer credential
   supplied by a trusted client, not a globally shared token in this Compose
   file. No plaintext credentials in Git, Chat, logs, or a published endpoint.
   Host `gh auth status` proves a Host client, not this container's identity.
3. Check/create the approved dedicated, private-inbound `gace-internal`
   network. `internal-only` in this design means **no Host-published service
   ports and only admitted clients**, not Docker's network `--internal`
   isolation flag. When the MCP joins only an `--internal` network, it has no
   normal default route for outbound HTTPS to `api.github.com`; Projects
   read calls then fail unless an **independently reviewed egress proxy**
   exists. Use a dedicated user-defined bridge with controlled membership
   and normal outbound GitHub API HTTPS only after permitted admission;
   verify DNS/HTTPS and inbound isolation before declaring E2E complete.
   Creating this network is an explicit protected Host effect, not implied
   by source/CI success. Do not start the Project Control receiver with
   the read-only MCP: the two Compose services have **no direct dependency**
   and require separate admission. Docker authority:
   https://docs.docker.com/reference/cli/docker/network/create/#network-internal-mode---internal
   https://docs.docker.com/engine/network/drivers/bridge/
4. The pinned image's HTTP arguments, nonroot/read-only isolated
   startup and missing-token HTTP 401 have passed in CI. The actual Host
   still must confirm internal connectivity without publishing a host
   port, and authenticated `projects_list` / `projects_get` for
   G-ACE Development Platform #1 and fields `Wave`, `Gate`,
   `Change Unit`, `Mutation Owner`.
5. Verify no credential is reused outside its explicit allowed consumer and
   no tool allows Project mutations under this read-only service.
   Test missing/invalid-scope credentials are rejected.
6. Register the **bounded** Server-AI client only after success. To enable
   CHAT, use the existing GitHub→Actions→Cloudflare Access→DebugAI
   request/status path with an explicit allowed command schema, actor,
   exact Project/Item/Field constraints and safe readback. Do not forward
   raw user-supplied MCP tool names or arbitrary JSON. Project writes must
   keep the existing server-core identity/HMAC/GraphQL authorization.
7. Record Source SHA, image digest, runtime container identity, credential
   identity/scopes (not secret), unauthorized-deny evidence and audit; only
   then classify the capability as RUNTIME_VERIFIED.

## Phase A admission (Host — separate from Source/CI)

Machine contract: `operations/github-mcp-readonly-runtime.json`.  
Rollback and network rules (bridge **without** Docker `--internal`, no host port publish,
DebugAI not on `gace-internal` today): `docs/GITHUB_MCP_PHASE_A_ADMISSION.md`.

| Gate | Phase A (readonly MCP) | Phase B (Project Control receiver) |
|------|------------------------|-------------------------------------|
| Compose file | `docker-compose.github-mcp-readonly.yml` | `docker-compose.project-control.yml` |
| Required for the other | **No** | **No** |
| Shared network name | Optional `gace-internal` bridge only | Same optional name |
| `workspace-mcp.json` advert | **After** RUNTIME_VERIFIED E2E | N/A |

CI (GitHub-hosted): bridged MCP without published ports (Docker inspect readback),
inbound 401 without token, and outbound `https://api.github.com` probe from a **sidecar**
on the same bridge (`scripts/github_mcp_ci_bridge_egress_verify.sh`). Unreachable egress
exits nonzero (`NETWORK_INCONCLUSIVE=YES`). CI does **not** prove authenticated MCP
`projects_*` on the bridge (`ci_verification` in `operations/github-mcp-readonly-runtime.json`).

## Change Unit boundary

Only Source/Test/CI are in scope here. No Host, Secret, Docker, production,
GitHub Project fields, commercial approval paths, existing DebugAI 13 tools,
TGserver ZERO or user Cursor configurations were changed.
