#!/usr/bin/env python3
"""Phase A official GitHub MCP — read-only Host plan; apply FAIL-CLOSED without verified receipt."""
from __future__ import annotations

import argparse
import os
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "operations/github-mcp-readonly-runtime.json"
BOOTSTRAP_PATH = ROOT / "operations/github-mcp-phase-a-host-bootstrap.json"
COMPOSE_PATH = ROOT / "docker-compose.github-mcp-readonly.yml"
PINNED = "fbec75de11c255213fa08d80fb166abe73d851fff631c51c0079872967720699"
SERVICE_NAME = "gace-github-mcp-readonly"
NETWORK_DEFAULT = "gace-internal"
REPO_FULL = "G-ACE-inc/server-core"


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_git_facts(repo: Path) -> dict[str, Any]:
    facts: dict[str, Any] = {"checkout_path": str(repo)}
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo)
    facts["checkout_branch"] = branch.stdout.strip() if branch.returncode == 0 else "UNKNOWN"
    head = run(["git", "rev-parse", "HEAD"], cwd=repo)
    facts["admitted_pr_sha"] = head.stdout.strip() if head.returncode == 0 else ""
    remote = run(["git", "remote", "get-url", "origin"], cwd=repo)
    facts["checkout_remote"] = remote.stdout.strip() if remote.returncode == 0 else ""
    status = run(["git", "status", "--porcelain"], cwd=repo)
    facts["checkout_clean"] = status.returncode == 0 and status.stdout.strip() == ""
    main_sha = run(["git", "rev-parse", "main"], cwd=repo)
    facts["host_main_checkout_sha"] = main_sha.stdout.strip() if main_sha.returncode == 0 else ""
    return facts


def network_inspect(name: str) -> dict[str, Any] | None:
    proc = run(["docker", "network", "inspect", name])
    if proc.returncode != 0:
        return None
    data = json.loads(proc.stdout)
    if not data:
        return None
    return data[0]


def docker_ps_names() -> list[str]:
    proc = run(["docker", "ps", "-a", "--format", "{{.Names}}"])
    if proc.returncode != 0:
        return []
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def debugai_preserved(names: list[str]) -> bool:
    return any(n.startswith("debug-ai-") for n in names)


def compose_invariants(compose_text: str) -> dict[str, bool]:
    before_expose = compose_text.split("expose:", 1)[0]
    return {
        "compose_host_ports_absent": "\n    ports:" not in before_expose,
        "compose_internal_network_flag_absent": "internal: true" not in compose_text,
        "pinned_digest_matches_runtime": PINNED in compose_text,
    }


def egress_probe() -> str:
    try:
        with urlopen("https://api.github.com/zen", timeout=15) as resp:
            if 200 <= resp.status < 500:
                return f"PASS code={resp.status}"
    except URLError:
        pass
    return "INCONCLUSIVE"


def validate_receipt(path: Path, admitted_sha: str) -> tuple[bool, str]:
    if not path.is_file():
        return False, "RECEIPT_MISSING"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, "RECEIPT_INVALID_JSON"
    if doc.get("schema") != "gace.github-mcp-phase-a-host-receipt/v1":
        return False, "RECEIPT_SCHEMA_MISMATCH"
    if doc.get("repository") != REPO_FULL:
        return False, "RECEIPT_REPOSITORY_MISMATCH"
    if doc.get("admitted_sha") != admitted_sha:
        return False, "RECEIPT_SHA_MISMATCH"
    if doc.get("effects") != ["phase_a_network", "phase_a_readonly_mcp_compose"]:
        return False, "RECEIPT_EFFECTS_MISMATCH"
    if doc.get("phase_b_included") is True:
        return False, "RECEIPT_PHASE_B_FORBIDDEN"
    exp = doc.get("expires_at")
    if not isinstance(exp, (int, float)) or exp <= time.time():
        return False, "RECEIPT_EXPIRED"
    issuer = doc.get("issuer", "")
    if not re.match(r"^(master:|host-admin:)[A-Za-z0-9._-]+$", str(issuer)):
        return False, "RECEIPT_ISSUER_INVALID"
    return True, "RECEIPT_OK"


def rollback_network_policy(network: dict[str, Any] | None, runtime_name: str) -> str:
    if network is None:
        return "no_network_to_remove_before_apply"
    labels = network.get("Labels") or {}
    if labels.get("gace.phase_a_owner") == SERVICE_NAME:
        return "may_remove_only_if_no_other_attachments_and_label_matches_phase_a"
    return "must_not_remove_preexisting_shared_network"


