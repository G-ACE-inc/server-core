# SERVER CORE STRUCTURE

## 目的

本ファイルは `/home/admin1/server-core` 自身の構造・主要責務・入口を示すProject Tree / Navigation Indexである。

単なるPath一覧ではなく、AI / Developerが必要な正本へ最短で到達するために使う。

## Entry Flow

```text
README.md
  -> docs/LOAD_SCOPE.md
  -> 今回必要なAuthorityだけ
```

全Documentを一括読込しない。

## Root

- `README.md`
  - Workspace共通の最初の入口
  - Current概要、Routing、主要Authorityへの導線
- `CORE.md`
  - LibralCore開発方法論
  - Part -> Feature -> Component -> System -> Application System
  - 再利用 / Module / ownership / public contractの基準
- `SERVER_CORE_PROTOCOL.md`
  - 共通運用規則とServer運用境界
  - 詳細はTask routingで必要な時だけ読む
- `.aiignore` / `.cursorignore`
  - 通常Context除外ヒント
- `.cursor/`
  - Cursor / Workspace Agent向けruntime rule / MCP設定
- `.github/`
  - GitHub Issue / PR / Actions / Dependabot
- `docs/`
  - Design、Routing、Registry、運用標準、Template、用語
- `operations/`
  - Secret値を持たないProvider / shared contract / audit policy manifest
- `scripts/`
  - 共通自動化・read-only audit
- `archive/`
  - 旧版・退避。通常Context対象外

`KB.md`、`PROJECT_STATUS.md`、`add-status.sh` は責務重複のためCurrent構成から削除済み。再利用KBは `docs/KB_REUSE_DESIGN.md`、Project/Runtime discoveryは `docs/WORKSPACE_REGISTRY.md`、作業履歴はGitHub commit / PRを正とする。

## docs/

- `SERVER_CORE_DESIGN.md`
  - server-coreのDesign Baseline
  - Workspace Authority、README/Design/Delta/Tree/System Document、GitHub作業報告、Shared Platform、KB、Server Operationsの境界
- `LOAD_SCOPE.md`
  - Workspace Task Router / progressive context loading
- `STRUCTURE.md`
  - 本ファイル。server-core Project Tree
- `WORKSPACE_REGISTRY.md`
  - Project / MCP / Tool / Secret Contract / Runtime入口の軽量Discovery Registry
- `KB_REUSE_DESIGN.md`
  - Master PC `F:` 1TBを使う再利用開発KBのDesign Baseline
  - Asset registration / search / lifecycle / bridge / safety boundary
- `STORAGE_LIFECYCLE.md`
  - Log / Cache / Docker storage / Cleanup / Backup / Recovery / Disk pressureのDesign Baseline
- `GLOSSARY.md`
  - 正式名称 / 用語
- `PROJECT_TEMPLATE.md`
  - Project構成、README/Design/Tree/Delta/System Document作成条件、Documentation Gate
- `G_ACE_WORKSPACE.md`
  - Workspace正規仕様
- `AUTO_COMMIT.md`
  - Commit = Work Report、Push、Remote Readback
- `DEPLOY_RUNBOOK.md`
  - Confirmed GitHub revision -> Server Deploy -> Runtime Verify
- `GITHUB_FREE_MAX.md`
  - GitHub無料枠運用。GitHub設定Task時だけ読む
- `GITHUB_SKILL.md`
  - Codex GitHub skill resolver。該当環境で必要時だけ読む
- `CLOUDFLARE_OPERATIONS.md`
  - Cloudflare固有運用
- `WORKSPACE_SHARED_SECRETS.md`
  - Vault経由のWorkspace Shared Secret / Token利用

## operations/

Provider / shared-secret等の**値を持たない契約**と、安全な共通Audit policyを置く。

現在確認対象:
- `cloudflare.json`
- `cloudflare-account.json`
- `huggingface.json`
- `storage-lifecycle.json`
  - Storage auditは`audit_only`
  - generic delete / prune / volume deleteを許可しない

Secret / Token値をoperationsへ保存しない。

## scripts/

- `ai-auto-commit.sh`
  - GitHub work report commit / push補助
- `resolve-codex-skill.sh`, `github-skill-path.sh`
  - GitHub skill resolver
- `init-dev-workspace.sh`
  - Workspace初期化補助
- `cloudflare_ops.py`
  - Cloudflare運用補助
- `storage_lifecycle_audit.py`
  - Storage / disk / Docker状態のread-only audit
  - delete / prune / rotate等のmutation機能を持たない
  - `--self-test`で決定論的Safety contractを検証

## .cursor/

- `.cursor/rules/00_agent_runtime.mdc`
  - Workspace内Agentへ常時適用する軽量実行Kernel
  - server-core README -> LOAD_SCOPE -> target Projectの順を強制
- `.cursor/rules/01_japanese_thinking.mdc`
  - 言語関連Rule
- `.cursor/rules/cloudflare-operations.mdc`
  - Cloudflare Task固有Rule
- `.cursor/mcp.json`
  - Cursorで実際に登録されたMCP設定
  - 未登録MCPを利用可能と扱わない
- `.cursor/agents`
  - Agent関連参照

## Shared Capability Boundary

server-coreはMCP / Tool / DebugAI / KB / Provider等の実装本体を抱え込まない。

server-coreが持つのは:
- discovery
- connection contract
- owner
- permission / safety boundary
- Workspace共通利用Rule

Discovery入口は `docs/WORKSPACE_REGISTRY.md`。

実装本体は各所有Project / Runtimeに置く。

DebugAI MCPはDebugAI PR #22でSource / CI / stdio Protocolまで検証済み。Live DebugAI Runtime接続とWorkspace登録が閉じるまで `AVAILABLE_VERIFIED` としない。

Master PC `F:` 1TBを利用する再利用開発KBは、server-core外部の実データ領域とし、server-coreにはaccess / lifecycle contractだけを置く。

## Project Tree Update Conditions

本ファイルを更新する条件:
- File / Directory追加・削除・移動
- 主要責務変更
- 主要Entry Point変更
- Authority routing変更
- Directory structure変更

内部文章修正だけでは必ずしも更新しない。

## archive/

`archive/YYYY-MM-DD/` を基本とする。

- Secretをarchiveへ保存しない
- archiveをCurrent state / Current design / Current ruleとして扱わない
- 通常Contextへ入れない

## 禁止

- ルート直下への用途不明な一時File
- 既存Authorityと重複する別名Documentの乱立
- Directory分類のためだけのDocument追加
- Secret / Token実値の保存
- 実構造変更後に本Treeを未更新のままDocumentation Completeとすること
