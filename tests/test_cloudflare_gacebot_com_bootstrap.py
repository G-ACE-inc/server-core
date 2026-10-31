"""Offline, no-network checks of the dedicated Cloudflare account-token flow."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / "scripts/cloudflare_gacebot_com_bootstrap.py"
spec = importlib.util.spec_from_file_location("cf_com_enroll", FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AccountEnrollment(unittest.TestCase):
    def test_reject_noninteractive(self):
        with patch.dict(os.environ, {"GACE_CF_ACCOUNT_ID": "a" * 32}), patch.object(sys, "argv", [str(FILE)]), patch.object(sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "INTERACTIVE_TERMINAL_REQUIRED"):
                module.main()

    def test_account_only_before_vault_write(self):
        calls = []
        zone = {"name": "g-acebot.com", "status": "active", "account": {"id": "a" * 32}}
        def fake_cloudflare(path, value):
            calls.append(path)
            self.assertEqual(value, "X" * 48)
            if path == "/accounts/" + "a" * 32 + "/tokens/verify":
                return {"result": {"status": "active"}}
            if path.startswith("/zones?"):
                return {"result": [zone]}
            raise AssertionError("Unexpected endpoint")
        def fake_vault(req):
            self.assertEqual(req.get_method(), "POST")
            return {"secret": {"id": module.SECRET_ID}}
        with patch.dict(os.environ, {"GACE_CF_ACCOUNT_ID": "a" * 32}), patch.object(sys, "argv", [str(FILE)]), patch.object(sys.stdin, "isatty", return_value=True), patch.object(module.getpass, "getpass", return_value="X" * 48), patch.object(module, "cf_get", side_effect=fake_cloudflare), patch.object(module, "vault_admin", return_value="Y" * 48), patch.object(module, "read_json", side_effect=fake_vault), contextlib.redirect_stdout(io.StringIO()) as out:
            module.main()
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], "/accounts/" + "a" * 32 + "/tokens/verify")
        self.assertIn("CLOUDFLARE_GACEBOT_COM_BOOTSTRAP=PASS", out.getvalue())

    def test_missing_zone_never_writes_vault(self):
        def fake_cf(path, value):
            return {"result": {"status": "active"}} if "/tokens/verify" in path else {"result": []}
        with patch.dict(os.environ, {"GACE_CF_ACCOUNT_ID": "a" * 32}), patch.object(sys, "argv", [str(FILE)]), patch.object(sys.stdin, "isatty", return_value=True), patch.object(module.getpass, "getpass", return_value="X" * 48), patch.object(module, "cf_get", side_effect=fake_cf), patch.object(module, "read_json") as vault:
            with self.assertRaisesRegex(RuntimeError, "TARGET_ZONE_NOT_ACCESSIBLE"):
                module.main()
            vault.assert_not_called()


    def test_zone_in_different_account_never_writes_vault(self):
        zone = {"name": "g-acebot.com", "status": "active", "account": {"id": "b" * 32}}
        def fake_cf(path, value):
            return {"result": {"status": "active"}} if "/tokens/verify" in path else {"result": [zone]}
        with patch.dict(os.environ, {"GACE_CF_ACCOUNT_ID": "a" * 32}), patch.object(sys, "argv", [str(FILE)]), patch.object(sys.stdin, "isatty", return_value=True), patch.object(module.getpass, "getpass", return_value="X" * 48), patch.object(module, "cf_get", side_effect=fake_cf), patch.object(module, "read_json") as vault:
            with self.assertRaisesRegex(RuntimeError, "ACCOUNT_ZONE_MISMATCH"):
                module.main()
            vault.assert_not_called()

    def test_no_expected_account_id_never_reads_credentials(self):
        with patch.dict(os.environ, {"GACE_CF_ACCOUNT_ID": ""}), patch.object(sys, "argv", [str(FILE)]), patch.object(sys.stdin, "isatty", return_value=True), patch.object(module.getpass, "getpass") as secret_input:
            with self.assertRaisesRegex(RuntimeError, "ACCOUNT_ID_REQUIRED"):
                module.main()
            secret_input.assert_not_called()


if __name__ == "__main__":
    unittest.main()
