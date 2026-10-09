#!/usr/bin/env python3
"""Fail-closed --project validation for init-dev-workspace.sh (no filesystem mutation)."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TABLE_ROW = re.compile(
    r"^\|\s*[^|]+\|\s*`([^`]+)`\s*\|\s*`(/home/admin1/projects/[^`]+)`",
    re.MULTILINE,
)
DEFAULT_PROJECTS_DIR = Path("/home/admin1/projects")


def fail(code: str, detail: str | None = None) -> int:
    payload = {"result": "DENY", "code": code}
    if detail:
        payload["detail"] = detail
    print(json.dumps(payload, sort_keys=True))
    return 1


def load_registry(registry_doc: Path) -> dict[str, str]:
    text = registry_doc.read_text(encoding="utf-8")
    mapping: dict[str, str] = {}
    for repo, path in TABLE_ROW.findall(text):
        name = Path(path).name
        if path.startswith("/home/admin1/projects/"):
            mapping[name] = repo
    return mapping


def resolve_under_projects(projects_dir: Path, name: str) -> tuple[Path | None, str | None]:
    if name in (".", "..") or ".." in name or "/" in name or "\\" in name:
        return None, "PROJECT_NAME_TRAVERSAL"
    if name.startswith("-") or Path(name).is_absolute():
        return None, "PROJECT_NAME_ABSOLUTE_OR_INVALID"
    if not NAME_RE.fullmatch(name):
        return None, "PROJECT_NAME_CHARSET_INVALID"
    candidate = (projects_dir / name).resolve()
    projects_root = projects_dir.resolve()
    try:
        candidate.relative_to(projects_root)
    except ValueError:
        return None, "PROJECT_PATH_ESCAPE"
    return candidate, None



def git_origin_repo(project_dir: Path) -> str | None:
    if not (project_dir / ".git").exists():
        return None
    proc = subprocess.run(
        ["git", "-C", str(project_dir), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    url = proc.stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2).removesuffix('.git')}"


def validate(name: str, projects_dir: Path, registry_doc: Path) -> int:
    if not registry_doc.is_file():
        return fail("REGISTRY_DOC_MISSING", str(registry_doc))
    mapping = load_registry(registry_doc)
    if not mapping:
        return fail("REGISTRY_EMPTY_OR_UNPARSEABLE")
    resolved, err = resolve_under_projects(projects_dir, name)
    if err:
        return fail(err, name)
    assert resolved is not None
    if name not in mapping:
        return fail("PROJECT_NOT_REGISTERED", name)
    if not resolved.is_dir():
        return fail("PROJECT_NOT_EXISTING", str(resolved))
    expected_repo = mapping[name]
    actual_repo = git_origin_repo(resolved)
    if actual_repo and actual_repo.lower() != expected_repo.lower():
        return fail(
            "PROJECT_REPOSITORY_IDENTITY_MISMATCH",
            json.dumps({"expected": expected_repo, "actual": actual_repo}),
        )
    print(
        json.dumps(
            {
                "result": "ALLOW",
                "code": "PROJECT_SELECT_VERIFIED",
                "name": name,
                "path": str(resolved),
                "repository": expected_repo,
            },
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--projects-dir", type=Path, default=DEFAULT_PROJECTS_DIR)
    parser.add_argument(
        "--registry-doc",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "WORKSPACE_REGISTRY.md",
    )
    args = parser.parse_args()
    return validate(args.name.strip(), args.projects_dir.resolve(), args.registry_doc.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
