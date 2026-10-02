# SERVER CORE STRUCTURE

Version: 2026-10-03
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
- `.aiignore` / `.cursorignore` — historical archive exclusion。Current operational filesを隠さない
- `.cursor/` — Workspace runtime rules / client integration contract。host-local client wiringは追跡しない
- `.github/` — CI / repository automation / task templates
- `docs/` — Design / Router / Registry / Operations contracts
- `operations/` — credential値を持たないmachine-readable contracts / policies
- `scripts/` — Workspace automation / verify / audit helpers
- `archive/` — historical/retired material; Current Authorityではない

## docs/ — Command Center Authorities

### Core command / architecture
- `SERVER_CORE_DESIGN.md` — server-core Design Baseline
- `DESIGN_DELTA.md` — accepted architecture/responsibility changes
- `LOAD_SCOPE.md` — Task routing / progressive context loading
- `G_ACE_WORKSPACE.md` — Workspace operation / fixed development routine
- `SERVER_COMMAND_CONTRACT.md` — Server command technical safety / mutation classification / partial state / evidence boundary
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
- `GITHUB_SKILL.md` — GitHub skill resolver tasks only

Task-specific support documents are not loaded at normal Workspace start.

## operations/

Current machine-readable contracts/policies:
- `cloudflare-account.json`
- `huggingface.json`
- `workspace-mcp.json`
- `storage-lifecycle.json`
- `pre-execution-schema.json` — command-center dispatch fields / routing invariants

`operations/` はcredential実値を保持しない。

## scripts/

Scriptの存在は実行許可を意味しない。read-only helperとmutation-capable helperを区別する。

### Read-only by default
- `storage_lifecycle_audit.py` — bounded read-only storage/disk/Docker audit。default出力は`GACE_RESULT_BEGIN...END`の要約。delete/pruneしない。
- `verify-workspace-mcp.sh` — defaultはglobal MCP config contract readbackのみ。`--client-readback` 時だけ外部clientへ問い合わせる。
- `resolve-codex-skill.sh`, `github-skill-path.sh` — installed skill path/full-read resolver。
- `workspace_command_center_check.py` — defaultはWorkspace wiringのread-only verification。`--repair` は別途 `--authorize-workspace-mutation` が必要。

### Mutation-capable with explicit gate
- `init-dev-workspace.sh` — defaultはread-only check。Workspace wiring / MCP configを変更する場合は `--apply-workspace-mutation` が必要。Project directory作成はさらに `--project NAME --create-project` が必要。Project名はsingle-directory安全文字列へ制限する。
- `install-workspace-mcp.sh` — `~/.cursor/mcp.json` mutation。`--apply-workspace-mcp-mutation` 必須。client credential containerを保持しつつfile modeを0600相当へ締め、bounded backup retentionを適用する。
- `ai-auto-commit.sh` — server-core専用commit helper。`--authorize-server-core-mutation` と1件以上の`--file PATH`が必須。repository-wide `git add -A` は行わず、main/masterへのdirect auto-commitを拒否する。

Mutation option/flagがDocumentに記載されていることを、Task上の実行許可として扱わない。

## .cursor/

- `.cursor/rules/00_agent_runtime.mdc` — Workspace routing / development routine / verification kernel
- `.cursor/rules/cloudflare-operations.mdc` — Cloudflare Task-specific operational rule

Repository-local `.cursor/mcp.json` と `.cursor/agents` はCurrent Authorityとして追跡しない。Workspace-global MCP contractは `operations/workspace-mcp.json`、runtime/client configは `~/.cursor/mcp.json`。Cursor agent installation / inventoryはclient環境が所有し、必要時にCurrent client stateをreadbackする。Repositoryにhost固有absolute symlinkやclient-local agent inventoryを置かない。

Workspace-wide always-applied rules are limited to behavior required for repository, Server, Provider, routing, verification or safety operation。

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
- fixed Workspace routine -> `docs/G_ACE_WORKSPACE.md`
- command-center dispatch fields -> `operations/pre-execution-schema.json`
- Server command technical safety -> `docs/SERVER_COMMAND_CONTRACT.md`
- credential broker/use -> `docs/WORKSPACE_SHARED_SECRETS.md`
- managed Workspace MCP -> `docs/WORKSPACE_MCP.md`

## Project Tree Update Conditions

次は本ファイルの**更新要否を判定する条件**であり、write permissionではない。
- File / Directory追加・削除・移動
- 主要責務変更
- Entry Point変更
- Authority routing変更
- Directory structure変更

実際に本ファイルを更新するには、server-core自体の変更についてexplicit owner authorizationがあり `SERVER_CORE_MUTATION_AUTHORIZED=YES` が成立していることを確認する。未成立なら必要な更新を報告・提案するだけに留める。

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
- host固有absolute symlinkやclient-local MCP/agent inventoryをCurrent Repository Authorityとして追跡しない
- explicit owner authorization無しにserver-coreのStructure/Documentを変更しない
- helperの存在/参照/実行可能性をmutation authorizationと扱わない
- Repository-local client configをWorkspace-global Authorityと二重管理しない
- command-center dispatch field namesを複数Documentで独自派生させず`operations/pre-execution-schema.json`へ揃える
