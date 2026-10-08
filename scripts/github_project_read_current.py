#!/usr/bin/env python3
"""Bounded read-only Current values for registered GitHub Project #1 items.

Reuses the existing Project Control identity, item and GraphQL field readers.
It never dispatches events or calls a Project mutation.
"""
import argparse
import json

from github_project_control import (
    ControlError,
    DEFAULT_CONTRACT,
    find_item_id,
    load_json,
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read four Current fields from existing G-ACE Project #1")
    parser.add_argument("--item-url", required=True)
    args = parser.parse_args(argv)
    try:
        contract = validate_contract(load_json(DEFAULT_CONTRACT, "CONTRACT_JSON_INVALID"))
        result = read_current(args.item_url, contract)
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
