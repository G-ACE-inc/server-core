# SERVER STORAGE / LOG / CACHE LIFECYCLE

Version: 2026-09-30
Status: Design Baseline / Runtime thresholds NOT_VERIFIED

## 1. Purpose

Server上のLog / Cache / temporary state / backup / Docker storageを、所有者とRecovery条件を失わず安全に管理し、Disk肥大・誤削除・復旧不能を防ぐ。

Cleanupの目的は単に空きを増やすことではなく、**再生成・再送・復旧可能性が確認された不要データだけを削除すること**。

## 2. Command-Center Boundary

server-core司令室はWorkspace共通のStorage分類・Safety Gate・監査契約を定義する。

Project固有のretention / acknowledgement / recovery条件がより具体的な場合はProject側契約を優先する。

server-coreはProject固有Dataのownerにならない。

## 3. Data Classes

### Durable authority
長期保管または正本。generic automatic cleanup対象にしない。

### Rebuildable cache / index
再構築手段とSource authorityが確認できる場合だけcleanup候補。

### Temporary operational state
送信待ち、再送待ち、処理途中、Recovery用一時状態等。TTLだけで消さず状態条件を確認する。

### Backup
Retention policyとrestore確認を持つ。単なる古いFileとして掃除しない。

### Unknown ownership
自動削除禁止。

## 4. Common Storage Boundaries

| Storage | Role | Generic automatic delete |
|---|---|---|
| Telegram | owning Project契約で定義されたdurable raw-log authority | NO |
| Meilisearch | rebuildable search index | CONDITIONAL |
| Redis | dedup / hot cache | TTL / Project contract |
| `/home/admin1/logs` | temporary operational disk state | CONDITIONAL |
| Docker build cache | rebuildable build cache | CONDITIONAL |
| Docker image/container/network | runtime artifacts | ownership + runtime readback required |
| Docker volume | persistent/runtime state possible | NEVER by generic cleanup |
| `/home/admin1/backups` | backup area | retention + integrity + restore policy required |

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

`UNKNOWN` をPressureだけで `SAFE_TO_DELETE` へ昇格させない。

## 6. Log Lifecycle

Logは次を分離する。
- durable/audit authority
- runtime stdout/stderr
- transport outbox/retry
- debug/diagnostic
- temporary processing

Projectは必要に応じてowner、retention、rotation、shipping acknowledgement、delete conditionを定義する。

Container logを無制限成長させない。実装時はDocker logging driver/rotationのCurrent設定をreadbackし、実測とProject要件に基づいて上限を設定する。

## 7. Cache Lifecycle

CacheはSource of Truthではないことを確認する。

Cache削除後の再構築方法が無い場合、そのCacheは実質Durable Stateとして扱い、先にOwnership/Recovery設計を修正する。

Redis / Meilisearch / filesystem cache / package cache / build cacheを同一ルールで一括削除しない。

## 8. Docker Cleanup

禁止:
- scheduled generic `docker system prune -a --volumes`
- ownership未確認volume削除
- running/required imageを「unused」に見えるだけで削除
- rollback candidateを確認せずsuperseded image削除

自動化候補:
- dangling/rebuildable build cacheでage/ownership条件を満たすもの
- stopped containerでRecovery不要が確認済みのもの
- superseded imageでrunning/rollback参照なしが確認済みのもの

実装時はdry-run / candidate list / delete result / disk deltaを記録する。

## 9. Backup Lifecycle

Backupは最低限次を持つ。
- owner
- source
- retention generation/time
- integrity check
- restore target
- restore procedure
- restore verification

Backup cleanupは「新しいbackupが存在する」だけで行わず、integrityと保持世代を確認する。

## 10. Disk Pressure Guard

Pressure state:

```text
NORMAL
  -> WARNING
  -> HIGH
  -> CRITICAL
```

具体thresholdは実Server容量・Project使用量・growth rateを測定して決定する。このDesignへ推測値を固定しない。

Pressure時も優先順位は原則:

```text
verified rebuildable / expired safe data
  -> other verified safe temporary data
  -> manual decision boundary
```

Durable / recovery / unknown ownershipへ自動で進まない。

## 11. Read-only Audit Contract

Current source:
- policy: `operations/storage-lifecycle.json`
- implementation: `scripts/storage_lifecycle_audit.py`

Current policy boundary:

```text
mode = audit_only
allow_delete = false
docker.allow_prune = false
docker.allow_volume_delete = false
```

Auditは最低限次を収集できる設計にする。
- disk/filesystem usage
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

失敗時に「掃除完了」と報告しない。

## 13. Scheduling

Data classごとに頻度を分離し、全領域を1本の巨大Cleanup scriptで処理しない。

候補:
- frequent lightweight audit
- daily/weekly bounded cleanup
- pressure-triggered extra audit

実Serverのscheduler / container / systemd timer等を確認してから方式を選ぶ。重複schedulerを新設しない。

## 14. Recovery First

Cleanup対象が障害復旧に使われる可能性がある場合、Recovery完了または別authorityへのarchive/ship receiptを確認するまで削除しない。

## 15. Verification

Mutation実装後は少なくとも次を検証する。
- dry-runが実削除しない
- active/recovery/unknown dataをpreserve
- expired safe candidateだけ削除
- disk使用量が期待通り変化
-主要Serviceが継続稼働
- restore/rebuild対象は実際に復元可能
- repeated runがidempotentまたは安全

## 16. Runtime Parameter Gate

次の値は実測なしに文書へ固定しない。
- disk pressure threshold
- retention days/generations
- log max-size/max-file
- cleanup schedule
- backup generations

値を採用する場合はowner、根拠、測定Evidence、適用範囲、rollbackを追跡する。

## 17. Document / Runtime Completion Boundary

このMDはStorage lifecycleのDesign Contractとして完成可能であり、Server実測/cleanup mutation未実装とは別状態。

Current boundary:

```text
DESIGN_CONTRACT=DEFINED
READ_ONLY_AUDIT_SOURCE=IMPLEMENTED
LIVE_SERVER_AUDIT=NOT_VERIFIED
RETENTION_RUNTIME_VALUES=NOT_VERIFIED
CLEANUP_MUTATION=NOT_IMPLEMENTED
BACKUP_RUNTIME_POLICY=TARGET_SPECIFIC / NOT_FULLY_VERIFIED
```

## 18. Design Change Rule

この文書はBaseline。実Serverの現状に合わせるためだけに履歴を消す上書きをしない。正式変更は理由・Evidence・適用Commitを追跡する。