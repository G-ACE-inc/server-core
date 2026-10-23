#!/usr/bin/env python3
"""Use a new, commit-unique CHAT request as a workspace-only Actions target."""
import json
import shlex
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

try:
    from scripts.chat_host_command_prepare import validate_command
except ModuleNotFoundError:
    from chat_host_command_prepare import validate_command

PREFIX = ".github/chat-host-requests/"
REQUEST = re.compile(r"^[.]github/chat-host-requests/req_[a-f0-9]{24}[.]json$")
TARGET = Path("/tmp/gace-common-host-request.json")
LEGACY_TARGET = ".github/chatgpt-live-api-target.json"
# Leave headroom for JSON escaping/envelope and generated source preflight
# within the Receiver's 1 MiB request boundary; never slice command text.
MAX_REQUEST_FILE_BYTES = 262144

def select(added, changed):
    candidates = [p for p in changed if p.startswith(PREFIX)]
    if not candidates:
        return None
    if len(candidates) != 1 or not REQUEST.fullmatch(candidates[0]):
        raise ValueError("REQUEST_PATH_DENIED")
    if candidates[0] not in added or LEGACY_TARGET in changed:
        raise ValueError("REQUEST_MUST_BE_NEW_AND_SEPARATE")
    return Path(candidates[0])

def git_paths(filter_added=False):
    cmd = ["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r"]
    if filter_added:
        cmd += ["--diff-filter=A"]
    cmd += ["HEAD"]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
    if result.returncode:
        raise ValueError("GIT_DIFF_FAILED")
    return result.stdout.splitlines()

