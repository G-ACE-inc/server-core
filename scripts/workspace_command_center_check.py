#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


def expected_workspace(server_core: Path, projects: Path) -> dict[str, Any]:
    return {
        "folders": [{"name": "server-core", "path": str(server_core)}, {"name": "projects", "path": str(projects)}],
        "settings": {
            "files.exclude": {"**/.git": True, "**/node_modules": True, "**/dist": True, "**/build": True, "**/.next": True, "**/archive": True, "**/logs": True, "**/backups": True},
            "search.exclude": {"**/.git": True, "**/node_modules": True, "**/dist": True, "**/build": True, "**/.next": True, "**/archive": True, "**/logs": True, "**/backups": True},
            "github.copilot.chat.codeGeneration.useInstructionFiles": True,
            "chat.useAgentsMdFile": True,
        },
    }


def paths(root: Path) -> dict[str, Path]:
    server_core = root / "server-core"
    projects = root / "projects"
    return {
        "server_core": server_core,
        "projects": projects,
        "workspace_file": root / "workspace" / "G-ACE.code-workspace",
        "rules_link": projects / ".cursor" / "rules",
        "expected_rules": server_core / ".cursor" / "rules",
        "copilot_link": projects / ".github" / "copilot-instructions.md",
        "expected_copilot": server_core / ".github" / "copilot-instructions.md",
        "agents_link": projects / "AGENTS.md",
        "expected_agents": server_core / "AGENTS.md",
    }


def load_workspace(workspace_file: Path) -> dict[str, Any]:
    if not workspace_file.exists():
        return {}
    raw = json.loads(workspace_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("workspace root must be a JSON object")
    return raw


def repair(root: Path) -> None:
    p = paths(root)
    expected = expected_workspace(p["server_core"], p["projects"])
    workspace_file = p["workspace_file"]
    workspace_file.parent.mkdir(parents=True, exist_ok=True)
    actual = load_workspace(workspace_file)
    repaired = dict(actual)
    repaired["folders"] = expected["folders"]
    settings = dict(repaired.get("settings") or {})
    for section in ("files.exclude", "search.exclude"):
        merged = dict(settings.get(section) or {})
        merged.update(expected["settings"][section])
        settings[section] = merged
    for key in ("github.copilot.chat.codeGeneration.useInstructionFiles", "chat.useAgentsMdFile"):
        settings[key] = True
    repaired["settings"] = settings
    rendered = json.dumps(repaired, ensure_ascii=False, indent=2) + "\n"
    if workspace_file.exists() and workspace_file.read_text(encoding="utf-8") == rendered:
        print(f"WORKSPACE_REPAIR=NO_CHANGE FILE={workspace_file}")
        return
    if workspace_file.exists():
        backup = workspace_file.with_suffix(workspace_file.suffix + ".backup")
        shutil.copy2(workspace_file, backup)
        print(f"WORKSPACE_BACKUP={backup}")
    fd, tmp_name = tempfile.mkstemp(prefix=workspace_file.name + ".", dir=workspace_file.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(rendered)
        os.replace(tmp_name, workspace_file)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    print(f"WORKSPACE_REPAIR=UPDATED FILE={workspace_file}")


def check_symlink(errors: list[str], link: Path, expected: Path, label: str) -> None:
    if not link.is_symlink():
        errors.append(f"{label} missing or not symlink: {link}")
        return
    resolved = link.resolve()
    if resolved != expected.resolve():
        errors.append(f"{label} target mismatch: {resolved} != {expected.resolve()}")


def check(root: Path) -> list[str]:
    errors: list[str] = []
    p = paths(root)
    server_core = p["server_core"]
    projects = p["projects"]
    for required in (
        server_core / "README.md",
        server_core / "docs" / "LOAD_SCOPE.md",
        server_core / ".cursor" / "rules" / "00_agent_runtime.mdc",
        server_core / ".github" / "copilot-instructions.md",
        server_core / "AGENTS.md",
    ):
        if not required.is_file():
            errors.append(f"missing required entry authority: {required}")
    workspace_file = p["workspace_file"]
    if not workspace_file.is_file():
        errors.append(f"missing workspace file: {workspace_file}")
    else:
        try:
            actual = load_workspace(workspace_file)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"invalid workspace json: {exc}")
        else:
            expected = expected_workspace(server_core, projects)
            if actual.get("folders") != expected["folders"]:
                errors.append("workspace folders must be server-core first, then projects")
            actual_settings = actual.get("settings", {})
            for section in ("files.exclude", "search.exclude"):
                actual_section = actual_settings.get(section, {})
                for key, value in expected["settings"][section].items():
                    if actual_section.get(key) is not value:
                        errors.append(f"workspace setting missing: {section} {key}=true")
            for key in ("github.copilot.chat.codeGeneration.useInstructionFiles", "chat.useAgentsMdFile"):
                if actual_settings.get(key) is not True:
                    errors.append(f"workspace setting missing: {key}=true")
    check_symlink(errors, p["rules_link"], p["expected_rules"], "Cursor rules link")
    check_symlink(errors, p["copilot_link"], p["expected_copilot"], "Copilot instructions link")
    check_symlink(errors, p["agents_link"], p["expected_agents"], "AGENTS entry link")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or repair G-ACE Workspace wiring")
    parser.add_argument("--root", default=os.environ.get("GACE_HOME", "/home/admin1"), help="Root containing server-core, projects and workspace directories")
    parser.add_argument("--repair", action="store_true", help="Repair canonical workspace folders/exclude/AI-instruction settings before verification")
    parser.add_argument("--authorize-workspace-mutation", action="store_true", help="Explicitly authorize workspace-file mutation for --repair")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.repair and not args.authorize_workspace_mutation:
        print("WORKSPACE_REPAIR=BLOCKED: --repair requires --authorize-workspace-mutation")
        print("NO_CHANGES_PERFORMED")
        return 2
    if args.authorize_workspace_mutation and not args.repair:
        print("WORKSPACE_REPAIR=BLOCKED: --authorize-workspace-mutation is valid only with --repair")
        print("NO_CHANGES_PERFORMED")
        return 2
    if args.repair:
        try:
            repair(root)
        except Exception as exc:  # noqa: BLE001
            print(f"WORKSPACE_REPAIR=FAIL: {exc}")
            return 1
    errors = check(root)
    if errors:
        print("WORKSPACE_WIRING=FAIL")
        print("WORKSPACE_WIRING_SCOPE=ENTRY_FILES,WORKSPACE_FILE,CURSOR_RULES_LINK,COPILOT_INSTRUCTIONS_LINK,AGENTS_ENTRY_LINK,AI_SETTINGS")
        for error in errors:
            print(f"- {error}")
        return 1
    print("WORKSPACE_WIRING=PASS")
    print("WORKSPACE_WIRING_SCOPE=ENTRY_FILES,WORKSPACE_FILE,CURSOR_RULES_LINK,COPILOT_INSTRUCTIONS_LINK,AGENTS_ENTRY_LINK,AI_SETTINGS")
    print("NOT_PROVEN=FULL_AUTHORITY_COMPLETENESS,SCRIPT_SAFETY,PROJECT_RUNTIME,PROVIDER_AVAILABILITY,CLIENT_ACTUAL_INSTRUCTION_CONSUMPTION")
    print(f"ROOT={root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
