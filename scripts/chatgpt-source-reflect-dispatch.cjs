"use strict";
const fs = require("node:fs");

const DELEGATION_ID = "dlg_master_servercore_reflect_v1";
const REGISTERED_REPOSITORY = "G-ACE-inc/server-core";
const REGISTERED_BRANCH = "main";
const REGISTERED_SCOPE = "gace.source.reflect";
const REGISTERED_RUNTIME = "servercore.source";

const IDLE_READ_COMMANDS = new Set([
  "",
  "project.git_head",
  "project.git_status",
  "service.debug_ai_state",
  "service.debug_ai_health",
  "system.projects_inventory",
  "system.disk_usage",
  "project.git_changed_paths",
  "system.project_file_inspect",
  "service.registered_container_logs",
  "service.debug_ai_logs",
  "service.sandbox_state",
  "project.git_recent_commits",
  "project.python_unittest",
]);

const REFLECT_TRIGGER_BRANCHES = new Set([
  "main",
  "feat/chat-actions-client-migration-20261011",
]);

function loadJson(path) {
  return JSON.parse(fs.readFileSync(path, "utf8"));
}

function findDelegation(registry, id) {
  const list = registry.repositories ?? registry.delegations ?? [];
  return list.find((item) => item.id === id) ?? null;
}

function assertReflectShape(reflect) {
  if (!reflect || typeof reflect !== "object" || reflect.enabled !== true) {
    throw new Error("SOURCE_REFLECT_SHAPE_INVALID");
  }
  const keys = Object.keys(reflect).sort();
  const expected = ["branch", "delegation_id", "enabled", "repository", "runtime_target", "sha"].sort();
  if (keys.join("|") !== expected.join("|")) throw new Error("SOURCE_REFLECT_KEYS_INVALID");
  const shaVal=String(reflect.sha||"");
  if (shaVal!=="GITHUB_WORKFLOW_SHA"&&!/^[0-9a-f]{40}$/.test(shaVal)) throw new Error("SOURCE_REFLECT_SHA_INVALID");
  if (!/^[A-Za-z0-9._/-]{1,160}$/.test(String(reflect.branch || "")) || reflect.branch.startsWith("-") || reflect.branch.includes("..")) {
    throw new Error("SOURCE_REFLECT_BRANCH_INVALID");
  }
  if (!/^dlg_[a-z0-9_-]{1,64}$/.test(String(reflect.delegation_id || ""))) {
    throw new Error("SOURCE_REFLECT_DELEGATION_INVALID");
  }
  if (!/^[a-z][a-z0-9_.-]{1,80}$/.test(String(reflect.runtime_target || ""))) {
    throw new Error("SOURCE_REFLECT_RUNTIME_INVALID");
  }
  if (!/^[A-Za-z0-9_-]+\/[A-Za-z0-9._-]+$/.test(String(reflect.repository || ""))) {
    throw new Error("SOURCE_REFLECT_REPOSITORY_INVALID");
  }
}

function validateRegisteredDelegation(reflect, delegation) {
  assertReflectShape(reflect);
  if (!delegation || delegation.enabled !== true || delegation.revoked === true) {
    throw new Error("SOURCE_REFLECT_DELEGATION_REGISTRY_DENIED");
  }
  if (reflect.delegation_id !== DELEGATION_ID || delegation.id !== DELEGATION_ID) {
    throw new Error("SOURCE_REFLECT_DELEGATION_MISMATCH");
  }
  if (reflect.repository !== REGISTERED_REPOSITORY || delegation.repository !== REGISTERED_REPOSITORY) {
    throw new Error("SOURCE_REFLECT_REPOSITORY_UNREGISTERED");
  }
  if (reflect.branch !== REGISTERED_BRANCH) throw new Error("SOURCE_REFLECT_BRANCH_REGISTRY_MISMATCH");
  if (!(delegation.allowed_branches || []).includes(REGISTERED_BRANCH)) {
    throw new Error("SOURCE_REFLECT_BRANCH_NOT_ALLOWED");
  }
  if (reflect.runtime_target !== REGISTERED_RUNTIME) throw new Error("SOURCE_REFLECT_RUNTIME_MISMATCH");
  if (!(delegation.allowed_scopes || []).includes(REGISTERED_SCOPE)) {
    throw new Error("SOURCE_REFLECT_SCOPE_REGISTRY_DENIED");
  }
  if (!(delegation.allowed_operations || []).includes("reflect")) {
    throw new Error("SOURCE_REFLECT_OPERATION_DENIED");
  }
  const runtime = delegation.runtime_target || {};
  if (runtime.id !== REGISTERED_RUNTIME) throw new Error("SOURCE_REFLECT_RUNTIME_REGISTRY_MISMATCH");
}

