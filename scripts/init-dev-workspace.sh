#!/usr/bin/env bash
set -euo pipefail

ROOT="${GACE_HOME:-/home/admin1}"
PROJECT_NAME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    --project)
      PROJECT_NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

ROOT="$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$ROOT")"
SERVER_CORE="${ROOT}/server-core"
PROJECTS_DIR="${ROOT}/projects"
WORKSPACE_DIR="${ROOT}/workspace"
WORKSPACE_FILE="${WORKSPACE_DIR}/G-ACE.code-workspace"
SERVER_CORE_RULES="${SERVER_CORE}/.cursor/rules"
PROJECTS_CURSOR="${PROJECTS_DIR}/.cursor"
PROJECTS_RULES="${PROJECTS_CURSOR}/rules"
CHECKER="${SERVER_CORE}/scripts/workspace_command_center_check.py"

require_file() {
  if [[ ! -f "$1" ]]; then
    echo "Missing required authority: $1" >&2
    exit 1
  fi
}

require_dir() {
  if [[ ! -d "$1" ]]; then
    echo "Missing required directory: $1" >&2
    exit 1
  fi
}

require_file "${SERVER_CORE}/README.md"
require_file "${SERVER_CORE}/docs/LOAD_SCOPE.md"
require_file "${SERVER_CORE}/.cursor/rules/00_agent_runtime.mdc"
require_file "$CHECKER"
require_dir "$SERVER_CORE_RULES"

mkdir -p "$PROJECTS_DIR" "$WORKSPACE_DIR" "$PROJECTS_CURSOR"

if [[ -n "$PROJECT_NAME" ]]; then
  if [[ ! "$PROJECT_NAME" =~ ^[A-Za-z0-9._-]+$ ]] || [[ "$PROJECT_NAME" == "." ]] || [[ "$PROJECT_NAME" == ".." ]]; then
    echo "Invalid project name: $PROJECT_NAME" >&2
    exit 1
  fi
  TARGET="${PROJECTS_DIR}/${PROJECT_NAME}"
  if [[ -d "$TARGET" ]]; then
    echo "[skip] ${TARGET} already exists"
  else
    mkdir -p "$TARGET"
    echo "[created] ${TARGET}"
  fi
fi

if [[ -e "$PROJECTS_RULES" || -L "$PROJECTS_RULES" ]]; then
  if [[ ! -L "$PROJECTS_RULES" ]]; then
    echo "Refusing to replace non-symlink rules path: ${PROJECTS_RULES}" >&2
    exit 1
  fi
  CURRENT_TARGET="$(readlink "$PROJECTS_RULES")"
  if [[ "$CURRENT_TARGET" != "$SERVER_CORE_RULES" ]]; then
    rm "$PROJECTS_RULES"
    ln -s "$SERVER_CORE_RULES" "$PROJECTS_RULES"
    echo "[fixed] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
  else
    echo "[ok] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
  fi
else
  ln -s "$SERVER_CORE_RULES" "$PROJECTS_RULES"
  echo "[created] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
fi

python3 - "$SERVER_CORE" "$PROJECTS_DIR" "$WORKSPACE_FILE" <<'PY'
import json
import sys
from pathlib import Path

server_core = Path(sys.argv[1])
projects = Path(sys.argv[2])
workspace_file = Path(sys.argv[3])

payload = {
    "folders": [
        {"name": "server-core", "path": str(server_core)},
        {"name": "projects", "path": str(projects)},
    ],
    "settings": {
        "files.exclude": {
            "**/.git": True,
            "**/node_modules": True,
            "**/dist": True,
            "**/build": True,
            "**/.next": True,
            "**/archive": True,
            "**/logs": True,
            "**/backups": True,
        },
        "search.exclude": {
            "**/.git": True,
            "**/node_modules": True,
            "**/dist": True,
            "**/build": True,
            "**/.next": True,
            "**/archive": True,
            "**/logs": True,
            "**/backups": True,
        },
    },
}
workspace_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[written] {workspace_file}")
PY

python3 "$CHECKER" --root "$ROOT"
echo "Done."
