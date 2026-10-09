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

# Static source regression checks only: effective client loading and Host enforcement
# need separate live E2E evidence. Keep the routine canonical in the Workspace doc.
workspace = (ROOT / "docs/G_ACE_WORKSPACE.md").read_text(encoding="utf-8")
router = (ROOT / "docs/LOAD_SCOPE.md").read_text(encoding="utf-8")
for token in (
    "## 6. Development Routine",
    "### Mission / Change Unit pre-dispatch",
    "MISSION",
    "IN_SCOPE / OUT_OF_SCOPE",
    "CURRENT_CHANGE_UNIT",
    "MUTATION_OWNER",
    "ACCEPTANCE",
    "EXACT_NEXT_GATE",
    "CURRENT_REFERENCE",
    "SCOPE_DRIFT_BLOCKED",
    "block only that mismatched mutation/delegation",
):
    assert token in workspace, ("missing routine/mission preflight", token)

for token in (
    "## Shared Work Routine ownership and scope-drift gate",
    "G_ACE_WORKSPACE.md",
    "Wave / Gate / Change Unit / Mutation Owner",
    "owning canonical Current Issue",
    "only its own",
):
    assert token in doc, ("missing shared routine routing", token)

assert "Project-list containment gate" in router
assert "TOP_LEVEL_CHILD_PROJECT_BLOCKED" in router
assert "ALLOWED_IN_PARENT=" in workspace
assert "DENIED_AS_SIBLING=" in workspace
assert "worktree" in workspace.lower()
assert "RULE_PLANE_CURRENT=NOT_VERIFIED" in (ROOT / ".cursor/rules/00_agent_runtime.mdc").read_text(encoding="utf-8")
assert set(json.loads((ROOT / "operations/github-project-control.json").read_text(encoding="utf-8"))["allowed_fields"]) == {
    "Wave", "Gate", "Change Unit", "Mutation Owner"
}

# Rule/file ownership has one normative source. Keep obsolete runtime evidence
# in one historical location, never in multiple bootstrap/registry entries.
readme = (ROOT / "README.md").read_text(encoding="utf-8")
registry = (ROOT / "docs/WORKSPACE_REGISTRY.md").read_text(encoding="utf-8")
mcp_doc = (ROOT / "docs/WORKSPACE_MCP.md").read_text(encoding="utf-8")
history_marker = "## Master Internal Persistent Delegation — Runtime verified (2026-10-08)"
assert history_marker not in readme, "stale live-runtime report copied into README"
assert history_marker not in registry, "stale live-runtime report copied into Registry"
assert mcp_doc.count(history_marker) == 1, "historical runtime evidence must have one copy"
assert mcp_doc.index("## Purpose") < mcp_doc.index(history_marker)
assert "DebugAI #41" in readme
assert "WORKSPACE_MCP.md" in registry
assert "## One owner per file type" in doc
for name in (
    "GitHub Project #1 + owning Current Issue",
    "Rule #16 SERVER_AI",
    "Rule #17 GPT_CHAT",
    "SERVER_CORE_PROTOCOL.md",
    "docs/G_ACE_WORKSPACE.md",
    "AGENTS.md",
    "copilot-instructions.md",
    ".cursor/mcp.json",
):
    assert name in doc, ("missing responsibility owner", name)
assert "### Execution responsibility" in workspace
assert "### Master-specific operating roles" not in workspace, (
    "do not duplicate detailed GPT_CHAT-only execution profile in shared routine"
)

print("GITHUB_PROJECT_RULE_PLANE=PASS")
