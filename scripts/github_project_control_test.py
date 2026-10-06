#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_project_control.py"
CONTRACT = ROOT / "operations" / "github-project-control.json"
ITEM_URL = "https://github.com/seigo-gace/asteria/issues/6"


MOCK_GH = r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
state_path = Path(os.environ["MOCK_GH_STATE"])
log_path = Path(os.environ["MOCK_GH_LOG"])
item_url = os.environ["MOCK_ITEM_URL"]

def load_state():
    return json.loads(state_path.read_text()) if state_path.exists() else {}

def save_state(value):
    state_path.write_text(json.dumps(value))

with log_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(args) + "\n")

if args[:2] == ["project", "view"]:
    print(json.dumps({"id":"PVT_kwHODOQFoM4BEJII","title":"G-ACE Development Platform"}))
    raise SystemExit(0)

if args[:2] == ["project", "item-list"]:
    if os.environ.get("MOCK_GH_ITEM_MISSING") == "1":
        print(json.dumps({"items":[]}))
    else:
        print(json.dumps({"items":[{"id":"PVTI_TEST","content":{"url":item_url}}]}))
    raise SystemExit(0)

if args[:2] == ["project", "item-edit"]:
    field = args[args.index("--field") + 1]
    value = args[args.index("--value") + 1]
    if os.environ.get("MOCK_GH_NO_UPDATE") != "1":
        state = load_state()
        state[field] = value
        save_state(state)
    print(json.dumps({"ok":True}))
    raise SystemExit(0)

if args[:2] == ["api", "graphql"]:
    field_arg = next(x for x in args if x.startswith("field="))
    field = field_arg.split("=", 1)[1]
    value = load_state().get(field)
    payload = None if value is None else {"text": value}
    print(json.dumps({"data":{"node":{"fieldValueByName":payload}}}))
    raise SystemExit(0)

raise SystemExit(2)
'''


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.mock = self.dir / "gh"
        self.mock.write_text(MOCK_GH, encoding="utf-8")
        self.mock.chmod(0o755)
        self.state = self.dir / "state.json"
        self.log = self.dir / "gh.log"
        self.env = os.environ.copy()
        self.env.update({
            "GACE_PROJECT_CONTROL_GH_BIN": str(self.mock),
            "GACE_PROJECT_CONTROL_LOCK": str(self.dir / "control.lock"),
            "MOCK_GH_STATE": str(self.state),
            "MOCK_GH_LOG": str(self.log),
            "MOCK_ITEM_URL": ITEM_URL,
        })

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, **overrides):
        value = {
            "schema": "gace.github-project-control/v1",
            "id": "gpc_" + "a" * 24,
            "actor": "seigo-gace",
            "operation": "set_field",
            "item_url": ITEM_URL,
            "field": "Gate",
            "value": "CI_PASS",
        }
        value.update(overrides)
        path = self.dir / "request.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def run(self, request, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--request", str(request), "--contract", str(CONTRACT), *extra],
            cwd=ROOT,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )

    def log_calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def test_mutates_only_bounded_field_and_exact_readback_passes(self):
        self.state.write_text(json.dumps({"Gate":"SOURCE_IN_PROGRESS"}), encoding="utf-8")
        result = self.run(self.request())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RESULT=PASS", result.stdout)
        self.assertIn("MUTATION_PERFORMED=YES", result.stdout)
        self.assertIn("READBACK=CI_PASS", result.stdout)
        edits = [call for call in self.log_calls() if call[:2] == ["project", "item-edit"]]
        self.assertEqual(len(edits), 1)
        self.assertIn("--field", edits[0])
        self.assertIn("Gate", edits[0])

    def test_matching_value_is_idempotent_and_skips_mutation(self):
        self.state.write_text(json.dumps({"Gate":"CI_PASS"}), encoding="utf-8")
        result = self.run(self.request())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("MUTATION_PERFORMED=NO", result.stdout)
        self.assertFalse(any(call[:2] == ["project", "item-edit"] for call in self.log_calls()))

    def test_external_repository_and_unknown_field_fail_before_github(self):
        bad_url = self.run(self.request(item_url="https://github.com/other/repo/issues/1"), "--validate-only")
        self.assertNotEqual(bad_url.returncode, 0)
        self.assertIn("ERROR=REQUEST_ITEM_URL_NOT_ALLOWED", bad_url.stdout)
        bad_field = self.run(self.request(field="Status"), "--validate-only")
        self.assertNotEqual(bad_field.returncode, 0)
        self.assertIn("ERROR=REQUEST_FIELD_NOT_ALLOWED", bad_field.stdout)
        self.assertFalse(self.log.exists())

    def test_gate_value_is_bounded(self):
        result = self.run(self.request(value="ci pass"), "--validate-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR=REQUEST_VALUE_NOT_ALLOWED", result.stdout)
        self.assertFalse(self.log.exists())

    def test_readback_mismatch_fails(self):
        self.state.write_text(json.dumps({"Gate":"SOURCE_IN_PROGRESS"}), encoding="utf-8")
        self.env["MOCK_GH_NO_UPDATE"] = "1"
        result = self.run(self.request())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR=PROJECT_FIELD_READBACK_MISMATCH", result.stdout)

    def test_missing_project_item_fails_closed(self):
        self.state.write_text(json.dumps({"Gate":"SOURCE_IN_PROGRESS"}), encoding="utf-8")
        self.env["MOCK_GH_ITEM_MISSING"] = "1"
        result = self.run(self.request())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR=PROJECT_ITEM_NOT_FOUND_OR_AMBIGUOUS", result.stdout)


if __name__ == "__main__":
    unittest.main()
