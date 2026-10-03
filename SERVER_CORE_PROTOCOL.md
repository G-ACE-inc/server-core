# SERVER CORE OPERATION PROTOCOL

Version: 2026-10-03
Role: G-ACE Workspace Command Centerの共通運用・変更・安全境界。

## Purpose

G-ACE Workspace全体で共通に必要なAuthority、変更境界、GitHub、Runtime、Secret、Storageの運用契約を定める。

server-coreはTaskをRouting / Dispatchするが、Project固有実装のownerにはならない。開発方法論、Project構成、Deploy詳細、KB、Storage lifecycle等は各専用Authorityへ分離し、本Protocolへ重複させない。

## Authority / Change Control

最終決定者はMaster。

質問、検討、read-only確認、提案、操作説明をMutation承認として扱わない。未確認状態を推測で補完しない。

Masterの明示指示なしに次を実行しない。
- main / PR merge
- Production deploy / publish / cutover
- force push / destructive history rewrite
- active service stop / restart / recreate
- Secret / credential add / delete / rotation
- Provider resource create / update / delete
- 新規Model download
- 新規Repository / Project / Space作成

**server-coreへのwrite / commit / branch mutationは、server-core自体の変更についてMasterの明示許可が必要。** 他ProjectのTask、共通Authority参照、障害調査、Shared Capability利用、Workspace共通Contractへの影響可能性から暗黙に承認を推論しない。

## Repository Mutation Ownership

Taskで参照するRepositoryと、Taskで変更してよいRepositoryを分離する。

```text
TARGET_REPOSITORY
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
SERVER_CORE_MUTATION_AUTHORIZED
```

- `TARGET_REPOSITORY`: 主対象ProjectのRepository。
- `MUTATION_REPOSITORIES`: 今回Source / Config / Document / Commitを変更してよいRepository。
- `READ_ONLY_REPOSITORIES`: Authority確認、再利用調査、Integration確認、Runtime調査のために読むだけのRepository。
- `SERVER_CORE_MUTATION_AUTHORIZED`: server-core自体の変更についてMasterの明示許可がある場合だけ `YES`。

server-coreは `SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示的に成立しない限りread-only。Workspace共通Contract変更が必要に見えても、自動的にmutation対象へ昇格しない。

Shared Capability / service / Provider owner Repositoryを確認したことは、そのRepository実装の変更理由にならない。利用・接続・検証Taskではowner側をread-onlyとし、owner-side changeが必要と確認された場合だけ別mutation対象へ昇格する。

Git操作前にはcurrent repository identityとmutation targetを照合する。別RepositoryのScriptを実行するために `cd` したことを、Task owner変更の根拠にしない。server-coreの場合はさらに `SERVER_CORE_MUTATION_AUTHORIZED=YES` を確認する。

## Workspace Entry / Dispatch

```text
server-core/README.md
  -> server-core/docs/LOAD_SCOPE.md
  -> 今回必要なserver-core Authorityだけ
  -> 対象Project README
  -> 必要なProject Authority / Source / Testだけ
```

全正本を一括読込しない。同一Taskで確認済みのAuthorityは、変更・矛盾・情報不足が無い限り繰り返し読まない。

Workspace仕様: `docs/G_ACE_WORKSPACE.md`  
Discovery: `docs/WORKSPACE_REGISTRY.md`  
Design: `docs/SERVER_CORE_DESIGN.md`  
Design Delta: `docs/DESIGN_DELTA.md`

## Development Boundary

- 開発方法論・再利用・5段Architecture・Module判断: `CORE.md`
- Project構成・Documentation Gate: `docs/PROJECT_TEMPLATE.md`
- Project固有の実装・Design・System仕様はowning Project側に置く。
- 公開契約は可能な限りCode上のInterface / Type / Schema / Testと整合させる。
- Design BaselineをCurrent実装へ合わせるためだけに書き換えない。
- Project Document更新Taskをserver-core Document更新へ読み替えない。
- server-core側に改善余地を発見しても、Masterの明示許可なしに併せて修正しない。
- 必要工程を理由なく省略せず、固定ルーティーンから勝手に脱線しない。

## Verification

Taskの受入条件に必要な範囲で確認する。
- Input
- execution condition
- expected output
- changed state
- state that must not change
- regression
- major failure cases
- Runtime / Provider readback when relevant

Process起動、Error無し、HTTP 200、Build成功、CI green等は、それ自体がTaskの受入条件でない限り、Task全体のPASS証拠にはしない。

未実行・未確認・未検証は `NOT_EXECUTED / UNKNOWN / NOT_VERIFIED` を維持する。

## State Semantics

状態名はDomainごとに証明範囲を固定し、隣接状態へ自動昇格させない。

```text
SOURCE_VERIFIED != CONFIG_PRESENT
CONFIG_PRESENT != CONFIG_REGISTERED
CONFIG_REGISTERED != CLIENT_REGISTRATION_VERIFIED
CLIENT_REGISTRATION_VERIFIED != AUTHENTICATION_VERIFIED
AUTHENTICATION_VERIFIED != TRANSPORT_VERIFIED
TRANSPORT_VERIFIED != INTERFACE_DISCOVERY_VERIFIED
INTERFACE_DISCOVERY_VERIFIED != REPRESENTATIVE_CALL_PASS
REPRESENTATIVE_CALL_PASS != AVAILABLE_VERIFIED unless that Capability gate is satisfied
AUDIT_PASS != MUTATION_AUTHORIZED
MUTATION_AUTHORIZED != MUTATION_APPLIED
BUILD_PASS != DEPLOY_PASS
DEPLOY_PASS != RUNTIME_PASS
RUNTIME_PASS != PRODUCTION_PASS
```

`HEALTHY`、`AVAILABLE`、`VERIFIED`、`REGISTERED`、`IMPLEMENTED`、`APPLIED` 等の語を使う場合は、何を実測・検証した状態かをAuthority / machine contract / readback evidenceで特定する。

単一のHTTP 200、config entry、process/container起動、client listing、Source存在、過去利用実績を、それより強いCurrent stateへ読み替えない。

逆に、Current live再検証待ちを理由に、Source/implementation/protocolの既検証状態を未実装へ降格しない。

## Documentation / Work History

Current仕様Documentへ一時的なセッション指示、個別作業メモ、時系列作業日誌を混在させない。

時系列の作業履歴はGitHub commit / PRへ残す。完成状態、Project構造、Designとの差、運用Contractが変わった場合はDocumentation Gateに従う。

対象ProjectのREADME / README-linked Documentは対象Project Repository側で更新する。server-coreはProject Documentの既定保存先ではない。

server-core Documentは `SERVER_CORE_MUTATION_AUTHORIZED=YES` のときだけ更新する。

Commit / Push / Remote Readbackは `docs/AUTO_COMMIT.md` を正とする。

## GitHub / Deploy

GitHub revisionとServer Runtimeを別状態として扱う。

```text
implementation / fix
 -> verify
 -> documentation gate
 -> commit
 -> push
 -> remote readback
 -> PR / CI when required
 -> confirmed GitHub revision
 -> target runtime identity lock
 -> Master approval when required
 -> Server deploy
 -> Runtime verification
