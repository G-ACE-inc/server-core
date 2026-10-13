#!/usr/bin/env python3
"""Trusted Host-side Docker provisioner for isolated development jobs (UNIX socket only).

Design authority: docs/SERVER_CORE_DESIGN.md section 16.11. Separate admin1 user-level Host
service so the low-privilege Receiver and the executed code never hold Docker authority.

One generic job = one disposable non-root container (no network, read-only rootfs, all caps
dropped, bounded CPU/memory/pids/time/output) whose ONLY mount is a per-session workspace that
is a git clone nested inside the registered canonical parent (`<root>/.worktrees/dev-jobs/<session>`).
Admission (all fail closed): committed contract `dev_job` registry, committed design digest,
registered repository/owner/branch, exact Host HEAD == expected_sha, strict ids, argv bounds,
replay record, per-session lock. The host never runs git inside a workspace after creation
(workspace content is untrusted); inspection of the workspace runs inside the sandbox too.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socketserver
import stat
import subprocess
import threading
import time

SOCKET_PATH = Path("/run/gace/servercore-dev-job.sock")
ROOT = Path("/home/admin1/server-core")
STATE_DIR = Path("/home/admin1/logs/servercore-dev-jobs")
CONTRACT_REL = "operations/github-project-bounded-host.json"
DESIGN_REL = "docs/SERVER_CORE_DESIGN.md"
DESIGN_HEADING = "### 16.11 "
SCHEMA = "gace.servercore-dev-job.request/v1"
KEYS = {"schema", "id", "repository", "expected_sha", "session", "argv", "timeout_s", "fresh"}
REQ_ID = re.compile(r"^req_[0-9a-f]{24}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
EXECUTABLE = re.compile(r"^[a-z][a-z0-9_.-]{0,31}$")
MAX_REQUEST = 4096
MAX_ARGV = 8
MAX_ARG_CHARS = 1200
MAX_ARGV_TOTAL = 2400
MAX_TIMEOUT = 15
CAPTURE_CAP = 256 * 1024
RESULT_CHARS = 8000
MAX_SESSIONS = 8
SESSION_TTL_SECONDS = 24 * 3600
SESSION_EVICT_IDLE_SECONDS = 3600  # at the cap only sessions idle this long may be reclaimed (active work is protected)
WORKSPACE_BYTES = 200 * 1024 * 1024
DOCKER_CANDIDATES = ("/usr/bin/docker", "/usr/local/bin/docker")
CLEAN_ENV = {"PATH": "/usr/bin:/bin", "HOME": "/home/admin1"}
_SLOTS = threading.BoundedSemaphore(2)


class JobError(Exception):
    pass


def git(root, *args, runner=subprocess.run):
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
           "-c", "safe.directory=" + str(root), "-C", str(root), *args]
    try:
        return runner(cmd, capture_output=True, text=True, timeout=30, check=False, env=CLEAN_ENV)
    except (OSError, subprocess.TimeoutExpired):
        raise JobError("HOST_GIT_FAILED") from None


def committed_text(root, rel):
    result = git(root, "show", "HEAD:" + rel)
    if result.returncode:
        raise JobError("COMMITTED_FILE_MISSING")
    return result.stdout


def design_section_digest(text):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(DESIGN_HEADING)), None)
    if start is None:
        raise JobError("DESIGN_NOT_VERIFIED")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## ") or lines[i].startswith("### "):
            end = i
            break
    return hashlib.sha256("\n".join(lines[start:end]).rstrip().encode("utf-8")).hexdigest()


def load_policy(root=ROOT):
    """Authority is the COMMITTED contract + COMMITTED design section at Host HEAD only."""
    try:
        contract = json.loads(committed_text(root, CONTRACT_REL))
        policy = contract["dev_job"]
    except (ValueError, KeyError, TypeError):
        raise JobError("CONTRACT_INVALID") from None
    if "dev.job" not in (contract.get("allowed_command_ids") or []) or contract.get("command_effects", {}).get("dev.job") != "dev_job":
        raise JobError("COMMAND_NOT_REGISTERED")
    for key in ("image", "design_section_sha256", "registered_repositories", "allowed_executables"):
        if key not in policy:
            raise JobError("CONTRACT_INVALID")
    if design_section_digest(committed_text(root, DESIGN_REL)) != policy["design_section_sha256"]:
        raise JobError("DESIGN_NOT_VERIFIED")
    return policy


def validate(value, policy):
    if not isinstance(value, dict) or set(value) != KEYS or value.get("schema") != SCHEMA:
        raise JobError("REQUEST_SHAPE_INVALID")
    for key in ("id", "session"):
        if not isinstance(value[key], str) or not REQ_ID.fullmatch(value[key]):
            raise JobError("REQUEST_ID_INVALID" if key == "id" else "SESSION_INVALID")
    if not isinstance(value["expected_sha"], str) or not SHA.fullmatch(value["expected_sha"]):
        raise JobError("EXPECTED_SHA_INVALID")
    repository = value["repository"]
    if not isinstance(repository, str) or not REPO.fullmatch(repository):
        raise JobError("REPOSITORY_INVALID")
    entry = (policy.get("registered_repositories") or {}).get(repository)
    if not isinstance(entry, dict) or repository.split("/")[0] != entry.get("owner"):
        raise JobError("REPOSITORY_NOT_REGISTERED")
    argv = value["argv"]
    if not isinstance(argv, list) or not 1 <= len(argv) <= MAX_ARGV \
            or any(not isinstance(a, str) or not 1 <= len(a) <= MAX_ARG_CHARS or "\x00" in a for a in argv) \
            or sum(len(a) for a in argv) > MAX_ARGV_TOTAL:
        raise JobError("ARGV_INVALID")
    if not EXECUTABLE.fullmatch(argv[0]) or argv[0] not in policy["allowed_executables"]:
        raise JobError("EXECUTABLE_NOT_ALLOWED")
    if type(value["timeout_s"]) is not int or not 1 <= value["timeout_s"] <= MAX_TIMEOUT:
        raise JobError("TIMEOUT_INVALID")
    if type(value["fresh"]) is not bool:
        raise JobError("FRESH_INVALID")
    return value, entry


def check_registered_root(entry, root=ROOT):
    path = Path(str(entry.get("root", "")))
    if not path.is_absolute() or path != Path(os.path.realpath(path)) or path.is_symlink() or not (path / ".git").is_dir():
        raise JobError("REGISTERED_ROOT_DENIED")
    if path != Path(root) and not str(path).startswith("/home/admin1/projects/"):
        raise JobError("REGISTERED_ROOT_DENIED")
    return path


def check_head(root, entry, expected_sha):
    head = git(root, "rev-parse", "HEAD")
    branch = git(root, "symbolic-ref", "--short", "-q", "HEAD")
    if head.returncode or head.stdout.strip() != expected_sha:
        raise JobError("STALE_SHA")
    registered = entry.get("branch")
    branches = entry.get("allowed_branches", [registered])
    if (not isinstance(branches, list) or not branches or
            any(not isinstance(b, str) or not b or b.startswith("-") for b in branches) or
            registered not in branches):
        raise JobError("REGISTERED_BRANCHES_INVALID")
    if branch.returncode == 0:
        if branch.stdout.strip() not in branches:
            raise JobError("BRANCH_NOT_REGISTERED")
        return
    # Detached HEAD must match a registered branch tip exactly.
    for registered_branch in branches:
        for ref in (registered_branch, "origin/" + registered_branch,
                    "refs/heads/" + registered_branch, "refs/remotes/origin/" + registered_branch):
            tip = git(root, "rev-parse", "-q", ref)
            if tip.returncode == 0 and tip.stdout.strip() == head.stdout.strip():
                return
    raise JobError("BRANCH_NOT_REGISTERED")


def _real_dir(path):
    info = os.lstat(path)
    return stat.S_ISDIR(info.st_mode)


def workspace_base(registered_root):
    """`<root>/.worktrees/dev-jobs`, created with no symlink component; always strictly inside root."""
    current = Path(registered_root)
    for part in (".worktrees", "dev-jobs"):
        current = current / part
        if current.is_symlink():
            raise JobError("WORKSPACE_PATH_SYMLINK_DENIED")
        if not current.exists():
            current.mkdir(mode=0o755)
            os.chmod(current, 0o755)
        elif not _real_dir(current):
            raise JobError("WORKSPACE_PATH_DENIED")
    if not str(os.path.realpath(current)).startswith(str(registered_root) + "/"):
        raise JobError("WORKSPACE_ESCAPE_DENIED")
    return current


def workspace_path(base, session):
    if not REQ_ID.fullmatch(session):
        raise JobError("SESSION_INVALID")
    path = Path(base) / session
    if path.is_symlink() or (path.exists() and not _real_dir(path)):
        raise JobError("WORKSPACE_PATH_SYMLINK_DENIED")
    if os.path.dirname(os.path.realpath(path)) != os.path.realpath(base):
        raise JobError("WORKSPACE_ESCAPE_DENIED")
    return path


def docker_binary(candidates=DOCKER_CANDIDATES):
    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise JobError("DOCKER_BINARY_MISSING")


def sandbox_argv(binary, name, workspace, image, argv):
    """The ONLY docker invocation shape. No input field can add a mount, network, env or capability."""
    return [binary, "run", "--rm", "--name", name, "--pull", "never", "--network", "none",
            "--user", "1000:1000", "--read-only", "--tmpfs", "/tmp:rw,size=64m,mode=1777",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
            "--pids-limit", "128", "--memory", "512m", "--memory-swap", "512m", "--cpus", "1",
            "--label", "gace.dev-job=1",
            "--mount", "type=bind,src=%s,dst=/work" % workspace, "--workdir", "/work",
            "-e", "HOME=/tmp", "-e", "GIT_CONFIG_NOSYSTEM=1", "-e", "GIT_CONFIG_GLOBAL=/dev/null",
            "-e", "GIT_CONFIG_COUNT=1", "-e", "GIT_CONFIG_KEY_0=safe.directory", "-e", "GIT_CONFIG_VALUE_0=/work",
            "--entrypoint", argv[0], image, *argv[1:]]


def run_bounded(argv, timeout, kill_argv=None):
    """Run with wall-clock and output bounds. Returns (rc, stdout, stderr, timed_out, output_exceeded)."""
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=CLEAN_ENV)
    buffers = {"out": bytearray(), "err": bytearray()}
    exceeded = threading.Event()

    def pump(stream, key):
        while True:
            chunk = stream.read(4096)
            if not chunk:
                return
            room = CAPTURE_CAP - len(buffers[key])
            buffers[key].extend(chunk[:max(room, 0)])
            if len(chunk) > room:
                exceeded.set()
                proc.kill()
                return

    threads = [threading.Thread(target=pump, args=(proc.stdout, "out"), daemon=True),
               threading.Thread(target=pump, args=(proc.stderr, "err"), daemon=True)]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait()
    for thread in threads:
        thread.join(timeout=5)
    proc.stdout.close()
    proc.stderr.close()
    if (timed_out or exceeded.is_set()) and kill_argv:
        subprocess.run(kill_argv, capture_output=True, timeout=15, check=False, env=CLEAN_ENV)
    return (124 if timed_out else proc.returncode), bytes(buffers["out"]), bytes(buffers["err"]), timed_out, exceeded.is_set()


def _text(data, limit=RESULT_CHARS):
    text = data.decode("utf-8", errors="replace")
    return text[-limit:] if len(text) > limit else text


def workspace_bytes(path):
    total = 0
    for current, dirs, files in os.walk(path, followlinks=False):
        for name in files + dirs:
            try:
                total += os.lstat(os.path.join(current, name)).st_size
            except OSError:
                pass
    return total


def _session_lock_free(state_dir, name):
    """True when no running job holds the session lock (a missing lock file means nothing is running)."""
    if state_dir is None:
        return True
    lock_path = Path(state_dir) / (name + ".lock")
    if not lock_path.is_file() or lock_path.is_symlink():
        return True
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW)
    except OSError:
        return False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    finally:
        os.close(fd)
    return True


def prune_sessions(base, keep, now=None, state_dir=None):
    now = time.time() if now is None else now
    entries = [p for p in Path(base).iterdir() if REQ_ID.fullmatch(p.name) and not p.is_symlink() and p.is_dir()]
    for path in entries:
        if path.name != keep and now - path.stat().st_mtime > SESSION_TTL_SECONDS \
                and _session_lock_free(state_dir, path.name):
            shutil.rmtree(path, ignore_errors=True)
    live = sorted((p for p in Path(base).iterdir()
                   if REQ_ID.fullmatch(p.name) and not p.is_symlink() and p.is_dir() and p.name != keep),
                  key=lambda p: p.stat().st_mtime)
    # At the cap, reclaim the least recently used IDLE sessions (oldest first, never a running one, never recent work)
    # instead of blocking every new session until the 24 h TTL; the cap itself is unchanged.
    for path in list(live):
        if len(live) < MAX_SESSIONS:
            break
        if now - path.stat().st_mtime > SESSION_EVICT_IDLE_SECONDS and _session_lock_free(state_dir, path.name):
            shutil.rmtree(path, ignore_errors=True)
            live.remove(path)
    if len(live) >= MAX_SESSIONS:
        raise JobError("SESSION_LIMIT_REACHED")


def create_workspace(root, workspace, sha, runner=subprocess.run):
    """Clone from the TRUSTED canonical repo's commits only (dirty working-tree bytes never enter)."""
    steps = (
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "init.templateDir=/nonexistent", "-c", "safe.directory=" + str(root),
         "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(root), str(workspace)],
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(workspace), "checkout", "--quiet", "--detach", sha],
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(workspace), "remote", "remove", "origin"],
    )
    for step in steps:
        try:
            # Only these fixed git children get a traversable umask (the process keeps 0117 for the socket and
            # private state); subprocess applies it in the child, so no process-wide umask swap in this threaded server.
            result = runner(step, capture_output=True, text=True, timeout=60, check=False, env=CLEAN_ENV,
                            umask=0o022)
        except (OSError, subprocess.TimeoutExpired):
            shutil.rmtree(workspace, ignore_errors=True)
            raise JobError("WORKSPACE_CREATE_FAILED") from None
        if result.returncode:
            shutil.rmtree(workspace, ignore_errors=True)
            raise JobError("WORKSPACE_CREATE_FAILED")
    os.chmod(workspace, 0o755)


