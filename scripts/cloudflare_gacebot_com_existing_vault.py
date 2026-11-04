#!/usr/bin/env python3
"""Read-only Cloudflare account/zone check via the existing Libral Vault.

Does not extract or copy the existing provider credential.
Does not change Cloudflare resources, account tokens or Vault records.
"""
import json
import os
from pathlib import Path
import re
import stat
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "operations/cloudflare-account.json"
DOMAIN = "g-acebot.com"
VAULT_AUTH = Path.home() / ".config/libral-vault/internal-token"
VAULT_ACTION = "http://127.0.0.1:8791/internal/v1/actions/http"
PROVIDER = "https://api.cloudflare.com/client/v4"


def vault_request(path):
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if (contract.get("secret_id") != "cf-account-api"
            or contract.get("consumer") != "g-ace-workspace"
            or contract.get("allowlist_origin") != "https://api.cloudflare.com"):
        raise RuntimeError("EXISTING_VAULT_CONTRACT_UNVERIFIED")
    st = VAULT_AUTH.lstat()
    if (not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077
            or not 24 <= st.st_size <= 4096):
        raise RuntimeError("VAULT_AUTH_FILE_UNSAFE")
    payload = {
        "secret_id": contract["secret_id"],
        "consumer": contract["consumer"],
        "url": PROVIDER + path,
        "method": "GET",
        "secret_header": "authorization",
        "secret_prefix": "Bearer ",
    }
    request = urllib.request.Request(
        VAULT_ACTION, data=json.dumps(payload).encode(), method="POST",
        headers={
            "Authorization": "Bearer " + VAULT_AUTH.read_text(encoding="utf-8").strip(),
            "Content-Type": "application/json",
        })
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.load(response)
    provider = data.get("provider") if isinstance(data, dict) else None
    if not isinstance(provider, dict) or provider.get("status") != 200:
        return None
    body = json.loads(provider.get("body", "{}"))
    return body if isinstance(body, dict) and body.get("success") is True else None


def check(account_id, request=vault_request):
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account_id):
        raise RuntimeError("ACCOUNT_ID_INVALID")
    account = request("/accounts/" + account_id + "/tokens/verify")
    if (isinstance(account, dict) and
            isinstance(account.get("result"), dict) and
            account["result"].get("status") == "active"):
        kind = "ACCOUNT"
    else:
        user = request("/user/tokens/verify")
        if (not isinstance(user, dict) or
                not isinstance(user.get("result"), dict) or
                user["result"].get("status") != "active"):
            raise RuntimeError("VAULT_TOKEN_NOT_VERIFIED")
        kind = "USER"
    query = urllib.parse.urlencode({"name": DOMAIN, "per_page": 5})
    data = request("/zones?" + query)
    zones = data.get("result") if isinstance(data, dict) else None
    if not isinstance(zones, list):
        raise RuntimeError("TARGET_ZONE_NOT_VISIBLE")
    matched = [z for z in zones if isinstance(z, dict) and z.get("name") == DOMAIN]
    if (len(matched) != 1 or matched[0].get("status") != "active"
            or (matched[0].get("account") or {}).get("id") != account_id):
        raise RuntimeError("TARGET_ZONE_OWNER_OR_STATUS_UNVERIFIED")
    return kind


def main():
    account_id = os.environ.get("GACE_CF_ACCOUNT_ID", "")
    result = check(account_id)
    print("EXISTING_VAULT_ACCOUNT_CLASS=" + result)
    print("GACEBOT_COM_ACCOUNT_ZONE_OWNER=PASS")
    print("GACEBOT_COM_REUSE_EXISTING_VAULT=PASS")
    print("CLOUDFLARE_MUTATIONS=NONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("GACEBOT_COM_REUSE_EXISTING_VAULT=NOT_VERIFIED")
        raise SystemExit(2)
