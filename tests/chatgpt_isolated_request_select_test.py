import copy
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts/chatgpt_isolated_request_select.py"
spec = importlib.util.spec_from_file_location("request_select", MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
P = ".github/chat-host-requests/req_" + "a" * 24 + ".json"
BASE = {"bounded_host_request": {"enabled": True, "command_id": "project.git_head", "expected_sha": "b" * 40},
        "chat_decision_checkpoint": {"phase": "START"},
        "gitops_request": {"enabled": False}, "source_reflect_request": {"enabled": False}}

class IsolatedRequests(unittest.TestCase):
    def test_gserver_planning_context_never_rewrites_free_command(self):
        source = {**BASE, "bounded_host_request": {
            "enabled": True, "command_id": "host.command", "host_target": "gserver",
            "repository": "seigo-gace/G-ACEserver", "expected_sha": "a" * 40,
            "repo_sha": "b" * 40, "command": "pwd; git rev-parse HEAD",
            "project_context": {"repository": "../ignored", "sha": "bad"},
            "source_context": {"workdir": "/ignored"},
            "source_preflight": True}}
        prepared = m.prepare_data(source)["bounded_host_request"]
        self.assertEqual(prepared["command"], "pwd; git rev-parse HEAD")
        self.assertNotIn("project_context", prepared)
        self.assertNotIn("source_context", prepared)
        self.assertNotIn("source_preflight", prepared)

    def test_gserver_syntax_and_production_words_reach_real_host(self):
        for command in ("if then", "docker compose up -d",
                        "sudo systemctl restart example"):
            source = {**BASE, "bounded_host_request": {
                "enabled": True, "command_id": "host.command",
                "host_target": "gserver",
                "repository": "seigo-gace/G-ACEserver",
                "expected_sha": "a" * 40, "repo_sha": "b" * 40,
                "command": command}}
            with self.subTest(command=command):
                self.assertEqual(
                    m.prepare_data(source)["bounded_host_request"]["command"],
                    command)

    def test_long_unicode_request_is_not_rejected_by_legacy_8k_limit(self):
        source = {**BASE, "bounded_host_request": {
            "enabled": True, "command_id": "host.command",
            "repository": "G-ACE-inc/server-core", "expected_sha": "a" * 40,
            "repo_sha": "a" * 40, "command": "#" + "日本語" * 2200 + "\nprintf ok\n"}}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "request.json"
            path.write_text(json.dumps(source, ensure_ascii=False))
            self.assertGreater(path.stat().st_size, 8192)
            self.assertEqual(m.prepare(path)["bounded_host_request"]["command"],
                             source["bounded_host_request"]["command"])
            path.write_text(" " * (m.MAX_REQUEST_FILE_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "REQUEST_FILE_TOO_LARGE"):
                m.prepare(path)

    def test_separate_commit_request(self):
        self.assertEqual(str(m.select([P], [P])), P)
        self.assertIsNone(m.select([], ["README.md"]))

    def test_selected_file_name_is_the_returned_host_request_id(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "selected.json"
            with patch.object(m, "git_paths", return_value=[P]), \
                 patch.object(m, "prepare", return_value={**BASE, "chat_host_request_id": "req_" + "f" * 24}), \
                 patch.object(m, "TARGET", target):
                self.assertEqual(m.main(), 0)
            self.assertEqual(json.loads(target.read_text())["chat_host_request_id"], Path(P).stem)

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
            self.assertIs(prepared["source_preflight"], True)
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


    def test_source_preflight_cannot_be_claimed_without_context(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "request.json"
            request = {**BASE, "bounded_host_request": {
                "enabled": True, "command_id": "host.command",
                "repository": "seigo-gace/ai-core",
                "expected_sha": "a" * 40, "repo_sha": "b" * 40,
                "command": "printf ok", "source_preflight": True}}
            path.write_text(json.dumps(request))
            with self.assertRaisesRegex(ValueError, "SOURCE_PREFLIGHT_INTERNAL_ONLY"):
                m.prepare(path)

    def test_real_git_worktree_dirty_and_independent_clone(self):
        # Execute the generated shell against temporary actual Git objects.
        # No Host checkout or AI Core worktree is touched.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp, "canonical")
            root.mkdir()
            def git(*argv):
                return subprocess.check_output(["git", *map(str, argv)], stderr=subprocess.DEVNULL).decode().strip()
            git("init", "-q", root)
            (root / "source.txt").write_text("baseline")
            git("-C", root, "add", "source.txt")
            git("-C", root, "-c", "user.email=unit@example.com",
                "-c", "user.name=Unit", "commit", "-qm", "initial")
            sha = git("-C", root, "rev-parse", "HEAD")
            git("-C", root, "worktree", "add", "-q", "--detach",
                root / ".worktrees" / "source-import-20261013", "HEAD")
            wt = root / ".worktrees" / "good"
            git("-C", root, "worktree", "add", "-q", "--detach", wt, "HEAD")
            def run_at(target):
                bounded = {"command_id": "host.command",
                           "repository": "seigo-gace/ai-core",
                           "command": "printf WORKTREE_OK"}
                ctx = {"repository": "seigo-gace/ai-core",
                       "workdir": "/home/admin1/projects/ai-core/.worktrees/" + target.name,
                       "source_sha": sha, "required_files": ["source.txt"]}
                cmd = m.bind_source_context(bounded, ctx)["command"]
                cmd = cmd.replace("/home/admin1/projects/ai-core", str(root))
                return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
            good = run_at(wt)
            self.assertEqual((good.returncode, good.stdout, good.stderr), (0, "__GACE_SOURCE_PREFLIGHT_OK__\nWORKTREE_OK", ""))
            (wt / "untracked.txt").write_text("dirty")
            dirty = run_at(wt)
            self.assertEqual(dirty.returncode, 76)
            self.assertEqual(dirty.stderr.strip(), "CHAT_SOURCE_DIRTY_WORKTREE")
            (wt / "untracked.txt").unlink()
            clone = root / ".worktrees" / "bad"
            git("clone", "-q", root, clone)
            wrong = run_at(clone)
            self.assertEqual(wrong.returncode, 72)
            self.assertEqual(wrong.stderr.strip(), "CHAT_SOURCE_ROOT_MISMATCH")
            missing = run_at(root / ".worktrees" / "missing")
            self.assertEqual((missing.returncode, missing.stderr.strip()),
                             (70, "CHAT_SOURCE_WORKDIR_MISSING"))

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

    def test_omitted_sibling_effects_are_independent_requests(self):
        # 2026-11-19 req_20261119140600000000c601 was denied before Host
        # dispatch because absent effect objects were read as enabled.
        minimal = {
            "bounded_host_request": {
                "enabled": True, "command_id": "host.command", "host_target": "gserver",
                "repository": "seigo-gace/G-ACEserver", "expected_sha": "a" * 40,
                "repo_sha": "b" * 40, "command": "printf TERMINAL_READONLY_OK\\n",
                "project_context": {"repository": "seigo-gace/create-videobot"},
            },
            "chat_decision_checkpoint": {"phase": "START"},
        }
        prepared = m.prepare_data(copy.deepcopy(minimal))
        self.assertNotIn("gitops_request", prepared)
        self.assertNotIn("source_reflect_request", prepared)
        self.assertNotIn("project_context", prepared["bounded_host_request"])
        self.assertIn("create-videobot", prepared["bounded_host_request"]["command"])
        self.assertIn("printf TERMINAL_READONLY_OK", prepared["bounded_host_request"]["command"])
        one_side = copy.deepcopy(minimal)
        one_side["gitops_request"] = {"enabled": False}
        self.assertIs(m.prepare_data(one_side)["gitops_request"]["enabled"], False)
        for key, value in (
            ("gitops_request", {"enabled": True}),
            ("source_reflect_request", {"enabled": True}),
            ("gitops_request", {}),
            ("source_reflect_request", {"enabled": None}),
            ("gitops_request", "false"),
            ("source_reflect_request", None),
        ):
            with self.subTest(key=key, value=value):
                candidate = copy.deepcopy(minimal)
                candidate[key] = value
                with self.assertRaisesRegex(ValueError, "CONCURRENT_EFFECT_DENIED"):
                    m.prepare_data(candidate)

    def test_distinct_commits_stay_independent_and_one_commit_cannot_carry_two(self):
        first = ".github/chat-host-requests/req_" + "a" * 24 + ".json"
        second = ".github/chat-host-requests/req_" + "b" * 24 + ".json"
        self.assertEqual(str(m.select([first], [first])), first)
        self.assertEqual(str(m.select([second], [second])), second)
        with self.assertRaisesRegex(ValueError, "REQUEST_PATH_DENIED"):
            m.select([first, second], [first, second])

    def test_workflow_validation_accepts_omitted_effects_and_rejects_active_ones(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/chatgpt-live-api-verify.yml").read_text()
        start = workflow.index("jq -e '") + len("jq -e '")
        filt = workflow[start:workflow.index("' \"$target\"", start)]
        self.assertIn('has("gitops_request")', filt)
        self.assertIn('has("source_reflect_request")', filt)
        self.assertNotIn(".gitops_request.enabled == false and .source_reflect_request.enabled == false", filt)

        def inactive(document, key):
            if key not in document:
                return True
            effect = document[key]
            return isinstance(effect, dict) and effect.get("enabled") is False

        def admit(document):
            bounded = document.get("bounded_host_request") or {}
            expected = (bounded.get("enabled") is True
                        and inactive(document, "gitops_request")
                        and inactive(document, "source_reflect_request")
                        and (document.get("server_command_id") or "") == ""
                        and (document.get("run_id") or "") == "")
            if shutil.which("jq"):
                completed = subprocess.run(
                    ["jq", "-e", filt], input=json.dumps(document),
                    text=True, capture_output=True, check=False)
                self.assertEqual(completed.returncode == 0, expected)
            return expected

        independent = {
            "bounded_host_request": {"enabled": True, "command_id": "host.command"},
            "chat_decision_checkpoint": {"phase": "START"},
        }
        explicit = {**independent, "gitops_request": {"enabled": False},
                    "source_reflect_request": {"enabled": False},
                    "server_command_id": "", "run_id": ""}
        self.assertTrue(admit(independent))
        self.assertTrue(admit(explicit))
        self.assertFalse(admit({**independent, "gitops_request": {"enabled": True},
                                "source_reflect_request": {"enabled": False}}))
        self.assertFalse(admit({**independent, "gitops_request": {"enabled": False},
                                "source_reflect_request": {"enabled": True}}))
        self.assertFalse(admit({**independent, "gitops_request": {}}))
        self.assertFalse(admit({**explicit, "server_command_id": "service.deploy"}))
        self.assertFalse(admit({**explicit, "run_id": "1"}))

if __name__ == "__main__":
    unittest.main()
