# Server Core — G-ACE Workspace Command Center

`server-core` は、G-ACE Workspace全体の**司令室**である。

各Projectの実装本体を抱え込む場所ではない。Workspaceで作業するAI / Developerが、**どのProjectで、何を読み、どの共通Tool/MCP/Secret/KBを使い、どう検証し、どうGitHubへ残し、どのApproval Boundaryまで進めるか**を決める共通Command Centerである。

この司令室の中心目的は、**非技術者のMasterが毎回Server構成・運用Rule・利用可能資源・開発手順を技術判断して個別指示しなくても、Workspace AIがserver-coreから必要情報を取得し、Masterの開発Ruleと固定Routineを自動適用して、安全かつ効率的に作業を継続できる状態を維持すること**である。一般的な開発方法へ勝手に置き換えたり、必要工程・既存要件を勝手に省略したりしない。

Workspace作業は、会話履歴や一時作業状態がなくてもserver-coreから開始・復旧できることを要求する。

## 必ずここから開始

Workspace内の作業開始順は固定する。

```text
server-core/README.md
  -> docs/LOAD_SCOPE.md
  -> docs/G_ACE_WORKSPACE.md の固定Routine
  -> 今回必要な追加server-core Authorityだけ
  -> 対象Project README
  -> Current GitHub state（branch / HEAD / latest commit / PR / CIをTaskに必要な範囲で確認）
  -> 必要なDesign / Project Tree / Design Delta / System Document
  -> 対象Source / 直接依存 / 関連Test
```

Source / Config / Test / API / Bug fix / 接続変更を伴う開発Taskでは、`docs/LOAD_SCOPE.md` に従って `CORE.md` を必須開発原則として読む。`G_ACE_WORKSPACE.md` が固定RoutineのOwnerであり、他DocumentはRoutineの一部だけを抜き出して代替しない。

server-coreの全正本を一括読込しない。同一Taskで確認済みのAuthorityは、変更・矛盾・情報不足が無い限り繰り返し読まない。

設計基準線: [`docs/SERVER_CORE_DESIGN.md`](docs/SERVER_CORE_DESIGN.md)  
設計差分: [`docs/DESIGN_DELTA.md`](docs/DESIGN_DELTA.md)

## 司令室としての役割

server-coreはWorkspace全体について次を担当する。

1. **Task Intake / Routing** — 依頼内容を分類し、対象Project・Repository・Authority・必要Contextを決める。
2. **Authority / Context Control** — 必要な正本だけを段階的に読ませる。
3. **Project Dispatch** — 実作業を所有Projectへ送る。Project固有実装をserver-coreへ吸収しない。
4. **Shared Capability Control** — MCP / Tool / Skill / DebugAI / KB / Secret Contract / Provider Contractの発見入口を持つ。
5. **Development / Verification Governance** — 再利用、Design、Delta、Tree、Test、Documentation Gate、PASS条件を統一する。
6. **GitHub Work History** — Commit / PRを実作業履歴として残す。
7. **Runtime / Operations Governance** — confirmed GitHub revisionからのDeploy、Docker Compose、Log/Cache/Cleanup、Backup/Recovery、安全境界を統一する。
8. **Mutation Ownership** — Task対象Repository、参照専用Repository、変更許可Repositoryを分離し、別Task・別Projectへ変更を漏らさない。
9. **Evidence / State Separation** — Source / Test / Commit / Push / PR / CI / Merge / Deploy / Runtime / Productionを別状態として扱う。

## Command Flow

```text
REQUEST
  -> ROUTE
  -> LOAD FIXED ROUTINE
  -> LOAD REQUIRED AUTHORITY
  -> DISPATCH TO PROJECT
  -> READ PROJECT README
  -> READ CURRENT GITHUB STATE
  -> READ REQUIRED DESIGN
  -> REUSE CHECK
  -> IMPLEMENT / DEBUG
  -> VERIFY
  -> DOCUMENTATION GATE
  -> COMMIT = WORK REPORT
  -> PUSH / REMOTE READBACK / PR CURRENT SYNC / CI
  -> APPROVAL BOUNDARY
  -> DEPLOY / RUNTIME VERIFY only when authorized
```

この順序を基本ルーティーンとする。Task固有の事情で工程が不要な場合は不要理由を根拠付きで判定し、必要工程を勝手に落とさない。

## Mutation Ownership

Repositoryを読むことと、変更することは別Operationである。

Task開始時に必要範囲で次を分離する。

