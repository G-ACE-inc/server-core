# SERVER CORE KNOWLEDGE AND DECISION REGISTER

## 文書の役割
本ファイルは、Server Coreで確認された知識、判断理由、障害原因、解決方法を記録する。

本ファイルは再利用開発KB本体ではない。KB本体のDesignは `docs/KB_REUSE_DESIGN.md`、実データはserver-core外部に置く。

## 変更制御
管理者の明示的な変更指示がない限り、AI・作業者による書き換え・追記・削除・置換を禁止する。

質問、疑問、検討、提案は、追記承認として扱わない。

## 確認済み判断

### LibralCoreの正式定義
- LibralCoreは、開発AIが再利用可能な設計とCodeを効率よく生成・修正するための開発概念、設計方針、開発スタイルである。
- LibralCoreの目的は、既存資産の再利用によって開発時間、AIコンテキスト、Token、Code生成、修正、検証コストを削減し、効果を最大化することである。
- 5段 `Part → Feature → Component → System → Application System` は、開発AIが完成物を理解、分解、再利用、再構成するための論理構造である。
- Moduleは、同一Project内または別Projectで再利用、交換、独立修正しやすいように責務をまとめた開発上の再利用単位である。
- LibralCoreは、開発時の設計、Code生成、再利用、局所修正、検証範囲の限定に適用する。
- 実行順序は、目的と期待結果の確定、再利用候補の確認、必要範囲の5段整理、最小実装、期待結果と回帰の検証とする。

### 管理者権限
- ルールの最終決定者は管理者である。
- AIは管理者の明示指示なしに正本を変更しない。
- 作業履歴の正本はGitHub上のcommit / PRとする。
- ファイル変更を伴う作業は、作業完了時に意味のある作業単位でcommitを作成する。
- `PROJECT_STATUS.md` は作業履歴の保存先としない。
- READMEは入口、SERVER_CORE_PROTOCOLは共通運用規則、docs配下は設計・Routing・実務手順として役割を分離する。
- main merge、Production deploy、公開、Force push、Branch削除はMasterの明示指示なしに実行しない。

### Workspace Authority
- G-ACE Workspace内のAI / Developerは `server-core/README.md` を共通入口とする。
- 次に `docs/LOAD_SCOPE.md` でTaskをRoutingし、必要なAuthorityだけ読む。
- server-core正本を新Task開始時に一括読込しない。
- 対象ProjectではProject READMEを入口にし、必要なDesign / Tree / Delta / System Document / Source / Testだけ読む。

### GitHub作業履歴
- Commitは単なる保存ではなく、実作業と変更履歴を追う作業報告として扱う。
- Commit / Push / Remote Readback / PR / CI / Merge / Deploy / Runtime / Productionは別状態として扱う。
- Designとの差を正式採用した場合、CommitだけでなくDesign Deltaへ理由とEvidenceを残す。

### TGserver
- Telegramを生ログの永続正本とする。
- VPSは処理場であり、永続ログ保管庫ではない。
- Meilisearchは再構築可能な検索インデックスである。
- Redisはdedup / hot-cacheを担当する。
- TGserverは仕分け、配送、保存制御、検索を担当する。
- TGserverは意味判定を行わない。

### 共通分離キャッシュ
- `/home/admin1/logs` は全体共通の分離ディスク一時領域である。
- 送信待ち、再送、処理途中、障害時一時退避など、削除条件を定義できるOperational Stateに限定する。
- 永続ログ、監査正本、Telegram原本の長期複製、KB、仕様書、Source Codeには使わない。
- Redisのhot-cacheとは別責務である。
- Cleanup / Retention / Backup / Recoveryの共通設計は `docs/STORAGE_LIFECYCLE.md` を正とする。

### 再利用開発KB
- KB runtime / bridgeは現在 `NOT_IMPLEMENTED` である。
- 実データのTarget StorageはMaster PCの `F:` 1 TB driveとする。
- 目的はvalidated reusable code/module/pattern/schema/interface/test/template/procedure/development knowledgeを蓄積し、Workspace内AIが再利用できるようにすること。
- server-coreにはKB data本体を置かず、Access / Registration / Lifecycle / Safety Contractだけを持たせる。
- VPSからPC `F:` を直接読める前提を置かない。実装・検証済みAPI/MCP等のBridgeを使用する。
- TGserverからKBへ生ログを直接送信しない。
- 生ログやV8推論結果を無判定で自動投入しない。
- 未検証AI出力、Secret、Token、credentialをvalidated KB assetとして登録しない。
- 登録条件・検索・version/supersede・backup/recoveryのDesign Baselineは `docs/KB_REUSE_DESIGN.md` とする。

### Shared MCP / Tool
- Workspace共通Capabilityの発見入口は `docs/WORKSPACE_REGISTRY.md`。
- Registryに記載されているだけで実利用可能と断定しない。
- Cloudflare API MCPは `.cursor/mcp.json` に登録済みである。
- DebugAIのCurrent verified shared accessはCLI / HTTPである。
- DebugAI MCPはDebugAI側の実装・検証・Workspace登録が閉じるまで `NOT_IMPLEMENTED` とする。
- Reuse KB MCPもBridge実装・検証まで `NOT_IMPLEMENTED` とする。

### Astera v8
- Astera v8は `/home/admin1/projects/astera_v8` に配置する。
- Astera v8は問いの意味判定、認知前処理、用途テンプレート自動判定、5本柱処理、8段判断材料出力を担当する。
- Astera v8はTGserverへ `P002` として構造化ログを送信する。
- Astera v8の未送信ログ一時状態は `/home/admin1/logs/astera-v8/outbox` に限定する。
- Astera v8の推論結果を無判定でKBへ自動投入しない。

### 秘密情報
- `.env` は原則commit禁止である。
- 共有が必要な環境変数は、値を含まない `.env.example` に記載する。
- Workspace共有Secretは値を各Projectへ複製せず、既存Broker/Vault契約を使う。
- 秘密情報の漏洩が疑われる場合は、該当credentialの失効または再発行を優先する。

## 運用上の教訓
- 未確認の事実をCurrent状態文書へ書かない。
- 実行していない処理を完了と記録しない。
- RegistryとRuntime readbackを混同しない。
- 状態、履歴、Design、Current仕様を混同しない。
- 生ログ、cache、index、knowledge assetを混同しない。
- 再利用可能性を確認する前に新規Code / Module / Documentを増やさない。
