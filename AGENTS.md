# G-ACE Workspace Agent Entry

Any AI agent operating in the G-ACE Workspace must use `/home/admin1/server-core` as the shared Command Center before project-specific work.

At the start of every new chat/task, even when Master does not repeat this instruction:

1. Read `/home/admin1/server-core/README.md`.
2. Read `/home/admin1/server-core/docs/LOAD_SCOPE.md`.
3. Read only the server-core Authority required for the task.
4. Identify the target Project and read its README.
5. Read only the required Project Design / Project Tree / Design Delta / System Document / Source / Test.
6. Recover current durable state from Project/Git/runtime evidence when needed; do not guess from temporary conversation state.
7. Follow `/home/admin1/server-core/docs/G_ACE_WORKSPACE.md` and applicable server-core Authority for the fixed development routine and approval boundaries.

The purpose is to let non-technical Master continue development without repeatedly deciding routine Server information, available resources, routing, development procedure, or verification procedure.

Do not replace G-ACE rules with generic software-development practice. Do not omit required workflow steps. Keep server-core read-only unless Master explicitly authorizes server-core mutation. Do not treat unverified work as complete.
