#!/usr/bin/env python3
"""Fail-closed selector for an EXISTING, registered canonical Git project."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

PROJECTS = Path("/home/admin1/projects")
ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TABLE_ROW = re.compile(
    r"^\|\s*[^|]+\|\s*\x60([^\x60]+)\x60\s*\|\s*\x60(/home/admin1/projects/[^\x60]+)\x60",
    re.MULTILINE,
)
ORIGIN_RE = re.compile(
    r"^(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)"
    r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def emit(result: str, code: str, **details: str) -> int:
    print(json.dumps({"result": result, "code": code, **details}, sort_keys=True))
    return 0 if result == "ALLOW" else 1


def registered(registry_doc: Path, master_registry: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}

    def add(path: str, repo: str) -> None:
        p = Path(path)
        if p.parent != PROJECTS or not NAME_RE.fullmatch(p.name):
            raise ValueError("REGISTRY_PATH_INVALID")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("REGISTRY_REPOSITORY_INVALID")
        if p.name in mapping and mapping[p.name].lower() != repo.lower():
            raise ValueError("REGISTRY_COLLISION")
        mapping[p.name] = repo

    for repo, path in TABLE_ROW.findall(registry_doc.read_text(encoding="utf-8")):
        add(path, repo)
    if master_registry.is_file():
        data = json.loads(master_registry.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("repositories"), list):
            raise ValueError("MASTER_REGISTRY_INVALID")
        for entry in data["repositories"]:
            if not isinstance(entry, dict):
                raise ValueError("MASTER_REGISTRY_ENTRY_INVALID")
            path, repo = entry.get("server_project_path"), entry.get("repository")
            if isinstance(path, str) and path.startswith(str(PROJECTS) + "/"):
                if not isinstance(repo, str):
                    raise ValueError("MASTER_REGISTRY_REPOSITORY_INVALID")
                add(path, repo)
    return mapping


def git_value(path: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else None


def verify_git(path: Path, repo: str) -> str | None:
    if not (path / ".git").is_dir() or (path / ".git").is_symlink():
        return "PROJECT_GIT_IDENTITY_UNKNOWN"
    origin = git_value(path, "remote", "get-url", "origin")
    match = ORIGIN_RE.fullmatch(origin or "")
    if not match:
        return "PROJECT_GIT_ORIGIN_INVALID"
    actual_repo = f"{match.group(1)}/{match.group(2)}"
    if actual_repo.lower() != repo.lower():
        return "PROJECT_REPOSITORY_IDENTITY_MISMATCH"
    toplevel = git_value(path, "rev-parse", "--show-toplevel")
    common = git_value(path, "rev-parse", "--git-common-dir")
    if not toplevel or not common:
        return "PROJECT_GIT_IDENTITY_UNKNOWN"
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = path / common_path
    if Path(toplevel).resolve() != path.resolve() or common_path.resolve() != (path / ".git").resolve():
        return "PROJECT_GIT_COMMON_DIR_MISMATCH"
    return None


def validate(name: str, projects_dir: Path, registry_doc: Path, master_registry: Path) -> int:
    if not registry_doc.is_file():
        return emit("DENY", "REGISTRY_DOC_MISSING")
    try:
        mapping = registered(registry_doc, master_registry)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return emit("DENY", "REGISTRY_INVALID", detail=str(exc))
    if not mapping:
        return emit("DENY", "REGISTRY_EMPTY_OR_UNPARSEABLE")
    if name in (".", "..") or ".." in name or "/" in name or "\\" in name:
        return emit("DENY", "PROJECT_NAME_TRAVERSAL")
    if not NAME_RE.fullmatch(name):
        return emit("DENY", "PROJECT_NAME_CHARSET_INVALID")
    if name not in mapping:
        return emit("DENY", "PROJECT_NOT_REGISTERED")
    root = projects_dir.resolve()
    raw = projects_dir / name
    if raw.is_symlink():
        return emit("DENY", "PROJECT_PATH_ALIAS_OR_SYMLINK")
    try:
        target = raw.resolve(strict=True)
    except (OSError, RuntimeError):
        return emit("DENY", "PROJECT_NOT_EXISTING")
    if target != root / name:
        return emit("DENY", "PROJECT_PATH_ALIAS_OR_SYMLINK")
    if not target.is_dir():
        return emit("DENY", "PROJECT_NOT_EXISTING")
    problem = verify_git(target, mapping[name])
    if problem:
        return emit("DENY", problem)
    return emit("ALLOW", "PROJECT_SELECT_VERIFIED", name=name, path=str(target), repository=mapping[name])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--projects-dir", type=Path, default=PROJECTS)
    parser.add_argument("--registry-doc", type=Path, default=ROOT / "docs/WORKSPACE_REGISTRY.md")
    parser.add_argument("--master-registry", type=Path, default=ROOT / "operations/master-internal-repositories.json")
    args = parser.parse_args()
    return validate(args.name.strip(), args.projects_dir, args.registry_doc, args.master_registry)


if __name__ == "__main__":
    raise SystemExit(main())
