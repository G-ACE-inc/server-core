#!/usr/bin/env python3
"""Mechanical repo/branch/HEAD/scope binding for mutation entry points."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
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
    prefix_err = invalid_binding_scope_prefixes(data)
    if prefix_err:
        return BindingState.INVALID, data, prefix_err
    return BindingState.VALID, data, None



def scope_prefix_validation_error(prefix: str) -> str | None:
    raw = prefix.strip()
    if not raw:
        return "SCOPE_PREFIX_EMPTY"
    norm = raw.replace("\\", "/")
    if norm.startswith("/") or (len(norm) > 1 and norm[1] == ":" and norm[0].isalpha()):
        return "SCOPE_PREFIX_ABSOLUTE"
    if ".." in PurePosixPath(norm).parts:
        return "SCOPE_PREFIX_TRAVERSAL"
    return None


def canonical_scope_prefix(prefix: str) -> str:
    norm = prefix.strip().replace("\\", "/")
    if norm.startswith("./"):
        norm = norm[2:]
    return norm.rstrip("/")


def invalid_binding_scope_prefixes(data: dict) -> str | None:
    prefixes = data.get("in_scope_path_prefixes")
    if not isinstance(prefixes, list):
        return None
    for item in prefixes:
        if not isinstance(item, str):
            return "in_scope_path_prefixes"
        err = scope_prefix_validation_error(item)
        if err:
            return err
    return None

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
    return canonical_scope_prefix(prefix)


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
        code = "BINDING_INVALID"
        if detail in (
            "SCOPE_PREFIX_EMPTY",
            "SCOPE_PREFIX_ABSOLUTE",
            "SCOPE_PREFIX_TRAVERSAL",
            "in_scope_path_prefixes",
        ):
            code = "BINDING_SCOPE_PREFIX_INVALID"
        return emit(
            "DENY",
            code,
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

    routine_deny = evaluate_work_routine_turn_receipt()
    if routine_deny is not None:
        return routine_deny

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


def evaluate_work_routine_turn_receipt() -> dict | None:
    """Optional mechanical Work Routine turn receipt (JSON path in env)."""
    raw = os.environ.get("GACE_WORK_ROUTINE_TURN", "").strip()
    if not raw:
        return None
    turn_path = Path(raw)
    if not turn_path.is_file():
        return emit(
            "DENY",
            "WORK_ROUTINE_TURN_RECEIPT_MISSING",
            current_mission_verified="NO",
        )
    try:
        state = json.loads(turn_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return emit(
            "DENY",
            "WORK_ROUTINE_TURN_RECEIPT_UNREADABLE",
            current_mission_verified="NO",
        )
    gate_path = Path(__file__).resolve().with_name("work_routine_design_entry_gate.py")
    spec = importlib.util.spec_from_file_location("work_routine_design_entry_gate", gate_path)
    if spec is None or spec.loader is None:
        return emit(
            "DENY",
            "WORK_ROUTINE_GATE_UNAVAILABLE",
            current_mission_verified="NO",
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    outcome = module.evaluate_turn(state)
    if outcome == "PASS":
        return None
    return emit(
        "DENY",
        outcome,
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




def _status_record_path(rec: bytes) -> str | None:
    if len(rec) < 4 or rec[2:3] != b" ":
        return None
    return rec[3:].decode("utf-8", "surrogateescape")


def _is_rename_or_copy_xy(xy: bytes) -> bool:
    return b"R" in xy or b"C" in xy


def parse_porcelain_v1_z(data: bytes) -> list[str]:
    if not data:
        return []
    parts = data.split(b"\0")
    while parts and parts[-1] == b"":
        parts.pop()
    paths: list[str] = []
    i = 0
    while i < len(parts):
        rec = parts[i]
        i += 1
        path = _status_record_path(rec)
        if path is None:
            continue
        xy = rec[:2]
        if _is_rename_or_copy_xy(xy):
            paths.append(path)
            if i < len(parts) and _status_record_path(parts[i]) is None:
                paths.append(parts[i].decode("utf-8", "surrogateescape"))
                i += 1
            continue
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def collect_changed_paths(repo_root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain=v1", "-z"],
        capture_output=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        return []
    return parse_porcelain_v1_z(proc.stdout)


GIT_GLOBAL_SKIP_ONE = frozenset({
    "--no-pager", "--no-replace-objects", "--bare", "--literal-pathspecs",
    "--glob-pathspecs", "--icase-pathspecs", "--noglob-pathspecs",
})


def parse_git_invocation(command: str, cwd: Path) -> tuple[Path | None, str | None, str | None]:
    try:
        parts = shlex.split(command.strip(), posix=True)
    except ValueError:
        return None, None, "GIT_COMMAND_PARSE_AMBIGUOUS"
    if not parts or parts[0].lower() != "git":
        return cwd.resolve(), "", None
    idx = 1
    effective = cwd.resolve()
    while idx < len(parts):
        tok = parts[idx]
        if tok.startswith("--git-dir="):
            idx += 1
            continue
        if tok.startswith("--work-tree="):
            val = tok.split("=", 1)[1]
            idx += 1
            candidate = Path(val)
            if not candidate.is_absolute():
                candidate = (effective / candidate).resolve()
            else:
                candidate = candidate.resolve()
            effective = candidate
            continue
        if tok in ("-C", "--work-tree"):
            if idx + 1 >= len(parts):
                return None, None, "GIT_COMMAND_PARSE_AMBIGUOUS"
            val = parts[idx + 1]
            idx += 2
            candidate = Path(val)
            if not candidate.is_absolute():
                candidate = (effective / candidate).resolve()
            else:
                candidate = candidate.resolve()
            effective = candidate
            continue
        if tok == "--git-dir":
            if idx + 1 >= len(parts):
                return None, None, "GIT_COMMAND_PARSE_AMBIGUOUS"
            idx += 2
            continue
        if tok == "-c":
            if idx + 1 >= len(parts):
                return None, None, "GIT_COMMAND_PARSE_AMBIGUOUS"
            idx += 2
            continue
        if tok in GIT_GLOBAL_SKIP_ONE:
            idx += 1
            continue
        if tok.startswith("-") and tok not in ("-C", "-c"):
            idx += 1
            continue
        break
    tail = " ".join(parts[idx:]).strip() if idx < len(parts) else ""
    return effective, tail, None


def git_repo_root_for_command(command: str, cwd: Path) -> tuple[Path | None, str | None]:
    root, _, err = parse_git_invocation(command, cwd)
    if err:
        return None, err
    return root, None


def git_command_tail(command: str, cwd: Path | None = None) -> str:
    base = cwd if cwd is not None else Path.cwd()
    _, tail, _ = parse_git_invocation(command, base)
    return tail or ""


def is_git_write_command(command: str, cwd: Path | None = None) -> bool:
    surface = command.strip()
    if not surface.lower().startswith("git"):
        return False
    tail = git_command_tail(surface, cwd=cwd)
    return any(re.search(p, tail, re.I) for p in GIT_WRITE_TAIL_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("readonly", "mutate"), default="mutate")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--paths-file", type=Path, default=None)
    parser.add_argument("--emit-checkpoint", action="store_true")
    parser.add_argument("--collect-changed-paths", action="store_true")
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

    if args.collect_changed_paths:
        for path in collect_changed_paths(repo_root.resolve()):
            print(path)
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
