# G-ACE REUSABLE DEVELOPMENT KB DESIGN

Version: 2026-10-01
Status: Design Baseline

## 1. Purpose

G-ACE開発で再利用できる**検証済み資産・知識**を、Workspaceから検索・取得・再利用できる共通KBとして扱うためのContractを定義する。

目的は情報量を増やすことではなく、既存資産の再利用、重複実装の削減、再調査・再検証Costの削減である。

## 2. server-core Boundary

server-coreはKB data本体、storage device、index実装を所有しない。

server-coreが所有するのは:
- KB discovery contract
- asset registration contract
- search/retrieval contract
- lifecycle / versioning rule
- credential/safety boundary
- bridge availability semantics
- Workspaceからowning KB runtimeへ到達するRouting

KB implementation/runtime/data/storage pathはowning Project/runtimeへ分離する。

## 3. Ownership

- KB data/runtimeはserver-coreへ格納しない。
- storage device/pathはowning KB authorityで定義する。
- Server/VPSから外部filesystemへ直接アクセスできる前提を置かない。
- Workspaceからの利用は、実装・検証済みAPI/MCP等の明示Bridgeを通す。
- Bridge availabilityはTask時のCurrent readbackで確認する。

複数のKB関連RepositoryまたはRuntimeが存在する場合でも、自動的に同一Authority扱いしない。統合/再利用はowner、purpose、data model、source authority、bridge、validation、backup/recovery responsibilityを確認してから行う。

## 4. Eligible Assets

登録対象候補:
- validated reusable code / module
- adapter / integration pattern
- schema / interface / contract
- test / fixture / benchmark pattern
- template
- verified operation / recovery procedure
- failure / root-cause / fix pattern
- official-source index / evidence route
- validated development knowledge

登録対象外:
- raw operational logs
- unsupported speculation
- unverified generated output
- Secret / Token / credential
- owner不明Data
- Project固有の一時状態だけで再利用価値がないもの

## 5. Registration Contract

```text
SOURCE_IDENTIFIED=YES
OWNERSHIP_KNOWN=YES
REUSE_SCOPE_DEFINED=YES
VALIDATION_STATE=PASS | VERIFIED_WITH_LIMITS
SECRET_SCAN=PASS
VERSION_OR_REVISION_BOUND=YES when applicable
LICENSE_OR_USAGE_BOUNDARY_KNOWN=YES when external asset
```

## 6. Asset Metadata

Assetごとに必要範囲で保持する。
- stable asset id
- title / purpose
- asset type
- source Project / repository / revision
- owner
- supported environment / version
- interface / input / output
- dependencies
- validation evidence summary
- limitations / incompatible cases
- reuse tags
- created / last verified timestamp
- supersedes / superseded-by relation
- visibility / usage boundary when applicable

## 7. Search / Retrieval

KB全体をContextへ流さない。

```text
query
  -> metadata/index search
  -> ranked candidate ids
  -> fetch only required assets
  -> confirm source/revision/validation/compatibility
  -> reuse
```

検索結果の存在とCurrent Projectへの適用可能性を分離する。

## 8. Reuse Priority

```text
そのまま利用
  -> config / argument / type adjustment
  -> thin adapter
  -> common extraction
  -> new implementation
```

KB candidateは再利用候補であり、対象ProjectのCurrent Design / Interface / Versionより強いAuthorityではない。

## 9. Bridge Contract

Bridge implementationはowning KB Project/runtimeが定義する。server-coreはWorkspaceから利用するために、少なくとも次を確認可能なContractを要求する。
- read/search/fetch interface
- writeがある場合のpermission分離
- registration/update時のvalidation gate
- health / availability確認方法
- failure behavior

Availability gate:

```text
OWNER_KNOWN=YES
STORAGE_RUNTIME_KNOWN=YES
METADATA_MODEL_VERIFIED=YES
SEARCH_VERIFIED=YES
FETCH_VERIFIED=YES
WRITE_PERMISSION_SEPARATED=YES when write exists
REGISTER_VALIDATION_GATE=YES when write exists
SECRET_BOUNDARY_VERIFIED=YES
BACKUP_RECOVERY_DEFINED=YES
WORKSPACE_BRIDGE_REGISTERED=YES
REPRESENTATIVE_REUSE_E2E=PASS
```

## 10. Safety

- Secret / Token / password / credentialをasset化しない
- private repository assetはvisibility/usage boundaryを継承する
- source revisionを失わない
- overwriteよりversion/supersedeを優先する
- unknown ownershipを自動削除しない
- corruption検知なしに修復済み扱いしない
- external assetはlicense/usage boundaryを保持する

## 11. Storage Lifecycle

KBはCacheではない。容量圧迫だけを理由にvalidated canonical assetを無条件削除しない。

削除候補:
- canonicalが別に存在するduplicate cache/binary
- superseded copyでrelation確認済み
- invalid import / incomplete transaction
- temporary staging data

削除前にmetadata/indexとの整合性を確認する。

## 12. Backup / Recovery

owning KB implementationは必要範囲で次を定義する。
- metadata/index backup
- asset backup strategy
- integrity check/hash
- restore target
- restore procedure
- representative restore verification
- rebuildable index boundary

server-coreはこのContractの存在/発見/availabilityを管理するが、backup data本体は保持しない。

## 13. Non-goals

Reusable KBは次の代替ではない。
- raw log保管庫
- 全Repository mirror
- conversation archive
- Secret vault
- Runtime cache
- unverified auto-generated knowledge dump

## 14. Completion Boundary

Design contract、KB storage/runtime、bridge、Workspace registration、backup runtimeは別状態として扱う。

Current implementation/runtimeの詳細はowning KB Project Authorityへ置き、server-core Designへdevice/path固有値や作業中状態を固定しない。

## 15. Design Change Rule

この文書はserver-core側の接続・再利用・安全Baseline。KB implementation architecture自体の変更はowning Project側Designを正とする。

server-core側の責務/contractが変わった場合は本Documentの更新要否を判定するが、それ自体はwrite permissionではない。実際に本Documentを変更するのは、server-core自体の変更についてexplicit owner authorizationがあり `SERVER_CORE_MUTATION_AUTHORIZED=YES` が成立した場合だけ。未成立なら必要変更を報告・提案する。
