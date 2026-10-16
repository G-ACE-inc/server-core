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
- `AGENTS.md`
  - Codex等SERVER_AI向け最小bootstrap。詳細Ruleを埋め込まずRule Plane #16へroutingする
- `.aiignore` / `.cursorignore`
  - normal context exclusion hints
- `.cursor/`
  - Workspace Agent runtime rules / MCP client config
- `.github/`
  - GitHub Actions / Dependabot / Issue/PR support
  - `copilot-instructions.md` はGitHub Copilot向けSERVER_AI最小bootstrap
- `Dockerfile.project-control`
  - bounded GitHub Project Control receiver image
- `Dockerfile.project-control.dockerignore`
  - Project Control image build context allowlist
- `docker-compose.project-control.yml`
  - Project Control receiver Docker Compose runtime Source; no host port publication
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
  - Task routing / progressive context loading / executor profile dispatch
- `GITHUB_PROJECT_RULE_PLANE.md`
  - GitHub Project #1でSERVER_AI / GPT_CHATのRule Planeを分離管理するAuthority / loading contract
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
  - Project / shared Capability / MCP / Tool / Secret Contract / Runtime discovery
- `WORKSPACE_MCP.md`
  - Cursor Global MCP / Workspace共通実行経路 / verification
- `PROJECT_INTEGRATION_RULES.md`
  - TGserver / webhook gateway / Vault / MCP / Tool Project導入契約
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
- `cloudflare-account.json`
- `huggingface.json`
- `workspace-mcp.json`
- `storage-lifecycle.json`
- `github-project-control.json` — Personal GitHub Project #1 bounded mutation/readback contract
- `github-project-rule-plane.json` — Project #1 / Issue #15/#16/#17を固定するdual rule-plane machine contract

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
  - Workspace initialization helper + shared MCP installation
- `install-workspace-mcp.sh`
  - Cursor Global MCP merge installer
- `verify-workspace-mcp.sh`
  - Global MCP config / optional Cursor CLI verification
- `storage_lifecycle_audit.py`
  - Storage / disk / Docker read-only audit
  - mutation機能なし
  - `--self-test`でSafety contract検証
- `github_project_control.py`
  - Personal Project #1の`Wave / Gate / Change Unit / Mutation Owner`だけを固定Contractで更新しexact readbackする
- `github_project_request_from_comment.py`
  - owner-only `[GACE-PROJECT]` commentをfixed requestへ変換する
- `github_project_internal_send.py`
  - Generic Internal Event API `/internal/events`へ固定destinationで送信する
- `github_project_internal_receiver.py`
  - 固定destination + HMAC署名を検証しProject-Control-only requestだけを実行する
- `github_project_*_test.py`
  - request / transport / runtime config回帰

### GPT CHAT decision checkpoint implementation (CU #40)

- `scripts/gace_project_current_recovery.py` / `scripts/gace_project_current_recovery_test.py`: read-only Project registration and owning Current recovery; exact `--issue-url` selection and optional `--include-body` avoid unrelated body reads and duplicate fetching; no dispatch grant
- `scripts/github_project_chat_turn_gate.py`: bounded START/FAILURE/STOP **supplied-receipt** evaluator; not native ChatGPT send interception
- `scripts/github_project_chat_turn_gate_test.py`: positive/negative receipt regression; does not prove an actual CHAT turn continued
- `scripts/servercore_bounded_result_poll.py` / `scripts/servercore_bounded_result_poll_test.py`: request-correlated Host-result wait, bounded backoff and logical lookup/wait diagnostics; existing verify workflow runs regression tests
- `.github/workflows/server-core-guard.yml`: existing deterministic test invocation; scoped CU #40 design/documentation PR preflight; on `main` push, rejects CU #40 gate-path changes without an exact main-target merged PR SHA when native branch protection is unavailable (private GitHub Free)
- `.github/workflows/chatgpt-live-api-verify.yml`: existing live bounded Host lane, explicit START admission before Host credentials and commands
- `.github/chatgpt-live-api-target.json`: existing bounded trigger; keep idle configuration after tests
- `docs/DESIGN_DELTA.md`: recorded decision/limit of CU #40 Gate implementation and real operational evidence

## .cursor/

- `.cursor/rules/00_agent_runtime.mdc`
  - Cursor SERVER_AI向け最小bootstrap
  - server-core -> rule-plane contract -> #16 / Project Current -> targetをroutingし、GPT_CHAT #17をdefault loadしない
- `.cursor/rules/01_japanese_thinking.mdc`
  - language-related rule
- `.cursor/rules/cloudflare-operations.mdc`
  - Cloudflare Task-specific rule
- `.cursor/mcp.json`
  - server-core Project固有/現在のCursor MCP client config
  - Workspace共通MCPの配布元は `operations/workspace-mcp.json` と `~/.cursor/mcp.json`
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

GitHub Project #1 bounded control contract -> `operations/github-project-control.json` + Project Control scripts / workflow。

Workspace DebugAI stdio entry -> `operations/workspace-mcp.json` -> existing
Compose container `/app/bin/debugai-mcp.mjs`; installer owns exact prior transport
migration and verification owns config readback. DebugAI retains execution ownership.
`scripts/verify-debugai-project-route.sh` checks that route with a live stdio MCP
client and exact Host revision comparison; it cannot approve/apply/deploy.

## Project Integration Boundary

`docs/PROJECT_INTEGRATION_RULES.md` is the common contract for adopting TGserver / webhook gateway / Libral Vault / MCP / Tool in a Project. TGserver and webhook gateway remain Project-owned services; Libral Vault remains a Workspace-shared Secret capability with Project-specific usage contracts.

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

`operations/github-project-debugai-routing.json` owns shared Standing Delegation
reflection dispatch metadata only. Policy verification/receipt issuance stays in
DebugAI; server-core does not copy its executor or policy engine.

## Master Internal Persistent Delegation

Purpose is fixed: preserve the existing sales/customer full approval path and
extend only Master's own development to persistent delegation for verified
GitHub Project #1 repositories. Canonical Workspace registry/mapping:
`operations/master-internal-repositories.json`; routing:
`operations/github-project-debugai-routing.json`. This extends the existing
Workspace registry, not a new control plane. DebugAI owns validation/admission
implementation: `docs/MASTER_INTERNAL_PERSISTENT_DELEGATION.md` in its repository.

Each entry has verified GitHub repo numeric/node/owner/Project-item identity,
server project/path, default/allowed branches, operations/scopes, pinned Compose
runtime/services/private health/digest, effect/path policy, enabled/revoked state
and audit identity. Initial entry is DebugAI; other registered repos receive no
automatic grant. Trusted Host admission verifies and reads back an exact private
copy in the existing delegation trust root. Every execution rechecks GitHub
owner/admin/principal, Project item, mapping and exact target before a short
single-use receipt. Repo delegation has no expiry; disable/revoke is immediate.

Design delta: optional Master Internal registry lookup on the existing MCP/Host
lane. Legacy manual and finite Standing modes remain compatible; no Commercial,
licensing, Customer authentication, new executor/queue/transport/service or shell
endpoint. Source/CI and real Runtime qualification remain separate; this source
checkpoint does not claim live persistent-mode PASS. Protected product/spec/public/
provider/model/Secret/destructive persistent decisions remain Master-owned.
