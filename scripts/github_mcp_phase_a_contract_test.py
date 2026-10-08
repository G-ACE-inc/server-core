#!/usr/bin/env python3
"""Deterministic Phase-A contract: network egress model, client limits, no workspace advert."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "operations/github-mcp-readonly-runtime.json"
WORKSPACE_MCP = ROOT / "operations/workspace-mcp.json"
ROUTING = ROOT / "operations/github-project-debugai-routing.json"
COMPOSE = (ROOT / "docker-compose.github-mcp-readonly.yml").read_text(encoding="utf-8")
ADMISSION = (ROOT / "docs/GITHUB_MCP_PHASE_A_ADMISSION.md").read_text(encoding="utf-8")


def main() -> None:
    runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
    assert runtime["network"]["docker_internal_isolation_flag"] is False
    assert runtime["network"]["host_port_publish"] is False
    assert runtime["authentication"]["shared_pat_in_compose"] is False
    assert runtime["client_contract"]["debugai_compose_on_gace_internal"] is False

    workspace = json.loads(WORKSPACE_MCP.read_text(encoding="utf-8"))
    servers = workspace.get("servers", {})
    forbidden_keys = ("github-mcp", "github_mcp", "gace-github-mcp", "gace_github_mcp")
    for key in servers:
        assert key not in forbidden_keys, ("WORKSPACE_MCP_PREMATURE_ADVERT", key)
        assert "github-mcp-server" not in json.dumps(servers[key]).lower()

    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    blob = json.dumps(routing)
    assert "debugai" in blob.lower()

    assert "rollback" in ADMISSION.lower()
    assert "gace-internal" in ADMISSION
    assert "--internal" in ADMISSION
    assert "api.github.com" in ADMISSION

    assert "Docker Host" in ADMISSION
    assert runtime["network"]["inbound_policy"].startswith("no_host_port_publish")
    assert runtime["network"].get("host_network_mode") is False
    ha = runtime.get("host_admission", {})
    assert ha.get("legacy_debugai_one_shot_supports_phase_a") is False
    ci = runtime.get("ci_verification", {})
    assert ci.get("mcp_authenticated_projects_on_bridge") == "NOT_VERIFIED_ADMISSION_GATE"

    assert "\n    ports:" not in COMPOSE
    assert "internal: true" not in COMPOSE

    print("GITHUB_MCP_PHASE_A_CONTRACT=PASS")
    print("WORKSPACE_MCP_GITHUB_SERVER_ABSENT=PASS")
    print("DEBUGAI_ON_GACE_INTERNAL=NO")


if __name__ == "__main__":
    main()
