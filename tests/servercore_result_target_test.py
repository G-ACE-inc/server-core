import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import servercore_result_target as target  # noqa: E402


class ResultTargetTests(unittest.TestCase):
    def test_registered_issue_and_ceiling_are_valid(self):
        value = target.load_target()
        self.assertEqual(value["repository"], target.OWNER)
        self.assertEqual(value["issue_number"], 351)
        self.assertEqual(value["dispatch_comment_ceiling"], 2400)

    def test_invalid_target_denied(self):
        value = target.load_target().copy()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.json"
            for change in ({"issue_number": 0}, {"issue_number": True},
                           {"dispatch_comment_ceiling": 2500}, {"repository": "other/repo"}):
                path.write_text(json.dumps({"result_return": {**value, **change}}))
                with self.assertRaisesRegex(target.ResultTargetError, "CONTRACT_INVALID"):
                    target.load_target(path)

    def test_capacity_guard_denies_before_dispatch(self):
        value = target.load_target()

        def response(comments, *, locked=False, state="open"):
            def runner(args, **_kwargs):
                self.assertEqual(args[-1], "repos/G-ACE-inc/server-core/issues/351")
                return SimpleNamespace(returncode=0, stdout=json.dumps({
                    "comments": comments, "locked": locked, "state": state}))
            return runner

        self.assertEqual(target.check_capacity(value, runner=response(2399)), 2399)
        with self.assertRaisesRegex(target.ResultTargetError, "CAPACITY_EXHAUSTED"):
            target.check_capacity(value, runner=response(2400))
        with self.assertRaisesRegex(target.ResultTargetError, "NOT_WRITABLE"):
            target.check_capacity(value, runner=response(0, locked=True))

    def test_workflow_checks_capacity_before_sender_and_polls_same_issue(self):
        workflow = (ROOT / ".github/workflows/chatgpt-live-api-verify.yml").read_text()
        dispatch = workflow.split("- name: Common bounded Host gateway dispatch", 1)[1]
        self.assertLess(dispatch.index("servercore_result_target.py --repository"),
                        dispatch.index("servercore_bounded_host_gateway_send.py"))
        self.assertIn('--issue "$BOUNDED_RESULT_ISSUE"', workflow)
        self.assertNotIn("--issue 10", workflow)


if __name__ == "__main__":
    unittest.main()
