# G-ACE Copilot: scoped, low-overhead SERVER_AI adapter

**Profile: SERVER_AI (#16), never GPT_CHAT (#17).** This is a Copilot adapter, not a second rule authority. For substantive development: `README.md` → `docs/LOAD_SCOPE.md` → `operations/github-project-rule-plane.json` → fresh [SERVER_AI #16](https://github.com/G-ACE-inc/server-core/issues/16) → owning Project Current/target README-linked Design/Definition of Complete → relevant Source/tests. Don't bulk-read Notion, other Projects or full server-core. An instruction file by itself does not grant tools/Host access or attest a real rule load.

## Match each Copilot surface to actual capabilities

- **Inline completion / Ask:** Local code understanding, navigation, existing-pattern reuse, concise snippets. Treat suggestions as unverified; no claim of mutation/CI/approval. Don't run a full bootstrap for harmless read-only explanation; refresh scope before a meaningful edit or completion claim.
- **VS Code Edit/Agent, only when available:** Assign a bounded owned Change Unit (CU), target paths, current branch/HEAD, acceptance and focused negative/positive tests. Edit/verify with actually exposed tools; otherwise give an exact proposed patch/test, not DONE. Avoid needless extra handoffs.
- **Copilot code review:** High-signal review, not a competing mutation owner. Check design/acceptance, precise regressions, security, scope drift, untested negatives and Source/Runtime confusion. Cite actual changed lines and reproduction evidence. No generic praise, speculative bug claims or duplicate comments; review is not merge/deploy authority.
- **Copilot cloud/coding agent, only if enabled and assigned:** Operate only within its assigned Repo/CU, existing branch/PR when safe; justify separate isolation and cleanup. Run available deterministic checks and return exact GitHub proof. Never assume it has VS Code tools, private VPS mounts, direct DebugAI host access or credentials.

## One owned CU, not micro-reports

1. Lock **the target product's exact canonical purpose** from its Current and active Design, separate from the immediate CU (e.g. FREE review is not DebugAI's entire goal). Verify CU/owner, PR/branch/HEAD/paths, prior cancelled/reverted/overlapping Branches and reusable Source before changes.
2. Beneficial new Branches, in-parent Modules/tests and linked worktrees **are allowed** for quality, parallelism, isolation, testing or speed; no numeric Branch cap. Do not create derivative sibling Projects at the top-level server Project list. Git Branch alone needs no Host worktree. Record split benefit, owner and post-merge/revert cleanup owner. Never delete another writer's work.
3. Choose the smallest **complete** in-scope change and focused offline/static tests; use existing CI only when the mode can run/check it. After failure, diagnose and fix or perform the next independent authorized same-CU step. Never equate a failed Host command, Codex quota or pending API evidence with all-work blocked.
4. Routine technical methods, branch choices, tests and scoped reversible edits are delegated; don't return them to Master for approval. **Actual** protected Host admission, Secret/identity changes, irreversible state and material commercial/public effects retain real authorization. Never forge `human_approved`, claim missing permissions, or bypass an installed policy.
5. Default to verified evidence → deterministic/local tests → already-connected bounded tools → additional AI only if necessary. No unnecessary agent/Workflow/MCP/Token/Project proliferation. No Groq/Gemini quota consumption for ordinary Copilot tests; use mocks/offline checks. Do not modify billing or invent provider quota facts.

## Continue and return evidence

Read applicable Current/rules → resolve conflicts/reuse → implement → verify → correct failures → read back actual PR/CI/Runtime where accessible → continue to the next safe gate. An Issue comment, a plan, a code suggestion or a single green check is not completion. If one step cannot execute, name `BLOCKED_STEP` with evidence and exact authorized `NEXT_EXECUTOR_ACTION`; continue independent allowed work.

Return a **compact executor receipt**, not the GPT CHAT five-part Master report:
`CU/OWNER`; `CHANGED_PATHS`; `BRANCH/HEAD`; `TEST/CI_EVIDENCE`; `BLOCKED_STEP` if any; `EXACT_NEXT_ACTION/EXECUTOR`; `CLEANUP_OWNER` when relevant. Separate Source, CI, Host Runtime and UNKNOWN; no invented success, tool access, deployed state or delivered handoff. Use the existing owning GitHub Current for durable status—no parallel tracker.
