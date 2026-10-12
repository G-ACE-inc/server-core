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

GPT CHAT / ChatGPT Work coordinatorはFresh main ManifestでGPT_CHAT Profileを確定し、Issue #17の本文全体を欠落・途中切断なしで読んでからGitHub Project #1 / owning Current / 固定目的を確認する。以後はRule変更分とCurrent差分だけ再取得し、Workspace/server controlが必要なTaskだけserver-coreを読む。Issue・CIの記述だけで実CHATのルール適用を証明したと扱わない。
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

### One owner per file type — adapter clarification

The normative assignment remains the **Responsibility boundary — Current vs common operation** table immediately above. Project control #15 records migration evidence, not changing Project task status. `docs/LOAD_SCOPE.md` dispatches conditional reads; `docs/WORKSPACE_MCP.md` keeps connection contracts and archived verification; `README.md` is only an index. `AGENTS.md`, `.cursor/rules/*.mdc`, `.github/copilot-instructions.md` are short client adapters. `.cursor/agents/*.md`, User Global Cursor rules and `.cursor/mcp.json` configure clients, not common rules. `.github/workflows/*`, existing bounded Host/DebugAI and TGserver enforce or record actual effects and evidence. No second rule authority is created. Rule #16 SERVER_AI and Rule #17 GPT_CHAT own only their respective execution profiles; GitHub Project #1 + owning Current Issue owns mutable Mission/CU.

## Shared Work Routine ownership and scope-drift gate

