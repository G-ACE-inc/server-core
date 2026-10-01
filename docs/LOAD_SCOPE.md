# SERVER CORE LOAD SCOPE / COMMAND ROUTER

Version: 2026-10-01
Role: G-ACE WorkspaceがTaskを正しいProject / Authorityへ振り分け、必要情報だけを段階的に読むためのRouter。

## 1. Mandatory Start

```text
1. server-core/README.md
2. server-core/docs/LOAD_SCOPE.md
3. Taskに必要なserver-core Authorityだけ
4. 対象Project README
5. 対象Project内の必要なDesign / Tree / Delta / System Document / Source / Test
```

README以外のserver-core Authorityを新Task開始時に一括読込しない。同一Taskで確認済みのAuthorityは、変更・矛盾・情報不足が無い限り繰り返し読まない。

## 2. Command Routing

| Task | 追加で読むserver-core Authority |
|---|---|
| server-core自身の設計 / 責務 | `docs/SERVER_CORE_DESIGN.md` + 必要なら `docs/DESIGN_DELTA.md` |
| 開発方法論 / Module / 再利用 | `CORE.md` |
| 共通運用 / 変更 / 安全境界 | `SERVER_CORE_PROTOCOL.md` |
| Workspace運用 / dispatch | `docs/G_ACE_WORKSPACE.md` |
| Project / Repository / shared Capability / Runtime discovery | `docs/WORKSPACE_REGISTRY.md` |
| Project Integration | `docs/PROJECT_INTEGRATION_RULES.md` |
| Git / Commit / Push / work history | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Project / Document構成 | `docs/PROJECT_TEMPLATE.md` |
| Shared Secret / credential | `docs/WORKSPACE_SHARED_SECRETS.md` |
| Reusable KB / bridge | `docs/KB_REUSE_DESIGN.md` |
| Log / Cache / Cleanup / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| GitHub無料枠 | `docs/GITHUB_FREE_MAX.md` |
| GitHub skill resolver | `docs/GITHUB_SKILL.md` |
| 用語 | `docs/GLOSSARY.md` |
| server-core構造 | `docs/STRUCTURE.md` |

複合作業では必要Authorityだけ組み合わせる。

## 3. Dispatch Decision

対象Projectへ入る前に、Taskに必要な範囲で次を解決する。

```text
PURPOSE
EXPECTED_RESULT
TARGET_PROJECT
TARGET_RESPONSIBILITY
TARGET_REPOSITORY
AUTHORITY_REQUIRED
REUSE_CANDIDATES
VERIFY_PATH
CHANGE_BOUNDARY
```

対象Project / ownerが不明なら `docs/WORKSPACE_REGISTRY.md` を読む。

既存owner / reusable assetを確認する前に新規Project / Module / Tool / Documentを作らない。

## 4. Target Repository Loading

対象Projectへ入った後はREADMEを入口とする。

### Level 0: Repository Entry
- Current purpose / responsibility
- Current verified state when present
- Design / Tree / Deltaへの導線
- run / test / verify entry

### Level 1: Target Boundary
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
- Task自体が全体監査 / 全コード確認 / 横断調査を要求している

## 5. Project Integration Routing

Project-owned service、Libral Vault、MCP、Tool integrationを変更または追加するときは `docs/PROJECT_INTEGRATION_RULES.md` を必要範囲で確認する。

```text
server-core README
  -> LOAD_SCOPE
  -> PROJECT_INTEGRATION_RULES
  -> target Project README
  -> target Project authority / Source / Test
```

## 6. Reuse Search Order

```text
対象Project内
  -> docs/WORKSPACE_REGISTRY.md の共有Capability
  -> Workspace内の既存共有資産
  -> verified KB / Tool / MCP
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

## 7. Normal Context Exclusions

通常Contextへ入れない。
- `.git/`
- dependency directories (`node_modules/` 等)
- generated output (`dist/`, `build/`, `.next/` 等)
- archive
- logs / dumps / cache
- backups
- credential実値
- Taskと無関係なRepository

`.github/` や `scripts/` もTask対象でない限り一括読込しない。

## 8. Documentation Read Rule

- README = Current entry
- Design = architecture baseline
- Design Delta = intentional architecture/responsibility difference
- Project Tree = navigation index
- System/Module Document = stable technical handoff
- Commit / PR = chronological work history
- Registry = discovery / owner / connection / verification boundary

一時的なセッション指示や個別作業メモをCurrent Authorityとして扱わない。

## 9. Runtime / Registry Rule

READMEやRegistryのRuntime記載はDiscovery metadataまたはlast-known record。

Current状態がTask判断に必要なら対象Provider / Docker / Endpoint / GitHub revision等をreadbackする。未確認値をcarry-forwardしてCurrent扱いしない。

## 10. Stop Reading Condition

作業開始に必要な読込は、次を説明・確認できた時点で止める。
- purpose / expected result
- target Project / responsibility
- relevant baseline / contract
- input / output
- direct dependencies / constraints
- reuse candidates
- related tests / verification path
- affected scope
- change boundary

不足した場合だけ次Levelへ進む。

## 11. Router Failure Rule

Task owner、Authority、Runtime state、credential contract等が不明な場合は推測で補完しない。

`UNKNOWN / NOT_VERIFIED / NOT_IMPLEMENTED` 等の状態を維持し、必要なAuthority/readbackだけ追加取得する。
