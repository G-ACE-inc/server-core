#!/usr/bin/env python3
"""Mechanical repo/branch/HEAD/scope binding for mutation entry points."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath

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

BINDING_REQUIRED_STRING_KEYS = (
    "repository",
    "branch",
    "head",
    "change_unit",
    "mutation_owner",
    "exact_next_gate",
)
GIT_WRITE_TAIL_PATTERNS = (
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
    r"^add\b",
    r"^rm\b",
    r"^mv\b",
)


class BindingState(str, Enum):
    ABSENT = "absent"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"
    VALID = "valid"


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


def binding_raw_present() -> bool:
    return bool(os.environ.get("GACE_MUTATION_BINDING", "").strip())


def parse_binding() -> tuple[BindingState, dict | None, str | None]:
    raw = os.environ.get("GACE_MUTATION_BINDING", "").strip()
    if not raw:
        return BindingState.ABSENT, None, None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return BindingState.INVALID, None, "json_decode_error"
    if not isinstance(data, dict):
        return BindingState.INVALID, None, "binding_not_object"
    missing = missing_binding_fields(data)
    if missing:
        return BindingState.INCOMPLETE, data, ",".join(missing)
    return BindingState.VALID, data, None


def missing_binding_fields(data: dict) -> list[str]:
    missing: list[str] = []
    for key in BINDING_REQUIRED_STRING_KEYS:
        val = data.get(key)
        if not isinstance(val, str) or not val.strip():
            missing.append(key)
    prefixes = data.get("in_scope_path_prefixes")
    if not isinstance(prefixes, list) or not prefixes:
        missing.append("in_scope_path_prefixes")
    else:
        for item in prefixes:
            if not isinstance(item, str) or not item.strip():
                missing.append("in_scope_path_prefixes")
                break
    return missing


def normalize_repo(value: str) -> str:
    return value.strip().lower()


def normalize_scope_prefix(prefix: str) -> str:
    p = prefix.strip().replace("\\", "/").lstrip("./")
    return p.rstrip("/")


def normalize_changed_path(path: str) -> tuple[str | None, str | None]:
    raw = path.strip()
    if not raw:
        return None, "SCOPE_PATH_EMPTY"
    if raw.startswith("/") or (len(raw) > 1 and raw[1] == ":" and raw[0].isalpha()):
        return None, "SCOPE_PATH_ABSOLUTE"
    if ".." in PurePosixPath(raw.replace("\\", "/")).parts:
        return None, "SCOPE_PATH_TRAVERSAL"
    norm = raw.replace("\\", "/").lstrip("./")
    if not norm:
        return None, "SCOPE_PATH_EMPTY"
    return norm, None


def path_under_prefix(norm_path: str, prefix: str) -> bool:
    pref = normalize_scope_prefix(prefix)
    if not pref:
        return False
    if norm_path == pref:
        return True
    return norm_path.startswith(pref + "/")


def paths_outside_scope(paths: list[str], prefixes: list[str]) -> tuple[list[str], str | None]:
    clean_prefixes = [normalize_scope_prefix(p) for p in prefixes if p.strip()]
    outside: list[str] = []
    for path in paths:
        norm, deny = normalize_changed_path(path)
        if deny:
            return [path], deny
        if norm is None:
            continue
        if any(path_under_prefix(norm, pref) for pref in clean_prefixes):
            continue
        outside.append(path)
    return outside, None


def validate_binding_identity(
    binding: dict,
    repository: str,
    branch: str | None,
    head: str | None,
) -> dict | None:
    expected_repo = binding["repository"].strip()
    if normalize_repo(repository) != normalize_repo(expected_repo):
        return emit(
            "DENY",
            "WRONG_MISSION_OR_CU",
            reason="repository_mismatch",
            expected=expected_repo,
            actual=repository,
        )

    expected_branch = binding["branch"].strip()
    if not branch or branch != expected_branch:
        return emit(
            "DENY",
            "WRONG_MISSION_OR_CU",
            reason="branch_mismatch",
            expected=expected_branch,
            actual=branch or "",
        )

    want = binding["head"].strip()
    if not head or not (head == want or head.startswith(want)):
        return emit(
            "DENY",
            "WRONG_MISSION_OR_CU",
            reason="head_mismatch",
            expected=want,
            actual=head or "",
        )
    return None


def check(
    *,
    mode: str,
    repo_root: Path,
    changed_paths: list[str] | None = None,
    require_changed_paths: bool = False,
) -> dict:
    if mode == "readonly":
        return emit("ALLOW", "READONLY_BYPASS")

    state, binding, detail = parse_binding()
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

    if state is BindingState.ABSENT:
        return emit(
            "ALLOW",
            "BASELINE_REPOSITORY_VERIFIED",
            repository=repository,
            branch=branch or "",
            head=head or "",
            current_mission_verified="NO",
        )

    if state is BindingState.INVALID:
        return emit(
            "DENY",
            "BINDING_INVALID",
            reason=detail or "invalid",
            current_mission_verified="NO",
        )

    if state is BindingState.INCOMPLETE:
        return emit(
            "DENY",
            "BINDING_INCOMPLETE",
            missing=detail or "unknown",
            current_mission_verified="NO",
        )

    assert binding is not None
    identity_deny = validate_binding_identity(binding, repository, branch, head)
    if identity_deny is not None:
        identity_deny["current_mission_verified"] = "NO"
        return identity_deny

    prefixes = binding["in_scope_path_prefixes"]
    if require_changed_paths and not changed_paths:
        return emit(
            "DENY",
            "SCOPE_PATHS_REQUIRED",
            current_mission_verified="NO",
        )

    if changed_paths is not None:
        drift, path_deny = paths_outside_scope(changed_paths, prefixes)
        if path_deny:
            return emit(
                "DENY",
                path_deny,
                paths=",".join(changed_paths[:5]),
                current_mission_verified="NO",
            )
        if drift:
            return emit(
                "DENY",
                "SCOPE_DRIFT_BLOCKED",
                paths=",".join(drift[:20]),
                current_mission_verified="NO",
            )

    return emit(
        "ALLOW",
        "IDENTITY_BOUND",
        repository=repository,
        branch=branch or "",
        head=head or "",
        change_unit=binding["change_unit"].strip(),
        mutation_owner=binding["mutation_owner"].strip(),
        exact_next_gate=binding["exact_next_gate"].strip(),
        current_mission_verified="NO",
    )


def checkpoint_comment_body(repo_root: Path) -> str:
    state, binding, _ = parse_binding()
    repository, branch, head = git_identity(repo_root)
    lines = [
        "<!-- gace-current-checkpoint:v1 -->",
        "### G-ACE Work Checkpoint",
        f"- REPOSITORY: {repository or 'UNKNOWN'}",
        f"- BRANCH: {branch or 'UNKNOWN'}",
        f"- HEAD: {head or 'UNKNOWN'}",
        "- CURRENT_MISSION_VERIFIED: NO",
    ]
    if state is BindingState.VALID and binding is not None:
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


def git_repo_root_for_command(command: str, cwd: Path) -> Path:
    stripped = command.strip()
    match = re.match(r"^git\s+-C\s+(\S+)", stripped, re.I)
    if match:
        candidate = Path(match.group(1))
        if not candidate.is_absolute():
            candidate = (cwd / candidate).resolve()
        else:
            candidate = candidate.resolve()
        return candidate
    return cwd.resolve()


def git_command_tail(stripped: str) -> str:
    tail = stripped.strip()
    while True:
        m = re.match(r"^git\s+(?:-C\s+\S+\s+|-c\s+\S+\s+)+", tail, re.I)
        if not m:
            break
        tail = tail[m.end() :]
    if tail.lower().startswith("git "):
        tail = tail[4:]
    return tail.strip()


def is_git_write_command(command: str) -> bool:
    surface = command.strip()
    if not surface.lower().startswith("git"):
        return False
    tail = git_command_tail(surface)
    return any(re.search(p, tail, re.I) for p in GIT_WRITE_TAIL_PATTERNS)


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

    changed: list[str] | None = None
    require_paths = False
    if args.paths_file is not None:
        require_paths = True
        if args.paths_file.is_file():
            changed = args.paths_file.read_text(encoding="utf-8").splitlines()

    out = check(
        mode=args.mode,
        repo_root=repo_root.resolve(),
        changed_paths=changed,
        require_changed_paths=require_paths,
    )
    print(json.dumps(out, sort_keys=True))
    return 0 if out["result"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
