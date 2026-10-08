#!/usr/bin/env python3
"""Fail-closed source contract for optional, isolated official GitHub MCP runtime."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = (ROOT / "docker-compose.github-mcp-readonly.yml").read_text(encoding="utf-8")
CORE = (ROOT / "docker-compose.project-control.yml").read_text(encoding="utf-8")
CI = (ROOT / ".github/workflows/github-project-control-verify.yml").read_text(encoding="utf-8")

RUNTIME = (ROOT / "operations/github-mcp-readonly-runtime.json").read_text(encoding="utf-8")


def assert_config() -> None:
    required = [
        "gace-github-mcp-readonly:",
        "ghcr.io/github/github-mcp-server@sha256:",
        "ghcr.io/github/github-mcp-server@sha256:fbec75de11c255213fa08d80fb166abe73d851fff631c51c0079872967720699",
        'command: ["http", "--listen-host", "0.0.0.0", "--scope-challenge"]',
        "GITHUB_TOOLSETS: projects",
        'GITHUB_READ_ONLY: "1"',
        "read_only: true",
        "no-new-privileges:true",
        "cap_drop:",
        "- ALL",
        "gace-internal:",
        "external: true",
        "expose:",
        '- "8082"',
        "Shared GitHub MCP source-only config",
    ]
    for needle in required[:-1]:
        assert needle in COMPOSE, ("MCP_REQUIRED_INVARIANT_MISSING", needle)
    assert required[-1] in CI, "MCP_CONFIG_NOT_TESTED_BY_CI"
    assert "gace-internal:" in CORE, "MCP_NETWORK_NOT_REUSED"
    # No host ports, privileged Docker daemon, static credentials or mutable tags.
    for forbidden in (
        "\n    ports:", "network_mode: host", "privileged: true",
        "docker.sock", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "GITHUB_MCP_SERVER_MRTR_STATE_KEY", "image: ghcr.io/github/github-mcp-server:latest",
    ):
        assert forbidden not in COMPOSE, ("MCP_SOURCE_BOUNDARY_VIOLATION", forbidden)
    assert COMPOSE.count("GITHUB_READ_ONLY:") == 1, "MCP_READ_ONLY_CONFIG_CHANGED"
    assert COMPOSE.count("GITHUB_TOOLSETS:") == 1, "MCP_TOOLSET_CONFIG_CHANGED"

    import json as _json
    _rt = _json.loads(RUNTIME)
    assert _rt["network"]["docker_internal_isolation_flag"] is False
    assert "github_mcp_phase_a_contract_test.py" in CI
    assert "github_mcp_ci_acceptance_matrix_test.py" in CI
    assert "github_mcp_ci_bridge_egress_verify.sh" in CI

    print("SHARED_GITHUB_MCP_SOURCE_CONTRACT=PASS")
    print("GITHUB_MCP_RUNTIME_DEPLOYED=NO")


if __name__ == "__main__":
    assert_config()
