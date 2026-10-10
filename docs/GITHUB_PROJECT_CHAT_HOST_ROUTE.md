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

`route_debugai_live_read` branches: `feat/tgserver-async-log-sink-20261003` and `feat/chat-gitops-request-20261009`.  
`route_asteria_baseline_probe` branch: `feat/tgserver-async-log-sink-20261003`.

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
     --project-control-url https://github.com/seigo-gace/debug-ai/issues/41 \
    --branch feat/tgserver-async-log-sink-20261003
   ```

## Boundaries

- No new MCP, queue, gateway service, or Host command expansion in this contract.
- No DebugAI `workflow.js` / PR56 edits from this CU.
- GitOps deploy paths remain separate; cross-project **read/probe** only here.
- Adding a repository requires a new `routes[]` entry and tests — not ad-hoc commands.

## CHAT acceptance safety — current verified boundaries (2026-10-09)

The route validator is **static CHAT preflight**, not Host runtime admission. It now
requires the **exact workflow repository**, canonical control Issue URL, allowed
branch, command ID and exact `execution_repo`. A prefix/nested path is not
a substitute for an exact target. It also distinguishes all configured catalog
command IDs from `workflow_supported_command_ids`: only the latter are actually
accepted by each existing GitHub Actions trigger. The registration still retains
previous catalog entries, but unsupported workflow commands FAIL CLOSED until
their separately owned implementation is verified.

Asteria's `asteria.baseline_probe_start` has effect
`bounded_probe_start`, **not read-only**; a later read-only health acceptance
must not execute it. A protected operation or new Project admission requires the
real existing Host/Project authorization — never an Issue comment or the flag
`static_preflight_only=true`.

Real GitHub Actions logs contain timestamps, ANSI escapes and script echoes.
`parse-evidence` accepts exact **emitted** marker lines, distinguishes safety
`=NO` from forbidden `=YES`, rejects conflicting duplicate markers, rejects
nonterminal/failed Server Command states and requires a valid command request ID
plus explicit `SERVER_COMMAND_READ_ONLY=TRUE` for the command path. It does not
claim to verify GitHub's run ID, commit SHA, or dynamic runtime loading of this
route manifest. CHAT must independently bind the GitHub run/job SHA and command
ID to real logs/status and enforce the actual Host authorization. Do **not**
promote `evidence_usable_for_chat=true` alone to cross-project runtime acceptance.

**CHAT confirmed existing Host E2E (different command from the prior git-head
proof):** [run 37803660277](https://github.com/seigo-gace/debug-ai/actions/runs/37803660277),
job `113402154427`, `cmd_ffbd9cb5f1ecacad2f814676`,
`service.debug_ai_health`, `http_status=200`,
`SERVER_COMMAND_STATE=PASS`, `SERVER_COMMAND_READ_ONLY=TRUE`.
This confirmed the **existing** workflow and Host command. The DebugAI workflow
does not import the server-core route JSON, so **PR36 dynamic route-enforcement
E2E is still NOT VERIFIED**. Integration with actual Project-item/Host admission
is a separate approval/scope gate; no new infrastructure, Shell, credential or
permission is authorized by these Source edits.

### Retained across the PR #36 / #37 integration

- `system.projects_inventory` remains in the catalog and in `workflow_supported_command_ids` with effect `read_only`. Historical inventory E2E run `37875336749` is not a new runtime acceptance.
- `system.project_file_inspect` is in the catalog and the trigger-supported allowlist. [Existing live run 38045018446](https://github.com/seigo-gace/debug-ai/actions/runs/38045018446) returned a registered-file READ_ONLY PASS. Static preflight now permits that bounded command, but stays `static_preflight_only=true` and `host_authorization_verified=false`; canonical `/home/admin1/server-core` read and dynamic route enforcement remain NOT_VERIFIED. The live-read handoff still uses `.github/chatgpt-live-api-target.json`, `chatgpt-live-api-verify.yml`, and `chatgpt-bounded-server-read.cjs`.
- `project.git_recent_commits` remains trigger-supported and `read_only` on `feat/chat-gitops-request-20261009`.
- Master-internal `allowed_paths` still includes the host inspect/inventory scripts and runner paths added on PR #36.
- Host authorization stays separate from this static preflight (`host_authorization_verified=false`).

Stacked PR #49 merged into PR #36's **source branch only**; PR #36 remains DRAFT and unmerged into main. This source/doc correction does not modify installed Host admission or Runtime.
