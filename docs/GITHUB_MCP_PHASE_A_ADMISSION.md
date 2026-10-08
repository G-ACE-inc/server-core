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

- **Inbound:** no `ports:` publish on the MCP compose service; reachability only from containers attached to the same network (and admitted clients).
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

## Host permission request (minimal, when no receipt)

Request **one-shot** Phase A admission scoped to:

- Repository: `G-ACE-inc/server-core`
- Exact SHA: PR #33 merge commit or named commit
- Effects: create bridge network `gace-internal` (no `--internal`), `compose up` MCP service only, no Secret rotation, no `workspace-mcp` change
- Rollback: commands above

No permanent repo-wide Host delegation is required for first deploy if one-shot receipt is issued.
