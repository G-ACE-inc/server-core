#!/usr/bin/env python3
import importlib.util
import contextlib
import hashlib
import io
import unittest
from unittest.mock import patch
from pathlib import Path

path=Path(__file__).with_name("gace_project_current_recovery.py")
spec=importlib.util.spec_from_file_location("recover",path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
P="PVT_kwHODOQFoM4BEJII"

def issue(item_id,url,state="OPEN",fields=None):
    fields=fields or {}
    vals=[{"field":{"name":k},"text":v} for k,v in fields.items()]
    return {"id":item_id,"content":{"__typename":"Issue","url":url,"state":state,"title":"Example"},
            "fieldValues":{"nodes":vals}}

def packet(nodes,next_cursor=None):
    return {"node":{"id":P,"items":{"nodes":nodes,"pageInfo":{"hasNextPage":bool(next_cursor),"endCursor":next_cursor}}}}

class RecoveryTests(unittest.TestCase):
    def test_mixed_items_and_owner_admission(self):
        a=issue("a","https://github.com/G-ACE-inc/server-core/issues/15",fields={"Change Unit":"C05","Mutation Owner":"team"})
        b=issue("b","https://github.com/seigo-gace/TGserver/issues/44","CLOSED")
        pr={"id":"pr","content":{"__typename":"PullRequest","url":"https://github.com/abc/def/pull/1"}}
        out=mod.recover(P,lambda q,v:packet([a,b,pr]))
        self.assertEqual(out["issue_count"],2)
        self.assertFalse(out["dispatch_authorized"])
        self.assertEqual(out["issue_items"][0]["recovery"],"READY_FOR_OWNER_CURRENT_RECHECK")
        self.assertEqual(out["issue_items"][1]["recovery"],"CLOSED_NO_DISPATCH")
    def test_missing_owner_must_not_dispatch(self):
        a=issue("a","https://github.com/seigo-gace/asteria/issues/5",fields={"Change Unit":"A/B"})
        out=mod.recover(P,lambda q,v:packet([a]))
        self.assertEqual(out["issue_items"][0]["recovery"],"OWNER_OR_CU_REQUIRED")
    def test_cursor_pagination(self):
        calls=[]
        def fetch(q,v):
            calls.append(v["cursor"])
            return packet([issue("a","https://github.com/x/y/issues/1")],"next") if len(calls)==1 else packet([issue("b","https://github.com/x/y/issues/2")])
        self.assertEqual(mod.recover(P,fetch)["issue_count"],2)
        self.assertEqual(calls,[None,"next"])
    def test_duplicate_issue_rejected(self):
        a=issue("a","https://github.com/x/y/issues/1")
        b=issue("b","https://github.com/x/y/issues/1")
        with self.assertRaisesRegex(RuntimeError,"DUPLICATE_ISSUE"):
            mod.recover(P,lambda q,v:packet([a,b]))
    def test_wrong_project_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"PROJECT_ID_MISMATCH"):
            mod.recover(P,lambda q,v:{"node":{"id":"PVT_other","items":{"nodes":[]}}})
    def test_invalid_issue_state_denied(self):
        with self.assertRaisesRegex(RuntimeError,"ISSUE_STATE_UNVERIFIED"):
            mod.recover(P,lambda q,v:packet([issue("a","https://github.com/x/y/issues/1","UNKNOWN")]))
    def test_repeated_cursor_denied(self):
        with self.assertRaisesRegex(RuntimeError,"PROJECT_PAGINATION_INVALID"):
            mod.recover(P,lambda q,v:packet([],"next"))
    def test_fresh_issue_closed_overrides_project_cache(self):
        item=issue("a","https://github.com/x/y/issues/1",state="OPEN",
                   fields={"Change Unit":"C05","Mutation Owner":"writer"})
        current={"html_url":"https://github.com/x/y/issues/1","state":"closed",
                 "body":"Canonical current", "updated_at":"2026-10-12T00:00:00Z"}
        out=mod.recover(P,lambda q,v:packet([item]),lambda repo,num:current)
        row=out["issue_items"][0]
        self.assertEqual(row["recovery"],"CLOSED_NO_DISPATCH")
        self.assertEqual(row["fields"]["Project state mismatch"],"YES")
        self.assertEqual(len(row["current_body_sha256"]),64)

    def test_wrong_issue_current_rejected(self):
        item=issue("a","https://github.com/x/y/issues/1")
        for current in (
            {"html_url":"https://github.com/x/y/issues/2","state":"open","body":"bad"},
            {"html_url":"https://github.com/x/y/issues/1","state":"open","body":"bad","pull_request":{}},
            {"html_url":"https://github.com/x/y/issues/1","state":"open"},
        ):
            with self.subTest(current=current):
                with self.assertRaisesRegex(RuntimeError,"ISSUE_CURRENT_IDENTITY_INVALID"):
                    mod.recover(P,lambda q,v:packet([item]),lambda repo,num:current)
    def test_wrong_project_id_denied(self):
        with self.assertRaisesRegex(ValueError,"PROJECT_ID_INVALID"):
            mod.recover("bad",lambda q,v:packet([]))

    def test_scoped_recovery_reads_one_current_and_returns_same_body(self):
        nodes = [issue(str(n), f"https://github.com/x/y/issues/{n}") for n in range(1, 12)]
        calls = []
        body = "## Purpose\n実際の目的\n" + "evidence\n" * 2000
        def current(repo, number):
            calls.append((repo, number))
            return {"html_url": f"https://github.com/{repo}/issues/{number}",
                    "state": "open", "body": body, "updated_at": "2026-10-17T00:00:00Z"}
        out = mod.recover(P, lambda q,v: packet(nodes), current,
                          issue_urls=["https://github.com/x/y/issues/7"], include_body=True)
        self.assertEqual(calls, [("x/y", 7)])
        self.assertEqual((out["issue_count"], out["registered_issue_count"]), (1, 11))
        self.assertEqual(out["issue_items"][0]["current_body"], body)
        self.assertEqual(out["issue_items"][0]["current_body_sha256"], hashlib.sha256(body.encode()).hexdigest())
        self.assertFalse(out["dispatch_authorized"])

    def test_default_inventory_remains_compatible_and_omits_bodies(self):
        nodes = [issue(str(n), f"https://github.com/x/y/issues/{n}") for n in (1, 2)]
        calls = []
        def current(repo, number):
            calls.append(number)
            return {"html_url": f"https://github.com/{repo}/issues/{number}", "state": "open", "body": "Current"}
        out = mod.recover(P, lambda q,v: packet(nodes), current)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(out["issue_count"], 2)
        self.assertTrue(all("current_body" not in row for row in out["issue_items"]))

    def test_selected_missing_issue_never_fetches_any_current(self):
        with self.assertRaisesRegex(RuntimeError, "SELECTED_ISSUE_NOT_REGISTERED"):
            mod.recover(P, lambda q,v: packet([issue("a", "https://github.com/x/y/issues/1")]),
                        lambda *args: self.fail("must not read an unregistered or partial selection"),
                        issue_urls=["https://github.com/x/y/issues/1", "https://github.com/x/y/issues/40"])

    def test_validate_complete_registration_before_scoped_read(self):
        calls = []
        url = "https://github.com/x/y/issues/1"
        def fetch(query, variables):
            calls.append(variables["cursor"])
            return packet([issue("a", url)], "next") if len(calls) == 1 else packet([issue("b", url)])
        with self.assertRaisesRegex(RuntimeError, "DUPLICATE_ISSUE_REGISTRATION"):
            mod.recover(P, fetch, lambda *args: self.fail("must finish registration checks first"), issue_urls=[url])
        self.assertEqual(calls, [None, "next"])

    def test_selected_later_page_and_duplicate_selectors_read_once(self):
        url = "https://github.com/x/y/issues/2"
        events = []
        def fetch(query, variables):
            events.append(variables["cursor"])
            return packet([issue("a", "https://github.com/x/y/issues/1")], "next") if variables["cursor"] is None else packet([issue("b", url)])
        def current(repo, number):
            events.append((repo, number))
            return {"html_url": url, "state": "closed", "body": "Current"}
        out = mod.recover(P, fetch, current, issue_urls=[url, url])
        self.assertEqual(events, [None, "next", ("x/y", 2)])
        self.assertEqual(out["issue_items"][0]["recovery"], "CLOSED_NO_DISPATCH")

    def test_invalid_selector_or_unscoped_body_denied_before_network(self):
        for selector in ([], "https://github.com/x/y/issues/1", [None],
                         ["https://github.com/x/y/pull/1"],
                         ["https://github.com/x/y/issues/1#issuecomment-2"]):
            with self.subTest(selector=selector), self.assertRaisesRegex(ValueError, "SELECTED_ISSUE_URL_INVALID"):
                mod.recover(P, lambda *args: self.fail("must not read"), issue_urls=selector)
        for kwargs in ({"include_body": True}, {"include_body": True, "issue_urls": ["https://github.com/x/y/issues/1"]}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, "CURRENT_BODY_REQUIRES_SCOPED_LIVE_READ"):
                mod.recover(P, lambda *args: self.fail("must not read"), **kwargs)

    def test_multi_cursor_cycle_is_rejected(self):
        cursors = iter(("a", "b", "a"))
        with self.assertRaisesRegex(RuntimeError, "PROJECT_PAGINATION_INVALID"):
            mod.recover(P, lambda q,v: packet([], next(cursors)))

    def test_cli_passes_selection_and_fails_closed(self):
        url = "https://github.com/x/y/issues/40"
        with patch.object(mod, "recover", side_effect=RuntimeError("SELECTED_ISSUE_NOT_REGISTERED")) as recover:
            with contextlib.redirect_stderr(io.StringIO()) as err, contextlib.redirect_stdout(io.StringIO()) as out:
                code = mod.main(["--project-id", P, "--issue-url", url, "--include-body"])
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("SELECTED_ISSUE_NOT_REGISTERED", err.getvalue())
        self.assertEqual(recover.call_args.kwargs["issue_urls"], [url])
        self.assertTrue(recover.call_args.kwargs["include_body"])

    def test_open_issue_done_project_status_requires_recheck_without_new_fields(self):
        item = issue("a", "https://github.com/x/y/issues/1",
                     fields={"Change Unit": "CU", "Mutation Owner": "writer"})
        item["fieldValues"]["nodes"].append({"field": {"name": "Status"}, "name": "Done"})
        out = mod.recover(P, lambda q,v: packet([item]),
                          lambda repo,num: {"html_url": "https://github.com/x/y/issues/1",
                                            "state": "open", "body": "Still unfinished"})
        row = out["issue_items"][0]
        self.assertEqual(row["project_status"], "Done")
        self.assertEqual(row["recovery"], "PROJECT_STATUS_RECHECK_REQUIRED")
        self.assertNotIn("Status", row["fields"])
        self.assertFalse(out["dispatch_authorized"])

    def test_in_progress_status_preserves_readiness_and_fresh_closed_still_wins(self):
        for state, expected in (("open", "READY_FOR_OWNER_CURRENT_RECHECK"),
                                ("closed", "CLOSED_NO_DISPATCH")):
            with self.subTest(state=state):
                item = issue("a", "https://github.com/x/y/issues/1",
                             fields={"Change Unit": "CU", "Mutation Owner": "writer", "Status": "In Progress"})
                calls = []
                def current(repo, num):
                    calls.append((repo,num))
                    return {"html_url": "https://github.com/x/y/issues/1", "state": state, "body": "Current"}
                out = mod.recover(P, lambda q,v: packet([item]), current,
                                  issue_urls=["https://github.com/x/y/issues/1"])
                self.assertEqual(out["issue_items"][0]["recovery"], expected)
                self.assertEqual(out["issue_items"][0]["project_status"], "In Progress")
                self.assertEqual(calls, [("x/y",1)])
if __name__=="__main__":
    unittest.main()