def build_plan(*, fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime = load_json(RUNTIME_PATH)
    bootstrap = load_json(BOOTSTRAP_PATH)
    compose_text = COMPOSE_PATH.read_text(encoding="utf-8")
    net_name = runtime["network"]["default_name"]

    if fixture:
        git_f = fixture["git"]
        net = fixture.get("network")
        names = fixture.get("container_names", [])
        inv = fixture.get("compose_invariants") or compose_invariants(compose_text)
        egress = fixture.get("egress_https_probe", "SKIPPED_FIXTURE")
    else:
        git_f = read_git_facts(ROOT)
        net = network_inspect(net_name)
        names = docker_ps_names()
        inv = compose_invariants(compose_text)
        egress = egress_probe()

    network_exists = net is not None
    network_internal = bool(net and net.get("Internal"))
    conflict = SERVICE_NAME in names

    receipt_env = bootstrap["apply_gate"]["receipt_env"]
    receipt_path = Path(os.environ[receipt_env]) if os.environ.get(receipt_env) else None
    receipt_ok = False
    receipt_reason = "RECEIPT_NOT_PROVIDED"
    if receipt_path:
        receipt_ok, receipt_reason = validate_receipt(receipt_path, git_f["admitted_pr_sha"])

    plan = {
        "schema": "gace.github-mcp-phase-a-host-plan/v1",
        "repository": REPO_FULL,
        "mode": "plan",
        **git_f,
        "network_name": net_name,
        "network_exists": network_exists,
        "network_internal_flag": network_internal,
        "service_name_conflict": conflict,
        **inv,
        "debugai_services_preserved": debugai_preserved(names),
        "phase_b_compose_not_started": "server-core-project-control" not in " ".join(names),
        "workspace_mcp_advert_changed": False,
        "egress_https_probe": egress,
        "rollback_network_policy": rollback_network_policy(net, net_name),
        "host_admission_granted": receipt_ok,
        "apply_permitted": False,
        "apply_block_reason": receipt_reason if not receipt_ok else "APPLY_NOT_IMPLEMENTED_IN_SOURCE",
    }
    if network_internal:
        plan["plan_blockers"] = plan.get("plan_blockers", []) + ["network_must_not_use_docker_internal_flag"]
    if conflict:
        plan["plan_blockers"] = plan.get("plan_blockers", []) + ["service_name_conflict"]
    if not inv["compose_host_ports_absent"]:
        plan["plan_blockers"] = plan.get("plan_blockers", []) + ["compose_must_not_publish_host_ports"]
    return plan


def cmd_plan(args: argparse.Namespace) -> int:
    fixture = None
    if args.fixture:
        fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    plan = build_plan(fixture=fixture)
    print(json.dumps(plan, indent=2, sort_keys=True))
    print("GITHUB_MCP_PHASE_A_HOST_PLAN=EMITTED", file=sys.stderr)
    blockers = plan.get("plan_blockers") or []
    if blockers:
        print(f"GITHUB_MCP_PHASE_A_PLAN_BLOCKERS={','.join(blockers)}", file=sys.stderr)
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    plan = build_plan()
    print(json.dumps({"schema": "gace.github-mcp-phase-a-host-apply/v1", "plan_sha": plan["admitted_pr_sha"]}, indent=2))
    if not plan["host_admission_granted"]:
        print(f"HOST_ADMISSION_NOT_GRANTED reason={plan.get('apply_block_reason')}", file=sys.stderr)
        return 2
    print("HOST_APPLY_NOT_IMPLEMENTED=Phase A apply remains Host-admin manual bounded steps per docs/GITHUB_MCP_PHASE_A_ADMISSION.md", file=sys.stderr)
    return 3


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase A GitHub MCP Host bootstrap (plan default, apply fail-closed).")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_plan = sub.add_parser("plan", help="Read-only Host/Source preflight plan JSON")
    p_plan.add_argument("--fixture", help="Test fixture JSON (CI/unit tests only)")
    sub.add_parser("apply", help="Fail-closed unless verified external receipt exists")
    args = parser.parse_args()
    if args.cmd == "plan":
        return cmd_plan(args)
    return cmd_apply(args)


if __name__ == "__main__":
    raise SystemExit(main())
