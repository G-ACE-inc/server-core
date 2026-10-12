#!/usr/bin/env python3
import importlib.util
import unittest
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
    def test_wrong_project_id_denied(self):
        with self.assertRaisesRegex(ValueError,"PROJECT_ID_INVALID"):
            mod.recover("bad",lambda q,v:packet([]))
if __name__=="__main__":
    unittest.main()
