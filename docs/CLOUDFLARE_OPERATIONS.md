# CLOUDFLARE OPERATIONS — WORKSPACE COMMAND CONTRACT

Version: 2026-10-01
Role: server-coreからCloudflare関連Taskを安全にRouting・統制するためのWorkspace共通契約。

## 1. Purpose

server-coreは各Project固有のTunnel / Worker / Pages / DNS / Access実装を所有しない。

server-coreが担当するのは:
- Cloudflare Taskのowner / target Project特定
- shared credential / MCP / Account API利用境界
- read-only / mutation / production境界
- Project固有Authorityへのdispatch
- GitHub revisionとProvider/Runtime stateの分離
- mutation後のProvider readback契約

## 2. Authority Split

### server-core owns
- Workspace共通Cloudflare operation rules
- Shared credential contractへの導線
- Cloudflare MCP / Account API discovery
- common mutation / verification boundary
- `operations/cloudflare-account.json` のAccount API contract

ここでの `owns` はCurrent Authorityの責務を示すだけで、server-core Repositoryのwrite permissionではない。これら共通Contractの変更が必要と判明しても、server-core自体についてexplicit owner authorizationがあり `SERVER_CORE_MUTATION_AUTHORIZED=YES` が成立するまではserver-coreを変更しない。

### owning Project owns
- hostname / route / zone / worker / pages / tunnelのProject固有Design
- Docker / Compose / application runtime definition
- Project固有origin / port / health endpoint
- Project固有rollback / release procedure
- Project固有credential injection

Project固有値をserver-core共通Authorityへ固定しない。

## 3. Task Routing

```text
TARGET_PROJECT
RESOURCE_TYPE
READ_ONLY_OR_MUTATION
PROVIDER_ACCOUNT_OR_ZONE
PROJECT_AUTHORITY
AUTH_METHOD
EXPECTED_CHANGE
VERIFY_METHOD
ROLLBACK_PATH
CHANGE_APPROVAL
```

対象Project / resource ownerが不明なら `docs/WORKSPACE_REGISTRY.md` と対象Project READMEを確認する。

hostname / account / zone / origin / tunnel nameを推測で作らない。

## 4. Shared Access Paths

### Cloudflare API MCP
Actual client registrationがある場合のみ利用候補。

Registry記載だけでCurrent availabilityを断定しない。Taskで必要な場合はauthentication / transport / tool discovery / representative callを確認する。

### Cloudflare Account API via Shared Credential Broker
Shared contract:
- secret id: `cf-account-api`
- consumer: `g-ace-workspace`
- authority: `docs/WORKSPACE_SHARED_SECRETS.md`
- machine contract: `operations/cloudflare-account.json`

Credential値をProjectへ配らない。

### Cloudflare Tunnel credential
Account API credentialとTunnel credentialを同一視しない。

Tunnel credentialのowner/injection方法は対象ProjectのCurrent Authorityを正とする。

## 5. Read-only vs Mutation

Read-only例:
- resource discovery
- DNS/route/config readback
- status / health確認
- deployment/runtime state確認
- permission確認

Mutation例:
- DNS record create/update/delete
- Tunnel/route変更
- Access policy変更
- Pages/Worker setting変更
- Secret/credential rotation
- Production publish/cutover

Read-only確認をMutation承認として扱わない。

Provider mutation permissionとserver-core Repository mutation permissionも別である。Cloudflare resource変更が承認されていても、それだけでserver-coreのDocument/operations/script変更は許可されない。

## 6. Mutation / Approval Boundary

Provider mutationは対象Project / Provider Authorityで定義された承認条件を満たしてから実行する。

Pre-change gate:

```text
OWNER_KNOWN=YES
TARGET_PROJECT_KNOWN=YES
RESOURCE_IDENTITY_VERIFIED=YES
CURRENT_STATE_READBACK=YES
EXPECTED_CHANGE_DEFINED=YES
AUTH_PATH_VERIFIED=YES
ROLLBACK_DEFINED=YES when required
REQUIRED_APPROVAL_SATISFIED=YES
```

承認者の個人名や会話上の呼称をWorkspace共通Contractへ固定しない。

server-core Repository側の変更が必要な場合は、このProvider gateとは別に `SERVER_CORE_MUTATION_AUTHORIZED=YES` を必要とする。

## 7. Change Execution Rule

Provider変更は正式Interfaceを使う。
- official UI
- official API
- registered MCP
- approved project-specific script

変更対象とscopeを限定し、別Project / 別Zone / 別Accountを同時に変更しない。

## 8. Verification

Provider APIの200/Successだけで完了としない。

必要範囲で確認する。
- intended resource changed
- unintended resource unchanged
- DNS/route resolution
- external/internal endpoint behavior
- Access/auth behavior
- target Project health
- deployed revisionとの対応
- rollback path validity

Mutation後はProvider readbackを行う。

## 9. Failure / Recovery

失敗時:
- Success扱いしない
- 次のpublish/cutoverへ自動で進まない
- actual Provider stateをreadbackする
- partial mutationの有無を確認する
- rollbackまたはforward fixをProject Authorityに従って判断する
- Source変更が必要なら対象Repository development loopへ戻す

Provider failureからserver-core共通Contractの欠陥が疑われても、explicit owner authorization無しにserver-coreを自己修正しない。

## 10. Credential Boundary

- Token / Secret値をGit / Source / docs / logsへ保存しない。
- Account API credentialとTunnel credentialを混同しない。
- server-core `operations/*.json` へcredential実値を保存しない。
- verificationのためにplaintext tokenをdumpしない。

Shared credential contractは `docs/WORKSPACE_SHARED_SECRETS.md` を正とする。

## 11. Project-specific Documentation

Project固有Cloudflare Design/Runbookはowning Project側へ置く。

対象例:
- production / preview hostname
- origin port
- cloudflared container / service
- Project-specific release gate
- Runtime credential path/injection

Git historyに残る旧server-core Project-specific Cloudflare実装はhistorical recordであり、Current Authorityとして再利用しない。

## 12. Completion Boundary

Read-only Task:

```text
TARGET_IDENTIFIED
CURRENT_STATE_READBACK
REQUESTED_FACTS_VERIFIED
NO_MUTATION
```

Mutation Task:

```text
TARGET_IDENTIFIED
PRE_CHANGE_STATE_CAPTURED
AUTHORIZED_CHANGE_APPLIED
PROVIDER_READBACK_PASS
PROJECT_BEHAVIOR_VERIFIED
UNINTENDED_CHANGE_NONE
ROLLBACK_OR_RECOVERY_STATE_KNOWN
```

server-coreはCloudflareの共通Routing / credential / change / verification contractを持つが、各ProjectのCloudflare実装そのものは所有しない。server-core共通Contract自体の変更には、Cloudflare操作権限とは別にexplicit server-core mutation authorizationが必要である。
