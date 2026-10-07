#!/usr/bin/env python3
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "server_gitops_request.py"
RUNNER = ROOT / "scripts" / "host-server-gitops-runner.sh"
CONTRACT = ROOT / "operations" / "server-gitops.json"

spec = importlib.util.spec_from_file_location("server_gitops_request", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SharedServerGitOpsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.control = self.root / "control"
        self.control.mkdir()
        self.queue = self.root / "queue"
        self.origin = self.root / "origin.git"
        self.producer = self.root / "producer"
        self.target = self.root / "target"

        subprocess.run(["git", "init", "--bare", "-q", str(self.origin)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.producer)], check=True)
        subprocess.run(["git", "-C", str(self.producer), "config", "user.email", "ci@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.producer), "config", "user.name", "GACE CI"], check=True)
        (self.producer / "proof.txt").write_text("one\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.producer), "add", "proof.txt"], check=True)
        subprocess.run(["git", "-C", str(self.producer), "commit", "-qm", "one"], check=True)
        subprocess.run(["git", "-C", str(self.producer), "remote", "add", "origin", str(self.origin)], check=True)
        subprocess.run(["git", "-C", str(self.producer), "push", "-q", "-u", "origin", "main"], check=True)

        subprocess.run(["git", "clone", "-q", "-b", "main", str(self.origin), str(self.target)], check=True)
        subprocess.run(
            ["git", "-C", str(self.target), "remote", "set-url", "origin", "https://github.com/G-ACE-inc/server-core.git"],
            check=True,
        )
        self.before = subprocess.check_output(
            ["git", "-C", str(self.target), "rev-parse", "HEAD"], text=True
        ).strip()

        (self.producer / "proof.txt").write_text("two\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.producer), "add", "proof.txt"], check=True)
        subprocess.run(["git", "-C", str(self.producer), "commit", "-qm", "two"], check=True)
        subprocess.run(["git", "-C", str(self.producer), "push", "-q", "origin", "main"], check=True)
        self.after = subprocess.check_output(
            ["git", "-C", str(self.producer), "rev-parse", "HEAD"], text=True
        ).strip()

        self.fake_gh = self.root / "gh"
        self.fake_gh.write_text(
            """#!/usr/bin/env python3
import json, os, sys
if len(sys.argv) != 3 or sys.argv[1] != "api":
    raise SystemExit(9)
comment_id = int(sys.argv[2].rsplit("/", 1)[-1])
created = os.environ["TEST_APPROVAL_TIME"]
body = os.environ["TEST_APPROVAL_BODY"]
actor = os.environ.get("TEST_APPROVAL_ACTOR", "seigo-gace")
issue = os.environ.get("TEST_APPROVAL_ISSUE", "10")
print(json.dumps({
    "id": comment_id,
    "issue_url": f"https://api.github.com/repos/G-ACE-inc/server-core/issues/{issue}",
    "user": {"login": actor},
    "body": body,
    "created_at": created,
    "updated_at": os.environ.get("TEST_APPROVAL_UPDATED", created),
}))
""",
            encoding="utf-8",
        )
        self.fake_gh.chmod(0o755)

        self.contract = mod.load_contract(CONTRACT)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.env = os.environ.copy()
        self.env.update(
            {
                "GACE_SERVER_CORE_REPO": str(self.control),
                "GACE_SERVER_GITOPS_CONTRACT": str(CONTRACT),
                "GACE_SERVER_GITOPS_QUEUE_ROOT": str(self.queue),
                "GACE_SERVER_GITOPS_TARGET_SERVER_CORE": str(self.target),
                "GACE_SERVER_GITOPS_GH_BIN": str(self.fake_gh),
                "TEST_APPROVAL_TIME": now,
                "TEST_APPROVAL_BODY": f"[GACE-SERVER-APPROVE] action=deploy target=server-core sha={self.after}",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": f"url.file://{self.origin}.insteadOf",
                "GIT_CONFIG_VALUE_0": "https://github.com/G-ACE-inc/server-core.git",
            }
        )

    def tearDown(self):
        self.temp.cleanup()

    def enqueue(self, comment_id=123):
        return mod.enqueue(
            self.contract,
            action="deploy",
            target_id="server-core",
            branch="main",
            expected_head=self.after,
            sha=self.after,
            approval_comment_id=comment_id,
            env=self.env,
        )

    def run_runner(self):
        completed = subprocess.run(
            ["bash", str(RUNNER)],
            cwd=ROOT,
            env=self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def status(self, request_id):
        return mod.status(self.contract, request_id, env=self.env)

    def test_exact_sha_fast_forward_with_owner_approval_and_readback(self):
        queued = self.enqueue()
        self.run_runner()
        status = self.status(queued["id"])
        self.assertEqual(status["state"], "PASS")
        self.assertEqual(status["result"]["before_head"], self.before)
        self.assertEqual(status["result"]["after_head"], self.after)
        self.assertEqual(status["result"]["remote_head"], self.after)
        self.assertEqual(status["result"]["approval_comment_id"], 123)
        actual = subprocess.check_output(
            ["git", "-C", str(self.target), "rev-parse", "HEAD"], text=True
        ).strip()
        self.assertEqual(actual, self.after)
        self.assertTrue(
            (self.control / ".gace-control/server-gitops/approvals-used/comment_123.used").is_file()
        )

    def test_approval_comment_cannot_be_replayed(self):
        first = self.enqueue()
        self.run_runner()
        self.assertEqual(self.status(first["id"])["state"], "PASS")
        second = self.enqueue()
        self.run_runner()
        status = self.status(second["id"])
        self.assertEqual(status["state"], "FAIL")
        self.assertEqual(status["error"], "SERVER_GITOPS_APPROVAL_ALREADY_USED")

    def test_wrong_approval_body_fails_without_mutation(self):
        self.env["TEST_APPROVAL_BODY"] = (
            f"[GACE-SERVER-APPROVE] action=deploy target=server-core sha={'0' * 40}"
        )
        queued = self.enqueue(comment_id=124)
        self.run_runner()
        status = self.status(queued["id"])
        self.assertEqual(status["state"], "FAIL")
        self.assertEqual(status["error"], "SERVER_GITOPS_APPROVAL_BODY_MISMATCH")
        actual = subprocess.check_output(
            ["git", "-C", str(self.target), "rev-parse", "HEAD"], text=True
        ).strip()
        self.assertEqual(actual, self.before)

    def test_dirty_worktree_fails_before_approval(self):
        (self.target / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        queued = self.enqueue(comment_id=125)
        self.run_runner()
        status = self.status(queued["id"])
        self.assertEqual(status["state"], "FAIL")
        self.assertEqual(status["error"], "SERVER_GITOPS_WORKTREE_NOT_CLEAN")
        self.assertFalse(
            (self.control / ".gace-control/server-gitops/approvals-used/comment_125.used").exists()
        )

    def test_debugai_shared_target_is_disabled_and_existing_path_preserved(self):
        with self.assertRaisesRegex(mod.ServerGitOpsError, "SERVER_GITOPS_TARGET_NOT_ALLOWED"):
            mod.enqueue(
                self.contract,
                action="deploy",
                target_id="debug-ai",
                branch="main",
                expected_head=self.after,
                sha=self.after,
                approval_comment_id=126,
                env=self.env,
            )
        target = self.contract["targets"]["debug-ai"]
        self.assertFalse(target["enabled"])
        self.assertEqual(target["preservation"], "EXISTING_DEBUGAI_GITOPS_REMAINS_ACTIVE")

    def test_expired_request_fails_closed(self):
        request = mod.make_request(
            self.contract,
            action="deploy",
            target_id="server-core",
            branch="main",
            expected_head=self.after,
            sha=self.after,
            approval_comment_id=127,
            now_ms=1,
        )
        mod.atomic_json(self.queue / "requests" / f"{request['id']}.json", request)
        self.run_runner()
        status = self.status(request["id"])
        self.assertEqual(status["state"], "FAIL")
        self.assertEqual(status["error"], "REQUEST_EXPIRED")


if __name__ == "__main__":
    unittest.main()
