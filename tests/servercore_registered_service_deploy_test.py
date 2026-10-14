import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

root = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("service_deploy", root / "servercore_registered_service_deploy.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SHA="a"*40
A={"root":"/home/admin1/projects/debug-ai","compose_file":"compose.yaml",
   "compose_digest":"a"*64,"service":"debug-ai","source_sha":SHA}
def cmd(args,timeout=120):
    if args[-2:] == ["config","--services"]: return "debug-ai\nsandbox-runner"
    if args[-3:] == ["ps","--quiet","debug-ai"]: return "a"*64
    if args[-3:] == ["--detach","--no-deps","--build"]: return ""
    if args[-1] == "a"*64 and "com.docker.compose.service" in " ".join(args): return "debug-ai"
    if args[-1] == "a"*64 and "{{.State.Status}}" in args: return "running"
    if args[-1] == "a"*64 and ".State.Health" in " ".join(args): return "healthy"
    return ""


class DeployTests(unittest.TestCase):
    def test_dry_run_never_mutates(self):
        with patch.object(m,"inspect_host",return_value=A),patch.object(m,"command",side_effect=cmd) as run:
            result=m.deploy({},"seigo-gace/debug-ai",SHA,"debug-ai")
        self.assertEqual(result["state"],"SERVICE_DEPLOY_PREFLIGHT_PASS")
        self.assertEqual(run.call_count,1)
        self.assertNotIn("up",run.call_args.args[0])

    def test_unregistered_service_denied(self):
        with patch.object(m,"inspect_host",side_effect=m.AdmissionError("SERVICE_NOT_REGISTERED")), \
             patch.object(m,"command") as run:
            with self.assertRaises(m.AdmissionError):m.deploy({},"seigo-gace/debug-ai",SHA,"postgres",apply=True)
            run.assert_not_called()

    def test_compose_absent_service_denied(self):
        with patch.object(m,"inspect_host",return_value=A),patch.object(m,"command",return_value="other"):
            with self.assertRaisesRegex(m.AdmissionError,"COMPOSE_SERVICE_MISMATCH"):
                m.deploy({},"seigo-gace/debug-ai",SHA,"debug-ai",apply=True)

    def test_runtime_service_must_match(self):
        def wrong(args,timeout=120):
            x=cmd(args,timeout)
            return "other" if "com.docker.compose.service" in " ".join(args) else x
        with patch.object(m,"inspect_host",return_value=A),patch.object(m,"command",side_effect=wrong):
            with self.assertRaisesRegex(m.AdmissionError,"SERVICE_RUNTIME_MISMATCH"):
                m.deploy({},"seigo-gace/debug-ai",SHA,"debug-ai",apply=True)

    def test_runtime_success_evidence(self):
        with patch.object(m,"inspect_host",return_value=A),patch.object(m,"command",side_effect=cmd):
            out=m.deploy({},"seigo-gace/debug-ai",SHA,"debug-ai",apply=True)
        self.assertEqual(out["state"],"SERVICE_DEPLOY_RUNTIME_RUNNING")
        self.assertEqual(out["container_id"],"a"*64)

    def test_starting_health_becomes_healthy_without_false_deploy_failure(self):
        inspections = iter(["starting", "healthy"])
        def slow_health(args, timeout=120):
            if ".State.Health" in " ".join(args):
                return next(inspections)
            return cmd(args,timeout)
        with patch.object(m,"inspect_host",return_value=A), \
             patch.object(m,"command",side_effect=slow_health), \
             patch.object(m.time,"sleep") as asleep:
            result=m.deploy({},"seigo-gace/debug-ai",SHA,"debug-ai",apply=True)
        self.assertEqual(result["health"],"healthy")
        asleep.assert_called_once_with(2)

    def test_stuck_health_fails_after_bounded_wait(self):
        def starting(args,timeout=120):
            if ".State.Health" in " ".join(args):
                return "starting"
            return cmd(args,timeout)
        with patch.object(m,"inspect_host",return_value=A), \
             patch.object(m,"command",side_effect=starting), \
             patch.object(m.time,"monotonic",side_effect=[100,160]), \
             patch.object(m.time,"sleep") as asleep:
            with self.assertRaisesRegex(m.AdmissionError,"SERVICE_HEALTH_NOT_READY"):
                m.deploy({},"seigo-gace/debug-ai",SHA,"debug-ai",apply=True)
            asleep.assert_not_called()


if __name__=="__main__":unittest.main()
