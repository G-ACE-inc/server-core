# SHARED SERVER EXECUTOR

Version: 2026-10-07  
Role: CHAT / DebugAI / server-side AIが同じ安全境界でVPS上の限定操作を実行するためのWorkspace共通executor contract。

## Purpose

DebugAIで既にLive dogfood済みの bounded Server Command / Host runner patternを、DebugAI固有実装として増殖させずserver-coreのShared Control capabilityへ共通化する。

```text
Parent AI / CHAT
  -> existing DebugAI MCP / workflow adapter
  -> shared server-command request
  -> durable queue
  -> one-shot Host runner
  -> allowlisted VPS operation
  -> status / exact readback
  -> RuntimeEvidence / TGserver where applicable
  -> parent AI
```

server-coreは共通executor contractとHost-side routingを所有する。DebugAIはspecialized consumerであり、DebugAI分析workflow・patch logicはserver-coreへ移さない。

## Reuse authority

Reuse source:
- repository: `seigo-gace/debug-ai`
- live evidence revision: `efe1de7c5b3108f7b64843bb814f7d5710e3e28c`
- proven files:
  - `server/control/server-command-request.js`
  - `scripts/host-server-command-runner.sh`
  - `ops/systemd-user/debugai-server-command.path`
  - `ops/systemd-user/debugai-server-command.service`

The proven live baseline used:
- fixed command IDs;
- no arbitrary shell;
- durable request/status files;
- 60s request expiry;
- single-writer lock;
- bounded output;
- one-shot Host runner;
- exact status/readback.

Current DebugAI source has additional product-specific commands and direct MCP surfaces. Those are not copied into the shared baseline merely because they exist.

## Shared contract

Machine contract:
`operations/server-command.json`

Queue client:
`scripts/server_command_request.py`

Host runner:
`scripts/host-server-command-runner.sh`

Watcher:
- `ops/systemd-user/gace-server-command.path`
- `ops/systemd-user/gace-server-command.service`

Current shared command allowlist:

```text
workspace.pwd
workspace.git_head
```

Current target allowlist:

```text
server-core
debug-ai
```

Requesters submit only `command_id` and `target_id`. They cannot submit:
- shell source;
- executable name;
- command arguments;
- arbitrary filesystem path;
- arbitrary environment variables;
- timeout overrides.

## Request / status lifecycle

```text
request
 -> requests/cmd_*.json
 -> systemd .path wakes oneshot runner
 -> processing/cmd_*.json
 -> PASS -> status/cmd_*.json + done/
 -> FAIL -> status/cmd_*.json + failed/
```

The runner processes at most the contract-defined batch size and uses one lock directory to preserve single-writer behavior.

Expired or malformed requests fail closed.

## Responsibility boundary

server-core owns:
- shared schema;
- command/target allowlists;
- queue lifecycle;
- Host runner;
- systemd watcher contract;
- approval classification when mutating operations are added later;
- Workspace-wide exact readback semantics.

DebugAI owns:
- debugging workflow;
- AI roles;
- patch candidate generation;
- verification/re-fix logic;
- its MCP/product adapter.

The Internal Event API / Webhook Gateway may still be used for events/logging where appropriate. It is not the primary server executor.

## Current source scope

This first shared extraction intentionally keeps the Live-proven minimal read-only surface.

```text
ARBITRARY_SHELL=NO
ARBITRARY_PATH=NO
PERSISTENT_MUTATION=NO
READ_ONLY_COMMANDS=2
TARGETS=2
HOST_RUNNER_SOURCE=IMPLEMENTED
SYSTEMD_SOURCE=IMPLEMENTED
RUNTIME_REFLECTION=NOT_RUN
DEBUGAI_ADAPTER_SWITCH=NOT_RUN
CHAT_DIRECT_E2E=NOT_RUN
```

## Migration sequence

1. Source/CI prove the shared executor contract in server-core.
2. Reflect the shared queue/runner/watcher to VPS after explicit runtime approval.
3. Verify exact readback for `workspace.pwd` and `workspace.git_head`.
4. Change the existing DebugAI MCP/workflow adapter to submit to the shared server-core queue instead of the DebugAI-local queue.
5. Prove DebugAI read-only E2E through the shared executor.
6. Expose the same bounded capability to GPT CHAT through the existing approved MCP/connector route.
7. Only after repeated evidence, add further allowlisted operations.
8. Persistent/destructive/deploy operations remain separately approval-gated.

Do not delete the DebugAI-local path until shared E2E is proven and rollback evidence exists.

## Approval boundary

Source/Test/Docs/PR/CI may proceed within Issue #10.

The following remain separate approval/runtime gates:
- systemd install/enable;
- live queue path creation if persistent runtime state is changed;
- service restart/recreate;
- DebugAI runtime adapter reflection;
- deploy;
- persistent/destructive server mutation;
- Secret/Provider changes;
- main merge.
