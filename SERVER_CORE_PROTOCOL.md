# SERVER CORE OPERATION PROTOCOL

Version: 2026-10-01
Role: G-ACE Workspace Command Centerの共通運用・変更・安全境界。

## Purpose

G-ACE Workspace全体で共通に必要なAuthority、変更境界、GitHub、Runtime、Secret、Storageの運用契約を定める。

server-coreはTaskをRouting / Dispatchするが、Project固有実装のownerにはならない。開発方法論、Project構成、Deploy詳細、KB、Storage lifecycle等は各専用Authorityへ分離し、本Protocolへ重複させない。

## Authority / Change Control

変更操作は、対象Repository / Project / Provider / RuntimeのCurrent Authorityで定義された権限と承認条件に従う。

質問、検討、read-only確認、提案、操作説明をMutation承認として扱わない。

次の操作はread-only確認と分離し、対象Authorityの承認条件を満たした場合だけ実行する。
- main / PR merge
- Production deploy / publish / cutover
- force push / destructive history rewrite
- active service stop / restart / recreate
- Secret / credential add / delete / rotation
- Provider resource create / update / delete

承認者の名称や個別セッション上の呼称をserver-core仕様へ固定しない。必要な承認主体はProject / Provider / Repository contractで定義する。

## Workspace Entry / Dispatch

```text
server-core/README.md
  -> server-core/docs/LOAD_SCOPE.md
  -> Taskに必要なserver-core Authorityだけ
  -> 対象Project README
  -> 必要なProject Authority / Source / Test
```

全正本を一括読込しない。

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

## Documentation / Work History

Current仕様Documentへ一時的なセッション指示、個別作業メモ、時系列作業日誌を混在させない。

時系列の作業履歴はGitHub commit / PRへ残す。完成状態、Project構造、Designとの差、運用Contractが変わった場合はDocumentation Gateに従う。

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
 -> required change approval
 -> Server deploy
 -> Runtime verification
```

Deploy詳細は `docs/DEPLOY_RUNBOOK.md`。

Server上の直接Source修正を正式開発履歴の代替にしない。Runtimeで修正必要性を発見した場合は、原則Repository開発Loopへ戻す。

## Shared Capability Boundary

server-coreは共有Capabilityの実装本体を抱え込まず、Discovery・接続契約・owner・permission/change boundary・verification methodを管理する。

Registry記載や過去利用実績だけでCurrent Runtimeを証明しない。必要時は実設定・Provider・Endpoint・Docker・GitHub等をreadbackする。

Capability固有のCurrent状態は `docs/WORKSPACE_REGISTRY.md` を正とし、本Protocolへ個別Projectの一時状態を複製しない。

## Project Integration

TGserver / webhook gateway等のProject-owned service、Libral Vault、MCP、ToolのProject導入契約は `docs/PROJECT_INTEGRATION_RULES.md` を正とする。

Shared CapabilityとProject-owned serviceを混同しない。

## Storage / Backup / Recovery

共通Storage分類・cleanup safety・backup/recovery契約は `docs/STORAGE_LIFECYCLE.md` を正とする。

server-coreはProject固有Dataのownerにならない。owner不明、active use、retry/recovery中、restore path不明、persistent volumeの可能性があるDataをgeneric cleanup対象にしない。

## Docker / Runtime

本番常駐の標準経路はDocker / Docker Compose。Project固有の正式例外がある場合はそのAuthorityを優先する。

Container起動だけでRuntime PASSとせず、Taskに必要なEndpoint / Output / State / side effectまで確認する。

## Secret / Credential

Secret / Token / password / session / credentialの実値をGit / Source / Document / Logへ保存しない。

Workspace共有Secretは `docs/WORKSPACE_SHARED_SECRETS.md` を正とし、各Projectへ実値を複製しない。

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
- credential実値をSource / Git / Document / Logへ保存しない。
- Project固有実装をserver-coreへ移して責務境界を崩さない。
