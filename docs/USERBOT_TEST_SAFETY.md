# Gserver shared Userbot verification safety and access map

**Owner:** G-ACE-inc/server-core, shared Gserver safety boundary. **Master approval:** 2026-11-12, all AI users of Gserver. **Applies when:** any GPT CHAT / Work / Cursor / Composer / Codex / SERVER_AI / future AI, test script, runner, and delegated host process accesses or requests Telegram Userbot verification via Gserver. This is an additional *effect-specific* protection, **not** a replacement for each executor's Rule Plane, existing GitHub/Host admission, source ownership or project acceptance.

## Non-negotiable invariant

The already authorized, persistent `gace-userbot-verify.service` remains the **only owner of its Telegram MTProto session**. Use it as an ongoing verification resource. A passing test must not leave it stopped, logged out, unauthenticated, re-enrolled, or unable to reconnect. The client must never assert permanent immunity to Telegram's server-side revocation.

### Prohibited, including for temporary testing

- `log_out()`, logout, auth-key revoke/reset, `auth.logOut`, password/phone reset, or any API action with equivalent effect.
- Stop/restart/disable/kill the service **to give a standalone test client temporary ownership of the session**, even with a `trap` to restart later. Do not use an independent `TelegramClient` pointed at the same session while the resident client owns it. A normal session-preserving maintenance/code-activation restart is separately permitted below.
- Delete/overwrite/rename/migrate/recreate/export or change the file permissions of the live `userbot_verify.session` or its backup, or edit `userbot.env`. Never copy a live SQLite session as a test workaround.
- Attempt login/OTP/SMS/code request/sign-in, revoke other sessions, device authorization manipulation, or rotate phone/credentials without a separate explicit Master authorization.
- Leak phone, hash, OTP, auth key, StringSession, SQLite contents, private usernames/IDs or private dialog contents to logs, GitHub, terminal command text or chat.
- Bypass membership approval, Telegram privacy settings, source project authorization or Host/Secret admission; execute arbitrary user-supplied Python in the resident process.
- Declare PASS from source/unit tests, an existing unrelated DM message, a worker state printed long ago, or automatic restart alone.

**2026-11-13 Master clarification — normal restart is permitted:** The protected boundary is **no phone number, OTP, SMS, sign-in/re-enrollment, session loss, or credential reset**. A controlled restart of the existing `gace-userbot-verify.service` for necessary code activation, maintenance, or recovery is an ordinary permitted technical operation under the existing Owner/Host admission; no additional approval is required solely because it restarts. Preserve the original session and credentials unchanged, keep one session owner, stage tested code and a code-only rollback, then verify active/enabled, existing-session authorization, allowed IPC response, and no login prompt. If any auth verification fails, stop further test requests and preserve the session; never auto-enroll. **Protected recovery still requires advance Master approval** when it would actually change, replace, revoke, or re-enroll the session/credentials or ask for a phone/OTP. Restarting simply to let a second test client use the session remains prohibited.

## Access and responsibility mapping

| Actor | Existing permitted entry | Common Userbot request route | Boundary |
| --- | --- | --- | --- |
| GPT CHAT / ChatGPT Work | server-core `.github/chat-host-requests/req_*.json` → Actions → authenticated Gateway → Receiver → Gserver `host.command`, with correct `project_context.repository` | Invoke only the allowlisted *resident-service* test client from the admitted Project checkout; collect request/Run/private result | No direct session client, no bypass of existing Host admission |
| Cursor / Composer / Codex / SERVER_AI on Gserver | Their authorized local Shell/Workspace under selected #16/Project Current | Same allowlisted resident-service test client; no stop-to-test or second session owner | No GPT CHAT-specific Actions or Notion obligations; controlled code-maintenance restart follows the clarification above |
| Other Gserver-using AI/agents | Their *already admitted* Gserver command/API execution surface | Same resident-service client, with project ownership and test action scope | No implicit access merely from Gserver connectivity; no new network listener |
| GateApp-Bot owner | `seigo-gace/GateApp-Bot` adopted verification module | Owns `scripts/userbot_keepalive.py`, the service unit and allowlisted resident test handler | One session owner, per-test isolation, restricted Socket permissions |
| server-core | This document + `docs/LOAD_SCOPE.md` router and GPT CHAT Work Routine reference | Controls rule discovery, shared mapping and evidence contract | Does not own/change live Telegram auth state |

