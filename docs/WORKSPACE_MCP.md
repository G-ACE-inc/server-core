# WORKSPACE SHARED MCP

Version: 2026-10-01

## Purpose

Workspace共通MCPをProjectごとに複製せず、CursorのUser Global MCPを共通入口として利用するためのContract。

Cursor公式仕様では、Project `.cursor/mcp.json` とUser Global `~/.cursor/mcp.json` が別の設定源として存在し、Global設定は全Projectで利用できる。Project設定は必要なProject固有MCPだけを追加し、Workspace共通MCPを各Repositoryへコピーしない。

## Architecture

```text
G-ACE Workspace
      |
      v
server-core
      |
      +--> WORKSPACE_REGISTRY
      |
      +--> operations/workspace-mcp.json
      |
      v
~/.cursor/mcp.json
      |
      +-------------------------------+
      |                               |
Project A                         Project B
Project C                         Project D
      |                               |
      +---------------+---------------+
                      |
                Shared MCPs
```

## Current server-side configuration state

Server readback on 2026-10-01 confirmed that `/home/admin1/.cursor/mcp.json` contains the following global entries:

| Server | Ownership in server-core manifest | Configuration state | Live availability state |
|---|---|---|---|
| Cloudflare API | managed by `operations/workspace-mcp.json` | `CONFIG_REGISTERED`; installer/verify PASS | authentication / transport / tool discovery / representative call still `NOT_VERIFIED` |
| Hugging Face | managed by `operations/workspace-mcp.json` | `CONFIG_REGISTERED`; installer/verify PASS | authentication / transport / tool discovery / representative call still `NOT_VERIFIED` |
| DebugAI | managed by `operations/workspace-mcp.json`; implementation remains `seigo-gace/debug-ai` | `CONFIG_REGISTERED`; installer/verify PASS | 13 tools, health, bounded Server Command and guarded deploy live PASS on the explicitly reflected revision |
| GitHub | pre-existing global entry; preserved, not rewritten by current manifest | `CONFIG_PRESENT` | live Cursor-client verification remains separate |
| Deterministic Japanese Parser | pre-existing global entry; preserved, not rewritten by current manifest | `CONFIG_PRESENT` | live transport / tool discovery / representative call remain `NOT_VERIFIED` |

The installer preserves unrelated existing MCP servers. Therefore `CONFIG_PRESENT` for GitHub / Parser does not mean server-core has taken ownership of their runtime definition.

Current Server shell does not have Cursor Agent CLI installed. `agent mcp list` is therefore not used as the verification route on this host.

## Manifest-managed shared servers

| Server | Endpoint | Authentication | State |
|---|---|---|---|
| Cloudflare API | `https://mcp.cloudflare.com/mcp` | Cursor OAuth | `CONFIG_REGISTERED`; live connection pending |
| Hugging Face | `https://huggingface.co/mcp` | Provider/Client OAuth or generated client config | `CONFIG_REGISTERED`; live connection pending |
| DebugAI | `/usr/bin/docker exec -i debug-ai-debug-ai-1 node /app/bin/debugai-mcp.mjs` (stdio) | existing Docker Compose runtime; no Provider token in manifest | configuration/discovery/health and representative Server execution are separate gates |

Cloudflare documents Cursor integration through its API MCP and OAuth authorization. Hugging Face provides an official MCP server for Cursor and other MCP-compatible clients.

## Why Global MCP

The previous failure mode was:

```text
Project A
  -> .cursor/mcp.json
  -> works

Project B
  -> no registration
  -> cannot use

Project C
  -> token/config missing
  -> cannot use
```

The common route is now:

```text
All Projects
   |
   v
Cursor User Global MCP
   |
   +--> Cloudflare API MCP
   +--> Hugging Face MCP
   +--> DebugAI MCP (existing stdio implementation)
   +--> preserved pre-existing global MCP entries
```

Project-specific MCPs remain project-scoped.

## Secret / Token rule

Do not place Provider tokens in this repository or in the shared manifest.

For OAuth-capable remote MCPs, authenticate once at the global Cursor MCP layer. The Project repositories do not receive the token.

If a Provider requires a bearer token instead of OAuth, the token must come from the approved Workspace Secret Contract / Libral Vault path. Do not copy it into a Project `.cursor/mcp.json`.

