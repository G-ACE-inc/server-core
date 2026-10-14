# Shared Server Terminal — ordinary shell command recipes

The **only normal GPT CHAT execution entrypoint** is the existing common `host.command` via GitHub Actions → Gateway → current Host receiver/writer. This document is a convenience list of shell snippets, **not** a registered-command menu, new permission system, API, Workflow, or separate executor. GPT CHAT selects/constructs the command, retrieves the current Host and repository SHA and checks the result itself. Master is not asked to approve or edit the commands.

| Task | Ordinary command example (inside the registered repository checkout) |
| --- | --- |
| Current checkout | `pwd && git rev-parse HEAD && git status --short` |
| Recent history | `git log -5 --oneline` |
| Current changes | `git diff --stat && git diff --cached --stat` |
| Inspect a file | `sed -n '1,160p' README.md` |
| Test | `python3 -m unittest discover -s tests` (adapt to the owner's test runner) |
| Docker logs | `docker logs --tail 100 --timestamps SERVICE_CONTAINER` (substitute actual verified container name in the AI-authored command) |
| Docker service status | `docker compose ps` (after confirming the repository's compose project) |
| Update checkout | `git fetch origin main && git merge --ff-only origin/main` after checking branch, worktree and current owners |

No literal placeholder is ever sent to the Host; these are **recipes** for the assistant, not copy/paste instructions for Master. Arbitrary mutating commands must be deliberately composed and verified, not blindly retried following an ambiguous result. Existing GitHub Project repository identity, exact SHA and Request-ID deduplication remain intrinsic to the current Terminal, not old DebugAI `MASTER_INTERNAL_PERSISTENT` menu grants.

Retired ordinary-CHAT paths: DebugAI `/v1/gitops/request`, `/v1/runs/start`, `/v1/status`, `/v1/inspect`, DebugAI Server Command readback, and fixed-menu selection in `.github/workflows/chatgpt-live-api-verify.yml`. Specialized DebugAI **product** APIs and unrelated product repos are separate and are not removed by retiring the ordinary CHAT executor.
