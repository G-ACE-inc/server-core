#!/usr/bin/env bash
set -euo pipefail

SERVER_CORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${SERVER_CORE_ROOT}/operations/workspace-mcp.json"
GLOBAL_DIR="${HOME}/.cursor"
GLOBAL_MCP="${GLOBAL_DIR}/mcp.json"
APPLY=0

usage() {
  cat <<'USAGE'
Usage: scripts/install-workspace-mcp.sh --apply-workspace-mcp-mutation

Mutates the current user's global Cursor MCP config to reconcile the
server-core managed Workspace MCP entries. This is a runtime/client config
mutation, not a server-core repository mutation.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply-workspace-mcp-mutation) APPLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[error] unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$APPLY" != "1" ]]; then
  echo "[error] Workspace-global MCP config mutation requires --apply-workspace-mcp-mutation" >&2
  echo "NO_CHANGES_PERFORMED" >&2
  exit 2
fi

python3 - "$MANIFEST" "$GLOBAL_MCP" <<'PY'
import json, os, shutil, stat, sys, time
from pathlib import Path

manifest_path = Path(sys.argv[1])
target = Path(sys.argv[2])
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
servers = manifest.get('servers')
if not isinstance(servers, dict) or not servers:
    raise SystemExit('[error] workspace MCP manifest has no servers')

runtime_servers = {name: {key: value for key, value in definition.items() if key != 'authentication'} for name, definition in servers.items()}
preserve_auth_fields = set(manifest.get('installation', {}).get('preserve_existing_auth_fields', ['auth', 'headers', 'env']))
backup_keep = int(manifest.get('installation', {}).get('backup_keep', 3))
if backup_keep < 1 or backup_keep > 20:
    raise SystemExit('[error] installation.backup_keep must be between 1 and 20')

def runtime_compatible(existing, expected):
    if not isinstance(existing, dict) or not isinstance(expected, dict):
        return existing == expected
    for key, expected_value in expected.items():
        if key not in existing:
            return False
        actual_value = existing[key]
        if key in preserve_auth_fields and isinstance(expected_value, dict):
            if not isinstance(actual_value, dict):
                return False
            for subkey, subvalue in expected_value.items():
                if actual_value.get(subkey) != subvalue:
                    return False
        elif actual_value != expected_value:
            return False
    for key in existing:
        if key not in expected and key not in preserve_auth_fields:
            return False
    return True

target.parent.mkdir(parents=True, exist_ok=True)
try:
    os.chmod(target.parent, 0o700)
except OSError:
    pass

existing_mode = 0o600
if target.exists():
    try:
        current = json.loads(target.read_text(encoding='utf-8'))
        original_mode = stat.S_IMODE(target.stat().st_mode)
        existing_mode = original_mode & 0o700
        if existing_mode == 0:
            existing_mode = 0o600
        existing_mode = min(existing_mode, 0o600)
    except Exception as exc:
        raise SystemExit(f'[error] invalid existing MCP JSON: {exc}')
else:
    current = {}

if not isinstance(current, dict):
    raise SystemExit('[error] existing MCP config is not a JSON object')
current_servers = current.setdefault('mcpServers', {})
if not isinstance(current_servers, dict):
    raise SystemExit('[error] existing mcpServers is not an object')

for name, definition in runtime_servers.items():
    if name in current_servers and not runtime_compatible(current_servers[name], definition):
        raise SystemExit(f'[error] MCP name collision: {name}; existing runtime transport definition differs')

changed = False
for name, definition in runtime_servers.items():
    if name not in current_servers:
        current_servers[name] = definition
        changed = True

mode_needs_tightening = target.exists() and stat.S_IMODE(target.stat().st_mode) != existing_mode
if changed or mode_needs_tightening:
    if target.exists():
        backup = target.with_name(target.name + '.backup-' + time.strftime('%Y%m%d-%H%M%S'))
        shutil.copy2(target, backup)
        os.chmod(backup, existing_mode)
        print(f'[backup] {backup}')
    tmp = target.with_suffix('.tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, existing_mode)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(json.dumps(current, ensure_ascii=False, indent=2) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, existing_mode)
        os.replace(tmp, target)
        os.chmod(target, existing_mode)
    finally:
        if tmp.exists():
            tmp.unlink()
    backups = sorted(target.parent.glob(target.name + '.backup-*'), key=lambda p: p.name, reverse=True)
    for stale in backups[backup_keep:]:
        stale.unlink()
    print(f'[updated] {target}')
else:
    print(f'[ok] already configured: {target}')

print(f'[ok] MCP config mode={oct(stat.S_IMODE(target.stat().st_mode)) if target.exists() else "n/a"} backup_keep={backup_keep}')
print('[ok] shared MCP manifest installed without provider token material')
PY
