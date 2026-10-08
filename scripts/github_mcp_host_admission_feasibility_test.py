#!/usr/bin/env python3
"""Read-only Source contract: Phase A Host admission feasibility (no Host deploy)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = json.loads(
    (ROOT / "operations/github-mcp-readonly-runtime.json").read_text(encoding="utf-8")
)
MASTER = json.loads(
    (ROOT / "operations/master-internal-repositories.json").read_text(encoding="utf-8")
)
ADMISSION = (ROOT / "docs/GITHUB_MCP_PHASE_A_ADMISSION.md").read_text(encoding="utf-8")
RUNNER_SNIP = (
    Path("/home/admin1/projects/debug-ai/scripts/host-gitops-runner.sh").read_text(
        encoding="utf-8", errors="replace"
    )
    if Path("/home/admin1/projects/debug-ai/scripts/host-gitops-runner.sh").is_file()
    else ""
)


def main() -> None:
    ha = RUNTIME["host_admission"]
    assert ha["legacy_debugai_one_shot_supports_phase_a"] is False
    assert ha["available_on_host"] is False
    assert ha["master_internal_enrolled_repository"] == "seigo-gace/debug-ai"
    assert ha["master_internal_persistent_data_effect"] is False
    assert ha["server_core_host_executor_implemented"] is False

    repos = MASTER.get("repositories", [])
    assert len(repos) == 1
    assert repos[0]["repository"] == "seigo-gace/debug-ai"
    assert repos[0]["effects"]["persistent_data"] is False

    assert "LEGACY_DEBUGAI_ONE_SHOT_SUPPORTS_PHASE_A=NO" in ADMISSION
    assert "HOST_ADMISSION_AVAILABLE=NO" in ADMISSION
    assert "Do not reuse or expand DebugAI deploy receipts" in ADMISSION

    if RUNNER_SNIP:
        assert "projects/debug-ai" in RUNNER_SNIP
        assert "gace-github-mcp-readonly" not in RUNNER_SNIP

    print("HOST_ADMISSION_AVAILABLE=NO")
    print("LEGACY_DEBUGAI_ONE_SHOT_SUPPORTS_PHASE_A=NO")
    assert (ROOT / "scripts/github_mcp_phase_a_host_bootstrap.py").is_file()
    print("GITHUB_MCP_HOST_ADMISSION_FEASIBILITY=PASS")


if __name__ == "__main__":
    main()