```

Deploy詳細は `docs/DEPLOY_RUNBOOK.md`。

Server上の直接Source修正を正式開発履歴の代替にしない。Runtimeで修正必要性を発見した場合は、原則対象Repository開発Loopへ戻す。

server-core Runbookを参照したことを、server-core自身がDeploy targetである証拠にしない。

## Shared Capability Boundary

server-coreは共有Capabilityの実装本体を抱え込まず、Discovery・接続契約・owner・permission/change boundary・verification methodを管理する。

Capabilityを利用・登録・接続・検証することと、Capability implementationを変更することを分離する。

Registry記載や過去利用実績だけでCurrent Runtimeを証明しない。必要時は実設定・Provider・Endpoint・Docker・GitHub等をreadbackする。

Capabilityのdurableなowner / authority / state semantics / verification boundaryは `docs/WORKSPACE_REGISTRY.md` を正とする。CapabilityのCurrent live stateはRegistry記載を代用せず、Task時の実client/provider/runtime readbackを正とする。本Protocolへ個別Projectの一時状態を複製しない。

## Project Integration

TGserver / webhook gateway等のProject-owned service、Libral Vault、MCP、ToolのProject導入契約は `docs/PROJECT_INTEGRATION_RULES.md` を正とする。

Shared CapabilityとProject-owned serviceを混同しない。

Integration Taskではconsumer Projectとservice/capability ownerを別mutation domainとして扱う。通常の利用・接続でowner実装を変更しない。

## Storage / Backup / Recovery

共通Storage分類・cleanup safety・backup/recovery契約は `docs/STORAGE_LIFECYCLE.md` を正とする。

server-coreはProject固有Dataのownerにならない。owner不明、active use、retry/recovery中、restore path不明、persistent volumeの可能性があるDataをgeneric cleanup対象にしない。

Storage auditでProject固有Dataを発見したことを、そのDataへのmutation permissionと扱わない。

## Docker / Runtime

本番常駐は **Docker Composeを正** とする。Host上の `node` / `python` / `npm start` / `pm2` / `nohup` / `screen` / `tmux` 等を本番常駐経路として採用しない。

Container起動だけでRuntime PASSとせず、Taskに必要なEndpoint / Output / State / side effectまで確認する。

Runtime上に複数Projectが存在しても、対象Project外のservice/container/volumeへ同一Taskで推測変更しない。

## Secret / Credential

Secret / Token / password / session / credentialの実値をGit / Source / Document / Logへ保存しない。

Workspace共有Secretは `docs/WORKSPACE_SHARED_SECRETS.md` を正とし、各Projectへ実値を複製しない。

Secret Contractを読むこと、credential availabilityを確認すること、credentialを登録/rotationすることを別Operationとして扱う。

## Archive

旧版・退避は `archive/YYYY-MM-DD/` を基本とする。

- credential実値をarchiveへ保存しない
- archiveをCurrent Authorityとして扱わない
- 通常Contextへ入れない

## Operational Invariants

- 推測をCurrent事実として扱わない。
- 未実行を実行済み、未検証をPASSとして記録しない。
- Testを削除・無効化して完成条件を満たしたことにしない。
- Design履歴を消してCurrent実装へ合わせない。
- Current仕様Documentを時系列作業日誌にしない。
- owner不明のFile / Module / Runtime / DataへMutationしない。
- `MUTATION_REPOSITORIES` 外のRepositoryへwrite/commitしない。
- Authorityを読んだだけのRepositoryへmutationしない。
- server-coreはMasterの明示許可なしにwrite/commit/branch mutationしない。
- credential実値をSource / Git / Document / Logへ保存しない。
- Project固有実装をserver-coreへ移して責務境界を崩さない。