## Installation

Run only from the canonical server-core checkout:

```bash
cd /home/admin1/server-core
scripts/install-workspace-mcp.sh
```

The installer:
1. validates the server-core manifest;
2. creates `~/.cursor/mcp.json` if absent;
3. preserves unrelated existing MCP servers;
4. adds the Workspace shared entries;
5. refuses a name collision with a different runtime definition;
6. creates a timestamped backup before mutation;
7. preserves existing credential containers covered by the merge policy;
8. never writes a Provider token from the repository.

## Workspace initialization

The Workspace initializer is the canonical entry for rules + managed global MCP configuration:

```bash
cd /home/admin1/server-core
scripts/init-dev-workspace.sh
```

It must run from `/home/admin1/server-core`. A duplicate checkout such as `/home/admin1/projects/server-core` is rejected before mutation. After installing the managed MCP entries, the initializer also runs `scripts/verify-workspace-mcp.sh`; configuration verification failure therefore prevents a successful initialization result.

## Verification

```bash
scripts/verify-workspace-mcp.sh
```

The verification command checks:
- global MCP file exists;
- JSON is valid;
- required manifest-managed Workspace servers exist;
- runtime transport definition matches the manifest contract;
- no obvious plaintext token pattern is embedded;
- when Cursor CLI is installed, `agent mcp list` can be used as an additional live client-side check.

A valid config is not equivalent to a live connection.

For the existing local DebugAI route, run `bash scripts/verify-debugai-project-route.sh`.
The client checks thirteen tools, health, rejection of an unapproved GitOps
request, and a real `project.git_head` request/status lifecycle against the Host
checkout. Fast operations may complete between polls; `started_at` and
`finished_at` bind actual execution even when a RUNNING poll is not observed.
This check grants no deploy approval and does not test a remote CHAT connection.

```text
CONFIG_PRESENT / CONFIG_REGISTERED
  -> AUTHENTICATION_VERIFIED
  -> TRANSPORT_VERIFIED
  -> INTERFACE_DISCOVERY_VERIFIED
  -> REPRESENTATIVE_CALL=PASS
  -> AVAILABLE_VERIFIED
```

## Project boundary

Project repositories do not need to contain these shared MCP entries.

A Project may contain a `.cursor/mcp.json` only for Project-owned or explicitly Project-scoped MCPs.

If a Project has the same server name as a global shared MCP, the Project definition takes precedence in Cursor. Therefore manifest-managed shared server names are reserved unless an explicit Project override is approved.

## DebugAI / private MCP boundary

DebugAI MCP **is implemented**. Current DebugAI authority records stdio source/unit/real-protocol verification, 9 MCP tools, health, and durable continuation surfaces as PASS. Master also reports prior successful Codex use of DebugAI, so server-core must not classify DebugAI MCP as `NOT_IMPLEMENTED`, `NOT_REGISTERED`, or as having no usage history.

The shared control-path verification is bound to the explicitly reflected revision,
not an arbitrary future DebugAI HEAD. Live stdio discovery/health and real Server
Command request/status/Host HEAD readback passed on reflected
`cc3462ddb07fb1379d61dc7c2321a776794800c1`. The owning repository's unrelated
workflow, benchmark, durable-continuation and Strict Completion qualifications
remain separate from this bounded control route. The existing guarded GitOps deploy
completed PASS under a new single-use exact-SHA Host receipt. The existing watcher
runs both bounded Bash runners with authorized Docker group access; no new executor
or queue was introduced.

Use the following distinction:

```text
MCP_IMPLEMENTATION=VERIFIED
MCP_PROTOCOL=VERIFIED
PRIOR_CODEX_USAGE=CONFIRMED_BY_MASTER
REFLECTED_SERVER_HEAD=cc3462ddb07fb1379d61dc7c2321a776794800c1
REFLECTED_SOURCE_IMAGE_PARITY=PASS_263_PACKAGED_FILES
WORKSPACE_REGISTRATION_READBACK=PASS
REPRESENTATIVE_SERVER_COMMAND_MCP_CALL=PASS
GUARDED_GITOPS_COMPLETION=PASS
GUARDED_GITOPS_DEPLOY_ID=gitops_7f181b2e296bb0cace801248
REPRESENTATIVE_SERVER_COMMAND_ID=cmd_01cb05dfdc1e107505c660bf
HOST_APPROVAL_REJECTION=PASS
PROJECT_COMMON_SERVER_E2E=PASS
REMOTE_CHATGPT_DIRECT_MCP_CONNECTOR=NOT_VERIFIED
```

