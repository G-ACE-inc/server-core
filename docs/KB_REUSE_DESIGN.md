# G-ACE REUSABLE DEVELOPMENT KB DESIGN

Version: 2026-10-03
Status: Design Baseline / Runtime NOT_IMPLEMENTED

## 1. Purpose

Master PCの `F:` 1 TB storageを、G-ACE開発で再利用できる検証済み資産・知識の共通KBとして運用する。

目的は情報を大量保存することではなく、Workspace内AIが既存資産を再利用し、新規生成・重複実装・再調査・再検証・Token消費を減らすこと。

## 2. Command-Center Boundary

server-core司令室はKB data本体、index実装を所有しない。

server-coreが所有するのは:
- KB discovery contract
- asset registration contract
- search/retrieval contract
- lifecycle / versioning rule
- safety / Secret boundary
- bridge availability state
- Workspaceからの利用Routing

KB implementation/runtime/dataは別ownerへ分離する。

## 3. Ownership

- KB data/runtimeはserver-coreへ格納しない。
- Master PC `F:` が予定Storage authority。
- Server/VPSからPC filesystemを直接読める前提を置かない。
- Workspace AIからの利用は、実装・検証済みAPI/MCP等のBridgeを通す。
- Bridgeが無い間は `NOT_IMPLEMENTED / NOT_AVAILABLE` を維持する。

複数のKB関連RepositoryまたはRuntimeが存在する場合でも、自動的に同一Authority扱いしない。統合/再利用はowner、purpose、data model、source authority、bridge、validation、backup/recovery responsibilityを確認してから行う。

## 4. Existing KB-related Repositories

Workspace Registryには既存KB関連Repositoryが存在する場合がある。

例:
- `seigo-gace/astera-kb`
- `seigo-gace/kb-system`
- `seigo-gace/gace-dev-kb`

これらをMaster PC `F:` reusable-development KBと自動的に同一Authority扱いしない。

統合/再利用する場合は事前にowner、purpose、data model、source authority、migration path、API/MCP bridge、validation state、backup/recovery responsibilityを決める。

既存資産を確認せず新規KB実装を増やさない。

## 5. Eligible Assets

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

直接登録禁止:
- raw operational logs
- unsupported speculation
- unverified generated output
- Secret / Token / credential
- owner不明Data
- Project固有の一時状態だけで再利用価値がないもの

## 6. Registration Contract

```text
SOURCE_IDENTIFIED=YES
OWNERSHIP_KNOWN=YES
REUSE_SCOPE_DEFINED=YES
VALIDATION_STATE=PASS | VERIFIED_WITH_LIMITS
SECRET_SCAN=PASS
VERSION_OR_REVISION_BOUND=YES when applicable
LICENSE_OR_USAGE_BOUNDARY_KNOWN=YES when external asset
```

## 7. Asset Metadata

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

## 8. Search / Retrieval

KB全体をContextへ流さない。

```text
query
  -> metadata/index search
  -> ranked candidate ids
  -> fetch only required assets
  -> confirm source/revision/validation/compatibility
  -> reuse
```

検索結果が存在することとCurrent Projectへ適用可能であることを分離する。

## 9. Reuse Priority

```text
そのまま利用
  -> config / argument / type adjustment
  -> thin adapter
  -> common extraction
  -> new implementation
```

KB candidateは再利用候補であり、対象ProjectのCurrent Design / Interface / Versionより強いAuthorityではない。

## 10. MCP / API Bridge

Preferred target:
- read/search/fetchはMCPから利用可能
- 内部TransportとしてAPI利用可
- register/update/deleteはreadより強い権限へ分離

Bridge completion gate:

```text
STORAGE_INITIALIZED=YES
METADATA_MODEL_VERIFIED=YES
SEARCH_VERIFIED=YES
FETCH_VERIFIED=YES
WRITE_PERMISSION_SEPARATED=YES
REGISTER_VALIDATION_GATE=YES
SECRET_BOUNDARY_VERIFIED=YES
BACKUP_RECOVERY_DEFINED=YES
WORKSPACE_REGISTRATION_VERIFIED=YES
REPRESENTATIVE_REUSE_E2E=PASS
```

未完了なら `AVAILABLE_VERIFIED` としない。

## 11. Safety

- Secret / Token / password / credentialをasset化しない
- private repository assetはvisibility/usage boundaryを継承する
- source revisionを失わない
- overwriteよりversion/supersedeを優先する
- unknown ownershipを自動削除しない
- corruption検知なしに修復済み扱いしない
- external assetはlicense/usage boundaryを保持する

## 12. Storage Lifecycle

KBはCacheではない。容量圧迫だけを理由にvalidated canonical assetを無条件削除しない。

削除候補:
- canonicalが別に存在するduplicate cache/binary
- superseded copyでrelation確認済み
- invalid import / incomplete transaction
- temporary staging data

削除前にmetadata/indexとの整合性を確認する。

## 13. Backup / Recovery

実装時に必須:
- metadata/index backup
- asset backup strategy
- integrity check/hash
- restore target
- restore procedure
- representative restore verification
- rebuildable index boundary

Backup未実装なら `BACKUP=NOT_IMPLEMENTED` と明記する。

## 14. Non-goals

初期KBに以下を持たせない。
- raw log保管庫
- 全Repository mirror
- conversation archive
- Secret vault
- Runtime cache
- unverified auto-generated knowledge dump

## 15. Document / Runtime Completion Boundary

このMDはKBのDesign Contractとして完成可能であり、KB runtime未実装とは別状態。

Current boundary:

```text
DESIGN_CONTRACT=DEFINED
F_DRIVE_RUNTIME=NOT_IMPLEMENTED
API_MCP_BRIDGE=NOT_IMPLEMENTED
WORKSPACE_REGISTRATION=NOT_IMPLEMENTED
BACKUP_RUNTIME=NOT_IMPLEMENTED
```

Runtime実装後はCurrent implementationへ合わせてDesign履歴を消さず、差分がある場合はserver-coreまたはowning ProjectのDesign Deltaへ記録する。

## 16. Design Change Rule

この文書はBaseline。Current実装へ合わせて履歴を消す上書きをしない。正式Architecture変更は理由・Evidence・適用Commitを追跡可能にする。

本Documentを変更するのは、server-core自体の変更についてMasterの明示許可があり `SERVER_CORE_MUTATION_AUTHORIZED=YES` が成立した場合だけ。
