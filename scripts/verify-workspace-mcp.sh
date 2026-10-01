#!/usr/bin/env bash
set -euo pipefail

SERVER_CORE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${SERVER_CORE_ROOT}/operations/workspace-mcp.json"
GLOBAL_MCP="${HOME}/.cursor/mcp.json"

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
for name, expected in runtime_servers.items():
    actual = servers.get(name)
    if actual != expected:
        raise SystemExit(f'[fail] shared MCP runtime mismatch: {name}')

serialized = target.read_text(encoding='utf-8')
if re.search(r'(?i)(bearer|token|secret|password|api[_-]?key)\\s*[:=]\\s*[A-Za-z0-9_./+=-]{12,}', serialized):
    raise SystemExit('[fail] possible plaintext credential in global MCP config')

print('WORKSPACE_MCP_CONFIG=PASS')
print('CLOUDFLARE_MCP=REGISTERED')
print('HUGGINGFACE_MCP=REGISTERED')
PY

if command -v agent >/dev/null 2>&1; then
  echo '[info] Cursor CLI detected; listing MCP state'
  agent mcp list || true
else
  echo '[info] Cursor CLI not installed in this shell; config verification only'
fi
