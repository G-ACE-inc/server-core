#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/github_project_chat_host_route.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("route", MODULE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_debugai_route_pass() -> None:
    mod = load_mod()
    out = mod.validate_dispatch(
        route_id="route_debugai_live_read",
        repository="seigo-gace/debug-ai",
        command_id="project.git_head",
        execution_repo="/workspace/debug-ai",
        project_control_url="https://github.com/seigo-gace/debug-ai/issues/41",
    )
    assert out["result"] == "PASS"


def test_unauthorized_repo() -> None:
    mod = load_mod()
    out = mod.validate_dispatch(
        route_id="route_debugai_live_read",
        repository="evil/other",
        command_id="project.git_head",
        execution_repo="/workspace/debug-ai",
    )
    assert out["result"] == "FAIL"


def test_unknown_command() -> None:
    mod = load_mod()
    out = mod.validate_dispatch(
        route_id="route_debugai_live_read",
        repository="seigo-gace/debug-ai",
        command_id="shell.rm_rf",
        execution_repo="/workspace/debug-ai",
    )
    assert out["error"] == "COMMAND_NOT_ALLOWLISTED"


def test_execution_repo_forbidden() -> None:
    mod = load_mod()
    out = mod.validate_dispatch(
        route_id="route_asteria_baseline_probe",
        repository="seigo-gace/debug-ai",
        command_id="asteria.baseline_probe_start",
        execution_repo="/etc/passwd",
    )
    assert out["result"] == "FAIL"


def test_project_control_mismatch() -> None:
    mod = load_mod()
    out = mod.validate_dispatch(
        route_id="route_debugai_live_read",
        repository="seigo-gace/debug-ai",
        command_id="project.git_head",
        execution_repo="/workspace/debug-ai",
        project_control_url="https://github.com/G-ACE-inc/server-core/issues/10",
    )
    assert out["error"] == "PROJECT_CONTROL_URL_MISMATCH"


def test_evidence_forbidden_marker() -> None:
    mod = load_mod()
    ev = mod.parse_evidence(["PRODUCTION_DEPLOY_CALLED=YES"])
    assert ev["forbidden_markers_present"]


def test_evidence_success_shape() -> None:
    mod = load_mod()
    lines = [
        "SERVER_COMMAND_REQUEST_ID=cmd_b805d7874776b23202e4dd5f",
        "SERVER_COMMAND_STATE=PASS",
        "SERVER_COMMAND_READ_ONLY=TRUE",
    ]
    ev = mod.parse_evidence(lines)
    assert ev["evidence_usable_for_chat"]
    assert ev["runtime_terminal_pass"]


def test_routing_link() -> None:
    routing = json.loads((ROOT / "operations/github-project-debugai-routing.json").read_text())
    assert routing["chat_github_host_routes"].endswith("github-project-chat-host-routes.json")


def main() -> None:
    test_debugai_route_pass()
    test_unauthorized_repo()
    test_unknown_command()
    test_execution_repo_forbidden()
    test_project_control_mismatch()
    test_evidence_forbidden_marker()
    test_evidence_success_shape()
    test_routing_link()
    print("GITHUB_PROJECT_CHAT_HOST_ROUTE_TESTS=PASS")


if __name__ == "__main__":
    main()
