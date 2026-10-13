import importlib.util
from pathlib import Path
import subprocess
import unittest

path = Path(__file__).resolve().parents[1] / "scripts/servercore_registered_docker_ops.py"
spec = importlib.util.spec_from_file_location("dockerops", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ENTRY = {"server_project_path": "/home/admin1/projects/example",
         "runtime_target": {"compose_file": "compose.yaml", "services": ["api", "worker"]}}

def completed(stdout="ok\n", stderr="", returncode=0):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)

class DockerOperationsTests(unittest.TestCase):
    def test_registered_status(self):
        seen = []
        def run(cmd, **kw):
            seen.append((cmd, kw))
            return completed("running\n")
        value = module.operate(ENTRY, "api", "ps", runner=run)
        self.assertEqual(value["stdout"], "running\n")
        self.assertEqual(seen[0][0][-2:], ["ps", "api"])
        self.assertEqual(seen[0][1]["cwd"], "/home/admin1/projects/example")
        self.assertNotIn("shell", seen[0][1])

    def test_registered_exec_runs_inside_compose_service(self):
        def run(cmd, **kw):
            self.assertEqual(cmd[-5:], ["-T", "api", "python3", "-c", "print(1)"])
            return completed("1\n")
        result = module.operate(ENTRY, "api", "exec",
                                argv=["python3", "-c", "print(1)"], runner=run)
        self.assertEqual(result["stdout"], "1\n")

    def test_registered_restart(self):
        def run(cmd, **kw):
            self.assertEqual(cmd[-2:], ["restart", "api"])
            return completed()
        self.assertEqual(module.operate(ENTRY, "api", "restart", runner=run)["exit_code"], 0)

    def test_stats_uses_exact_registered_container_id(self):
        calls = []
        def run(cmd, **kw):
            calls.append(cmd)
            return completed("a" * 64 + "\n" if len(calls) == 1 else "api|0.1%|12MiB\n")
        out = module.operate(ENTRY, "api", "stats", runner=run)
        self.assertEqual(out["stdout"], "api|0.1%|12MiB\n")
        self.assertEqual(calls[0][-3:], ["ps", "--quiet", "api"])
        self.assertEqual(calls[1][-1], "a" * 64)

    def test_stats_rejects_ambiguous_ids(self):
        with self.assertRaisesRegex(module.DockerOperationError, "SERVICE_CONTAINER_ID_INVALID"):
            module.operate(ENTRY, "api", "stats",
                           runner=lambda *a, **kw: completed("a" * 64 + "\n" + "b" * 64))

    def test_unregistered_service_denied(self):
        with self.assertRaisesRegex(module.DockerOperationError, "SERVICE_NOT_REGISTERED"):
            module.operate(ENTRY, "database", "restart", runner=lambda *a, **kw: None)

    def test_unregistered_operation_denied(self):
        with self.assertRaisesRegex(module.DockerOperationError, "OPERATION_DENIED"):
            module.operate(ENTRY, "api", "down")

    def test_host_project_escape_denied(self):
        altered = {"server_project_path": "/tmp/example", "runtime_target": ENTRY["runtime_target"]}
        with self.assertRaisesRegex(module.DockerOperationError, "ROOT_NOT_REGISTERED"):
            module.operate(altered, "api", "ps")

    def test_compose_traversal_denied(self):
        altered = {"server_project_path": ENTRY["server_project_path"],
                   "runtime_target": {"compose_file": "../compose.yml", "services": ["api"]}}
        with self.assertRaisesRegex(module.DockerOperationError, "COMPOSE_NOT_REGISTERED"):
            module.operate(altered, "api", "ps")

    def test_output_cap(self):
        result = module.operate(ENTRY, "api", "logs", runner=lambda *a, **k: completed("x"*6000))
        self.assertEqual(len(result["stdout"]), 6000)
        self.assertFalse(result["stdout_truncated"])

    def test_log_tail_over_cap_keeps_latest_lines_and_marks_truncation(self):
        data = "prefix:" + "x" * 16000 + ":LATEST"
        result = module.operate(ENTRY, "api", "logs", runner=lambda *a, **k: completed(data))
        self.assertEqual(len(result["stdout"]), 16000)
        self.assertTrue(result["stdout"].endswith(":LATEST"))
        self.assertTrue(result["stdout_truncated"])
        self.assertFalse(result["stderr_truncated"])

    def test_untrusted_exec_argv_rejected(self):
        with self.assertRaisesRegex(module.DockerOperationError, "EXEC_ARGV_INVALID"):
            module.operate(ENTRY, "api", "exec", argv=["sh", "-c", "echo hi\nrm -rf /"])

    def test_exec_argument_only_for_exec(self):
        with self.assertRaisesRegex(module.DockerOperationError, "EXEC_ARGV_REQUIRED_OR_UNEXPECTED"):
            module.operate(ENTRY, "api", "ps", argv=["true"])

    def test_subprocess_failure_redacted(self):
        with self.assertRaisesRegex(module.DockerOperationError, "DOCKER_OPERATION_FAILED"):
            module.operate(ENTRY, "api", "restart", runner=lambda *a, **k: completed("private",returncode=1))

    def test_subprocess_timeout(self):
        def timeout(*a, **kw):
            raise subprocess.TimeoutExpired("docker", 1)
        with self.assertRaisesRegex(module.DockerOperationError, "DOCKER_EXECUTION_UNAVAILABLE"):
            module.operate(ENTRY, "api", "ps", runner=timeout)

if __name__ == "__main__":
    unittest.main()
