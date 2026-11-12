import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location(
    "contabo_recover", SCRIPTS / "servercore_contabo_terminal_recover.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

OLD = "a" * 40
NEW = "b" * 40


class RecoverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / "server-core"
        (self.root / ".git").mkdir(parents=True)
        (self.root / "operations").mkdir()
        (self.root / "operations/github-project-bounded-host.json").write_text(
            json.dumps({"result_return": {"issue_number": 351}}))
        self.uid = self.root.stat().st_uid
        if self.uid == 0:
            self.skipTest("A non-root CI user is required by the real Host contract")
        self.commands = []
        self.head = OLD
        self.remote_head = NEW
        self.branch = "main"
        self.origin = "https://github.com/G-ACE-inc/server-core.git"
        self.dirty = False
        self.fail_reflect = False
        self.socket_patcher = patch.object(m.SOCKET.__class__, "is_socket", return_value=True)
        self.socket_patcher.start()
        self.addCleanup(self.socket_patcher.stop)
        uid_patcher = patch.object(m.os, "geteuid", return_value=self.uid)
        uid_patcher.start()
        self.addCleanup(uid_patcher.stop)

    def fake_command(self, *argv, **kwargs):
        self.commands.append(argv)
        if "remote" in argv and "get-url" in argv:
            return self.origin
        if "branch" in argv:
            return self.branch
        if "status" in argv:
            return " M scripts/other.py" if self.dirty else ""
        if "rev-parse" in argv:
            if "FETCH_HEAD" in argv:
                return self.remote_head
            return self.head
        if "fetch" in argv:
            return ""
        if "servercore_source_reflect.py" in argv:
            if self.fail_reflect:
                raise m.RecoveryError("COMMAND_FAILED")
            self.head = NEW
            return ""
        if "restart" in argv:
            return ""
        if "is-active" in argv:
            return "active"
        raise AssertionError(argv)

    def test_fast_forward_and_only_sink_restart(self):
        with patch.object(m, "command", side_effect=self.fake_command):
            out = m.recover(root=self.root)
        self.assertEqual(out["state"], "SOURCE_AND_SINK_ACTIVE")
        self.assertEqual((out["before_head"], out["after_head"], out["result_issue"]),
                         (OLD, NEW, 351))
        self.assertEqual(out["result_publication"], "NOT_VERIFIED")
        self.assertEqual(sum("servercore_source_reflect.py" in call for call in self.commands), 1)
        restarts = [call for call in self.commands if "restart" in call]
        self.assertEqual(restarts, [("systemctl", "--user", "restart",
                                     "gace-servercore-result-sink.service")])
        self.assertFalse(any("docker" in call for call in self.commands))

    def test_already_current_does_not_reflect(self):
        self.remote_head = OLD
        with patch.object(m, "command", side_effect=self.fake_command):
            out = m.recover(root=self.root)
        self.assertEqual(out["before_head"], out["after_head"])
        self.assertFalse(any("servercore_source_reflect.py" in call for call in self.commands))

    def test_dirty_checkout_denies_mutation(self):
        self.dirty = True
        with patch.object(m, "command", side_effect=self.fake_command):
            with self.assertRaisesRegex(m.RecoveryError, "TRACKED_WORKTREE_DIRTY"):
                m.recover(root=self.root)
        self.assertFalse(any("fetch" in call or "restart" in call for call in self.commands))

    def test_wrong_remote_denies_mutation(self):
        self.origin = "file:///tmp/other.git"
        with patch.object(m, "command", side_effect=self.fake_command):
            with self.assertRaisesRegex(m.RecoveryError, "REMOTE_ORIGIN_DENIED"):
                m.recover(root=self.root)
        self.assertFalse(any("fetch" in call or "restart" in call for call in self.commands))

    def test_source_reflect_failure_never_restarts(self):
        self.fail_reflect = True
        with patch.object(m, "command", side_effect=self.fake_command):
            with self.assertRaisesRegex(m.RecoveryError, "COMMAND_FAILED"):
                m.recover(root=self.root)
        self.assertFalse(any("restart" in call for call in self.commands))

    def test_cannot_represent_sink_active_as_publication(self):
        self.remote_head = OLD
        with patch.object(m, "command", side_effect=self.fake_command):
            result = m.recover(root=self.root)
        self.assertNotEqual(result["result_publication"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
