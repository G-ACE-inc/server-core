# WORKSPACE SHARED SECRETS

Version: 2026-10-01
Role: Workspace Shared Secret / credentialを安全に利用するための共通契約。

この文書はSecret値の保管場所ではない。Secret / Token / password / credential / session値をGit / Source / Document / Logへ保存しない。

## 1. server-core Responsibility

server-coreが管理するのは次のContract情報だけ。
- provider / purpose
- secret identifier
- allowed consumer
- broker / Vault access route
- allowed origin / request boundary
- identity / availability verification method
- failure behavior
- rotation / replacement boundary

Secret値そのものはserver-coreへ置かない。

## 2. Current Shared Contracts

機械可読Authority:
- Hugging Face: `operations/huggingface.json`
- Cloudflare Account API: `operations/cloudflare-account.json`

`operations/cloudflare.json` はCurrent server-core assetではない。Project固有Tunnel credentialはowning Project authorityで管理する。

| Provider / purpose | secret_id | consumer | provider verification |
|---|---|---|---|
| Hugging Face | `hf-token` | `g-ace-workspace` | `https://huggingface.co/api/whoami-v2` またはTaskに必要なrepresentative call |
| Cloudflare Account API | `cf-account-api` | `g-ace-workspace` | `/client/v4/user` + `/client/v4/accounts` またはTaskに必要なrepresentative call |

## 3. Broker Contract

Current broker authority: Libral Vault。

Runtime entry:

```text
Vault endpoint: http://127.0.0.1:8791
Action API: POST /internal/v1/actions/http
Secret registration API: POST /internal/v1/secrets
Consumer: g-ace-workspace
Internal auth source: /home/admin1/.config/libral-vault/internal-token
```

Internal auth valueはruntimeでのみ読み、Source / Git / Document / Logへ複製しない。

Provider request pattern:

```json
{
  "secret_id": "<registered-id>",
  "consumer": "g-ace-workspace",
  "url": "<allowlisted-provider-url>",
  "method": "GET",
  "secret_header": "authorization",
  "secret_prefix": "Bearer "
}
```

Vaultがprovider credentialをinjectし、callerはplaintext provider tokenを必要としない。

## 4. Use Rule

```text
Project needs provider access
  -> WORKSPACE_REGISTRY / this contract
  -> identify existing secret contract
  -> use broker action
  -> verify provider identity / representative behavior as required
```

既存Contractが無い場合は、secret id、consumer、allowlist、broker route、verification method、failure behaviorを先に定義する。Project-local token copyを即席で作らない。

## 5. Registration / Replacement

Credential registration / replacementはMutation。

対象Runtime / Provider Authorityで定義された承認条件を満たしてから実行する。

Credential入力は一時process environment等のapproved secure channelを使用し、committed fileや長期保存される出力へ残さない。

Required registration fields:
- id
- value (runtime input only)
- allowed consumers
- provider / purpose linkage

Replacement時はactive consumerへの影響、rollback/recovery、old credential removal timingを確認する。

## 6. Identity / Availability Verification

Vaultはplaintext tokenを返さない設計を前提とする。

Credential availabilityはprovider identity endpointまたはharmless representative API callで確認する。

HTTP statusだけでpermission scopeまで証明されたとみなさず、Taskで必要なoperationが可能かを確認する。

## 7. Failure Contract

代表的failure class:
- `SECRET_NOT_FOUND`
- `ACCESS_DENIED`
- `HTTP_ORIGIN_NOT_ALLOWED`
- provider 401/403
- broker unavailable
- provider/API transport failure

Failure時にplaintext credentialを表示・コピー・embedするfallbackへ切り替えない。

## 8. Consumer Boundary

Workspace-shared credentialは明示されたconsumerだけが利用する。

Project-specific credentialを自動的にWorkspace shared contractへ昇格しない。Sharedはunrestrictedを意味しない。

## 9. Add-New-Contract Gate

```text
SHARED_USE_CASE_CONFIRMED=YES
OWNER_KNOWN=YES
PROVIDER_KNOWN=YES
SECRET_ID_DEFINED=YES
CONSUMERS_DEFINED=YES
ALLOWLIST_DEFINED=YES
BROKER_PATH_DEFINED=YES
IDENTITY_OR_REPRESENTATIVE_VERIFY_DEFINED=YES
FAILURE_BEHAVIOR_DEFINED=YES
PLAINTEXT_PERSISTENCE=NO
```

Unknown項目がある状態で `AVAILABLE_VERIFIED` としない。

## 10. Registry Sync

shared credential contractが追加/削除/rename、consumer/broker path変更された場合:
- relevant `operations/*.json` contractを更新
- `docs/WORKSPACE_REGISTRY.md` を更新
- common use/failure modelが変わる場合は本Documentを更新
- applicable validationを実行
- source/config変更をGitHub historyへ残す

本Documentをchronological work logにしない。

## 11. Safety Invariants

- Secret / Token valuesをGit / Source / docs / logsへ保存しない。
- Workspace sharingのためにplaintext Secret fileを増やさない。
- approved shared contractがある場合、Projectごとのduplicate token helperを作らない。
- Vaultからplaintext値をdumpしない。
- Provider credentialの目的/consumerを別Contractへ流用しない。
- Cloudflare Account API credentialとProject固有Tunnel credentialを混同しない。
- credential availabilityをTaskで必要なbroker/provider verificationなしに断定しない。

## 12. Availability Boundary

Document contract completenessとbroker/provider Current Runtime availabilityは別状態。

Current availabilityがTask判断に必要な場合はbroker health、contract presence、consumer permission、provider representative callを必要範囲でreadbackする。
