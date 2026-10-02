# G-ACE WORKSPACE

Version: 2026-10-02
Role: G-ACE Workspaceでserver-coreを共通Command Centerとして利用するための正規運用契約。

## 1. Purpose

標準Workspace `/home/admin1/workspace/G-ACE.code-workspace` では、server-coreがTask routing、共通Authority、execution orchestration、shared capability discovery、GitHub work history、Server/Provider operation boundaryを管理する。

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

## 3. Command-Center Dispatch / Canonical Pre-execution Contract

Pre-execution field名のmachine-readable正本は `operations/pre-execution-schema.json`。本Document以外のDomain Documentは独自aliasを増やさず、このschemaを参照する。

Task開始時に必要範囲で次を解決する。

```text
PURPOSE
EXPECTED_RESULT
TARGET_PROJECT
TARGET_RESPONSIBILITY
TARGET_REPOSITORY
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
SERVER_CORE_MUTATION_AUTHORIZED
REQUIRED_SERVER_CORE_AUTHORITY
REQUIRED_PROJECT_AUTHORITY
REUSE_CANDIDATES
VERIFY_PATH
CHANGE_BOUNDARY
CONTEXT_SCOPE
NEXT_ACTION
EXECUTION_ROUTE
EXECUTION_CAPABILITY
EXECUTION_AUTHORIZATION
AUTHORIZATION_DOMAIN
AUTHORIZATION_SCOPE
MUTATION_CLASS
PRE_EXECUTION_COMPLETE
BLOCKER
```

対象Projectや責務が不明な場合は `docs/WORKSPACE_REGISTRY.md` でownerを確認する。server-coreや別ProjectをAuthority確認のために読んだだけでは、そのRepositoryをmutation対象にしない。

`PRE_EXECUTION_COMPLETE=YES` とできるのは、Taskに必要な範囲でexact target、required Authority、mutation/read-only boundary、exact next action、required input/revision/endpoint/service identity、verification path、authorization state、unresolved blockerが確定している場合だけ。

現在のAI/Clientに実行Toolが無い場合でも、上記が確定していれば `EXECUTION_CAPABILITY=UNAVAILABLE_IN_CURRENT_CLIENT` として実行直前までhandoffできる。Tool不在と実行許可不足は分離する。

承認待ち、Runtime identity未確認、exact command/action未確定、credential contract不明等が残る場合は `PRE_EXECUTION_COMPLETE=NO` とし、`BLOCKER` を明示する。推測Commandで穴埋めしない。

## 4. Executor Selection

Taskを最も低costかつ安全に閉じられる実行主体を選ぶ。

```text
existing deterministic check / CI
  -> directly available assistant tool / connector
  -> existing read-only helper
  -> exact operator Server command
  -> Server-side AI only when deterministic/direct routes are insufficient
```

現在のassistant/clientで実行できる処理をoperatorへ戻さない。Server-side AIはdeterministic command、Source/Test、既存helper、CI、Provider readbackで閉じられない場合だけ使用する。

`EXECUTION_ROUTE` は `operations/pre-execution-schema.json` の値を使用する。Server command/operator handoffへ進む場合は `docs/SERVER_COMMAND_CONTRACT.md` を追加Authorityとして読む。

## 5. Mutation Ownership / Authorization Scope

Project Taskの既定mutation先は対象Project Repository。

```text
Target Project source/docs/config = target Project ownership
server-core = routing/reference; explicit owner authorizationが無い限りread-only
Shared Capability owner = implementation authority; read-only for ordinary use/integration Task
Provider/service owner = read-only unless owner-side change is actually required
```

`SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示的に成立しない限り、server-coreは `MUTATION_REPOSITORIES` に入れない。

Authorizationは**Current Task / change unit / target identity / operation**へscopeする。過去Taskのpermissionを別Task、別Repository、別Provider resource、別credential、別Runtime、別Production operationへcarry-forwardしない。

「server-coreを読め」「README/Documentを更新」「MCP/Tool/DebugAI/Vault/TGserver/webhook gateway/Cloudflareを使う・接続する・検証する」「Workspace共通Contractに影響がありそう」という指示や判断だけで、server-coreやowner Repositoryをwrite対象へ昇格しない。

複数Repository変更が必要な場合は、各Repositoryについて変更理由・範囲・verification・Git historyを分離する。server-coreを含む場合は、server-core自体の変更についてexplicit owner authorizationを別途確認する。

## 6. Multi-task / Multi-worker Boundary

複数Project、複数Agent、複数change unitが同時進行し得る前提で作業する。

- write/commit前にcurrent repository rootとmutation targetを照合する。
- intended change unitと無関係なuncommitted diffをstage/overwriteしない。
- shared checkoutのbranch switch/reset/rebaseは他Taskへの影響を確認できない限り行わない。
- readbackだけならworking treeを切り替えるよりGit object/API inspectionを優先する。
- server-core `scripts/ai-auto-commit.sh` は明示された `--file PATH` だけをstageする。repository-wide stagingを行わない。

## 7. Workspace Folders / Context

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

通常Contextへ一括投入しない領域:
- `/home/admin1/workspace`
- `/home/admin1/logs`
- `/home/admin1/backups`
- archive / build / dist / dependency / cache / dump領域

Task対象になった場合だけ必要範囲を開く。

## 8. Project Entry

対象ProjectではREADMEを入口にする。

READMEから、存在する場合はDesign、Project Tree、Design Delta、stable System/Feature-bundle/Module documents、run/test/verify entry pointsへ到達できることを標準とする。

これらは**対象Project側のAuthority**である。対象ProjectのREADMEやREADME-linked Documentを更新するTaskを、server-core Document更新へ読み替えない。

server-core側のDocumentは、server-core自体の変更についてexplicit owner authorizationがある場合だけ変更する。

対象Source、直接依存、関連Testから開始し、必要時だけ `docs/LOAD_SCOPE.md` のLevelに従ってContextを広げる。

## 9. Development Routine

```text
server-core command center
  -> target Project README
  -> mutation/read-only repository lock
  -> target Project required Authority
  -> repository / branch / HEAD / status
  -> Source / direct dependency / tests
  -> reuse check
  -> executor selection
  -> implementation / debug / exact pre-execution preparation
  -> verification
  -> target Project documentation gate
  -> GitHub work history
  -> push / remote readback
  -> PR / CI when required
  -> authorized change boundary
  -> deploy/runtime when applicable
