#!/usr/bin/env python3
"""One-time, interactive Cloudflare g-acebot.jp credential enrollment.

No CLI/argv token, no local token file, no credential in stdout or Git.
Cloudflare MCP remains a separate OAuth integration.
"""
import base64
import getpass
import json
import pathlib
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request

DOMAIN = "g-acebot.jp"
SECRET_ID = "cf-gacebot-jp-api"
CONSUMER = "g-ace-workspace"
API_ROOT = "https://api.cloudflare.com/client/v4"
VAULT_URL = "http://127.0.0.1:8791/internal/v1/secrets"
VAULT_ADMIN_FILE = pathlib.Path.home() / ".config/libral-vault/internal-token"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect())


def read_json(req):
    with OPENER.open(req, timeout=12) as res:
        return json.load(res)


def cf_get(path, token):
    req = urllib.request.Request(API_ROOT + path, method="GET", headers={
        "Authorization": "Bearer " + token, "Accept": "application/json",
    })
    body = read_json(req)
    if not isinstance(body, dict) or body.get("success") is not True:
        raise RuntimeError("CLOUDFLARE_API_REJECTED")
    return body


def vault_admin():
    st = VAULT_ADMIN_FILE.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077 or not 24 <= st.st_size <= 4096:
        raise RuntimeError("VAULT_ADMIN_CREDENTIAL_UNSAFE")
    return VAULT_ADMIN_FILE.read_text(encoding="utf-8").strip()


def main():
    if len(sys.argv) > 1:
        raise RuntimeError("NO_CLI_TOKEN_ARGS_ALLOWED")
    if not sys.stdin.isatty():
        raise RuntimeError("INTERACTIVE_TERMINAL_REQUIRED")
    print("TARGET_ZONE=" + DOMAIN)
    print("VAULT_SECRET_ID=" + SECRET_ID)
    print("MCP_AUTHENTICATION=SEPARATE_OAUTH")
    token = getpass.getpass("Cloudflare API token (hidden): ")
    if not 32 <= len(token) <= 512 or not token.isascii() or any(c.isspace() for c in token):
        raise RuntimeError("TOKEN_FORMAT_INVALID")
    result = cf_get("/user/tokens/verify", token).get("result")
    if not isinstance(result, dict) or result.get("status") != "active":
        raise RuntimeError("TOKEN_NOT_ACTIVE")
    print("CLOUDFLARE_TOKEN=ACTIVE")
    query = urllib.parse.urlencode({"name": DOMAIN, "per_page": "5"})
    rows = cf_get("/zones?" + query, token).get("result")
    if not isinstance(rows, list):
        raise RuntimeError("ZONE_RESPONSE_INVALID")
    matches = [z for z in rows if isinstance(z, dict) and z.get("name") == DOMAIN]
    if len(matches) != 1:
        raise RuntimeError("TARGET_ZONE_NOT_ACCESSIBLE_NO_SECRET_STORED")
    if matches[0].get("status") != "active":
        raise RuntimeError("ZONE_NOT_ACTIVE_NO_SECRET_STORED")
    if not isinstance(matches[0].get("account"), dict) or not matches[0]["account"].get("id"):
        raise RuntimeError("ZONE_ACCOUNT_UNKNOWN_NO_SECRET_STORED")
    print("CLOUDFLARE_TARGET_ZONE=ACTIVE_AND_VISIBLE")
    payload = {
        "id": SECRET_ID,
        "allowed_consumers": [CONSUMER],
        "value_base64": base64.b64encode(token.encode()).decode(),
    }
    req = urllib.request.Request(VAULT_URL, data=json.dumps(payload).encode(),
        method="POST", headers={
            "Authorization": "Bearer " + vault_admin(),
            "Content-Type": "application/json",
        })
    result = read_json(req)
    ref = result.get("secret") if isinstance(result, dict) else None
    if not isinstance(ref, dict) or ref.get("id") != SECRET_ID:
        raise RuntimeError("VAULT_READBACK_NOT_VERIFIED")
    print("VAULT_STORAGE=PASS")
    print("CLOUDFLARE_GACEBOT_JP_BOOTSTRAP=PASS")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        print("BOOTSTRAP=FAIL_HTTP_" + str(exc.code))
        raise SystemExit(2)
    except (OSError, ValueError, RuntimeError) as exc:
        allowed = {
            "NO_CLI_TOKEN_ARGS_ALLOWED", "INTERACTIVE_TERMINAL_REQUIRED",
            "TOKEN_FORMAT_INVALID", "CLOUDFLARE_API_REJECTED",
            "TOKEN_NOT_ACTIVE", "ZONE_RESPONSE_INVALID",
            "TARGET_ZONE_NOT_ACCESSIBLE_NO_SECRET_STORED",
            "ZONE_NOT_ACTIVE_NO_SECRET_STORED",
            "ZONE_ACCOUNT_UNKNOWN_NO_SECRET_STORED",
            "VAULT_ADMIN_CREDENTIAL_UNSAFE", "VAULT_READBACK_NOT_VERIFIED",
        }
        code = str(exc) if str(exc) in allowed else "AUTH_OR_TRANSPORT_NOT_VERIFIED"
        print("BOOTSTRAP=FAIL_" + code)
        raise SystemExit(2)
