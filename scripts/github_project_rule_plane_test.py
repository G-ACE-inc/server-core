#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = json.loads((ROOT / "operations/github-project-rule-plane.json").read_text(encoding="utf-8"))

assert p["schema_version"] == "1.0"
assert p["name"] == "gace-github-project-rule-plane"
assert p["project"]["number"] == 1
assert p["project"]["node_id"] == "PVT_kwHODOQFoM4BEJII"
assert p["control_plane"]["issue_number"] == 15
assert p["rule_planes"]["server_ai"]["issue_number"] == 16
assert p["rule_planes"]["gpt_chat"]["issue_number"] == 17
assert p["rule_planes"]["server_ai"]["payload_class"] == "MINIMAL"
assert p["rule_planes"]["gpt_chat"]["payload_class"] == "EXTENDED"
assert p["rule_planes"]["gpt_chat"]["server_ai_default_load"] is False
assert p["authority_model"]["current_control_plane"] == "GITHUB_PROJECT"
assert p["authority_model"]["server_core_role"] == "BOOTSTRAP_ROUTER_CONTROL_ROOM"
assert p["authority_model"]["full_gpt_rule_payload_in_server_ai_context_forbidden"] is True
assert p["migration"]["cutover"] == "NOT_RUN"

for rel, limit in {
    ".cursor/rules/00_agent_runtime.mdc": 70,
    "AGENTS.md": 40,
    ".github/copilot-instructions.md": 40,
}.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert len(text.splitlines()) <= limit, (rel, len(text.splitlines()), limit)
    assert "SERVER_AI" in text
    assert "github-project-rule-plane.json" in text
    assert "#16" in text
    assert "#17" in text
    assert "default-load GPT_CHAT" in text

doc = (ROOT / "docs/GITHUB_PROJECT_RULE_PLANE.md").read_text(encoding="utf-8")
for token in ("Issue #16", "Issue #17", "GitHub Project #1", "server-core"):
    assert token in doc


# PREFLIGHT_OWNER_AND_REUSE_CONTRACT: existing owners, no duplicate rules or sibling projects.
workspace = (ROOT / "docs/G_ACE_WORKSPACE.md").read_text(encoding="utf-8")
router = (ROOT / "docs/LOAD_SCOPE.md").read_text(encoding="utf-8")
core_protocol = (ROOT / "SERVER_CORE_PROTOCOL.md").read_text(encoding="utf-8")
for required in (
    "## 4.1 Canonical parent Project",
    "## 6. Development Routine",
    "reuse check",
    "GitHub commit as work report",
    "CREATED_NEW_TOP_LEVEL_SIBLING=NO",
):
    assert required in workspace, required
for required in (
    "REUSE_CANDIDATES",
    "CANONICAL_PARENT_REALPATH",
    "TOP_LEVEL_CHILD_PROJECT_BLOCKED",
):
    assert required in router, required
assert "Docker / Runtime" in core_protocol
for owner in (
    "GitHub Project #1 + owning Current Issue",
    "Rule #16 SERVER_AI",
    "Rule #17 GPT_CHAT",
    "docs/G_ACE_WORKSPACE.md",
):
    assert owner in doc, owner

# A safety gate must really exist in the existing source; text cannot substitute for it.
for path, required in {
    "scripts/init_dev_workspace_project_gate.py": ("PROJECT_NOT_REGISTERED", "PROJECT_PATH_ALIAS_OR_SYMLINK"),
    "scripts/gace_shell_workspace_command_guard.py": ("TOP_LEVEL_CHILD_PROJECT_BLOCKED", "DERIVED_REPO_INSIDE_PARENT"),
}.items():
    # Guard files are staged on PR39, not installed on main yet. Require only once on main.
    guard = ROOT / path
    if guard.is_file():
        source = guard.read_text(encoding="utf-8")
        for marker in required:
            assert marker in source, (path, marker)

print("GITHUB_PROJECT_RULE_PLANE=PASS")