```

## 10. Documentation Gate

Documentationは実変更に必要なものだけ更新する。

- Current entryが変わる -> 対象Project README
- File/Directory/主要責務/Entry Pointが変わる -> 対象Project Tree
- Design Baselineから正式に変える -> 対象Project Design Delta
- READMEだけでは運用/保守継続が困難な安定System/Module -> 対象Project System Document

Project固有のDocumentation Gateをserver-core Documentation Gateで代用しない。server-core Documentation Gateは `SERVER_CORE_MUTATION_AUTHORIZED=YES` の場合だけ適用する。

Documentation GateはDocument乱立のためのCheck listではない。

## 11. GitHub Work History

GitHub commit / PRは時系列の実作業履歴。Commit / Push / Remote Readback / PR / CI / Merge / Deploy / Runtime / Productionを別状態として扱う。

Authority: `docs/AUTO_COMMIT.md`。

Commit対象Repositoryはmutation ownershipに従う。参照専用RepositoryへTaskの副作用を残さない。server-coreへのCommitはexplicit owner authorizationが必要。

## 12. Helper Execution Boundary

server-coreのScriptを読む・参照する・Documentから到達できることと、そのScriptを実行してWorkspace / Client / Runtimeを変更することを分離する。

- `scripts/init-dev-workspace.sh`: default read-only check。Workspace mutationは `--apply-workspace-mutation`。Project作成名はsingle-directory safe nameへ限定。
- `scripts/install-workspace-mcp.sh`: global MCP config mutationは `--apply-workspace-mcp-mutation` 必須。authorized installではconfig modeを0600相当へ締め、backup retentionを適用。
- `scripts/verify-workspace-mcp.sh`: default config-only。外部client readbackは `--client-readback` 指定時だけ。client-local credential containerは値を表示せず、live auth proofにも使わない。
- `scripts/workspace_command_center_check.py`: default read-only Workspace wiring check。repairは `--repair --authorize-workspace-mutation`。
- `scripts/ai-auto-commit.sh`: server-core専用。`--authorize-server-core-mutation` と1件以上の `--file PATH` 必須。unrelated diffをstageしない。
- `scripts/storage_lifecycle_audit.py`: bounded audit-only。delete/pruneせず、default出力はcompact result envelope。
- Skill resolver: `--read` は全文を返し、glob/path traversalを許可しない。

Workspace/Client mutation permissionとserver-core Repository mutation permissionは別状態である。

## 13. Shared Capability / Project Integration

Shared Capabilityの発見入口は `docs/WORKSPACE_REGISTRY.md`。server-coreが管理するのはdiscovery、owner、connection/config authority、permission/change boundary、verification method。Capability本体はowning Project/runtimeへ残す。

Project-owned service、Libral Vault、MCP、ToolをProjectへ導入するときは `docs/PROJECT_INTEGRATION_RULES.md` を確認する。

Project-owned serviceをWorkspace Shared Capabilityと誤分類しない。通常はconsumer Project側で接続を完結し、service/capability owner側Source変更は必要性が確認された場合だけ別Task/別mutationとして扱う。

文書記載、過去利用実績、Current Runtime availabilityを分離する。

## 14. Shared Credential

Credential実値をProjectへ複製しない。共有契約は `docs/WORKSPACE_SHARED_SECRETS.md`、発見入口は `docs/WORKSPACE_REGISTRY.md`。

Credential Contractを参照することと、Secret registration/rotation/provider mutationを分離する。

## 15. Reusable Development KB

Reusable KBはserver-core外のowning runtime/data storeに置く。server-coreはAccess / Registration / Lifecycle / Safety / Bridge Contractを管理し、data本体やdevice-specific storage layoutは所有しない。

Authority: `docs/KB_REUSE_DESIGN.md`。

## 16. Server / Runtime

本番常駐は原則Docker / Docker Compose。Project固有の正式例外は対象Project Authorityを優先する。

ServerはRuntime / Processing環境であり、Project Source履歴・Design・Documentの代替正本にしない。

Deployはconfirmed GitHub revisionを起点にし、対象Runbookのchange/approval条件を満たしてから実行する。Authority: `docs/DEPLOY_RUNBOOK.md`。

server-core共通Runbookからgeneric deploy commandを生成・実行しない。対象ProjectのCurrent Authorityでexact target / path / service / deploy procedureが確定している場合だけDeployへ進む。

OperatorへServer commandを渡す場合は `docs/SERVER_COMMAND_CONTRACT.md` に従う。

## 17. Logs / Cache / Cleanup / Backup

Authority: `docs/STORAGE_LIFECYCLE.md`。

server-coreは共通分類・監査・安全境界を定義する。owner不明、active、retry/recovery中、persistent volumeの可能性があるDataをgeneric auto-deleteしない。

Read-only auditもI/O costを持つため、scan budgetとbounded outputを持たせる。

## 18. Runtime Readback Rule

README / Registry / historical reportをCurrent Runtimeの代用にしない。

Container / Port / Domain / Provider / Deploy状態がTask判断に必要なら、対象Provider / Docker / Endpoint / Repositoryをreadbackする。

未確認は `UNKNOWN / NOT_VERIFIED / NOT_EXECUTED` を維持する。Runtime readbackのために別Repository/Providerを参照しても、mutation permissionは自動付与されない。

`git fetch`、temporary checkout/detach、branch switch等は最終状態を戻してもpure read-onlyではなく `REVERSIBLE_LOCAL_MUTATION` として分類する。

## 19. Evidence Handoff

Stateを別Project、別AI、次Taskへ引き継ぐ場合、証明範囲を失わない。

TaskでCurrent stateが重要なら、必要範囲で次を分離して残す。

```text
SUBJECT
EVIDENCE_SCOPE
OBSERVED_AT
OBSERVATION_ROUTE
RESULT
NOT_PROVEN
SOURCE_REVISION when relevant
RUNTIME_OR_PROVIDER_IDENTITY when relevant
```

`HTTP 200` はそのendpoint応答の証拠、`CONFIG_PRESENT` は設定存在の証拠、`CI SUCCESS` はそのrevision/checkの証拠である。これらを隣接Domainの `AVAILABLE / RUNTIME_PASS / PRODUCTION_PASS / COMPLETE` へ自動昇格しない。

Durable Authorityへ残すのはowner、contract、state semantics、verification method等の安定情報。時点付きlive result、branch/HEAD進捗、Task固有failureはGitHub work historyまたはTask evidenceとして扱い、Registry/Designをchronological status boardへしない。

## 20. Completion Rule

Workspace Taskの完了は、Taskに必要な範囲でcorrect routing、correct mutation/read-only ownership、requested implementation/operation、required verification、required target-Project documentation、GitHub work history、required remote/CI/runtime evidence、change boundary complianceが閉じた場合に判定する。

外部実行が必要で現在のclientが実行不能なら、exact actionとauthorization/verificationまで閉じた `PRE_EXECUTION_COMPLETE=YES` をhandoff completionとして扱えるが、実行済み・PASSとは扱わない。

## 21. Authority Ownership / Non-Duplication

同じ共通Ruleを複数Documentで独立定義しない。詳細Ruleのownerを固定し、他Documentは必要な範囲だけ参照する。

```text
Cross-domain mutation / state semantics -> SERVER_CORE_PROTOCOL.md
Workspace task sequence / evidence handoff -> docs/G_ACE_WORKSPACE.md
Canonical pre-execution field schema -> operations/pre-execution-schema.json
Server operator command contract -> docs/SERVER_COMMAND_CONTRACT.md
Discovery / owner / durable capability semantics -> docs/WORKSPACE_REGISTRY.md
Project-to-service/capability integration -> docs/PROJECT_INTEGRATION_RULES.md
Shared credential lifecycle / broker use -> docs/WORKSPACE_SHARED_SECRETS.md
Workspace MCP registration / verification -> docs/WORKSPACE_MCP.md
Deploy state / runtime promotion -> docs/DEPLOY_RUNBOOK.md
Storage audit / cleanup / recovery -> docs/STORAGE_LIFECYCLE.md
Git work history -> docs/AUTO_COMMIT.md
```

Domain Documentはgeneric State SemanticsやPre-execution field名を独自再定義しない。READMEは入口とRouting map、RegistryはDiscoveryとdurable semantics、Design/Design DeltaはArchitectureと正式変更理由を扱い、日々の運用状態や作業ログを保持しない。
