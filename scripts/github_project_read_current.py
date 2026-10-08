#!/usr/bin/env python3
"""Bounded read-only Current values for registered GitHub Project #1 items.

Reuses the existing Project Control identity, item and GraphQL field readers.
It never dispatches events or calls a Project mutation.
"""
import argparse
import json

import github_project_control as control
from github_project_control import (
    ControlError,
    DEFAULT_CONTRACT,
    find_item_id,
    load_json,
    parse_json,
    read_field_value,
    validate_contract,
    validate_item_url,
    verify_project_identity,
)

FIELDS = ("Wave", "Gate", "Change Unit", "Mutation Owner")
SCHEMA = "gace.github-project-current-read/v1"


def read_current(item_url, contract):
    item_url = validate_item_url(item_url, contract)
    verify_project_identity(contract)
    item_id = find_item_id(item_url, contract)
    values = {field: read_field_value(item_id, field, contract) for field in FIELDS}
    complete = all(isinstance(v, str) and bool(v.strip()) for v in values.values())
    return {
        "schema": SCHEMA,
        "status": "PASS" if complete else "PARTIAL",
        "project": {
            "owner": contract["project"]["owner"],
            "number": contract["project"]["number"],
            "node_id": contract["project"]["node_id"],
        },
        "item_url": item_url,
        "fields": values,
        "read_only": True,
        "mutation_performed": False,
    }


def expected_control_issue_urls(contract):
    """Derive mandatory control/rule-plane items from existing canonical files."""
    manifest = load_json(DEFAULT_CONTRACT.with_name("github-project-rule-plane.json"),
                         "RULE_PLANE_JSON_INVALID")
    if not isinstance(manifest, dict) or manifest.get("project") != contract["project"]:
        raise ControlError("RULE_PLANE_PROJECT_MISMATCH")
    try:
        urls = [
            manifest["control_plane"]["issue_url"],
            manifest["rule_planes"]["server_ai"]["issue_url"],
            manifest["rule_planes"]["gpt_chat"]["issue_url"],
            ("https://github.com/" +
             contract["internal_event_transport"]["result_sink"]["repository"] +
             "/issues/" +
             str(contract["internal_event_transport"]["result_sink"]["issue_number"])),
        ]
    except (KeyError, TypeError, ValueError):
        raise ControlError("CONTROL_ISSUE_REGISTRY_INVALID")
    normalized = tuple(validate_item_url(url, contract) for url in urls)
    if len(normalized) != 4 or len(set(normalized)) != 4:
        raise ControlError("CONTROL_ISSUE_REGISTRY_INVALID")
    return normalized


def read_registered_current(contract):
    """Enumerate existing Project items without adding or changing any item."""
    verify_project_identity(contract)
    project = contract["project"]
    raw = control.gh_run(
        ["project", "item-list", str(project["number"]),
         "--owner", project["owner"],
         "--limit", str(contract.get("item_read_limit", 1000)),
         "--format", "json"], contract,
    )
    data = parse_json(raw, "PROJECT_ITEMS_JSON_INVALID")
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ControlError("PROJECT_ITEMS_SCHEMA_INVALID")
    items = data["items"]
    limit = min(int(contract.get("item_read_limit", 1000)), 1000)
    if len(items) > limit:
        raise ControlError("PROJECT_ITEMS_LIMIT_EXCEEDED")
    registered = []
    skipped = 0
    seen_urls = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("content"), dict):
            skipped += 1
            continue
        url = item["content"].get("url")
        item_id = item.get("id")
        try:
            valid_url = validate_item_url(url, contract)
        except ControlError:
            skipped += 1
            continue
        if not isinstance(item_id, str) or not item_id.startswith("PVTI_"):
            raise ControlError("PROJECT_ITEM_ID_INVALID")
        if valid_url in seen_urls:
            raise ControlError("PROJECT_ITEM_DUPLICATE")
        seen_urls.add(valid_url)
        registered.append({"url": valid_url, "item_id": item_id})
    if len(registered) > 25:
        raise ControlError("PROJECT_READ_BATCH_TOO_LARGE")
    unregistered = sorted(set(expected_control_issue_urls(contract)) - seen_urls)
    out = []
    for item in registered:
        fields = {field: read_field_value(item["item_id"], field, contract)
                  for field in FIELDS}
        out.append({"item_url": item["url"], "item_id": item["item_id"],
                    "fields": fields})
    complete = bool(out) and skipped == 0 and not unregistered and all(
        all(isinstance(v, str) and v.strip() for v in item["fields"].values())
        for item in out
    )
    return {
        "schema": SCHEMA,
        "status": "PASS" if complete else "PARTIAL",
        "project": {"owner": project["owner"], "number": project["number"],
                    "node_id": project["node_id"]},
        "items": out,
        "excluded_item_count": skipped,
        "registered_item_count": len(out),
        "unregistered_control_issue_urls": unregistered,
        "read_only": True,
        "mutation_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read four Current fields from existing G-ACE Project #1")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--item-url")
    target.add_argument("--all-registered", action="store_true")
    args = parser.parse_args(argv)
    try:
        contract = validate_contract(load_json(DEFAULT_CONTRACT, "CONTRACT_JSON_INVALID"))
        result = read_registered_current(contract) if args.all_registered else read_current(args.item_url, contract)
    except ControlError as exc:
        result = {"schema": SCHEMA, "status": "FAIL", "error": str(exc)[:120],
                  "read_only": True, "mutation_performed": False}
    except Exception:
        result = {"schema": SCHEMA, "status": "FAIL", "error": "PROJECT_CURRENT_READ_FAILED",
                  "read_only": True, "mutation_performed": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
