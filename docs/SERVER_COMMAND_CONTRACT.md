# SERVER COMMAND EXECUTION CONTRACT

Version: 2026-10-02
Role: Technical safety and evidence contract for Server-side operations that are executed outside the current assistant/client.

## 1. Purpose

This contract defines the **Server-operation technical boundary**: exact target resolution, shell/process safety, mutation classification, authorization scope, concurrency, exit-status handling, bounded diagnostics, interruption recovery and evidence promotion.

It does not grant mutation permission. Repository, Workspace, Provider, credential, runtime and production authorization are owned by their respective authorities.

## 2. Operator Interface Boundary

The Workspace top-level operating authority owns the GPT/operator interaction interface, including command presentation shape, current command-size budget, copy/paste formatting and the outer result-return format.

This server-core Document does **not** duplicate or override those interface values. It only defines what a technically valid Server operation must guarantee underneath that interface.

If the top-level operator-interface authority and this technical contract appear inconsistent, do not silently choose one. Classify `AUTHORITY_CONFLICT`, preserve the stronger safety boundary and resolve the ownership conflict before mutation.

## 3. Technical Pre-command Requirement

Before a Server operation is handed off, resolve the canonical Pre-execution Contract defined by `docs/G_ACE_WORKSPACE.md` / `operations/pre-execution-schema.json` and identify at minimum:

```text
TARGET_PROJECT
TARGET_REPOSITORY
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
NEXT_ACTION
EXECUTION_ROUTE
EXECUTION_CAPABILITY
EXECUTION_AUTHORIZATION
AUTHORIZATION_DOMAIN
AUTHORIZATION_SCOPE
MUTATION_CLASS
VERIFY_PATH
PRE_EXECUTION_COMPLETE
BLOCKER
```

A Server operation may proceed only when the exact target and its authorization boundary are known. Unknown path, branch, runtime identity, service identity, provider target or mutation authority must not be filled by assumption.

## 4. Shell / Process Safety

A command intended for an existing interactive terminal must not terminate or corrupt the parent shell as a side effect of fail-fast behavior.

Technical requirements:
- fail-fast state such as `set -e`, `set -u` and `pipefail` belongs inside an isolated child shell/process when the caller shell must remain usable;
- an `exit` used for workflow control must exit the isolated child process, not the operator's parent interactive shell;
- `cd` failure must not allow execution to continue in an unintended directory;
- unbounded interactive waits and unbounded `tail -f` style operations require an explicit timeout/cancellation boundary;
- pipeline success must represent the intended pipeline, not only the final process when earlier failure is material;
- the primary operation return code must be captured before later diagnostic output can overwrite `$?`.

Isolation may use `bash -lc '...'` when appropriate, but equivalent safe process isolation is valid. The technical requirement is parent-shell preservation and correct failure propagation, not a specific quoting style.

## 5. Mutation Classification

Do not label a workflow `READ_ONLY` merely because final state is restored.

Use these classes where relevant:

```text
READ_ONLY_INSPECTION
REVERSIBLE_LOCAL_MUTATION
REPOSITORY_MUTATION
WORKSPACE_CLIENT_MUTATION
RUNTIME_MUTATION
PROVIDER_MUTATION
CREDENTIAL_MUTATION
PRODUCTION_MUTATION
```

Examples:
- `git fetch`, temporary checkout/detach, or branch switching are `REVERSIBLE_LOCAL_MUTATION`, not pure read-only inspection;
- config/file writes are mutation even when later restored;
- a health/readback HTTP call is read-only only if the called operation itself has no mutation side effect.

## 6. Authorization Scope

An authorization state must be scoped to the current Task/change unit. Do not carry mutation permission forward merely because an earlier turn or adjacent Task allowed it.

When mutation is involved, evidence should identify as applicable:

```text
AUTHORIZATION_DOMAIN
AUTHORIZATION_SCOPE
AUTHORIZED_OPERATION
TARGET_IDENTITY
AUTHORIZATION_STATE
```

A new Task, target repository, provider resource, credential, runtime or production operation requires its own boundary evaluation.

## 7. Multi-task / Multi-worker Safety

