#!/usr/bin/env python3
import argparse
import fcntl
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "operations" / "github-project-control.json"
REQUEST_ID_RE = re.compile(r"^gpc_[0-9a-f]{24}$")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


class ControlError(RuntimeError):
    pass


def fail(code):
    raise ControlError(code)


def load_json(path, code):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        fail(code)


def validate_contract(contract):
    if contract.get("schema_version") != "1.0":
        fail("CONTRACT_VERSION_INVALID")
    if contract.get("name") != "gace-github-project-control":
        fail("CONTRACT_NAME_INVALID")
    if contract.get("request_schema") != "gace.github-project-control/v1":
        fail("CONTRACT_REQUEST_SCHEMA_INVALID")
    project = contract.get("project")
    if not isinstance(project, dict):
        fail("CONTRACT_PROJECT_INVALID")
    if project.get("owner") != "seigo-gace" or project.get("number") != 1:
        fail("CONTRACT_PROJECT_BOUNDARY_INVALID")
    if project.get("node_id") != "PVT_kwHODOQFoM4BEJII":
        fail("CONTRACT_PROJECT_ID_INVALID")
    if project.get("title") != "G-ACE Development Platform":
        fail("CONTRACT_PROJECT_TITLE_INVALID")
    if contract.get("allowed_repository_owners") != ["seigo-gace", "G-ACE-inc"]:
        fail("CONTRACT_REPOSITORY_OWNERS_INVALID")
    fields = contract.get("allowed_fields")
    if not isinstance(fields, dict) or set(fields) != {"Wave", "Gate", "Change Unit", "Mutation Owner"}:
        fail("CONTRACT_FIELDS_INVALID")
    return contract


def validate_item_url(value, contract):
    if not isinstance(value, str) or value != value.strip():
        fail("REQUEST_ITEM_URL_INVALID")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment:
        fail("REQUEST_ITEM_URL_INVALID")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 4 or parts[0] not in contract["allowed_repository_owners"]:
        fail("REQUEST_ITEM_URL_NOT_ALLOWED")
    if not parts[1] or parts[2] not in {"issues", "pull"} or not parts[3].isdigit() or int(parts[3]) < 1:
        fail("REQUEST_ITEM_URL_INVALID")
    return "https://github.com/" + "/".join(parts)


def normalize_value(field, value, contract):
    if not isinstance(value, str) or value != value.strip() or not value:
        fail("REQUEST_VALUE_INVALID")
    if CONTROL_CHAR_RE.search(value):
        fail("REQUEST_VALUE_INVALID")
    rule = contract["allowed_fields"][field]
    if len(value) > int(rule["max_length"]):
        fail("REQUEST_VALUE_TOO_LONG")
    pattern = rule.get("pattern")
    if pattern and not re.fullmatch(pattern, value):
        fail("REQUEST_VALUE_NOT_ALLOWED")
    return value


def validate_request(request, contract):
    if not isinstance(request, dict):
        fail("REQUEST_INVALID")
    required = {"schema", "id", "actor", "operation", "item_url", "field", "value"}
    if set(request) != required:
        fail("REQUEST_KEYS_INVALID")
    if request["schema"] != contract["request_schema"]:
        fail("REQUEST_SCHEMA_INVALID")
    if not isinstance(request["id"], str) or not REQUEST_ID_RE.fullmatch(request["id"]):
        fail("REQUEST_ID_INVALID")
    if request["actor"] != contract["request_actor"]:
        fail("REQUEST_ACTOR_INVALID")
    if request["operation"] != "set_field":
        fail("REQUEST_OPERATION_INVALID")
    field = request["field"]
    if field not in contract["allowed_fields"]:
        fail("REQUEST_FIELD_NOT_ALLOWED")
    return {
        "schema": request["schema"],
        "id": request["id"],
        "actor": request["actor"],
        "operation": request["operation"],
        "item_url": validate_item_url(request["item_url"], contract),
        "field": field,
        "value": normalize_value(field, request["value"], contract),
    }


