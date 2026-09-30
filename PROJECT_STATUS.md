# SERVER / PROJECT STATUS ENTRY

Role: Current状態を断定する一覧ではなく、Workspace内ProjectとRuntime確認先への入口。

最終実Runtime一括確認: NOT_VERIFIED_IN_THIS_CHANGE

この文書のPathやRepository記載はDiscovery用。Container / Port / Domain / Deploy / Provider状態は必要時に実readbackする。

作業履歴は記載しない。作業履歴の正本はGitHub commit / PR。

## Server Core
- Repository: `G-ACE-inc/server-core`
- Server path: `/home/admin1/server-core`
- Role: G-ACE Workspace共通開発・運用Authority
- Entry: `README.md` -> `docs/LOAD_SCOPE.md`
- Design: `docs/SERVER_CORE_DESIGN.md`
- Structure: `docs/STRUCTURE.md`
- Shared capability discovery: `docs/WORKSPACE_REGISTRY.md`

## Workspace
- Standard Workspace: `/home/admin1/workspace/G-ACE.code-workspace`
- Normal folders: `/home/admin1/server-core`, `/home/admin1/projects`
- Excluded from normal Workspace context: `/home/admin1/logs`, `/home/admin1/backups`, `/home/admin1/kb`, `/home/admin1/workspace`
- Authority: `docs/G_ACE_WORKSPACE.md`

## Project Entries

### TGserver
- Entry path: `/home/admin1/projects/TGserver`
- Current Source / Runtime: verify from TGserver README, Git state, Docker/runtime readback
- Do not reuse old container/runtime claims from this file as Current evidence

### Astera v8
- Entry path: `/home/admin1/projects/astera_v8`
- Current Source / Runtime: verify from Astera v8 README, Git state, Docker/runtime readback
- Project-specific Design / API / runtime details remain in Astera v8 repository

### Astera App
- Entry path: `/home/admin1/projects/astera-app`
- Current Source / Runtime: verify from App README, Git state, Provider/runtime readback

### DebugAI
- Repository authority: `seigo-gace/debug-ai`
- Runtime: independent from server-core
- Verified shared interface recorded by server-core: CLI / HTTP
- MCP: `NOT_IMPLEMENTED` until DebugAI implementation + runtime verification + Workspace registration complete

## Shared Platform

Discovery authority: `docs/WORKSPACE_REGISTRY.md`

Current documented categories:
- Project entries
- MCP
- Tool / Skill
- Shared Secret contracts
- KB bridge target
- Runtime registry rules

Registry is not Runtime Evidence.

## Reusable Development KB
- Target storage: Master PC `F:` 1 TB drive
- Runtime / Bridge: `NOT_IMPLEMENTED`
- Design authority: `docs/KB_REUSE_DESIGN.md`
- server-core stores only access / registration / lifecycle / safety contract, not KB data

## Log / Cache / Cleanup
- Common design authority: `docs/STORAGE_LIFECYCLE.md`
- Telegram / Meilisearch / Redis / `/home/admin1/logs` roles are ownership contracts, not proof of Current health
- Current capacity, retention, Docker log rotation and cleanup state require actual Server readback before reporting

## Deploy
- Authority: `docs/DEPLOY_RUNBOOK.md`
- Required route: confirmed GitHub revision -> required Master approval -> Server deploy -> Runtime verification
- Current Server deployment state for any Project: verify from that Project/runtime; do not infer from GitHub

## Current-state Readback Rule

When a task needs Current runtime facts, inspect only the relevant target and record evidence such as:
- repository / branch / HEAD
- Docker compose/service/container
- port / domain ownership
- endpoint / health result
- Provider resource state
- timestamp / revision

If not checked, report `UNKNOWN / NOT_VERIFIED / NOT_EXECUTED` rather than carrying forward old values.
