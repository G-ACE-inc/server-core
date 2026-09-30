# G-ACE REUSABLE DEVELOPMENT KB DESIGN

Version: 2026-09-30
Status: Design Baseline

## 1. Purpose

Master PCの `F:` 1 TB storageを、G-ACE開発で再利用できる検証済み資産・知識の共通KBとして運用する。

目的は情報を大量保存することではなく、Workspace内AIが既存資産を再利用し、新規生成・再調査・再検証・Token消費を減らすこと。

## 2. Ownership

- KB data/runtimeはserver-coreへ格納しない。
- server-coreはAccess / Registration / Lifecycle / Safety Contractだけを定義する。
- Master PC `F:` が予定Storage authority。
- Server/VPSからPC filesystemを直接読める前提を置かない。
- Workspace AIからの利用は、実装・検証済みAPI/MCP等のBridgeを通す。

## 3. Eligible Assets

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

生ログ、推測、未検証AI出力、Secret、Token、credentialは直接KB化しない。

## 4. Registration Contract

KB登録前に最低限判定する。

```text
SOURCE_IDENTIFIED=YES
OWNERSHIP_KNOWN=YES
REUSE_SCOPE_DEFINED=YES
VALIDATION_STATE=PASS | VERIFIED_WITH_LIMITS
SECRET_SCAN=PASS
VERSION_OR_REVISION_BOUND=YES when applicable
```

再利用価値がなくProject固有だけの一時情報は登録しない。

## 5. Asset Metadata

Assetごとに必要範囲で保持する。

- stable asset id
- title / purpose
- asset type
- source Project / repository / revision
- supported environment / version
- interface / input / output
- dependencies
- validation evidence summary
- limitations / incompatible cases
- reuse tags
- created / last verified timestamp
- supersedes / superseded-by relation

隠れた推論やraw chain-of-thoughtを保存しない。

## 6. Search / Retrieval

Searchは、最初からKB全体をPromptへ流さない。

```text
query
 -> metadata / index search
 -> ranked candidate ids
 ->必要Assetだけfetch
 -> source / revision / validation state確認
 -> reuse
```

検索結果が存在することと、現在Projectへ適用可能であることを分離する。

## 7. Reuse Priority

Workspace標準の順序:

```text
そのまま利用
 -> config / argument / type adjustment
 -> thin adapter
 -> common extraction
 -> new implementation
```

KB candidateは再利用候補であり、対象ProjectのCurrent Design / Interface / Versionより強いAuthorityではない。

## 8. MCP / API Bridge

Preferred target:
- read/search/fetchはMCPから利用可能
-必要ならAPIを内部Transportとして利用
-登録/更新/削除はreadより強い権限を分離

最低Capability候補:
- search assets
- get asset metadata
- fetch asset content / reference
- register validated asset
- mark superseded
- health / storage status

MCP/Bridgeが実装・疎通・権限検証されるまで `NOT_IMPLEMENTED` とする。

## 9. Safety

- Secret / Token / password / credential保存禁止
- repository-private資産は公開範囲を継承
- source revisionを失わない
- overwriteよりversion / supersedeを優先
- unknown ownershipを自動削除しない
- corruption検知なしに自動修復済み扱いしない

## 10. Storage Lifecycle

KBはCacheではないため、容量圧迫を理由にvalidated canonical assetを無条件削除しない。

削除候補:
- duplicate binary/cache
- superseded copyでcanonical relationが確認済み
- invalid import / incomplete transaction
- temporary staging data

削除はAsset metadata/indexとの整合性を確認して行う。

## 11. Backup / Recovery

F:単独障害を考慮し、実装時に次を決める。
- metadata/index backup
- asset backup strategy
- integrity hash
- restore procedure
- rebuildable index boundary

Backupが未実装なら `BACKUP=NOT_IMPLEMENTED` と明記する。

## 12. Non-goals

初期KBに以下を持たせない。
- 生ログ保管庫
- 全Repository mirror
- AI conversation archive
- Secret vault
- Runtime cache
- 未検証の自動知識化

## 13. Design Change Rule

この文書はBaseline。Current実装へ合わせて履歴を消す上書きをしない。正式なArchitecture変更は理由・Evidence・Commitを追跡可能にする。