```text
TARGET_REPOSITORY
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
SERVER_CORE_MUTATION_AUTHORIZED
```

- `TARGET_REPOSITORY`: 今回の主対象Repository。
- `MUTATION_REPOSITORIES`: 今回Source / Config / Document / Git historyを変更してよいRepository。
- `READ_ONLY_REPOSITORIES`: Authority確認、再利用調査、Integration確認等の参照専用Repository。
- `SERVER_CORE_MUTATION_AUTHORIZED`: server-core自体の変更が明示的に許可されている場合だけ `YES`。

**server-coreは、server-core自体の変更について明示許可が無い限りread-onlyとする。** 別Project作業、共通Rule参照、障害調査、Shared Capability利用だけからserver-core変更許可を推論しない。

複数Project / Agent / change unitが同時進行し得るため、別Taskの未Commit差分をstage / overwriteしない。shared checkoutのreset / rebase / branch switch等は他Taskへの影響を閉じられない限り行わない。

## Current Documentation State

### Command / Routing
- `README.md` — Workspace共通Command Center入口
- `docs/SERVER_CORE_DESIGN.md` — server-core設計基準線
- `docs/DESIGN_DELTA.md` — 設計差分と理由
- `docs/LOAD_SCOPE.md` — Task routing / progressive context loading
- `docs/G_ACE_WORKSPACE.md` — Workspace正規運用 / **固定開発Routineの唯一Owner**
- `docs/SERVER_COMMAND_CONTRACT.md` — Server commandのtechnical safety / partial state / evidence boundary
- `operations/pre-execution-schema.json` — command-center dispatch fieldsのmachine-readable contract
- `docs/STRUCTURE.md` — server-core Project Tree / Navigation

### Development / GitHub
- `CORE.md` — LibralCore開発方法論
- `SERVER_CORE_PROTOCOL.md` — 共通運用・禁止・Approval Boundary・State Semantics
- `docs/PROJECT_TEMPLATE.md` — Project/Document標準
- `docs/AUTO_COMMIT.md` — Commit = Work Report / Push / Remote Readback / PR Current同期
- `docs/DEPLOY_RUNBOOK.md` — confirmed GitHub revisionからRuntime verificationまでの共通Deploy境界

### Shared Platform
- `docs/WORKSPACE_REGISTRY.md` — Project / MCP / Tool / Secret Contract / Runtime discovery
- `docs/WORKSPACE_MCP.md` — Workspace-global MCP設定・検証契約
- `docs/PROJECT_INTEGRATION_RULES.md` — Project-owned service / Vault / MCP / Tool導入契約
- `docs/WORKSPACE_SHARED_SECRETS.md` — Vault経由Shared Secret / Token契約
- `docs/KB_REUSE_DESIGN.md` — reusable-development KB設計
- `docs/STORAGE_LIFECYCLE.md` — Log / Cache / Cleanup / Backup/Recovery設計
- `docs/CLOUDFLARE_OPERATIONS.md` — Cloudflare共通運用契約

### Support
- `docs/GLOSSARY.md` — 正式用語
- `docs/GITHUB_SKILL.md` — GitHub Skill resolver利用時のみ

## Task Routing

