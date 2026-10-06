#!/usr/bin/env python3
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "github_project_request_from_comment.py"

spec = importlib.util.spec_from_file_location("github_project_request_from_comment", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def event(body, login="seigo-gace", comment_id=123, issue_number=10, repo="G-ACE-inc/server-core"):
    return {
        "repository": {"full_name": repo},
        "issue": {"number": issue_number},
        "comment": {
            "id": comment_id,
            "body": body,
            "user": {"login": login},
        },
    }


class CommentRequestTest(unittest.TestCase):
    def test_valid_owner_comment_builds_fixed_request(self):
        payload = {
            "item_url": "https://github.com/seigo-gace/asteria/issues/6",
            "field": "Gate",
            "value": "CI_PASS",
        }
        req, meta = module.parse_comment_event(
            event("[GACE-PROJECT]\n" + json.dumps(payload))
        )
        expected = "gpc_" + hashlib.sha256(
            b"G-ACE-inc/server-core:10:123"
        ).hexdigest()[:24]
        self.assertEqual(req, {
            "schema": "gace.github-project-control/v1",
            "id": expected,
            "actor": "seigo-gace",
            "operation": "set_field",
            **payload,
        })
        self.assertEqual(meta["request_id"], expected)
        self.assertEqual(meta["execution"], "NOT_RUN")

    def test_request_id_is_stable_for_same_comment(self):
        body = '[GACE-PROJECT]\n{"item_url":"https://github.com/G-ACE-inc/server-core/issues/10","field":"Gate","value":"CI_PASS"}'
        first, _ = module.parse_comment_event(event(body, comment_id=999))
        second, _ = module.parse_comment_event(event(body, comment_id=999))
        self.assertEqual(first["id"], second["id"])

    def test_non_owner_is_rejected(self):
        body = '[GACE-PROJECT]\n{"item_url":"https://github.com/G-ACE-inc/server-core/issues/10","field":"Gate","value":"CI_PASS"}'
        with self.assertRaisesRegex(module.RequestBuildError, "COMMENT_ACTOR_NOT_ALLOWED"):
            module.parse_comment_event(event(body, login="someone-else"))

    def test_unknown_payload_key_is_rejected(self):
        body = '[GACE-PROJECT]\n{"item_url":"https://github.com/G-ACE-inc/server-core/issues/10","field":"Gate","value":"CI_PASS","command":"rm -rf /"}'
        with self.assertRaisesRegex(module.RequestBuildError, "COMMENT_KEYS_INVALID"):
            module.parse_comment_event(event(body))

    def test_secret_like_value_is_rejected(self):
        body = '[GACE-PROJECT]\n{"item_url":"https://github.com/G-ACE-inc/server-core/issues/10","field":"Change Unit","value":"Bearer abcdefghijklmnop"}'
        with self.assertRaisesRegex(module.RequestBuildError, "COMMENT_SECRET_LIKE_VALUE_REJECTED"):
            module.parse_comment_event(event(body))

    def test_wrong_control_repository_is_rejected(self):
        body = '[GACE-PROJECT]\n{"item_url":"https://github.com/G-ACE-inc/server-core/issues/10","field":"Gate","value":"CI_PASS"}'
        with self.assertRaisesRegex(module.RequestBuildError, "CONTROL_REPOSITORY_INVALID"):
            module.parse_comment_event(event(body, repo="seigo-gace/debug-ai"))


if __name__ == "__main__":
    unittest.main()
