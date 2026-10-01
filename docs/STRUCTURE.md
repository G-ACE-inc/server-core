# SERVER CORE STRUCTURE

Version: 2026-10-01
Role: `/home/admin1/server-core` のProject Tree / Navigation Index。

## Entry Flow

```text
README.md
  -> docs/LOAD_SCOPE.md
  -> Taskに必要なAuthority
  -> target Project README
```

全Documentを一括読込しない。

## Root

- `README.md` — Workspace Command Center入口 / Authority map
- `CORE.md` — LibralCore開発方法論
- `SERVER_CORE_PROTOCOL.md` — 共通運用・変更・安全境界
- `.aiignore` / `.cursorignore` — context exclusion hints
- `.cursor/` — Workspace runtime rules / client integration
- `.github/` — CI / repository automation
- `docs/` — Design / Router / Registry / Operations contracts
- `operations/` — credential値を持たないmachine-readable contracts / policies
- `scripts/` — Workspace automation / verify / audit helpers
- `archive/` — historical/retired material; Current Authorityではない

## docs/ — Command Center Authorities

### Core command / architecture
- `SERVER_CORE_DESIGN.md` — server-core Design Baseline
- `DESIGN_DELTA.md` — accepted architecture/responsibility changes
- `LOAD_SCOPE.md` — Task routing / progressive context loading
- `G_ACE_WORKSPACE.md` — Workspace operation contract
- `STRUCTURE.md` — 本Navigation Index

### Development / repository governance
- `PROJECT_TEMPLATE.md` — Project/document standard
- `AUTO_COMMIT.md` — GitHub work history / commit / push / readback
- `DEPLOY_RUNBOOK.md` — confirmed GitHub revision -> Server deploy -> Runtime verify
- `GLOSSARY.md` — terminology

### Shared platform / operations
- `WORKSPACE_REGISTRY.md` — Project / Capability / MCP / Tool / credential contract / Runtime discovery
- `WORKSPACE_MCP.md` — Workspace-global MCP manifest/install/verify contract
- `PROJECT_INTEGRATION_RULES.md` — Project-owned service / Vault / MCP / Tool integration contract
- `WORKSPACE_SHARED_SECRETS.md` — shared credential Broker contract
- `KB_REUSE_DESIGN.md` — reusable-development KB access / bridge / lifecycle contract
- `STORAGE_LIFECYCLE.md` — Server log / cache / cleanup / backup / recovery contract
- `CLOUDFLARE_OPERATIONS.md` — Cloudflare common operation contract

### Task-specific support
- `GITHUB_FREE_MAX.md` — GitHub quota-related tasks only
- `GITHUB_SKILL.md` — GitHub skill resolver tasks only

Task-specific support documents are not loaded at normal Workspace start.

## operations/

Current machine-readable contracts/policies:
- `cloudflare-account.json`
- `huggingface.json`
- `workspace-mcp.json`
- `storage-lifecycle.json`

`operations/` はcredential実値を保持しない。

## scripts/

- `ai-auto-commit.sh` — GitHub commit/push helper
- `resolve-codex-skill.sh`, `github-skill-path.sh` — GitHub skill resolver
- `init-dev-workspace.sh` — Workspace initialization + managed MCP configuration
- `install-workspace-mcp.sh` — Cursor Global MCP merge installer
- `verify-workspace-mcp.sh` — Global MCP config verification
- `storage_lifecycle_audit.py` — read-only storage/disk/Docker audit
- `workspace_command_center_check.py` — canonical Workspace structure/settings verification and bounded repair

## .cursor/

- `.cursor/rules/00_agent_runtime.mdc` — Workspace routing / execution / verification kernel
- `.cursor/rules/cloudflare-operations.mdc` — Cloudflare Task-specific operational rule
- `.cursor/mcp.json` — Project/client-specific MCP config when present
- `.cursor/agents/` — agent-related repository assets when present

Workspace-wide always-applied rules are limited to behavior required for repository, Server, Provider, routing, verification or safety operation.

## Shared Capability Boundary

server-coreはMCP / Tool / DebugAI / KB / Providerのimplementation bodyを抱え込まない。

server-coreが持つのは:
- discovery
- owner
- connection/config contract
- permission / change boundary
- verification method
- Workspace common use rule

Discovery authority: `docs/WORKSPACE_REGISTRY.md`。

## Project Integration Boundary

`docs/PROJECT_INTEGRATION_RULES.md` はProject-owned service / Shared CapabilityをProjectへ接続する共通契約。

IntegrationしただけでProject固有実装をserver-coreへ移さない。

## Single Source of Truth

- Project/Runtime discovery -> `docs/WORKSPACE_REGISTRY.md`
- reusable KB access design -> `docs/KB_REUSE_DESIGN.md`
- chronological work history -> GitHub commit / PR
- Workspace routing -> `README.md` + `docs/LOAD_SCOPE.md`
- credential broker/use -> `docs/WORKSPACE_SHARED_SECRETS.md`
- managed Workspace MCP -> `docs/WORKSPACE_MCP.md`

## Project Tree Update Conditions

本ファイルを更新する条件:
- File / Directory追加・削除・移動
- 主要責務変更
- Entry Point変更
- Authority routing変更
- Directory structure変更

内部文章修正だけでは必ずしも更新しない。

## archive/

- credential実値をarchiveへ保存しない
- archiveをCurrent state / Design / Ruleとして扱わない
- normal contextへ入れない

## Invariants

- rootへ用途不明な一時Fileを増やさない
- 既存Authorityと重複する別名Documentを乱立させない
- Directory分類だけを目的にDocumentを増やさない
- credential実値を保存しない
- Project固有implementationをserver-coreへ移してownershipを曖昧にしない
