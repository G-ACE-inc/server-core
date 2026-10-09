#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GUARD="${ROOT}/scripts/gace_shell_workspace_command_guard.py"
input="$(cat)"
result="$(
  printf '%s' "$input" | python3 "$GUARD" --hook-stdin --json 2>/dev/null || true
)"
if [[ -z "$result" ]]; then
  echo '{"permission":"deny","user_message":"Blocked: HOOK_GUARD_FAILURE. Shell guard produced no verdict.","agent_message":"TOP_LEVEL_CHILD_PROJECT_BLOCKED:HOOK_GUARD_FAILURE"}'
  exit 2
fi
read -r verdict code <<<"$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("result","DENY"), d.get("code","DENY"))' "$result")"
if [[ "$verdict" == "ALLOW" ]]; then
  echo '{"permission":"allow","agent_message":"gace workspace shell guard ALLOW"}'
  exit 0
fi
echo "{\"permission\":\"deny\",\"user_message\":\"Blocked: ${code}. See G-ACE workspace parent/worktree policy (#16).\",\"agent_message\":\"TOP_LEVEL_CHILD_PROJECT_BLOCKED:${code}\"}"
exit 2
