#!/usr/bin/env python3
"""Bounded read-only storage lifecycle audit for G-ACE server-core.

This tool never deletes, prunes, rotates, or mutates storage/runtime state.
Default output is a concise result envelope; --full-json emits the bounded report.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY = ROOT / "operations" / "storage-lifecycle.json"
DEFAULT_MAX_FILES = 200_000
DEFAULT_MAX_DEPTH = 32
DEFAULT_SCAN_SECONDS = 15.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_policy(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("mode") != "audit_only":
        raise ValueError("policy mode must be audit_only")
    if data.get("allow_delete") is not False:
        raise ValueError("allow_delete must be false for this auditor")
    return data


def path_summary(path: Path, max_files: int, max_depth: int, max_seconds: float) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path), "exists": path.exists(), "is_dir": path.is_dir(), "is_symlink": path.is_symlink(),
        "entries": None, "bytes": None, "latest_mtime": None, "scan_errors": [], "scan_complete": True,
        "scan_limits_hit": [], "mount_usage": None,
    }
    if not path.exists() or not path.is_dir():
        return result
    try:
        usage = shutil.disk_usage(path)
        result["mount_usage"] = {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free,
                                 "used_percent": round((usage.used / usage.total) * 100, 2) if usage.total else None}
    except OSError as exc:
        result["scan_errors"].append({"path": str(path), "error": f"disk_usage: {exc}"})
        result["scan_complete"] = False

    total_bytes = 0
    entries = 0
    latest_mtime = 0.0
    started = time.monotonic()
    root_depth = len(path.parts)

    def onerror(exc: OSError) -> None:
        result["scan_errors"].append({"path": getattr(exc, "filename", str(path)), "error": str(exc)})
        result["scan_complete"] = False

    stop = False
    for root, dirs, files in os.walk(path, followlinks=False, onerror=onerror):
        depth = len(Path(root).parts) - root_depth
        if depth >= max_depth:
            dirs[:] = []
            result["scan_complete"] = False
            if "max_depth" not in result["scan_limits_hit"]:
                result["scan_limits_hit"].append("max_depth")
        else:
            dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
        for filename in files:
            if entries >= max_files:
                result["scan_complete"] = False
                result["scan_limits_hit"].append("max_files")
                stop = True
                break
            if time.monotonic() - started >= max_seconds:
                result["scan_complete"] = False
                result["scan_limits_hit"].append("max_seconds")
                stop = True
                break
            fp = Path(root) / filename
            try:
                st = fp.lstat()
                entries += 1
                total_bytes += st.st_size
                latest_mtime = max(latest_mtime, st.st_mtime)
            except OSError as exc:
                result["scan_errors"].append({"path": str(fp), "error": str(exc)})
                result["scan_complete"] = False
        if stop:
            break
    result["entries"] = entries
    result["bytes"] = total_bytes
    if latest_mtime:
        result["latest_mtime"] = datetime.fromtimestamp(latest_mtime, timezone.utc).isoformat()
    result["scan_limits_hit"] = sorted(set(result["scan_limits_hit"]))
    return result


def run_readonly(command: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return {"available": True, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    except FileNotFoundError:
        return {"available": False, "returncode": None, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired:
        return {"available": True, "returncode": None, "stdout": "", "stderr": "timeout"}


def docker_summary() -> dict[str, Any]:
    version = run_readonly(["docker", "version", "--format", "{{.Server.Version}}"])
    ps = run_readonly(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"])
    volume = run_readonly(["docker", "volume", "ls", "-q"])
    rows = [line for line in ps["stdout"].splitlines() if line.strip()] if ps.get("returncode") == 0 else []
    problems = [line for line in rows if not any(word in line.lower() for word in ("up ", "healthy"))]
    volumes = [line for line in volume["stdout"].splitlines() if line.strip()] if volume.get("returncode") == 0 else []
    return {
        "version": version.get("stdout") if version.get("returncode") == 0 else None,
        "docker_available": bool(version.get("available")),
        "container_count": len(rows),
        "container_problem_count": len(problems),
        "container_problem_excerpt": problems[:20],
        "volume_count": len(volumes),
        "readback_errors": [x for x in (version.get("stderr"), ps.get("stderr"), volume.get("stderr")) if x][:10],
    }


def build_report(policy: dict[str, Any], max_files: int, max_depth: int, max_seconds: float) -> dict[str, Any]:
    roots = []
    for item in policy.get("roots", []):
        summary = path_summary(Path(item["path"]), max_files, max_depth, max_seconds)
        summary["class"] = item.get("class")
        summary["default_action"] = item.get("default_action")
        summary["deletion_state"] = "PRESERVE_OR_REVIEW"
        roots.append(summary)
    audit_complete = all(r.get("scan_complete") for r in roots)
    return {
        "schema_version": 2, "generated_at": utc_now(), "mode": "audit_only", "mutation_performed": False,
        "policy_allow_delete": policy.get("allow_delete"), "roots": roots,
        "docker": docker_summary() if policy.get("docker", {}).get("inspect") else {"inspected": False},
        "disk_pressure_policy": policy.get("disk_pressure"), "safety_policy": policy.get("safety"),
        "audit_complete": audit_complete, "cleanup_decision": "NOT_EXECUTED",
        "note": "Audit does not classify data as safe-to-delete; incomplete scans remain incomplete evidence.",
    }


def print_envelope(report: dict[str, Any]) -> None:
    roots = report["roots"]
    incomplete = [r["path"] for r in roots if not r.get("scan_complete")]
    errors = sum(len(r.get("scan_errors", [])) for r in roots)
    docker = report.get("docker", {})
    result = "PASS" if report.get("audit_complete") and errors == 0 else "PARTIAL"
    print("GACE_RESULT_BEGIN")
    print("TASK=SERVER_STORAGE_AUDIT")
    print("TARGET=server-storage-observation")
    print("ACTION=READ_ONLY_AUDIT")
    print("MUTATION_CLASS=READ_ONLY_INSPECTION")
    print(f"RESULT={result}")
    print(f"EVIDENCE=roots={len(roots)} scan_errors={errors} containers={docker.get('container_count','NA')} container_problems={docker.get('container_problem_count','NA')} volumes={docker.get('volume_count','NA')}")
    print(f"NOT_PROVEN=cleanup_safety; deletion_authorization; full_scan={report.get('audit_complete')}; incomplete_roots={','.join(incomplete) if incomplete else 'NONE'}")
    print("NEXT_ACTION=NONE")
    print("GACE_RESULT_END")


def self_test() -> int:
    policy = {"mode": "audit_only", "allow_delete": False, "roots": [], "docker": {"inspect": False, "allow_prune": False, "allow_volume_delete": False}, "disk_pressure": {}, "safety": {"unknown_owner": "preserve"}}
    report = build_report(policy, 10, 2, 1.0)
    ok = report.get("mode") == "audit_only" and report.get("mutation_performed") is False and report.get("cleanup_decision") == "NOT_EXECUTED" and report.get("docker") == {"inspected": False}
    print("STORAGE_LIFECYCLE_AUDIT_SELF_TEST=PASS" if ok else "STORAGE_LIFECYCLE_AUDIT_SELF_TEST=FAIL")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded read-only G-ACE storage lifecycle audit")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--full-json", action="store_true", help="Print the bounded full JSON report instead of concise envelope")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_SCAN_SECONDS)
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.max_files < 1 or args.max_depth < 0 or args.max_seconds <= 0:
        print('{"status":"FAIL","error":"invalid scan budget"}', file=sys.stderr)
        return 2
    try:
        report = build_report(load_policy(Path(args.policy)), args.max_files, args.max_depth, args.max_seconds)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    if args.full_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_envelope(report)
    return 0 if report.get("audit_complete") else 3


if __name__ == "__main__":
    raise SystemExit(main())
