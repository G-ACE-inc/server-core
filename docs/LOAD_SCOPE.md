# SERVER CORE LOAD SCOPE / COMMAND ROUTER

Version: 2026-10-02
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
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
SERVER_CORE_MUTATION_AUTHORIZED
AUTHORITY_REQUIRED
REUSE_CANDIDATES
VERIFY_PATH
CHANGE_BOUNDARY
NEXT_ACTION
EXECUTION_ROUTE
EXECUTION_CAPABILITY
EXECUTION_AUTHORIZATION
PRE_EXECUTION_COMPLETE
BLOCKER
```

`TARGET_REPOSITORY` はTaskの主対象であり、参照したRepository一覧ではない。

`MUTATION_REPOSITORIES` は今回Source / Config / Document / Git historyを変更してよいRepositoryだけを列挙する。Authority確認・再利用調査・shared capability確認のために開いたRepositoryは、明示的な変更理由が無ければ `READ_ONLY_REPOSITORIES` とする。

**server-coreはexplicit owner authorizationが無い限り常にread-only。** server-core自身やWorkspace共通Contractに変更が必要に見えても、`SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示的に成立しない限りmutation対象へ入れない。

対象Project / ownerが不明なら `docs/WORKSPACE_REGISTRY.md` を読む。

既存owner / reusable assetを確認する前に新規Project / Module / Tool / Documentを作らない。

実行Toolが現在のAI/Clientに無い場合でも、exact target / Authority / next action / required inputs / authorization / verify pathまで確定できるなら、`PRE_EXECUTION_COMPLETE=YES` として実行直前のhandoffを成立させる。Tool不在と承認不足は別状態として扱う。

## 4. Mutation Routing

次の語だけではmutation先をserver-coreへ変更しない。
- READMEを更新
- README付属Documentを更新
- 各種Documentを更新
- MCPを使う / 接続する / 検証する
- Vault / TGserver / webhook gateway / Cloudflareを使う
- server-coreを先に読む
- Workspace共通Contractへ影響する可能性がある

これらはTARGET_PROJECT / TARGET_REPOSITORYを維持したまま、対象Project側のDocument / Config / Integrationを変更する指示として解釈する。Shared CapabilityやProvider owner側の実装変更が必要と判明した場合だけ、そのRepositoryを追加mutation対象として明示する。

server-coreは例外で、追加mutation対象にするには**server-core自体の変更についてexplicit owner authorization**が必要。AI判断・依存関係・影響範囲だけでは昇格しない。

複数Repositoryを変更する場合は、Repositoryごとに変更理由、diff、verification、Git historyを分離する。

## 5. Target Repository Loading

対象Projectへ入った後はREADMEを入口にする。

### Documentation ownership rule

対象ProjectのREADME、READMEからリンクされたDesign / Tree / Delta / System / Operations / Contract等は、その対象Project RepositoryのAuthorityとして扱う。

対象Project内で「READMEに付属するDocument」「各種Document」「READMEからリンクするDocument」を更新する指示は、対象Project Repository内のDocument更新を意味する。server-coreのDocument更新へ読み替えない。

server-core側Documentは、server-core自体の変更が明示的に許可された場合だけ更新する。Workspace共通Routing / Authority / Shared Capability / 共通運用Contractに関係するという理由だけでは変更しない。

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

## 6. Project Integration Routing

Project-owned service、Libral Vault、MCP、Tool integrationを変更または追加するときは `docs/PROJECT_INTEGRATION_RULES.md` を必要範囲で確認する。

```text
server-core README
  -> LOAD_SCOPE
  -> PROJECT_INTEGRATION_RULES
  -> target Project README
  -> target Project authority / Source / Test
```

Integration Contractを読むこと自体はserver-coreやservice/provider owner Projectへの変更理由ではない。

## 7. Reuse Search Order

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

Registry entryはCurrent Runtime健康状態の証明でもmutation permissionでもない。

## 8. Normal Context Exclusions

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

## 9. Documentation Read Rule

- README = Current entry
- Design = architecture baseline
- Design Delta = intentional architecture/responsibility difference
- Project Tree = navigation index
- System/Module Document = stable technical handoff
- Commit / PR = chronological work history
- Registry = discovery / owner / connection / verification boundary

一時的なセッション指示や個別作業メモをCurrent Authorityとして扱わない。

Project固有Documentは対象Project Authority。server-core共通DocumentはWorkspace Authority。この2つを相互代用しない。

## 10. Runtime / Registry Rule

READMEやRegistryのRuntime記載はDiscovery metadataまたはlast-known record。

Current状態がTask判断に必要なら対象Provider / Docker / Endpoint / GitHub revision等をreadbackする。未確認値をcarry-forwardしてCurrent扱いしない。

RuntimeやRegistryを確認するためにserver-coreを参照したことを、server-core mutationの理由にしない。

## 11. Stop Reading Condition

作業開始または実行直前handoffに必要な読込は、次を説明・確認できた時点で止める。
- purpose / expected result
- target Project / responsibility
- target repository
- mutation vs read-only repositories
- server-core mutation authorization state
- relevant baseline / contract
- input / output
- direct dependencies / constraints
- reuse candidates
- related tests / verification path
- affected scope
- change boundary
- exact next action / execution route
- execution capability / authorization state
- pre-execution completeness / unresolved blocker

不足した場合だけ次Levelへ進む。

## 12. Router Failure Rule

Task owner、Authority、Runtime state、credential contract、mutation target、exact execution action等が不明な場合は推測で補完しない。

Document更新先が不明な場合も、server-coreを既定の変更先にしない。対象Project READMEとRepository ownershipを確認してから更新する。

server-core mutation authorizationが不明または未付与ならread-onlyを維持する。

`UNKNOWN / NOT_VERIFIED / NOT_IMPLEMENTED` 等の状態を維持し、必要なAuthority/readbackだけ追加取得する。mutation targetが不明な状態ではwrite/commitへ進まない。実行Toolが無いだけなら、target/action/authorization/verificationが確定した時点で外部実行handoffへ切り替える。
