# Server Core — 全Project共通統治基盤

## 目的

`Server Core`（`/home/admin1/server-core`）は、G-ACE環境内の全Projectへ適用する共通思想、運用規則、読込範囲、作業手順、GitHub運用、Workspace方針を管理する最上位の統治領域である。

本Repository自体はApplicationや業務Systemではない。各Projectの実装詳細を集約せず、全Projectへ共通適用する規則と、各正本への入口だけを保持する。

LibralCoreは、開発AIが再利用可能な設計とCodeを効率よく生成・修正するための開発概念、設計方針、開発スタイルである。アプリ接続基盤、共通Runtime、Plugin Framework、Module登録・起動・停止機構ではなく、各Application Systemへの接続・依存を前提としない。

## 管理者と変更権限

- 最終決定者は管理者である。
- AI・作業者は、管理者の明示的な変更指示がある対象と範囲だけを変更する。
- 質問、疑問、検討、提案、操作方法の説明は変更承認として扱わない。
- 実装済み・検証済み・稼働中などの状態は、実File、実行結果、対象Projectの正本文書で確認する。

## 作業開始時の読込順序

1. `README.md`
2. `docs/LOAD_SCOPE.md`
3. `SERVER_CORE_PROTOCOL.md`
4. `CORE.md`
5. `KB.md`
6. `PROJECT_STATUS.md`

`archive/`、`.github/`、`scripts/`は通常読込対象ではない。現在の作業に直接必要なFileだけを限定して読む。

## 正本文書

| File | 役割 |
|---|---|
| `README.md` | Server Coreの入口、読込順序、現行構成の要約 |
| `docs/LOAD_SCOPE.md` | AI・作業者が読む範囲と読まない範囲 |
| `SERVER_CORE_PROTOCOL.md` | 全Project共通の運用規則 |
| `CORE.md` | LibralCore開発方法論と5段Architecture原則 |
| `KB.md` | Server Coreで確認済みの知識・判断Register |
| `PROJECT_STATUS.md` | 現在状態と各Project正本への入口 |
| `docs/STRUCTURE.md` | Server Core自身のDirectory構造 |
| `docs/GLOSSARY.md` | 正式名称、表記、責務境界 |
| `docs/G_ACE_WORKSPACE.md` | G-ACE Workspaceの正規仕様 |

`KB.md`はServer Core内の判断Registerであり、Knowledge Base System本体ではない。KB Systemの設計・実装・状態は対象Repository側の正本文書を正とする。

## 現行Repository構成

```text
server-core/
├── README.md
├── SERVER_CORE_PROTOCOL.md
├── CORE.md
├── KB.md
├── PROJECT_STATUS.md
├── add-status.sh
├── .aiignore
├── .cursorignore
├── .cursor/
│   ├── agents -> /home/admin1/.cursor/agents
│   └── rules/
│       └── 00_agent_runtime.mdc
├── docs/
│   ├── LOAD_SCOPE.md
│   ├── STRUCTURE.md
│   ├── GLOSSARY.md
│   ├── PROJECT_TEMPLATE.md
│   ├── DEPLOY_RUNBOOK.md
│   ├── OPERATION_CHECKLIST.md
│   ├── AUTO_COMMIT.md
│   ├── GITHUB_FREE_MAX.md
│   ├── GITHUB_SKILL.md
│   └── G_ACE_WORKSPACE.md
├── scripts/
│   ├── ai-auto-commit.sh
│   ├── resolve-codex-skill.sh
│   └── github-skill-path.sh
├── .github/
│   ├── workflows/server-core-guard.yml
│   ├── ISSUE_TEMPLATE/ai-task.yml
│   ├── pull_request_template.md
│   └── dependabot.yml
└── archive/
    ├── README.md
    └── isolated/
        ├── README.md
        └── 2026-06-26/
            └── PROJECT_STATUS.before-tgserver-canonical.archived.md
```

### `add-status.sh`

旧運用からの呼出しを安全に停止する互換Guardである。`PROJECT_STATUS.md`へ追記せず、エラー終了してGitHub commit / PRを作業履歴の正本として案内する。

### Cursor Runtime

- `.cursor/agents`は共通Agent定義 `/home/admin1/.cursor/agents` への参照である。
- `.cursor/rules/00_agent_runtime.mdc`はWorkspace固有の読込Guardと優先順位を適用する。
- `.aiignore`と`.cursorignore`は、`archive/`、`.github/`、`scripts/`を通常Contextから除外する補助設定である。

