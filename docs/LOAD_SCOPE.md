# SERVER CORE LOAD SCOPE / COMMAND ROUTER

Version: 2026-10-05
Role: G-ACE Workspace司令室がTaskを正しいProject / Authorityへ振り分け、必要情報だけを段階的に読ませるためのRouter。

## 1. Executor Profile / Mandatory Start

最初に実行主体を分ける。Rule payloadを混ぜない。

### SERVER_AI

```text
1. server-core/README.md
2. server-core/docs/LOAD_SCOPE.md
3. operations/github-project-rule-plane.json
4. canonical Rule Plane #16 / GitHub Project #1 Current when accessible
5. 対象Repository Current
6. 今回必要なserver-core / Project Authority・Source・Testだけ
```

### GPT_CHAT

```text
1. canonical Rule Plane #17
2. GitHub Project #1 Current
3. Workspace/server controlが必要なTaskだけserver-coreを読む
4. target Project Current / Repository Evidence
```

GPT_CHAT拡張RuleをSERVER_AIへdefault loadしない。

README以外のserver-core Authorityを新Task開始時に一括読込しない。

同一Taskで一度確認済みのAuthorityは、変更・矛盾・情報不足が無い限り毎ターン再読込しない。

## 2. Command Routing

| Task | 追加で読むserver-core Authority |
|---|---|
| server-core自身の設計/司令室責務 | `docs/SERVER_CORE_DESIGN.md` + 必要なら `docs/DESIGN_DELTA.md` |
| 開発方法論 / 責務 / 5段 / Module / 再利用 | `CORE.md` |
| 共通運用 / 禁止 / Approval Boundary | `SERVER_CORE_PROTOCOL.md` |
| Master Terminal Command / Copy&Paste / GACE_RESULT / Shell Safety / Syntax Validation | `docs/MASTER_TERMINAL_COMMAND.md` |
| Workspace運用 / dispatch | `docs/G_ACE_WORKSPACE.md` |
| Project / Repository / shared Capability / MCP / Tool / DebugAI / Runtime discovery | `docs/WORKSPACE_REGISTRY.md` |
| Project Integration（TGserver / webhook gateway / Vault / MCP / Tool） | `docs/PROJECT_INTEGRATION_RULES.md` |
| Git / Commit / Push / work report | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Project / Document構成 | `docs/PROJECT_TEMPLATE.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| Reusable KB / F: storage / KB bridge | `docs/KB_REUSE_DESIGN.md` |
| Log / Cache / Cleanup / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| GitHub無料枠 | `docs/GITHUB_FREE_MAX.md` |
| GitHub skill resolver | `docs/GITHUB_SKILL.md` |
| 用語 | `docs/GLOSSARY.md` |
| GitHub Project Rule Plane / executor profile | `docs/GITHUB_PROJECT_RULE_PLANE.md` + `operations/github-project-rule-plane.json` |
| server-core構造 | `docs/STRUCTURE.md` |

複合作業では必要Authorityだけ組み合わせる。

## 3. Dispatch Decision

対象Projectへ入る前に、Taskに必要な範囲で次を確定する。

```text
PURPOSE
EXPECTED_RESULT
TARGET_PROJECT
TARGET_RESPONSIBILITY
TARGET_REPOSITORY
AUTHORITY_REQUIRED
REUSE_CANDIDATES
VERIFY_PATH
APPROVAL_BOUNDARY
```

対象Project / ownerが不明なら `docs/WORKSPACE_REGISTRY.md` を読む。

既存owner / reusable assetを確認する前に新規Project / Module / Tool / Documentを作らない。

## 4. Target Repository Loading

対象Projectへ入った後はREADMEを入口とする。

### Level 0: Repository Entry
- README Current State
- Designへのリンク
- Project Treeへのリンク
- Design Deltaへのリンク
- completed System / Feature-bundle / Module Documentへのリンク
- run / test / verify entry

存在しないDocumentを推測で作成済み扱いしない。

### Level 1: Target Boundary
最初に読む。
- 対象Source
- Input / Output
- 直接依存
- 関連Test
- 明示された再利用候補

通常変更がLevel 1で閉じられるならそこで止める。

### Level 2: Adjacent Boundary
次の場合だけ拡張する。
- 呼出元 / 呼出先が必要
- Config / State ownerが不明
- Interface / Schema契約確認が必要
- 近接再利用候補の比較が必要

### Level 3: Reuse Unit
次の場合だけModule / Component範囲へ拡張する。
- 同じ責務の既存実装比較が必要
- Adapter / shared contract検討が必要
- 責務混在 / 循環依存の可能性がある

### Level 4: System / Repository
次の場合だけSystem / Repository全体へ拡張する。
- 複数Component / Moduleへ影響
- 局所情報で影響範囲を閉じられない
- Masterが全体監査 / 全コード確認 / 横断調査を明示

### 4.1 Project Integration Routing

TGserver / webhook gateway / Libral Vault / Project-level MCP・Tool integrationを変更または追加するときは、`docs/PROJECT_INTEGRATION_RULES.md` を必要範囲で確認する。

```text
server-core README
  -> LOAD_SCOPE
  -> PROJECT_INTEGRATION_RULES
  -> target Project README
  -> target Project authority / Source / Test
```

## 5. Reuse Search Order

新規Code / Module / Tool / Document作成前に必要範囲で確認する。

```text
対象Project内
  -> docs/WORKSPACE_REGISTRY.md の共有Capability
  -> Workspace内の既存共有資産
  -> AVAILABLE_VERIFIEDなKB / Tool / MCP
  -> 必要な場合だけ公式外部Authority
```

Reuse priority:

```text
そのまま利用
  -> 設定 / 引数 / 型調整
  -> 薄いAdapter
  -> 共通部分抽出
  -> 新規実装
```

Registry entryはCurrent Runtime健康状態の証明ではない。

## 6. Normal Context Exclusions

通常Contextへ入れない。
- `archive/`
- `.github/`（GitHub Task時を除く）
- `scripts/`（Script Task時を除く）
- `.git/`
- `node_modules/`
- `dist/` / `build/` / `.next/`
- logs / dumps / cache
- backups
- Secret / credential実値

Task対象の場合だけ必要Fileへ限定して読む。

## 7. Documentation Read Rule

- README = Current completed / verified entry
- Design = architecture baseline
- Design Delta = intentional difference / rationale
- Project Tree = navigation index
- System/Module Document = completed unit handoff
- Commit / PR = chronological work history

DesignとCurrent実装が違う場合、DesignをCurrentへ合わせて履歴を消さない。

## 8. Runtime / Registry Rule

READMEや `docs/WORKSPACE_REGISTRY.md` のRuntime記載はDiscovery metadata。

Current状態がTask判断に必要なら対象Provider / Docker / Endpoint / GitHub revision等をreadbackする。

未確認値をcarry-forwardしてCurrent扱いしない。

## 9. Stop Reading Condition

作業開始に必要な読込は、次を説明・確認できた時点で止める。
- purpose / expected result;
- target Project / responsibility;
- Design baseline when relevant;
- input / output;
- direct dependencies / constraints;
- reuse candidates;
- related tests / verification path;
- affected scope;
- approval boundary。

不足した場合だけ次Levelへ進む。

## 10. Router Failure Rule

Task owner、Authority、Runtime state、Secret contract等が不明な場合は推測で補完しない。

`UNKNOWN / NOT_VERIFIED / NOT_IMPLEMENTED` を維持し、必要なAuthority/readbackだけ追加取得する。