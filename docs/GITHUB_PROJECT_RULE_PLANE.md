# GITHUB PROJECT DUAL RULE PLANE

Version: 2026-10-07
Authority contract: `operations/github-project-rule-plane.json`

## Purpose

GitHub Project #1をCurrent運用のControl Planeとし、実行主体ごとにRule payloadを分離する。

```text
GitHub Project #1
  ├─ #16 Server AI Minimal Kernel
  ├─ #17 GPT CHAT Orchestrator Kernel
  └─ Project / Change Unit Current

server-core = bootstrap / router / control room
```

## SERVER_AI

Canonical item: Issue #16.

対象はCursor / Codex / GitHub Copilot / server-side automation。
server-coreを自動入口にし、#16とProject Currentを読み、対象Repositoryの必要最小Contextだけを読む。
GPT CHAT用#17をdefault loadしない。

Cost順序:
1. 既存Verified Evidence / Current readback
2. deterministic command / static check / focused test
3. AVAILABLE_VERIFIEDなTool / MCP / DebugAI
4. server-side AI reasoning
5. 高コストAI escalation

## GPT_CHAT

Canonical item: Issue #17.

GPT CHATは#17 -> GitHub Project Currentを先に読み、Workspace/server controlが必要なTaskだけserver-coreを読む。
GPT CHAT拡張Ruleはserver AIの常時Contextへ複製しない。

## Authority ownership

```text
Changing work Current       -> GitHub Project #1
SERVER_AI rule Current      -> Issue #16
GPT_CHAT rule Current       -> Issue #17
Control-plane migration     -> Issue #15
Stable bootstrap/routing    -> server-core
Project implementation      -> owning repository
Source/CI evidence          -> owning repository / GitHub
Runtime state               -> actual runtime readback
Notion GPT-only principles  -> migration source/history until cutover
```

## Shared invariants

両Planeで共有するのはFresh Current、reuse-first、minimum context、状態分離、Approval Boundary、Secret安全、Docker Compose production residency、GitHub Work Reportなどの最小Invariantだけ。

## Parent Project containment (Master current 2026-10-09)

Both executor profiles share the **location invariant**, but maintain their own independent prompts:

- The server's top-level Project listing contains the registered **parent Projects**, not one derived child per Branch/PR/debug/agent.
- **Allowed:** GitHub branches, concurrent isolated linked Git worktrees and files *inside the verified existing parent Project root* (e.g. `/home/admin1/projects/debug-ai/.worktrees/cu-123/`). This is a normal technical choice, not a new Project requiring approval.
- **Forbidden:** `/home/admin1/projects/debug-ai-cu-123/` and any other top-level sibling checkout/worktree/clone of the same parent, including detours to other persistent roots. A real independently registered parent still remains valid.
- **Enforcement procedure:** before workspace-creating commands or delegating to Codex/Composer/SERVER_AI, identify current owner Repo, canonical host parent path, resolve actual destination without symlink/`..` escape, confirm nested containment, link to branch/CU/cleanup owner, and read back the resulting path. Unknown roots deny only the creation. Prevent nested worktrees from appearing as staged parent content.
- **Source authority:** SERVER_AI [#16](https://github.com/G-ACE-inc/server-core/issues/16), GPT CHAT [#17](https://github.com/G-ACE-inc/server-core/issues/17); Workspace details [§4.1](G_ACE_WORKSPACE.md). A Rule Plane edit proves governance/readback only, not an installed Host ACL or pre-execution interception.
- The separate CHAT conducting existing parent/child consolidation exclusively owns that **cleanup**; this rule must not rename/remove/move its current directories.

## Minimal-context decision routing

- SERVER_AI: use Issue #16 (MINIMAL) and the target Current. Read SERVER_CORE_PROTOCOL and the exact Master Internal registry entry only for approval/deploy/Host-routing decisions; never default-load Issue #17 or unrelated historical evidence.
- GPT_CHAT: use Issue #17 (EXTENDED) and relevant Project Current. Load this server-core control-room material only when Workspace/server capability, authorization or runtime governance is involved.
- Runtime capability: read the canonical `operations/master-internal-repositories.json` enrollment and the owning DebugAI Current/actual Host evidence only when necessary. Project membership alone never grants delegation.
- Delegate-specific status is evidence-bound: a verified DebugAI internal Host admission does not authorize another Repo, a commercial client, or this ChatGPT application's direct connector.
- If the same decision appears in older history or a stale PR, use verified Current and direct Source/Host evidence, preserving historical records instead of copying them into the working Rule payload. Record CONFLICT without silently changing Product/Scope/Gate.
- No Rule Plane cutover is asserted from this documentation update; existing migration checks remain required.

## Cutover

Notionからの移行完了はIssue作成だけでは成立しない。

```text
RULE_ITEMS_CREATED=YES
MACHINE_CONTRACT_IMPLEMENTED=required
SERVER_AI_BOOTSTRAP_ROUTING_VERIFIED=required
GPT_CHAT_LOADING_PATH_VERIFIED=required
PROJECT_ITEM_REGISTRATION_VERIFIED=required
CURRENT_READBACK_VERIFIED=required
NOTION_CUTOVER=after all required evidence
```

完了まではNotionをmigration source/historyとして保持し、削除しない。
