#!/usr/bin/env bash
set -euo pipefail

PROJECTS_DIR="/home/admin1/projects"
SERVER_CORE_ROOT="/home/admin1/server-core"
DUPLICATE_SERVER_CORE="${PROJECTS_DIR}/server-core"
SERVER_CORE_RULES="${SERVER_CORE_ROOT}/.cursor/rules"
PROJECTS_RULES="${PROJECTS_DIR}/.cursor/rules"
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPLY=0
CREATE_PROJECT=0
PROJECT_NAME=""

usage() {
  cat <<'USAGE'
Usage: scripts/init-dev-workspace.sh [--check] [--apply-workspace-mutation] [--project NAME --create-project]

Default behavior is read-only verification. Workspace/client mutation requires
--apply-workspace-mutation. Creating a Project directory additionally requires
--create-project together with --project NAME.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) shift ;;
    --apply-workspace-mutation) APPLY=1; shift ;;
    --create-project) CREATE_PROJECT=1; shift ;;
    --project)
      if [[ $# -lt 2 ]]; then
        echo "[error] missing value for --project" >&2
        exit 2
      fi
      PROJECT_NAME="$2"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "[error] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$SCRIPT_ROOT" != "$SERVER_CORE_ROOT" ]]; then
  echo "[error] server-core workspace initializer must run from canonical checkout: ${SERVER_CORE_ROOT}" >&2
  echo "[error] current checkout: ${SCRIPT_ROOT}" >&2
  echo "NO_CHANGES_PERFORMED" >&2
  exit 1
fi

if [[ -e "$DUPLICATE_SERVER_CORE" ]]; then
  echo "[error] duplicate server-core checkout detected: ${DUPLICATE_SERVER_CORE}" >&2
  echo "[error] reconcile/remove the duplicate before workspace initialization" >&2
  echo "NO_CHANGES_PERFORMED" >&2
  exit 1
fi

if [[ ! -d "$SERVER_CORE_RULES" ]]; then
  echo "[error] server-core rules directory is missing: $SERVER_CORE_RULES" >&2
  exit 1
fi

if [[ "$CREATE_PROJECT" == "1" && -z "$PROJECT_NAME" ]]; then
  echo "[error] --create-project requires --project NAME" >&2
  echo "NO_CHANGES_PERFORMED" >&2
  exit 2
fi
if [[ -n "$PROJECT_NAME" && "$CREATE_PROJECT" != "1" ]]; then
  echo "[error] --project NAME does not create or modify anything without --create-project" >&2
  echo "NO_CHANGES_PERFORMED" >&2
  exit 2
fi
if [[ "$CREATE_PROJECT" == "1" && "$APPLY" != "1" ]]; then
  echo "[error] Project directory creation requires --apply-workspace-mutation" >&2
  echo "NO_CHANGES_PERFORMED" >&2
  exit 2
fi