Assume multiple Projects, agents or change units may be active concurrently.

Before a write/commit/runtime operation:
- identify the exact change unit;
- ensure unrelated uncommitted changes are not staged or overwritten;
- do not use repository-wide staging when intended-file ownership is not exclusive;
- refuse automatic commit when the intended diff cannot be separated from other work;
- serialize helpers that mutate the same Git index, client config or shared runtime state, or fail closed when another writer is active;
- avoid switching or resetting a shared checkout when another active task may depend on its current state;
- prefer read-only Git object/API inspection over working-tree switching when possible.

## 8. Exit Status / Partial Apply

A successful outer command must not hide a failed primary operation.

- preserve the primary operation's real return code;
- if multiple required operations run, record each material result or aggregate only after all required results are known;
- if an operation mutates state and a later required step fails, report `PARTIAL` unless rollback/recovery has been actually verified;
- do not call a multi-step workflow atomic unless the implementation actually provides transaction/rollback semantics;
- recovery instructions are not recovery evidence.

## 9. Output / Diagnostic Budget

Server-side commands and helpers should suppress or summarize unbounded output by default.

For inventories/logs:
- return counts, failing identifiers and bounded excerpts first;
- write large diagnostic output to a temporary file only when needed;
- expose only the bounded evidence needed for the acceptance decision;
- never hide a failure merely to keep output short;
- never print Secret / Token / credential values as diagnostics.

A successful audit should not dump every healthy container/file/record when a concise count and exception list proves the acceptance condition.

The exact operator-facing return envelope is owned by the Workspace top-level operating authority. Server helpers may expose machine-readable status fields, but must not redefine the external interface contract independently.

## 10. Interruption / Pending-State Recovery

UI transport failure, chat response truncation, network disconnect, client retry UI, tool-response delivery failure and an async operation still being `queued` / `in_progress` are **not** proof that the underlying operation failed, succeeded or never started.

Within an available execution turn:
- when a dependent CI / async check is expected to settle and its status is queryable, continue bounded polling to a terminal state instead of stopping after the first `queued` / `in_progress` readback;
- do not wait indefinitely; use a bounded wait/retry budget appropriate to the operation and preserve the pending identifier when the budget is exhausted;
- a transient read failure should be retried or independently read back when safe before declaring the Task blocked.

After an assistant/client/network interruption:
- recover from durable external state first: exact repository/PR HEAD, commit presence, CI/workflow state, runtime/provider readback or other authoritative target state as applicable;
- do not blindly repeat the last mutation merely because the previous response was not delivered;
- determine whether the previous mutation was `NOT_APPLIED`, `APPLIED`, `PARTIAL`, or `UNKNOWN` before retrying;
- if the operation has a stable run/job/request identifier, continue from that identifier when possible rather than starting a duplicate operation;
- if the prior action is idempotent, idempotency does not remove the need to read back target state when duplicate side effects or concurrent work are possible;
- the next available execution turn should resume from the last verified durable state without requiring the operator to reconstruct already-recorded context.

A UI message such as “waiting for the full response”, “network error”, “retry”, or equivalent transport status is evidence about response delivery only. It must not be promoted into Server/Repository/Provider operation state.

## 11. Completion Boundary

`PRE_EXECUTION_COMPLETE=YES` means the exact external operation can be handed off safely. It does not mean that operation has executed.

After external execution, promote state only from returned evidence. Never infer Server/Provider/Runtime/Production PASS from command issuance alone.

If evidence is incomplete or contradicts detailed diagnostics, keep the stronger state `UNKNOWN / NOT_VERIFIED / PARTIAL` until resolved.

## 12. Invariants

- preserve the caller's interactive shell when a child operation fails;
- never present reversible local Git mutation as pure read-only inspection;
- never mix another task's diff into an automated commit;
- serialize same-target writers or fail closed on lock contention;
- never expose credential values in command output;
- never hide partial mutation behind a successful final print command;
- never claim execution, verification or PASS without returned evidence;
- response-delivery failure is not operation failure;
- after interruption, read back durable target state before retrying a mutation;
- server-core mutation permission and Server-operation execution permission remain separate boundaries.
