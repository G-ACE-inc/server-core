#!/usr/bin/env python3
"""Deterministic tests for static CHAT dispatch and real GitHub log evidence."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/github_project_chat_host_route.py"
REQUEST_ID = "cmd_ffbd9cb5f1ecacad2f814676"


def load_mod():
    spec = importlib.util.spec_from_file_location("route", MODULE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dispatch(**overrides):
    params = dict(
        route_id="route_debugai_live_read",
        repository="seigo-gace/debug-ai",
        command_id="project.git_head",
        execution_repo="/workspace/debug-ai",
        project_control_url="https://github.com/seigo-gace/debug-ai/issues/41",
        branch="feat/tgserver-async-log-sink-20261003",
    )
    params.update(overrides)
    return load_mod().validate_dispatch(**params)


def test_debugai_route_pass():
    out = dispatch()
    assert out["result"] == "PASS"
    assert out["static_preflight_only"] is True
    assert out["host_authorization_verified"] is False
    assert out["read_only"] is True


def test_unauthorized_repo():
    assert dispatch(repository="evil/other")["error"] == "WORKFLOW_REPOSITORY_MISMATCH"


def test_unknown_command():
    assert dispatch(command_id="shell.rm_rf")["error"] == "COMMAND_NOT_ALLOWLISTED"


def test_execution_repo_forbidden():
    assert dispatch(execution_repo="/etc/passwd")["error"] == "EXECUTION_REPO_FORBIDDEN"
    assert dispatch(execution_repo="/workspace/debug-ai/other")["error"] == "EXECUTION_REPO_FORBIDDEN"


def test_project_control_mismatch():
    assert dispatch(project_control_url="https://github.com/G-ACE-inc/server-core/issues/10")["error"] == "PROJECT_CONTROL_URL_MISMATCH"
    assert dispatch(project_control_url=None)["error"] == "PROJECT_CONTROL_URL_REQUIRED"


def test_branch_mismatch():
    assert dispatch(branch=None)["error"] == "WORKFLOW_BRANCH_REQUIRED"
    assert dispatch(branch="main")["error"] == "WORKFLOW_BRANCH_FORBIDDEN"


def test_real_workflow_command_support():
    assert dispatch(command_id="service.debug_ai_health")["result"] == "PASS"
    for command in (
        "service.debug_ai_logs",
        "service.debug_ai_state",
        "service.sandbox_state",
    ):
        out = dispatch(command_id=command, branch="feat/chat-gitops-request-20261009")
        assert out["result"] == "PASS"
        assert out["read_only"] is True
    for command in ("project.pwd", "project.git_status", "github.auth_status_scopes"):
        assert dispatch(command_id=command)["error"] == "COMMAND_UNSUPPORTED_BY_TRIGGER"


def test_existing_current_live_branch_and_git_history():
    assert dispatch(branch="feat/chat-gitops-request-20261009")["result"] == "PASS"
    assert dispatch(command_id="project.git_recent_commits", branch="feat/chat-gitops-request-20261009")["result"] == "PASS"
    assert dispatch(command_id="project.git_recent_commits", branch="feat/chat-gitops-request-20261009")["read_only"] is True
    assert dispatch(command_id="project.git_recent_commits", branch="main")["error"] == "WORKFLOW_BRANCH_FORBIDDEN"


def test_pr96_source_reflect_dev_branch():
    branch = "fix/gace-registered-repo-source-reflect-20261010"
    assert dispatch(branch=branch)["result"] == "PASS"
    assert dispatch(command_id="service.debug_ai_state", branch=branch)["result"] == "PASS"
    assert dispatch(branch="main")["error"] == "WORKFLOW_BRANCH_FORBIDDEN"


def test_pr36_registry_and_host_paths_retained():
    doc = json.loads((ROOT / "operations/github-project-chat-host-routes.json").read_text(encoding="utf-8"))
    route = next(item for item in doc["routes"] if item["id"] == "route_debugai_live_read")
    allowed = route["server_command"]["allowed_command_ids"]
    supported = route["workflow_supported_command_ids"]
    for command_id in (
        "system.projects_inventory",
        "system.project_file_inspect",
        "project.git_recent_commits",
        "service.debug_ai_logs",
        "service.debug_ai_state",
        "service.sandbox_state",
    ):
        assert command_id in allowed
    for command_id in ("service.debug_ai_logs", "service.debug_ai_state", "service.sandbox_state"):
        assert command_id in supported
        assert route["command_effects"][command_id] == "read_only"
    assert "fix/gace-registered-repo-source-reflect-20261010" in route["github_trigger"]["allowed_branches"]
    assert "system.projects_inventory" in supported
    assert route["command_effects"]["system.projects_inventory"] == "read_only"
    inventory = dispatch(command_id="system.projects_inventory", branch="feat/chat-gitops-request-20261009")
    assert inventory["result"] == "PASS"
    assert inventory["static_preflight_only"] is True
    assert inventory["host_authorization_verified"] is False
    assert inventory["read_only"] is True
    # Live evidence: real existing Actions/DebugAI registered-file read PASS,
    # but this static preflight is not canonical server-core Host root admission.
    assert "system.project_file_inspect" in supported
    assert route["command_effects"]["system.project_file_inspect"] == "read_only"
    for branch in ("feat/chat-gitops-request-20261009", "feat/tgserver-async-log-sink-20261003"):
        inspected = dispatch(command_id="system.project_file_inspect", branch=branch)
        assert inspected["result"] == "PASS"
        assert inspected["read_only"] is True
        assert inspected["static_preflight_only"] is True
        assert inspected["host_authorization_verified"] is False
    assert dispatch(command_id="system.project_file_inspect", branch="main")["error"] == "WORKFLOW_BRANCH_FORBIDDEN"
    assert dispatch(command_id="system.project_file_inspect", execution_repo="/home/admin1/server-core")["error"] == "EXECUTION_REPO_FORBIDDEN"
    registry = json.loads((ROOT / "operations/master-internal-repositories.json").read_text(encoding="utf-8"))
    paths = registry["repositories"][0]["allowed_paths"]
    for path in (
        "server/control/server-command-request.js",
        "scripts/host-workspace-file-inspect.py",
        "scripts/host-workspace-inventory.py",
        "scripts/host-server-command-runner.sh",
        "scripts/chatgpt-bounded-server-read.cjs",
        "operations/host-admitted-workspace-entries.json",
    ):
        assert path in paths


def test_asteria_effect_not_readonly():
    a = dict(
        route_id="route_asteria_baseline_probe",
        repository="seigo-gace/debug-ai",
        command_id="asteria.baseline_probe_start",
        project_control_url="https://github.com/seigo-gace/asteria/issues/6",
    )
    out = dispatch(**a)
    assert out["result"] == "PASS"
    assert out["read_only"] is False
    assert out["command_effect"] == "bounded_probe_start"
    assert dispatch(**dict(a, repository="seigo-gace/asteria"))["result"] == "FAIL"
    assert dispatch(**dict(a, command_id="asteria.baseline_probe_status"))["read_only"] is True


def emitted_lines(state="PASS", safety="NO"):
    return [
        f"2026-10-08T15:47:44.0197830Z SERVER_COMMAND_REQUEST_ID={REQUEST_ID}",
        "2026-10-08T15:47:44.9946873Z SERVER_HEALTH=http_status=200",
        f"2026-10-08T15:47:44.9947273Z SERVER_COMMAND_STATE={state}",
        "2026-10-08T15:47:44.9947680Z SERVER_COMMAND_READ_ONLY=TRUE",
        f"2026-10-08T15:47:45.0609515Z PRODUCTION_DEPLOY_CALLED={safety}",
        "2026-10-08T15:47:45.0608277Z APPROVE_APPLY_VERIFY_CALLED=NO",
    ]


def test_actual_github_log_timestamp_and_ansi():
    lines = [
        '2026-10-08T15:47:45.0519354Z \x1b[36;1mecho "PRODUCTION_DEPLOY_CALLED=YES"\x1b[0m',
        '2026-10-08T15:47:45.0517823Z ##[group]Run echo "SERVER_COMMAND_STATE=FAIL"',
    ] + emitted_lines()
    out = load_mod().parse_evidence(lines)
    assert out["evidence_usable_for_chat"] is True
    assert out["runtime_terminal_pass"] is True
    assert out["forbidden_markers_present"] == []
    assert out["markers"]["PRODUCTION_DEPLOY_CALLED"] == "NO"
    assert out["runtime_route_enforcement_verified"] is False


def test_forbidden_yes():
    out = load_mod().parse_evidence(emitted_lines(safety="YES"))
    assert out["forbidden_markers_present"]
    assert not out["evidence_usable_for_chat"]


def test_invalid_safety_state():
    out = load_mod().parse_evidence(emitted_lines(safety="UNKNOWN"))
    assert out["invalid_safety_markers"]
    assert not out["evidence_usable_for_chat"]


def test_terminal_fail_cannot_pass():
    out = load_mod().parse_evidence(emitted_lines(state="FAIL"))
    assert out["required_group_satisfied"]
    assert not out["runtime_terminal_pass"]
    assert not out["evidence_usable_for_chat"]


def test_nonterminal_queued_cannot_pass():
    assert not load_mod().parse_evidence(emitted_lines(state="QUEUED"))["evidence_usable_for_chat"]


def test_duplicate_conflicting_terminal_fail_closed():
    lines = emitted_lines() + ["2026-10-08T15:47:46Z SERVER_COMMAND_STATE=FAIL"]
    out = load_mod().parse_evidence(lines)
    assert out["duplicate_conflicting_markers"] == ["SERVER_COMMAND_STATE"]
    assert not out["evidence_usable_for_chat"]


def test_echo_only_no_false_pass():
    lines = [
        '2026-10-08T15:47:45.0519354Z \x1b[36;1mecho "SERVER_COMMAND_REQUEST_ID=cmd_ffbd9cb5f1ecacad2f814676"\x1b[0m',
        '2026-10-08T15:47:45.0519354Z \x1b[36;1mecho "SERVER_COMMAND_STATE=PASS"\x1b[0m',
    ]
    assert not load_mod().parse_evidence(lines)["evidence_usable_for_chat"]


def test_missing_or_malformed_request_id():
    mod = load_mod()
    assert not mod.parse_evidence([line for line in emitted_lines() if "SERVER_COMMAND_REQUEST_ID=" not in line])["evidence_usable_for_chat"]
    assert not mod.parse_evidence([line.replace(REQUEST_ID, "cmd_invalid") for line in emitted_lines()])["evidence_usable_for_chat"]


def test_host_head_readback_is_not_asteria_probe_completion():
    lines = ["2026-10-08T15:47:45Z LIVE_HEALTH=PASS", "2026-10-08T15:47:46Z LIVE_HOST_HEAD=" + "a" * 40]
    out = load_mod().parse_evidence(lines)
    assert out["runtime_terminal_pass"] is True
    assert out["runtime_route_enforcement_verified"] is False


def test_failed_command_cannot_be_masked_by_unrelated_host_head():
    lines = emitted_lines(state="FAIL") + [
        "2026-10-08T15:47:47Z LIVE_HEALTH=PASS",
        "2026-10-08T15:47:48Z LIVE_HOST_HEAD=" + "a" * 40,
    ]
    out = load_mod().parse_evidence(lines)
    assert out["required_group_satisfied"] is True
    assert out["runtime_terminal_pass"] is False
    assert out["evidence_usable_for_chat"] is False


def test_partial_command_cannot_be_masked_by_unrelated_host_head():
    lines = [line for line in emitted_lines() if "SERVER_COMMAND_STATE=" not in line] + [
        "2026-10-08T15:47:47Z LIVE_HEALTH=PASS",
        "2026-10-08T15:47:48Z LIVE_HOST_HEAD=" + "a" * 40,
    ]
    out = load_mod().parse_evidence(lines)
    assert out["runtime_terminal_pass"] is False
    assert out["evidence_usable_for_chat"] is False


def test_routing_link():
    routing = json.loads((ROOT / "operations/github-project-debugai-routing.json").read_text(encoding="utf-8"))
    assert routing["chat_github_host_routes"].endswith("github-project-chat-host-routes.json")


def main():
    tests = [func for name, func in sorted(globals().items()) if name.startswith("test_") and callable(func)]
    for test in tests:
        test()
    print(f"GITHUB_PROJECT_CHAT_HOST_ROUTE_TESTS=PASS count={len(tests)}")


if __name__ == "__main__":
    main()
