#!/usr/bin/env python3
"""Host-local privilege-separated registered service deploy writer (UNIX socket ONLY).

Separate writer authority: the HMAC-bearing Gateway receiver never gets Docker
access. It can only ask this fixed socket to (a) accept a deploy of an already
registered repository/service at an exact SHA, or (b) read back the durable
result of an earlier request id. Admission is delegated to the existing
registry-backed preflight and Compose executor; no shell, branch, Compose file
or service wildcard is accepted from the request. Deploys run asynchronously
because Gateway delivery timeouts are shorter than image builds.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socketserver
import stat
import threading
import time
import urllib.request

from servercore_registered_service_deploy import command, deploy
from servercore_service_deploy_admission import REGISTRY, AdmissionError as DeployAdmissionError, require_registered
from servercore_registered_docker_ops import DockerOperationError, operate, OPS

SOCKET_PATH = Path("/run/gace/servercore-service-deploy.sock")
LOCK_PATH = Path("/tmp/gace-servercore-service-deploy.lock")
RESULT_DIR = Path("/home/admin1/logs/servercore-service-deploy")
MAX_REQUEST = 1048576
DEPLOY_SCHEMA = "gace.servercore-service-deploy.request/v1"
STATUS_SCHEMA = "gace.servercore-service-deploy.status/v1"
DOCKER_OP_SCHEMA = "gace.servercore-docker-operation.request/v1"
DOCKER_OP_KEYS = {"schema", "id", "repository", "service", "target_sha", "operation", "argv", "tail"}
REQ_ID = re.compile(r"^req_[0-9a-f]{24}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
SERVICE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
DEPLOY_KEYS = {"schema", "id", "repository", "service", "target_sha"}
STATUS_KEYS = {"schema", "id"}


class AdmissionError(Exception):
    pass


def _req_id(value):
    if not isinstance(value, str) or not REQ_ID.fullmatch(value):
        raise AdmissionError("REQUEST_ID_DENIED")
    return value


def validate(value):
    if not isinstance(value, dict) or set(value) != DEPLOY_KEYS:
        raise AdmissionError("REQUEST_KEYS_DENIED")
    if value["schema"] != DEPLOY_SCHEMA:
        raise AdmissionError("REQUEST_SCHEMA_DENIED")
    _req_id(value["id"])
    if not isinstance(value["repository"], str) or not REPO.fullmatch(value["repository"]):
        raise AdmissionError("REPOSITORY_INVALID")
    if not isinstance(value["service"], str) or not SERVICE.fullmatch(value["service"]):
        raise AdmissionError("SERVICE_INVALID")
    if not isinstance(value["target_sha"], str) or not SHA.fullmatch(value["target_sha"]):
        raise AdmissionError("TARGET_SHA_INVALID")
    return value


def validate_status(value):
    if not isinstance(value, dict) or set(value) != STATUS_KEYS or value["schema"] != STATUS_SCHEMA:
        raise AdmissionError("STATUS_KEYS_DENIED")
    _req_id(value["id"])
    return value


def result_path(request_id, result_dir=None):
    return Path(result_dir or RESULT_DIR) / (_req_id(request_id) + ".json")


def write_result(request_id, payload, result_dir=None):
    path = result_path(request_id, result_dir)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)  # mkdir mode is masked by the service UMask=0117 (no x bit)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def read_result(request_id, result_dir=None):
    path = result_path(request_id, result_dir)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def runtime_identity(root, compose_file, service):
    """Read the Compose-owned container identity for before/after comparison."""
    prefix = ["docker", "compose", "--project-directory", root, "-f", str(Path(root) / compose_file)]
    ids = command([*prefix, "ps", "--quiet", service], timeout=30).splitlines()
    if len(ids) != 1 or not re.fullmatch(r"[a-f0-9]{12,64}", ids[0]):
        return None
    created = command(["docker", "inspect", "--format", "{{.Created}}|{{.Image}}", ids[0]], timeout=15)
    return {"container_id": ids[0], "created_image": created}


def http_health(url, *, timeout_seconds=60):
    """Registered health URL readback: loopback http only, bounded."""
    if not isinstance(url, str) or not url.startswith("http://127.0.0.1:"):
        return "NOT_REGISTERED"
    deadline = time.monotonic() + timeout_seconds
    status = "UNREACHABLE"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                status = "HTTP_%d" % response.status
                if response.status == 200:
                    return status
        except Exception:
            status = "UNREACHABLE"
        time.sleep(2)
    return status


def run_apply(request, registry, entry, lock, result_dir=None):
    runtime = entry["runtime_target"]
    root = entry["server_project_path"]
    base = {"request_id": request["id"], "repository": request["repository"],
            "service": request["service"], "source_sha": request["target_sha"]}
    try:
        write_result(request["id"], {**base, "state": "RUNNING"}, result_dir)
        before = runtime_identity(root, runtime["compose_file"], request["service"])
        result = deploy(registry, request["repository"], request["target_sha"],
                        request["service"], apply=True)
        after = runtime_identity(root, runtime["compose_file"], request["service"])
        health = http_health(runtime.get("health_url"))
        if runtime.get("health_url") and health != "HTTP_200":
            raise AdmissionError("SERVICE_HTTP_HEALTH_NOT_READY")
        write_result(request["id"], {
            **base, **result, "state": "SERVICE_DEPLOY_PASS",
            "compose_digest": runtime["compose_digest"], "http_health": health,
            "before": before, "after": after,
            "recreated": before is None or before != after}, result_dir)
    except (AdmissionError, DeployAdmissionError, DockerOperationError) as exc:
        write_result(request["id"], {**base, "state": "FAIL", "failure_class": str(exc)[:80]}, result_dir)
    except Exception:
        write_result(request["id"], {**base, "state": "FAIL", "failure_class": "INTERNAL_ERROR"}, result_dir)
    finally:
        lock.close()


def accept_request(value, *, registry_path=REGISTRY, lock_path=LOCK_PATH, result_dir=None, threaded=True):
    request = validate(value)
    existing = read_result(request["id"], result_dir)
    if existing is not None:  # Gateway retry/duplicate: idempotent, never redeploys
        return {"state": "SERVICE_DEPLOY_DUPLICATE", "recorded_state": existing.get("state")}
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    # Dry-run first: fails closed before any lock, result or mutation.
    deploy(registry, request["repository"], request["target_sha"], request["service"])
    entry = [x for x in registry["repositories"] if x.get("repository") == request["repository"]][0]
    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    lock = os.fdopen(fd, "w")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise
    write_result(request["id"], {"request_id": request["id"], "repository": request["repository"],
                                 "service": request["service"], "source_sha": request["target_sha"],
                                 "state": "QUEUED"}, result_dir)
    if threaded:
        threading.Thread(target=run_apply, args=(request, registry, entry, lock, result_dir),
                         daemon=True).start()
    else:
        run_apply(request, registry, entry, lock, result_dir)
    return {"state": "SERVICE_DEPLOY_ACCEPTED"}


def status_request(value, *, result_dir=None):
    request = validate_status(value)
    result = read_result(request["id"], result_dir)
    if result is None:
        raise AdmissionError("DEPLOY_REQUEST_UNKNOWN")
    return result



def validate_docker_operation(value):
    if not isinstance(value, dict) or set(value) != DOCKER_OP_KEYS:
        raise AdmissionError("DOCKER_OPERATION_KEYS_DENIED")
    if value["schema"] != DOCKER_OP_SCHEMA:
        raise AdmissionError("DOCKER_OPERATION_SCHEMA_DENIED")
    _req_id(value["id"])
    if not isinstance(value["repository"], str) or not REPO.fullmatch(value["repository"]):
        raise AdmissionError("REPOSITORY_INVALID")
    if not isinstance(value["service"], str) or not SERVICE.fullmatch(value["service"]):
        raise AdmissionError("SERVICE_INVALID")
    if not isinstance(value["target_sha"], str) or not SHA.fullmatch(value["target_sha"]):
        raise AdmissionError("TARGET_SHA_INVALID")
    if not isinstance(value["operation"], str) or value["operation"] not in OPS:
        raise AdmissionError("DOCKER_OPERATION_DENIED")
    argv = value["argv"]
    if not isinstance(argv, list) or (value["operation"] == "exec") != bool(argv):
        raise AdmissionError("DOCKER_EXEC_ARGS_DENIED")
    if len(argv) > 10 or sum(len(arg) for arg in argv if isinstance(arg, str)) > 1000:
        raise AdmissionError("DOCKER_EXEC_ARGS_TOO_LARGE")
    if any(not isinstance(arg, str) or not 1 <= len(arg) <= 512 for arg in argv):
        raise AdmissionError("DOCKER_EXEC_ARGS_INVALID")
    if type(value["tail"]) is not int or not 1 <= value["tail"] <= 200:
        raise AdmissionError("DOCKER_TAIL_INVALID")
    return value



def check_registered_compose_path(admitted):
    """Revalidate on-disk registered Compose scope; no status-clean requirement.

    The user can legitimately have dirty source work while inspecting/restarting
    a container. Never let a symlink or swapped Compose file redirect privileged
    operations away from the preexisting protected registry.
    """
    root = Path(admitted["root"])
    if root.is_symlink() or not root.is_dir() or not (root / ".git").is_dir():
        raise AdmissionError("DOCKER_HOST_CHECKOUT_INVALID")
    path = root / admitted["compose_file"]
    if path.is_symlink() or not path.is_file() or path.resolve().parent != root.resolve():
        raise AdmissionError("DOCKER_COMPOSE_PATH_CHANGED")
    if hashlib.sha256(path.read_bytes()).hexdigest() != admitted["compose_digest"]:
        raise AdmissionError("DOCKER_COMPOSE_DIGEST_CHANGED")
    for item in admitted.get("compose_overrides", []):
        override = Path(item["path"])
        if override.is_symlink() or not override.is_file() or not override.is_absolute():
            raise AdmissionError("DOCKER_COMPOSE_OVERRIDE_PATH_CHANGED")
        if hashlib.sha256(override.read_bytes()).hexdigest() != item["sha256"]:
            raise AdmissionError("DOCKER_COMPOSE_OVERRIDE_DIGEST_CHANGED")
    return root

def run_docker_operation(value, *, registry_path=REGISTRY, lock_path=LOCK_PATH, result_dir=None):
    """Use the existing registry and Host writer lock; retry IDs never repeat writes."""
    request = validate_docker_operation(value)
    existing = read_result(request["id"], result_dir)
    if existing is not None:
        return {"request_id": request["id"], "state": "DOCKER_OPERATION_DUPLICATE",
                "recorded_state": existing.get("state"), "result": existing}
    registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    admitted = require_registered(registry, request["repository"], request["target_sha"], request["service"], permission="docker.operation")
    entry = next(x for x in registry["repositories"] if x.get("repository") == request["repository"])
    runtime = entry["runtime_target"]
    admitted["compose_overrides"] = runtime.get("compose_overrides", [])
    check_registered_compose_path(admitted)
    entry = next(x for x in registry["repositories"] if x.get("repository") == request["repository"])
    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Repeat the idempotency read inside the lock as well.
        existing = read_result(request["id"], result_dir)
        if existing is not None:
            return {"request_id": request["id"], "state": "DOCKER_OPERATION_DUPLICATE",
                    "recorded_state": existing.get("state"), "result": existing}
        base = {"request_id": request["id"], "repository": request["repository"],
                "service": request["service"], "operation": request["operation"],
                "source_sha": request["target_sha"]}
        write_result(request["id"], {**base, "state": "RUNNING"}, result_dir)
        try:
            result = operate(entry, request["service"], request["operation"],
                             argv=request["argv"] or None, tail=request["tail"], timeout=45)
            outcome = {**base, "state": "DOCKER_OPERATION_PASS", **result}
        except DockerOperationError as exc:
            outcome = {**base, "state": "FAIL", "failure_class": str(exc)[:80]}
        except Exception:
            outcome = {**base, "state": "FAIL", "failure_class": "INTERNAL_ERROR"}
        write_result(request["id"], outcome, result_dir)
    return {"request_id": request["id"], **outcome}


HOST_COMMAND_SCHEMA = "gace.servercore-host-command.request/v1"
HOST_COMMAND_KEYS = {"schema", "id", "repository", "target_sha", "command"}
HOST_COMMAND_MAX_SECONDS = 90

def run_host_command(value, *, registry_path=REGISTRY, lock_path=LOCK_PATH, result_dir=None,
                     runner=None):
    """Run a Master-delegated Host command inside an existing, registered checkout.

    Not a sandbox/dev.job. Uses the already privileged Host writer and durable
    result ledger. No caller-provided cwd, uid, Docker socket, or registry path.
    """
    import subprocess
    if not isinstance(value, dict) or set(value) != HOST_COMMAND_KEYS or value.get("schema") != HOST_COMMAND_SCHEMA:
        raise AdmissionError("HOST_COMMAND_KEYS_INVALID")
    request_id = _req_id(value["id"])
    repository, target_sha, command_text = value["repository"], value["target_sha"], value["command"]
    if not isinstance(repository, str) or not REPO.fullmatch(repository):
        raise AdmissionError("REPOSITORY_INVALID")
    if not isinstance(target_sha, str) or not SHA.fullmatch(target_sha):
        raise AdmissionError("TARGET_SHA_INVALID")
    if not isinstance(command_text, str) or not command_text or "\x00" in command_text:
        raise AdmissionError("HOST_COMMAND_INVALID")
    previous = read_result(request_id, result_dir)
    if previous is not None:
        return {"request_id": request_id, "state": "HOST_COMMAND_DUPLICATE", "result": previous}
    # Current shared Terminal: its Project #1 registered checkout map is the
    # sole host.command registration source. Legacy DebugAI delegation grants
    # are not part of general Chat Host command admission.
    terminal_contract = json.loads(
        (Path(__file__).resolve().parents[1] / "operations/github-project-bounded-host.json")
        .read_text(encoding="utf-8"))
    registered = terminal_contract.get("dev_job", {}).get("registered_repositories", {})
    entry = registered.get(repository) if isinstance(registered, dict) else None
    if not isinstance(entry, dict):
        raise AdmissionError("HOST_COMMAND_NOT_REGISTERED")
    root = Path(str(entry.get("root", "")))
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() \
            or not (root / ".git").exists() or root.resolve() != root \
            or not (str(root).startswith("/home/admin1/projects/") or str(root) == "/home/admin1/server-core"):
        raise AdmissionError("HOST_COMMAND_ROOT_INVALID")
    git = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                         capture_output=True, text=True, timeout=15)
    if git.returncode or git.stdout.strip() != target_sha:
        raise AdmissionError("HOST_COMMAND_SHA_MISMATCH")
    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        previous = read_result(request_id, result_dir)
        if previous is not None:
            return {"request_id": request_id, "state": "HOST_COMMAND_DUPLICATE", "result": previous}
        base = {"request_id": request_id, "repository": repository, "source_sha": target_sha}
        write_result(request_id, {**base, "state": "RUNNING"}, result_dir)
        try:
            run = runner or subprocess.run
            # The socket uses umask 0117; normal Host commands need executable directories.
            # Keep socket masking intact and set the child shell umask only.
            completed = run(["/bin/bash", "-lc", "umask 0022; " + command_text], cwd=str(root),
                            capture_output=True, text=True, timeout=HOST_COMMAND_MAX_SECONDS,
                            check=False)
            result = {**base, "state": "HOST_COMMAND_PASS" if completed.returncode == 0 else "FAIL",
                      "exit_code": completed.returncode,
                      "stdout": completed.stdout, "stderr": completed.stderr}
        except (OSError, subprocess.TimeoutExpired):
            result = {**base, "state": "FAIL", "failure_class": "HOST_COMMAND_EXECUTION_FAILED"}
        write_result(request_id, result, result_dir)
        return result


def host_command_wire_reply(reply):
    """Preserve complete output in the Host ledger; bound only socket framing."""
    if not isinstance(reply, dict):
        return reply
    result = reply.get("result") if reply.get("state") == "HOST_COMMAND_DUPLICATE" else reply
    if not isinstance(result, dict) or "stdout" not in result:
        return reply
    import hashlib
    import json
    wire = json.dumps(reply, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(wire) <= 256 * 1024:
        return reply
    out = dict(result)
    for stream in ("stdout", "stderr"):
        full = str(out.get(stream) or "")
        out[stream + "_sha256"] = hashlib.sha256(full.encode("utf-8")).hexdigest()
        out[stream + "_chars"] = len(full)
        out[stream + "_stored_complete"] = True
        out[stream] = ""
    out["output_record_request_id"] = str(out.get("request_id", ""))
    if reply.get("state") == "HOST_COMMAND_DUPLICATE":
        return {**reply, "result": out}
    return out


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(60)
        try:
            raw = self.rfile.readline(MAX_REQUEST + 1)
            if not raw or len(raw) > MAX_REQUEST or not raw.endswith(b"\n"):
                raise AdmissionError("REQUEST_SIZE_DENIED")
            value = json.loads(raw.decode("utf-8"))
            if isinstance(value, dict) and value.get("schema") == STATUS_SCHEMA:
                reply = {"ok": True, **status_request(value)}
            elif isinstance(value, dict) and value.get("schema") == DOCKER_OP_SCHEMA:
                reply = {"ok": True, **run_docker_operation(value)}
            elif isinstance(value, dict) and value.get("schema") == HOST_COMMAND_SCHEMA:
                reply = {"ok": True, **run_host_command(value)}
            else:
                reply = {"ok": True, "request_id": value["id"], **accept_request(value)}
        except BlockingIOError:
            reply = {"ok": False, "error": "DEPLOY_LOCK_BUSY"}
        except (AdmissionError, DeployAdmissionError) as exc:
            reply = {"ok": False, "error": str(exc)[:80]}
        except (ValueError, UnicodeError, TypeError, KeyError, IndexError):
            reply = {"ok": False, "error": "REQUEST_INVALID"}
        except Exception:
            reply = {"ok": False, "error": "INTERNAL_ERROR"}
        self.wfile.write((json.dumps(host_command_wire_reply(reply), separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8"))


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def watch_socket(path, inode):
    """Exit when the runtime directory/socket was replaced so systemd rebinds."""
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
        raise AdmissionError("SOCKET_PATH_DENIED")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise AdmissionError("SOCKET_PARENT_INVALID")
    if path.is_socket():
        path.unlink()  # stale socket of this same fixed service only
    elif path.exists() or path.is_symlink():
        raise AdmissionError("SOCKET_ALREADY_EXISTS")
    old = os.umask(0o117)
    try:
        with Server(str(path), Handler) as server:
            info = path.stat()
            if stat.S_IMODE(info.st_mode) & 0o007:
                raise AdmissionError("SOCKET_WORLD_ACCESS_DENIED")
            threading.Thread(target=watch_socket, args=(path, info.st_ino), daemon=True).start()
            server.serve_forever()
    finally:
        os.umask(old)
        if path.is_socket():
            path.unlink()


def main():
    argparse.ArgumentParser(description="Fixed registered service deploy Host writer socket").parse_args()
    serve()


if __name__ == "__main__":
    main()
