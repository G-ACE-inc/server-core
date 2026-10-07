# G-ACE SERVER_AI Minimal Kernel

Use `SERVER_AI` profile.

Bootstrap:
- `README.md`
- `docs/LOAD_SCOPE.md`
- `operations/github-project-rule-plane.json`
- canonical rule item #16 / GitHub Project #1 Current when available
- target repository Current + minimum required source/test

Do not default-load GPT_CHAT rule item #17 or full historical Notion rules.

Prefer existing evidence, deterministic checks, focused tests, and AVAILABLE_VERIFIED shared tools before additional AI reasoning.

Never guess Current state. Keep SOURCE/CI/RUNTIME/MERGE/DEPLOY separate, preserve approval boundaries, never expose Secret values, and keep Project implementation in its owning repository.

server-core is the Workspace bootstrap/router/control room, not the owner of every Project implementation or every AI-specific rule payload.
