# Master impact brief — Phase A official GitHub MCP (read-only)

**Audience:** Master (product / protected Host effects)  
**Technical owner:** `G-ACE-inc/server-core#10`  
**Source SHA binding:** exact PR #33 merge commit or named commit on `feat/shared-github-mcp-readonly-20261008`  
**Not authorization:** this document, Issue comments, or CHAT text.

## Purpose

Allow **authorized Server AI** to read GitHub Project #1 fields through the **official** `github-mcp-server` read-only HTTP surface (`projects_get`, `projects_list`) on the private Host, without replacing DebugAI’s existing 13-tool MCP or bundling Phase B field mutation.

## Concrete effects (Phase A only)

| Effect | Detail |
|--------|--------|
| Docker network | One user-defined **bridge** named `gace-internal` (or `GACE_INTERNAL_NETWORK_NAME`), **without** Docker’s `--internal` flag |
| Service | One resident container `gace-github-mcp-readonly` from `docker-compose.github-mcp-readonly.yml` |
| Image | Pinned immutable digest `sha256:fbec75de…` only |
| Ports | **No** host `ports:` publish (`expose: 8082` only) |
| Secrets | **None** in compose; callers use **per-request** Bearer (never logged) |
| Excluded | Phase B Project Control receiver, Gateway destination, `workspace-mcp.json` advert, DebugAI compose changes, registry expansion |

## Cost

No new SaaS subscription. Uses existing VPS CPU/RAM (~128m limit in compose) and outbound HTTPS to GitHub API.

## Risk

| Risk | Mitigation |
|------|------------|
| Docker bridge reachable from Host and attached containers | No internet publish; MCP requires Bearer on every call; read-only tool surface |
| GitHub data exposure via stolen bearer | Short-lived caller credentials; no shared PAT in compose; audit HTTP codes only |
| DebugAI disruption | Independent compose; plan checks DebugAI containers still present; rollback stops MCP only |

## Rollback

```bash
docker compose -f docker-compose.github-mcp-readonly.yml down
```

Remove network **only** if created for Phase A (label `gace.phase_a_owner=gace-github-mcp-readonly`) **and** no other service is attached. **Never** remove a pre-existing shared `gace-internal` used elsewhere.

## Legitimate execution route (after Master approval)

1. Master approves this brief (protected effects).  
2. **Trusted Host administrator** runs read-only plan:  
   `python3 scripts/github_mcp_phase_a_host_bootstrap.py plan`  
   (from admitted `server-core` checkout at exact SHA).  
3. Host admin performs **manual bounded** steps in `docs/GITHUB_MCP_PHASE_A_ADMISSION.md` (network create + MCP compose up).  
4. **Do not** use DebugAI `host-gitops-runner.sh`, DebugAI one-shot `.approve` files, or Master Internal debug-ai registry deploy.  
5. Post-deploy: internal client probe (401 without token; authenticated tools/list = 2 tools) — then separate RUNTIME_VERIFIED / client E2E gates.

Future optional: verified `gace.github-mcp-phase-a-host-receipt/v1` file consumed by `github_mcp_phase_a_host_bootstrap.py apply` (currently **NOT_IMPLEMENTED** for automated apply).

## Pre-approval Source readiness

Run on Host (read-only): `python3 scripts/github_mcp_phase_a_host_bootstrap.py plan`  
CI: `scripts/github_mcp_phase_a_host_bootstrap_test.py` + existing MCP contract tests.

**Source readiness ≠ Runtime PASS.**
