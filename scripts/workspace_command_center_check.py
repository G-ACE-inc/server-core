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
        },
    }


def paths(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    server_core = root / "server-core"
    projects = root / "projects"
    workspace_file = root / "workspace" / "G-ACE.code-workspace"
    rules_link = projects / ".cursor" / "rules"
    expected_rules = server_core / ".cursor" / "rules"
    return server_core, projects, workspace_file, rules_link, expected_rules


def load_workspace(workspace_file: Path) -> dict[str, Any]:
    if not workspace_file.exists():
        return {}
    raw = json.loads(workspace_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("workspace root must be a JSON object")
    return raw


def repair(root: Path) -> None:
    server_core, projects, workspace_file, _rules_link, _expected_rules = paths(root)
    expected = expected_workspace(server_core, projects)
    workspace_file.parent.mkdir(parents=True, exist_ok=True)
    actual = load_workspace(workspace_file)
    repaired = dict(actual)
    repaired["folders"] = expected["folders"]
    settings = dict(repaired.get("settings") or {})
    for section in ("files.exclude", "search.exclude"):
        merged = dict(settings.get(section) or {})
        merged.update(expected["settings"][section])
        settings[section] = merged
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


def check(root: Path) -> list[str]:
    errors: list[str] = []
    server_core, projects, workspace_file, rules_link, expected_rules = paths(root)
    for required in (server_core / "README.md", server_core / "docs" / "LOAD_SCOPE.md", server_core / ".cursor" / "rules" / "00_agent_runtime.mdc"):
        if not required.is_file():
            errors.append(f"missing required entry authority: {required}")
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
    parser = argparse.ArgumentParser(description="Verify or repair G-ACE Workspace wiring")
    parser.add_argument("--root", default=os.environ.get("GACE_HOME", "/home/admin1"), help="Root containing server-core, projects and workspace directories")
    parser.add_argument("--repair", action="store_true", help="Repair canonical workspace folders/exclude settings before verification")
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
        print("WORKSPACE_WIRING_SCOPE=ENTRY_FILES,WORKSPACE_FILE,RULES_LINK")
        for error in errors:
            print(f"- {error}")
        return 1
    print("WORKSPACE_WIRING=PASS")
    print("WORKSPACE_WIRING_SCOPE=ENTRY_FILES,WORKSPACE_FILE,RULES_LINK")
    print("NOT_PROVEN=FULL_AUTHORITY_COMPLETENESS,SCRIPT_SAFETY,PROJECT_RUNTIME,PROVIDER_AVAILABILITY")
    print(f"ROOT={root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
