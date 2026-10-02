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

command -v flock >/dev/null 2>&1 || { echo "[error] flock is required for serialized Workspace MCP mutation" >&2; echo "NO_CHANGES_PERFORMED" >&2; exit 1; }
[[ -d "$HOME" ]] || { echo "[error] HOME directory is unavailable for Workspace MCP mutation lock" >&2; echo "NO_CHANGES_PERFORMED" >&2; exit 1; }
exec 9<"$HOME"
flock -n 9 || { echo "[error] another Workspace MCP mutation is active; refusing concurrent config write" >&2; echo "NO_CHANGES_PERFORMED" >&2; exit 1; }

python3 - "$MANIFEST" "$GLOBAL_MCP" <<'PY'
import json, os, shutil, stat, sys, time
from pathlib import Path

manifest_path = Path(sys.argv[1])
target = Path(sys.argv[2])
state = {
    'client_dir_updated': False,
    'backup_created': False,
    'config_updated': False,
    'backup_retention': 'NOT_APPLICABLE',
}

def emit(result: str, exit_code: int) -> None:
    print('GACE_MCP_INSTALL_RESULT_BEGIN')
    print(f'RESULT={result}')
    print(f'EXIT_CODE={exit_code}')
    print(f'CLIENT_DIR_UPDATED={"YES" if state["client_dir_updated"] else "NO"}')
    print(f'BACKUP_CREATED={"YES" if state["backup_created"] else "NO"}')
    print(f'CONFIG_UPDATED={"YES" if state["config_updated"] else "NO"}')
    print(f'BACKUP_RETENTION={state["backup_retention"]}')
    print('GACE_MCP_INSTALL_RESULT_END')

def fail(message: str, code: int = 1) -> None:
    print(f'[error] {message}', file=sys.stderr)
    result = 'PARTIAL' if any((state['client_dir_updated'], state['backup_created'], state['config_updated'])) else 'FAIL'
    emit(result, code)
    raise SystemExit(code)

try:
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
except Exception as exc:
    fail(f'invalid workspace MCP manifest: {exc}')
servers = manifest.get('servers')
if not isinstance(servers, dict) or not servers:
    fail('workspace MCP manifest has no servers')

runtime_servers = {name: {key: value for key, value in definition.items() if key != 'authentication'} for name, definition in servers.items()}
preserve_auth_fields = set(manifest.get('installation', {}).get('preserve_existing_auth_fields', ['auth', 'headers', 'env']))
try:
    backup_keep = int(manifest.get('installation', {}).get('backup_keep', 3))
except (TypeError, ValueError):
    fail('installation.backup_keep must be an integer')
if backup_keep < 1 or backup_keep > 20:
    fail('installation.backup_keep must be between 1 and 20')

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

def normalized_secure_mode(original_mode: int) -> int:
    owner_read = bool(original_mode & stat.S_IRUSR)
    owner_write = bool(original_mode & stat.S_IWUSR)
    if owner_read and not owner_write:
        return 0o400
    return 0o600

try:
    if not target.parent.exists():
        target.parent.mkdir(parents=True, mode=0o700)
        state['client_dir_updated'] = True
    current_dir_mode = stat.S_IMODE(target.parent.stat().st_mode)
    if current_dir_mode != 0o700:
        os.chmod(target.parent, 0o700)
        state['client_dir_updated'] = True
except Exception as exc:
    fail(f'failed to secure client config directory: {exc}')

existing_mode = 0o600
if target.exists():
    try:
        current = json.loads(target.read_text(encoding='utf-8'))
        existing_mode = normalized_secure_mode(stat.S_IMODE(target.stat().st_mode))
    except Exception as exc:
        fail(f'invalid existing MCP JSON: {exc}')
else:
    current = {}

if not isinstance(current, dict):
    fail('existing MCP config is not a JSON object')
current_servers = current.setdefault('mcpServers', {})
if not isinstance(current_servers, dict):
    fail('existing mcpServers is not an object')

for name, definition in runtime_servers.items():
    if name in current_servers and not runtime_compatible(current_servers[name], definition):
        fail(f'MCP name collision: {name}; existing runtime transport definition differs')

changed = False
for name, definition in runtime_servers.items():
    if name not in current_servers:
        current_servers[name] = definition
        changed = True

mode_needs_tightening = target.exists() and stat.S_IMODE(target.stat().st_mode) != existing_mode
if changed or mode_needs_tightening:
    if target.exists():
        try:
            backup = target.with_name(target.name + '.backup-' + time.strftime('%Y%m%d-%H%M%S') + f'-{time.time_ns()}')
            shutil.copy2(target, backup)
            os.chmod(backup, existing_mode)
            state['backup_created'] = True
            print(f'[backup] {backup}')
        except Exception as exc:
            fail(f'failed to create secure MCP config backup: {exc}')
    tmp = target.with_name(target.name + f'.tmp-{os.getpid()}-{time.time_ns()}')
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, existing_mode)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(json.dumps(current, ensure_ascii=False, indent=2) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, existing_mode)
        os.replace(tmp, target)
        state['config_updated'] = True
        os.chmod(target, existing_mode)
    except Exception as exc:
        fail(f'failed to update MCP config: {exc}')
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    try:
        backups = sorted(target.parent.glob(target.name + '.backup-*'), key=lambda p: p.name, reverse=True)
        for stale in backups[backup_keep:]:
            stale.unlink()
        state['backup_retention'] = 'PASS'
    except Exception as exc:
        state['backup_retention'] = 'FAIL'
        fail(f'MCP config updated but backup retention failed: {exc}')
    print(f'[updated] {target}')
else:
    print(f'[ok] already configured: {target}')

print(f'[ok] MCP config mode={oct(stat.S_IMODE(target.stat().st_mode)) if target.exists() else "n/a"} backup_keep={backup_keep}')
print('[ok] shared MCP manifest installed without provider token material')
emit('PASS', 0)
PY
