# G-ACE WORKSPACE

Version: 2026-10-03
Role: G-ACE Workspaceでserver-core司令室を必ず起点にして作業するための正規運用契約。

## 1. Purpose

標準Workspace `/home/admin1/workspace/G-ACE.code-workspace` では、AI / Developerはserver-coreを共通Command Centerとして使用する。

server-coreはTask routing、共通Authority、shared capability discovery、GitHub work history、operations boundaryを管理する。Project固有Design / Source / Test / Runtime logic / Project Documentは各Projectが所有する。

## 2. Mandatory Entry

Workspace作業は必ず次から開始する。

```text
/home/admin1/server-core/README.md
  -> /home/admin1/server-core/docs/LOAD_SCOPE.md
  -> 今回必要なserver-core Authorityだけ
  -> 対象Project README
  -> 対象Projectの必要Authority / Source / Testだけ
```

Masterが新規チャット冒頭でこの指示を繰り返さなくてもAI側で適用されることをWorkspace要件とする。Cursorは `/home/admin1/server-core/.cursor/rules/00_agent_runtime.mdc` の `alwaysApply: true` を正とする。VS Code / GitHub Copilot系は `/home/admin1/server-core/.github/copilot-instructions.md`、複数Agent互換入口は `/home/admin1/server-core/AGENTS.md` を正とし、Workspace初期化時に `/home/admin1/projects` ルートへ同一正本のSymlinkを作成する。Workspace checkerはこれらのリンクとAI instruction設定を検証する。

Instruction Fileが存在することだけを実Client適用済みの証明にはしない。Current live WorkspaceではClient側の実読込/readbackも別に確認する。

server-core全正本の一括読込は禁止する。同一Taskで既に確認済みのAuthorityは、変更・矛盾・情報不足が無い限り繰り返し読まない。

## 3. Command-Center Dispatch

Taskを受けたAI / Developerは、作業開始前に必要範囲で次を確定する。

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
APPROVAL_BOUNDARY
CHANGE_BOUNDARY
CONTEXT_SCOPE
BLOCKER
```

対象Projectや責務が不明な場合は `docs/WORKSPACE_REGISTRY.md` でownerを確認する。既存owner / reusable assetを確認せず新規Project / Module / Tool / Documentを作らない。

不明項目を推測で埋めない。作業開始に必要な項目が未確定なら、必要なAuthority/readbackだけ追加取得してから固定ルーティーンへ進む。

## 4. Repository Mutation Ownership

Project Taskの既定mutation先は対象Project Repository。

```text
Target Project source/docs/config = target Project ownership
server-core = routing/reference; server-core自体の明示許可が無い限りread-only
Shared Capability owner = ordinary use/integrationではread-only
Provider/service owner = owner-side changeが実際に必要と確認されるまでread-only
```

`SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示的に成立しない限り、server-coreを `MUTATION_REPOSITORIES` に入れない。

複数Repository変更が必要な場合は、Repositoryごとに変更理由・範囲・verification・Git historyを分離する。

複数Project / Agent / change unitが同時進行し得るため、別Taskのuncommitted diffをstage / overwriteしない。shared checkoutのswitch/reset/rebaseは他Taskへの影響を閉じられない限り行わない。readbackだけならGit object/API inspectionを優先する。

## 5. Workspace Folders

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

通常Workspace Contextへ含めない:
- `/home/admin1/workspace`
- `/home/admin1/logs`
- `/home/admin1/backups`
- archive / build / dist / dependency / cache / dump領域

Task対象になった場合だけ必要範囲を開く。

## 6. Project Entry

対象ProjectではREADMEを入口にする。

READMEから、存在する場合は次へ直接到達できる状態を標準とする。
- Design
- Project Tree
- Design Delta
- completed System / Feature-bundle / Module documents
- run / test / verify entry points

これらは対象Project側のAuthorityである。対象ProjectのREADMEやREADME-linked Document更新をserver-core Document更新へ読み替えない。

対象Source、直接依存、関連Testから開始し、必要時だけ `docs/LOAD_SCOPE.md` のLevelに従ってContextを広げる。

## 7. Development Routine

```text
server-core command center
  -> target Project README
  -> required Design / Tree / Delta / System Document
  -> repository / branch / HEAD / status
  -> Source / direct dependency / tests
  -> reuse check
  -> implementation / debug
  -> diff
  -> verification
  -> documentation gate
  -> GitHub commit as work report
  -> push / remote readback
  -> PR / CI when required
  -> approval boundary
  -> deploy/runtime only when authorized
```

この順序を通常ルーティーンとして維持し、必要工程を理由なく省略しない。

## 8. Documentation Gate

作業終了前に必ず判定する。

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Requiredなのに未更新ならDocumentation Completeではない。

DesignをCurrent実装へ合わせて履歴が消える形で上書きしない。

## 9. GitHub Work History

