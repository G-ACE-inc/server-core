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

## One owner per file type — no more rule copies

This is the **existing** responsibility map, not a new control plane. On any rule change identify the *owner below* and update that owner first; entrypoint adapters only link to it. A capability config or a history report is **not** an independent Rule authority.

| Place | Owns (may change here) | Must only reference / must not own |
|---|---|---|
| **GitHub Project #1 + owning Current Issue** | Mutable Mission, priority, Scope, CU, Mutation Owner, Gate, acceptance, exact next action and progress | Shared server policy, code and runtime facts |
| **Project control #15** | Migration/cutover state and evidence, not every project task | Common Work Routine implementation |
| **Rule #16 SERVER_AI** | SERVER_AI-only execution/dispatch profile and minimum context | Full shared server operating rules; GPT CHAT orchestration |
| **Rule #17 GPT_CHAT** | GPT CHAT-only orchestration, included-cost preferences, delegation, nontechnical Master decision interface | Copies of shared server/Host/Workspace rules |
| **`SERVER_CORE_PROTOCOL.md`** | Stable common safety, permissions and operation boundaries | Live approval receipts or changing Current |
| **`docs/G_ACE_WORKSPACE.md` §6, §4.1** | Stable shared Work Routine and canonical-parent workspace location rules | A second GPT_CHAT/SERVER_AI-specific full policy |
| **`docs/LOAD_SCOPE.md`** | Small conditional reading / Project and tool Authority dispatch | Entire repeated rule bodies |
| **`docs/WORKSPACE_REGISTRY.md`, `operations/*`** | Registered Project/capability identity and versioned tool/execution contracts | Historic E2E as live runtime authorization |
| **`docs/WORKSPACE_MCP.md`** | MCP install/use contract; archived prior verification kept below active contract | Tool implementation, current Host health |
| **`README.md`** | Index into server-core roles and required startup pointers | Duplicated live status or bulk Rule Plane |
| **`AGENTS.md`, `.cursor/rules/*.mdc`, `.github/copilot-instructions.md`** | Vendor-specific **short adapters** selecting profile, Current and server-core owner | Competing common Rules, Project Mission, stale hard-coded build instructions |
| **`.cursor/agents/*.md`, User Global Cursor rules, `.cursor/mcp.json`** | Agent/model definitions, UI/session defaults, provider connection settings | A new G-ACE common safety or task authority |
| **`.github/workflows/*` and existing bounded Host/DebugAI runner** | CI/regression and actual authorized machine action/readback | Product intention or broader self-granted permission |
| **Owning Repository** | Product code, local constraints, design, tests, Source/CI evidence | Global shared rules; another Project's Current |
| **TGserver, Host, deployed containers** | Logs and actual runtime evidence | Project Current, Rule source, inferred deployment from CI alone |

**Precedence by responsibility:** Master product intention and actual platform/tool authorization are not editable through an Agent instruction. For development operations, read the relevant GitHub Current, then the shared server-core owner for common invariants, then **one** executor profile (#16 or #17), then task-specific repo guidance. A genuine local product rule supplements common safety; it never promotes an old stage-specific mission over verified Current. Resolve conflicts at the owning source, **not** by adding a contradictory override in another `.mdc`/Issue. Before removing old text, confirm consumers and CI, preserve its history and validate the effective client/Host behavior.

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

## Shared Work Routine ownership and scope-drift gate

The only **stable common Work Routine** is [`docs/G_ACE_WORKSPACE.md` §6](G_ACE_WORKSPACE.md#6-development-routine), including its Mission/CU pre-dispatch requirements. Do **not** copy a second full routine into Issue #16, Issue #17, per-agent `AGENTS.md`, Cursor `.mdc`, or Copilot instructions. Each executor fetches the same owning GitHub Project/Issue Current but **only its own** minimal SERVER_AI #16 or GPT CHAT #17 profile.

Use existing Project Control fields `Wave / Gate / Change Unit / Mutation Owner`. `MISSION / IN_SCOPE / OUT_OF_SCOPE / ACCEPTANCE / EXACT_NEXT_GATE` stay in the **owning canonical Current Issue**, until genuine Project field registration and readback explicitly prove otherwise. Before dispatch verify actual task ownership and whether the planned diff/effect is within the current CU; deny only out-of-scope mutations. Recording a current reference or passing a source-file test is not evidence that Cursor/Codex/GPT actually loaded it or that the bounded Host runner enforced it; those require their own runtime/readback proofs.

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
