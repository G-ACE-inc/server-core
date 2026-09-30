# SERVER CORE DESIGN

Version: 2026-09-30
Status: Design Baseline

## 1. Purpose

`server-core` is the common development and operations control layer for every Project opened inside the G-ACE Workspace.

Its job is not to own each Project's implementation. Its job is to make every AI / developer enter through the same authority, load only the information needed for the current task, reuse shared capabilities, record work consistently, and operate the server safely.

## 2. Workspace Authority Model

The standard path is:

```text
G-ACE Workspace
  -> server-core/README.md
  -> server-core/docs/LOAD_SCOPE.md
  -> only the server-core authority required for the current task
  -> target Project README
  -> only the target Design / Project Tree / Design Delta / System Document / Source / Test required for the task
  -> implementation / debug / verification
  -> documentation gate
  -> GitHub work report commit
  -> remote readback / PR / CI as required
  -> approved deployment from a confirmed GitHub revision
```

All Workspace AIs must be able to continue development without depending on ChatGPT-only state or Notion.

## 3. Authority Responsibilities

### README

README is the current-state entry point. It is not the design baseline.

A Project README must make the following reachable when they exist:
- Design
- Project Tree
- Design Delta
- completed System / Feature-bundle documents
- run / test / verification entry points

README must describe only completed / verified current state. It must not convert pending work into completed work.

### Design

Design preserves the architecture, contract, responsibility and boundary baseline.

Do not rewrite Design merely to make it match later implementation. If the architecture itself is formally changed, preserve the old baseline, reason, new decision and applicable commit so the history remains traceable.

### Design Delta

When implementation intentionally differs from the baseline Design, record at least:
- baseline design
- actual change
- reason / root cause
- evidence
- affected scope
- applied commit
- compatibility / migration / rollback considerations

### Project Tree

Project Tree is the navigation index for AI and developers. It records meaningful files/directories, responsibility, entry points, related Design and related Tests.

Update it when files/directories are added, deleted or moved, or when major responsibility / entry-point structure changes. Generated dependencies, build artifacts and cache are excluded.

### System / Feature-bundle Documents

Create or update a technical document when a completed unit is too large to be explained reliably by README alone or must be transferable without verbal explanation.

Typical trigger conditions:
- multiple Features form one System responsibility
- an independently reusable Module is completed
- an internal or external Interface becomes a stable contract
- state/data ownership is non-trivial
- runtime, recovery, security or operational behavior must be understood to maintain the unit
- another AI/developer should be able to continue work by reading the document instead of asking the owner to explain it

The document must contain the technical information actually required by the completed unit, such as purpose, scope, architecture, entry points, contracts, dependencies, state ownership, processing flow, failure/recovery, configuration, runtime, tests, verified state, source map, extension constraints and related Design/Delta/commits. Do not create empty category documents merely to satisfy a template.

## 4. Development Loop

```text
server-core README / LOAD_SCOPE
  -> target Project README
  -> required Design / Tree / Delta / System Document only
  -> repository identity / branch / HEAD / status
  -> target Source / direct dependency / related Test
  -> reuse check
  -> implementation or debug
  -> diff
  -> verification
  -> documentation gate
  -> commit as work report
  -> push
  -> remote readback
  -> PR / CI when required
  -> deployment only after the required approval boundary
```

The load scope expands only when the current evidence is insufficient.

## 5. GitHub Work Report Contract

A commit is both implementation history and a durable work report.

Where applicable, the commit subject/body must make it possible to determine:
- purpose of the work
- material changes
- affected scope
- verification performed and its result
- documentation updated
- remaining / unverified work

Do not use commit text as a replacement for Design Delta when a formal design difference must be preserved.

Commit, push, remote readback, PR, CI, merge, deployment, runtime and production are separate states. A PASS in one state never implies PASS in another.

## 6. Documentation Gate

Before work is considered documentation-complete, determine:

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Additional specialized documentation is created only when the implemented responsibility requires it, for example:
- Interface / Contract
- Data / State Ownership
- Operations / Recovery
- Security
- Verification / Acceptance
- Migration / Compatibility
- reusable Module documentation
- important architectural decision record

Do not create all document types by default.

## 7. Shared Workspace Capabilities

`server-core` defines how shared capabilities are discovered and used from the Workspace. It does not absorb the implementation of those capabilities.

Shared capability categories include:
- MCP servers
- developer tools / skills
- shared secrets / token broker contracts
- GitHub access
- DebugAI access
- KB access
- Cloudflare / Hugging Face and other provider contracts

Actual Secret / Token values must never be committed into server-core.

### DebugAI

DebugAI remains an independent Project/runtime. server-core may publish the supported connection contract (CLI / HTTP and, when implemented and verified, MCP). Do not claim MCP support until the DebugAI repository/runtime provides and verifies an MCP interface.

### Knowledge Base

The planned reusable-development KB lives on the Master PC storage rather than inside server-core. Current target storage is `F:` on the Master PC (1 TB drive).

server-core owns only the access, registration, lifecycle and safety contract. KB data itself is not stored in this repository.

The KB should be suitable for reusable assets such as validated modules, code patterns, schemas, interfaces, tests, templates, verified procedures and curated development knowledge. Server-side access must use an explicit API/MCP or other verified bridge; never assume the VPS can directly read the PC drive.

## 8. Server Operations

The server is a runtime / processing environment, not a replacement for GitHub source history.

Production-resident services use Docker / Docker Compose unless a Project has a formally approved exception.

Operational policy covers:
- deployment from a confirmed repository revision
- runtime verification
- log/cache lifecycle
- server cleanup
- backup/recovery
- resource pressure guardrails

### Log / Cache boundary

Current common model:
- Telegram: durable raw-log authority where the owning Project contract says so
- Meilisearch: rebuildable search index
- Redis: dedup / hot cache
- `/home/admin1/logs`: temporary disk state only
- VPS: processing/runtime environment, not long-term source/document storage

Automated cleanup must be fail-closed. Active state, unshipped data, recovery data, unknown ownership and active volumes are not safe deletion targets.

## 9. Registries

server-core should maintain compact registries for facts that Workspace AIs repeatedly need to discover, where those facts can be kept current and verified, such as:
- Project -> repository -> server path
- runtime / container / port / domain ownership
- available shared MCP / tools
- shared-secret contract identifiers (never values)

Registries are navigation/contract data, not a substitute for runtime readback.

## 10. Context and Efficiency Rules

- Do not read every server-core document at chat/task start.
- Start from README and LOAD_SCOPE.
- Load only the authority needed for the present task.
- Start inside the target repository from its README, then the relevant source/test boundary.
- Do not use archive/build/dist/node_modules/logs/backups/cache as normal context.
- Prefer existing assets before creating new code/files/modules/documents.
- A new document must reduce future development, verification, handoff or operating cost.

## 11. Explicit Non-Goals

server-core does not own:
- Project-specific implementation details
- Project-specific Design bodies
- DebugAI internal design
- Astera / TGserver internal specifications
- KB data
- runtime logs or cache data
- Secret/Token values
- ChatGPT-only Notion continuity
- per-AI private prompts or reasoning

## 12. Design Change Rule

This file is a design baseline. Do not silently rewrite it to follow implementation drift.

When implementation differs, preserve the difference and rationale through the repository's Design Delta mechanism. A formal change to this baseline requires an explicit architecture decision and traceable commit.