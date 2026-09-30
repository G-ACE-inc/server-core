#!/usr/bin/env python3
"""Read-only storage lifecycle audit for G-ACE server-core.

This tool never deletes, prunes, rotates, or mutates storage/runtime state.
It collects enough evidence to design and verify later cleanup automation.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY = ROOT / "operations" / "storage-lifecycle.json"


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


def path_summary(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_symlink": path.is_symlink(),
        "entries": None,
        "bytes": None,
        "latest_mtime": None,
        "scan_errors": [],
    }
    if not path.exists() or not path.is_dir():
        return result

    total_bytes = 0
    entries = 0
    latest_mtime = 0.0

    for root, dirs, files in os.walk(path, followlinks=False):
        # Do not traverse symlinked directories.
        dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
        for filename in files:
            fp = Path(root) / filename
            try:
                st = fp.lstat()
                entries += 1
                total_bytes += st.st_size
                latest_mtime = max(latest_mtime, st.st_mtime)
            except OSError as exc:
                result["scan_errors"].append({"path": str(fp), "error": str(exc)})

    result["entries"] = entries
    result["bytes"] = total_bytes
    if latest_mtime:
        result["latest_mtime"] = datetime.fromtimestamp(latest_mtime, timezone.utc).isoformat()
    return result


def disk_summary(path: Path = Path("/")) -> dict[str, Any]:
    usage = shutil.disk_usage(path)
    percent = round((usage.used / usage.total) * 100, 2) if usage.total else None
    return {
        "path": str(path),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "used_percent": percent,
    }


def run_readonly(command: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        return {
            "available": True,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"available": False, "returncode": None, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired:
        return {"available": True, "returncode": None, "stdout": "", "stderr": "timeout"}


def docker_summary() -> dict[str, Any]:
    return {
        "version": run_readonly(["docker", "version", "--format", "{{.Server.Version}}"]),
        "containers": run_readonly(["docker", "ps", "-a", "--format", "{{json .}}"]),
        "system_df": run_readonly(["docker", "system", "df"]),
        "volumes": run_readonly(["docker", "volume", "ls", "--format", "{{.Name}}"]),
    }


def build_report(policy: dict[str, Any]) -> dict[str, Any]:
    roots = []
    for item in policy.get("roots", []):
        summary = path_summary(Path(item["path"]))
        summary["class"] = item.get("class")
        summary["default_action"] = item.get("default_action")
        summary["deletion_state"] = "PRESERVE_OR_REVIEW"
        roots.append(summary)

    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "mode": "audit_only",
        "mutation_performed": False,
        "policy_allow_delete": policy.get("allow_delete"),
        "disk": disk_summary(),
        "roots": roots,
        "docker": docker_summary() if policy.get("docker", {}).get("inspect") else {"inspected": False},
        "disk_pressure_policy": policy.get("disk_pressure"),
        "safety_policy": policy.get("safety"),
        "cleanup_decision": "NOT_EXECUTED",
        "note": "This audit does not classify any data as safe-to-delete. Project ownership, active use, retry/recovery state, and restore/rebuild paths must be verified first.",
    }
    return report


def self_test() -> int:
    policy = {
        "mode": "audit_only",
        "allow_delete": False,
        "roots": [],
        "docker": {"inspect": False, "allow_prune": False, "allow_volume_delete": False},
        "disk_pressure": {"thresholds_status": "UNSET_PENDING_REAL_SERVER_MEASUREMENT"},
        "safety": {"unknown_owner": "preserve"},
    }
    if policy["allow_delete"] is not False:
        return 1
    report = build_report(policy)
    required = {
        "mode": "audit_only",
        "mutation_performed": False,
        "cleanup_decision": "NOT_EXECUTED",
    }
    for key, expected in required.items():
        if report.get(key) != expected:
            return 1
    if report.get("docker") != {"inspected": False}:
        return 1
    print("STORAGE_LIFECYCLE_AUDIT_SELF_TEST=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only G-ACE storage lifecycle audit")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY), help="Path to audit-only policy JSON")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic non-runtime self-test")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    try:
        policy = load_policy(Path(args.policy))
        report = build_report(policy)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
