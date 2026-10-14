import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts/chatgpt_isolated_request_select.py"
spec = importlib.util.spec_from_file_location("request_select", MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
P = ".github/chat-host-requests/req_" + "a" * 24 + ".json"
BASE = {"bounded_host_request": {"enabled": True, "command_id": "project.git_head", "expected_sha": "b" * 40},
        "chat_decision_checkpoint": {"phase": "START"},
        "gitops_request": {"enabled": False}, "source_reflect_request": {"enabled": False}}

class IsolatedRequests(unittest.TestCase):
    def test_separate_commit_request(self):
        self.assertEqual(str(m.select([P], [P])), P)
        self.assertIsNone(m.select([], ["README.md"]))

    def test_reject_shared_target_mutation_and_replay(self):
        for added, changed in [([], [P]), ([P], [P, m.LEGACY_TARGET]),
                               ([P], [P, P.replace("a" * 24, "c" * 24)]),
                               ([P], [P.replace("req_", "bad_")])]:
            with self.subTest(added=added, changed=changed):
                with self.assertRaises(ValueError):
                    m.select(added, changed)

    def test_current_terminal_uses_independent_commit_lanes(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/chatgpt-live-api-verify.yml").read_text()
        self.assertIn("group: common-host-${{ github.sha }}", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("github.sha || 'legacy'", workflow)
        self.assertNotIn("DEBUGAI_CF_ACCESS_CLIENT_ID", workflow)

    def test_receipt_and_effect_admission(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "request.json"
            p.write_text(json.dumps(BASE))
            self.assertEqual(m.prepare(p)["bounded_host_request"]["command_id"], "project.git_head")
            for mutate in [
                {**BASE, "chat_decision_checkpoint": {"phase": "STOP"}},
                {**BASE, "gitops_request": {"enabled": True}},
                {**BASE, "server_command_id": "service.debug_ai_logs"},
            ]:
                p.write_text(json.dumps(mutate))
                with self.assertRaises(ValueError):
                    m.prepare(p)

if __name__ == "__main__":
    unittest.main()
