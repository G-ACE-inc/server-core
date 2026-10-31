# Server Core — G-ACE Workspace Command Center

## Current and runtime evidence (not this README's authority)

This README is the stable **server-core entry and routing index**. Current Mission/CU lives in GitHub Project #1 and its owning Current Issue; runtime admission/status requires direct Host readback. Historical 2026-10-08 Master Internal Delegation evidence is retained in [WORKSPACE_MCP historical snapshot](docs/WORKSPACE_MCP.md#master-internal-persistent-delegation-runtime-verified-2026-10-08); current product implementation/evidence: [DebugAI #41](https://github.com/seigo-gace/debug-ai/issues/41). Do not treat that snapshot as present runtime authorization.


`server-core` は、G-ACE Workspace全体の**司令室**である。

Current運用の最上位Control PlaneはGitHub Project #1へ移行する。server-coreは両AI用Rule全文を抱える場所ではなく、**GitHub Projectを運用するためのbootstrap / router / control room**として、Workspace/serverの安定した入口・安全境界・shared capability・bounded runtimeを提供する。

Rule Planeは二つに分離する。
- Server AI Minimal Kernel: `G-ACE-inc/server-core#16`
- GPT CHAT Orchestrator Kernel: `G-ACE-inc/server-core#17`

Machine contract: [`operations/github-project-rule-plane.json`](operations/github-project-rule-plane.json)  
Design / loading contract: [`docs/GITHUB_PROJECT_RULE_PLANE.md`](docs/GITHUB_PROJECT_RULE_PLANE.md)

各Projectの実装本体は所有Repositoryに残す。

TGserver ZEROのProject登録・Group増設管理もserver-coreを入口にする：`python3 scripts/tgzero_admin.py lookup --repo OWNER/REPO` で既存番号・実Topic ID・実機正本ファイルを照会、`register --request /private/request.json` で登録から既存Composeへの反映・読込SHA照合まで実施する。`runtime-status` で稼働一致を確認。発見契約は [`operations/tgzero-registration.json`](operations/tgzero-registration.json)、運用は [Project Integration Rules](docs/PROJECT_INTEGRATION_RULES.md) と所有RepositoryのZERO Operations。

## 必ずここから開始

Workspace内の作業開始順は固定する。

```text
SERVER_AI
  -> server-core/README.md
  -> docs/LOAD_SCOPE.md
  -> operations/github-project-rule-plane.json
  -> Rule Plane #16 / GitHub Project Current
  -> target Repository Current
  -> 必要なAuthority / Source / Testだけ

GPT_CHAT / ChatGPT Work coordinator
  -> docs/G_ACE_WORKSPACE.md §6 (sole CHAT development Work Routine)
  -> GitHub Project #1 / Control #15 / owning Project and Change Unit Current
  -> current Mission / writer / acceptance / next runnable action
  -> target Repository Source / CI / required Host evidence
  -> execute -> verify -> record -> iterate in the same turn
  -> docs/MASTER_TERMINAL_COMMAND.md only when issuing Master a terminal command
```

server-coreの全正本を一括読込しない。

