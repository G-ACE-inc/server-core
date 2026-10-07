#!/usr/bin/env python3
import argparse
import json
import os
import re
import secrets
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "operations" / "server-gitops.json"


class ServerGitOpsError(RuntimeError):
    pass


def fail(code):
    raise ServerGitOpsError(code)


def load_contract(path=DEFAULT_CONTRACT):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ServerGitOpsError("SERVER_GITOPS_CONTRACT_INVALID") from exc
    if data.get("request_schema") != "gace.server-gitops-request/v1":
        fail("SERVER_GITOPS_REQUEST_SCHEMA_INVALID")
    if data.get("status_schema") != "gace.server-gitops-status/v1":
        fail("SERVER_GITOPS_STATUS_SCHEMA_INVALID")
    if not isinstance(data.get("actions"), dict) or "deploy" not in data["actions"]:
        fail("SERVER_GITOPS_ACTIONS_INVALID")
    if not isinstance(data.get("targets"), dict) or not data["targets"]:
        fail("SERVER_GITOPS_TARGETS_INVALID")
    queue = data.get("queue")
    if not isinstance(queue, dict):
        fail("SERVER_GITOPS_QUEUE_INVALID")
    ttl = int(queue.get("ttl_ms", 0))
    if ttl < 1000 or ttl > 300000:
        fail("SERVER_GITOPS_TTL_INVALID")
    approval = data.get("approval")
    if not isinstance(approval, dict) or approval.get("actor") != "seigo-gace":
        fail("SERVER_GITOPS_APPROVAL_INVALID")
    return data


def queue_root(contract, env=None):
    current = os.environ if env is None else env
    override = str(current.get("GACE_SERVER_GITOPS_QUEUE_ROOT") or "").strip()
    if override:
        return Path(override).resolve()
    rel = str(contract["queue"].get("relative_root") or "").strip()
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        fail("SERVER_GITOPS_QUEUE_ROOT_INVALID")
    return (ROOT / rel).resolve()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def normalize_sha(value, code):
    sha = str(value or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        fail(code)
    return sha


def normalize_branch(value):
    branch = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9._/-]{1,160}", branch):
        fail("SERVER_GITOPS_BRANCH_INVALID")
    if branch.startswith("-") or ".." in branch or "@{" in branch:
        fail("SERVER_GITOPS_BRANCH_INVALID")
    return branch


def validate_request(contract, *, action, target_id, branch, expected_head, sha, approval_comment_id):
    action = str(action or "").strip()
    if action not in contract["actions"]:
        fail("SERVER_GITOPS_ACTION_NOT_ALLOWED")
    if action != "deploy":
        fail("SERVER_GITOPS_ACTION_NOT_ALLOWED")
    target_id = str(target_id or "").strip()
    target = contract["targets"].get(target_id)
    if not isinstance(target, dict) or target.get("enabled") is not True:
        fail("SERVER_GITOPS_TARGET_NOT_ALLOWED")
    branch = normalize_branch(branch)
    if branch not in target.get("allowed_branches", []):
        fail("SERVER_GITOPS_BRANCH_NOT_ALLOWED")
    expected = normalize_sha(expected_head, "SERVER_GITOPS_EXPECTED_HEAD_INVALID")
    deploy_sha = normalize_sha(sha, "SERVER_GITOPS_DEPLOY_SHA_INVALID")
    if deploy_sha != expected:
        fail("SERVER_GITOPS_SHA_HEAD_MISMATCH")
    try:
        comment_id = int(approval_comment_id)
    except (TypeError, ValueError):
        fail("SERVER_GITOPS_APPROVAL_COMMENT_ID_INVALID")
    if comment_id < 1:
        fail("SERVER_GITOPS_APPROVAL_COMMENT_ID_INVALID")
    return action, target_id, branch, expected, deploy_sha, comment_id


def make_request(
    contract,
    *,
    action,
    target_id,
    branch,
    expected_head,
    sha,
    approval_comment_id,
    now_ms=None,
):
    action, target_id, branch, expected, deploy_sha, comment_id = validate_request(
        contract,
        action=action,
        target_id=target_id,
        branch=branch,
        expected_head=expected_head,
        sha=sha,
        approval_comment_id=approval_comment_id,
    )
    created = int(time.time() * 1000 if now_ms is None else now_ms)
    return {
        "schema": contract["request_schema"],
        "id": "gitops_" + secrets.token_hex(12),
        "action": action,
        "target_id": target_id,
        "branch": branch,
        "expected_head": expected,
        "sha": deploy_sha,
        "approval_comment_id": comment_id,
        "created_at": created,
        "expires_at": created + int(contract["queue"]["ttl_ms"]),
    }


def enqueue(contract, *, env=None, now_ms=None, **kwargs):
    request = make_request(contract, now_ms=now_ms, **kwargs)
    root = queue_root(contract, env=env)
    atomic_json(root / "requests" / f"{request['id']}.json", request)
    return {
        "schema": contract["request_schema"],
        "id": request["id"],
        "state": "QUEUED",
        "action": request["action"],
        "target_id": request["target_id"],
        "branch": request["branch"],
        "expected_head": request["expected_head"],
        "approval_comment_id": request["approval_comment_id"],
    }


def validate_request_id(contract, request_id):
    value = str(request_id or "").strip()
    try:
        pattern = re.compile(contract["request_id_pattern"])
    except Exception as exc:
        raise ServerGitOpsError("SERVER_GITOPS_REQUEST_ID_PATTERN_INVALID") from exc
    if not pattern.fullmatch(value):
        fail("SERVER_GITOPS_REQUEST_ID_INVALID")
    return value


def status(contract, request_id, *, env=None):
    value = validate_request_id(contract, request_id)
    root = queue_root(contract, env=env)
    status_file = root / "status" / f"{value}.json"
    processing = root / "processing" / f"{value}.json"
    request_file = root / "requests" / f"{value}.json"
    if status_file.is_file():
        try:
            result = json.loads(status_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ServerGitOpsError("SERVER_GITOPS_STATUS_JSON_INVALID") from exc
        if result.get("schema") != contract["status_schema"]:
            fail("SERVER_GITOPS_STATUS_SCHEMA_INVALID")
        return result
    if processing.is_file():
        return {"schema": contract["status_schema"], "id": value, "state": "RUNNING"}
    if request_file.is_file():
        return {"schema": contract["status_schema"], "id": value, "state": "QUEUED"}
    fail("SERVER_GITOPS_REQUEST_NOT_FOUND")


def main():
    parser = argparse.ArgumentParser(description="G-ACE shared guarded server GitOps queue client")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    sub = parser.add_subparsers(dest="mode", required=True)

    req = sub.add_parser("request")
    req.add_argument("--action", required=True, choices=["deploy"])
    req.add_argument("--target-id", required=True)
    req.add_argument("--branch", required=True)
    req.add_argument("--expected-head", required=True)
    req.add_argument("--sha", required=True)
    req.add_argument("--approval-comment-id", required=True, type=int)

    stat = sub.add_parser("status")
    stat.add_argument("--id", required=True)

    args = parser.parse_args()
    try:
        contract = load_contract(args.contract)
        if args.mode == "request":
            result = enqueue(
                contract,
                action=args.action,
                target_id=args.target_id,
                branch=args.branch,
                expected_head=args.expected_head,
                sha=args.sha,
                approval_comment_id=args.approval_comment_id,
            )
        else:
            result = status(contract, args.id)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    except ServerGitOpsError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
