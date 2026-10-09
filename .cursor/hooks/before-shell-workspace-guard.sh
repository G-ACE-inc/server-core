#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/admin1/server-core"
GUARD="${ROOT}/scripts/gace_shell_workspace_command_guard.py"
input="$(cat)"
command="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("command",""))' <<<"$input")"
if [[ -z "$command" ]]; then
  echo '{"permission":"allow"}'
  exit 0
fi
if python3 "$GUARD" --command "$command" --json >/tmp/gace-shell-guard-last.json 2>/dev/null; then
  echo '{"permission":"allow","agent_message":"gace workspace shell guard ALLOW"}'
  exit 0
fi
code="$(python3 -c 'import json; print(json.load(open("/tmp/gace-shell-guard-last.json")).get("code","DENY"))' 2>/dev/null || echo DENY)"
echo "{\"permission\":\"deny\",\"user_message\":\"Blocked: ${code}. See G-ACE workspace parent/worktree policy (#16).\",\"agent_message\":\"TOP_LEVEL_CHILD_PROJECT_BLOCKED:${code}\"}"
exit 2