GitHub commit / PRは実作業履歴の正本。

Commitは必要に応じて目的、主要変更、影響範囲、検証、Document更新、残作業を後から追えるWork Reportにする。

次を別状態として扱う。

```text
SOURCE
TEST
COMMIT
PUSH
REMOTE_READBACK
PR
CI
MERGE
DEPLOY
RUNTIME
PRODUCTION
```

Authority: `docs/AUTO_COMMIT.md`。

## 10. Shared MCP / Tool / DebugAI

共有Capabilityの発見入口は `docs/WORKSPACE_REGISTRY.md`。

server-coreが管理するのは接続契約・owner・permission boundary・availability / verification stateであり、Capability本体ではない。

`.cursor/mcp.json` 等の実設定とRegistry文書を分離する。文書記載だけでMCP利用可能とは扱わない。

DebugAIは独立Project/runtimeとして扱い、Source実装、MCP Protocol、Workspace registration、Current live runtimeを別状態として保持する。DebugAIを利用する場合は、既に取得済みのEvidenceや既存Tool結果を再利用し、同じ調査をServer AIへ重複実行させない。

## 11. Project Integration

TGserver / webhook gateway等のProject-owned service、Libral Vault、MCP、ToolをProjectへ導入するときは `docs/PROJECT_INTEGRATION_RULES.md` を確認する。

Project-owned serviceは複数Projectで利用されても自動的にShared Capabilityへ分類変更しない。通常はconsumer Project側で接続を完結し、owner側Source変更が必要と確認された場合だけ別mutationとして扱う。

## 12. Shared Secrets

Secret / Token実値を各Projectへ複製しない。

共有契約は `docs/WORKSPACE_SHARED_SECRETS.md`、発見入口は `docs/WORKSPACE_REGISTRY.md`。

ProjectはShared Secretが必要な場合、既存Contractを確認してBroker経由で利用する。既存Contractが無ければ勝手なtoken copy/helperを作らない。

## 13. Reusable Development KB

Reusable KBはserver-core外のowning runtime/data storeに置く。server-coreはAccess / Registration / Lifecycle / Safety Contractを持ち、data本体は持たない。

VPS / Workspace AIからPC filesystemを直接読める前提は禁止し、実装・検証済みAPI/MCP等のbridgeを使う。

Authority: `docs/KB_REUSE_DESIGN.md`。

## 14. Server / Runtime

本番常駐は **Docker Composeを正** とする。Host上の `node` / `python` / `npm start` / `pm2` / `nohup` / `screen` / `tmux` 等を本番常駐経路として採用しない。

ServerはRuntime/Processing環境であり、Project Source履歴・Design・Documentの正本をServerだけに置かない。

Deployはconfirmed GitHub revisionを起点にし、必要なApproval Boundaryを満たした後に対象Project/共通Runbookへ従う。

Authority: `docs/DEPLOY_RUNBOOK.md`。

## 15. Server Command Safety

Server commandのtechnical safetyは `docs/SERVER_COMMAND_CONTRACT.md` を正とする。

- parent interactive shellを意図せず終了させない。
- exact target / repository / path / serviceを確認する。
- multi-step mutationで後段が失敗した場合は、実際に適用済みのstateを `PARTIAL` として保持する。
- diagnosticsは必要十分な範囲へbounded化し、Secret値を出力しない。
- same-target writerはserializeするかfail closedする。
- commandを発行しただけで実行済み/PASSへ昇格しない。

## 16. Logs / Cache / Cleanup / Backup

Authority: `docs/STORAGE_LIFECYCLE.md`。

server-coreは共通分類・監査・安全境界を定義する。owner不明、active、retry/recovery中、persistent volumeの可能性があるDataをgeneric auto-deleteしない。

Read-only auditもI/O costを持つため、scan budgetとbounded outputを持たせる。

## 17. Runtime Readback Rule

README / Registry / historical reportをCurrent Runtimeの代用にしない。

Container / Port / Domain / Provider / Deploy状態がTask判断に必要なら、対象Provider / Docker / Endpoint / Repositoryをreadbackする。

未確認は `UNKNOWN / NOT_VERIFIED / NOT_EXECUTED` を維持する。

`git fetch`、temporary checkout/detach、branch switch等は最終状態を戻してもpure read-onlyではなく `REVERSIBLE_LOCAL_MUTATION` として扱う。

## 18. Completion Rule

Workspace Taskが完了と言えるのは、Taskに必要な範囲で次が閉じた場合だけ。
- correct Project/authority routing;
- implementation or requested work;
- required verification;
- Documentation Gate;
- GitHub work history;
- required remote/CI/runtime evidence;
- approval boundary compliance。

司令室の役割は「何でも実装すること」ではなく、**Workspace全体の作業を正しいowner・正しいAuthority・正しいEvidenceへ導き、固定ルーティーンから勝手に脱線させないこと**である。
