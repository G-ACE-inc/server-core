# SERVER CORE STRUCTURE

Version: 2026-09-30
Role: `/home/admin1/server-core` のProject Tree / Navigation Index。G-ACE Workspace司令室のAuthorityと実装入口を最短で辿るために使う。

## Entry Flow

```text
README.md
  -> docs/LOAD_SCOPE.md
  -> 今回必要なAuthorityだけ
  -> target Project README
```

全Documentを一括読込しない。

## Root

- `README.md`
  - Workspace Command Centerの唯一の共通入口
  - Task routing / Current scope / Authority map
- `CORE.md`
  - LibralCore開発方法論
  - Part -> Feature -> Component -> System -> Application System
  - reuse / Module / ownership / public contract基準
- `SERVER_CORE_PROTOCOL.md`
  - 共通運用・禁止・Approval Boundary
- `.aiignore` / `.cursorignore`
  - normal context exclusion hints
- `.cursor/`
  - Workspace Agent runtime rules / MCP client config
- `.github/`
  - GitHub Actions / Dependabot / Issue/PR support
- `docs/`
  - Design / Delta / Router / Registry / Project standard / Operations contract
- `operations/`
  - Secret値を持たないProvider / shared contract / audit-policy manifests
- `scripts/`
  - 共通自動化・resolver・read-only audit
- `archive/`
  - 旧版・退避。Current Authorityではなく通常Context対象外

## docs/ — Command Center Authorities

### Core command / architecture
- `SERVER_CORE_DESIGN.md`
  - server-core＝G-ACE Workspace Command CenterのDesign Baseline
- `DESIGN_DELTA.md`
  - Baselineとの差分・理由・Evidence・適用Commit
- `LOAD_SCOPE.md`
  - Task routing / progressive context loading / dispatch
- `G_ACE_WORKSPACE.md`
  - Workspace正規運用契約
- `STRUCTURE.md`
  - 本ファイル。server-core Project Tree

### Development / repository governance
- `PROJECT_TEMPLATE.md`
  - Project構成、README/Design/Tree/Delta/System Document作成条件、Documentation Gate
- `AUTO_COMMIT.md`
  - Commit = Work Report、Push、Remote Readback
- `DEPLOY_RUNBOOK.md`
  - confirmed GitHub revision -> approved deploy -> Runtime Verify
- `GLOSSARY.md`
  - 正式名称 / 用語

### Shared platform / operations
- `WORKSPACE_REGISTRY.md`
  - Project / Repository / MCP / Tool / Secret Contract / Runtime discovery
- `WORKSPACE_SHARED_SECRETS.md`
  - Vault経由Workspace shared Secret / Token契約
- `KB_REUSE_DESIGN.md`
  - Master PC `F:` 1TB reusable-development KB Design Baseline
- `STORAGE_LIFECYCLE.md`
  - Log / Cache / Cleanup / Backup / Recovery / Disk pressure Design Baseline
- `CLOUDFLARE_OPERATIONS.md`
  - Cloudflare固有運用契約

### Task-specific support
- `GITHUB_FREE_MAX.md`
  - GitHub無料枠最適化Task時のみ
- `GITHUB_SKILL.md`
  - GitHub/Codex skill resolver利用時のみ

Task-specific support documents are not loaded at normal Workspace start.

## operations/

Provider / shared-secret / audit-policy等の**値を持たない契約**を置く。

Current known manifests:
- `cloudflare.json`
- `cloudflare-account.json`
- `huggingface.json`
- `storage-lifecycle.json`

`storage-lifecycle.json` current safety boundary:
- `mode=audit_only`
- generic delete disabled
- generic Docker prune disabled
- volume delete disabled

Secret / Token値をoperationsへ保存しない。

## scripts/

- `ai-auto-commit.sh`
  - GitHub work-report commit / push補助
- `resolve-codex-skill.sh`, `github-skill-path.sh`
  - GitHub skill resolver
- `init-dev-workspace.sh`
  - Workspace initialization helper
- `cloudflare_ops.py`
  - Cloudflare operations helper
- `storage_lifecycle_audit.py`
  - Storage / disk / Docker read-only audit
  - mutation機能なし
  - `--self-test`でSafety contract検証

## .cursor/

- `.cursor/rules/00_agent_runtime.mdc`
  - Workspace Agent向けlightweight execution kernel
  - server-core README -> LOAD_SCOPE -> target Projectを強制
- `.cursor/rules/01_japanese_thinking.mdc`
  - language-related rule
- `.cursor/rules/cloudflare-operations.mdc`
  - Cloudflare Task-specific rule
- `.cursor/mcp.json`
  - Cursorに実登録されたMCP client config
  - 文書Registryと実設定を混同しない
- `.cursor/agents`
  - Agent-related references

## Shared Capability Boundary

server-coreはMCP / Tool / DebugAI / KB / Providerの実装本体を抱え込まない。

server-coreが持つのは:
- discovery;
- owner;
- connection contract;
- permission / safety boundary;
- availability state;
- Workspace common use rule。

Discovery authority: `docs/WORKSPACE_REGISTRY.md`。

## Removed Redundant Authorities

重複していた旧Current-state / Knowledge register / status helper / agent-specific checklistはCurrent構成から除去済み。

現在のSingle Source of Truth:
- Project/Runtime discovery -> `docs/WORKSPACE_REGISTRY.md`
- reusable KB design -> `docs/KB_REUSE_DESIGN.md`
- chronological work history -> GitHub commit / PR
- Workspace routing -> `README.md` + `docs/LOAD_SCOPE.md`

## Project Tree Update Conditions

本ファイルを更新する条件:
- File / Directory追加・削除・移動
- 主要責務変更
- Entry Point変更
- Authority routing変更
- Directory structure変更

内部文章修正だけでは必ずしも更新しない。

## archive/

`archive/YYYY-MM-DD/` を基本とする。

- Secretをarchiveへ保存しない
- archiveをCurrent state / Design / Ruleとして扱わない
- normal contextへ入れない

## Prohibitions

- ルート直下への用途不明な一時File
- 既存Authorityと重複する別名Document乱立
- Directory分類だけを目的としたDocument追加
- Secret / Token実値保存
- 実構造変更後に本Treeを未更新のままDocumentation Completeとすること
- Project固有実装を司令室都合だけでserver-coreへ移すこと