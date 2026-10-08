# CHAT → GitHub → bounded Host — common Project routes

**Owner:** `G-ACE-inc/server-core#10` / control `#15`  
**Contract:** `operations/github-project-chat-host-routes.json`  
**DebugAI execution body:** unchanged (`seigo-gace/debug-ai`)

## Purpose

Reuse the **already proven** path (CHAT `update_file` → GitHub Actions push → Cloudflare Access → DebugAI `/v1/server-command/*`) for registered Project control repositories, with server-core owning **dispatch binding and evidence shape** only.

Do **not** treat Actions green alone as Runtime PASS. Do **not** rerun completed proof runs (`37801337126`, Asteria `#6` evidence).

## Registered routes (initial)

| Route ID | Project control | Trigger repo | Target file |
|----------|-----------------|--------------|-------------|
| `route_debugai_live_read` | [debug-ai #41](https://github.com/seigo-gace/debug-ai/issues/41) | `seigo-gace/debug-ai` | `.github/chatgpt-live-api-target.json` |
| `route_asteria_baseline_probe` | [asteria #6](https://github.com/seigo-gace/asteria/issues/6) | `seigo-gace/debug-ai` | `.github/asteria-baseline-probe-target.json` |

Branch (both): `feat/tgserver-async-log-sink-20261003`

## CHAT final E2E handoff (Composer does not execute CHAT)

1. Read handoff JSON:
   ```bash
   python3 scripts/github_project_chat_host_route.py chat-handoff --route-id route_debugai_live_read
   ```
2. CHAT **only** `update_file` on the route’s `target_file` in `workflow_repository` (bounded JSON; no shell).
3. Push to allowed branch → Actions run → CHAT reads job log for markers in `evidence_contract`.
4. Validate dispatch before editing (optional local/CI):
   ```bash
   python3 scripts/github_project_chat_host_route.py validate-dispatch \
     --route-id route_debugai_live_read \
     --repository seigo-gace/debug-ai \
     --command-id project.git_head \
     --execution-repo /workspace/debug-ai \
     --project-control-url https://github.com/seigo-gace/debug-ai/issues/41
   ```

## Boundaries

- No new MCP, queue, gateway service, or Host command expansion in this contract.
- No DebugAI `workflow.js` / PR56 edits from this CU.
- GitOps deploy paths remain separate; cross-project **read/probe** only here.
- Adding a repository requires a new `routes[]` entry and tests — not ad-hoc commands.
