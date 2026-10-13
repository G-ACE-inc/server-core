import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "scripts/servercore_registered_docker_ops.py"
spec = importlib.util.spec_from_file_location("dockerops", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ENTRY = {"server_project_path": "/home/admin1/projects/example",
         "runtime_target": {"compose_file": "docker-compose.yml", "service": "api"}}

class DockerOperationsTests(unittest.TestCase):
    def test_registered_status(self):
        seen = []
        def run(command, **kwargs):
            seen.append((command, kwargs))
            return type("Completed", (), {"returncode": 0, "stdout": "running", "stderr": ""})()
        out = module.operate(ENTRY, "api", "ps", runner=run)
        self.assertEqual(out["stdout"], "running")
        self.assertEqual(seen[0][0][-2:], ["ps", "api"])
        self.assertFalse(seen[0][1]["check"])
        self.assertNotIn("shell", seen[0][1])

    def test_registered_exec(self):
        def run(cmd, **kw):
            self.assertEqual(cmd[-3:], ["python3", "-V", "--version"])
            return type("Completed", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()
        module.operate(ENTRY, "api", "exec", argv=["python3", "-V", "--version"], runner=run)

    def test_banned_target(self):
        with self.assertRaisesRegex(module.DockerOperationError, "SERVICE_NOT_REGISTERED"):
            module.operate(ENTRY, "db", "restart", runner=lambda *a, **kw: None)

    def test_banned_operation(self):
        with self.assertRaisesRegex(module.DockerOperationError, "OPERATION_DENIED"):
            module.operate(ENTRY, "api", "down")

    def test_no_shell_injection(self):
        with self.assertRaisesRegex(module.DockerOperationError, "EXEC_ARGV_INVALID"):
            module.operate(ENTRY, "api", "exec", argv=["sh", "-c", "echo hi\nrm -rf /"])

    def test_bad_compose_scope(self):
        broken = {"server_project_path": "/tmp/project", "runtime_target": ENTRY["runtime_target"]}
        with self.assertRaises(module.DockerOperationError):
            module.operate(broken, "api", "ps")

    def test_exec_args_are_separate(self):
        def run(cmd, **kw):
            self.assertEqual(cmd[-3:], ["sh", "-c", "echo harmless"])
            return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        module.operate(ENTRY, "api", "exec", argv=["sh", "-c", "echo harmless"], runner=run)

if __name__ == "__main__":
    unittest.main()
