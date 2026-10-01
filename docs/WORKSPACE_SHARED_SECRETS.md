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

## 2. Operation Separation

Credential関連Taskは次を別Operationとして扱う。

```text
USE_EXISTING_CONTRACT
VERIFY_AVAILABILITY
ADD_CONTRACT
REGISTER_CREDENTIAL
REPLACE_OR_ROTATE_CREDENTIAL
CHANGE_BROKER_IMPLEMENTATION
```

- `USE_EXISTING_CONTRACT`: 既存broker contractを利用するだけ。server-core Document、Vault implementation、credential値を変更しない。
- `VERIFY_AVAILABILITY`: health / identity / representative callのreadback。credential mutationを行わない。
- `ADD_CONTRACT`: Workspace共通contract自体の追加。server-core contract変更対象。
- `REGISTER_CREDENTIAL`: broker runtime mutation。Source/Document変更とは別Operation。
- `REPLACE_OR_ROTATE_CREDENTIAL`: active credential mutation。明示されたchange boundaryを必要とする。
- `CHANGE_BROKER_IMPLEMENTATION`: Libral Vault owning Project側の実装Task。server-coreは共通Contractが変わらない限りread-only。

「credentialを使う」「接続確認する」「provider APIを呼ぶ」だけでregistration / rotation / Vault implementation変更へ進まない。

## 3. Current Shared Contracts

機械可読Authority:
- Hugging Face: `operations/huggingface.json`
- Cloudflare Account API: `operations/cloudflare-account.json`

`operations/cloudflare.json` はCurrent server-core assetではない。Project固有Tunnel credentialはowning Project authorityで管理する。

| Provider / purpose | secret_id | consumer | provider verification |
|---|---|---|---|
| Hugging Face | `hf-token` | `g-ace-workspace` | `https://huggingface.co/api/whoami-v2` またはTaskに必要なrepresentative call |
| Cloudflare Account API | `cf-account-api` | `g-ace-workspace` | `/client/v4/user` + `/client/v4/accounts` またはTaskに必要なrepresentative call |

Contract記載はcredential値の存在・Current availabilityを保証しない。

## 4. Broker Contract

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

Broker endpoint/registration APIがDocumentに記載されていても、それ自体はregistration permissionではない。

## 5. Use Rule

```text
Project needs provider access
  -> WORKSPACE_REGISTRY / this contract
  -> identify existing secret contract
  -> use broker action
  -> verify provider identity / representative behavior as required
```

既存Contract利用で足りる場合、Project-local token copy、new secret registration、server-core contract変更を行わない。

既存Contractが無い場合は、secret id、consumer、allowlist、broker route、verification method、failure behaviorを先に定義する。Project-local token copyを即席で作らない。

## 6. Registration / Replacement

Credential registration / replacementはMutation。

対象Runtime / Provider Authorityで定義された承認条件を満たしてから実行する。

Credential入力は一時process environment等のapproved secure channelを使用し、committed fileや長期保存される出力へ残さない。

Required registration fields:
- id
- value (runtime input only)
- allowed consumers
- provider / purpose linkage

Replacement時はactive consumerへの影響、rollback/recovery、old credential removal timingを確認する。

利用Taskのfailureだけを根拠に、新規registration/rotationで回避しない。まず `SECRET_NOT_FOUND` / permission / transport / provider error等のfailure classを確認する。

## 7. Identity / Availability Verification

Vaultはplaintext tokenを返さない設計を前提とする。

Credential availabilityはprovider identity endpointまたはharmless representative API callで確認する。

HTTP statusだけでpermission scopeまで証明されたとみなさず、Taskで必要なoperationが可能かを確認する。

Availability verificationはread-only/harmless routeを優先し、verificationのためだけにcredentialを置換しない。

## 8. Failure Contract

代表的failure class:
- `SECRET_NOT_FOUND`
- `ACCESS_DENIED`
- `HTTP_ORIGIN_NOT_ALLOWED`
- provider 401/403
- broker unavailable
- provider/API transport failure

Failure時にplaintext credentialを表示・コピー・embedするfallbackへ切り替えない。

Failure原因ownerが不明な状態でserver-core / Vault / consumer Project / Providerの複数領域を同時変更しない。

## 9. Consumer Boundary

Workspace-shared credentialは明示されたconsumerだけが利用する。

Project-specific credentialを自動的にWorkspace shared contractへ昇格しない。Sharedはunrestrictedを意味しない。

Consumer Projectで既存Contractを利用するだけなら、Libral Vault Repositoryやserver-core Documentはread-onlyとする。

## 10. Add-New-Contract Gate

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

## 11. Registry Sync

shared credential contractが追加/削除/rename、consumer/broker path変更された場合:
- relevant `operations/*.json` contractを更新
- `docs/WORKSPACE_REGISTRY.md` を更新
- common use/failure modelが変わる場合は本Documentを更新
- applicable validationを実行
- source/config変更をGitHub historyへ残す

Credentialを単に利用・検証しただけではRegistry/Document updateを必須にしない。

本Documentをchronological work logにしない。

## 12. Safety Invariants

- Secret / Token valuesをGit / Source / docs / logsへ保存しない。
- Workspace sharingのためにplaintext Secret fileを増やさない。
- approved shared contractがある場合、Projectごとのduplicate token helperを作らない。
- Vaultからplaintext値をdumpしない。
- Provider credentialの目的/consumerを別Contractへ流用しない。
- Cloudflare Account API credentialとProject固有Tunnel credentialを混同しない。
- credential availabilityをTaskで必要なbroker/provider verificationなしに断定しない。
- credential利用をregistration/rotation permissionと読み替えない。
- broker Contract参照をVault implementation mutation permissionと読み替えない。

## 13. Availability Boundary

Document contract completenessとbroker/provider Current Runtime availabilityは別状態。

Current availabilityがTask判断に必要な場合はbroker health、contract presence、consumer permission、provider representative callを必要範囲でreadbackする。

Current availabilityの確認結果を、Source/Document mutationの必要性と自動的に結び付けない。
