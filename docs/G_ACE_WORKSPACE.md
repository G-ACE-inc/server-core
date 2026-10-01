# G-ACE WORKSPACE

Version: 2026-10-01
Role: G-ACE Workspaceでserver-coreを共通Command Centerとして利用するための正規運用契約。

## 1. Purpose

標準Workspace `/home/admin1/workspace/G-ACE.code-workspace` では、server-coreがTask routing、共通Authority、shared capability discovery、GitHub work history、Server/Provider operation boundaryを管理する。

Project固有Design / Source / Test / Runtime logic / Project Documentは各Projectが所有する。

## 2. Mandatory Entry

```text
/home/admin1/server-core/README.md
  -> /home/admin1/server-core/docs/LOAD_SCOPE.md
  -> Taskに必要なserver-core Authorityだけ
  -> 対象Project README
  -> 対象Projectの必要Authority / Source / Test
```

server-core全正本を一括読込しない。

## 3. Command-Center Dispatch

Task開始時に必要範囲で次を解決する。

```text
PURPOSE
EXPECTED_RESULT
TARGET_PROJECT
TARGET_RESPONSIBILITY
REQUIRED_SERVER_CORE_AUTHORITY
REQUIRED_PROJECT_AUTHORITY
REUSE_CANDIDATES
VERIFY_PATH
CHANGE_BOUNDARY
```

対象Projectや責務が不明な場合は `docs/WORKSPACE_REGISTRY.md` でownerを確認する。

## 4. Workspace Folders

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

通常Contextへ一括投入しない領域:
- `/home/admin1/workspace`
- `/home/admin1/logs`
- `/home/admin1/backups`
- archive / build / dist / dependency / cache / dump領域

Task対象になった場合だけ必要範囲を開く。

## 5. Project Entry

対象ProjectではREADMEを入口にする。

READMEから、存在する場合は次へ到達できることを標準とする。
- Design
- Project Tree
- Design Delta
- stable System / Feature-bundle / Module documents
- run / test / verify entry points

これらは**対象Project側のAuthority**である。対象ProjectのREADMEやREADME-linked Documentを更新するTaskを、server-core Document更新へ読み替えない。

server-core側のDocument変更は、Workspace共通のRouting / Authority / Shared Capability / 共通運用Contract自体が変更される場合に限定する。

対象Source、直接依存、関連Testから開始し、必要時だけ `docs/LOAD_SCOPE.md` のLevelに従ってContextを広げる。

## 6. Development Routine

```text
server-core command center
  -> target Project README
  -> target Project required Design / Tree / Delta / System Document
  -> repository / branch / HEAD / status
  -> Source / direct dependency / tests
  -> reuse check
  -> implementation / debug
  -> diff
  -> verification
  -> target Project documentation gate
  -> GitHub commit
  -> push / remote readback
  -> PR / CI when required
  -> authorized change boundary
  -> deploy/runtime when applicable
```

## 7. Documentation Gate

Documentationは実変更に必要なものだけ更新する。

- Current entryが変わる -> 対象Project README
- File/Directory/主要責務/Entry Pointが変わる -> 対象Project Tree
- Design Baselineから正式に変える -> 対象Project Design Delta
- READMEだけでは運用/保守継続が困難な安定System/Module -> 対象Project System Document

Project固有のDocumentation Gateをserver-core Documentation Gateで代用しない。

Documentation GateはDocument乱立のためのCheck listではない。

## 8. GitHub Work History

GitHub commit / PRは時系列の実作業履歴。

Commit / Push / Remote Readback / PR / CI / Merge / Deploy / Runtime / Productionを別状態として扱う。

Authority: `docs/AUTO_COMMIT.md`。

## 9. Shared Capability

Shared Capabilityの発見入口は `docs/WORKSPACE_REGISTRY.md`。

server-coreが管理するのはdiscovery、owner、connection/config authority、permission/change boundary、verification method。Capability本体はowning Project/runtimeへ残す。

文書記載、過去利用実績、Current Runtime availabilityを分離する。

## 10. Project Integration

Project-owned service、Libral Vault、MCP、ToolをProjectへ導入するときは `docs/PROJECT_INTEGRATION_RULES.md` を確認する。

Project-owned serviceをWorkspace Shared Capabilityと誤分類しない。Shared CapabilityでもProject固有consumer/injection/runtime usageはProject側契約で管理する。

## 11. Shared Credential

Credential実値をProjectへ複製しない。

共有契約は `docs/WORKSPACE_SHARED_SECRETS.md`、発見入口は `docs/WORKSPACE_REGISTRY.md`。

既存Contractが無い場合は、識別子・consumer・broker・allowlist・verification methodを先に定義する。

## 12. Reusable Development KB

Reusable KBはserver-core外のowning runtime/data storeに置く。

server-coreはAccess / Registration / Lifecycle / Safety / Bridge Contractを管理し、data本体やdevice-specific storage layoutは所有しない。

Authority: `docs/KB_REUSE_DESIGN.md`。

## 13. Server / Runtime

本番常駐は原則Docker / Docker Compose。Project固有の正式例外は対象Project Authorityを優先する。

ServerはRuntime / Processing環境であり、Project Source履歴・Design・Documentの代替正本にしない。

Deployはconfirmed GitHub revisionを起点にし、対象Runbookのchange/approval条件を満たしてから実行する。

Authority: `docs/DEPLOY_RUNBOOK.md`。

## 14. Logs / Cache / Cleanup / Backup

Authority: `docs/STORAGE_LIFECYCLE.md`。

server-coreは共通分類・監査・安全境界を定義する。Project固有のdurable log authority、retention、retry/recovery条件はowning Project側を正とする。

owner不明、active、retry/recovery中、persistent volumeの可能性があるDataをgeneric auto-deleteしない。

## 15. Runtime Readback Rule

README / Registry / historical reportをCurrent Runtimeの代用にしない。

Container / Port / Domain / Provider / Deploy状態がTask判断に必要なら、対象Provider / Docker / Endpoint / Repositoryをreadbackする。

未確認は `UNKNOWN / NOT_VERIFIED / NOT_EXECUTED` を維持する。

## 16. Completion Rule

Workspace Taskの完了は、Taskに必要な範囲で次が閉じた場合に判定する。
- correct Project / authority routing
- requested implementation or operation
- required verification
- required target-Project documentation update
- GitHub work history when source/config changed
- required remote / CI / runtime evidence
- change boundary compliance

server-coreの役割はWorkspace全体の作業を正しいowner・Authority・Evidence・Runtime boundaryへ導くことである。
