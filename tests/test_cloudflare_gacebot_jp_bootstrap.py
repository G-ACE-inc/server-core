"""Offline, no-network checks of the dedicated Cloudflare account-token flow."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / "scripts/cloudflare_gacebot_jp_bootstrap.py"
spec = importlib.util.spec_from_file_location("cf_jp_enroll", FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AccountEnrollment(unittest.TestCase):
    def test_reject_noninteractive(self):
        with patch.object(sys, "argv", [str(FILE)]), patch.object(sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "INTERACTIVE_TERMINAL_REQUIRED"):
                module.main()

    def test_account_only_before_vault_write(self):
        calls = []
        zone = {"name": "g-acebot.jp", "status": "active", "account": {"id": "a" * 32}}
        def fake_cloudflare(path, value):
            calls.append(path)
            self.assertEqual(value, "X" * 48)
            if path.startswith("/zones?"):
                return {"result": [zone]}
            if path == "/accounts/" + "a" * 32 + "/tokens/verify":
                return {"result": {"status": "active"}}
            raise AssertionError("Unexpected endpoint")
        def fake_vault(req):
            self.assertEqual(req.get_method(), "POST")
            return {"secret": {"id": module.SECRET_ID}}
        with patch.object(sys, "argv", [str(FILE)]), patch.object(sys.stdin, "isatty", return_value=True), patch.object(module.getpass, "getpass", return_value="X" * 48), patch.object(module, "cf_get", side_effect=fake_cloudflare), patch.object(module, "vault_admin", return_value="Y" * 48), patch.object(module, "read_json", side_effect=fake_vault), contextlib.redirect_stdout(io.StringIO()) as out:
            module.main()
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1], "/accounts/" + "a" * 32 + "/tokens/verify")
        self.assertIn("CLOUDFLARE_GACEBOT_JP_BOOTSTRAP=PASS", out.getvalue())

    def test_missing_zone_never_writes_vault(self):
        with patch.object(sys, "argv", [str(FILE)]), patch.object(sys.stdin, "isatty", return_value=True), patch.object(module.getpass, "getpass", return_value="X" * 48), patch.object(module, "cf_get", return_value={"result": []}), patch.object(module, "read_json") as vault:
            with self.assertRaisesRegex(RuntimeError, "TARGET_ZONE_NOT_ACCESSIBLE"):
                module.main()
            vault.assert_not_called()


if __name__ == "__main__":
    unittest.main()
