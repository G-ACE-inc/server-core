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


workspace = (ROOT / "docs/G_ACE_WORKSPACE.md").read_text(encoding="utf-8")
router = (ROOT / "docs/LOAD_SCOPE.md").read_text(encoding="utf-8")

# The one canonical Current/work-location gate must be routed before source creation.
for required in (
    "## 4.2 Mandatory work location and reuse handoff gate",
    "OWNER_PROJECT / OWNER_REPOSITORY / CANONICAL_PARENT_REALPATH",
    "CURRENT_ISSUE / MISSION / CHANGE_UNIT / MUTATION_OWNER",
    "REUSE_CANDIDATES:",
    "PREFLIGHT_LOCATION_UNVERIFIED",
    "HANDOFF_RECORDED",
):
    assert required in workspace, required
for required in (
    "### 3.2 Current/work-location preflight",
    "PREFLIGHT_LOCATION_UNVERIFIED",
    "EXACT_NEXT_GATE",
):
    assert required in router, required

# Keep the existing design authority attached to the execution route.
# These are contract presence checks, not proof that an agent read a specific design.
for marker in (
    "### Design-alignment checks within the existing Work Routine",
    "DESIGN_BASELINE_NOT_VERIFIED",
    "DESIGN_DRIFT_REVIEW_REQUIRED",
    "initial diff, before PR/merge",
):
    assert marker in workspace, ("WORK_ROUTINE_DESIGN_GATE_MISSING", marker)
for marker in (
    "### Design baseline / anti-drift routing",
    "DESIGN_BASELINE_NOT_VERIFIED",
    "DESIGN_DRIFT_REVIEW_REQUIRED",
):
    assert marker in router, ("DESIGN_ROUTER_GATE_MISSING", marker)

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
    "SERVER_AI Issue #16",
    "GPT CHAT Issue #17",
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

# Both entrypoints must route CHAT through Manifest and complete #17, not a snippet.
readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert "operations/github-project-rule-plane.json (Fresh main Manifest; confirm GPT_CHAT profile)" in readme
assert "fetch complete Rule Plane #17 body" in readme
assert "apply #17 pre-action and continuation/report gates" in readme
assert "Fetch the COMPLETE canonical Issue #17 body" in router
assert "recover truncated/missing content" in router
assert "progress messages do not end work" in router
assert "do not pass #17 to SERVER_AI/Composer/Codex" in router

# Ordering regression: CHAT Manifest must precede FULL #17, and #17 precede Current.
chat_entry = readme.split("GPT_CHAT / ChatGPT Work coordinator", 1)[1].split("```", 1)[0]
assert chat_entry.index("operations/github-project-rule-plane.json") < chat_entry.index("fetch complete Rule Plane #17 body") < chat_entry.index("GitHub Project #1 / Control #15")
chat_route = router.split("### GPT_CHAT / ChatGPT Work", 1)[1].split("```", 2)[1]
assert chat_route.index("operations/github-project-rule-plane.json") < chat_route.index("Fetch the COMPLETE canonical Issue #17 body") < chat_route.index("GitHub Project #1 / Control #15")
