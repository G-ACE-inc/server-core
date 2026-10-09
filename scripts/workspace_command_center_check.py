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


STUB_NAMES = {
    "00_agent_runtime.mdc",
    "01_japanese_thinking.mdc",
    "02_master_terminal_command.mdc",
    "cloudflare-operations.mdc",
}


def check_stub_rule_mode(root: Path, rules_dir: Path, canonical_rules: Path) -> list[str]:
    """Validate the CU2 multi-root stub mode without promoting it to runtime PASS."""
    errors: list[str] = []
    if rules_dir.is_symlink() or rules_dir.resolve() == canonical_rules.resolve():
        return ["stub mode may not alias canonical server-core rules"]
    global_rule = root / ".cursor" / "rules" / "00_agent_language_router.mdc"
    if global_rule.is_symlink() or not global_rule.is_file():
        errors.append("G-ACE user-global router missing or is a symlink")
    else:
        try:
            global_text = global_rule.read_text(encoding="utf-8")
        except OSError:
            errors.append("G-ACE user-global router unreadable")
        else:
            if not all(token in global_text for token in ("alwaysApply: true", "## G-ACE SERVER_AI", "COMPOSER")):
                errors.append("G-ACE user-global router required profile/activation missing")
    actual_names = {p.name for p in rules_dir.iterdir() if p.suffix == ".mdc"}
    if actual_names != STUB_NAMES:
        errors.append(f"projects rule stubs mismatch: {sorted(actual_names ^ STUB_NAMES)}")
    for name in STUB_NAMES & actual_names:
        stub = rules_dir / name
        if stub.is_symlink() or not stub.is_file():
            errors.append(f"projects rule stub is not a regular file: {name}")
            continue
        try:
            content = stub.read_text(encoding="utf-8")
        except OSError:
            errors.append(f"projects rule stub unreadable: {name}")
            continue
        if "alwaysApply: false" not in content or "alwaysApply: true" in content:
            errors.append(f"projects rule stub is active or lacks explicit opt-out: {name}")
        if "server-core" not in content:
            errors.append(f"projects rule stub missing canonical source reference: {name}")
    return errors


def check(root: Path) -> list[str]:
    errors: list[str] = []
    server_core, projects, workspace_file, rules_link, expected_rules = paths(root)
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
    if rules_link.is_symlink():
        resolved = rules_link.resolve()
        if resolved != expected_rules.resolve():
            errors.append(f"rules link target mismatch: {resolved} != {expected_rules.resolve()}")
    elif rules_link.is_dir():
        # Explicit Composer CU2 compatibility: projects root contains only inactive
        # redirect stubs, while a verified G-ACE User Global rule owns dispatch.
        # This is a SOURCE/FILE gate, NOT proof of Cursor Active Rules injection.
        errors.extend(check_stub_rule_mode(root, rules_link, expected_rules))
    else:
        errors.append(f"rules link missing or invalid stub directory: {rules_link}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or repair G-ACE Workspace command-center wiring")
    parser.add_argument("--root", default=os.environ.get("GACE_HOME", "/home/admin1"), help="Root containing server-core, projects and workspace directories")
    parser.add_argument("--repair", action="store_true", help="Repair canonical workspace folders/exclude settings before verification")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.repair:
        try:
            repair(root)
        except Exception as exc:  # noqa: BLE001
            print(f"WORKSPACE_REPAIR=FAIL: {exc}")
            return 1
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
