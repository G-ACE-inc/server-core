#!/usr/bin/env python3
"""Fail-closed regression checks for the read-only Project Current facade."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import github_project_control as control
import github_project_read_current as current


class ProjectCurrentReadTests(unittest.TestCase):
    ITEM = "https://github.com/seigo-gace/debug-ai/issues/41"

    def setUp(self):
        self.contract = control.validate_contract(
            control.load_json(control.DEFAULT_CONTRACT, "CONTRACT_JSON_INVALID")
        )

    def stub(self, values):
        calls = []

        def fake_gh(args, _contract):
            calls.append(args)
            if args[:2] == ["project", "view"]:
                return json.dumps({"title": "G-ACE Development Platform",
                                   "id": "PVT_kwHODOQFoM4BEJII"})
            if args[:2] == ["project", "item-list"]:
                return json.dumps({"items": [{"id": "PVTI_TEST",
                                              "content": {"url": self.ITEM}}]})
            if args[:2] == ["api", "graphql"]:
                fields = [x[6:] for x in args if x.startswith("field=")]
                if len(fields) != 1:
                    raise AssertionError("Unexpected GraphQL request")
                value = values[fields[0]]
                return json.dumps({"data": {"node": {"fieldValueByName":
                    None if value is None else {"text": value}}}})
            raise AssertionError(f"Unexpected command: {args!r}")
        return calls, fake_gh

    def test_exact_four_fields_without_any_write(self):
        values = {"Wave": "Wave 1", "Gate": "CURRENT_RECONCILIATION",
                  "Change Unit": "Project Current verification",
                  "Mutation Owner": "G-ACE"}
        calls, fake_gh = self.stub(values)
        with patch.object(control, "gh_run", side_effect=fake_gh):
            result = current.read_current(self.ITEM, self.contract)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["fields"], values)
        self.assertEqual(result["item_url"], self.ITEM)
        self.assertTrue(result["read_only"])
        self.assertFalse(result["mutation_performed"])
        self.assertEqual(len(calls), 6)
        self.assertTrue(all("mutation(" not in " ".join(c) for c in calls))
        self.assertTrue(all(c[:2] in (["project", "view"], ["project", "item-list"],
                                       ["api", "graphql"]) for c in calls))

    def test_unassigned_field_is_partial_not_invented(self):
        values = {"Wave": "Wave 1", "Gate": None, "Change Unit": "Source",
                  "Mutation Owner": "G-ACE"}
        _, fake_gh = self.stub(values)
        with patch.object(control, "gh_run", side_effect=fake_gh):
            result = current.read_current(self.ITEM, self.contract)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertIsNone(result["fields"]["Gate"])

    def test_non_allowlisted_owner_and_malformed_target_rejected_pre_auth(self):
        for item in ("https://github.com/other/repo/issues/1",
                     "https://github.com/seigo-gace/debug-ai/issues/41?x=1",
                     "https://github.com/seigo-gace/debug-ai/pull/notanumber"):
            with self.subTest(item=item), patch.object(control, "gh_run") as gh:
                with self.assertRaises(control.ControlError):
                    current.read_current(item, self.contract)
                gh.assert_not_called()

    def test_project_identity_and_auth_fail_closed(self):
        with patch.object(control, "gh_run", side_effect=control.ControlError("GH_COMMAND_FAILED")):
            with self.assertRaisesRegex(control.ControlError, "GH_COMMAND_FAILED"):
                current.read_current(self.ITEM, self.contract)

    def test_registered_item_batch_uses_same_project_identity_and_four_field_reads(self):
        values = {"Wave": "Wave 1", "Gate": "CI_PASS",
                  "Change Unit": "Project bounded readback",
                  "Mutation Owner": "G-ACE"}
        calls, fake_gh = self.stub(values)
        with patch.object(control, "gh_run", side_effect=fake_gh):
            result = current.read_registered_current(self.contract)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["registered_item_count"], 1)
        self.assertEqual(result["excluded_item_count"], 0)
        self.assertEqual(result["items"][0]["item_id"], "PVTI_TEST")
        self.assertEqual(result["items"][0]["item_url"], self.ITEM)
        self.assertEqual(result["items"][0]["fields"], values)
        self.assertEqual(len(calls), 6)
        self.assertTrue(all("mutation(" not in " ".join(c) for c in calls))

    def test_missing_control_issue_is_not_fabricated_in_project_current(self):
        values = {"Wave": None, "Gate": "CI_PASS",
                  "Change Unit": "Actual registered task",
                  "Mutation Owner": "DebugAI"}
        _, fake_gh = self.stub(values)
        with patch.object(control, "gh_run", side_effect=fake_gh):
            result = current.read_registered_current(self.contract)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["registered_item_count"], 1)
        self.assertEqual(result["items"][0]["fields"]["Wave"], None)
        self.assertNotIn("https://github.com/G-ACE-inc/server-core/issues/10",
                         [item["item_url"] for item in result["items"]])

    def test_untrusted_or_duplicate_registered_items_fail_closed(self):
        def gh_with_items(items):
            def fake(args, _contract):
                if args[:2] == ["project", "view"]:
                    return json.dumps({"title": "G-ACE Development Platform",
                                       "id": "PVT_kwHODOQFoM4BEJII"})
                if args[:2] == ["project", "item-list"]:
                    return json.dumps({"items": items})
                raise AssertionError("Field read must not occur for invalid item listing")
            return fake
        for items, code in [
            ([{"id": "BAD", "content": {"url": self.ITEM}}], "PROJECT_ITEM_ID_INVALID"),
            ([{"id": "PVTI_A", "content": {"url": self.ITEM}},
              {"id": "PVTI_B", "content": {"url": self.ITEM}}], "PROJECT_ITEM_DUPLICATE"),
        ]:
            with self.subTest(code=code), patch.object(control, "gh_run",
                                                     side_effect=gh_with_items(items)):
                with self.assertRaisesRegex(control.ControlError, code):
                    current.read_registered_current(self.contract)

    def test_external_or_draft_project_items_are_counted_not_presented_as_pass(self):
        values = {"Wave": "Wave 1", "Gate": "CI_PASS",
                  "Change Unit": "Source", "Mutation Owner": "G-ACE"}
        calls, fake_gh = self.stub(values)
        def mixed(args, contract):
            if args[:2] == ["project", "item-list"]:
                return json.dumps({"items": [
                    {"id": "PVTI_TEST", "content": {"url": self.ITEM}},
                    {"id": "PVTI_EXT", "content": {"url": "https://github.com/other/repo/issues/3"}},
                    {"id": "PVTI_DRAFT", "content": {"title": "Draft without URL"}},
                ]})
            return fake_gh(args, contract)
        with patch.object(control, "gh_run", side_effect=mixed):
            result = current.read_registered_current(self.contract)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["excluded_item_count"], 2)
        self.assertEqual(result["registered_item_count"], 1)

    def test_facade_never_has_a_second_graphql_mutation_implementation(self):
        source = (Path(__file__).resolve().parent /
                  "github_project_read_current.py").read_text(encoding="utf-8")
        for forbidden in ("updateProjectV2ItemFieldValue", "subprocess.run(",
                          "GITHUB_TOKEN=", "os.environ[", "createComment"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
