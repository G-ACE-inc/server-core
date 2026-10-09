#!/usr/bin/env python3
"""Mechanical repo/branch/HEAD/scope binding for mutation entry points."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_PLANE = ROOT / "operations" / "github-project-rule-plane.json"
SSH_ALIAS_RE = re.compile(
    r"^git@[^:]+:([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
ORIGIN_RE = re.compile(
    r"^(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)"
    r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def emit(result: str, code: str, **details: str) -> dict:
    return {"result": result, "code": code, **details}


def git_value(repo_root: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    return text or None


def parse_repository(origin: str | None) -> str | None:
    if not origin:
        return None
    origin = origin.strip()
    for pattern in (ORIGIN_RE, SSH_ALIAS_RE):
        match = pattern.fullmatch(origin)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


def git_identity(repo_root: Path) -> tuple[str | None, str | None, str | None]:
    origin = git_value(repo_root, "remote", "get-url", "origin")
    repository = parse_repository(origin)
    branch = git_value(repo_root, "branch", "--show-current")
    head = git_value(repo_root, "rev-parse", "HEAD")
    return repository, branch, head


def control_plane_repository() -> str | None:
    if not RULE_PLANE.is_file():
        return None
    try:
        doc = json.loads(RULE_PLANE.read_text(encoding="utf-8"))
        cp = doc.get("control_plane")
        if isinstance(cp, dict) and isinstance(cp.get("repository"), str):
            return cp["repository"]
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    return None


def load_binding() -> dict | None:
    raw = os.environ.get("GACE_MUTATION_BINDING", "").strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def normalize_repo(value: str) -> str:
    return value.strip().lower()


def paths_outside_scope(paths: list[str], prefixes: list[str]) -> list[str]:
    outside: list[str] = []
    for path in paths:
        p = path.strip().lstrip("./")
        if not p:
            continue
        if any(p == pref.rstrip("/") or p.startswith(pref) for pref in prefixes):
            continue
        outside.append(path)
    return outside


def check(
    *,
    mode: str,
    repo_root: Path,
    changed_paths: list[str] | None = None,
) -> dict:
    if mode == "readonly":
        return emit("ALLOW", "READONLY_BYPASS")

    binding = load_binding()
    repository, branch, head = git_identity(repo_root)
    if not repository:
        return emit("DENY", "REPOSITORY_IDENTITY_UNKNOWN")

    baseline = control_plane_repository()
    if baseline and normalize_repo(repository) != normalize_repo(baseline):
        return emit(
            "DENY",
            "REPOSITORY_IDENTITY_MISMATCH",
            expected=baseline,
            actual=repository,
        )

    if binding is None:
        return emit(
            "ALLOW",
            "BASELINE_REPOSITORY_VERIFIED",
            repository=repository,
            branch=branch or "",
            head=head or "",
        )

    expected_repo = binding.get("repository")
    if isinstance(expected_repo, str) and expected_repo.strip():
        if normalize_repo(repository) != normalize_repo(expected_repo):
            return emit(
                "DENY",
                "WRONG_MISSION_OR_CU",
                reason="repository_mismatch",
                expected=expected_repo.strip(),
                actual=repository,
            )

    expected_branch = binding.get("branch")
    if isinstance(expected_branch, str) and expected_branch.strip():
        if not branch or branch != expected_branch.strip():
            return emit(
                "DENY",
                "WRONG_MISSION_OR_CU",
                reason="branch_mismatch",
                expected=expected_branch.strip(),
                actual=branch or "",
            )

    expected_head = binding.get("head")
    if isinstance(expected_head, str) and expected_head.strip():
        want = expected_head.strip()
        if not head or not (head == want or head.startswith(want)):
            return emit(
                "DENY",
                "WRONG_MISSION_OR_CU",
                reason="head_mismatch",
                expected=want,
                actual=head or "",
            )

    prefixes = binding.get("in_scope_path_prefixes")
    if changed_paths and isinstance(prefixes, list) and prefixes:
        clean_prefixes = [p for p in prefixes if isinstance(p, str) and p.strip()]
        if clean_prefixes:
            drift = paths_outside_scope(changed_paths, clean_prefixes)
            if drift:
                return emit(
                    "DENY",
                    "SCOPE_DRIFT_BLOCKED",
                    paths=",".join(drift[:20]),
                )

    details = {
        "repository": repository,
        "branch": branch or "",
        "head": head or "",
    }
    for key in ("change_unit", "mutation_owner", "exact_next_gate"):
        val = binding.get(key)
        if isinstance(val, str) and val.strip():
            details[key] = val.strip()
    return emit("ALLOW", "MUTATION_REHYDRATE_VERIFIED", **details)


def checkpoint_comment_body(repo_root: Path) -> str:
    binding = load_binding() or {}
    repository, branch, head = git_identity(repo_root)
    lines = [
        "<!-- gace-current-checkpoint:v1 -->",
        "### G-ACE Work Checkpoint",
        f"- REPOSITORY: {repository or 'UNKNOWN'}",
        f"- BRANCH: {branch or 'UNKNOWN'}",
        f"- HEAD: {head or 'UNKNOWN'}",
    ]
    for label, key in (
        ("CHANGE_UNIT", "change_unit"),
        ("MUTATION_OWNER", "mutation_owner"),
        ("EXACT_NEXT_GATE", "exact_next_gate"),
        ("CURRENT_REFERENCE", "current_reference"),
    ):
        val = binding.get(key)
        if isinstance(val, str) and val.strip():
            lines.append(f"- {label}: {val.strip()}")
    lines.append(f"- RECORDED_AT: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    return "\n".join(lines) + "\n"


def is_git_write_command(command: str) -> bool:
    surface = command.strip()
    if not surface.lower().startswith("git"):
        return False
    tail = surface.split(None, 1)[1] if " " in surface else ""
    patterns = (
        r"^commit\b",
        r"^push\b",
        r"^merge\b",
        r"^rebase\b",
        r"^reset\b",
        r"^cherry-pick\b",
        r"^revert\b",
        r"^checkout\b",
        r"^switch\b",
        r"^restore\b",
        r"^clean\b",
        r"^stash\s+push\b",
        r"^stash\s+drop\b",
    )
    return any(re.search(p, tail, re.I) for p in patterns)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("readonly", "mutate"), default="mutate")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--paths-file", type=Path, default=None)
    parser.add_argument("--emit-checkpoint", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root
    if repo_root is None:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            repo_root = Path(proc.stdout.strip())
        except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
            out = emit("DENY", "REPOSITORY_ROOT_UNKNOWN")
            print(json.dumps(out, sort_keys=True))
            return 1

    if args.emit_checkpoint:
        print(checkpoint_comment_body(repo_root.resolve()), end="")
        return 0

    changed: list[str] = []
    if args.paths_file and args.paths_file.is_file():
        changed = [
            line.strip()
            for line in args.paths_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    out = check(mode=args.mode, repo_root=repo_root.resolve(), changed_paths=changed or None)
    print(json.dumps(out, sort_keys=True))
    return 0 if out["result"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
