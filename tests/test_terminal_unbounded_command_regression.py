"""Regression for long arbitrary host commands without arbitrary character rejection."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import servercore_bounded_host_gateway_send as sender
import servercore_bounded_host_receiver as receiver

SHA = "a" * 40
CONTRACT = {"allowed_command_ids": ["host.command"], "request_schema": "test.host/v1"}

class CommandPayloadTests(unittest.TestCase):
    def test_long_utf8_command_survives_sender_and_receiver(self):
        command = "printf '%s' '" + ("日本語Ω-" * 850) + "'"
        self.assertGreater(len(command), 1600)
        req = sender.validate_cli(
            "host.command", SHA, CONTRACT, repository="G-ACE-inc/server-core",
            repo_sha=SHA, host_command=command)
        out = receiver.validate_request(req, CONTRACT)
        self.assertEqual(out["command"], command)
        self.assertEqual(out["repo_sha"], SHA)

    def test_nul_is_still_rejected(self):
        with self.assertRaises(sender.SendError):
            sender.validate_cli("host.command", SHA, CONTRACT,
                repository="G-ACE-inc/server-core", repo_sha=SHA,
                host_command="printf ok\x00")

if __name__ == "__main__":
    unittest.main()
