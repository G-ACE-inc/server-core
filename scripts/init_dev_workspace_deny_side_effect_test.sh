#!/usr/bin/env bash
# Isolated deny-path test: gate failure must not mkdir project dir.
set -euo pipefail
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
FAKE_PROJECTS="$TMP/projects"
mkdir -p "$FAKE_PROJECTS"
REG="$TMP/registry.md"
cat > "$REG" << 'REGDOC'
| Project | Repository authority | Known Workspace / Server entry | X | Y |
|---|---|---|---|---|
| demo | `seigo-gace/demo` | `/home/admin1/projects/demo` | a | b |
REGDOC
GATE=/home/admin1/server-core/scripts/init_dev_workspace_project_gate.py
python3 "$GATE" --name unregistered-cu --projects-dir "$FAKE_PROJECTS" --registry-doc "$REG" && exit 1 || true
test ! -e "$FAKE_PROJECTS/unregistered-cu"
python3 "$GATE" --name demo --projects-dir "$FAKE_PROJECTS" --registry-doc "$REG" && exit 1 || true
test ! -e "$FAKE_PROJECTS/demo"
echo INIT_DEV_WORKSPACE_DENY_ZERO_SIDE_EFFECT=PASS
