#!/usr/bin/env python3
"""Read-only shell command classifier for G-ACE workspace proliferation gates."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
from pathlib import Path

DEFAULT_PROJECTS = Path("/home/admin1/projects")
DEFAULT_WORKTREES = Path("/home/admin1/worktrees")
DEFAULT_SERVER_CORE = Path("/home/admin1/server-core")
TABLE_ROW = re.compile(
    r"^\|\s*[^|]+\|\s*`([^`]+)`\s*\|\s*`(/home/admin1/projects/[^`]+)`",
    re.MULTILINE,
)

WORKSPACE_MUTATORS = (
    re.compile(r"\bgit\s+clone\b", re.I),
    re.compile(r"\bgit\s+worktree\s+add\b", re.I),
    re.compile(r"\bgit\s+init\b", re.I),
    re.compile(r"\bgh\s+repo\s+(?:clone|create|fork)\b", re.I),
    re.compile(r"\bmkdir\b", re.I),
    re.compile(r"\bos\.makedirs\b", re.I),
    re.compile(r"\brsync\b", re.I),
    re.compile(r"\bcp\b", re.I),
    re.compile(r"\bmv\b", re.I),
)

HEREDOC_PATTERN = re.compile(
    r"<<-?\s*(?:\'([^\']+)\'|\"([^\"]+)\"|(\w+))\s*(?:\r?\n|\s)([\s\S]*?)\r?\n\s*(?:\1|\2|\3)\s*(?:\)|;|$|\s)",
    re.MULTILINE,
)

SINGLE_QUOTED = re.compile(r"'([^'\\]|\\.)*'")

GH_MUTATING_SUBCOMMANDS = (
    "repo clone",
    "repo create",
    "repo fork",
    "repo sync",
    "project create",
    "gist create",
)

GH_READONLY_SUBCOMMAND_PREFIXES = (
    "issue comment",
    "issue view",
    "issue list",
    "issue status",
    "pr comment",
    "pr view",
    "pr list",
    "pr status",
    "pr checks",
    "run view",
    "run list",
    "release view",
    "release list",
    "workflow view",
    "workflow list",
)

GIT_READONLY_TAIL_PATTERNS = (
    re.compile(r"^status\b", re.I),
    re.compile(r"^diff\b", re.I),
    re.compile(r"^log\b", re.I),
    re.compile(r"^show\b", re.I),
    re.compile(r"^rev-parse\b", re.I),
    re.compile(r"^ls-files\b", re.I),
    re.compile(r"^ls-remote\b", re.I),
    re.compile(r"^grep\b", re.I),
    re.compile(r"^blame\b", re.I),
    re.compile(r"^describe\b", re.I),
    re.compile(r"^fetch\b", re.I),
    re.compile(r"^stash\s+list\b", re.I),
    re.compile(r"^config\s+--get\b", re.I),
    re.compile(r"^config\s+--list\b", re.I),
    re.compile(r"^branch\s*$", re.I),
    re.compile(r"^branch\s+-[aAvv]", re.I),
    re.compile(r"^branch\s+--list\b", re.I),
    re.compile(r"^branch\s+--show-current\b", re.I),
    re.compile(r"^branch\s+--contains\b", re.I),
    re.compile(r"^branch\s+--merged\b", re.I),
    re.compile(r"^branch\s+--no-merged\b", re.I),
    re.compile(r"^remote\s*$", re.I),
    re.compile(r"^remote\s+-v\b", re.I),
    re.compile(r"^remote\s+show\b", re.I),
    re.compile(r"^tag\s*$", re.I),
    re.compile(r"^tag\s+-l\b", re.I),
    re.compile(r"^tag\s+--list\b", re.I),
)

INTERPRETER_C = re.compile(
    r"^(?:/usr/bin/)?(?:bash|sh|dash|zsh)\s+(?:-[^\s]+\s+)*-c\s+",
    re.I,
)

PYTHON_C = re.compile(
    r"^(?:/usr/bin/)?(?:python3?|python)\s+(?:-[^\s]+\s+)*-c\s+",
    re.I,
)


def strip_heredocs(command: str) -> str:
    out = command
    while True:
        m = HEREDOC_PATTERN.search(out)
        if not m:
            break
        out = out[: m.start()] + " '' " + out[m.end() :]
    return out


def strip_single_quoted(command: str) -> str:
    return SINGLE_QUOTED.sub("''", command)


def _substitutions_from_double_quoted(segment: str) -> str:
    """Keep $(...) and `...` from inside double quotes; drop literal text."""
    parts: list[str] = []
    i = 0
    n = len(segment)
    while i < n:
        if segment[i : i + 2] == "$(":
            depth = 1
            j = i + 2
            while j < n and depth:
                if segment[j : j + 2] == "$(":
                    depth += 1
                    j += 2
                    continue
                if segment[j] == ")":
                    depth -= 1
                    j += 1
                    continue
                if segment[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                j += 1
            parts.append(segment[i:j])
            i = j
            continue
        if segment[i] == "`":
            j = i + 1
            while j < n and segment[j] != "`":
                if segment[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                j += 1
            if j < n:
                j += 1
            parts.append(segment[i:j])
            i = j
            continue
        i += 1
    return " ".join(parts)


def extract_double_quote_executable(command: str) -> str:
    """Remove double-quoted literals but preserve command substitutions."""
    out: list[str] = []
    i = 0
    n = len(command)
    while i < n:
        if command[i] == '"':
            j = i + 1
            inner: list[str] = []
            while j < n:
                if command[j] == "\\" and j + 1 < n:
                    inner.append(command[j : j + 2])
                    j += 2
                    continue
                if command[j] == '"':
                    break
                inner.append(command[j])
                j += 1
            if j < n:
                j += 1
            subst = _substitutions_from_double_quoted("".join(inner))
            if subst:
                out.append(subst)
            i = j
            continue
        out.append(command[i])
        i += 1
    return "".join(out)


def strip_gh_body_arguments(command: str) -> str:
    """Remove gh --body/-b values including heredocs from scanning surface."""
    stripped = command.strip()
    if not stripped.lower().startswith("gh "):
        return command
    s = re.sub(r"(?i)--body=\S+", " ", command)
    s = re.sub(r"(?i)(?:--body|-b)\b\s+[\s\S]*$", " ", s)
    try:
        parts = shlex.split(s, posix=True)
    except ValueError:
        return strip_heredocs(s)
    if not parts or parts[0].lower() != "gh":
        return strip_heredocs(s)
    out_parts: list[str] = [parts[0]]
    i = 1
    while i < len(parts):
        tok = parts[i]
        low = tok.lower()
        if low in ("--body", "-b"):
            i += 1
            if i < len(parts):
                i += 1
            continue
        if low.startswith("--body="):
            i += 1
            continue
        out_parts.append(tok)
        i += 1
    rebuilt = " ".join(shlex.quote(p) for p in out_parts)
    return strip_heredocs(rebuilt)


def executable_scan_surface(command: str) -> str:
    s = strip_gh_body_arguments(command)
    s = strip_heredocs(s)
    s = strip_single_quoted(s)
    s = extract_double_quote_executable(s)
    return s


def mutators_in_executable(command: str) -> list[re.Pattern[str]]:
    surface = executable_scan_surface(command)
    return [rx for rx in WORKSPACE_MUTATORS if rx.search(surface)]


def _gh_subcommand(parts: list[str]) -> str:
    if len(parts) < 2:
        return ""
    rest = parts[1:]
    if rest[0].lower() == "api":
        return "api"
    if len(rest) >= 2:
        return f"{rest[0].lower()} {rest[1].lower()}"
    return rest[0].lower()


def classify_gh(command: str) -> dict | None:
    try:
        parts = shlex.split(command.strip(), posix=True)
    except ValueError:
        return None
    if not parts or parts[0].lower() != "gh":
        return None
    sub = _gh_subcommand(parts)
    lowered = command.lower()
    if sub == "api":
        for tok in parts[2:]:
            if tok.upper() in ("GET", "HEAD", "VIEW") or tok.startswith("-"):
                continue
            break
        else:
            pass
        method = None
        for tok in parts[2:]:
            u = tok.upper()
            if u in ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"):
                method = u
                break
        if method in (None, "GET", "HEAD"):
            if not mutators_in_executable(command):
                return {"result": "ALLOW", "code": "GH_READONLY_API"}
        return None
    for prefix in GH_READONLY_SUBCOMMAND_PREFIXES:
        if sub == prefix or sub.startswith(prefix + " "):
            if not mutators_in_executable(command):
                return {"result": "ALLOW", "code": "GH_READONLY_SUBCOMMAND"}
            return {"result": "DENY", "code": "GH_READONLY_SUBCOMMAND_EXECUTABLE_MUTATOR"}
    for mut in GH_MUTATING_SUBCOMMANDS:
        if sub == mut or sub.startswith(mut + " "):
            return None
    if mutators_in_executable(command):
        return {"result": "DENY", "code": "GH_UNKNOWN_WITH_EXECUTABLE_MUTATOR"}
    return {"result": "DENY", "code": "GH_UNKNOWN_SUBCOMMAND"}


def _git_tail(stripped: str) -> str:
    tail = stripped
    while True:
        m = re.match(r"^git\s+(?:-C\s+\S+\s+|-c\s+\S+\s+)+", tail, re.I)
        if not m:
            break
        tail = tail[m.end() :]
    if tail.lower().startswith("git "):
        tail = tail[4:]
    return tail.strip()


def _git_readonly_tail(tail: str) -> bool:
    for pattern in GIT_READONLY_TAIL_PATTERNS:
        if pattern.match(tail):
            return True
    return False


def classify_git(command: str) -> dict | None:
    stripped = command.strip()
    if not stripped.lower().startswith("git"):
        return None
    tail = _git_tail(stripped)
    if _git_readonly_tail(tail):
        if not mutators_in_executable(command):
            return {"result": "ALLOW", "code": "GIT_READONLY_INVOCATION"}
    return None


def _extract_interpreter_c_script(command: str) -> str | None:
    stripped = command.strip()
    for pattern in (INTERPRETER_C, PYTHON_C):
        m = pattern.match(stripped)
        if not m:
            continue
        rest = stripped[m.end() :]
        try:
            parts = shlex.split(rest, posix=True)
        except ValueError:
            return None
        if not parts:
            return None
        return parts[0]
    return None


def classify_interpreter_c(command: str) -> dict | None:
    script = _extract_interpreter_c_script(command)
    if script is None:
        return None
    if not mutators_in_executable(script):
        return {"result": "ALLOW", "code": "INTERPRETER_C_NO_MUTATOR"}
    return None


def load_registered(registry_doc: Path, master_internal: Path | None = None) -> set[str]:
    names: set[str] = set()
    if registry_doc.is_file():
        text = registry_doc.read_text(encoding="utf-8")
        for _repo, path in TABLE_ROW.findall(text):
            names.add(Path(path).name)
    if master_internal and master_internal.is_file():
        doc = json.loads(master_internal.read_text(encoding="utf-8"))
        for repo in doc.get("repositories", []):
            path = repo.get("server_project_path")
            if isinstance(path, str) and path.startswith("/home/admin1/projects/"):
                names.add(Path(path).name)
    return names


def extract_paths(command: str) -> list[str]:
    surface = executable_scan_surface(command)
    script = _extract_interpreter_c_script(command)
    if script is not None:
        surface = surface + " " + script
    paths: list[str] = []
    try:
        parts = shlex.split(surface)
    except ValueError:
        parts = surface.split()
    for token in parts:
        if token.startswith("/") or token.startswith("~"):
            paths.append(token)
    return paths


def resolve_path(raw: str, cwd: Path) -> Path | None:
    p = Path(raw.replace("~", str(Path.home())))
    try:
        if not p.is_absolute():
            p = (cwd / p).resolve()
        else:
            p = p.resolve()
    except OSError:
        return None
    return p


def under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _is_nested_full_git_dir(target: Path) -> bool:
    git_entry = target / ".git"
    return git_entry.is_dir()


def classify_path(
    target: Path,
    *,
    projects_root: Path,
    worktrees_root: Path,
    registered: set[str],
) -> tuple[str, str | None]:
    projects_root = projects_root.resolve()
    if under(target, worktrees_root.resolve()):
        return "DENY", "WORKTREES_ROOT_PERSISTENT_CHECKOUT_FORBIDDEN"
    if not under(target, projects_root):
        return "ALLOW", None
    rel = target.relative_to(projects_root)
    parts = rel.parts
    if not parts:
        return "ALLOW", None
    top = parts[0]
    if top in registered and len(parts) == 1:
        return "ALLOW", None
    for name in registered:
        parent = projects_root / name
        if parent.is_dir() and under(target, parent):
            if len(parts) >= 2 and parts[0] == name and _is_nested_full_git_dir(target):
                return "DENY", "DERIVED_REPO_INSIDE_PARENT"
            return "ALLOW", None
    if target.exists() and target.is_dir():
        return "DENY", "UNREGISTERED_TOP_LEVEL_PROJECT_PATH"
    return "DENY", "TOP_LEVEL_CHILD_PROJECT_BLOCKED"


def _has_executable_mutators(command: str) -> bool:
    if mutators_in_executable(command):
        return True
    script = _extract_interpreter_c_script(command)
    if script and mutators_in_executable(script):
        return True
    return False


def _persistent_vcs_checkout(command: str) -> bool:
    """Checkout creation via git or gh. Ordinary scratch files stay allowed."""
    surface = executable_scan_surface(command).lower()
    patterns = (
        r"\bgit\s+clone\b",
        r"\bgit\s+init\b",
        r"\bgit\s+worktree\s+add\b",
        r"\bgh\s+repo\s+clone\b",
    )
    return any(re.search(p, surface) for p in patterns)


def _inside_canonical_parent(
    target: Path,
    *,
    projects_root: Path,
    registered: set[str],
    server_core: Path = DEFAULT_SERVER_CORE,
) -> bool:
    if under(target, server_core.resolve()):
        return True
    projects_root = projects_root.resolve()
    if not under(target, projects_root):
        return False
    parts = target.relative_to(projects_root).parts
    if not parts or parts[0] not in registered:
        return False
    parent = projects_root / parts[0]
    return parent.is_dir() and under(target, parent)


def _copy_like_command(command: str) -> bool:
    return bool(re.search(r"\b(?:cp|rsync|mv)\b", executable_scan_surface(command), re.I))


def _copy_argv_parts(command: str) -> list[str]:
    surface = executable_scan_surface(command)
    try:
        return shlex.split(surface)
    except ValueError:
        return surface.split()


def _copy_endpoints(command: str) -> tuple[list[str], str | None]:
    parts = _copy_argv_parts(command)
    if len(parts) < 2:
        return [], None
    head = parts[0].lower()
    if head not in {"cp", "rsync", "mv"}:
        return [], None
    path_tokens: list[str] = []
    for token in parts[1:]:
        if token.startswith("-"):
            continue
        if token.startswith("/") or token.startswith("~") or token.startswith("."):
            path_tokens.append(token)
    if len(path_tokens) < 2:
        return [], None
    return path_tokens[:-1], path_tokens[-1]


def _registered_project_root(path: Path, projects_root: Path, registered: set[str]) -> Path | None:
    projects_root = projects_root.resolve()
    if not under(path, projects_root):
        return None
    parts = path.relative_to(projects_root).parts
    if not parts or parts[0] not in registered:
        return None
    return projects_root / parts[0]


def _tree_export_source(command: str, source: Path, *, projects_root: Path) -> bool:
    surface = executable_scan_surface(command).lower()
    if re.search(r"\brsync\b", surface):
        return True
    if ".git" in source.parts or source.name == ".git":
        return True
    if re.search(r"\bcp\b", surface) and (
        re.search(r"(?:^|\s)(?:-[a-zA-Z]*[rR]|--recursive|--archive)\b", surface)
        or " -r " in f" {surface} "
        or " -R " in f" {surface} "
        or " -a " in f" {surface} "
    ):
        return True
    if re.search(r"\bmv\b", surface):
        root = projects_root.resolve()
        if under(source, root):
            rel = source.relative_to(root)
            if len(rel.parts) == 1:
                return True
        if under(source, DEFAULT_SERVER_CORE.resolve()):
            if source.name == ".git" or ".git" in source.parts or ".worktrees" in source.parts:
                return True
            if source.resolve() == DEFAULT_SERVER_CORE.resolve():
                return True
        return False
    return False


def _deny_parent_export_copy(
    command: str,
    *,
    cwd: Path,
    projects_root: Path,
    registered: set[str],
) -> dict | None:
    if not _copy_like_command(command):
        return None
    sources, dest_raw = _copy_endpoints(command)
    if not dest_raw:
        return None
    dest = resolve_path(dest_raw, cwd)
    if dest is None:
        return None
    if _inside_canonical_parent(dest, projects_root=projects_root, registered=registered):
        return None
    for src_raw in sources:
        src = resolve_path(src_raw, cwd)
        if src is None:
            continue
        if not _inside_canonical_parent(src, projects_root=projects_root, registered=registered):
            continue
        src_root = _registered_project_root(src, projects_root, registered)
        dest_root = _registered_project_root(dest, projects_root, registered)
        if src_root is not None and dest_root is not None and src_root == dest_root:
            continue
        if under(src, DEFAULT_SERVER_CORE.resolve()) and under(dest, DEFAULT_SERVER_CORE.resolve()):
            continue
        if not _tree_export_source(command, src, projects_root=projects_root):
            continue
        return {
            "result": "DENY",
            "code": "PERSISTENT_COPY_OUTSIDE_PARENT",
            "path": str(dest),
            "source": str(src),
            "command_class": "WORKSPACE_CREATING",
        }
    return None


def _surface_has_git_clone_or_init(command: str) -> tuple[bool, bool]:
    surface = executable_scan_surface(command).lower()
    return (
        bool(re.search(r"\bgit\s+clone\b", surface)),
        bool(re.search(r"\bgit\s+init\b", surface)),
    )


def _extract_relative_mkdir_paths(command: str) -> list[str]:
    surface = executable_scan_surface(command)
    paths: list[str] = []
    try:
        argv_parts = shlex.split(surface)
    except ValueError:
        argv_parts = surface.split()
    for idx, token in enumerate(argv_parts):
        if token == "mkdir" and idx + 1 < len(argv_parts):
            nxt = argv_parts[idx + 1]
            if nxt in ("-p", "-m", "-v") and idx + 2 < len(argv_parts):
                nxt = argv_parts[idx + 2]
            if not nxt.startswith("-") and ".." not in nxt:
                paths.append(nxt)
        if token == "mkdir" and idx + 2 < len(argv_parts) and argv_parts[idx + 1] == "-p":
            nxt = argv_parts[idx + 2]
            if not nxt.startswith("-") and ".." not in nxt:
                paths.append(nxt)
    return paths




def _rehydrate_module():
    spec = importlib.util.spec_from_file_location(
        "gace_mutation_rehydrate_check",
        Path(__file__).resolve().with_name("gace_mutation_rehydrate_check.py"),
    )
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rehydrate_bound_git_write(command: str, cwd: Path) -> dict | None:
    if not os.environ.get("GACE_MUTATION_BINDING", "").strip():
        return None
    mod = _rehydrate_module()
    if mod is None or not mod.is_git_write_command(command):
        return None
    try:
        proc = __import__("subprocess").run(
            [
                __import__("sys").executable,
                str(Path(__file__).resolve().with_name("gace_mutation_rehydrate_check.py")),
                "--mode",
                "mutate",
                "--repo-root",
                str(cwd),
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, __import__("subprocess").TimeoutExpired):
        return {"result": "DENY", "code": "REHYDRATE_CHECK_UNAVAILABLE", "command_class": "GIT_WRITE"}
    try:
        out = json.loads(proc.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return {"result": "DENY", "code": "REHYDRATE_CHECK_INVALID", "command_class": "GIT_WRITE"}
    if out.get("result") == "DENY":
        out.setdefault("command_class", "GIT_WRITE")
        return out
    return None


def classify_command(
    command: str,
    *,
    cwd: Path,
    projects_root: Path,
    worktrees_root: Path,
    registry_doc: Path,
) -> dict:
    rehydrate = _rehydrate_bound_git_write(command, cwd=cwd)
    if rehydrate is not None:
        return rehydrate

    gh_verdict = classify_gh(command)
    if gh_verdict is not None and gh_verdict.get("result") in ("ALLOW", "DENY"):
        return gh_verdict

    git_verdict = classify_git(command)
    if git_verdict is not None:
        return git_verdict

    registered_early = load_registered(
        registry_doc,
        Path(__file__).resolve().parents[1] / "operations" / "master-internal-repositories.json",
    )
    export_verdict = _deny_parent_export_copy(
        command,
        cwd=cwd,
        projects_root=projects_root,
        registered=registered_early,
    )
    if export_verdict is not None:
        return export_verdict

    interp = classify_interpreter_c(command)
    if interp is not None and interp.get("result") == "ALLOW":
        return interp

    if not _has_executable_mutators(command):
        return {"result": "ALLOW", "code": "NOT_WORKSPACE_MUTATION_COMMAND"}

    try:
        shlex.split(command)
    except ValueError:
        if command.strip().lower().startswith(("gh ", "git ", "bash ", "sh ")):
            return {"result": "DENY", "code": "UNPARSEABLE_DANGEROUS_COMMAND"}

    registered = load_registered(
        registry_doc,
        Path(__file__).resolve().parents[1] / "operations" / "master-internal-repositories.json",
    )
    is_clone, is_init = _surface_has_git_clone_or_init(command)
    paths = extract_paths(command)
    paths.extend(_extract_relative_mkdir_paths(command))
    seen: set[str] = set()
    paths = [p for p in paths if not (p in seen or seen.add(p))]
    if not paths:
        return {"result": "DENY", "code": "WORKSPACE_MUTATION_WITHOUT_RESOLVED_PATH"}
    projects_root_resolved = projects_root.resolve()
    for raw in paths:
        if ".." in raw:
            return {"result": "DENY", "code": "PATH_TRAVERSAL", "path": raw, "command_class": "WORKSPACE_CREATING"}
        resolved = resolve_path(raw, cwd)
        if resolved is None:
            return {"result": "DENY", "code": "PATH_UNRESOLVED"}
        if under(resolved, projects_root_resolved):
            rel = resolved.relative_to(projects_root_resolved)
            if len(rel.parts) >= 2 and (is_clone or is_init):
                parent_name = rel.parts[0]
                if parent_name in registered and ".worktrees" not in resolved.parts:
                    return {
                        "result": "DENY",
                        "code": "DERIVED_REPO_INSIDE_PARENT",
                        "path": str(resolved),
                        "command_class": "WORKSPACE_CREATING",
                    }
        verdict, code = classify_path(
            resolved,
            projects_root=projects_root,
            worktrees_root=worktrees_root,
            registered=registered,
        )
        if verdict == "DENY":
            return {
                "result": "DENY",
                "code": code,
                "path": str(resolved),
                "command_class": "WORKSPACE_CREATING",
            }
        if _persistent_vcs_checkout(command) and not _inside_canonical_parent(
            resolved,
            projects_root=projects_root,
            registered=registered,
        ):
            return {
                "result": "DENY",
                "code": "PERSISTENT_CHECKOUT_OUTSIDE_PARENT",
                "path": str(resolved),
                "command_class": "WORKSPACE_CREATING",
            }
        server_core = DEFAULT_SERVER_CORE.resolve()
        if (
            (is_clone or is_init)
            and under(resolved, server_core)
            and resolved != server_core
            and ".worktrees" not in resolved.parts
        ):
            return {
                "result": "DENY",
                "code": "DERIVED_REPO_INSIDE_PARENT",
                "path": str(resolved),
                "command_class": "WORKSPACE_CREATING",
            }
    return {"result": "ALLOW", "code": "WORKSPACE_PATHS_VERIFIED"}


def parse_hook_payload(raw: str) -> tuple[str | None, Path | None, str | None]:
    if not raw.strip():
        return None, None, "HOOK_INPUT_EMPTY"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, None, "HOOK_INPUT_INVALID_JSON"
    if not isinstance(data, dict):
        return None, None, "HOOK_INPUT_INVALID_SHAPE"
    command = data.get("command")
    if not isinstance(command, str) or not command.strip():
        return None, None, "HOOK_INPUT_MISSING_COMMAND"
    cwd_raw = (
        data.get("cwd")
        or data.get("workingDirectory")
        or data.get("working_directory")
        or data.get("workspaceFolder")
        or "/home/admin1"
    )
    if not isinstance(cwd_raw, str) or not cwd_raw.strip():
        return None, None, "HOOK_INPUT_INVALID_CWD"
    return command.strip(), Path(cwd_raw).expanduser(), None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command")
    parser.add_argument("--cwd", default="/home/admin1")
    parser.add_argument("--projects-root", type=Path, default=DEFAULT_PROJECTS)
    parser.add_argument("--worktrees-root", type=Path, default=DEFAULT_WORKTREES)
    parser.add_argument(
        "--registry-doc",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "WORKSPACE_REGISTRY.md",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--hook-stdin",
        action="store_true",
        help="Read Cursor beforeShellExecution JSON from stdin and classify once.",
    )
    args = parser.parse_args()

    if args.hook_stdin:
        command, cwd, err = parse_hook_payload(__import__("sys").stdin.read())
        if err:
            out = {"result": "DENY", "code": err, "command_class": "HOOK_INPUT"}
            print(json.dumps(out, sort_keys=True))
            return 1
        assert command is not None and cwd is not None
    else:
        if not args.command:
            parser.error("--command is required unless --hook-stdin is set")
        command = args.command
        cwd = Path(args.cwd)

    out = classify_command(
        command,
        cwd=cwd,
        projects_root=args.projects_root,
        worktrees_root=args.worktrees_root,
        registry_doc=args.registry_doc,
    )
    print(json.dumps(out, sort_keys=True))
    return 0 if out.get("result") == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
