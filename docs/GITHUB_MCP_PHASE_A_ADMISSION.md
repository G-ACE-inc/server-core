# Phase A — Official GitHub MCP read-only (Host admission)

**Owner:** `G-ACE-inc/server-core#10`  
**Source:** `docker-compose.github-mcp-readonly.yml` + `operations/github-mcp-readonly-runtime.json`  
**Out of scope here:** Project Control Receiver (Phase B), `workspace-mcp.json` advertisement, Host deploy without receipt.

## Phase A vs Phase B

| | Phase A (this doc) | Phase B (separate CU) |
|---|-------------------|------------------------|
| Compose | `docker-compose.github-mcp-readonly.yml` | `docker-compose.project-control.yml` |
| Purpose | Read-only Projects MCP (`projects_get`, `projects_list`) | Field-mutating receiver + Gateway HMAC |
| Depends on other | **No** | **No** (optional shared network name only) |
| Secrets in compose | **None** (per-request Bearer) | Delivery secret file + `gh` config mount |
| Host admission | Required before `up -d` | Separate admission |

## Network (inbound private, outbound GitHub HTTPS)

Create a **user-defined bridge** network. **Do not** use Docker’s `--internal` network flag as the only network for the MCP service: that blocks default outbound routes and breaks GitHub API HTTPS unless a separately reviewed egress proxy exists.

```bash
# Protected Host effect — run only after explicit admission / receipt.
docker network create "${GACE_INTERNAL_NETWORK_NAME:-gace-internal}"
# Correct: plain bridge (no --internal)
# Wrong for MCP egress: docker network create --internal gace-internal
```

