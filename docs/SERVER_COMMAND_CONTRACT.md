# SERVER COMMAND EXECUTION CONTRACT

Version: 2026-10-02
Role: Server-side work that cannot be executed directly by the current assistant/client is prepared and handed off safely, with minimum operator interaction and explicit evidence boundaries.

## 1. Purpose

This contract defines how server commands are prepared, executed by an operator when required, and returned for verification.

It does not grant mutation permission. Repository, Workspace, Provider, credential, runtime and production authorization are owned by their respective authorities.

## 2. Executor Selection

Before issuing a Server command, use the least costly capable execution route in this order when the Task permits it:

1. existing deterministic repository checks / static inspection / CI;
2. directly available assistant tools/connectors;
3. existing read-only server helper;
4. exact operator Server command;
5. Server-side AI only when deterministic tooling and the current assistant/client cannot complete the required reasoning/action safely.

Do not ask the operator to perform work that the current assistant/client can already complete directly.

Do not invoke Server-side AI for work that a deterministic command, existing helper, source inspection, test, CI or provider readback can settle reliably.

## 3. Pre-command Requirement

Before producing an operator command, resolve the canonical Pre-execution Contract defined by `docs/G_ACE_WORKSPACE.md` and identify at minimum:

```text
TARGET_PROJECT
TARGET_REPOSITORY
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
NEXT_ACTION
EXECUTION_ROUTE
EXECUTION_CAPABILITY
EXECUTION_AUTHORIZATION
VERIFY_PATH
PRE_EXECUTION_COMPLETE
BLOCKER
```

A command may be emitted only when the exact operation and its authorization boundary are known. Unknown path, branch, runtime identity, service identity, provider target or mutation authority must not be filled by assumption.

## 4. Interaction Budget

Operator interaction is a scarce resource. Prefer one paste-ready command that safely bundles:

```text
precheck -> exact action -> verification -> concise result envelope
```

Do not split a deterministic workflow into repeated `run -> paste -> next command` cycles when the same workflow can safely evaluate its own conditions and return one consolidated result.

Ask for intermediate output only when the next safe action genuinely depends on information that cannot be evaluated inside the command.

The total command body in one assistant response must not exceed **6072 characters**. If the safe workflow cannot fit, split only at a real safety/authority boundary.

## 5. Paste Safety

Operator commands must be complete, literal and paste-ready.

Requirements:
- put executable text in one fenced code block unless a real safety boundary requires separate blocks;
- do not include shell prompt prefixes such as `user@host:$`;
- do not mix expected output, previous output or explanatory prose into the command block;
- do not use `...`, `<placeholder>`, fake paths or omitted values in an executable command;
- avoid unnecessary blank lines and decorative comments;
- prefer compact composition with `&&`, `;` and grouped commands when readability and safety remain acceptable;
- never require the operator to edit the command manually unless the Task itself requires a secret/value that must not be disclosed to the assistant.

## 6. Interactive Shell Safety

Never apply fail-fast shell state directly to the operator's interactive shell.

Forbidden as a top-level interactive command pattern:

```text
set -e
set -u
set -o pipefail
set -euo pipefail
exit
```

When fail-fast behavior is required, run the workflow inside a child shell such as:

```text
bash -lc '...'
```

`exit` may be used inside that child shell. A child failure must return control to the operator's existing terminal instead of terminating the interactive session.

Read-only probes that may return non-zero should also be isolated when their exit behavior could disrupt the operator shell.

## 7. Mutation Classification

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

## 8. Authorization Scope

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

## 9. Multi-task / Multi-worker Safety

Assume multiple Projects, agents or change units may be active concurrently.

Before a write/commit operation:
- identify the exact change unit;
- ensure unrelated uncommitted changes are not staged or overwritten;
- do not use repository-wide staging when intended-file ownership is not exclusive;
- refuse automatic commit when the intended diff cannot be separated from other work;
- avoid switching or resetting a shared checkout when another active task may depend on its current state;
- prefer read-only Git object inspection over working-tree switching when possible.

## 10. Result Envelope

Server commands intended for operator execution should emit one concise final envelope even if detailed diagnostics are printed earlier.

Canonical format:

```text
GACE_RESULT_BEGIN
TASK=<stable short identifier>
TARGET=<exact target>
ACTION=<what was actually executed>
MUTATION_CLASS=<classification>
RESULT=PASS|FAIL|BLOCKED|PARTIAL
EVIDENCE=<compact decisive evidence>
NOT_PROVEN=<important limits>
NEXT_ACTION=<NONE or exact next action>
GACE_RESULT_END
```

Use additional fields only when they materially improve verification. Never put secret values in the envelope.

The operator should normally be asked to return the `GACE_RESULT_BEGIN ... GACE_RESULT_END` block plus any explicitly requested failure excerpt, not an unbounded terminal dump.

## 11. Output Budget

Commands should suppress or summarize unbounded output by default.

For inventories/logs:
- return counts, failing identifiers and bounded excerpts first;
- write large diagnostic output to a temporary file only when needed;
- print the path and a bounded summary rather than flooding the chat;
- never hide a failure merely to keep output short.

A successful audit should not dump every healthy container/file/record when a concise count and exception list proves the acceptance condition.

## 12. Completion Boundary

`PRE_EXECUTION_COMPLETE=YES` means the exact external operation can be handed off safely. It does not mean that operation has executed.

After operator execution, promote state only from returned evidence. Never infer Server/Provider/Runtime/Production PASS from command issuance alone.

If the returned envelope is incomplete or contradicts detailed evidence, keep the stronger state `UNKNOWN / NOT_VERIFIED / PARTIAL` until resolved.

## 13. Invariants

- minimize operator round trips;
- minimize paid/remote AI usage when deterministic routes are sufficient;
- never terminate the operator's interactive shell as a side effect of fail-fast command design;
- never present reversible local Git mutation as pure read-only inspection;
- never mix another task's diff into an automated commit;
- never expose credential values in command output;
- never claim execution, verification or PASS without returned evidence;
- server-core mutation permission and Server command execution permission remain separate boundaries.
