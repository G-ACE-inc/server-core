#!/usr/bin/env bash
set -euo pipefail

SERVER_CORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${SERVER_CORE_ROOT}/operations/workspace-mcp.json"
GLOBAL_DIR="${HOME}/.cursor"
GLOBAL_MCP="${GLOBAL_DIR}/mcp.json"

python3 - "$MANIFEST" "$GLOBAL_MCP" <<'PY'
import json, os, shutil, sys, time
from pathlib import Path

manifest_path = Path(sys.argv[1])
target = Path(sys.argv[2])
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
servers = manifest.get('servers')
if not isinstance(servers, dict) or not servers:
    raise SystemExit('[error] workspace MCP manifest has no servers')

# "servers" is the Workspace contract source. Cursor only receives
# runtime-supported MCP fields; contract metadata such as "authentication"
# is intentionally not compared against the live client definition.
runtime_servers = {
    name: {key: value for key, value in definition.items() if key != 'authentication'}
    for name, definition in servers.items()
}
preserve_auth_fields = set(
    manifest.get('installation', {}).get(
        'preserve_existing_auth_fields',
        ['auth', 'headers', 'env'],
    )
)

def runtime_compatible(existing, expected):
    if not isinstance(existing, dict) or not isinstance(expected, dict):
        return existing == expected

    # Expected runtime fields must exist and match exactly, except that
    # credential containers are compared only for the contract-owned
    # expected keys. Existing provider credentials are never overwritten.
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

    # Existing extra fields are allowed only when they are credential/auth
    # containers explicitly covered by the Workspace merge policy.
    for key in existing:
        if key not in expected and key not in preserve_auth_fields:
            return False

    return True

target.parent.mkdir(parents=True, exist_ok=True)
if target.exists():
    try:
        current = json.loads(target.read_text(encoding='utf-8'))
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

if changed:
    if target.exists():
        backup = target.with_name(target.name + '.backup-' + time.strftime('%Y%m%d-%H%M%S'))
        shutil.copy2(target, backup)
        print(f'[backup] {backup}')
    tmp = target.with_suffix('.tmp')
    tmp.write_text(json.dumps(current, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, target)
    print(f'[updated] {target}')
else:
    print(f'[ok] already configured: {target}')

print('[ok] shared MCP manifest installed without provider token material')
PY
