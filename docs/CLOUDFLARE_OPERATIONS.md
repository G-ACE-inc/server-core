# CLOUDFLARE OPERATIONS — WORKSPACE COMMAND CONTRACT

Version: 2026-09-30
Role: server-core司令室からCloudflare関連Taskを安全にRouting・統制するためのWorkspace共通契約。

## 1. Purpose

server-coreはCloudflareの各Project固有Tunnel / Worker / Pages / DNS / Access実装を所有しない。

server-coreが担当するのは:
- Cloudflare Taskのowner/target Projectを特定する;
- 共通Credential / MCP / Account API利用境界を示す;
- change/read-only/production境界を明確にする;
- Project固有AuthorityへDispatchする;
- GitHub revisionとRuntime/Provider stateを分離する;
-変更後のProvider readbackを要求する。

## 2. Authority Split

### server-core owns
- Workspace共通Cloudflare operation rules
- Shared Secret / Token contractへの導線
- Cloudflare MCP / Account API discovery
- common approval boundary
- common provider verification rule
- `operations/cloudflare-account.json` のSecret値を含まないAccount API契約
- `operations/huggingface.json` 等の他Provider契約とは混同しない

### owning Project owns
- hostname / route / zone / worker / pages / tunnelのProject固有Design
- Docker / Compose / application runtime definition
- Project固有origin / port
- Project固有health endpoint
- Project固有rollback
- Project固有Secret file path / runtime injection
- release/deploy decision

Project固有値をserver-coreの共通正本へ固定しない。

## 3. Task Routing

Cloudflare Taskを受けたら次を判定する。

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
APPROVAL_REQUIRED
```

対象Project / resource ownerが不明なら `docs/WORKSPACE_REGISTRY.md` と対象Project READMEを確認する。

推測でhostname / account / zone / origin / tunnel nameを作らない。

## 4. Shared Access Paths

### Cloudflare API MCP
Clientに実登録されている場合のみ利用候補。

Actual config authority例: `.cursor/mcp.json`。

Registry記載だけで利用可能と断定せず、Task時に必要な疎通/権限を確認する。

### Cloudflare Account API via Shared Secret Broker
Shared contract:
- secret id: `cf-account-api`
- consumer: `g-ace-workspace`
- authority: `docs/WORKSPACE_SHARED_SECRETS.md`
- machine contract: `operations/cloudflare-account.json`

Secret値を読み出してProjectへ配らない。

### Cloudflare Tunnel credential
Account API credentialとTunnel credentialを同一視しない。

Tunnel credentialのowner/injection方法は対象ProjectのCurrent Authorityを正とする。

## 5. Read-only vs Mutation

Read-only例:
- resource discovery
- DNS/route/config readback
- status / health確認
- deployment/runtime state確認
- permissions確認

Mutation例:
- DNS record create/update/delete
- Tunnel/route変更
- Access policy変更
- Pages/Worker setting変更
- Secret/credential rotation
- Production publish/cutover

Read-only確認をMutation承認として扱わない。

## 6. Approval Boundary

Masterの明示指示なしに次を実行しない。
- Provider resource create/update/delete
- Production publish / cutover
- Secret/credential add/delete/rotation
- DNS/route/tunnel/access変更
- 稼働Service停止/recreateを伴う変更

現在の明示指示が対象Mutationを含む場合だけその範囲で進める。

## 7. Pre-change Gate

Mutation前に必要範囲で確認する。

```text
OWNER_KNOWN=YES
TARGET_PROJECT_KNOWN=YES
RESOURCE_IDENTITY_VERIFIED=YES
CURRENT_STATE_READBACK=YES
EXPECTED_CHANGE_DEFINED=YES
AUTH_PATH_VERIFIED=YES
ROLLBACK_DEFINED=YES when change is reversible/critical
MASTER_APPROVAL=YES when required
```

Unknownを推測でYESにしない。

## 8. Change Execution Rule

Provider変更は対象Project / Providerの正式Interfaceを使う。

- UI操作
- official API
- registered MCP
- approved project-specific script

どの経路でも、変更対象とscopeを限定する。

別Project / 別Zone / 別Accountをついでに変更しない。

## 9. Verification

Provider APIの200/Successだけで完了としない。

必要範囲で確認する。
- intended resource changed
- unintended resource unchanged
- DNS/route resolution
- external/internal endpoint behavior
- Access/auth behavior
- target Project health
- deployed revisionとの対応
- rollback path still valid

Mutation後はProvider readbackを行う。

## 10. Failure / Recovery

失敗時:
- Success扱いしない
- 次の公開/切替へ自動で進まない
- actual Provider stateをreadbackする
- partial mutationの有無を確認する
- rollbackまたはforward fixをProject Authorityに従って判断する
- Source変更が必要なら対象Repositoryのdevelopment loopへ戻す

## 11. Secret Boundary

禁止:
- Token / Secret値をChat / Git / docs / logsへ出す
- Account API TokenとTunnel Tokenを混同する
- Secret値をserver-core `operations/*.json`へ保存する
- provider credentialをProjectへ無断複製する
- verificationのためにplaintext tokenをdumpする

Shared Secret契約は `docs/WORKSPACE_SHARED_SECRETS.md` を正とする。

## 12. Project-specific Cloudflare Documentation

Project固有Cloudflare design/runbookはowning Project側へ置く。

Project固有Authorityへ置く対象例:
- production / preview hostname
- origin port
- cloudflared container / service
- Project-specific release gate sequence
- Runtime Secret path

必要な場合は対象Project README / Design / Runtime docs / Git historyからCurrent Authorityを確認する。

Git historyに残る旧server-core Cloudflare文書はhistorical implementation recordであり、Current Project-specific Authorityとして再利用しない。

## 13. Common Tooling

server-coreにProject固有Cloudflare操作Scriptを常設しない。CloudflareのProject固有操作は対象ProjectのCurrent Authorityにある公式API / MCP / approved project-specific scriptを使う。

Workspace共通でserver-coreが保持する機械可読契約は、Shared Secret / Account API等の共通境界に限定する。

Tool利用前に:
- target Project compatibility
- current configuration
- mutation behavior
- credential path
- output / verification behavior
を確認する。

## 14. Completion Boundary

Cloudflare Taskの完了はTask種別に応じて判定する。

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
ROLLBACK/RECOVERY_STATE_KNOWN
```

## 15. Command-center Rule

server-coreはCloudflareを**操作する司令室の共通境界**を持つが、各ProjectのCloudflare実装そのものは所有しない。