Do not downgrade an already implemented/previously used MCP to `NOT_IMPLEMENTED` merely because the latest exact HEAD has not yet been re-verified live. Conversely, prior use is not proof that the current in-progress HEAD is live and identical; current-head availability remains a separate verification state.

Do not invent a new local path or endpoint while DebugAI is being changed. server-core owns the discovery/registration/verification contract; DebugAI owns its implementation body.

Current registration runs the existing `/app/bin/debugai-mcp.mjs` inside the existing `debug-ai-debug-ai-1` Compose container through `operations/workspace-mcp.json`. Host Node/Python is not required for MCP execution. No TTY is allocated, preserving stdio JSON-RPC. Container name is bound to the current Compose deployment; if it changes, update and reverify the contract rather than selecting an arbitrary container.

The installer permits migration only from the manifest's explicit prior DebugAI command definition, preserving covered auth containers and backing up the existing file. Unknown transport collisions still fail closed. Host environment fields are preserved in the client config; `docker exec` does not forward them automatically. The existing container's runtime environment remains authoritative.

GitHub Project server-operation routing is fixed separately in `operations/github-project-debugai-routing.json`; server-core owns that routing contract, while DebugAI retains all MCP/Server Command/GitOps implementation. Cursor global registration does not configure a remote ChatGPT connector; CHAT-side tool availability must be verified on that execution surface separately.

## Deterministic Japanese Parser MCP

The Server global Cursor config now has a Deterministic Japanese Parser entry. This closes only the configuration-presence boundary.

The current server-core manifest does not own or rewrite that pre-existing entry. Before promoting it to `AVAILABLE_VERIFIED`, verify the actual client execution route, authentication when required, transport, tool discovery, and at least one representative parser call. Do not infer live availability from the JSON entry alone.

## Non-goals

- No Project code moved into server-core.
- No Provider credentials stored in Git.
- No automatic Provider mutation.
- No production deployment.
- No assumption that configuration equals runtime availability.

## Standing Delegation routing

Existing `debugai_gitops_request/status` supports the Host-installed Standing
Delegation reference for bounded `deploy` / `debugai.compose.reflect`. Routing
contract: `operations/github-project-debugai-routing.json`. Implementation and
trust/receipt/revocation contract stay in owning DebugAI
`docs/GITOPS_STANDING_DELEGATION.md`. No extra MCP approval tool or transport exists.

Master may preauthorize this narrow technical scope. CHAT/Codex then decides and
requests reflection; the Host verifies its installed issuer/policy, exact target,
scope, identity, expiry/revocation, changed paths and single-use receipt. CHAT text
and `human_approved` are not credential proof. Legacy manual receipts remain
compatible. Secret/provider/model/public/persistent/destructive effects and broader
DebugAI patch approval are not granted by this route. Remote ChatGPT direct
connector registration remains a separate availability boundary. Source/CI
qualification does not imply delegated Runtime E2E.

Standing Delegation live qualification is bound to reflected `cc3462ddb07fb1379d61dc7c2321a776794800c1`,
not future source. Delegated MCP deploy `gitops_7f181b2e296bb0cace801248` showed
QUEUED -> RUNNING -> PASS without a manually created per-operation receipt.
Status returns the installed Master delegation `dlg_debugai_reflect_v1`, issuer,
exact operation/SHA/scope and receipt consumption timestamp. Duplicate replay
was rejected without changing its original terminal status or recreating the
container. A missing-policy live request was rejected before receipt issuance.
The installed narrow reflection policy expires 2026-10-15 14:03:30 JST; it grants
no destructive/persistent/Secret/provider/model/public-exposure mutation.
CLI/MCP availability in this Codex execution environment does not prove direct
remote ChatGPT app connector installation or broader PR #40 product completion.

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
