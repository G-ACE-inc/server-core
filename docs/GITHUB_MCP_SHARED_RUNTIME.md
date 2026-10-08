# Shared official GitHub MCP — source-only deployment gate

**Owner**: `G-ACE-inc/server-core#10`. Executor: existing G-ACE/DebugAI guarded
Host path, not a new shell proxy. The existing GitHub Projects mutation owner
remains `scripts/github_project_control.py` (GraphQL + exact readback).

## What this adds

`docker-compose.github-mcp-readonly.yml` describes the official
`ghcr.io/github/github-mcp-server` image in native HTTP mode, with only the
`projects` toolset and **global read-only** policy. It joins the same
`gace-internal` network already required by Project Control.

This file is **source-only**: it has not downloaded an image, installed an
MCP client, created a network, changed permissions, created a token, or started
a container. The existing `operations/workspace-mcp.json` is unchanged:
only advertise the shared capability as available once the real runtime is
healthy and its permitted caller-specific authentication is demonstrated.

Official upstream:
- https://github.com/github/github-mcp-server
- https://github.com/github/github-mcp-server/blob/main/docs/streamable-http.md

## Reused bounded Project Current reader (source only)

`scripts/github_project_read_current.py --item-url <approved GitHub Issue or PR URL>`
reuses the **existing** `github_project_control.py` Project identity, item lookup,
field-read GraphQL and error contracts. It reads **only** `Wave`, `Gate`,
`Change Unit` and `Mutation Owner` for Project #1 and emits sanitized JSON;
unassigned fields stay `null` and return `PARTIAL`. Invalid targets and missing
GitHub permissions fail closed. No second mutation engine, generic GraphQL
forwarder, new transport, token, runtime permission or additional repository
registration is created. Its source tests run in existing Project Control CI.

This is a bounded diagnostic/readback helper for an **already authorized**
Server AI/Host execution context, not proof that GPT CHAT can execute it or
that real GitHub Project field values have been retrieved. Do not deploy it
through a new uncontrolled shell path. The official MCP remains the adopted
shared Project read capability; these existing GraphQL readers are reused,
not a replacement for the official MCP Server-AI/CHAT E2E acceptance.

## Activation prerequisites — must be demonstrated, not assumed

1. Verify image provenance and choose one real **immutable SHA256 digest** for
   `GACE_GITHUB_MCP_IMAGE_SHA256` (64 lowercase hexadecimal characters). Do
   not substitute a floating tag, and do not treat the CI dummy digest as real.
2. Verify the intended consumer, authorization and actual GitHub Projects
   credential scopes. HTTP accepts a **per-request** bearer credential
   supplied by a trusted client, not a globally shared token in this Compose
   file. No plaintext credentials in Git, Chat, logs, or a published endpoint.
   Host `gh auth status` proves a Host client, not this container's identity.
3. Check/create the approved internal-only `gace-internal` network.
   Project Control currently also requires it; never silently start an
   unrelated receiver or recreate production services.
4. Verify that the pinned image accepts the exact command and security
   restrictions (`65532:65532`, read-only root, tmpfs) in an isolated
   non-production test; confirm internal connection without publishing a
   host port, and authenticated `projects_list` / `projects_get` for
   G-ACE Development Platform #1 and fields `Wave`, `Gate`,
   `Change Unit`, `Mutation Owner`.
5. Verify no credential is reused outside its explicit allowed consumer and
   no tool allows Project mutations under this read-only service.
   Test missing/invalid-scope credentials are rejected.
6. Register the **bounded** Server-AI client only after success. To enable
   CHAT, use the existing GitHub→Actions→Cloudflare Access→DebugAI
   request/status path with an explicit allowed command schema, actor,
   exact Project/Item/Field constraints and safe readback. Do not forward
   raw user-supplied MCP tool names or arbitrary JSON. Project writes must
   keep the existing server-core identity/HMAC/GraphQL authorization.
7. Record Source SHA, image digest, runtime container identity, credential
   identity/scopes (not secret), unauthorized-deny evidence and audit; only
   then classify the capability as RUNTIME_VERIFIED.

## Change Unit boundary

Only Source/Test/CI are in scope here. No Host, Secret, Docker, production,
GitHub Project fields, commercial approval paths, existing DebugAI 13 tools,
TGserver ZERO or user Cursor configurations were changed.