def state_paths(state_dir, request_id, session):
    return (Path(state_dir) / (request_id + ".json"), Path(state_dir) / (session + ".meta.json"),
            Path(state_dir) / (session + ".lock"))


def _write_private(path, data):
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True, separators=(",", ":")))
    os.replace(tmp, path)


def execute(request, entry, policy, registered_root, *, state_dir=STATE_DIR, binary=None, runner=run_bounded,
            clone=create_workspace):
    state_dir = Path(state_dir)
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(state_dir, 0o700)
    record_path, meta_path, lock_path = state_paths(state_dir, request["id"], request["session"])
    if record_path.is_file() and not record_path.is_symlink():  # replay: never re-execute
        return {**json.loads(record_path.read_text(encoding="utf-8")), "replayed": True}
    if not _SLOTS.acquire(blocking=False):
        raise JobError("DEV_JOB_BUSY")
    lock = None
    try:
        lock = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise JobError("DEV_JOB_BUSY") from None
        started = time.monotonic()
        base = workspace_base(registered_root)
        workspace = workspace_path(base, request["session"])
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() and workspace.exists() else None
        if meta is not None:
            os.utime(workspace)  # mark the session as recently used (idle clock for TTL and reclamation)
        if request["fresh"] or meta is None:
            if workspace.exists():
                shutil.rmtree(workspace)
            prune_sessions(base, request["session"], state_dir=state_dir)
            clone(registered_root, workspace, request["expected_sha"])
            _write_private(meta_path, {"base_sha": request["expected_sha"], "repository": request["repository"]})
        elif meta.get("base_sha") != request["expected_sha"] or meta.get("repository") != request["repository"]:
            raise JobError("SESSION_BASE_MISMATCH")
        docker = binary or docker_binary()
        image = policy["image"]

        def sandbox(argv, name, timeout):
            cmd = sandbox_argv(docker, name, str(workspace), image, argv)
            return runner(cmd, timeout, [docker, "kill", name])

        rc, out, err, timed_out, exceeded = sandbox(request["argv"], "gace-devjob-" + request["id"][4:], request["timeout_s"])
        info = {}
        for key, argv in (("head", ["git", "rev-parse", "HEAD"]),
                          ("status", ["git", "status", "--porcelain=v1"]),
                          ("diff", ["git", "diff", "--shortstat", "HEAD"])):
            r = sandbox(argv, "gace-devjob-%s-%s" % (key, request["id"][4:16]), 10)
            info[key] = _text(r[1], 4000).rstrip("\n") if r[0] == 0 else "UNKNOWN"
        removed = False
        if workspace_bytes(workspace) > WORKSPACE_BYTES:
            shutil.rmtree(workspace, ignore_errors=True)
            removed = True
        changed = [line[:100] for line in info["status"].splitlines()[:15]] if info["status"] != "UNKNOWN" else []
        result = {
            "request_id": request["id"], "session": request["session"], "repository": request["repository"],
            "project_item": entry.get("project_item", ""), "base_sha": request["expected_sha"],
            "workspace_head": info["head"][:40], "job_exit": rc, "timed_out": timed_out,
            "output_limit_exceeded": exceeded, "workspace_budget_exceeded": removed,
            "stdout_truncated": len(out.decode("utf-8", errors="replace")) > RESULT_CHARS,
            "stderr_truncated": len(err.decode("utf-8", errors="replace")) > RESULT_CHARS,
            "stdout": _text(out), "stderr": _text(err), "changed": changed, "diff_stat": info["diff"][:200],
            "duration_ms": int((time.monotonic() - started) * 1000), "replayed": False,
        }
        _write_private(record_path, result)
        return result
    finally:
        if lock is not None:
            os.close(lock)
        _SLOTS.release()


