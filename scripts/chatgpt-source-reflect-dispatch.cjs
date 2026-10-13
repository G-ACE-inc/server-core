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

const BOUNDED_HOST_CONTRACT_PATH = "operations/github-project-bounded-host.json";

function assertBoundedHostShape(request) {
  if (!request || typeof request !== "object" || request.enabled !== true) {
    throw new Error("BOUNDED_HOST_SHAPE_INVALID");
  }
  const keys = Object.keys(request).sort();
  const expected = request.command_id === "project.source_reflect"
    ? ["command_id", "enabled", "expected_before", "expected_sha"].sort()
    : request.command_id === "service.deploy"
      ? ["command_id", "enabled", "expected_sha", "repository", "service"].sort()
      : request.command_id === "docker.operation"
        ? ["argv", "command_id", "enabled", "expected_sha", "operation", "repository", "service", "tail"].sort()
      : request.command_id === "host.command"
        ? ["command", "command_id", "enabled", "expected_sha", "repo_sha", "repository"].sort()
      : request.command_id === "service.deploy_status"
        ? ["command_id", "deploy_request_id", "enabled", "expected_sha"].sort()
        : request.command_id === "project.file_inspect"
          ? ["command_id", "enabled", "expected_sha", "offset", "path"].sort()
          : request.command_id === "docker.logs"
            ? ["command_id", "container", "enabled", "expected_sha", "tail"].sort()
            : request.command_id === "dev.job"
              ? (Object.hasOwn(request, "repo_sha")
                ? ["argv", "command_id", "enabled", "expected_sha", "fresh", "repo_sha", "repository", "session", "timeout_s"].sort()
                : ["argv", "command_id", "enabled", "expected_sha", "fresh", "repository", "session", "timeout_s"].sort())
              : ["command_id", "enabled", "expected_sha"].sort();
  if (keys.join("|") !== expected.join("|")) throw new Error("BOUNDED_HOST_KEYS_INVALID");
  if (request.command_id === "project.source_reflect" &&
      !/^[0-9a-f]{40}$/.test(String(request.expected_before || ""))) {
    throw new Error("BOUNDED_HOST_BEFORE_SHA_INVALID");
  }
  if (request.command_id === "service.deploy") {
    if (!/^[A-Za-z0-9][A-Za-z0-9_.-]*\/[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(String(request.repository || "")) ||
        !/^[a-z0-9][a-z0-9_-]{0,62}$/.test(String(request.service || ""))) {
      throw new Error("BOUNDED_HOST_DEPLOY_TARGET_INVALID");
    }
  }
  if (request.command_id === "docker.operation") {
    const allowed = new Set(["ps", "inspect", "logs", "stats", "start", "stop", "restart", "up", "exec"]);
    if (!/^[A-Za-z0-9][A-Za-z0-9_.-]*\/[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(String(request.repository || "")) ||
        !/^[a-z0-9][a-z0-9_-]{0,62}$/.test(String(request.service || "")) ||
        !allowed.has(request.operation)) throw new Error("BOUNDED_HOST_DOCKER_TARGET_INVALID");
    if (!Array.isArray(request.argv) || request.argv.length > 10 ||
        request.argv.some(a => typeof a !== "string" || a.length < 1 || a.length > 512) ||
        request.argv.join("").length > 1000 ||
        (request.operation === "exec") !== (request.argv.length > 0) ||
        !Number.isInteger(request.tail) || request.tail < 1 || request.tail > 200) {
      throw new Error("BOUNDED_HOST_DOCKER_ARGV_INVALID");
    }
  }
  if (request.command_id === "host.command" &&
      (!/^[A-Za-z0-9][A-Za-z0-9_.-]*\/[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(String(request.repository || "")) ||
       !/^[0-9a-f]{40}$/.test(String(request.repo_sha || "")) ||
       typeof request.command !== "string" || request.command.length < 1 || request.command.length > 1600 ||
       request.command.includes("\\x00"))) {
    throw new Error("BOUNDED_HOST_TERMINAL_TARGET_INVALID");
  }
  if (request.command_id === "service.deploy_status" &&
      !/^req_[0-9a-f]{24}$/.test(String(request.deploy_request_id || ""))) {
    throw new Error("BOUNDED_HOST_DEPLOY_REQUEST_ID_INVALID");
  }
  if (request.command_id === "project.file_inspect" &&
      (!/^[A-Za-z0-9_.][A-Za-z0-9_./-]{0,159}$/.test(String(request.path || "")) || String(request.path).includes("..") ||
       !Number.isInteger(request.offset) || request.offset < 0 || request.offset > 4000000)) {
    throw new Error("BOUNDED_HOST_FILE_TARGET_INVALID");
  }
  if (request.command_id === "docker.logs" &&
      (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(String(request.container || "")) ||
       !Number.isInteger(request.tail) || request.tail < 1 || request.tail > 200)) {
    throw new Error("BOUNDED_HOST_LOG_TARGET_INVALID");
  }
  if (request.command_id === "dev.job" &&
      (!/^[A-Za-z0-9][A-Za-z0-9_.-]*\/[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(String(request.repository || "")) ||
       !/^req_[0-9a-f]{24}$/.test(String(request.session || "")) ||
       !Array.isArray(request.argv) || request.argv.length < 1 || request.argv.length > 8 ||
       request.argv.some((a) => typeof a !== "string" || a.length < 1 || a.length > 1200) ||
       !Number.isInteger(request.timeout_s) || request.timeout_s < 1 || request.timeout_s > 15 ||
       typeof request.fresh !== "boolean")) {
    throw new Error("BOUNDED_HOST_JOB_TARGET_INVALID");
  }
  if (request.command_id === "dev.job" && Object.hasOwn(request, "repo_sha") &&
      (typeof request.repo_sha !== "string" || !/^[0-9a-f]{40}$/.test(request.repo_sha))) {
    throw new Error("BOUNDED_HOST_REPO_SHA_INVALID");
  }
  const shaVal = String(request.expected_sha || "");
  // Service deploy targets another repository: never the workflow SHA alias.
  if (shaVal === "GITHUB_WORKFLOW_SHA" && String(request.command_id || "").startsWith("service.deploy")) {
    throw new Error("BOUNDED_HOST_DEPLOY_SHA_EXPLICIT_REQUIRED");
  }
  if (shaVal !== "GITHUB_WORKFLOW_SHA" && !/^[0-9a-f]{40}$/.test(shaVal)) {
    throw new Error("BOUNDED_HOST_SHA_INVALID");
  }
  if (!/^[a-z][a-z0-9_.-]{1,80}$/.test(String(request.command_id || ""))) {
    throw new Error("BOUNDED_HOST_COMMAND_INVALID");
  }
}

function validateBoundedHostRequest(request, contract) {
  assertBoundedHostShape(request);
  const allowed = new Set(contract.allowed_command_ids || []);
  if (!allowed.has(request.command_id)) throw new Error("BOUNDED_HOST_COMMAND_DENIED");
  const effects = contract.command_effects || {};
  if (!["read_only", "source_reflect", "service_deploy", "dev_job", "registered_container_operation", "registered_host_command"].includes(effects[request.command_id])) throw new Error("BOUNDED_HOST_EFFECT_DENIED");
}

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
  const gitopsEnabled = target.gitops_request?.enabled === true;
  const reflectEnabled = target.source_reflect_request?.enabled === true;
  const boundedHostEnabled = target.bounded_host_request?.enabled === true;
  if (reflectEnabled && gitopsEnabled) throw new Error("CHAT_REFLECT_CONCURRENT_DEPLOY_DENIED");
  if (reflectEnabled && target.mode !== "readonly") throw new Error("CHAT_REFLECT_MODE_DENIED");
  if (boundedHostEnabled && (reflectEnabled || gitopsEnabled)) {
    throw new Error("BOUNDED_HOST_CONCURRENT_OPERATION_DENIED");
  }
  if (boundedHostEnabled && (target.server_command_id ?? "") !== "") {
    throw new Error("BOUNDED_HOST_DEBUGAI_COMMAND_FORBIDDEN");
  }

  if (boundedHostEnabled) {
    if (target.mode !== "readonly") throw new Error("BOUNDED_HOST_MODE_DENIED");
    if (!REFLECT_TRIGGER_BRANCHES.has(gitRefName)) throw new Error("BOUNDED_HOST_TRIGGER_BRANCH_DENIED");
    const hostContract = loadJson(BOUNDED_HOST_CONTRACT_PATH);
    validateBoundedHostRequest(target.bounded_host_request, hostContract);
    return { mode: "bounded_host", commandId: target.bounded_host_request.command_id };
  }

  // Independent bounded Host does not require the DebugAI product route.
  const current = (route.routes || []).find((item) => item.id === "route_debugai_live_read");
  if (!current) throw new Error("COMMON_ROUTE_MISSING");
  if (current.workflow_repository !== "G-ACE-inc/server-core") {
    throw new Error("MIGRATED_ROUTE_OWNER_MISMATCH");
  }

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
  if (result.commandId) console.log("BOUNDED_HOST_DISPATCH_COMMAND=" + result.commandId);
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
  BOUNDED_HOST_CONTRACT_PATH,
  validateDispatch,
  validateRegisteredDelegation,
  validateIdleTarget,
  validateBoundedHostRequest,
  assertReflectShape,
  assertBoundedHostShape,
};
