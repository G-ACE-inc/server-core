# CU40 — Work Routine actual execution binding (proposed design, 2026-10-12)

Status: PROPOSED_PR, not adopted main. Owner: GPT CHAT / CU40, server-core existing shared routine. Baseline: `docs/G_ACE_WORKSPACE.md` §6; `docs/LOAD_SCOPE.md`; Rule #17 §§5–7; Current #40. Do not alter #10 Tool B, DebugAI or TGserver owners.

## Problem and root cause

Actual GPT CHAT repeatedly read current rules then ended after progress prose, Issue comment, or an abstract NEXT while same-CU work remained. Repository CI and opt-in receipts prove bounded commands only; no available `github_project_chat_turn_gate.py` hook intercepts normal ChatGPT final-response submission. Treating another receipt/guard as native reply enforcement is a false claim and does not correct the model's termination. The effective fix therefore has two separate planes: **operator behavior** (real same-turn continuation under #17) and **existing machine action admission** (actual callers, without making STOP promises).

## Chosen minimal executable correction

An existing CU40 machine path `scripts/gace_mutation_rehydrate_check.py`, when run for an actual mutation with `GACE_WORK_ROUTINE_TURN`, calls `work_routine_design_entry_gate.evaluate_turn`. That latter function accepts `mutation_scope=read_only`, because design checks are rightly irrelevant to purely read-only activity. If a read-only receipt can authorize a mutation without matching the actual effect, the existing guard does not preserve the purpose/design binding. Repair **at the existing mutation admission**, not in a new workflow: deny `mutation_scope=read_only` for a mutation receipt, even if its readback hashes and rule-entry fields are valid. Preserve optional legacy behavior when no opt-in receipt is supplied; preserve already-valid `routine_fix` / `design_changing` receipts and all other Owner/branch/paths constraints. This is a real limited trust-boundary correction, **not** a native reply-stop fix.

### Preconditions and acceptance

1. Freeze this design in the existing server-core repo on an isolated owner branch **before** source mutation.
2. Demonstrate via focused unit regression that a read-only Work Routine receipt is rejected at actual mutation preflight (expected specific deny), while routine_fix with a valid receipt continues. Preserve absent receipt behavior controlled by `GACE_WORK_ROUTINE_REQUIRED`. No Github Projects fields, token, MCP, workflow, Host policy, owner widening or free external AI calls.
3. Read back exact changed Source and tests, run focused local tests and actual CI on the same branch/PR. If CI fails, determine root cause and repair without treating the fail as a CU stop.
4. Operator behavioral acceptance is separate and remains unverified until real GPT CHAT repeatedly completes same-CU follow-on actions after progress/commit/CI/Issue, actually recovers from a failure and terminates only at #17's legitimate stopping point. An Issue or test PASS cannot assert that behavior. A verified missing native send hook stays documented as unavailable rather than simulated.

## Scope and rollback

Only existing `scripts/gace_mutation_rehydrate_check.py`, focused tests, and this design baseline on the same branch. Changes to shared §6 / Design Delta only if the actual behavior or architecture diverges from the adopted contract. Rollback is the isolated source commit. No mutation of other CHAT-owned paths.

## Why this correction matters

The mismatch allows a read-only proof to be treated as write authorization in the actual installed mutation-check pathway. The proposed code change closes one genuine instance of **reading/verifying something different from the action performed**. This is a necessary but **not sufficient** component of restoring normal CHAT autonomous development; it must never be reported as a guarantee against premature replies.
