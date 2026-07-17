#!/usr/bin/env python3
"""
cloudflare_ops.py — Astera v8 Cloudflare Tunnel 運用スクリプト

正本: /home/admin1/server-core/operations/cloudflare.json
設計正本: /home/admin1/server-core/docs/CLOUDFLARE_OPERATIONS.md

このスクリプトは Cloudflare API を直接変更しない。
Mutation 系 Subcommand は --confirm なしでは拒否する。
Secret・Token の値を出力しない。
"""

import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

OPERATIONS_FILE = Path(__file__).parent.parent / "operations" / "cloudflare.json"

SUBCOMMANDS = {
    "inspect":   "Projectと正本設定を表示する（Secret除外）",
    "plan":      "必要なCloudflare操作をJSON Planとして出力する（変更なし）",
    "preflight": "Docker/Compose/GPG/Runtime Directoryを事前確認する",
    "review":    "現在状態をまとめて表示する（Secret除外）",
    "local-up":  "cloudflare Profileを起動する（--confirm必須）",
    "status":    "Container稼働状態とState Fileを表示する",
    "verify":    "Tunnel疎通とメトリクスエンドポイントを検証する",
    "stop":      "cloudflare ProfileのContainerを停止する（--confirm必須）",
    "rollback":  "前回State Fileの状態へ戻す（--confirm必須）",
}

MUTATION_SUBCOMMANDS = {"local-up", "stop", "rollback"}


def die(msg: str, code: int = 1) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(code)

def info(msg: str) -> None:
    print(f"[INFO] {msg}")

def warn(msg: str) -> None:
    print(f"[WARN] {msg}")

def ok(msg: str) -> None:
    print(f"[ OK ] {msg}")


def load_ops(project_id: str) -> dict:
    if not OPERATIONS_FILE.exists():
        die(f"operations file not found: {OPERATIONS_FILE}")
    with OPERATIONS_FILE.open() as f:
        data = json.load(f)
    if data.get("project_id") != project_id:
        die(
            f"unknown project '{project_id}'. "
            f"operations file defines project_id='{data.get('project_id')}'"
        )
    return data


