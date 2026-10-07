#!/usr/bin/env bash
set -euo pipefail
# Verification client only. Execution remains owned by the existing DebugAI MCP.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="$root/operations/workspace-mcp.json"
route="$root/operations/github-project-debugai-routing.json"
jq -e '.servers.debugai.command == "/usr/bin/docker" and
  .servers.debugai.args == ["exec","-i","debug-ai-debug-ai-1","node","/app/bin/debugai-mcp.mjs"]' "$manifest" >/dev/null
jq -e '.project.node_id == "PVT_kwHODOQFoM4BEJII" and
  .execution_backend.mcp_server == "debugai" and
  .execution_backend.tools.server_read_request == "debugai_server_read" and
  .execution_backend.tools.server_read_status == "debugai_server_status" and
  .execution_backend.tools.gitops_request == "debugai_gitops_request" and
  .execution_backend.tools.gitops_status == "debugai_gitops_status"' "$route" >/dev/null
expected_head="$(git -C /home/admin1/projects/debug-ai rev-parse HEAD)"
/usr/bin/docker exec -i -e GACE_EXPECTED_HEAD="$expected_head" debug-ai-debug-ai-1 node --input-type=module <<'JS'
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
const child = spawn(process.execPath, ['/app/bin/debugai-mcp.mjs'], {stdio:['pipe','pipe','pipe']});
let buffer = '', sequence = 0;
const pending = new Map();
child.stdout.on('data', chunk => {
  buffer += chunk;
  let newline;
  while ((newline = buffer.indexOf('\n')) >= 0) {
    const value = JSON.parse(buffer.slice(0, newline));
    buffer = buffer.slice(newline + 1);
    if (pending.has(value.id)) { pending.get(value.id)(value); pending.delete(value.id); }
  }
});
// Do not forward arbitrary runtime stderr into evidence.
child.stderr.on('data', () => {});
const timer = setTimeout(() => { child.kill(); process.exit(1); }, 30000);
const rpc = (method, params) => new Promise(resolve => {
  const id = ++sequence;
  pending.set(id, resolve);
  child.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method,params}) + '\n');
});
const tool = async (name, args) => {
  const response = await rpc('tools/call', {name,arguments:args});
  const payload = JSON.parse(response.result.content.find(v => v.type === 'text').text);
  assert.notEqual(response.result.isError, true, payload.error);
  assert.equal(payload.exit_code, 0);
  return payload.result;
};
try {
  const init = await rpc('initialize', {protocolVersion:'2025-03-26',capabilities:{},clientInfo:{name:'gace-project-route-verify',version:'1'}});
  assert.equal(init.result.serverInfo.name, 'debugai');
  child.stdin.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'}) + '\n');
  const names = (await rpc('tools/list', {})).result.tools.map(v => v.name);
  assert.deepEqual(names, ['debugai_health','debugai_analyze','debugai_start','debugai_resume','debugai_wait','debugai_patch_candidate','debugai_verify','debugai_status','debugai_inspect','debugai_server_read','debugai_server_status','debugai_gitops_request','debugai_gitops_status']);
  console.log('MCP_TOOL_DISCOVERY=PASS');
  const health = await tool('debugai_health', {});
  assert.equal(health.ok, true);
  assert.equal(health.guarded_gitops, true);
  console.log('DEBUGAI_HEALTH=PASS');
  const rejected = await rpc('tools/call', {name:'debugai_gitops_request',arguments:{action:'deploy',human_approved:false}});
  assert.equal(rejected.result.isError, true);
  assert.equal(JSON.parse(rejected.result.content[0].text).error, 'GITOPS_HUMAN_APPROVAL_REQUIRED');
  console.log('GUARDED_GITOPS_UNAPPROVED_REQUEST=REJECTED');
  const q = await tool('debugai_server_read', {command_id:'project.git_head'});
  assert.equal(q.state, 'QUEUED');
  console.log('SERVER_COMMAND_REQUEST=PASS');
  console.log(`REQUEST_ID=${q.id}`);
  const deadline = Date.now() + 15000;
  let final;
  while (Date.now() < deadline) {
    final = await tool('debugai_server_status', {id:q.id});
    console.log(`SERVER_COMMAND_STATE=${final.state}`);
    if (final.state === 'PASS' || final.state === 'FAIL') break;
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  assert.equal(final.state, 'PASS', final.error);
  assert.equal(final.id, q.id);
  assert.equal(final.result.read_only, true);
  assert.equal(final.result.stdout, process.env.GACE_EXPECTED_HEAD);
  assert.ok(final.started_at <= final.finished_at);
  console.log(`EXACT_SERVER_HEAD=${final.result.stdout}`);
  console.log('SERVER_COMMAND_STATUS=PASS');
  console.log('HOST_RUNNER_EXECUTION=PASS');
  console.log('EXACT_SERVER_READBACK=PASS');
  console.log('PROJECT_COMMON_SERVER_E2E=PASS');
} finally {
  clearTimeout(timer);
  child.kill();
}
JS
