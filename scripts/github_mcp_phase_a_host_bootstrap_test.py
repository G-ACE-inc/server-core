#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "scripts/github_mcp_phase_a_host_bootstrap.py"
COMPOSE = (ROOT / "docker-compose.github-mcp-readonly.yml").read_text(encoding="utf-8")


def run_plan(fixture: dict) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(fixture, tf)
        path = tf.name
    proc = subprocess.run(
        [sys.executable, str(BOOT), "plan", "--fixture", path],
        capture_output=True,
        text=True,
        check=False,
    )
    Path(path).unlink(missing_ok=True)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_compose_invariants_pass() -> None:
    from importlib.util import spec_from_loader, module_from_spec
    import importlib.machinery

    loader = importlib.machinery.SourceFileLoader("boot", str(BOOT))
    spec = spec_from_loader("boot", loader)
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    inv = mod.compose_invariants(COMPOSE)
    assert inv["compose_host_ports_absent"]
    assert inv["pinned_digest_matches_runtime"]


def test_stale_receipt_sha_rejected() -> None:
    from importlib.util import spec_from_loader, module_from_spec
    import importlib.machinery

    loader = importlib.machinery.SourceFileLoader("boot", str(BOOT))
    spec = spec_from_loader("boot", loader)
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        json.dump(
            {
                "schema": "gace.github-mcp-phase-a-host-receipt/v1",
                "repository": "G-ACE-inc/server-core",
                "admitted_sha": "0" * 40,
                "issuer": "master:seigo-gace",
                "expires_at": time.time() + 3600,
                "effects": ["phase_a_network", "phase_a_readonly_mcp_compose"],
                "phase_b_included": False,
            },
            tf,
        )
        path = Path(tf.name)
    ok, reason = mod.validate_receipt(path, "a" * 40)
    path.unlink(missing_ok=True)
    assert not ok and reason == "RECEIPT_SHA_MISMATCH"


def test_internal_network_blocker() -> None:
    plan = run_plan(
        {
            "git": {
                "checkout_path": "/tmp/sc",
                "checkout_branch": "feat/x",
                "admitted_pr_sha": "b" * 40,
                "checkout_remote": "https://github.com/G-ACE-inc/server-core.git",
                "checkout_clean": True,
                "host_main_checkout_sha": "c" * 40,
            },
            "network": {"Internal": True, "Labels": {}},
            "container_names": [],
        }
    )
    assert plan["network_internal_flag"] is True
    assert "network_must_not_use_docker_internal_flag" in (plan.get("plan_blockers") or [])


def test_service_name_conflict_blocker() -> None:
    plan = run_plan(
        {
            "git": {
                "checkout_path": "/tmp/sc",
                "checkout_branch": "feat/x",
                "admitted_pr_sha": "b" * 40,
                "checkout_remote": "https://github.com/G-ACE-inc/server-core.git",
                "checkout_clean": True,
                "host_main_checkout_sha": "c" * 40,
            },
            "network": None,
            "container_names": ["gace-github-mcp-readonly"],
        }
    )
    assert plan["service_name_conflict"] is True


def test_rollback_preexisting_network() -> None:
    from importlib.util import spec_from_loader, module_from_spec
    import importlib.machinery

    loader = importlib.machinery.SourceFileLoader("boot", str(BOOT))
    spec = spec_from_loader("boot", loader)
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    pol = mod.rollback_network_policy({"Labels": {}}, "gace-internal")
    assert pol == "must_not_remove_preexisting_shared_network"
    pol2 = mod.rollback_network_policy(
        {"Labels": {"gace.phase_a_owner": "gace-github-mcp-readonly"}}, "gace-internal"
    )
    assert "may_remove" in pol2


def test_compose_ports_fail() -> None:
    from importlib.util import spec_from_loader, module_from_spec
    import importlib.machinery
    loader = importlib.machinery.SourceFileLoader("boot", str(BOOT))
    spec = spec_from_loader("boot", loader)
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    bad = "services:\n  x:\n    ports:\n      - \"8082:8082\"\n    expose:\n      - \"8082\"\n"
    inv = mod.compose_invariants(bad)
    assert not inv["compose_host_ports_absent"]


def test_apply_fail_closed_without_receipt() -> None:
    proc = subprocess.run([sys.executable, str(BOOT), "apply"], capture_output=True, text=True, check=False)
    assert proc.returncode == 2
    assert "HOST_ADMISSION_NOT_GRANTED" in proc.stderr


def main() -> None:
    test_compose_invariants_pass()
    test_stale_receipt_sha_rejected()
    test_internal_network_blocker()
    test_service_name_conflict_blocker()
    test_rollback_preexisting_network()
    test_compose_ports_fail()
    test_apply_fail_closed_without_receipt()
    print("GITHUB_MCP_PHASE_A_HOST_BOOTSTRAP_TESTS=PASS")


if __name__ == "__main__":
    main()
