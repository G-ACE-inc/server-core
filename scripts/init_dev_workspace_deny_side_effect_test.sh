#!/usr/bin/env bash
# Intentional gate denial must not be confused with a missing or crashed checker.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$ROOT/scripts/init_dev_workspace_project_gate.py"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
PROJECTS="$TMP/projects"
REG="$TMP/registry.md"
MASTER="$TMP/master.json"
mkdir -p "$PROJECTS"
BT="$(printf '\140')"
printf '| Project | Repository authority | Known Workspace / Server entry | X |\n|---|---|---|---|\n| Demo | %sseigo-gace/demo%s | %s/home/admin1/projects/demo%s | x |\n' "$BT" "$BT" "$BT" "$BT" >"$REG"
printf '%s\n' '{"repositories":[]}' >"$MASTER"

check_deny() {
  local script="$1" name="$2" code="$3" target="$4" out rc
  if [[ ! -f "$script" ]]; then
    echo "GATE_EXECUTABLE_MISSING" >&2
    return 4
  fi
  if out="$(python3 -B "$script" --name "$name" --projects-dir "$PROJECTS" --registry-doc "$REG" --master-registry "$MASTER" 2>&1)"; then
    echo "UNEXPECTED_GATE_ALLOW:$name" >&2
    return 4
  else
    rc=$?
  fi
  if [[ "$rc" -ne 1 ]]; then
    echo "GATE_EXECUTION_NOT_POLICY_DENIAL:$rc:$out" >&2
    return 4
  fi
  if ! printf '%s' "$out" | python3 -B -c 'import json,sys; x=json.load(sys.stdin); assert x["result"]=="DENY" and x["code"]==sys.argv[1]' "$code"; then
    echo "GATE_DENIAL_ORACLE_INVALID:$name" >&2
    return 4
  fi
  test ! -e "$target"
}

if check_deny "$TMP/missing_helper.py" never PROJECT_NOT_REGISTERED "$PROJECTS/never" >/dev/null 2>&1; then
  echo "FALSE_POSITIVE_MISSING_HELPER" >&2
  exit 1
fi
check_deny "$GATE" evil-cu PROJECT_NOT_REGISTERED "$PROJECTS/evil-cu"
check_deny "$GATE" demo PROJECT_NOT_EXISTING "$PROJECTS/demo"
echo INIT_DEV_WORKSPACE_DENY_ZERO_SIDE_EFFECT=PASS
