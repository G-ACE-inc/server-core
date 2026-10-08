#!/usr/bin/env python3
"""CI vs admission gates for GitHub MCP Phase A (no credentials in CI)."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = json.loads(
    (ROOT / "operations/github-mcp-readonly-runtime.json").read_text(encoding="utf-8")
)
BRIDGE = (ROOT / "scripts/github_mcp_ci_bridge_egress_verify.sh").read_text(encoding="utf-8")


def main() -> None:
    ci = RUNTIME.get("ci_verification", {})
    assert ci.get("bridge_sidecar_https_egress") == "github_actions_verify_job"
    assert ci.get("mcp_authenticated_projects_on_bridge") == "NOT_VERIFIED_ADMISSION_GATE"
    assert ci.get("persistent_host_runtime") == "NOT_VERIFIED"
    assert "NETWORK_INCONCLUSIVE=YES" in BRIDGE
    assert "fail_inconclusive_egress" in BRIDGE
    assert "assert_no_published_host_ports" in BRIDGE
    assert "readback=zero_host_port_bindings" in BRIDGE
    assert "GITHUB_MCP_MCP_PROJECTS_ON_BRIDGE=NOT_VERIFIED" in BRIDGE

    env = os.environ.copy()
    env["GACE_MCP_EGRESS_PROBE_URL"] = "http://127.0.0.1:9/unreachable"
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts/github_mcp_ci_bridge_egress_verify.sh"), "--egress-probe-only"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0, ("EGRESS_NEGATIVE_FIXTURE_MUST_FAIL", proc.stdout, proc.stderr)
    assert "NETWORK_INCONCLUSIVE=YES" in proc.stdout + proc.stderr

    print("GITHUB_MCP_CI_ACCEPTANCE_MATRIX=PASS")
    print("GITHUB_MCP_EGRESS_NEGATIVE_FIXTURE=PASS")


if __name__ == "__main__":
    main()