- **Inbound (no port publish):** the compose service must not map container port 8082 to a host `ports:` binding, so the service is **not reachable from the ordinary public Internet** via published NAT. On a default **user-defined bridge**, Docker also allows reachability from **attached containers and the Docker Host** (see [bridge driver](https://docs.docker.com/engine/network/drivers/bridge/) and [port publishing](https://docs.docker.com/engine/network/port-publishing/)). This is **not** `network_mode: host`. Security still requires **`--scope-challenge` and a per-request Bearer on every MCP call** for every caller (Host-local or container).
- **Outbound:** normal DNS + HTTPS to `api.github.com` (and related GitHub API hosts) from the MCP container.

Machine contract: `operations/github-mcp-readonly-runtime.json`.

## Trusted Server AI client (current limitation)

| Fact | State |
|------|--------|
| DebugAI stdio MCP | Verified via `operations/workspace-mcp.json` → existing Compose container |
| DebugAI container on `gace-internal` | **No** (current Host) |
| Intended routing authority | `operations/github-project-debugai-routing.json` |
| Post-admission client | Bounded internal client on `gace-internal` with **per-request** `Authorization: Bearer`, or a **reviewed** secondary network attachment on DebugAI — not implemented in server-core |
| Remote ChatGPT direct MCP URL | **Forbidden** |
| DebugAI-owned typed read adapter inside server-core | **Forbidden** (this CU) |

`operations/workspace-mcp.json` must **not** list the GitHub MCP server until Host runtime + authenticated client E2E are `RUNTIME_VERIFIED`.

## Acceptance (after admitted Host deploy)

1. Checkout exact merged or admitted PR SHA on Host `server-core` path.
2. `docker compose -f docker-compose.github-mcp-readonly.yml config --quiet`
3. `docker compose -f docker-compose.github-mcp-readonly.yml up -d` (**MCP only**)
4. Confirm `docker ps` shows **no** `0.0.0.0:*->8082` mapping.
5. From a throwaway client container on the same network: unauthenticated `POST /mcp` → **401**; valid per-request bearer → `tools/list` exactly **2** project tools.
6. From MCP or same-network client: HTTPS reachability to `api.github.com` (egress).

Record digest, container id, network name, and HTTP codes only — no secrets.

## Rollback (Phase A only)

```bash
docker compose -f docker-compose.github-mcp-readonly.yml down
# Remove network only when no Phase-B receiver or other service is attached:
docker network rm "${GACE_INTERNAL_NETWORK_NAME:-gace-internal}" 2>/dev/null || true
```

Optional image removal: `docker rmi ghcr.io/github/github-mcp-server@sha256:fbec75de11c255213fa08d80fb166abe73d851fff631c51c0079872967720699`

## Host authorization routes (verified feasibility — 2026-10-08)

Phase A Host effects (exact scope):

```text
create outbound-enabled user-defined bridge gace-internal (no Docker --internal)
start gace-github-mcp-readonly ONLY via docker-compose.github-mcp-readonly.yml @ admitted SHA
no host ports: publish; preserve existing DebugAI compose services; rollback documented
no Phase B receiver; no Secret rotation; no workspace-mcp advert
```

### Routes that do **not** authorize Phase A today

| Route | Verdict | Why (Source / Host read-only) |
|-------|---------|--------------------------------|
| DebugAI legacy manual one-shot approval (`host-gitops-runner.sh`) | **NOT APPLICABLE** | Hardcoded `REPO=/home/admin1/projects/debug-ai`, `CONTAINER_REPO=/workspace/debug-ai`, fixed `compose.yaml` services `debug-ai` / `sandbox-runner`. No `G-ACE-inc/server-core` checkout, no new network, no third-party MCP image compose. |
| Master Internal persistent delegation (`operations/master-internal-repositories.json` + `host-gitops-master-internal.sh`) | **NOT APPLICABLE** | Sole enrolled repo is `seigo-gace/debug-ai`; mapping requires `repo==/workspace/debug-ai` and `server_project_path` under `/home/admin1/projects/debug-ai`. Registry entry **requires** `effects.persistent_data=false` and `runtime_target.compose_file==compose.yaml` — incompatible with creating `gace-internal` and `restart: unless-stopped` readonly MCP. **Do not reuse or expand DebugAI deploy receipts for server-core.** |
| server-core in-repo Host executor | **UNIMPLEMENTED** | No `host-gitops` / approval consumer for `G-ACE-inc/server-core` Phase A in this repository (by design: no generic shell bridge in PR #33). |
| GPT CHAT / Issue comment text | **NOT A CREDENTIAL** | Instructions record intent only. |

`LEGACY_DEBUGAI_ONE_SHOT_SUPPORTS_PHASE_A=NO`  
`HOST_ADMISSION_AVAILABLE=NO` (no verified executor + receipt for the exact effects above on actual Host as of this CU)

### Legitimate next authorization (minimal)

1. **Master (product / protected effects):** approve Phase A persistent Host effects for official readonly MCP only (network + single compose service), explicit SHA, rollback, no Phase B bundled.
2. **Host admin (execution):** perform admitted steps on Host using `docs/GITHUB_MCP_PHASE_A_ADMISSION.md` acceptance/rollback **or** a **new narrowly reviewed** admission lane (e.g. dedicated allowlisted Host operation for `github.mcp.readonly.phase_a` — **not implemented in Source yet**; do not forge `.approve` files or borrow DebugAI `gitops_*.approve`).

One-shot vs standing: a **future** dedicated Phase A receipt could be one-shot; the **existing** DebugAI one-shot path is **not** that receipt.

### Pre-apply read-only plan (Source)

```bash
cd /home/admin1/server-core   # admitted checkout at exact SHA
python3 scripts/github_mcp_phase_a_host_bootstrap.py plan
```

Emits JSON (`gace.github-mcp-phase-a-host-plan/v1`). Default mode performs **no** Docker/network mutations. `apply` remains **fail-closed** without verified external receipt.

Master impact brief: `docs/GITHUB_MCP_PHASE_A_MASTER_IMPACT_BRIEF.md`.

### Post-admission verification (required before RUNTIME_VERIFIED)

- Docker inspect: zero host port bindings; not `host` network mode.
- Private-bridge client: unauthenticated `POST /mcp` → 401; authenticated per-request bearer → `tools/list` exactly two project tools; optional `projects_list` (credential never logged).
- DebugAI 13-tool MCP and existing services remain healthy.

Until then: `CLIENT_E2E=NOT_VERIFIED`, `workspace-mcp` advert blocked.

## Host permission request template (for Master → Host admin)

When no valid receipt exists, request scoped to:

- Repository: `G-ACE-inc/server-core`
- Exact SHA: merged PR #33 commit (e.g. post-merge) or named commit on branch
- Effects: create bridge `gace-internal` (no `--internal`), `docker compose -f docker-compose.github-mcp-readonly.yml up -d` **only**
- Explicit **non-effects:** Phase B receiver, Secret/registry expansion, DebugAI compose mutation, `workspace-mcp.json` change
- Rollback: `compose down` + conditional `network rm` (see above)
