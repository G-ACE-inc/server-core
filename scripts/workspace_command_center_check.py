#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def expected_workspace(server_core: Path, projects: Path) -> dict[str, Any]:
    return {
        "folders": [
            {"name": "server-core", "path": str(server_core)},
            {"name": "projects", "path": str(projects)},
        ],
        "settings": {
            "files.exclude": {
                "**/.git": True,
                "**/node_modules": True,
                "**/dist": True,
                "**/build": True,
                "**/.next": True,
                "**/archive": True,
                "**/logs": True,
                "**/backups": True,
            },
            "search.exclude": {
                "**/.git": True,
                "**/node_modules": True,
                "**/dist": True,
                "**/build": True,
                "**/.next": True,
                "**/archive": True,
                "**/logs": True,
                "**/backups": True,
            },
        },
    }


def check(root: Path) -> list[str]:
    errors: list[str] = []
    server_core = root / "server-core"
    projects = root / "projects"
    workspace_file = root / "workspace" / "G-ACE.code-workspace"
    rules_link = projects / ".cursor" / "rules"
    expected_rules = server_core / ".cursor" / "rules"

    for required in (
        server_core / "README.md",
        server_core / "docs" / "LOAD_SCOPE.md",
        server_core / ".cursor" / "rules" / "00_agent_runtime.mdc",
    ):
        if not required.is_file():
            errors.append(f"missing required authority: {required}")

    if not workspace_file.is_file():
        errors.append(f"missing workspace file: {workspace_file}")
    else:
        try:
            actual = json.loads(workspace_file.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"invalid workspace json: {exc}")
        else:
            expected = expected_workspace(server_core, projects)
            if actual.get("folders") != expected["folders"]:
                errors.append("workspace folders must be server-core first, then projects")
            for section in ("files.exclude", "search.exclude"):
                actual_section = actual.get("settings", {}).get(section, {})
                for key, value in expected["settings"][section].items():
                    if actual_section.get(key) is not value:
                        errors.append(f"workspace setting missing: {section} {key}=true")

    if not rules_link.is_symlink():
        errors.append(f"rules link missing or not symlink: {rules_link}")
    else:
        resolved = rules_link.resolve()
        if resolved != expected_rules.resolve():
            errors.append(f"rules link target mismatch: {resolved} != {expected_rules.resolve()}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify G-ACE Workspace command-center wiring")
    parser.add_argument(
        "--root",
        default=os.environ.get("GACE_HOME", "/home/admin1"),
        help="Root containing server-core, projects and workspace directories",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors = check(root)
    if errors:
        print("WORKSPACE_COMMAND_CENTER=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("WORKSPACE_COMMAND_CENTER=PASS")
    print(f"ROOT={root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
