> **Current Tool B entry (2026-10-13):** Normal CHAT uses the existing **server-core-owned** `.github/chat-host-requests/req_*.json` → `chatgpt-live-api-verify.yml` → Gateway → bounded Host receiver → isolated Docker `dev.job` → request-linked #10 result. Five registered repositories and logical session parallelism are runtime-qualified; exact ZERO checkpoint/Telegram correlation is qualified. This path does not call DebugAI product API when `bounded_host_request.enabled=true`. Legacy `base_url` / `repo` compatibility fields remain in the request envelope and do not select the common Host execution repository. The earlier DebugAI-specific route below is retained history; use the following normal-CHAT procedure first.

# CHAT → GitHub → bounded Host — common Project routes

**Owner:** `G-ACE-inc/server-core#10` / control `#15`  
**Contract:** `operations/github-project-chat-host-routes.json`  
**DebugAI execution body:** unchanged (`seigo-gace/debug-ai`)

## 通常CHATの開始・別CHAT実測手順

Owner: existing `G-ACE-inc/server-core#10`, approved minimum Tool B task. Native CHAT uses its GPT_CHAT profile: read `operations/github-project-rule-plane.json`, the manifest-selected Rule #17 and owning #10 Current; do not copy a prior executor's read attestations. SERVER_AI continues to use #16. Fetch this page from current GitHub main. Read the design §16.11 / §17 and committed `operations/github-project-bounded-host.json`; preserve the parent platform purpose and approved read-only test scope. Project #1 membership is established in the committed mapping but never broad Host authority.

1. Use current #10 Host evidence to pin `expected_sha`; GitHub main alone does not establish Host HEAD. Use the selected registered repo's current verified canonical branch tip as `repo_sha`; keep these two SHAs distinct. On an actual `SOURCE_SHA_MISMATCH`, re-anchor using the returned actual Host SHA and a new request file. Do not deploy or change policies to make a read-only test pass.
2. Generate a new unique `req_<24 lowercase hex>` for this CHAT's session and a distinct new request file with that naming convention. Copy the envelope shape from a committed successful request such as `.github/chat-host-requests/req_dcb0ba0366cc58ce5bf3e6ca.json`, but replace the session, exact SHAs, selected repository, request summary, command and START receipt with this CHAT's own verified values. Keep gitops/source_reflect disabled, run_id empty and no server_command_id. A copied envelope is a schema reference, never transferable rule/current evidence.
3. Set command_id `dev.job`; argv `["python3","-c",<code below>]`, timeout_s15, fresh true. Put this CHAT's session id in the printed marker. The code only inspects the isolated repository and records a seven-second execution interval:
   ```python
   import subprocess,time
   print('NATIVE_CHAT_SESSION='+SESSION,flush=True)
   print('START_NS='+str(time.time_ns()),flush=True)
   time.sleep(7)
   subprocess.run(['git','rev-parse','HEAD'],check=True)
   subprocess.run(['git','status','--short'],check=True)
   print('END_NS='+str(time.time_ns()),flush=True)
   ```
   `SESSION` is the generated session string literal in the committed code; resolve it before writing, not a user-edited placeholder. The START receipt must contain actual current verification, profileGPT_CHAT, purpose/CU alignment, read_only scope, adopted design reference/evidence and a concise source_evidence locator/description. Never claim a rule read that did not happen.
4. First verify that this native CHAT actually exposes GitHub file creation and Actions/result read tools. If its connector is read-only, report that precise missing capability; do not invent a write or treat another executor as this client. Create exactly one new file on server-core main through the existing GitHub connector with commit message containing `[isolated-host-request]`. Leave `.github/chatgpt-live-api-target.json` and other CHAT files untouched. Bind the resulting exact commit SHA to its existing workflow Run; read its correlated #10 result. PASS requires expected/actual Host SHA, selected repo base SHA, this CHAT's session marker and its generated Host request ID to match. An Actions dispatch202 alone is insufficient.
5. A native two-CHAT test uses two real independent newly opened conversations, not two synthetic receipts from one executor. CHAT A selects `G-ACE-inc/server-core`; CHAT B selects `seigo-gace/TGserver`. Master pastes the instructions into both chats close together. Each records its own actual request/session/Run/result URL in #10. Compare the two emitted START_NS/END_NS intervals: `min(endA,endB)>max(startA,startB)` proves real worker overlap. If both pass but do not overlap, preserve those successes and repeat only this bounded pair with new request IDs; do not relabel sequential execution as parallel.
6. Each CHAT may record the visible checkpoint through the existing owner-only TGserver #50 `[DEVLOG]` relay and search its returned exact event_id through existing `[TGZERO]` Reader. Use the observed repo/stream map and your own session/sequence; require actual Telegram correlation. Never capture internal reasoning or credentials. Existing final qualified example: TGserver #123 / event3d877d5e34f52664e170d6d2691328e428ff6d03088924039dcef4d981b7c120.

The server executor cannot create native ChatGPT conversations with its available tools. Until two actual conversations produce the above evidence, `NATIVE_TWO_CHAT_ACCEPTANCE=NOT_VERIFIED`, even though the server-side independent-request test already passed. No new connector/workflow/token is required by this test.

