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

    def test_server_core_dispatcher_and_target_sha_must_agree(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "request.json"
            base = {**BASE, "bounded_host_request": {
                "enabled": True, "command_id": "host.command",
                "repository": "G-ACE-inc/server-core",
                "expected_sha": "a" * 40, "repo_sha": "b" * 40,
                "command": "git rev-parse HEAD"}}
            p.write_text(json.dumps(base))
            with self.assertRaisesRegex(ValueError, "SERVER_CORE_HOST_SHA_PINS_CONFLICT"):
                m.prepare(p)
            base["bounded_host_request"]["repo_sha"] = "a" * 40
            p.write_text(json.dumps(base))
            self.assertEqual(m.prepare(p)["bounded_host_request"]["repo_sha"], "a" * 40)
            # Other repositories have distinct registered target checkout SHAs.
            base["bounded_host_request"]["repository"] = "seigo-gace/ai-core"
            base["bounded_host_request"]["repo_sha"] = "b" * 40
            p.write_text(json.dumps(base))
            self.assertEqual(m.prepare(p)["bounded_host_request"]["repo_sha"], "b" * 40)

    def test_source_bound_diagnostic_targets_existing_pr_worktree(self):
        # Real AI Core failure: the registered source import checkout did
        # not contain the test, while this already-existing PR worktree did.
        source = {**BASE, "bounded_host_request": {
            "enabled": True, "command_id": "host.command",
            "repository": "seigo-gace/ai-core",
            "expected_sha": "a" * 40,
            "repo_sha": "b" * 40,
            "command": "python3 -m unittest discover -s tests -p test_model_gate.py -q",
            "source_context": {
                "repository": "seigo-gace/ai-core",
                "workdir": "/home/admin1/projects/ai-core/.worktrees/pr3-verification-20261015",
                "source_sha": "c" * 40,
                "required_files": ["tests/test_model_gate.py"],
            },
        }}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "request.json"
            path.write_text(json.dumps(source))
            prepared = m.prepare(path)["bounded_host_request"]
            script = prepared["command"]
            self.assertNotIn("source_context", prepared)
            self.assertTrue(script.startswith("(\ncd /home/admin1/projects/ai-core/"))
            self.assertIn('git rev-parse HEAD', script)
            self.assertIn('CHAT_SOURCE_SHA_MISMATCH', script)
            self.assertIn('CHAT_SOURCE_REQUIRED_FILE_MISSING', script)
            self.assertIn('test -f tests/test_model_gate.py', script)
            self.assertIn('python3 -m unittest discover', script)
            self.assertTrue(script.endswith("\n)"))

    def test_source_bound_diagnostic_rejects_misrouted_repo_and_escape(self):
        target = {
            "enabled": True, "command_id": "host.command",
            "repository": "seigo-gace/ai-core", "expected_sha": "a" * 40,
            "repo_sha": "b" * 40, "command": "printf ok",
            "source_context": {"repository": "seigo-gace/ai-core",
                 "workdir": "/home/admin1/projects/ai-core/.worktrees/pr3-verification-20261015",
                 "source_sha": "c" * 40, "required_files": ["tests/test_model_gate.py"]},
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "request.json"
            for field, value, expected in [
                ("repository", "G-ACE-inc/server-core", "SOURCE_CONTEXT_REPOSITORY_MISMATCH"),
                ("workdir", "/home/admin1/server-core", "SOURCE_CONTEXT_WORKDIR_OUTSIDE_REGISTERED_CHECKOUT"),
                ("workdir", "/home/admin1/projects/ai-core/.worktrees/../other", "SOURCE_CONTEXT_WORKDIR_INVALID"),
                ("source_sha", "a" * 8, "SOURCE_CONTEXT_SHA_INVALID"),
                ("required_files", ["../scripts/servercore_host_output_read.py"],
                 "SOURCE_CONTEXT_REQUIRED_FILES_INVALID"),
            ]:
                changed = {**target["source_context"], field: value}
                candidate = {**BASE, "bounded_host_request": {**target, "source_context": changed}}
                p.write_text(json.dumps(candidate))
                with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, expected):
                    m.prepare(p)
            # Existing legacy freeform calls are unchanged when no context is
            # requested. This adds no global Master approval or new worker.
            clean = {**target}
            clean.pop("source_context")
            p.write_text(json.dumps({**BASE, "bounded_host_request": clean}))
            self.assertEqual(m.prepare(p)["bounded_host_request"]["command"], "printf ok")

    def test_source_bound_diagnostic_shell_quotes_untrusted_file_names(self):
        base = {**BASE, "bounded_host_request": {
            "enabled": True, "command_id": "host.command",
            "repository": "G-ACE-inc/server-core", "expected_sha": "a" * 40,
            "repo_sha": "a" * 40, "command": "printf done",
            "source_context": {"repository": "G-ACE-inc/server-core",
                 "workdir": "/home/admin1/server-core", "source_sha": "a" * 40,
                 "required_files": ["tests/test user's.py"]}}}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "request.json"
            p.write_text(json.dumps(base))
            script = m.prepare(p)["bounded_host_request"]["command"]
            self.assertIn("test -f 'tests/test user", script)
            self.assertIn("CHAT_SOURCE_REQUIRED_FILE_MISSING", script)

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