function validateIdleTarget(target) {
  if (target.mode !== "readonly") throw new Error("IDLE_MODE_INVALID");
  if (target.gitops_request?.enabled !== false) throw new Error("IDLE_GITOPS_MUST_BE_DISABLED");
  if (target.source_reflect_request?.enabled !== false) throw new Error("IDLE_SOURCE_REFLECT_MUST_BE_DISABLED");
  const command = target.server_command_id ?? "";
  if (!IDLE_READ_COMMANDS.has(command)) throw new Error("IDLE_READ_COMMAND_DENIED");
}

function validateDispatch({ target, route, registry, gitRefName }) {
  const current = (route.routes || []).find((item) => item.id === "route_debugai_live_read");
  if (!current) throw new Error("COMMON_ROUTE_MISSING");
  if (current.workflow_repository !== "G-ACE-inc/server-core") {
    throw new Error("MIGRATED_ROUTE_OWNER_MISMATCH");
  }
  const gitopsEnabled = target.gitops_request?.enabled === true;
  const reflectEnabled = target.source_reflect_request?.enabled === true;
  if (reflectEnabled && gitopsEnabled) throw new Error("CHAT_REFLECT_CONCURRENT_DEPLOY_DENIED");
  if (reflectEnabled && target.mode !== "readonly") throw new Error("CHAT_REFLECT_MODE_DENIED");

  if (reflectEnabled) {
    if (!REFLECT_TRIGGER_BRANCHES.has(gitRefName)) throw new Error("CHAT_SOURCE_REFLECT_TRIGGER_BRANCH_DENIED");
    const delegation = findDelegation(registry, DELEGATION_ID);
    validateRegisteredDelegation(target.source_reflect_request, delegation);
    const command = target.server_command_id ?? "";
    if (command !== "") throw new Error("SOURCE_REFLECT_SERVER_COMMAND_FORBIDDEN");
    if (target.gitops_request?.enabled !== false) throw new Error("SOURCE_REFLECT_GITOPS_MUST_BE_DISABLED");
    return { mode: "source_reflect", delegationId: DELEGATION_ID };
  }

  validateIdleTarget(target);
  const command = target.server_command_id ?? "";
  if (command) {
    const supported = current.workflow_supported_command_ids || [];
    const allowed = current.server_command?.allowed_command_ids || [];
    const effects = current.command_effects || {};
    if (!supported.includes(command) || !allowed.includes(command) || effects[command] !== "read_only") {
      throw new Error("IDLE_EFFECTIVE_ROUTE_ADMISSION_DENIED");
    }
  }
  if (gitopsEnabled) {
    throw new Error("IDLE_GITOPS_TARGET_NOT_SUPPORTED_HERE");
  }
  return { mode: "idle" };
}

function verifyDispatchCli(argv) {
  let gitRefName = "main";
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--git-ref" && argv[i + 1]) {
      gitRefName = argv[++i];
    }
  }
  const target = loadJson(".github/chatgpt-live-api-target.json");
  const route = loadJson("operations/github-project-chat-host-routes.json");
  const registry = loadJson("operations/master-internal-repositories.json");
  const result = validateDispatch({ target, route, registry, gitRefName });
  console.log("SERVER_CORE_COPY_ROUTE_PREFLIGHT=PASS");
  console.log("MIGRATED_ACTIONS_ROUTE=SERVER_CORE");
  console.log("SOURCE_REFLECT_DISPATCH_MODE=" + result.mode);
  if (result.delegationId) console.log("SOURCE_REFLECT_DELEGATION_ID=" + result.delegationId);
}

if (require.main === module) {
  const cmd = process.argv[2];
  if (cmd === "verify-dispatch") {
    try {
      verifyDispatchCli(process.argv);
    } catch (err) {
      const code = String(err.message || "UNKNOWN").replace(/[^A-Z0-9_]/g, "").slice(0, 80) || "DISPATCH_VERIFY_FAILED";
      console.error("SOURCE_REFLECT_DISPATCH_ERROR=" + code);
      process.exitCode = 1;
    }
  } else {
    console.error("USAGE: node scripts/chatgpt-source-reflect-dispatch.cjs verify-dispatch [--git-ref NAME]");
    process.exitCode = 2;
  }
}

module.exports = {
  DELEGATION_ID,
  REGISTERED_REPOSITORY,
  REGISTERED_BRANCH,
  REGISTERED_RUNTIME,
  REGISTERED_SCOPE,
  REFLECT_TRIGGER_BRANCHES,
  validateDispatch,
  validateRegisteredDelegation,
  validateIdleTarget,
  assertReflectShape,
};