## Retained legacy Purpose

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

Stacked PR #49 was integrated into PR #36's source branch; PR #36 itself was merged to `main` on 2026-10-10 (GitHub PR #36 direct readback). The common route registry and dispatch checks are therefore present on `main`, but repository Source availability alone does not prove canonical-parent Host admission or Runtime acceptance.

**server-core main Source reflect (2026-10-11):** `G-ACE Common Chat Host Actions` on `main` may set `source_reflect_request` for registered `dlg_master_servercore_reflect_v1` (`G-ACE-inc/server-core`, branch `main`, runtime `servercore.source`) using existing `/v1/gitops/request` → `/v1/gitops/status`. When the trigger commit only updates `.github/chatgpt-live-api-target.json`, set an explicit 40-char `sha` for a reachable docs-only commit on `main`; restore idle target after terminal evidence. Docs-only pushes to this file on `main` auto-invoke Source reflect when the job emits `SOURCE_REFLECT_AUTO_DOCS_HEAD=YES` and `CHAT_REFLECT_TERMINAL=PASS`.

**CHAT-origin bounded Host recovery (2026-10-12):** Pin `expected_sha` to an independently observed canonical Host HEAD; a GitHub `main` SHA alone is not Host readback. On `SOURCE_SHA_MISMATCH`, re-anchor from the returned Host SHA before resubmission. For `dev.job` `SESSION_LIMIT_REACHED`, reuse a confirmed existing idle session with `fresh=false` for read-only diagnostics rather than silently creating another workspace. Do not promote sandbox diffs if `stdout_truncated` is true; validate changed paths, exact base, and full patch before GitHub-native PR promotion.


**Independent CHAT requests (2026-10-13):** Create exactly one new `.github/chat-host-requests/req_<24 lowercase hex>.json` per commit, leave the shared target untouched, and include `[isolated-host-request]` in the commit message. The existing workflow uses this push-payload marker plus exact commit SHA for concurrency; unmarked legacy requests retain their singleton lane. GitHub Actions push payloads omit the added-file list, so testing `head_commit.added` incorrectly put independent requests into the legacy queue and a third request cancelled the pending second one (run 38285068012). Each job selects its own immutable file and returns the generated Host request ID, command, expected/actual SHA, session and output through #10. Preserve the original CHAT START checkpoint when a SERVER_AI executor replays a delegated handoff; do not relabel that replay as a second independent ordinary CHAT or a fresh #17 read.

The committed `dev_job.registered_repositories` now enumerates all five distinct repositories observed in Project #1: server-core, TGserver, debug-ai, webhook-gateway and asteria. Added entries use independently read-back canonical parent paths and existing branches/Project item IDs. Dirty canonical files and other owners' worktrees remain outside isolated job writes; this registration grants isolated development only, never product deployment. Runtime qualification and TGserver same-event search require actual #10 evidence.


**Minimum runtime qualification (2026-10-13 JST):** PR #181 deployed executable Source acea4a8a994388f7604fe814b5dc106f9e2232e1. Five existing CHAT-path Actions (38285967458 / 38285970862 / 38285973372 / 38285976955 / 38285978921) SUCCESS for TGserver, debug-ai, server-core, webhook-gateway and asteria. Per-request/session outputs remained separate; TGserver and debug-ai actual worker intervals overlapped 3.938098340 seconds. Docker logs Actions38285099470 PASS returned an empty log body. The executor forwarded an established upstream GPT CHAT START receipt under SERVER_AI #16; this does not claim two new native CHAT identities or fresh #17 adoption. Current Host HEAD must still be read back before each request; request-only GitHub commits can legitimately be ahead of executable Host Source.

Master-authorized existing TGserver auth wiring retained its exact running image and no secret values were printed. Canonical delivery then exposed missing P008 topic routing: an index hit existed before durable raw delivery, so it was not accepted as completion. Restored missing registered P004/P007/P008/P013 mappings additively from the existing 2026-10-08 runtime backup after exact project/group/chat-map equality checks; no Topic/Group was created. Runtime routing state `.tgs-state/topics.json` is newer than the tracked GitHub snapshot: preserve its owner delta and `.tgs-state/topics.toolb-before-20261013.json` rollback copy on subsequent Source reflection; never reset it from Source. Only tgs reloaded.

Final authentic DEVLOG session `chat-toolb-completion-20261013`, sequence3, event_id `3d877d5e34f52664e170d6d2691328e428ff6d03088924039dcef4d981b7c120` was delivered through existing relay38287435566 and retrieved through [TGserver #123](https://github.com/seigo-gace/TGserver/issues/123), Reader38287495725: returned1, COMPLETEtrue, healthy index, producer verified, ALL_RETURNED_HITS_CORRELATED; artifact exact event/session/sequence matches, Telegram message33852. [Final #10 evidence](https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-6129708234). Full historical raw/index coverage and all-surface automatic producers remain separate, unproven broader Tool A acceptance.
