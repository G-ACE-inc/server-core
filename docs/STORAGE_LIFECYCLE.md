# SERVER STORAGE / LOG / CACHE LIFECYCLE

Version: 2026-09-30
Status: Design Baseline

## 1. Purpose

Server上のLog / Cache / temporary state / backup / Docker storageを、所有者とRecovery条件を失わず自動管理し、Disk肥大・誤削除・復旧不能を防ぐ。

Cleanupの目的は「空きを増やすこと」ではなく、安全に再生成・再送・復旧できる不要データだけを削除すること。

## 2. Data Classes

### Durable authority
長期保管または正本。自動Cleanup対象にしない。

### Rebuildable cache / index
再構築手段とSource authorityが確認できる場合だけ自動Cleanup候補。

### Temporary operational state
送信待ち、再送待ち、処理途中、Recovery用一時状態等。TTLだけで消さず、状態条件を確認する。

### Backup
Retention policyとrestore確認を持つ。単なる古いFileとして掃除しない。

### Unknown ownership
自動削除禁止。

## 3. Current Common Boundaries

| Storage | Role | Automatic delete default |
|---|---|---|
| Telegram | Project契約で定義されたdurable raw log authority | NO |
| Meilisearch | rebuildable search index | CONDITIONAL |
| Redis | dedup / hot cache | TTL / Project contract |
| `/home/admin1/logs` | temporary disk operational state | CONDITIONAL |
| Docker build cache | rebuildable build cache | CONDITIONAL |
| Docker image/container/network | runtime artifacts | ownership/readback required |
| Docker volume | persistent/runtime state possible | NEVER by generic cleanup |
| `/home/admin1/backups` | backup area | retention + restore policy required |

Project固有契約がより具体的な場合は、その契約を優先する。

## 4. Safe Deletion Gate

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

## 5. Log Lifecycle

Logは次を分離する。
- durable/audit authority
- runtime stdout/stderr
- transport outbox/retry
- debug/diagnostic
- temporary processing

Projectは必要な場合、owner、retention、rotation、shipping acknowledgement、delete conditionを定義する。

Container logは無制限成長させない。実装時はDocker logging driver/rotationのCurrent設定をreadbackし、Project要件に合う上限を設定する。

## 6. Cache Lifecycle

CacheはSource of Truthではないことを確認する。

Cache削除後に必要な再構築方法がない場合、そのCacheは実質Durable Stateとして扱い、先に設計を修正する。

Redis / Meilisearch / filesystem cache / package cache / build cacheを同一ルールで一括削除しない。

## 7. Docker Cleanup

禁止:
- generic scheduled `docker system prune -a --volumes`
- ownership未確認volume削除
- running/required imageを「unused」に見えるだけで削除

自動化候補:
- dangling build cacheでage/ownership条件を満たすもの
- stopped containerでProject側Recovery不要が確認済みのもの
- superseded imageでrunning/rollback参照なしが確認済みのもの

実装時はdry-run / candidate list / delete result / disk deltaを記録する。

## 8. Backup Lifecycle

Backupは最低限次を持つ。
- owner
- source
- retention generation/time
- integrity check
- restore target
- restore procedure / verification

Backup cleanupは「新しいbackupが存在する」だけで行わず、最低限integrityと保持世代を確認する。

## 9. Disk Pressure Guard

Resource pressureによるCleanupは段階化する。

```text
NORMAL
 -> WARNING
 -> HIGH
 -> CRITICAL
```

具体的thresholdは実Server容量・Project使用量を測定して決定し、このDesignで推測固定しない。

優先削除順は、原則としてrebuildable / expired / verified-safeなものから。Unknown ownershipやdurable dataへPressureだけを理由に進まない。

## 10. Automation Contract

Cleanup automationは少なくとも以下を出力する。
- run id / timestamp
- disk before / after
- candidate count / bytes
- deleted count / bytes
- preserved count / reason
- UNKNOWN / blocked items
- errors

失敗時に「掃除完了」と報告しない。

## 11. Scheduling

定期実行頻度はData classごとに分離する。全領域を1本の巨大Cleanup scriptで処理しない。

実装候補:
- frequent lightweight audit
- daily/weekly bounded cleanup
- pressure-triggered extra audit

Server実装時は既存scheduler / container / systemd timer等を確認してから方式を選ぶ。重複schedulerを新設しない。

## 12. Recovery First

Cleanup対象が障害復旧に使われる可能性がある場合、Recovery完了または別authorityへのarchive receiptを確認するまで削除しない。

## 13. Verification

自動化実装後は少なくとも次を検証する。
- dry-runが実削除しない
- active/recovery/unknown dataをpreserve
- expired safe candidateだけ削除
- disk使用量が期待通り変化
-主要Serviceが継続稼働
- restore/rebuild対象は実際に復元可能
- repeated runがidempotentまたは安全

## 14. Design Change Rule

この文書はBaseline。実Serverの現状に合わせるためだけに履歴を消す上書きをしない。正式変更は理由・Evidence・適用Commitを追跡する。