| Task | 追加で読むAuthority |
|---|---|
| 全Workspace開発Task | `docs/G_ACE_WORKSPACE.md` |
| Source / Config / Test / API / Bug fix / 接続変更を伴うTask | `CORE.md` |
| server-core設計 / 責務 | `docs/SERVER_CORE_DESIGN.md` + 必要なら `docs/DESIGN_DELTA.md` |
| 共通運用 / 禁止 / Approval Boundary / State | `SERVER_CORE_PROTOCOL.md` |
| Context / 読込範囲 | `docs/LOAD_SCOPE.md` |
| Server command technical safety / evidence | `docs/SERVER_COMMAND_CONTRACT.md` |
| Git / Commit / Push / PR Current同期 | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Project / Document構成 | `docs/PROJECT_TEMPLATE.md` |
| Project / MCP / Tool / DebugAI / Secret / Runtime発見 | `docs/WORKSPACE_REGISTRY.md` |
| Workspace MCP | `docs/WORKSPACE_MCP.md` |
| Project Integration | `docs/PROJECT_INTEGRATION_RULES.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| 再利用KB | `docs/KB_REUSE_DESIGN.md` |
| Log / Cache / Cleanup / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| 用語 | `docs/GLOSSARY.md` |
| server-core構造 | `docs/STRUCTURE.md` |

## Documentation Contract

### README
Current completed / verified stateと入口を示す。Design正本にはしない。

### Design
Architecture / Contract / Boundary / ResponsibilityのBaseline。Current実装へ合わせて履歴を消す上書きをしない。元のDesign記述を保持し、正式変更は元記述の下へ変更履歴として追記する。

### Design Delta
Designとの差を正式採用する場合、差分・理由・Evidence・影響範囲・適用Commit・Compatibility/rollbackを残す。Design本文の履歴保存を置き換えるのではなく補助する。

### Project Tree
主要File/Directoryの責務、Entry Point、関連Design/Testを示すNavigation Index。

### System / Module Document
READMEだけでは別AI/Developerへ説明なしで引継げない完成単位のみ作成/更新する。

Document更新先は対象Projectで決める。対象ProjectのREADMEやREADME-linked Document更新をserver-core Document更新へ読み替えない。

## Documentation Gate

作業完了前に必ず判定する。

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Requiredなのに未更新ならDocumentation Completeではない。

## GitHub = Work History Authority

Commitは単なる保存点ではなく作業報告として扱う。

必要に応じて次を後から追える状態にする。
- Purpose
- Changed
- Affected
- Verified
- Docs
- Remaining / Unverified

Commit / Push / Remote Readback / PR / CI / Merge / Deploy / Runtime / Productionは別状態として扱う。Open PRがあるTaskは、Push/Remote Readback後にPR headと本文がCurrent HEADの作業状態を表しているか確認し、古ければPR本文を同期する。

詳細は `docs/AUTO_COMMIT.md`。

## Shared Workspace Capabilities

共有Capabilityの発見入口は `docs/WORKSPACE_REGISTRY.md`。

server-coreが管理するのは:
- discovery;
- connection contract;
- owner;
- permission / safety boundary;
- availability / verification state;
- Workspace共通利用Rule。

Capability本体は所有Project/runtimeへ残す。

対象:
- MCP;
- DebugAI;
- GitHub tools;
- reusable KB;
- Cloudflare / Hugging Face;
- Vault経由Secret / Token;
- shared development tools / skills。

Capabilityを利用・接続・検証することと、そのowner実装を変更することを分離する。TGserver / webhook gateway等のProject-owned serviceは、複数Projectで使っていても自動的にShared Capability扱いへ変更しない。

DebugAIを使うTaskでは、既に取得済みのEvidence / Tool結果 / prior verified stateを再利用し、同じ調査をServer AIへ重複実行させない。

## Helper Execution Boundary

server-coreのScriptを読むことと、実行してWorkspace / Client / Runtimeを変更することを分離する。

- `scripts/init-dev-workspace.sh`: default read-only check。Workspace wiring変更は明示的なmutation optionが必要。
- `scripts/install-workspace-mcp.sh`: Workspace-global MCP config mutationは明示的なmutation optionが必要。同一config writerは競合時fail closed。
- `scripts/verify-workspace-mcp.sh`: default config-only verification。Live availabilityへ勝手に昇格しない。
- `scripts/workspace_command_center_check.py`: wiring checkとrepairを分離する。
- `scripts/ai-auto-commit.sh`: server-core専用。明示したfile change unitだけをstageし、別Task差分を混ぜない。
- `scripts/storage_lifecycle_audit.py`: bounded audit-only。cleanup/delete/pruneを実行しない。

Helperが存在すること自体をmutation許可として扱わない。

## Server / Runtime

VPSはRuntime / Processing環境であり、GitHub Source履歴・Design・Documentの代替正本にしない。

本番常駐は **Docker Composeを正** とし、Host上の `node` / `python` / `npm start` / `pm2` / `nohup` / `screen` / `tmux` 等を本番常駐経路として採用しない。

Deploy Authority: `docs/DEPLOY_RUNBOOK.md`  
Storage Authority: `docs/STORAGE_LIFECYCLE.md`

Runtime値はRegistryや古い報告から推測せず、必要時に実readbackする。

## Approval Boundary

Masterの明示指示なしに次を越えない。
- main / PR merge
- Production deploy / 公開 / 切替
- Force push / Branch削除
- destructive reset / rebase
- 既存Service停止 / restart / recreate
- Secret変更
- Provider resource作成・変更・削除
- 新規Model download
- 新規Repository / Project / Space作成

未確認・未実行・未検証は `UNKNOWN / NOT_EXECUTED / NOT_VERIFIED` を維持する。
