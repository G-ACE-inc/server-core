#!/usr/bin/env bash
set -euo pipefail

PROJECTS_DIR="/home/admin1/projects"
SERVER_CORE_ROOT="/home/admin1/server-core"
SERVER_CORE_RULES="${SERVER_CORE_ROOT}/.cursor/rules"
PROJECTS_RULES="${PROJECTS_DIR}/.cursor/rules"
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$SCRIPT_ROOT" != "$SERVER_CORE_ROOT" ]]; then
  echo "[error] server-core workspace initializer must run from canonical checkout: ${SERVER_CORE_ROOT}" >&2
  echo "[error] current checkout: ${SCRIPT_ROOT}" >&2
  echo "NO_CHANGES_PERFORMED" >&2
  exit 1
fi

PROJECT_NAME=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --project" >&2
        exit 2
      fi
      PROJECT_NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "$SERVER_CORE_RULES" ]]; then
  echo "[error] server-core rules directory is missing: $SERVER_CORE_RULES" >&2
  exit 1
fi

if [[ -n "$PROJECT_NAME" ]]; then
  TARGET="${PROJECTS_DIR}/${PROJECT_NAME}"
  if [[ -d "$TARGET" ]]; then
    echo "[skip] ${TARGET} already exists"
  elif [[ -e "$TARGET" ]]; then
    echo "[error] project target exists but is not a directory: ${TARGET}" >&2
    exit 1
  else
    mkdir -p "$TARGET"
    echo "[created] ${TARGET}"
  fi
fi

if [[ -L "$PROJECTS_RULES" ]]; then
  if [[ "$(readlink "$PROJECTS_RULES")" == "$SERVER_CORE_RULES" ]]; then
    echo "[ok] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
  else
    echo "[error] ${PROJECTS_RULES} is a symlink to an unexpected target: $(readlink "$PROJECTS_RULES")" >&2
    exit 1
  fi
elif [[ -e "$PROJECTS_RULES" ]]; then
  echo "[error] ${PROJECTS_RULES} already exists and is not the required symlink; no deletion performed" >&2
  exit 1
else
  mkdir -p "$(dirname "$PROJECTS_RULES")"
  ln -s "$SERVER_CORE_RULES" "$PROJECTS_RULES"
  echo "[created] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
fi

python3 "${SERVER_CORE_ROOT}/scripts/workspace_command_center_check.py" --repair
bash "${SERVER_CORE_ROOT}/scripts/install-workspace-mcp.sh"
bash "${SERVER_CORE_ROOT}/scripts/verify-workspace-mcp.sh"
python3 "${SERVER_CORE_ROOT}/scripts/workspace_command_center_check.py"
echo "Done."
