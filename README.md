# Server Core — G-ACE Workspace Command Center

`server-core` は、G-ACE Workspace全体の**共通運用・Routing・Authority入口**である。

各Projectの実装本体を抱え込む場所ではない。Workspace内の作業を、正しいProject、正しいAuthority、正しいShared Capability、正しい検証経路へ振り分けるためのCommand Centerである。

## Start Here

Workspace内の作業は次の順で開始する。

```text
server-core/README.md
  -> docs/LOAD_SCOPE.md
  -> Taskに必要なserver-core Authorityだけ
  -> 対象Project README
  -> 必要なDesign / Tree / Delta / System Document / Source / Test
```

server-core全Documentを毎回読み込まない。Task対象に必要なAuthorityだけを段階的に開く。

設計基準線: [`docs/SERVER_CORE_DESIGN.md`](docs/SERVER_CORE_DESIGN.md)  
設計差分: [`docs/DESIGN_DELTA.md`](docs/DESIGN_DELTA.md)

## server-coreの責務

1. **Task Routing** — Taskの対象Project、責務、Repository、必要Authorityを決める。
2. **Authority / Context Control** — Current Authorityを特定し、必要情報だけを読み込む。
3. **Project Dispatch** — Project固有実装をowning Projectへ送る。
4. **Shared Capability Discovery** — MCP / Tool / DebugAI / KB / Provider / Secret Contractのowner・接続・利用境界を示す。
5. **Verification Governance** — Source / Test / CI / Runtime / Provider readbackを混同せず、Taskごとの受入条件を確認する。
6. **GitHub Work History** — Commit / PRを変更履歴として残す。
7. **Server / Runtime Governance** — confirmed sourceからDeploy、Runtime verification、Storage/Backup/Recoveryまでの共通境界を定義する。

## Mutation Ownership

server-coreを読むことと、server-coreを変更することは別である。

Project Task開始時は次を分離する。

```text
TARGET_REPOSITORY = 主対象Repository
MUTATION_REPOSITORIES = 今回write/commitしてよいRepository
READ_ONLY_REPOSITORIES = Authority/Reuse/Integration確認だけのRepository
```

**server-coreは明示的なowner authorization（explicit owner authorization）が無い限り常にread-onlyとする。** Workspace共通Routing / Authority / Shared Capability / 共通運用Contractの変更が必要に見える場合でも、それだけでserver-coreをmutation対象へ昇格しない。server-core変更は、server-core自体の変更を明示的に許可した場合だけ実行する。

明示許可は、別Projectの作業依頼、`server-coreを読め`、`必要ならDocumentを更新`、`共通Ruleも確認`、`改善できるところは進めろ` 等から推論してはならない。**server-core自体を変更してよいことが明確でない限り、server-coreはread-onlyを維持する。**

Shared CapabilityやProject-owned serviceを「使う・接続する・検証する」ことは、そのowner Repository実装を変更する意味ではない。consumer Project側で閉じられるTaskはconsumer側だけを変更する。

## Standard Flow

```text
REQUEST
  -> ROUTE
  -> LOCK TARGET / MUTATION OWNERSHIP
  -> LOAD REQUIRED AUTHORITY
  -> DISPATCH TO PROJECT
  -> REUSE CHECK
  -> IMPLEMENT / DEBUG
  -> VERIFY
  -> DOCUMENTATION GATE
  -> COMMIT / PUSH / REMOTE READBACK
  -> PR / CI when required
  -> AUTHORIZED CHANGE BOUNDARY
  -> DEPLOY / RUNTIME VERIFY when applicable
```

`Source`, `Test`, `Commit`, `Push`, `PR`, `CI`, `Merge`, `Deploy`, `Runtime`, `Production` は別状態として扱う。

## Authority Map

### Command / Architecture
- `docs/SERVER_CORE_DESIGN.md` — server-core設計基準線
- `docs/DESIGN_DELTA.md` — 正式な設計差分
- `docs/LOAD_SCOPE.md` — Task routing / progressive context loading
- `docs/G_ACE_WORKSPACE.md` — Workspace運用
- `docs/STRUCTURE.md` — server-core Navigation / Project Tree

### Development / Repository
- `CORE.md` — LibralCore開発方法論
- `SERVER_CORE_PROTOCOL.md` — 共通運用・変更・安全境界
- `docs/PROJECT_TEMPLATE.md` — Project / Document標準
- `docs/AUTO_COMMIT.md` — Commit / Push / Remote Readback
- `docs/DEPLOY_RUNBOOK.md` — GitHub revisionからServer RuntimeまでのDeploy境界

### Shared Platform / Server Operations
- `docs/WORKSPACE_REGISTRY.md` — Project / Capability / MCP / Tool / Secret Contract / Runtime discovery
- `docs/WORKSPACE_MCP.md` — Workspace-global MCP設定・検証契約
- `docs/PROJECT_INTEGRATION_RULES.md` — Project-owned service / Vault / MCP / Tool導入契約
- `docs/WORKSPACE_SHARED_SECRETS.md` — Shared Secret / Token Broker契約
- `docs/KB_REUSE_DESIGN.md` — reusable development KB接続契約
- `docs/STORAGE_LIFECYCLE.md` — Server storage / log / cache / backup / recovery
- `docs/CLOUDFLARE_OPERATIONS.md` — Cloudflare共通運用契約

### Task-specific Support
- `docs/GITHUB_SKILL.md` — GitHub Skill resolver利用時のみ
- `docs/GLOSSARY.md` — 用語

## Task Routing