### GitHub Automation

- `.github/workflows/server-core-guard.yml`: 必須File、Load Scope、Secret、表記、Shell構文を確認する軽量CI
- `.github/dependabot.yml`: GitHub Actions Dependencyを週次確認
- `.github/pull_request_template.md`: PR確認項目
- `.github/ISSUE_TEMPLATE/ai-task.yml`: AI作業のGoal、Scope、Guardrailを固定するIssue Template

### Script

- `scripts/ai-auto-commit.sh`: 差分、`.env`、Secret Pattern、`git diff --check`、Shell構文を確認してcommitし、指定時にpushする
- `scripts/resolve-codex-skill.sh`: Codex Plugin SkillのVersion非依存Path Resolver
- `scripts/github-skill-path.sh`: GitHub Plugin Skill用Wrapper

## 共通Architecture原則

全Projectは次の5段を、開発AIが完成物を理解・分解・再利用・再構成するための論理構造として使用する。

1. Part
2. Feature
3. Component
4. System
5. Application System

5段はRuntime階層、アプリ接続順序、物理Directory構造ではない。Moduleは、同一Project内または別Projectで再利用・交換・独立修正しやすいように責務をまとめた開発上の再利用単位であり、LibralCoreへの登録、起動、停止を意味しない。詳細は`CORE.md`と`SERVER_CORE_PROTOCOL.md`を正とする。

## 標準Workspace

標準Workspaceは次とする。

```text
/home/admin1/workspace/G-ACE.code-workspace
```

通常Folderは次に限定する。

- `/home/admin1/server-core`
- `/home/admin1/projects`

`/home/admin1/logs`、`/home/admin1/backups`、`/home/admin1/kb`、`/home/admin1/workspace`は通常作業Folderに含めない。

## Project正本

Project固有の構造、仕様、API、環境変数、Test、Deployment、運用状態は各Project側の正本文書を正とする。

主要入口:

- TGserver: `/home/admin1/projects/TGserver`
- Astera v8: `/home/admin1/projects/astera_v8`

実在Path、Git状態、Docker状態は作業開始時に実環境で確認する。

## 作業原則

- 目的 → 設計 → 構造 → 実装 → 検証 → 運用の順序を飛ばさない。
- 新規Code生成前に、同じ責務を持つ既存の設計、Code、Module、型、Schema、Test、Templateを確認する。
- 既存資産は、そのまま利用 → 設定・型調整 → 薄いAdapter → 共通部分抽出 → 新規実装の順で判断する。
- Project構造は各Projectの`STRUCTURE.md`を正とする。
- 実Fileと正本文書を一致させる。
- 作業報告や変更履歴を正本文書の本文へ混在させない。
- 不要・重複・旧版Fileは即削除せず、秘密情報を含まないことを確認して`archive/YYYY-MM-DD/`へ退避する。
- `.env`、Token、Password、Session、CredentialをGit管理へ含めない。
- 本番運用はDocker / Docker Composeを基本とする。
- 本番起動、公開、切替、Deploymentは管理者の明示承認後に行う。

## GitHub運用

- 作業履歴の正本はGitHub commit / PRである。
- File変更を伴う作業は、差分と検証結果を確認し、意味のある単位でcommit / pushする。
- 標準手順は`docs/AUTO_COMMIT.md`と`scripts/ai-auto-commit.sh`を正とする。
- mainへの直接pushは、管理者が明示した正本更新または小規模な運用文書更新に限定する。
- 実装変更、複数Project変更、高Risk変更はPRを優先する。

## 状態確認

現在のサーバー状態と主要Project入口は`PROJECT_STATUS.md`を確認する。

`PROJECT_STATUS.md`は作業履歴の保管先ではない。管理者の明示指示がある場合だけ、確認済みの現在状態へ更新する。

## 最重要

- LibralCoreをRuntimeまたはアプリ連結基盤として扱わない。
- 既存Application SystemへLibralCore接続・登録・依存を追加しない。
- 再利用候補を確認せず、同じ責務をゼロから生成しない。
- 未確認の状態を断定しない。
- 実行していない処理を完了扱いしない。
- 未実装機能を実装済みとして扱わない。
- 記録されていない作業は存在しないものとして扱う。
