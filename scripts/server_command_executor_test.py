#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "server_command_request.py"
RUNNER = ROOT / "scripts" / "host-server-command-runner.sh"
CONTRACT = ROOT / "operations" / "server-command.json"

spec = importlib.util.spec_from_file_location("server_command_request", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SharedServerCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.queue = self.root / "queue"
        self.target = self.root / "target"
        self.target.mkdir()
        subprocess.run(["git", "init", "-q", str(self.target)], check=True)
        subprocess.run(["git", "-C", str(self.target), "config", "user.email", "ci@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.target), "config", "user.name", "GACE CI"], check=True)
        (self.target / "proof.txt").write_text("proof\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.target), "add", "proof.txt"], check=True)
        subprocess.run(["git", "-C", str(self.target), "commit", "-qm", "proof"], check=True)
        self.head = subprocess.check_output(
            ["git", "-C", str(self.target), "rev-parse", "HEAD"], text=True
        ).strip()
        self.contract = mod.load_contract(CONTRACT)
        self.env = os.environ.copy()
        self.env.update(
            {
                "GACE_SERVER_CORE_REPO": str(ROOT),
                "GACE_SERVER_COMMAND_CONTRACT": str(CONTRACT),
                "GACE_SERVER_COMMAND_QUEUE_ROOT": str(self.queue),
                "GACE_SERVER_COMMAND_TARGET_SERVER_CORE": str(self.target),
            }
        )

    def tearDown(self):
        self.temp.cleanup()

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

    def test_pwd_request_runs_through_host_queue_and_readback(self):
        queued = mod.enqueue(
            self.contract,
            "workspace.pwd",
            "server-core",
            env=self.env,
        )
        self.assertEqual(queued["state"], "QUEUED")
        self.run_runner()
        status = mod.status(self.contract, queued["id"], env=self.env)
        self.assertEqual(status["state"], "PASS")
        self.assertTrue(status["result"]["read_only"])
        self.assertEqual(status["result"]["command_id"], "workspace.pwd")
        self.assertEqual(status["result"]["target_id"], "server-core")
        self.assertEqual(status["result"]["stdout"], str(self.target.resolve()))

    def test_git_head_request_returns_exact_head(self):
        queued = mod.enqueue(
            self.contract,
            "workspace.git_head",
            "server-core",
            env=self.env,
        )
        self.run_runner()
        status = mod.status(self.contract, queued["id"], env=self.env)
        self.assertEqual(status["state"], "PASS")
        self.assertEqual(status["result"]["stdout"], self.head)

    def test_unknown_command_fails_before_queue_write(self):
        with self.assertRaisesRegex(mod.ServerCommandError, "SERVER_COMMAND_NOT_ALLOWED"):
            mod.enqueue(
                self.contract,
                "shell.exec",
                "server-core",
                env=self.env,
            )
        requests = self.queue / "requests"
        self.assertFalse(requests.exists())

    def test_unknown_target_fails_before_queue_write(self):
        with self.assertRaisesRegex(mod.ServerCommandError, "SERVER_COMMAND_TARGET_NOT_ALLOWED"):
            mod.enqueue(
                self.contract,
                "workspace.pwd",
                "arbitrary-path",
                env=self.env,
            )

    def test_expired_request_fails_closed(self):
        request = mod.make_request(
            self.contract,
            "workspace.pwd",
            "server-core",
            now_ms=1,
        )
        mod.atomic_json(self.queue / "requests" / f"{request['id']}.json", request)
        self.run_runner()
        status = mod.status(self.contract, request["id"], env=self.env)
        self.assertEqual(status["state"], "FAIL")
        self.assertEqual(status["error"], "REQUEST_EXPIRED")

    def test_contract_keeps_mutating_surfaces_disabled(self):
        bounds = self.contract["boundaries"]
        self.assertFalse(bounds["arbitrary_shell"])
        self.assertFalse(bounds["arbitrary_path"])
        self.assertFalse(bounds["arbitrary_environment"])
        self.assertFalse(bounds["persistent_mutation"])
        self.assertTrue(bounds["single_writer_host_runner"])
        self.assertTrue(bounds["expired_request_fail_closed"])


if __name__ == "__main__":
    unittest.main()