| Task | 追加で読むAuthority |
|---|---|
| server-core設計 / 責務 | `docs/SERVER_CORE_DESIGN.md` + 必要なら `docs/DESIGN_DELTA.md` |
| 開発方法論 / 再利用 / Module | `CORE.md` |
| 共通運用 / 変更境界 | `SERVER_CORE_PROTOCOL.md` |
| Workspace運用 | `docs/G_ACE_WORKSPACE.md` |
| Project / Capability / Runtime discovery | `docs/WORKSPACE_REGISTRY.md` |
| Workspace MCP | `docs/WORKSPACE_MCP.md` |
| Project Integration | `docs/PROJECT_INTEGRATION_RULES.md` |
| Git / Commit / Push | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| Reusable KB | `docs/KB_REUSE_DESIGN.md` |
| Storage / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| Repository構造 | `docs/STRUCTURE.md` |

## Documentation Responsibilities

- **README**: Current entry point。詳細な作業日誌や一時的な検証状態を置かない。
- **Design**: Architecture / Contract / Responsibility / BoundaryのBaseline。
- **Design Delta**: Baselineから正式に変えた事項と理由を記録する。
- **Project Tree**: 主要File / Directory / Entry PointのNavigation。
- **System Document**: READMEだけでは継続運用できない完成単位の技術仕様。
- **Commit / PR**: 時系列の作業履歴。
- **Registry**: Project / Capability / owner / connection / verification boundaryの発見情報。

### Documentation Ownership

Document更新先は**Taskの対象Project**で決める。

対象Projectで「READMEと付属Documentを更新」「各種Documentを更新」「READMEからリンクするDocumentを整備」と指示された場合、対象はそのProject Repository内のREADME / Design / Tree / Delta / System / Operations等である。`server-core` Documentへ置き換えて解釈しない。

server-coreは共通の**参照・Routing元**であって、他ProjectのREADME関連Documentの保存先ではない。

`server-core`側Documentは、**server-core自体の変更が明示的に許可された場合だけ**更新する。Workspace共通Contractへ影響しそうという判断だけで、server-core Documentを変更してはならない。

Current Authorityへ個人向け指示、一時的な作業報告、Task固有の進捗状態を混在させない。

## Shared Capability Boundary

server-coreが保持するのはShared Capabilityの**発見・owner・connection contract・permission/change boundary・verification method**である。

Capability本体はowning Project/runtimeへ残す。Project固有の実装値、runtime値、hostname、port、container、secret injection等をWorkspace共通文書へ固定しない。

AvailabilityはTask時に必要な範囲で実設定 / transport / interface / representative callを確認する。過去利用実績とCurrent Runtime状態を分離する。

Capabilityを利用・検証しただけでowner実装を変更しない。実装改修が必要と確認された場合だけ、そのowner Repositoryを別mutation対象として扱う。

## Project Integration Boundary

TGserver / webhook gateway等のProject-owned serviceや、Libral Vault / MCP / ToolをProjectへ接続する場合は `docs/PROJECT_INTEGRATION_RULES.md` を共通契約として使う。

Integration contractはowner、consumer、interface、credential、failure、verification等の必要事項だけを定義する。Project固有実装やRuntime内部をserver-coreへ移さない。

Integration Contractを読むことを、server-coreやservice owner Repositoryへのwrite permissionと扱わない。

## Helper Execution Boundary

server-coreのScriptを**読むこと・存在を確認すること・Documentから参照すること**と、そのScriptを実行してWorkspace/Client/Runtimeを変更することは別Operationである。

- `scripts/init-dev-workspace.sh` はdefaultでread-only check。Workspace wiringを変更する場合だけ `--apply-workspace-mutation` を明示する。
- `scripts/install-workspace-mcp.sh` は `~/.cursor/mcp.json` を変更し得るため、`--apply-workspace-mcp-mutation` が無ければ変更しない。
- `scripts/verify-workspace-mcp.sh` はdefaultでconfig-only readback。外部client readbackは `--client-readback` 指定時だけ行う。
- `scripts/workspace_command_center_check.py --repair` は `--authorize-workspace-mutation` を追加指定しない限りrepairしない。
- `scripts/ai-auto-commit.sh` はserver-core専用で、server-core自体への明示許可を表す `--authorize-server-core-mutation` が必須。
- `scripts/storage_lifecycle_audit.py` はread-only auditであり、cleanup/delete/pruneを実行しない。

Scriptにmutation optionが存在すること自体を実行許可として扱わない。Taskの対象とchange boundaryに必要なOperationだけ選ぶ。

## Server / Runtime Boundary

ServerはRuntime / Processing環境であり、GitHub Source履歴・Design・Documentの代替正本ではない。

本番常駐の標準経路はDocker / Docker Compose。Project固有の正式例外がある場合は対象Project Authorityを優先する。

Deploy Authority: `docs/DEPLOY_RUNBOOK.md`  
Storage Authority: `docs/STORAGE_LIFECYCLE.md`

Runtime値は古い報告やRegistry記載から推測せず、Task判断に必要な時点でreadbackする。

server-coreのDeploy/Storage Runbookを読んだことを、server-core自身や別Projectを操作対象にする根拠にしない。

Generic Deploy Commandはserver-coreから生成しない。Deploy実行は対象Project側のCurrent Authorityでexact target/path/service/procedureが確定している場合だけ行う。

## Change / Safety Boundary

Read-only確認とMutationを分離する。Merge、Deploy、Production cutover、active service restart/recreate、Secret mutation、Provider resource mutation等は、対象Repository / Project / Provider Authorityで定義された権限・承認条件に従う。

**server-coreへのwrite / commit / branch mutationは、server-core自体の変更について明示的なowner authorizationが必要。** 他Project Task、共通Authority参照、障害調査、Shared Capability利用から暗黙に承認を推論しない。

未確認・未実行・未検証の状態を、文書記載や過去実績だけでCurrent PASSへ昇格しない。
