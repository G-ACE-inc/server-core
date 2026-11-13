# Common ServerTerminal one-step structure — PROPOSAL ONLY

Status: NOT ADOPTED / NOT DEPLOYED. This is a change proposal, not an authority, production route, policy change, or permission grant. Owner: server-core Control #10.

## Verified starting point

- 2026-11-12 Contabo and Gserver E2E: CHAT -> committed JSON request -> Actions -> existing Gateway -> Receiver/Host -> durable Result Sink -> GitHub Issue #351 -> Actions poll. Gserver PR #31, server-core PR #357 and Actions 43233182477 confirmed ordinary Project read without Project SHA. Contabo PR #358 added and live-tested **local** result querying by Request ID through the already-existing Sink Unix socket.
- The Dispatcher expected_sha supports the placeholder GITHUB_WORKFLOW_SHA; Actions binds its own commit SHA. It does NOT eliminate the per-command GitHub commit.
- Gserver repo_sha refers to the actual installed Host checkout, which can differ from a merged GitHub main commit. Never guess from the remote branch.
- Issue comments have a capacity limit and are not the authoritative Host ledger. ChatGPT's present connected GitHub API tool cannot directly POST arbitrary requests to the existing Gateway.

## Before and proposed after

| Concern | BEFORE | AFTER, IF AUTHORIZED |
|---|---|---|
| Submit command | Commit a file in .github/chat-host-requests; trigger Actions | Call one authenticated terminal.execute action against the existing Gateway ingress, receive request_id; no source commit for an ordinary shell command |
| Read result | Poll Issue comment pages until receipt | Call authenticated terminal.result(request_id) using the existing Receiver and Result Sink keyed ledger; no Issue comment needed |
| Ordinary read SHA | expected_sha and repo_sha required in external request | No manual SHA; the admitting Host attests actual Dispatcher and Project checkout SHA at read time. Optional explicit pin still rejects mismatches |
| Source / deployment write | Duplicate external pins and preconditions | Preserve protected registered effect permission and compare exact expected-before HEAD immediately before the mutation |
| Retry | Gateway at-least-once; writer de-duplicates Request ID | Same stable idempotency; querying result never re-executes. Same ID/different content rejects |
| Failure / outage | Actions sees no Issue result and cannot determine Host execution | Existing durable Host ledger remains truth; query same ID after recovery; typed gateway-unavailable vs host-running vs publication failure |

Proposed minimal caller request: (request_id, project_context.repository, command, optional explicit_sha, operation_class). The Receiver must derive/verify operation class rather than trust arbitrary caller classification. Result: (request_id, state, exit_code, host_sha, project_head, safe output locator, timestamps). Never return secret content as public metadata.

## Ownership, proposed changes and compatibility

1. server-core: adapt existing signed request validator and result query (not a new service), add exact result correlation, refactor Actions-only request-sha pins for read-only traffic; retain durable Writer and Sink, registered roots, authorizations, HMAC and command digest. This would change the deployed protocol and adopted SERVER_CORE_DESIGN §16 / common Terminal route, so DO NOT implement in main before approval.
2. Gserver: after protocol adoption, adjust the common caller/target adapter only; preserve PR #31 local checkout lookup and protected SHA behavior for explicit pins. Never touch resident Userbot sessions.
3. Shared Gateway: reuse existing POST /internal/events and registered destination; do not duplicate gateway, key, daemon or queue. A new authenticated private read endpoint, if required, is a provider-scope change requiring owner permission. No speculative address or credential.
4. ChatGPT client: a real authenticated execute/query action MUST be connected. The current GitHub connector can write a GitHub request file but does not offer arbitrary Gateway HTTP POST. Deploying a Host endpoint without this client action DOES NOT make ordinary GPT CHAT able to invoke it.
5. Output: retain existing owner-only private Host output artifact; public receipt is metadata-only.

## Rollout and verification

- Step A ALREADY DONE: Host-local result lookup without GitHub Issue (PR #358).
- Step B PROPOSED: Add an opt-in read-only direct execute/query path behind a default-off compatibility flag. Existing Actions and permission model remain unchanged during trials.
- Step C PROPOSED: Prove the actual client action can invoke this path. Test Contabo and Gserver: read with no manual SHA, explicit mismatch rejection before execution, mutation precondition, two concurrent Requests, same-ID replay without duplicate effect, wrong ID/credentials denied, Gateway 5xx and recovery, Result Sink restart, complete result redaction, Userbot unaffected.
- Step D PROPOSED: Only after Master authorizes this exact design, change the default route; retain the legacy route as rollback, never replay an unknown execution. Remove GitHub source commit and Issue result dependencies from normal usage, not from source control or development evidence.
- Rollback: switch routing back while preserving immutable Host request IDs and ledgers; no hard reset, new user session or bulk rerun.

## Explicit protected-architecture approval scope

Approve only the listed common request/result transport, optional SHA for ordinary reads, and the tested staged cutover. This does not approve: deleting unrelated policies, adding producer domains, changing external Gateway credential provisioning, expanding Repository admission, starting another AI, introducing a paid provider, or changing unrelated product services.

Status remains PROPOSED until Master confirms this concrete before/after and impact. Local readback code already completed is not a substitute for this client-facing change.
