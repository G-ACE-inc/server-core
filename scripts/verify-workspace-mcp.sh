#!/usr/bin/env bash
set -euo pipefail

SERVER_CORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${SERVER_CORE_ROOT}/operations/workspace-mcp.json"
GLOBAL_MCP="${HOME}/.cursor/mcp.json"
CLIENT_READBACK=0

usage() {
  cat <<'USAGE'
Usage: scripts/verify-workspace-mcp.sh [--client-readback]

Default behavior verifies the managed global MCP config contract only and
performs no external client command. Existing client-local auth/headers/env
containers are permitted and never printed or treated as live-auth proof.
--client-readback additionally asks an available Cursor CLI for registration
state only.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --client-readback) CLIENT_READBACK=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[error] unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

python3 - "$MANIFEST" "$GLOBAL_MCP" <<'PY'
import json, stat, sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
target = Path(sys.argv[2])
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
if not target.is_file():
    raise SystemExit(f'[fail] global MCP config missing: {target}')
mode = stat.S_IMODE(target.stat().st_mode)
if mode not in (0o400, 0o600):
    raise SystemExit(f'[fail] global MCP config mode must be owner-only non-executable 0400 or 0600: {oct(mode)}')
config = json.loads(target.read_text(encoding='utf-8'))
servers = config.get('mcpServers', {})
if not isinstance(servers, dict):
    raise SystemExit('[fail] mcpServers is not an object')
manifest_servers = manifest.get('servers', {})
preserve_auth_fields = set(manifest.get('installation', {}).get('preserve_existing_auth_fields', ['auth', 'headers', 'env']))
runtime_servers = {name: {key: value for key, value in definition.items() if key != 'authentication'} for name, definition in manifest_servers.items()}

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

for name, expected in runtime_servers.items():
    actual = servers.get(name)
    if actual is None:
        raise SystemExit(f'[fail] shared MCP missing: {name}')
    if not runtime_compatible(actual, expected):
        raise SystemExit(f'[fail] shared MCP runtime mismatch: {name}')

# Repository manifest must not carry provider bearer/password/token values.
# Client-local credential containers may exist by design, but this verifier
# never prints or validates their secret values and never promotes them to auth PASS.
for name, definition in manifest_servers.items():
    for key in ('headers', 'env'):
        if key in definition:
            raise SystemExit(f'[fail] managed manifest must not embed client credential container: {name}.{key}')

print('WORKSPACE_MCP_CONFIG=PASS')
print(f'MCP_CONFIG_MODE={oct(mode)}')
print('MCP_VERIFICATION_SCOPE=CONFIG_ONLY')
for name in sorted(runtime_servers):
    print(f'MCP_MANAGED_CONFIG={name}:REGISTERED')
print('MCP_CLIENT_CREDENTIAL_CONTAINERS=PERMITTED_NOT_DISCLOSED')
print('MCP_AUTHENTICATION=NOT_VERIFIED')
print('MCP_TRANSPORT=NOT_VERIFIED')
print('MCP_INTERFACE_DISCOVERY=NOT_VERIFIED')
print('MCP_REPRESENTATIVE_CALL=NOT_VERIFIED')
print('MCP_AVAILABLE_VERIFIED=NO')
PY

if [[ "$CLIENT_READBACK" == "1" ]]; then
  if command -v agent >/dev/null 2>&1; then
    echo '[info] Cursor CLI detected; listing MCP registration state'
    agent mcp list
    echo 'MCP_CLIENT_READBACK=EXECUTED'
    echo 'MCP_CLIENT_READBACK_SCOPE=REGISTRATION_ONLY'
    echo 'MCP_AVAILABLE_VERIFIED=NO'
  else
    echo '[info] Cursor CLI not installed in this shell; client readback not executed'
    echo 'MCP_CLIENT_READBACK=NOT_EXECUTED'
    echo 'MCP_AVAILABLE_VERIFIED=NO'
  fi
else
  echo '[info] client MCP readback not requested; config verification only'
  echo 'MCP_CLIENT_READBACK=NOT_REQUESTED'
  echo 'MCP_AVAILABLE_VERIFIED=NO'
fi
