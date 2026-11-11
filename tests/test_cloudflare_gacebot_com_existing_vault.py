"""Offline contract checks: existing Cloudflare token stays inside Vault."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "scripts/cloudflare_gacebot_com_existing_vault.py"
spec = importlib.util.spec_from_file_location("cf_existing_vault", FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ACCOUNT = "a" * 32


def zone(owner=ACCOUNT):
    return {"result": [{
        "name": "g-acebot.com", "status": "active",
        "account": {"id": owner}
    }]}


class ExistingVaultContract(unittest.TestCase):
    def test_account_token_and_matching_zone_pass(self):
        calls = []
        def getter(path):
            calls.append(path)
            if "/tokens/verify" in path:
                return {"result": {"status": "active"}}
            return zone()
        self.assertEqual(module.check(ACCOUNT, getter), "ACCOUNT")
        self.assertEqual(len(calls), 2)

    def test_user_token_fallback_and_matching_zone_pass(self):
        def getter(path):
            if "/accounts/" in path:
                return None
            if "/user/tokens/verify" in path:
                return {"result": {"status": "active"}}
            return zone()
        self.assertEqual(module.check(ACCOUNT, getter), "USER")

    def test_other_account_rejected(self):
        def getter(path):
            return {"result": {"status": "active"}} if "/tokens/verify" in path else zone("b" * 32)
        with self.assertRaisesRegex(RuntimeError, "TARGET_ZONE_OWNER_OR_STATUS_UNVERIFIED"):
            module.check(ACCOUNT, getter)

    def test_existing_token_not_valid_rejected(self):
        def getter(path):
            return None
        with self.assertRaisesRegex(RuntimeError, "VAULT_TOKEN_NOT_VERIFIED"):
            module.check(ACCOUNT, getter)

    def test_invalid_account_id_never_calls_provider(self):
        def reject(path):
            raise AssertionError("No request allowed")
        with self.assertRaisesRegex(RuntimeError, "ACCOUNT_ID_INVALID"):
            module.check("bad", reject)


if __name__ == "__main__":
    unittest.main()