validate_project_name() {
  local name="$1"
  if [[ -z "$name" || "$name" == "." || "$name" == ".." || "$name" == */* || "$name" == *\\* ]]; then
    return 1
  fi
  [[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]]
}

if [[ "$CREATE_PROJECT" == "1" ]] && ! validate_project_name "$PROJECT_NAME"; then
  echo "[error] unsafe project name; expected a single directory name using A-Z a-z 0-9 . _ -" >&2
  echo "NO_CHANGES_PERFORMED" >&2
  exit 2
fi

if [[ "$APPLY" != "1" ]]; then
  echo "WORKSPACE_INIT_MODE=READ_ONLY_CHECK"
  python3 "${SERVER_CORE_ROOT}/scripts/workspace_command_center_check.py"
  bash "${SERVER_CORE_ROOT}/scripts/verify-workspace-mcp.sh"
  echo "Done. No changes performed."
  exit 0
fi

mutations=()
record_mutation() {
  local value="$1"
  local item
  for item in "${mutations[@]}"; do
    [[ "$item" == "$value" ]] && return 0
  done
  mutations+=("$value")
}
finish_apply() {
  local rc=$?
  trap - EXIT
  echo "GACE_WORKSPACE_INIT_RESULT_BEGIN"
  if [[ "$rc" -eq 0 ]]; then
    echo "RESULT=PASS"
  elif [[ ${#mutations[@]} -gt 0 ]]; then
    echo "RESULT=PARTIAL"
  else
    echo "RESULT=FAIL"
  fi
  echo "EXIT_CODE=$rc"
  if [[ ${#mutations[@]} -gt 0 ]]; then
    printf 'MUTATION_APPLIED=%s\n' "$(IFS=,; echo "${mutations[*]}")"
  else
    echo "MUTATION_APPLIED=NONE"
  fi
  echo "GACE_WORKSPACE_INIT_RESULT_END"
  exit "$rc"
}
trap finish_apply EXIT

echo "WORKSPACE_INIT_MODE=AUTHORIZED_MUTATION"

if [[ "$CREATE_PROJECT" == "1" ]]; then
  TARGET="${PROJECTS_DIR}/${PROJECT_NAME}"
  case "$TARGET" in
    "${PROJECTS_DIR}/"*) ;;
    *)
      echo "[error] project target escaped canonical projects root: ${TARGET}" >&2
      echo "NO_CHANGES_PERFORMED" >&2
      exit 2
      ;;
  esac
  if [[ -d "$TARGET" ]]; then
    echo "[skip] ${TARGET} already exists"
  elif [[ -e "$TARGET" ]]; then
    echo "[error] project target exists but is not a directory: ${TARGET}" >&2
    exit 1
  else
    mkdir -p -- "$TARGET"
    record_mutation "PROJECT_DIR_CREATED"
    echo "[created] ${TARGET}"
  fi
fi

if [[ -L "$PROJECTS_RULES" ]]; then
  if [[ "$(readlink -f "$PROJECTS_RULES")" == "$(readlink -f "$SERVER_CORE_RULES")" ]]; then
    echo "[ok] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
  else
    echo "[error] ${PROJECTS_RULES} is a symlink to an unexpected target: $(readlink -f "$PROJECTS_RULES")" >&2
    exit 1
  fi
elif [[ -e "$PROJECTS_RULES" ]]; then
  echo "[error] ${PROJECTS_RULES} already exists and is not the required symlink; no deletion performed" >&2
  exit 1
else
  mkdir -p "$(dirname "$PROJECTS_RULES")"
  ln -s "$SERVER_CORE_RULES" "$PROJECTS_RULES"
  record_mutation "RULES_LINK_CREATED"
  echo "[created] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
fi

set +e
repair_out="$(python3 "${SERVER_CORE_ROOT}/scripts/workspace_command_center_check.py" --repair --authorize-workspace-mutation 2>&1)"
repair_rc=$?
set -e
printf '%s\n' "$repair_out"
grep -q '^WORKSPACE_BACKUP=' <<<"$repair_out" && record_mutation "WORKSPACE_BACKUP_CREATED"
grep -q '^WORKSPACE_REPAIR=UPDATED ' <<<"$repair_out" && record_mutation "WORKSPACE_FILE_UPDATED"
[[ "$repair_rc" -eq 0 ]] || exit "$repair_rc"

set +e
install_out="$(bash "${SERVER_CORE_ROOT}/scripts/install-workspace-mcp.sh" --apply-workspace-mcp-mutation 2>&1)"
install_rc=$?
set -e
printf '%s\n' "$install_out"
grep -q '^CLIENT_DIR_UPDATED=YES$' <<<"$install_out" && record_mutation "GLOBAL_MCP_CLIENT_DIR_UPDATED"
grep -q '^BACKUP_CREATED=YES$' <<<"$install_out" && record_mutation "GLOBAL_MCP_BACKUP_CREATED"
grep -q '^CONFIG_UPDATED=YES$' <<<"$install_out" && record_mutation "GLOBAL_MCP_UPDATED"
[[ "$install_rc" -eq 0 ]] || exit "$install_rc"

bash "${SERVER_CORE_ROOT}/scripts/verify-workspace-mcp.sh"
python3 "${SERVER_CORE_ROOT}/scripts/workspace_command_center_check.py"
echo "Done."
