#!/usr/bin/env bash
set -euo pipefail

PROJECTS_DIR="/home/admin1/projects"
SERVER_CORE_RULES="/home/admin1/server-core/.cursor/rules"
PROJECTS_RULES="${PROJECTS_DIR}/.cursor/rules"

PROJECT_NAME=""
while [[ $# -gt 0 ]]; do
  case "$1" in
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

if [[ -n "$PROJECT_NAME" ]]; then
  TARGET="${PROJECTS_DIR}/${PROJECT_NAME}"
  if [[ -d "$TARGET" ]]; then
    echo "[skip] ${TARGET} already exists"
  else
    mkdir -p "$TARGET"
    echo "[created] ${TARGET}"
  fi
fi

if [[ -L "$PROJECTS_RULES" ]] && [[ "$(readlink "$PROJECTS_RULES")" == "$SERVER_CORE_RULES" ]]; then
  echo "[ok] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
else
  rm -rf "$PROJECTS_RULES"
  ln -sfn "$SERVER_CORE_RULES" "$PROJECTS_RULES"
  echo "[fixed] ${PROJECTS_RULES} -> ${SERVER_CORE_RULES}"
fi

echo "Done."