def git_info(repo_path: str) -> dict:
    result = {}
    base = ["git", "-C", repo_path]
    try:
        result["branch"] = subprocess.check_output(
            base + ["rev-parse", "--abbrev-ref", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        result["sha"] = subprocess.check_output(
            base + ["rev-parse", "--short", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty_out = subprocess.check_output(
            base + ["status", "--porcelain"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        result["dirty"] = bool(dirty_out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        result["branch"] = "unknown"
        result["sha"] = "unknown"
        result["dirty"] = None
    return result


def check_runuser_fs() -> dict:
    uid = os.getuid()
    run_user = Path(f"/run/user/{uid}")
    result = {"path": str(run_user), "exists": run_user.exists(), "fstype": None}
    if run_user.exists():
        try:
            out = subprocess.check_output(
                ["stat", "-f", "-c", "%T", str(run_user)],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            result["fstype"] = out
        except (subprocess.CalledProcessError, FileNotFoundError):
            result["fstype"] = "unknown"
    return result


def check_docker() -> dict:
    result = {"docker": False, "compose": False}
    try:
        subprocess.check_output(["docker", "info"], stderr=subprocess.DEVNULL)
        result["docker"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    try:
        subprocess.check_output(["docker", "compose", "version"], stderr=subprocess.DEVNULL)
        result["compose"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return result


def check_compose_profile(ops: dict) -> dict:
    project_path = Path(ops["project_path"])
    compose_file = project_path / "docker-compose.yml"
    profile = ops["compose_profile"]
    service = ops["compose_service"]
    result = {
        "compose_file_exists": compose_file.exists(),
        "profile_found": False,
        "service_found": False,
    }
    if not compose_file.exists():
        return result
    content = compose_file.read_text()
    result["profile_found"] = profile in content
    result["service_found"] = service in content
    return result


def get_container_env_names(service_name: str) -> list:
    try:
        out = subprocess.check_output(
            ["docker", "inspect", service_name,
             "--format", "{{range .Config.Env}}{{.}}\n{{end}}"],
            text=True, stderr=subprocess.DEVNULL
        )
        names = []
        for line in out.splitlines():
            if "=" in line:
                names.append(line.split("=", 1)[0])
        return names
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def check_token_not_in_env(service_name: str) -> dict:
    token_keywords = ["TOKEN", "SECRET", "KEY", "CREDENTIAL", "PASS"]
    env_names = get_container_env_names(service_name)
    suspicious = [n for n in env_names if any(k in n.upper() for k in token_keywords)]
    return {"env_names_count": len(env_names), "suspicious_keys": suspicious}


def check_gpg_core(ops: dict) -> dict:
    provider_path = Path(ops["secret_provider_path"])
    secure_up = provider_path / "scripts" / "secure_up.sh"
    return {
        "gpg_core_path_exists": provider_path.exists(),
        "secure_up_exists": secure_up.exists(),
        "secure_up_executable": os.access(secure_up, os.X_OK) if secure_up.exists() else False,
    }


def check_runtime_dir() -> dict:
    uid = os.getuid()
    run_user = Path(f"/run/user/{uid}")
    return {
        "run_user_path": str(run_user),
        "exists": run_user.exists(),
        "writable": os.access(run_user, os.W_OK) if run_user.exists() else False,
    }


def load_state(ops: dict) -> dict:
    state_path = Path(ops["state_file"])
    if not state_path.exists():
        return {}
    with state_path.open() as f:
        return json.load(f)


def save_state(ops: dict, state: dict) -> None:
    state_path = Path(ops["state_file"])
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=state_path.parent, prefix=".tmp-state-")
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(state, f, indent=2)
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp_path, state_path)
        os.chmod(state_path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        die(f"state file write failed: {e}")


def cmd_inspect(ops: dict, _args) -> None:
    sc_git = git_info(str(OPERATIONS_FILE.parent.parent))
    project_git = git_info(ops["project_path"])
    report = {
        "schema_version": ops.get("schema_version"),
        "project_id": ops["project_id"],
        "project_path": ops["project_path"],
        "tunnel_name": ops["tunnel_name"],
        "preview_hostname": ops["preview_hostname"],
        "production_hostname": ops["production_hostname"],
        "origin_url": ops["origin_url"],
        "metrics_url": ops["metrics_url"],
        "compose_profile": ops["compose_profile"],
        "compose_service": ops["compose_service"],
        "runtime_secret_environment_name": ops["runtime_secret_environment_name"],
        "container_secret_path": ops["container_secret_path"],
        "external_blocked_paths": ops.get("external_blocked_paths", []),
        "approval_required": ops.get("approval_required", []),
        "state_file": ops["state_file"],
        "server_core_git": sc_git,
        "project_git": project_git,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


def cmd_plan(ops: dict, _args) -> None:
    sc_git = git_info(str(OPERATIONS_FILE.parent.parent))
    project_git = git_info(ops["project_path"])
    plan = {
        "plan_generated_at": datetime.now(timezone.utc).isoformat(),
        "server_core_git": sc_git,
        "project_git": project_git,
        "note": "このPlanはCloudflare APIを変更しない。管理者が承認後に手動で実行すること。",
        "cloudflare_operations_required": [
            {
                "step": 1, "action": "CREATE_TUNNEL",
                "description": f"Cloudflare Tunnelを作成する: {ops['tunnel_name']}",
                "tunnel_name": ops["tunnel_name"], "approval_gate": "Gate7:Tunnelだけ作成", "status": "pending",
            },
            {
                "step": 2, "action": "OBTAIN_TUNNEL_TOKEN",
                "description": "Tunnel Token を取得しGPG-Core で暗号化して .env.gpg に保存する",
                "token_env_name": ops["runtime_secret_environment_name"],
                "secret_provider": ops["secret_provider_path"], "approval_gate": "Gate8:Token暗号化・Runtime-Secret生成", "status": "pending",
            },
            {
                "step": 3, "action": "CREATE_DNS_CNAME_PREVIEW",
                "description": f"DNS CNAMEを作成: {ops['preview_hostname']} → <tunnel-id>.cfargotunnel.com",
                "hostname": ops["preview_hostname"], "zone": "asterav8.jp",
                "approval_gate": "Gate9:Preview-Route・Access作成", "status": "pending",
            },
            {
                "step": 4, "action": "CONFIGURE_INGRESS_RULES",
                "description": "Tunnel Ingress ルールを設定する (origin, blocked_paths)",
                "origin_url": ops["origin_url"], "blocked_paths": ops.get("external_blocked_paths", []),
                "approval_gate": "Gate9:Preview-Route・Access作成", "status": "pending",
            },
            {
                "step": 5, "action": "CREATE_DNS_CNAME_PRODUCTION",
                "description": f"本番DNS CNAMEを作成: {ops['production_hostname']} → <tunnel-id>.cfargotunnel.com",
                "hostname": ops["production_hostname"], "zone": "asterav8.jp",
                "approval_gate": "Gate12:api.asterav8.jp本番公開", "status": "pending",
            },
        ],
        "local_operations_required": [
            {
                "step": "L1", "action": "GPG_ENCRYPT_TOKEN",
                "description": "Tunnel Token を GPG 暗号化して astera_v8/.env.gpg に保存する",
                "script": f"{ops['secret_provider_path']}/scripts/secure_up.sh",
                "approval_gate": "Gate8:Token暗号化・Runtime-Secret生成",
            },
            {
                "step": "L2", "action": "START_CLOUDFLARE_PROFILE",
                "description": "secure_up.sh --profile cloudflare --secret ... 経由で docker compose --profile cloudflare up -d を実行する",
                "approval_gate": "Gate10:Docker起動",
            },
        ],
    }
    print(json.dumps(plan, indent=2, ensure_ascii=False))


def cmd_preflight(ops: dict, _args) -> None:
    passed = True
    docker = check_docker()
    (ok if docker["docker"] else warn)("docker daemon " + ("応答あり" if docker["docker"] else "接続不可"))
    if not docker["docker"]: passed = False
    (ok if docker["compose"] else warn)("docker compose " + ("利用可能" if docker["compose"] else "見つからない"))
    if not docker["compose"]: passed = False

    compose_check = check_compose_profile(ops)
    if compose_check["compose_file_exists"]:
        ok(f"docker-compose.yml 存在: {ops['project_path']}/docker-compose.yml")
    else:
        warn(f"docker-compose.yml が見つからない: {ops['project_path']}/docker-compose.yml"); passed = False
    if compose_check["profile_found"]:
        ok(f"compose profile '{ops['compose_profile']}' 検出")
    else:
        warn(f"compose profile '{ops['compose_profile']}' が docker-compose.yml に見つからない"); passed = False
    if compose_check["service_found"]:
        ok(f"compose service '{ops['compose_service']}' 検出")
    else:
        warn(f"compose service '{ops['compose_service']}' が見つからない"); passed = False

    gpg = check_gpg_core(ops)
    if gpg["gpg_core_path_exists"]: ok(f"GPG-Core 存在: {ops['secret_provider_path']}")
    else: warn(f"GPG-Core が見つからない: {ops['secret_provider_path']}"); passed = False
    if gpg["secure_up_exists"]: ok("secure_up.sh 存在")
    else: warn("secure_up.sh が見つからない"); passed = False
    if gpg["secure_up_executable"]: ok("secure_up.sh 実行可能")
    else: warn("secure_up.sh に実行権限がない"); passed = False

    runtime = check_runtime_dir()
    if runtime["exists"]: ok(f"/run/user/<uid> 存在: {runtime['run_user_path']}")
    else: warn(f"/run/user/<uid> が存在しない: {runtime['run_user_path']}"); passed = False
    if runtime["writable"]: ok("/run/user/<uid> 書き込み可能")
    else: warn("/run/user/<uid> に書き込み権限がない"); passed = False

    fs = check_runuser_fs()
    info(f"/run/user/<uid> fstype: {fs.get('fstype', 'unknown')}")

    token_env = os.environ.get(ops["runtime_secret_environment_name"])
    if token_env:
        if Path(token_env).exists(): ok(f"Token File 存在: {token_env} (値は表示しない)")
        else: warn(f"Token File が見つからない: {token_env}")
    else:
        info(f"{ops['runtime_secret_environment_name']} 未設定 (cloudflare Profile 起動前に設定が必要)")

    state_path = Path(ops["state_file"])
    if state_path.exists():
        mode = oct(stat.S_IMODE(os.stat(state_path).st_mode))
        ok(f"State File 存在: {ops['state_file']} (mode {mode})")
    else:
        info(f"State File 未作成: {ops['state_file']}")

    if passed: ok("preflight 全チェック通過")
    else: die("preflight に失敗した項目があります。上記 [WARN] を確認してください。")


def cmd_review(ops: dict, _args) -> None:
    sc_git = git_info(str(OPERATIONS_FILE.parent.parent))
    project_git = git_info(ops["project_path"])
    docker = check_docker()
    compose_check = check_compose_profile(ops)
    gpg = check_gpg_core(ops)
    runtime = check_runtime_dir()
    fs = check_runuser_fs()
    state = load_state(ops)
    token_check = check_token_not_in_env(ops["compose_service"])
    token_file_env = os.environ.get(ops["runtime_secret_environment_name"])
    report = {
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "server_core_git": sc_git, "project_git": project_git,
        "docker": docker, "compose": compose_check, "gpg_core": gpg,
        "runtime_dir": runtime, "run_user_fs": fs,
        "token_file": {
            "env_set": token_file_env is not None,
            "file_exists": Path(token_file_env).exists() if token_file_env else False,
        },
        "container_env_check": {
            "env_names_count": token_check["env_names_count"],
            "suspicious_key_names": token_check["suspicious_keys"],
            "note": "値は表示しない",
        },
        "current_state": state if state else "(state file なし)",
        "tunnel_name": ops["tunnel_name"],
        "hostnames": {"preview": ops["preview_hostname"], "production": ops["production_hostname"]},
        "approval_required": ops.get("approval_required", []),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


def cmd_local_up(ops: dict, args) -> None:
    if not args.confirm:
        die("--confirm が必要です (Mutation 系操作)")
    token_file_env = os.environ.get(ops["runtime_secret_environment_name"])
    if not token_file_env:
        die(f"{ops['runtime_secret_environment_name']} が設定されていません。GPG-Core の secure_up.sh で Token File を生成してから実行してください。")
    if not Path(token_file_env).exists():
        die(f"Token File が見つかりません: {token_file_env}")

    info(f"compose profile '{ops['compose_profile']}' を起動します...")
    result = subprocess.run(
        ["docker", "compose", "--project-directory", ops["project_path"],
         "--profile", ops["compose_profile"], "up", "-d"],
        capture_output=True, text=True
    )
    completed = ["compose コマンドを発行"]
    pending = []
    if result.returncode == 0:
        ok("docker compose up 完了"); completed.append("container 起動")
        state = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "profile": ops["compose_profile"], "service": ops["compose_service"],
            "server_core_git": git_info(str(OPERATIONS_FILE.parent.parent)),
            "project_git": git_info(ops["project_path"]),
            "token_file_path": token_file_env, "token_file_value": "(保存しない)",
        }
        save_state(ops, state)
        ok(f"State File 更新: {ops['state_file']}"); completed.append("state file 更新")
        pending = ["verify サブコマンドで疎通確認を実施すること"]
    else:
        warn(f"docker compose up 失敗:\n{result.stderr}"); pending = ["エラーを確認して再実行すること"]
    print(json.dumps({"completed": completed, "pending": pending}, indent=2, ensure_ascii=False))


def cmd_status(ops: dict, _args) -> None:
    service = ops["compose_service"]
    state = load_state(ops)
    try:
        out = subprocess.check_output(
            ["docker", "inspect", service, "--format", "{{.State.Status}} {{.State.Running}}"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        container_status = {"raw": out}
    except (subprocess.CalledProcessError, FileNotFoundError):
        container_status = {"raw": "container not found or not running"}

    state_path = Path(ops["state_file"])
    state_mode = oct(stat.S_IMODE(os.stat(state_path).st_mode)) if state_path.exists() else None
    print(json.dumps({
        "service": service, "container": container_status,
        "state_file": ops["state_file"], "state_file_mode": state_mode,
        "state": state if state else "(state file なし)",
    }, indent=2, ensure_ascii=False))


def cmd_verify(ops: dict, _args) -> None:
    results = {}
    info(f"origin {ops['origin_url']}/healthz を確認します...")
    try:
        with urllib.request.urlopen(ops["origin_url"] + "/healthz", timeout=5) as r:
            results["origin_healthz"] = {"status": r.status, "ok": r.status == 200}
    except Exception as e:
        results["origin_healthz"] = {"status": None, "ok": False, "error": str(e)}

    info(f"metrics {ops['metrics_url']} を確認します...")
    try:
        with urllib.request.urlopen(ops["metrics_url"], timeout=5) as r:
            results["metrics"] = {"status": r.status, "ok": r.status == 200}
    except Exception as e:
        results["metrics"] = {"status": None, "ok": False, "error": str(e)}

    all_ok = all(v["ok"] for v in results.values())
    results["overall"] = "PASS" if all_ok else "FAIL"
    print(json.dumps(results, indent=2, ensure_ascii=False))
    if not all_ok:
        die("verify: 一部のチェックが失敗しました")


def cmd_stop(ops: dict, args) -> None:
    if not args.confirm:
        die("--confirm が必要です (Mutation 系操作)")
    result = subprocess.run(
        ["docker", "compose", "--project-directory", ops["project_path"],
         "--profile", ops["compose_profile"], "stop", ops["compose_service"]],
        capture_output=True, text=True
    )
    completed = ["stop コマンドを発行"]
    pending = []
    if result.returncode == 0:
        ok(f"service '{ops['compose_service']}' 停止完了"); completed.append("container 停止")
        state = load_state(ops); state["stopped_at"] = datetime.now(timezone.utc).isoformat()
        save_state(ops, state); completed.append("state file 更新 (stopped_at)")
    else:
        warn(f"stop 失敗:\n{result.stderr}"); pending.append("エラーを確認して再実行すること")
    print(json.dumps({"completed": completed, "pending": pending}, indent=2, ensure_ascii=False))


def cmd_rollback(ops: dict, args) -> None:
    if not args.confirm:
        die("--confirm が必要です (Mutation 系操作)")
    state = load_state(ops)
    if not state:
        die("rollback: State File が存在しないか空です。rollback できません。")
    info(f"rollback: sha={state.get('project_git', {}).get('sha')}, started_at={state.get('started_at')}")
    stop_result = subprocess.run(
        ["docker", "compose", "--project-directory", ops["project_path"],
         "--profile", ops["compose_profile"], "stop", ops["compose_service"]],
        capture_output=True, text=True
    )
    completed = []
    pending = []
    if stop_result.returncode == 0:
        ok(f"service '{ops['compose_service']}' 停止完了"); completed.append("container 停止")
    else:
        warn(f"stop 失敗 (続行します):\n{stop_result.stderr}"); pending.append("手動で container を停止すること")
    state["rollback_at"] = datetime.now(timezone.utc).isoformat()
    save_state(ops, state); completed.append("state file に rollback_at を記録")
    pending.append("CloudflareダッシュボードでTunnelの状態を確認し、必要に応じて手動でIngress設定を戻すこと")
    print(json.dumps({"completed": completed, "pending": pending}, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Astera v8 Cloudflare Tunnel 運用スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(f"  {cmd:<12} {desc}" for cmd, desc in SUBCOMMANDS.items()),
    )
    parser.add_argument("subcommand", choices=list(SUBCOMMANDS.keys()), help="実行するサブコマンド")
    parser.add_argument("--project", default="astera_v8", help="操作対象のプロジェクトID (default: astera_v8)")
    parser.add_argument("--confirm", action="store_true", help="Mutation 系サブコマンドの実行を許可するフラグ")
    args = parser.parse_args()

    if args.subcommand not in SUBCOMMANDS:
        die(f"unknown subcommand: '{args.subcommand}'")

    ops = load_ops(args.project)
    dispatch = {
        "inspect": cmd_inspect, "plan": cmd_plan, "preflight": cmd_preflight,
        "review": cmd_review, "local-up": cmd_local_up, "status": cmd_status,
        "verify": cmd_verify, "stop": cmd_stop, "rollback": cmd_rollback,
    }
    dispatch[args.subcommand](ops, args)


if __name__ == "__main__":
    main()
