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

print("GITHUB_PROJECT_RULE_PLANE=PASS")
