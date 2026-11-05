import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import servercore_bounded_host_gateway_send as sender
import servercore_gserver_target as target

CONTRACT = json.loads((ROOT / "operations/github-project-bounded-host.json").read_text())
SHA = "a" * 40
COMMAND = "git -C /home/gace/Project/Gserver/repository status --short"


def request():
    return sender.validate_cli(
        "host.command", SHA, CONTRACT, repository=target.REPOSITORY,
        repo_sha=SHA, host_command=COMMAND, host_target=target.TARGET_ID)


class GserverTargetTests(unittest.TestCase):
    def test_target_is_common_host_command_without_fixed_terminal(self):
        config = target.target_config(CONTRACT)
        self.assertEqual(config["common_command_id"], "host.command")
        self.assertFalse(config["fixed_command_terminal"])
        self.assertEqual(config["status"], "HOST_ADMITTED")

    def test_request_and_event_bind_target_repository_and_digest(self):
        value = request()
        self.assertEqual(target.event_destination(value, CONTRACT), "gserver-bounded-host")
        event = sender.build_event(value, CONTRACT)
        self.assertEqual(event["destinationId"], "gserver-bounded-host")
        self.assertEqual(event["data"]["host_target"], "gserver")
        self.assertEqual(value["command_sha256"], hashlib.sha256(COMMAND.encode()).hexdigest())

    def test_wrong_target_or_repository_is_rejected(self):
        with self.assertRaisesRegex(sender.SendError, "HOST_TARGET_NOT_REGISTERED"):
            sender.validate_cli("host.command", SHA, CONTRACT, repository=target.REPOSITORY,
                                repo_sha=SHA, host_command=COMMAND, host_target="contabo")
        value = request()
        value["repository"] = "seigo-gace/other"
        with self.assertRaisesRegex(target.GserverTargetError, "GSERVER_TARGET_MISMATCH"):
            target.validate_request(value, CONTRACT)

    def test_command_integrity_and_result_correlation(self):
        value = request()
        bad = dict(value, command_sha256="b" * 64)
        with self.assertRaisesRegex(target.GserverTargetError, "GSERVER_COMMAND_TRANSPORT_CHANGED"):
            target.validate_request(bad, CONTRACT)
        result = {
            "request_id": value["id"], "host_target": "gserver", "repository": target.REPOSITORY,
            "repo_sha": value["repo_sha"], "host_sha": value["repo_sha"], "state": "PASS", "exit_code": 0,
            "dispatcher_sha": value["expected_sha"], "command_sha256": value["command_sha256"],
            "stdout": "ok", "stderr": "",
            "stdout_sha256": hashlib.sha256(b"ok").hexdigest(),
            "stderr_sha256": hashlib.sha256(b"").hexdigest(),
        }
        self.assertIs(target.validate_result(result, value), result)
        for key, changed in {
            "request_id": "req_" + "0" * 24, "host_target": "contabo",
            "repository": "other/repo", "repo_sha": "f" * 40,
            "host_sha": "f" * 40, "dispatcher_sha": "f" * 40,
            "command_sha256": "f" * 64, "exit_code": 1,
            "stdout": "tampered", "stderr": "tampered",
        }.items():
            with self.subTest(key=key), self.assertRaises(target.GserverTargetError):
                target.validate_result(dict(result, **{key: changed}), value)

    def test_target_contract_does_not_contain_secrets_or_fixed_commands(self):
        config = target.target_config(CONTRACT)
        serialized = json.dumps(config, sort_keys=True)
        self.assertNotIn("token", serialized.lower())
        self.assertNotIn('"secret":', serialized.lower())
        self.assertNotIn('"token":', serialized.lower())
        self.assertNotIn("allowed_commands", serialized.lower())


if __name__ == "__main__":
    unittest.main()
