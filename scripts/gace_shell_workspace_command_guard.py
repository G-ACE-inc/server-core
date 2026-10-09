#!/usr/bin/env python3
"""Read-only shell command classifier for G-ACE workspace proliferation gates."""
from __future__ import annotations

import argparse
import json
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

READONLY_GIT_PREFIXES = (
    "git status",
    "git diff",
    "git log",
    "git show",
    "git branch",
    "git rev-parse",
    "git remote",
    "git fetch",
    "git ls-files",
    "git ls-remote",
    "git grep",
    "git blame",
    "git describe",
    "git tag",
    "git stash list",
    "git config --get",
    "git config --list",
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
    return {"result": "ALLOW", "code": "GH_NO_EXECUTABLE_MUTATOR"}


def _git_readonly_tail(tail: str) -> bool:
    t = tail.strip().lower()
    for prefix in READONLY_GIT_PREFIXES:
        p = prefix[4:].strip() if prefix.startswith("git ") else prefix
        if t == p or t.startswith(p + " "):
            return True
    readonly_ops = (
        "status",
        "diff",
        "log",
        "show",
        "branch",
        "rev-parse",
        "remote",
        "fetch",
        "ls-files",
        "ls-remote",
        "grep",
        "blame",
        "describe",
        "tag",
        "stash list",
        "config --get",
        "config --list",
    )
    first = t.split()[0] if t.split() else ""
    if first in readonly_ops:
        return True
    if t.startswith("status") or t.startswith("diff") or t.startswith("log"):
        return True
    return False


def classify_git(command: str) -> dict | None:
    stripped = command.strip()
    lowered = stripped.lower()
    if lowered.startswith("git -c ") or lowered.startswith("git -C "):
        m = re.match(r"^git\s+-[Cc]\s+\S+\s+(.*)$", stripped, re.I | re.DOTALL)
        if m and _git_readonly_tail(m.group(1)):
            if not mutators_in_executable(command):
                return {"result": "ALLOW", "code": "GIT_READONLY_INVOCATION"}
    for prefix in READONLY_GIT_PREFIXES:
        if lowered.startswith(prefix) or lowered == prefix.strip():
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
    if top in registered:
        return "ALLOW", None
    for name in registered:
        parent = projects_root / name
        if parent.is_dir() and under(target, parent):
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


def classify_command(
    command: str,
    *,
    cwd: Path,
    projects_root: Path,
    worktrees_root: Path,
    registry_doc: Path,
) -> dict:
    gh_verdict = classify_gh(command)
    if gh_verdict is not None and gh_verdict.get("result") in ("ALLOW", "DENY"):
        return gh_verdict

    git_verdict = classify_git(command)
    if git_verdict is not None:
        return git_verdict

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
    paths = extract_paths(command)
    if not paths:
        return {"result": "DENY", "code": "WORKSPACE_MUTATION_WITHOUT_RESOLVED_PATH"}
    for raw in paths:
        if ".." in raw or raw.startswith("./") and ".." in raw:
            return {"result": "DENY", "code": "PATH_TRAVERSAL", "path": raw, "command_class": "WORKSPACE_CREATING"}
        resolved = resolve_path(raw, cwd)
        if resolved is None:
            return {"result": "DENY", "code": "PATH_UNRESOLVED"}
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
    return {"result": "ALLOW", "code": "WORKSPACE_PATHS_VERIFIED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", required=True)
    parser.add_argument("--cwd", default="/home/admin1")
    parser.add_argument("--projects-root", type=Path, default=DEFAULT_PROJECTS)
    parser.add_argument("--worktrees-root", type=Path, default=DEFAULT_WORKTREES)
    parser.add_argument(
        "--registry-doc",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs" / "WORKSPACE_REGISTRY.md",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    out = classify_command(
        args.command,
        cwd=Path(args.cwd),
        projects_root=args.projects_root,
        worktrees_root=args.worktrees_root,
        registry_doc=args.registry_doc,
    )
    print(json.dumps(out, sort_keys=True))
    return 0 if out.get("result") == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
