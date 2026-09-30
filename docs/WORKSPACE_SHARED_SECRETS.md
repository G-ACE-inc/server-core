# WORKSPACE SHARED SECRETS

Version: 2026-09-30
Role: G-ACE Workspace司令室からShared Secret / Tokenを安全に利用するための共通契約。

この文書はSecret値の保管場所ではない。Secret / Token / password / credential / session値をGit / Chat / Log / Documentへ出さない。

## 1. Command-Center Responsibility

server-coreが管理するのは次だけ。
- provider / purpose;
- secret identifier;
- allowed consumer;
- broker / Vault access path;
- allowed origin / request boundary;
- identity/availability verification method;
- failure behavior;
- rotation / replacement boundary。

Secret値そのものはserver-coreへ置かない。

## 2. Current Shared Contracts

機械可読Authority:
- Hugging Face: `operations/huggingface.json`
- Cloudflare Account API: `operations/cloudflare-account.json`
- Cloudflare Tunnel: `operations/cloudflare.json` + `docs/CLOUDFLARE_OPERATIONS.md`（Account APIとは別契約）

| Provider / purpose | secret_id | consumer | allowlist / provider identity |
|---|---|---|---|
| Hugging Face | `hf-token` | `g-ace-workspace` | `https://huggingface.co`; identity `https://huggingface.co/api/whoami-v2` |
| Cloudflare Account API | `cf-account-api` | `g-ace-workspace` | `https://api.cloudflare.com`; identity `/client/v4/user` + `/client/v4/accounts` |

## 3. Broker Contract

Current broker authority: Libral Vault.

```text
Vault endpoint: http://127.0.0.1:8791
Action API: POST /internal/v1/actions/http
Secret registration API: POST /internal/v1/secrets
Consumer: g-ace-workspace
Internal auth source: /home/admin1/.config/libral-vault/internal-token
```

Internal auth value is read only at runtime and is never copied into this document, Chat, Git or logs.

Provider request pattern:

```json
{
  "secret_id": "<registered-id>",
  "consumer": "g-ace-workspace",
  "url": "<allowlisted-provider-url>",
  "method": "GET",
  "secret_header": "authorization",
  "secret_prefix": "Bearer "
}
```

Vault injects the provider credential. The caller must not need the plaintext provider token.

## 4. Use Rule

When a Project needs a Workspace-shared Secret:

```text
Project needs provider access
  -> server-core WORKSPACE_REGISTRY / this document
  -> identify existing contract
  -> use broker action
  -> verify provider response / identity as required
  -> do not add Project-local token copy/helper unless formally required
```

If no contract exists, do not invent an identifier or copy a token into the Project. Define the new contract first.

## 5. Secret Registration / Replacement

Registration or replacement is a mutation boundary. It requires explicit authorization under `SERVER_CORE_PROTOCOL.md`.

Input credential should be supplied through a temporary process environment or another approved secure channel; never through Chat or committed files.

Required registration fields:
- id;
- value (runtime only, never documented);
- allowed consumers;
- provider/purpose linkage.

Replacement must preserve a clear failure/recovery path. Do not delete the old credential before the replacement procedure is understood when doing so could break an active service.

## 6. Identity / Availability Verification

Vault intentionally does not return plaintext tokens.

Verify a registered credential through the provider identity endpoint or a harmless representative API call.

### Hugging Face
- secret id: `hf-token`
- identity endpoint: `https://huggingface.co/api/whoami-v2`
- HTTP 401 means invalid/unauthorized credential until proven otherwise.

### Cloudflare Account API
- secret id: `cf-account-api`
- identity checks: `/client/v4/user` and `/client/v4/accounts`
- `tokens/verify` is not the sole identity authority because endpoint permission behavior may differ.

Only expose non-secret identity fields needed for verification, such as id/name/status/email where appropriate.

## 7. Failure Contract

Known broker/provider failure classes:
- `SECRET_NOT_FOUND`: secret absent or identifier mismatch;
- `ACCESS_DENIED`: consumer not allowed;
- `HTTP_ORIGIN_NOT_ALLOWED`: provider origin not allowlisted;
- provider 401/403: invalid credential or insufficient provider permission;
- broker unavailable: shared-secret capability is not available until broker health is restored.

A failure must not trigger fallback to printing, copying or embedding the plaintext Secret.

## 8. Consumer Boundary

Workspace-shared credentials may be used only by explicitly allowed consumers.

Project-specific credentials that should not be shared across the Workspace remain Project-owned and must not be silently promoted into the shared contract.

Shared does not mean unrestricted.

## 9. Add-New-Contract Gate

Before adding a shared Secret contract, determine:

```text
SHARED_USE_CASE_CONFIRMED=YES
OWNER_KNOWN=YES
PROVIDER_KNOWN=YES
SECRET_ID_DEFINED=YES
CONSUMERS_DEFINED=YES
ALLOWLIST_DEFINED=YES
BROKER_PATH_DEFINED=YES
IDENTITY_OR_REPRESENTATIVE_VERIFY_DEFINED=YES
FAILURE_BEHAVIOR_DEFINED=YES
PLAINTEXT_PERSISTENCE=NO
```

Unknown fields block the contract from being marked available.

## 10. Registry Sync

When a shared Secret contract is added/removed/renamed or its consumer/broker path changes:
- update the relevant `operations/*.json` contract;
- update `docs/WORKSPACE_REGISTRY.md`;
- update this document when the common use/failure model changes;
- run applicable validation;
- record the work in GitHub commit / PR.

Do not turn this document into a chronological work log.

## 11. Prohibitions

- Secret / Token values in Git / Chat / docs / logs;
- plaintext Secret files for Workspace sharing;
- per-Project duplicate token helpers when an approved shared contract already exists;
- dumping plaintext values from Vault;
- using one Provider credential as another contract without explicit design;
- confusing Cloudflare Tunnel credentials with Cloudflare Account API credentials;
- using GPG-Core as an implicit replacement for the current Workspace shared-secret contract;
- claiming Secret availability without broker/provider verification when the task requires live access.

## 12. Availability Boundary

This document can be complete as a **contract** while current broker/provider Runtime is `NOT_VERIFIED` for a given task.

Document completeness and Runtime availability are separate states.