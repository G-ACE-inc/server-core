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

## Responsibility boundary — Current vs common operation (Master clarification 2026-10-09)

**Do not create a second authority, another Work Routine, or another AI rule file.** The ownership of a question is determined by its subject, not merely by an apparent hierarchy between GitHub Project and server-core.

| Decision / fact | Sole owning authority | Other surfaces must do |
|---|---|---|
| Mission, priority, current CU, mutation owner, gate, acceptance, next action | GitHub Project #1 + owning Current Issue | Resolve/read the current item, never keep a parallel current task plan |
| GPT CHAT orchestration, tool-routing preference and reporting behavior | GPT CHAT Issue #17 | Entry adapters reference #17 only for GPT CHAT |
| SERVER_AI / Composer / Codex executor-specific minimum behavior | SERVER_AI Issue #16 | Entry adapters reference #16; never load #17 by default |
| Common development Work Routine and documentation/verification sequence | `docs/G_ACE_WORKSPACE.md` §6 and §7 | Project Current selects which CU; agents execute the common method without copying it |
| Common Host, Docker/Compose, workspace location, GitOps and security/authorization contracts | `SERVER_CORE_PROTOCOL.md`, `docs/G_ACE_WORKSPACE.md`, `docs/DEPLOY_RUNBOOK.md` and registered operations contracts | Project intent cannot grant Runtime permission or override verified Host denial |
| Capability discovery, canonical parent identity and registered connection contracts | `docs/WORKSPACE_REGISTRY.md` + authorized `operations/*` | The real Host/provider status requires independent readback |
| Source, implementation details, tests, package/runtime integration | Owning Project repository | server-core routes; it does not absorb Product implementation |
| Actual container state, Git deployed HEAD, logs, resource consumption | Owning Runtime/Host evidence | Historical issue notes or passing CI never substitute for live status |

If two records contradict each other, **inspect what they each own**. Project Current supersedes an older server-core *task plan*, but cannot waive server-core's common safety/permission contract. A newer server-core instruction cannot silently rewrite the owning Project's active CU. Resolve actual same-owner conflicts at that owner and record the discrepancy.

### Automation / mechanical enforcement policy

Use the **existing** Work Routine, GitHub Project Control, CI, registries, bounded DebugAI command/GitOps and workspace/shell guards first. Do not add a new general-purpose orchestrator or duplicated rule plane.

| Candidate check | Mechanism / appropriate boundary | Status and limit |
|---|---|---|
| Current issue / exact source branch and SHA / CU owner before mutation | Existing Project fields + exact GitHub/Host admission | Enforce in approved execution routes; issue prose alone is not admission |
| One mutation owner and preconditioned file updates | Existing GitHub SHA compare-and-swap, PR/branch checks and Host admitted scope | Automate conflict refusal when identifiable; parallel agents are not themselves prohibited |
| Reuse registered parent, deny new sibling project and path traversal | Registry + initializer/known shell Hook and CI negative tests | Coverage is per intercepted entrypoint; never claim Codex/SSH/global shell protection without runtime evidence |
| Source/test/CI/merge/deploy/runtime phase separation | Existing CI and signed/bounded Runtime readback | CI can verify Source/tests; only actual Host evidence verifies Runtime |
| Authorized Docker/Compose deployment, changed path/owner/branch/SHA/effects | Existing guarded GitOps + registry/Host admission | Deny unregistered protected effects; never turn a README assertion into credentials |
| Required tests, basic file structure, known rule bootstrap targets | Existing repository-specific CI | Enforce deterministically where safe; choose task-specific tests rather than global expensive full suites |
| Documentation Gate / reusable asset check | Existing Work Routine and targeted CI where machine-verifiable | Human judgment for design rationale and product suitability; do not reject merely for lack of arbitrary keywords |
| Every AI actually loaded the correct Current Rule; actual Host health | New-session client evidence / direct runtime query | Cannot be proven by repository text or CI alone; retain NOT_VERIFIED until observed |
| Current server CPU/RAM/Disk/OS/containers | Actual Host inventory and monitored state | Stable specs may be registered, but utilization/status must be measured fresh; do not hard-code stale values |

**Automate only a deterministic invariant with an actual enforcement hook, known input contract, bounded permissions, useful negative tests and no undue interruption to normal work.** Otherwise keep it as a documented review/readback gate. Machine denial applies to the unsafe operation, not unrelated safe work. Preserve ownership, rollback paths and history; do not silently relax Master-owned approval or expand DebugAI's enrollment to other repos.

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