**Specific runtime ownership (verified historical location, recheck before execution):**
`/home/gace/Project/Gserver/projects/TGtumbler/GateApp-Bot`.
Local service: `gace-userbot-verify.service`; session and secrets live under `deploy/secrets/` (0600 files; never read contents into evidence).
Do not bake this path into a general dispatcher registry; use the existing canonical Project mapping and owner verification.

### Canonical processing pipeline

`AI → pre-existing authorized Gserver execution channel → admitted target repository → userbot resident request client → tightly scoped local IPC → existing resident process → Telegram → redacted result and live service readback → owning Project Current`.

**Runtime interface gate:** until the resident worker has a verified allowlisted local IPC handler and corresponding client, **mark live operations BLOCKED_NOT_IMPLEMENTED**. Do not use `systemctl stop` + standalone Telethon, second session copy, PID injection, background login or an unverified control endpoint to simulate it. Remote shell access does not imply the resident interface exists.

Use an owner-only UNIX socket (or equivalent existing Gserver internal IPC) when implementing the handler; no externally exposed port, arbitrary code execution or raw Telegram credential access. Require a bounded request ID, allowlisted action, validated arguments, target bot/group, per-request timeout, single ordered execution, small redacted output, and a non-destructive cancellation path. Mutations affecting real third-party messages or groups need the Project's own scope/approval. Never silently publish test Rooms.

## Readback and acceptance

Before and after every live test, read **actual** `systemctl --user is-active`, `is-enabled`, `loginctl ... Linger`, process/account authorization, and existence/mode of session without reading its contents. Confirm same account ID across operations using non-reversible short fingerprint in private evidence, and no login event or service stop attributable to the test. Scope result by source SHA, target bot, test action, request ID, observed Telegram message/callback when safe, actual Host/Runtime outcome, and restore invariant. An input-message deletion check must reference the **newly sent** input, not earlier history. No result can be PASS if the worker was stopped, session overwritten, login requested, or end state is unknown; report FAIL/NOT_VERIFIED separately.

Connection failure is not auth failure. Keep the same resident process alive for transport retry as designed. On auth invalidation, preserve all files, stop only further *test requests*, do not auto-enroll or mutate session; report protective BLOCKED and request an explicitly authorized recovery procedure.

### Negative acceptance examples

1. A proposed test stops/restarts the worker to open a *standalone session test client*, or calls `client.log_out()`: **REJECT**. A necessary session-preserving maintenance/code-activation restart is **not** that prohibited test method; apply the explicit normal-restart safeguards above.
2. A script opens `TelegramClient(str(SESSION_BASE), ...)` outside the resident worker: **REJECT**.
3. Resident socket missing, worker inactive or authorization unverified: **BLOCK**, not fallback to direct session.
4. A test succeeds, but end-of-test active/enabled/session mode cannot be read: **NOT_VERIFIED**, not PASS.
5. Separate allowed bot-test behavior is verified through IPC while service remains active and session unchanged: **PASS** only for that bounded action.

## References and precedence

- server-core `docs/LOAD_SCOPE.md`: all-Gserver-AI conditional policy entry.
- server-core `docs/G_ACE_WORKSPACE.md` §6: GPT CHAT operator applies this shared effect policy, without importing the full CHAT routine into server agents.
- server-core `docs/GITHUB_PROJECT_CHAT_HOST_ROUTE.md`: GPT CHAT admission/transport; never an independent credential.
- Target `seigo-gace/GateApp-Bot` Issue #7 and owner Source: service and implementation Current. Existing historical tests which briefly stopped the service are historical evidence only; **not an approved method for future tests**.
