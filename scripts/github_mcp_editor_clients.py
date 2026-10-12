#!/usr/bin/env python3
"""Configure one official GitHub MCP definition for editor clients; never store tokens."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import tomllib
from pathlib import Path

CONTRACT = Path(__file__).resolve().parents[1] / "operations/github-mcp-editor-clients.json"
CLIENTS = ("cursor", "vscode", "codex")


class ClientConfigError(Exception):
    pass


def spec():
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if (data.get("schema") != "gace.github-mcp-editor-clients/v1"
            or data.get("name") != "github"
            or data.get("url") != "https://api.githubcopilot.com/mcp/"
            or data.get("bearer_env") != "GACE_GITHUB_MCP_TOKEN"
            or data.get("readonly") is not True
            or data.get("consumers") != list(CLIENTS)
            or data.get("toolsets") != ["projects", "repos", "issues", "pull_requests", "actions"]):
        raise ClientConfigError("CANONICAL_CLIENT_CONTRACT_MISMATCH")
    return data


def definitions(data):
    toolsets = ",".join(data["toolsets"])
    name, url, env = data["name"], data["url"], data["bearer_env"]
    headers = {"X-MCP-Toolsets": toolsets, "X-MCP-Readonly": "true"}
    return {
        "cursor": {"url": url, "headers": {
            **headers, "Authorization": "Bearer ${env:" + env + "}"
        }},
        # VS Code / Copilot user-portable config uses OAuth via the official
        # GitHub-hosted MCP. Never put a static token in the JSON file.
        "vscode": {"type": "http", "url": url, "headers": headers},
        "codex": {"url": url, "bearer_token_env_var": env, "http_headers": headers},
    }


def target_paths(home):
    home = Path(home)
    return {
        "cursor": home / ".cursor" / "mcp.json",
        "vscode": home / ".copilot" / "mcp-config.json",
        "codex": home / ".codex" / "config.toml",
    }


def read_existing(client, path):
    if path.is_symlink():
        raise ClientConfigError(client.upper() + "_CONFIG_SYMLINK_NOT_ALLOWED")
    if not path.exists():
        return {}, None
    try:
        raw = path.read_text(encoding="utf-8")
        parsed = tomllib.loads(raw) if client == "codex" else json.loads(raw)
    except (OSError, ValueError) as exc:
        raise ClientConfigError(client.upper() + "_CONFIG_UNREADABLE_OR_INVALID") from exc
    if not isinstance(parsed, dict):
        raise ClientConfigError(client.upper() + "_CONFIG_NOT_OBJECT")
    return parsed, raw


def entry_container(client):
    return "mcp_servers" if client == "codex" else "mcpServers"


def entry_state(client, parsed, expected):
    slot = parsed.get(entry_container(client), {})
    if not isinstance(slot, dict):
        raise ClientConfigError(client.upper() + "_SERVER_MAP_INVALID")
    if "github" not in slot:
        return "ADD"
    # No rewriting an existing GitHub MCP entry. Even a valid but differently
    # scoped client entry needs its owner's explicit reconciliation.
    return "MATCH" if slot["github"] == expected else "COLLISION"


def json_render(client, parsed, expected):
    out = dict(parsed)
    slot = dict(parsed.get(entry_container(client), {}))
    slot["github"] = expected
    out[entry_container(client)] = slot
    return json.dumps(out, ensure_ascii=False, indent=2) + "\n"


def codex_render(raw, expected):
    # Append a uniquely named TOML table; never rewrite any user setting.
    # Existing GitHub table is detected and rejected before reaching here.
    name = "github"
    headers = expected["http_headers"]
    rows = ["[mcp_servers." + name + "]",
            "url = " + json.dumps(expected["url"]),
            "bearer_token_env_var = " + json.dumps(expected["bearer_token_env_var"]),
            "http_headers = { " + ", ".join(
                json.dumps(k) + " = " + json.dumps(v) for k, v in headers.items()
            ) + " }"]
    prefix = (raw or "").rstrip()
    return (prefix + "\n\n" if prefix else "") + "\n".join(rows) + "\n"


def inspect(*, home=None, clients=CLIENTS):
    data = spec()
    paths = target_paths(Path.home() if home is None else home)
    expected = definitions(data)
    result = {}
    for client in clients:
        if client not in CLIENTS:
            raise ClientConfigError("CLIENT_UNKNOWN")
        parsed, raw = read_existing(client, paths[client])
        state = entry_state(client, parsed, expected[client])
        result[client] = {
            "target": paths[client], "existing": parsed, "raw": raw,
            "expected": expected[client], "state": state,
        }
    return result


def atomic_write(path, content, old_content):
    if path.is_symlink():
        raise ClientConfigError("CONFIG_SYMLINK_NOT_ALLOWED")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ClientConfigError("CONFIG_DIRECTORY_SYMLINK_NOT_ALLOWED")
    if old_content is None:
        if path.exists():
            raise ClientConfigError("CHANGED_SINCE_PREFLIGHT")
    else:
        if not path.is_file() or path.read_text(encoding="utf-8") != old_content:
            raise ClientConfigError("CHANGED_SINCE_PREFLIGHT")
        backup = path.with_name(path.name + ".gace-backup")
        if backup.exists() or backup.is_symlink():
            raise ClientConfigError("BACKUP_PATH_ALREADY_EXISTS")
        shutil.copy2(path, backup)
        os.chmod(backup, 0o600)
    fd, temporary = tempfile.mkstemp(prefix=".gace-github-mcp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(content)
        os.chmod(temporary, 0o600)
        if old_content is None:
            try:
                os.link(temporary, path)
            except FileExistsError as exc:
                raise ClientConfigError("CHANGED_SINCE_PREFLIGHT") from exc
        else:
            if path.read_text(encoding="utf-8") != old_content or path.is_symlink():
                raise ClientConfigError("CHANGED_SINCE_PREFLIGHT")
            os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(*, home=None, clients=CLIENTS, apply=False, environ=None):
    items = inspect(home=home, clients=clients)
    results = {c: obj["state"] for c, obj in items.items()}
    if any(v == "COLLISION" for v in results.values()):
        raise ClientConfigError("EXISTING_GITHUB_MCP_COLLISION_NO_MUTATION")
    if not apply:
        return {"status": "PLAN_ONLY_NO_MUTATION", "clients": results}
    env = os.environ if environ is None else environ
    # Cursor/Codex require a bearer. VS Code OAuth authorization occurs
    # in its own UI; config presence is NOT an authenticated E2E.
    token_clients = set(clients).intersection(("cursor", "codex"))
    if token_clients and not str(env.get("GACE_GITHUB_MCP_TOKEN", "")).strip():
        raise ClientConfigError("GITHUB_MCP_TOKEN_ENV_ABSENT_NO_MUTATION")
    # Merge only when GitHub is absent; existing GitHub entries are immutable.
    for client, obj in items.items():
        if obj["state"] != "ADD":
            continue
        rendered = (codex_render(obj["raw"], obj["expected"]) if client == "codex"
                    else json_render(client, obj["existing"], obj["expected"]))
        atomic_write(obj["target"], rendered, obj["raw"])
        results[client] = "CONFIG_WRITTEN_AUTH_NOT_VERIFIED"
    return {"status": "CONFIG_ONLY_NOT_RUNTIME_VERIFIED", "clients": results}


def main():
    parser = argparse.ArgumentParser(description="GitHub official MCP user-client registration, no Secret values")
    parser.add_argument("mode", choices=("plan", "apply"), nargs="?", default="plan")
    parser.add_argument("--client", choices=("all",) + CLIENTS, default="all")
    args = parser.parse_args()
    clients = CLIENTS if args.client == "all" else (args.client,)
    try:
        output = run(clients=clients, apply=args.mode == "apply")
    except ClientConfigError as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}))
        return 2
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
