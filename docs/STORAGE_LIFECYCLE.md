# SERVER STORAGE / LOG / CACHE LIFECYCLE

Version: 2026-10-01
Status: Design Baseline

## 1. Purpose

Server上のLog / Cache / temporary state / backup / Docker storageを、所有者とRecovery条件を失わず安全に管理し、Disk肥大・誤削除・復旧不能を防ぐ。

Cleanupの目的は空き容量確保そのものではなく、**削除しても再生成・再送・復旧に支障がないと確認されたDataだけを対象にすること**。

## 2. Ownership Boundary

server-coreはWorkspace共通のStorage分類、Audit、Safety Gateを定義する。

Project固有のretention、shipping acknowledgement、retry、recovery、restore条件はowning Project側Contractを正とする。

server-coreはProject固有Dataのownerにならない。

## 3. Data Classes

### Durable authority
長期保管または正本。generic automatic cleanup対象にしない。

### Rebuildable cache / index
Source authorityと再構築手順が確認できる場合だけcleanup候補。

### Temporary operational state
送信待ち、再送待ち、処理途中、Recovery用一時状態等。TTLだけで消さず状態条件を確認する。

### Backup
Retention policyとrestore手順を持つ。単なる古いFileとして掃除しない。

### Unknown ownership
owner/classificationが不明。自動削除しない。

## 4. Common Server Storage Categories

| Storage class | Generic policy |
|---|---|
| application/service logs | owner + shipping/retention contract required |
| search/index data | rebuild path verifiedならconditional cleanup |
| hot cache / dedup state | owner contract / TTL / recovery semantics required |
| `/home/admin1/logs` | temporary operational area; item owner/classification required |
| Docker build cache | rebuildableならconditional cleanup |
| Docker image/container/network | runtime ownership + active/rollback readback required |
| Docker volume | persistent stateの可能性があるためgeneric delete禁止 |
| `/home/admin1/backups` | retention + integrity + restore policy required |

Telegram、Meilisearch、Redis等の特定ProductをWorkspace共通の唯一Authorityとして固定しない。実際のData owner/roleはowning Project/runtime Contractを確認する。

## 5. Safe Deletion Gate

自動削除前に最低限判定する。

```text
OWNER_KNOWN=YES
CLASSIFICATION_KNOWN=YES
ACTIVE_USE=NO
UNSHIPPED_DATA=NO
RETRY_PENDING=NO
RECOVERY_REQUIRED=NO
LOCK_OR_ACTIVE_TRANSACTION=NO
REBUILD_OR_RESTORE_PATH=VERIFIED when required
RETENTION_EXPIRED=YES or PRESSURE_POLICY_ALLOWS=YES
```

1つでもUNKNOWNならgeneric auto-deleteしない。

Candidate classification:

```text
SAFE_TO_DELETE
PRESERVE
UNKNOWN
```

`UNKNOWN` をDisk pressureだけで `SAFE_TO_DELETE` へ昇格させない。

## 6. Log Lifecycle

Logは次を分離する。
- durable / audit authority
- runtime stdout/stderr
- transport outbox/retry
- debug/diagnostic
- temporary processing

Projectは必要に応じてowner、retention、rotation、shipping acknowledgement、delete conditionを定義する。

Container logを無制限成長させない。実装時はCurrent logging driver/rotation設定をreadbackし、実測とProject要件に基づいて上限を決める。

## 7. Cache / Index Lifecycle

Cache / IndexはSource of Truthかどうかを確認する。

削除後の再構築方法が無い場合、実質Durable Stateとして扱い、先にOwnership/Recovery設計を修正する。

異なるCache/Index種別を1つのgeneric ruleで一括削除しない。

## 8. Docker Cleanup

Generic automationで禁止:
- `docker system prune -a --volumes`
- ownership未確認volume削除
- active/required imageの削除
- rollback candidateを確認しないsuperseded image削除

自動化候補:
- dangling/rebuildable build cacheでage/ownership条件を満たすもの
- stopped containerでRecovery不要が確認済みのもの
- superseded imageでrunning/rollback参照なしが確認済みのもの

Mutation実装時はdry-run/candidate、actual delete result、disk deltaを追跡可能にする。

## 9. Backup Lifecycle

Backupは最低限次を持つ。
- owner
- source
- retention generation/time
- integrity check
- restore target
- restore procedure
- restore verification

Backup cleanupは「新しいbackupがある」だけで行わず、integrity、保持世代、restore可能性を確認する。

## 10. Disk Pressure Guard

Pressure state:

```text
NORMAL
  -> WARNING
  -> HIGH
  -> CRITICAL
```

具体thresholdは実Server容量、使用量、growth rateを測定して決定する。このDesignへ推測値を固定しない。

Pressure時も原則:

```text
verified rebuildable / expired safe data
  -> other verified safe temporary data
  -> explicit operator decision
```

Durable / recovery / unknown ownershipへ自動で進まない。

## 11. Read-only Audit Contract

Current source:
- policy: `operations/storage-lifecycle.json`
- implementation: `scripts/storage_lifecycle_audit.py`

Expected policy boundary:

```text
mode = audit_only
allow_delete = false
docker.allow_prune = false
docker.allow_volume_delete = false
```

Auditは最低限次を収集できる設計にする。
- filesystem usage
- known log/cache/backup path summary
- Docker disk/resource summary when available
- candidate / preserve / unknown classifications when implemented
- timestamp and errors

Audit成功をCleanup成功と扱わない。

## 12. Cleanup Automation Contract

Mutation実装後は少なくとも以下を出力する。
- run id / timestamp
- policy revision
- disk before / after
- candidate count / bytes
- deleted count / bytes
- preserved count / reason
- UNKNOWN / blocked items
- errors

Failure時にcleanup完了と報告しない。

## 13. Scheduling

Data classごとに頻度を分離し、全領域を1本の巨大Cleanup processで処理しない。

実Serverのscheduler / container / systemd timer等をreadbackしてから方式を選ぶ。既存schedulerと重複させない。

## 14. Recovery First

Cleanup対象が障害復旧に使われる可能性がある場合、Recovery完了または別authorityへのarchive/ship receiptを確認するまで削除しない。

## 15. Verification

Mutation実装後はTaskに必要な範囲で検証する。
- dry-runが実削除しない
- active/recovery/unknown dataをpreserve
- safe candidateだけ削除
- disk使用量が期待通り変化
- required serviceが継続稼働
- restore/rebuild対象が実際に復元可能
- repeated runがidempotentまたは安全

## 16. Runtime Parameter Gate

次の値は実測なしに共通文書へ固定しない。
- disk pressure threshold
- retention days/generations
- log max-size/max-file
- cleanup schedule
- backup generations

採用する値はowner、根拠、適用範囲、rollbackを追跡する。

## 17. Completion Boundary

Design contract、read-only audit source、current Server audit result、cleanup mutation、backup runtime policyは別状態として扱う。

Current Runtime値は本Documentへ作業日誌として蓄積せず、必要時にaudit/readbackする。