def gh_run(args, contract):
    gh_bin = os.environ.get("GACE_PROJECT_CONTROL_GH_BIN", "gh")
    timeout = int(contract.get("timeouts", {}).get("command_seconds", 30))
    env = os.environ.copy()
    env["GH_PROMPT_DISABLED"] = "1"
    try:
        completed = subprocess.run(
            [gh_bin, *args],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except FileNotFoundError:
        fail("GH_DEPENDENCY_MISSING")
    except subprocess.TimeoutExpired:
        fail("GH_COMMAND_TIMEOUT")
    if completed.returncode != 0:
        fail("GH_COMMAND_FAILED")
    return completed.stdout


def parse_json(raw, code):
    try:
        return json.loads(raw)
    except Exception:
        fail(code)


def verify_project_identity(contract):
    project = contract["project"]
    raw = gh_run(
        ["project", "view", str(project["number"]), "--owner", project["owner"], "--format", "json"],
        contract,
    )
    data = parse_json(raw, "PROJECT_VIEW_JSON_INVALID")
    if data.get("title") != project["title"]:
        fail("PROJECT_TITLE_MISMATCH")
    if data.get("id") is not None and data.get("id") != project["node_id"]:
        fail("PROJECT_ID_MISMATCH")


def find_item_id(item_url, contract):
    project = contract["project"]
    raw = gh_run(
        [
            "project", "item-list", str(project["number"]),
            "--owner", project["owner"],
            "--limit", str(contract.get("item_read_limit", 1000)),
            "--format", "json",
        ],
        contract,
    )
    data = parse_json(raw, "PROJECT_ITEMS_JSON_INVALID")
    matches = []
    for item in data.get("items", []):
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if isinstance(content, dict) and content.get("url") == item_url and isinstance(item.get("id"), str):
            matches.append(item["id"])
    if len(matches) != 1:
        fail("PROJECT_ITEM_NOT_FOUND_OR_AMBIGUOUS")
    return matches[0]


FIELD_QUERY = """query($item: ID!, $field: String!) {
  node(id: $item) {
    ... on ProjectV2Item {
      fieldValueByName(name: $field) {
        ... on ProjectV2ItemFieldTextValue { text }
        ... on ProjectV2ItemFieldSingleSelectValue { name }
        ... on ProjectV2ItemFieldNumberValue { number }
        ... on ProjectV2ItemFieldDateValue { date }
        ... on ProjectV2ItemFieldIterationValue { title }
      }
    }
  }
}"""


def read_field_value(item_id, field, contract):
    raw = gh_run(
        ["api", "graphql", "-f", "query=" + FIELD_QUERY, "-f", "item=" + item_id, "-f", "field=" + field],
        contract,
    )
    data = parse_json(raw, "PROJECT_FIELD_READBACK_JSON_INVALID")
    try:
        value = data["data"]["node"]["fieldValueByName"]
    except Exception:
        fail("PROJECT_FIELD_READBACK_MISSING")
    if value is None:
        return None
    if not isinstance(value, dict):
        fail("PROJECT_FIELD_READBACK_INVALID")
    for key in ("text", "name", "number", "date", "title"):
        if key in value and value[key] is not None:
            return str(value[key])
    fail("PROJECT_FIELD_READBACK_INVALID")


def edit_field(item_url, field, value, contract):
    project = contract["project"]
    gh_run(
        [
            "project", "item-edit", str(project["number"]),
            "--owner", project["owner"],
            "--url", item_url,
            "--field", field,
            "--value", value,
        ],
        contract,
    )


def result_lines(result):
    print("GACE_RESULT_BEGIN")
    for key in (
        "RESULT", "REQUEST_ID", "PROJECT", "ITEM_URL", "FIELD", "VALUE",
        "READBACK", "MUTATION_PERFORMED", "ERROR",
    ):
        if key in result:
            print(f"{key}={result[key]}")
    print("GACE_RESULT_END")


def execute(request, contract):
    request = validate_request(request, contract)
    verify_project_identity(contract)
    item_id = find_item_id(request["item_url"], contract)
    before = read_field_value(item_id, request["field"], contract)
    mutation = "NO"
    if before != request["value"]:
        edit_field(request["item_url"], request["field"], request["value"], contract)
        mutation = "YES"
    readback = read_field_value(item_id, request["field"], contract)
    if readback != request["value"]:
        fail("PROJECT_FIELD_READBACK_MISMATCH")
    return {
        "RESULT": "PASS",
        "REQUEST_ID": request["id"],
        "PROJECT": f'{contract["project"]["owner"]}#{contract["project"]["number"]}',
        "ITEM_URL": request["item_url"],
        "FIELD": request["field"],
        "VALUE": request["value"],
        "READBACK": readback,
        "MUTATION_PERFORMED": mutation,
    }


def main():
    parser = argparse.ArgumentParser(description="Bounded GitHub Project #1 field mutation with exact readback")
    parser.add_argument("--request", required=True)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    try:
        contract = validate_contract(load_json(args.contract, "CONTRACT_JSON_INVALID"))
        request = validate_request(load_json(args.request, "REQUEST_JSON_INVALID"), contract)
        if args.validate_only:
            result_lines({
                "RESULT": "PASS",
                "REQUEST_ID": request["id"],
                "PROJECT": f'{contract["project"]["owner"]}#{contract["project"]["number"]}',
                "ITEM_URL": request["item_url"],
                "FIELD": request["field"],
                "VALUE": request["value"],
                "READBACK": "NOT_EXECUTED",
                "MUTATION_PERFORMED": "NO",
            })
            return 0

        lock_path = Path(os.environ.get(
            "GACE_PROJECT_CONTROL_LOCK",
            str(Path.home() / ".cache" / "gace" / "github-project-control.lock"),
        ))
        lock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fail("PROJECT_CONTROL_BUSY")
            result_lines(execute(request, contract))
            return 0
    except ControlError as exc:
        result_lines({"RESULT": "FAIL", "ERROR": str(exc)[:120]})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