def bind_source_context(bounded, context):
    """Bind an explicitly chosen project checkout without changing Host admission.

    Optional for ordinary freeform commands. For source-sensitive diagnostics,
    require the actual existing worktree HEAD and the source files on which
    the command depends, before the command can run. This reuses the existing
    Host writer and does not create a worktree, token or additional Gate.
    """
    if bounded.get("command_id") != "host.command" or not isinstance(context, dict):
        raise ValueError("SOURCE_CONTEXT_INVALID")
    if set(context) != {"repository", "workdir", "source_sha", "required_files"}:
        raise ValueError("SOURCE_CONTEXT_KEYS_INVALID")
    repository = bounded.get("repository")
    if repository != context.get("repository"):
        raise ValueError("SOURCE_CONTEXT_REPOSITORY_MISMATCH")
    sha = context.get("source_sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("SOURCE_CONTEXT_SHA_INVALID")
    root_map = json.loads(
        (Path(__file__).resolve().parents[1] /
         "operations/github-project-bounded-host.json").read_text(encoding="utf-8")
    ).get("dev_job", {}).get("registered_repositories", {})
    registered = root_map.get(repository)
    if not isinstance(registered, dict):
        raise ValueError("SOURCE_CONTEXT_REPO_UNREGISTERED")
    root_str = registered.get("root")
    target_str = context.get("workdir")
    if (not isinstance(root_str, str) or not isinstance(target_str, str)
            or not 1 <= len(target_str) <= 256
            or any(c in target_str for c in ("\n", "\r", "\x00"))):
        raise ValueError("SOURCE_CONTEXT_WORKDIR_INVALID")
    root, target = PurePosixPath(root_str), PurePosixPath(target_str)
    if (not target.is_absolute() or not root.is_absolute()
            or any(part in ("..", ".") for part in target_str.split("/"))):
        raise ValueError("SOURCE_CONTEXT_WORKDIR_INVALID")
    # Existing worktrees may be siblings beneath the registered checkout's
    # .worktrees parent. This validates *paths*, never creates new checkouts.
    parts = root.parts
    if ".worktrees" in parts:
        existing_parent = PurePosixPath(*parts[:parts.index(".worktrees") + 1])
    else:
        existing_parent = root / ".worktrees"
    allowed = (target == root or
               (target.parts[:len(existing_parent.parts)] == existing_parent.parts
                and len(target.parts) == len(existing_parent.parts) + 1))
    if not allowed:
        raise ValueError("SOURCE_CONTEXT_WORKDIR_OUTSIDE_REGISTERED_CHECKOUT")
    files = context.get("required_files")
    if (not isinstance(files, list) or len(files) > 16
            or any(not isinstance(p, str) or not p or len(p) > 200
                   or p.startswith("/") or
                   any(bit in ("", ".", "..") for bit in p.split("/"))
                   or "\x00" in p or "\n" in p or "\r" in p
                   for p in files)):
        raise ValueError("SOURCE_CONTEXT_REQUIRED_FILES_INVALID")
    original = bounded.get("command")
    if not isinstance(original, str) or not original.strip():
        raise ValueError("SOURCE_CONTEXT_COMMAND_INVALID")
    quoted_root, quoted_sha = shlex.quote(target_str), shlex.quote(sha)
    quoted_registered = shlex.quote(root_str)
    preflight = [
        "(",
        "cd " + quoted_root + " 2>/dev/null || { echo CHAT_SOURCE_WORKDIR_MISSING >&2; exit 70; }",
        '_gace_source_root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo CHAT_SOURCE_GIT_UNAVAILABLE >&2; exit 71; }',
        '[ "$_gace_source_root" = ' + quoted_root + ' ] || { echo CHAT_SOURCE_ROOT_MISMATCH >&2; exit 72; }',
        '_gace_registered_common="$(git -C ' + quoted_registered + ' rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || { echo CHAT_SOURCE_GIT_UNAVAILABLE >&2; exit 71; }',
        '_gace_actual_common="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || { echo CHAT_SOURCE_GIT_UNAVAILABLE >&2; exit 71; }',
        '_gace_registered_real="$(realpath -e "$_gace_registered_common" 2>/dev/null)" || { echo CHAT_SOURCE_GIT_UNAVAILABLE >&2; exit 71; }',
        '_gace_actual_real="$(realpath -e "$_gace_actual_common" 2>/dev/null)" || { echo CHAT_SOURCE_GIT_UNAVAILABLE >&2; exit 71; }',
        '[ "$_gace_actual_real" = "$_gace_registered_real" ] || { echo CHAT_SOURCE_ROOT_MISMATCH >&2; exit 72; }',
        '_gace_source_sha="$(git rev-parse HEAD 2>/dev/null)" || { echo CHAT_SOURCE_SHA_UNAVAILABLE >&2; exit 73; }',
        '[ "$_gace_source_sha" = ' + quoted_sha + ' ] || { echo CHAT_SOURCE_SHA_MISMATCH >&2; exit 74; }',
        '_gace_dirty="$(git status --porcelain --untracked-files=all 2>/dev/null)" || { echo CHAT_SOURCE_GIT_UNAVAILABLE >&2; exit 71; }',
        '[ -z "$_gace_dirty" ] || { echo CHAT_SOURCE_DIRTY_WORKTREE >&2; exit 76; }',
    ]
    for path in files:
        preflight.append("test -f " + shlex.quote(path) +
                         " || { echo CHAT_SOURCE_REQUIRED_FILE_MISSING >&2; exit 75; }")
    # Writer strips this protected-prefix from the captured stdout. Its
    # presence proves the source checks passed before the user command ran.
    preflight += ["printf '__GACE_SOURCE_PREFLIGHT_OK__\\n'", original, ")"]
    return {**bounded, "command": "\n".join(preflight)}


def prepare(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("REQUEST_FILE_INVALID")
    if path.stat().st_size > MAX_REQUEST_FILE_BYTES:
        raise ValueError("REQUEST_FILE_TOO_LARGE")
    data = json.loads(path.read_text(encoding="utf-8"))
    return prepare_data(data)


def prepare_data(data, *, command_diagnostics=None):
    if not isinstance(data, dict) or data.get("bounded_host_request", {}).get("enabled") is not True:
        raise ValueError("REQUEST_NOT_ENABLED")
    if data.get("chat_decision_checkpoint", {}).get("phase") != "START":
        raise ValueError("START_RECEIPT_MISSING")
    if data.get("gitops_request", {}).get("enabled") is not False or data.get("source_reflect_request", {}).get("enabled") is not False:
        raise ValueError("CONCURRENT_EFFECT_DENIED")
    if data.get("server_command_id") or data.get("run_id"):
        raise ValueError("OTHER_COMMAND_DENIED")
    bounded = data["bounded_host_request"]
    if "source_preflight" in bounded:
        raise ValueError("SOURCE_PREFLIGHT_INTERNAL_ONLY")
    if "source_context" in bounded:
        data["bounded_host_request"] = bounded = bind_source_context(
            bounded, bounded["source_context"])
        # Source context is a planning input; Host receives only freeform
        # command, repo, and both authenticated independent SHA pins.
        bounded.pop("source_context", None)
        bounded["source_preflight"] = True
    # The dispatcher and target checkout are the same for server-core itself.
    # Reject contradictory pins before enqueuing a doomed Host operation.
    if bounded.get("command_id") == "host.command" and bounded.get("repository") == "G-ACE-inc/server-core":
        if bounded.get("expected_sha") != bounded.get("repo_sha"):
            raise ValueError("SERVER_CORE_HOST_SHA_PINS_CONFLICT")
    if bounded.get("command_id") == "host.command":
        evidence = validate_command(bounded.get("command"))
        if command_diagnostics is not None:
            command_diagnostics.update(evidence)
    return data

def main():
    try:
        selected = select(git_paths(True), git_paths())
        if selected is None:
            print("CHAT_ISOLATED_REQUEST=NONE")
            return 0
        data = prepare(selected)
        TARGET.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("CHAT_ISOLATED_REQUEST=SELECTED")
        print("CHAT_ISOLATED_REQUEST_FILE=" + str(selected))
        return 0
    except (ValueError, TypeError, AttributeError, OSError, subprocess.TimeoutExpired) as exc:
        print("CHAT_ISOLATED_REQUEST=DENIED")
        print("CHAT_ISOLATED_REQUEST_ERROR=" + str(exc)[:100])
        return 1

if __name__ == "__main__":
    sys.exit(main())
