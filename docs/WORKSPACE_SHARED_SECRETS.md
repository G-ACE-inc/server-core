# WORKSPACE SHARED SECRETS

この Workspace（server-core + projects）で Hugging Face と Cloudflare Account API を使うときの正本。Token は配らない。Libral Vault の既存 API だけを使う。

機械可読契約:
- Hugging Face: `operations/huggingface.json`
- Cloudflare Account API: `operations/cloudflare-account.json`
- Tunnel は別: `operations/cloudflare.json` と `docs/CLOUDFLARE_OPERATIONS.md`

`PROTOCOL` / `CORE` / `KB` / `PROJECT_STATUS` はこの文書では変更しない。

## 使うとき
AI または作業者が Hugging Face Hub / Inference、または Cloudflare Account API（`https://api.cloudflare.com`）を呼ぶとき。各 Project に helper を足さない。Cursor MCP の OAuth とは別経路。

## 共通契約
- Vault: `http://127.0.0.1:8791`
- 内部認証: `Authorization: Bearer`。値は `/home/admin1/.config/libral-vault/internal-token` から読む。文書と Chat に書かない
- consumer: `g-ace-workspace`
- 利用: `POST /internal/v1/actions/http`
- 投入: `POST /internal/v1/secrets`
- Header: `authorization` + 接頭辞 `Bearer `
- 平文 Secret File は作らない。GPG-Core は使わない

| 対象 | secret_id | allowlist origin | 識別URL |
|---|---|---|---|
| Hugging Face | `hf-token` | `https://huggingface.co` | `https://huggingface.co/api/whoami-v2` |
| Cloudflare Account API | `cf-account-api` | `https://api.cloudflare.com` | `/client/v4/user` と `/client/v4/accounts` |

Cloudflare `tokens/verify` は権限不足で 401 になり得る。どの token かの確認は `/user` と `/accounts` を正とする。

## 利用（Token を読まない）
`POST http://127.0.0.1:8791/internal/v1/actions/http`

```json
{
  "secret_id": "hf-token または cf-account-api",
  "consumer": "g-ace-workspace",
  "url": "allowlist origin 配下の URL",
  "method": "GET",
  "secret_header": "authorization",
  "secret_prefix": "Bearer "
}
```

Vault が Provider へ Header を注入する。応答に Token は出ない。

## 投入（既存 API のみ。スクリプト追加禁止）
環境変数に Token を入れてから実行する。Chat に Token を貼らない。

Hugging Face: `HF_TOKEN`
Cloudflare Account API: `CLOUDFLARE_API_TOKEN`

```bash
python3 - <<'PY'
import base64, json, os, pathlib, urllib.request
token = os.environ["CLOUDFLARE_API_TOKEN"].strip()  # HF なら HF_TOKEN
auth = pathlib.Path("/home/admin1/.config/libral-vault/internal-token").read_text().strip()
body = json.dumps({
    "id": "cf-account-api",  # HF なら hf-token
    "value_base64": base64.b64encode(token.encode("utf-8")).decode("ascii"),
    "allowed_consumers": ["g-ace-workspace"],
}).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8791/internal/v1/secrets",
    data=body, method="POST",
    headers={"Authorization": f"Bearer {auth}", "Content-Type": "application/json", "Accept": "application/json"},
)
with urllib.request.urlopen(req) as res:
    print(res.status)
    print(res.read().decode("utf-8"))
PY
```

成功は HTTP 201。入れ直しは先に `DELETE /internal/v1/secrets/<id>`（body `{"consumer":"g-ace-workspace"}`）。

## どの Token か確認する
Vault は Token 文字列を返さない。入っている Token の身元は Provider の識別 API で見る。出す項目は `id` / `name` / `status` / `email` のみ。Token 文字列は出さない。

```bash
python3 - <<'PY'
import json, pathlib, urllib.request
auth = pathlib.Path("/home/admin1/.config/libral-vault/internal-token").read_text().strip()

def vault_get(url):
    body = json.dumps({
        "secret_id": "cf-account-api",
        "consumer": "g-ace-workspace",
        "url": url,
        "method": "GET",
        "secret_header": "authorization",
        "secret_prefix": "Bearer ",
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8791/internal/v1/actions/http",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {auth}", "Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8")).get("provider") or {}

def ident(provider):
    raw = provider.get("body") or ""
    payload = json.loads(raw)
    data = payload.get("result")
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        data = {}
    return {
        "http": provider.get("status"),
        "ok": payload.get("success"),
        "id": data.get("id"),
        "name": data.get("name"),
        "status": data.get("status"),
        "email": data.get("email"),
    }

print("user", ident(vault_get("https://api.cloudflare.com/client/v4/user")))
print("account", ident(vault_get("https://api.cloudflare.com/client/v4/accounts?per_page=1")))
PY
```

Hugging Face は `secret_id` を `hf-token`、URL を `https://huggingface.co/api/whoami-v2` にする。

## 失敗
- `SECRET_NOT_FOUND`: 未投入、または `secret_id` 違い
- `ACCESS_DENIED`: `allowed_consumers` に `g-ace-workspace` が無い
- `HTTP_ORIGIN_NOT_ALLOWED`: Vault の `LIBRAL_VAULT_HTTP_ALLOWLIST` に origin が無い
- Cloudflare 401: Token 無効、またはその endpoint の権限不足。`/user` と `/accounts` で切り分ける
- Hugging Face 401: Token 無効

## 禁止
- 各 Project への Token helper 追加
- 投入用スクリプト追加
- GPG-Core でこの共有 Secret を扱うこと
- Token を Chat / Log / Git / 常駐 Container に出す・渡すこと
- Tunnel Token（`operations/cloudflare.json`）と Account API を混ぜること
- Vault から平文 Token を dump すること
