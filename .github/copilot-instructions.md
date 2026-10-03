# G-ACE Workspace Copilot Entry

GitHub Copilot / VS Code AI working in this repository or the G-ACE Workspace must treat `/home/admin1/server-core` as the shared Command Center before project-specific work.

At the start of a new chat/task, before project-specific implementation or debugging, read and apply in this order:

1. `/home/admin1/server-core/README.md`
2. `/home/admin1/server-core/docs/LOAD_SCOPE.md`
3. Only the server-core Authority required for the current task
4. The target Project README
5. Only the target Project Design / Project Tree / Design Delta / System Document / Source / Test required for the task

Do this even when Master does not repeat the instruction in the chat. Do not replace G-ACE rules with generic software-development practice, and do not skip required workflow steps.

The purpose is that non-technical Master does not need to repeatedly decide routine Server information, available resources, development procedure, verification procedure, or project routing. Derive these from server-core and the target Project Authority.

If the target Project or current state is unclear, use server-core routing/registry and durable Git/Project evidence to recover it. Do not guess from temporary chat/session state.

Keep server-core read-only unless Master explicitly authorizes server-core mutation. Keep owner/shared/provider repositories read-only unless their mutation is specifically required and authorized.

Follow the fixed G-ACE development routine from `docs/G_ACE_WORKSPACE.md` and the approval boundaries from `.cursor/rules/00_agent_runtime.mdc` / server-core Authority. Never treat unverified work as complete.