設計基準線: [`docs/SERVER_CORE_DESIGN.md`](docs/SERVER_CORE_DESIGN.md)  
ツール開発の**２つの必須機能／実行順：先に② CHAT→Server、既存Log成果を維持して後に①残課題**（共通設計・Current責任＝[server-core Control #10](https://github.com/G-ACE-inc/server-core/issues/10)）：**① 統合Development Log（収集→TGserver ZERO保存→検索→CHAT間復元）**は [`SERVER_CORE_DESIGN` §17](docs/SERVER_CORE_DESIGN.md#17-tool-capability-a--unified-development-log-collect-persist-search-and-restore-2026-10-10)、**② CHAT→Serverの調査・操作・安全なSource反映・Runtime証拠**は [`SERVER_CORE_DESIGN` §16](docs/SERVER_CORE_DESIGN.md#16-tool-capability-b--common-chat-to-host-controlled-reflection-design-contract-2026-10-10)。いずれもGitHub Project #1の固定目的に従う。**設計のmain反映やCIのみではLog保存・Server反映の実E2Eは未完**。
設計差分: [`docs/DESIGN_DELTA.md`](docs/DESIGN_DELTA.md)

server-core owns intake/routing, shared capability discovery, verification boundaries and GitHub work history. Project implementation stays in its owning Repository. GitHub Project #1 / owning Current controls changing work; this README is a stable entry index, not a parallel work plan or runtime status authority.

## Task Routing

| Task | 追加で読むAuthority |
|---|---|
| 開発方法論 / 責務 / Module / 再利用 | `CORE.md` |
| 共通運用 / 禁止 / Approval Boundary | `SERVER_CORE_PROTOCOL.md` |
| Context / 読込範囲 | `docs/LOAD_SCOPE.md` |
| Master Terminal Command / Copy&Paste / GACE_RESULT / Shell Safety / Syntax Validation | `docs/MASTER_TERMINAL_COMMAND.md` |
| Workspace運用 | `docs/G_ACE_WORKSPACE.md` |
| Git / Commit / Push | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Repo登録 / Project開始 / 両Hostの共通接続手順 | `docs/PROJECT_INTEGRATION_RULES.md` → Project開始・登録runbook + `docs/PROJECT_TEMPLATE.md` |
| Project / shared Capability / MCP / Tool / DebugAI / Secret / Runtime発見 | `docs/WORKSPACE_REGISTRY.md` |
| Workspace共通MCPの登録 / Cursor Global MCP / 検証 | `docs/WORKSPACE_MCP.md` |
| GitHub Projectからの共通server操作routing | `operations/github-project-bounded-host.json` + `docs/GITHUB_PROJECT_CHAT_HOST_ROUTE.md` |
| Project導入（TGserver / webhook gateway / Vault / MCP / Tool） | `docs/PROJECT_INTEGRATION_RULES.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| 再利用KB | `docs/KB_REUSE_DESIGN.md` |
| Log / Cache / Cleanup / Backup / Recovery | `docs/STORAGE_LIFECYCLE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| 用語 | `docs/GLOSSARY.md` |
| GitHub無料枠 / GitHub Skill resolver（該当Taskのみ） | `docs/GITHUB_FREE_MAX.md` / `docs/GITHUB_SKILL.md` |
| GitHub Project Rule Plane / AI profile routing | `docs/GITHUB_PROJECT_RULE_PLANE.md` + `operations/github-project-rule-plane.json` |
| server-core構造 | `docs/STRUCTURE.md` |
| server-core設計判断 / 差分 | `docs/SERVER_CORE_DESIGN.md` + `docs/DESIGN_DELTA.md` |

## Documentation Contract

| Artifact | Responsibility |
|---|---|
| README | Verified entry/status index; no duplicated rule or runtime history |
| Design | Architecture / contract / boundary baseline; do not overwrite history to match incidental code |
| Design Delta | Adopted differences, reasons, evidence, impact and rollback |
| Project Tree | Navigation / file responsibilities / related tests |
| System / Module document | Existing owning unit's implementation and handoff contract |
| Commit / PR | Chronological work report and exact verification evidence |

GPT app CHAT's development procedure is [Work Routine §6–§7](docs/G_ACE_WORKSPACE.md#6-development-routine). SERVER_AI follows [Rule #16](https://github.com/G-ACE-inc/server-core/issues/16), the commissioned task and owning repository, using normal local tools. CHAT's ServerTerminal/Actions route, Notion, output conventions and per-turn loop are not SERVER_AI prerequisites. [GitHub work-report contract](docs/AUTO_COMMIT.md) owns Commit/Push/remote readback. Judge only the documentation affected by the change before completion:

```text
README_UPDATE_REQUIRED=YES/NO
PROJECT_TREE_UPDATE_REQUIRED=YES/NO
DESIGN_DELTA_REQUIRED=YES/NO
SYSTEM_DOCUMENT_REQUIRED=YES/NO/UPDATE_EXISTING
```

Required documentation must be updated. Keep Source / Test / Commit / Push / PR / CI / Merge / Deploy / Runtime / Production separate; UNKNOWN / NOT_EXECUTED / NOT_VERIFIED must not become PASS by inference.

## Execution and evidence

The supplied-receipt CHAT gate and existing CI enforce only their actual admission/check surfaces. They do not intercept ordinary ChatGPT answers, prove live rule loading or qualify client performance. Current Source/CI/behavioral evidence belongs in [CU #40](https://github.com/G-ACE-inc/server-core/issues/40); implementation entrypoints and tests are indexed in [STRUCTURE](docs/STRUCTURE.md). Optional scoped Current recovery is in [LOAD_SCOPE](docs/LOAD_SCOPE.md).

Ordinary CHAT Host work uses the [common ServerTerminal route](docs/GITHUB_PROJECT_CHAT_HOST_ROUTE.md), including independent-request marker, exact request/Run/result correlation and actual admission. Preserve runtime-owned TGserver topic mappings during Source reflection. A directly commissioned SERVER_AI uses its verified local tools under #16.

Fresh native CHAT adoption requires real conversations and their own Current/request/Run/result evidence; see the [existing native CHAT test](docs/GITHUB_PROJECT_CHAT_HOST_ROUTE.md#通常chatの開始別chat実測手順). A server executor cannot manufacture those conversations. Incomplete ZERO index coverage cannot prove absence of client failures.

The common Receiver health checks Host Writer and Result Sink RPC reachability; sustained dependency loss triggers a bounded self-restart to refresh stale socket-directory mounts. Common CHAT Receiver and existing Gateway Tunnel residency/restart recovery are defined in [`compose.chat-host.yml`](compose.chat-host.yml); command-integrity and GPT-only delegation boundaries are in the [Host route](docs/GITHUB_PROJECT_CHAT_HOST_ROUTE.md) and Work Routine §6.

## Runtime and approval boundaries

[SERVER_CORE_PROTOCOL](SERVER_CORE_PROTOCOL.md) owns shared authorization; Rule #16 owns SERVER_AI execution and Work Routine §6 owns GPT CHAT progression. Master selects the lead AI/external executor; configured in-client subagents are available within the selected task and existing model/cost settings. Routine approved technical work does not acquire a new Master gate merely because it is a merge or restart. Protected intent, irreversible data, Secret/provider/public effects and explicit Current gates still require their actual authority. Never forge a receipt, widen Host access or infer delegation from Project membership.

Production residency remains Docker / Docker Compose. Use [DEPLOY_RUNBOOK](docs/DEPLOY_RUNBOOK.md) for source-to-runtime reflection, exact readback and rollback, and [STORAGE_LIFECYCLE](docs/STORAGE_LIFECYCLE.md) for log/cache/backup/cleanup. A README, registry entry or old CI/run is not current Host/container evidence.

Shared capability discovery belongs to [WORKSPACE_REGISTRY](docs/WORKSPACE_REGISTRY.md). **Project Integration:** TGserver / webhook gateway use [PROJECT_INTEGRATION_RULES](docs/PROJECT_INTEGRATION_RULES.md); Vault follows the [shared Secret contract](docs/WORKSPACE_SHARED_SECRETS.md). Do not read or store Secret values as development context.

Master Internal/Standing delegation uses the existing [repository registry](operations/master-internal-repositories.json), [common Host contract](operations/github-project-bounded-host.json) and [MCP contract](docs/WORKSPACE_MCP.md); product validation remains in [DebugAI #41](https://github.com/seigo-gace/debug-ai/issues/41). Scope, owner, exact Source and trusted Host admission/readback must match on each operation. No automatic grant to other repositories or commercial/customer paths. Historical proof stays in [WORKSPACE_MCP](docs/WORKSPACE_MCP.md#master-internal-persistent-delegation-runtime-verified-2026-10-08) and the owning Issue/run history; old SHAs/test counts are not live status.