def handle_request(value, *, root=ROOT, **kwargs):
    policy = load_policy(root)
    request, entry = validate(value, policy)
    registered_root = check_registered_root(entry, root)
    check_head(registered_root, entry, request["expected_sha"])
    return execute(request, entry, policy, registered_root, **kwargs)


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(60)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if not raw or len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise JobError("REQUEST_SIZE_DENIED")
            reply = {"ok": True, **handle_request(json.loads(raw.decode("utf-8")))}
        except JobError as exc:
            reply = {"ok": False, "error": str(exc)[:80]}
        except (ValueError, UnicodeError, TypeError, KeyError):
            reply = {"ok": False, "error": "REQUEST_INVALID"}
        except Exception:
            reply = {"ok": False, "error": "INTERNAL_ERROR"}
        self.wfile.write((json.dumps(reply, separators=(",", ":")) + "\n").encode("utf-8"))


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def watch_socket(path, inode):
    while True:
        time.sleep(10)
        try:
            if path.stat().st_ino != inode:
                os._exit(75)
        except OSError:
            os._exit(75)


def serve(path=SOCKET_PATH):
    path = Path(path)
    if path != SOCKET_PATH:
        raise JobError("SOCKET_PATH_DENIED")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise JobError("SOCKET_PARENT_INVALID")
    if path.is_socket():
        path.unlink()
    elif path.exists() or path.is_symlink():
        raise JobError("SOCKET_ALREADY_EXISTS")
    old = os.umask(0o117)
    try:
        with Server(str(path), Handler) as server:
            info = path.stat()
            if stat.S_IMODE(info.st_mode) & 0o007:
                raise JobError("SOCKET_WORLD_ACCESS_DENIED")
            threading.Thread(target=watch_socket, args=(path, info.st_ino), daemon=True).start()
            server.serve_forever()
    finally:
        os.umask(old)
        if path.is_socket():
            path.unlink()


def main():
    argparse.ArgumentParser(description="Isolated development job provisioner").parse_args()
    serve()


if __name__ == "__main__":
    main()
