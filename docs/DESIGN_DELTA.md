# SERVER CORE DESIGN DELTA

## Purpose

This document records intentional changes from the `docs/SERVER_CORE_DESIGN.md` baseline without erasing the previous design history.

A Design Delta is required when server-core architecture, responsibility, authority routing, shared-capability boundary, or command-center behavior is formally changed.

It is not a daily work log. Chronological work history remains in GitHub commit / PR.

## Required fields

Each accepted delta records:
- Baseline design
- Actual change
- Reason / root cause
- Evidence
- Affected scope
- Applied commit
- Compatibility / migration / rollback considerations
- Verification state

## 2026-09-30 — Formalize server-core as the G-ACE Workspace command center

### Baseline design
server-core was described primarily as the Workspace common development/operations control layer and common authority entry point.

### Actual change
The role is formally clarified as the **G-ACE Workspace command center**.

The command-center responsibility is explicitly defined as:
- receive and route tasks;
- determine target Project / authority;
- control progressive context loading;
- dispatch work to the owning Project;
- expose shared MCP / Tool / Secret / KB capabilities through explicit contracts;
- enforce common development, verification and documentation rules;
- preserve GitHub work history;
- govern approval and runtime-operation boundaries.

server-core still does not absorb Project-specific implementation or runtime internals.

### Reason / root cause
The earlier wording was technically compatible but too weak: it could be interpreted as a passive rule/document repository. The intended architecture requires server-core to be the active common command point from which Workspace AI/developer work is routed and governed.

### Evidence
- Master explicitly clarified that server-core's role is equivalent to a command room / command center for the Workspace.
- Existing README / LOAD_SCOPE / Workspace routing already implemented server-core-first routing, so the formal design wording is being aligned with that intended responsibility rather than creating a separate orchestration layer.

### Affected scope
- `README.md`
- `docs/SERVER_CORE_DESIGN.md`
- `docs/LOAD_SCOPE.md`
- `docs/G_ACE_WORKSPACE.md`
- `docs/WORKSPACE_REGISTRY.md`
- `docs/STRUCTURE.md`
- Workspace guard contract

### Applied commit
Filled by the commit/PR that completes this documentation change.

### Compatibility / migration / rollback
- No Project implementation is moved into server-core.
- Existing Project README-first entry remains valid after routing.
- Existing LibralCore, GitHub, Secret, KB and Storage authorities remain valid.
- The change strengthens responsibility wording and command flow; it does not require a runtime migration.
- Rollback would restore weaker control-layer wording but is not recommended because it reintroduces ambiguity about Workspace ownership/routing.

### Verification state
Pending exact branch CI at creation time. Do not mark PASS until the updated server-core guard succeeds on the final branch HEAD.

## Update rule

When a later architecture decision changes the server-core baseline, append a new section. Do not rewrite or delete prior accepted deltas merely because the current implementation changed.