The only **stable common Work Routine** is [`docs/G_ACE_WORKSPACE.md` §6](G_ACE_WORKSPACE.md#6-development-routine), including its Mission/CU pre-dispatch requirements. Do **not** copy a second full routine into Issue #16, Issue #17, per-agent `AGENTS.md`, Cursor `.mdc`, or Copilot instructions. Each executor fetches the same owning GitHub Project/Issue Current but **only its own** minimal SERVER_AI #16 or GPT CHAT #17 profile.

Use existing Project Control fields `Wave / Gate / Change Unit / Mutation Owner`. `MISSION / IN_SCOPE / OUT_OF_SCOPE / ACCEPTANCE / EXACT_NEXT_GATE` stay in the **owning canonical Current Issue**, until genuine Project field registration and readback explicitly prove otherwise. Before dispatch verify actual task ownership and whether the planned diff/effect is within the current CU; deny only out-of-scope mutations. Recording a current reference or passing a source-file test is not evidence that Cursor/Codex/GPT actually loaded it or that the bounded Host runner enforced it; those require their own runtime/readback proofs.

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

## Consumer inventory — evidence and loading boundaries

This register distinguishes an **entrypoint source** from an **effective runtime consumer**. It is not a new Router or an assertion that a local editor fetched the GitHub issue. Verify the specific owning repository, commit and installed client configuration before retiring a duplicate rule.

| Consumer | Intended source / only owner | Current evidence boundary | Next proof required |
|---|---|---|---|
| GPT CHAT | Manifest -> Issue #17 -> Project/owning Issue Current; conditional server-core shared contract | GitHub connector can explicitly read manifest and #17; automatic per-turn integration is NOT_VERIFIED | Fresh issue/Current loading on a new CHAT turn, with version/readback |
| SERVER_AI / delegated Host worker | README -> LOAD_SCOPE -> manifest -> Issue #16 -> owning Current -> conditional server-core | Source routing documented; Host-local automatic load is NOT_VERIFIED | Exact Host source/config and real session load trace, excluding #17 |
| Cursor Composer | User Global + workspace `.cursor/rules/*.mdc`, selecting SERVER_AI #16 | PR39 validates symlink or inactive-stub source contract; Composer-reported CU2 local changes are not independent live readback | Fresh Active Rules/Global precedence and exact installed file hashes |
| VS Code Codex | Repo `AGENTS.md`, any verified actual configuration, SERVER_AI #16 | Repository adapter source exists; effective issue fetch and applicable global config are NOT_VERIFIED | New-session loaded instruction trace for owning repo |
| GitHub Copilot | Repo `.github/copilot-instructions.md`, SERVER_AI #16 | Repository adapter source exists; actual current-issue injection is NOT_VERIFIED | Effective client/session instruction readback |
| GitHub Actions / Project Control | Existing `.github/workflows/*`, `operations/github-project-control.json`, owning GitHub Current | Four fields only: Wave, Gate, Change Unit, Mutation Owner; CI does not attest Mission match at Host | Exact-SHA checks plus authorized/denied dispatch tests on owner-controlled route |
| Host / DebugAI runner | Existing bounded Host admission, registry and verified running revision | PR39 Source CI is not Host reflection; PR36/#37 are separate mutation owners | Pinned runtime rule version, wrong-CU denial and allowed nested-worktree proof |

**Safe migration gate:** collect actual consumer readback first; identify a single owner for each shared invariant, preserve client-specific adapters and legacy compatibility, then remove a duplicate only after focused regression and actual-loader proof. A missing Host/client proof is `NOT_VERIFIED`, never implicit approval to rewrite another owner's Global file or Host branch. Project item registration and formal Notion cutover remain separate gates.


## Master client acceptance — ChatGPT-first, concurrent project continuity (2026-10-12 proposed design)

**Origin and status:** Independent architecture review of [Notion GPT CHAT r18](https://app.notion.com/p/3aecdcf128e481e0ada5dfbb2c5ae93d), [control #15](https://github.com/G-ACE-inc/server-core/issues/15), [Rule #17](https://github.com/G-ACE-inc/server-core/issues/17), [owning work-routine §6](G_ACE_WORKSPACE.md#6-development-routine), and observed [CHAT regression #40](https://github.com/G-ACE-inc/server-core/issues/40). This section defines **proposed product-level acceptance criteria and evidence boundaries** for improving the existing system. It is not an additional Rule Plane, a new Work Routine, a new mutation authorization, or a declaration of operational completion. Existing owner Current and approved implementation/change boundaries still control actual changes.

### Client operating model (non-negotiable acceptance context)

- Master is a nontechnical client and product/acceptance authority; do not require Master to select commands, code changes, SHAs, branches, test strategies, CI repairs or deployment implementation. Ask for genuine product-result choices or protected irreversible external effects only. If an unavoidable Master command is required, provide a validated, immediately executable complete command and its expected return evidence.
- Ordinary ChatGPT app CHAT is the **primary design, investigation, planning, GitHub dispatch, evidence interpretation, debugging and orchestration interface**; GitHub Project + owning Issues are the shared Current/control plane and registered repository Source/CI/Host remain the authority for actual state. Cursor, Codex, Composer and Server AI are bounded workers, not competing independent planners.
- Support **up to eight concurrently active Projects** under separate owning Current/CU/writer boundaries. This is a capacity goal, **not** permission for eight simultaneous conflicting mutations, unregistered repositories, extra paid providers or automatic background CHAT execution. Existing approved isolation inside parent projects remains allowed.
- Optimize for the user's included ChatGPT application capacity and verified low-cost execution. Avoid repeated Master shell work, repeated full rules, unnecessary provider calls, duplicated agent research and branch/worktree/project proliferation. Do not represent ChatGPT Plus usage as unlimited or promise autonomous background tool use where no scheduler/worker is actually deployed.
- Meaning of **minimal**: preserve all required features, safety, design fidelity and verification while removing unnecessary handoffs, repeated checks, duplicate authorities and terminal explanations.

### Responsibility-to-effect matrix — distinguish document from execution

| Capability | Existing source/owner | Execution/verification boundary | Acceptance evidence |
|---|---|---|---|
| Stable mission, Master latest intent, project isolation | Project #1 + owning Issue Current | Existing authenticated Project/Host admissions, checked against purpose/CU/owner/effects | Real correct-CU allow + wrong-CU/wrong-scope deny; per-project Current readback |
| GPT CHAT behavior and formal report triggers | #17 (refer to §§5–7) | Actual active CHAT session actions; no known built-in answer pre-send hook | Independent transcript showing progress explanation **followed by** same-turn work and only legitimate STOP |
| Shared development loop | Workspace §6 (single owner) | Existing executor/CI/Host steps, preserving precise scope | Evidence chain of analyze → design/reuse → patch → focused test → failure repair → CI → optional Host readback |
| Effective rules, adapted per surface | Manifest + #16/#17 + thin adapters | Actual new-session client load; code/static CI only proves stored configuration | Per-surface applied version and behavior; UNKNOWN if not observable |
| Safe source/deploy operation | Owning repo + authorized Host/Registry | Path/branch/SHA/effect admission; exact source and runtime checks | Allow/deny tests, exact SHA, deployed revision and runtime evidence as applicable |
| Long-session/CHAT handoff and parallel continuity | Existing Current Issue, Project fields, retained Dev Log evidence | Resume by fresh readback, not by chat recollection | One CHAT changeover resumes the actual next undone action, no duplicate PR/mutation |
| Multi-project cost and progress | Existing Project Current + per-owner events/CI | Independent owner queues with bounded external workers where they exist | Up to eight distinct Current records recoverable; no global stop caused by one project's failure |

### Cohesive CU execution contract (implementation target, not a second routine)

Keep the six existing Workspace §6 stages. **Do not add another workflow merely to express them.** Their runtime semantics must be:

1. Resolve a single owning Mission/CU and actual next incomplete acceptance gate from fresh Current and Design; determine the safe executable work set and a single writer before action.
2. Execute the largest **coherent and safe** CU segment that tools/capacity permit; create a branch/commit/PR only when justified by isolation/review/recovery needs, not for every file, explanation, test or chat reply.
3. After any failure, mark the **failed operation** and its dependency scope, collect direct evidence, replan and execute another legal same-CU action. Authentication refusal must never be bypassed and an unverified step must never be counted PASS.
4. Treat commit, passing CI, Issue record, and intermediate explanations as **checkpoints**, not completion. Continue legal and independent same-CU work before concluding the response; no unowned switch to a neighboring project.
5. Persist a compact validated current state at durable checkpoints: canonical purpose; latest Master intent; owning project/CU/writer; adopted design/revision; last verified Source/CI/Host status; pending external run ID; preservation constraints; exact unfinished action and its dependencies. Store it in the **existing** owning Current; do not create a parallel tracker or copy raw logs into policy.
6. Finish only upon demonstrable CU acceptance, explicit Master stop/report, a proven Master-only input/decision or genuinely exhausted authorized work; do not misclassify tool failure, provider quota, CI wait or missing GPT app answer interceptor as a global blocker.

### Acceptance trials before migration cutover

Maintain **three separate verification planes** without conflating PASS:

**A — stored design/source:** Existing owner contracts have one normative home; Notion r18 eight chapters are mapped meaning-for-meaning; static tests and CI pass for an exact SHA; safety/permission/one-writer/parent containment are not weakened.

**B — effective executable route:** New active CHAT and delegated executor actually load intended source/current version; GitHub Project control admission protects wrong owner/CU; eligible GitHub→Actions→Host path returns job/run/readback evidence. Do not infer project-wide Host enrollment from the DebugAI-only route.

**C — client-observed continuity:** (i) one live CHAT continues tool work after an explanatory checkpoint, (ii) an injected test failure yields evidence→replan→further legal action, (iii) passing CI does not end an unfinished CU, (iv) a new CHAT restores actual Current and does not redo completed steps, (v) two isolated project CUs progress without cross-owner mutation, (vi) recovery records permit up to eight distinct Project contexts without conflation, (vii) real completion or real Master-only boundary produces correct nontechnical report. Record an actual failed trial as FAIL, not a documentary PASS.

**Cost/continuity measurements:** per CU count user interventions, avoidable CHAT stop events, real action transitions after intermediate explanations, repeated full-policy reads, duplicate research/PRs, and provider paid/free quota consumption. Capture baseline and post-change samples; values not measured are UNKNOWN. Eight-project support must not imply eight simultaneously autonomous ChatGPT sessions or infinite context.

**Cutover:** Existing Manifest `migration.cutover=NOT_RUN` and `project_item_registration=NOT_VERIFIED` remain unchanged until actual Project registration, active consumer load, route admission and observed behavior meet the required proof. Notion continues as migration/history and decision context until then. Do not delete historical Notion pages or close #15 based on a document/CI-only success.


### Concrete migration and implementation allocation (client acceptance delta)

The table below is an **implementation backlog against existing owners**, not a new cross-project CU or authority. Each item needs its actual owning Current/branch check before any source mutation. A passing static rule test must not close these rows.

| Gap ID | Required user-visible change | Reuse/current implementation | Responsible change boundary | Exact trial / completion evidence |
|---|---|---|---|---|
| C01 | A development CHAT advances after an interim explanation instead of stopping | #17 §5–7; existing CU40 design and `github_project_chat_turn_gate.py` | Existing CU40 GPT_CHAT behavior owner; **not** #162 | Real same-turn tool action after interim explanation, with verified unfinished CU |
| C02 | Failure leads to diagnosis and useful action without asking Master for routine debugging | Workspace §6 ITERATE; #40 behavior matrix | Existing CU40, scoped to operator behavior | Failed action evidence, scoped replan, new authorized action and its result |
| C03 | A green PR/CI does not masquerade as Product/CU completion | GitHub checks + owning Issue acceptance + #17 stop contract | Existing CU40 and per-repo Current owner | Evidence of a post-CI legal next action, or evidence proving actual terminal condition |
| C04 | New CHAT recovers correct exact work without redoing completed fixes | Project #1 / canonical Issue; `EXECUTION_SNAPSHOT` contract | Existing Project Control / owning Project Current | Across two independent CHAT sessions, same CU/last SHA/next gate rehydrated and deduplicated |
| C05 | Eight projects are separately recoverable with no mutation collision | Existing four Project fields + per-project canonical Current | Project Control owner and each owning Project; no new Project fields without proof | Enumerate up to eight registered contexts, read exact next gate for each and reject cross-CU mutation |
| C06 | CHAT can request only eligible registered server actions and independently verify result | Current GitHub Actions transport / bounded Host consumer and registry | Existing #10 common-host capability owner, separate from DebugAI product owner | Authorized command allow, invalid repo/scope deny, exact request/Actions job/Host revision result |
| C07 | Master rarely needs to paste commands or select a technical fix | #17 decision authority and available tool routing | GPT CHAT operator + owner-specific task packets | Count Master interventions and validate any exceptional completed command, with an exact legitimate reason |
| C08 | Rule/Design changes do not multiply token, branch, project or model costs | Dual profile Manifest, LOAD_SCOPE, existing Work Routine §6 | Rule Plane #15/16/17 respective owners; per-consumer adapters | Track full-policy re-reads, client load evidence and duplicate research/branch work, before/after |
| C09 | Notion r18 meaning remains while GitHub becomes the working rule authority | Notion r18 §§1–8, #15 migration and existing adapters | #15 migration owner, not a new Notion copy | Requirements trace + actual selected consumer load + Project item registration and cutover readback |

**Order of execution:** C01–C03 first for the observed stop regression; C04 then validates real chat handoff; C06 closes the server command dependency without treating the temporary DebugAI product API as final common architecture; C05 validates multi-project separation; C07–C09 quantify reduced intervention/cost and conclude migration. Parallelize only across verified distinct mutation owners and branches. A client-observed failure in C01–C03 overrides any synthetic receipt PASS. Preserve current #10/DebugAI/TGserver owners and pause states instead of claiming this governance PR authorizes Host changes.

**Trial recording contract:** for each row, record `CASE_ID / PROJECT_CURRENT / OWNER / DESIGN_REV / SOURCE_SHA / ENTRY_SURFACE / BEFORE / ACTION / ACTUAL_RESULT / AFTER / STATUS / EVIDENCE_URL / NEXT_SAFE_ACTION` in the existing owning Issue. Do not turn this table into a second mutable Current; record `UNKNOWN` when the client behavior, installed loader or Host result is not observed.

**Baseline at proposal time:** C01–C03 have real failure observations under #40 and remain NOT_VERIFIED as recovered; C04–C09 are NOT_VERIFIED as full end-to-end outcomes. No invented elapsed-time, autonomy percentage, API quota or savings.
