#!/usr/bin/env python3
"""Read-only TGserver ZERO log/stream to repository coverage audit.

Never treats log registration as Host deploy authorization. Does not duplicate
TGserver registration, issue commands, or mutate runtime.
"""
import argparse
import json

# Master-confirmed workspace component, not a second independent deployment.
# Do not rewrite TGserver's repository-to-log-project registry.
COMPONENT_PARENT = {"seigo-gace/gace-dev-kb": "seigo-gace/modular-catalog"}
from pathlib import Path


def coverage(storage, repo_map, collector, deploy_registry):
    projects = storage.get("projects", {})
    mappings = repo_map.get("repos", {})
    containers = collector
    delegated = deploy_registry.get("repositories", [])
    rows = []
    reverse = {}
    for repo, streams in mappings.items():
        for stream, pid in streams.items():
            reverse.setdefault(pid, []).append({"repository": repo, "stream": stream})
    for pid, info in sorted(projects.items()):
        repos = reverse.get(pid, [])
        associated = sorted(k for k, v in containers.items() if v == pid)
        authorized = []
        for item in repos:
            for e in delegated:
                if e.get("repository") == item["repository"] and e.get("enabled") is True and e.get("revoked") is False and "deploy" in e.get("allowed_operations", []):
                    authorized.append(item["repository"])
        rows.append({
            "project_id": pid,
            "name": info.get("name"),
            "tgserver_registered": True,
            "repository_mappings": repos,
            "runtime_container_mappings": associated,
            "registered_deploy_repositories": sorted(set(authorized)),
            "deploy_coverage": "AUTHORITY_MAPPED_NOT_HOST_VERIFIED" if authorized else "DEPLOY_BINDING_MISSING",
        })
    repo_rows = []
    for repo, streams in sorted(mappings.items()):
        mapped = [row for row in rows if any(m["repository"] == repo for m in row["repository_mappings"])]
        authorized = any(repo in row["registered_deploy_repositories"] for row in mapped)
        parent = COMPONENT_PARENT.get(repo)
        repo_rows.append({"repository": repo, "deployment_unit": parent or repo,
                          "component_of": parent, "independent_deploy": parent is None,
                          "streams": dict(streams),
                          "project_ids": sorted({pid for pid in streams.values()}),
                          "runtime_containers": sorted({c for row in mapped for c in row["runtime_container_mappings"]}),
                          "deploy_coverage": "AUTHORITY_MAPPED_NOT_HOST_VERIFIED" if authorized else "DEPLOY_BINDING_MISSING"})
    return {"schema": "gace.tool-b.tgzero-deploy-coverage/v2",
            "total_registered_log_project_ids": len(rows),
            "total_repository_mappings": len(repo_rows),
            "total_deployment_units": len({r["deployment_unit"] for r in repo_rows}),
            "repositories": repo_rows, "total_registered": len(rows),
            "deploy_authority_mapped": sum(bool(row["registered_deploy_repositories"]) for row in rows),
            "rows": rows}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tgserver-root", required=True)
    p.add_argument("--server-core-root", default="/home/admin1/server-core")
    args = p.parse_args()
    source = Path(args.tgserver_root)
    registry = Path(args.server_core_root)
    storage = json.loads((source / "storage-registry.json").read_text())
    project_map = json.loads((source / ".github/tgserver-zero-project-map.json").read_text())
    collector = json.loads((source / "collector/server-log-projects.json").read_text())
    authorization = json.loads((registry / "operations/master-internal-repositories.json").read_text())
    print(json.dumps(coverage(storage, project_map, collector, authorization), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
