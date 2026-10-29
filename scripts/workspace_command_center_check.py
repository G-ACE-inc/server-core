#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import re
import time
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
    # Retired ad-hoc settings duplicated rules, stale inventories and missing files.
    # Actual client adapters / Rule16 own instruction entry, not a second workspace payload.
    settings = {key: value for key, value in settings.items() if not key.startswith("codex.serverCore.")}
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
        backup = root / ".config/gace/server-ai-profile-backups" / str(time.time_ns()) / workspace_file.name
        backup.parent.mkdir(parents=True, mode=0o700)
        shutil.copy2(workspace_file, backup)
        backup.chmod(0o600)
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


def profile_sources(root: Path) -> list[tuple[Path, Path]]:
    server = root / "server-core"
    return [
        (server / ".cursor/templates/00_agent_language_router.mdc", root / ".cursor/rules/00_agent_language_router.mdc"),
        (server / ".cursor/rules/01_japanese_thinking.mdc", root / ".cursor/rules/01_japanese_thinking.mdc"),
    ] + [(server / ".cursor/templates/agents" / name, root / ".cursor/agents" / name)
         for name in ("composer.md", "GPT-4.5Mini.md", "gemini-flash.md", "log.md")]


def without_model(text: str) -> str:
    return re.sub(r"(?m)^model:.*$", "model: USER_CONFIGURED", text)


def repair_profile(root: Path) -> None:
    changes = []
    for source, target in profile_sources(root):
        if not source.is_file() or target.is_symlink():
            raise ValueError("PROFILE_SOURCE_MISSING_OR_TARGET_SYMLINK")
        text = source.read_text(encoding="utf-8")
        if source.suffix == '.md':
            if not target.is_file():
                raise ValueError("EXISTING_AGENT_MODEL_CONFIGURATION_REQUIRED")
            # User owns model/cost selection. Do not reset it from the template.
            model = re.search(r"(?m)^model:.*$", target.read_text(encoding="utf-8"))
            if not model:
                raise ValueError("EXISTING_AGENT_MODEL_CONFIGURATION_REQUIRED")
            text = re.sub(r"(?m)^model:.*$", lambda _: model.group(0), text)
        changes.append((target, text))
    backup = root / ".config/gace/server-ai-profile-backups" / str(time.time_ns())
    backup.mkdir(parents=True, mode=0o700)
    for target, text in changes:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            saved = backup / (target.parent.name + '-' + target.name)
            shutil.copy2(target, saved)
            saved.chmod(0o600)
        fd, temporary = tempfile.mkstemp(prefix=target.name + '.', dir=target.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o644)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    print("SERVER_AI_PROFILE=INSTALLED_EXISTING_MODELS_PRESERVED")


def check_installed_profile(root: Path) -> list[str]:
    # Older fixture/legacy installations without templates retain wiring-only checks.
    if not (root / "server-core/.cursor/templates").exists():
        return []
    errors = []
    for source, target in profile_sources(root):
        if not source.is_file() or not target.is_file() or target.is_symlink():
            errors.append(f"profile source/installed adapter missing: {target.name}")
        elif without_model(source.read_text()) != without_model(target.read_text()):
            errors.append(f"installed SERVER_AI adapter drift: {target.name}")
    return errors


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
            if not all(token in global_text for token in ("alwaysApply: true", "## G-ACE SERVER_AI", "LEAD_SELECTION=USER_SELECTED", "CONFIGURED_SUBAGENTS=AVAILABLE_WHEN_USEFUL", "GPT_CHAT_WORKFLOW=NOT_APPLICABLE")):
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
            if any(key.startswith('codex.serverCore.') for key in actual.get('settings', {})):
                errors.append('retired codex.serverCore workspace rule/settings payload remains')
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
    errors.extend(check_installed_profile(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or repair G-ACE Workspace command-center wiring")
    parser.add_argument("--root", default=os.environ.get("GACE_HOME", "/home/admin1"), help="Root containing server-core, projects and workspace directories")
    parser.add_argument("--repair", action="store_true", help="Repair canonical workspace folders/exclude settings before verification")
    parser.add_argument("--repair-profile", action="store_true", help="Install versioned Cursor profile adapters, preserving existing models; normalize legacy workspace settings")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.repair or args.repair_profile:
        try:
            repair(root)
        except Exception as exc:  # noqa: BLE001
            print(f"WORKSPACE_REPAIR=FAIL: {exc}")
            return 1
    if args.repair_profile:
        try:
            repair_profile(root)
        except (OSError, ValueError) as exc:
            print(f"SERVER_AI_PROFILE=FAIL: {exc}")
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
