#!/usr/bin/env bash
set -euo pipefail

SERVER_CORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${SERVER_CORE_ROOT}/operations/workspace-mcp.json"
GLOBAL_MCP="${HOME}/.cursor/mcp.json"
CLIENT_READBACK=0

usage() {
  cat <<'USAGE'
Usage: scripts/verify-workspace-mcp.sh [--client-readback]

Default behavior verifies the global MCP config file only and performs no
external client command. --client-readback additionally asks an available
Cursor CLI for its MCP registration state.

This verifier never promotes config/client-registration evidence to live MCP
availability. Authentication, transport, interface discovery and a
representative call remain separate task-time verification responsibilities.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --client-readback)
      CLIENT_READBACK=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[error] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

python3 - "$MANIFEST" "$GLOBAL_MCP" <<'PY'
import json, re, sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
target = Path(sys.argv[2])
if not target.is_file():
    raise SystemExit(f'[fail] global MCP config missing: {target}')
config = json.loads(target.read_text(encoding='utf-8'))
servers = config.get('mcpServers', {})
manifest_servers = manifest.get('servers', {})
runtime_servers = {
    name: {key: value for key, value in definition.items() if key != 'authentication'}
    for name, definition in manifest_servers.items()
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

serialized = target.read_text(encoding='utf-8')
if re.search(r'(?i)(bearer|token|secret|password|api[_-]?key)\s*[:=]\s*[A-Za-z0-9_./+=-]{12,}', serialized):
    raise SystemExit('[fail] possible plaintext credential in global MCP config')

print('WORKSPACE_MCP_CONFIG=PASS')
print('MCP_VERIFICATION_SCOPE=CONFIG_ONLY')
print('CLOUDFLARE_MCP_CONFIG=REGISTERED')
print('HUGGINGFACE_MCP_CONFIG=REGISTERED')
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
