# PROJECT INTEGRATION RULES

Version: 2026-10-31
Role: Projectへ共通基盤を導入するときの接続・利用ルール。

## Purpose

server-coreは共通Capabilityの司令室であり、Project固有実装は所有しない。

本Documentは、各Projectが共通基盤を利用するときの導入契約を定義する。

## 開始時の入口

新規Repoの登録・既存Projectの導入・Vault/TGserver/Gateway接続開始では、本書の[Project開始・登録runbook（両Host共通）](#project開始登録runbookcontabo--gserver共通)を実行する。利用／提供元変更の境界とAPI詳細の所有権は以下を正本とする。

## Shared service usage and change boundary

**適用対象:** GPT CHAT、SERVER_AI、設定済みサブエージェント、自動処理を含む全実行主体。webhook-gateway、Libral Vault、TGserverおよび今後の共通サービスの利用・接続・提供元変更に適用する。本節が共通の利用／変更境界の正本であり、各サービスのAPI詳細・管理手順・Runtime状態は提供元Repository／Currentが所有する。

1. **利用と変更の権限を分離する。** 利用側Projectの開発・接続・障害対応の依頼や、技術判断の一任は、提供元の実装・共通設定・認証・配送・保存仕様を変更する許可ではない。特定Projectの都合で提供元を無断変更・専用化し、既存利用者の動作を変えてはならない。server-coreを管理入口にしても、提供元の所有権は移らない。
2. **正式な接続契約を使用する。** 提供元が定めたAPI又はMCPを使い、内部DB・保存ファイル・非公開関数・GPG等の内部部品を直接利用／操作して代用しない。提供元が正式に公開するModule APIや、それを使う既存の管理CLI・provisionerは接続契約に含む。APIとMCPの両方の新設や、新たなHTTPサービスの設置を義務化しない。接続口が未提供・不明なら、実装や利用可能状態を推測せず、提供元の契約確認又は拡張案の提示を行う。読取診断は許可された範囲で可能だが、内部状態の直接読取を製品の通常接続口にしない。
3. **承認済みの管理操作は維持する。** 既存手順で許可されたProject／Topic／配送先の登録、キー管理等は、その対象・権限・手順内で実施できる。管理CLIが正本設定ファイルを更新すること自体は禁止しない。ただし既存利用者の割当・ポリシー・共有既定値の変更、直接ファイル編集による迂回、権限拡大はその登録権限に含まれない。Secret・Host・ドメイン等の個別承認境界も維持する。
4. **提供元の変更は事前提案と明示承認を要する。** 接続契約内の利用側対応で解決できない場合は、提供元Owner／Current、変更理由、対象・具体案、既存利用者への影響、互換性確認、移行・復旧方法を示し、Masterの明示許可後に提供元の変更として別の範囲を確定する。Masterから直接依頼された提供元開発や、既に明示承認された提供元変更は、その範囲で通常の実装・検証を継続し、各編集で再承認を要求しない。利用側の包括的な改善依頼や過去の別件許可を、提供元変更の承認へ読み替えない。承認待ちはその変更だけを止め、独立した許可済み作業は継続する。
5. **既存契約を保護する。** 既存のAPI／MCP／設定の意味、認証境界、データ、配送先、Project／Topic識別子を保存する。破壊的変更は明示承認された移行計画・必要な版分け／移行期間・復旧策なしに適用しない。特定利用者の成功で他利用者への影響確認を代用しない。影響範囲の既存契約との互換性を検証し、Source・CI・Runtimeを分けて記録する。利用者一覧や稼働状態が不明ならUNKNOWNとして残し、影響なしと断定しない。
6. **契約と運用方法を提供元で管理する。** 接続先の発見方法、対応版、認証・権限、入力／出力、制限、エラー、再試行・重複処理、登録・設定反映、更新・廃止・復旧方法を該当する範囲で明示する。server-coreは正本への参照と管理入口を持ち、API仕様や実Topic台帳、Secretを複製しない。仕様の記載だけで接続・配送・保存完了と扱わない。
7. **適用範囲を混同しない。** 本節は既存・承認済みの共通サービスを安全に利用・変更する規則であり、全製品への内部／外部商用機能の追加や外部公開を命じるものではない。内部利用・外部商用を設計時に考慮する手順はGPT CHAT [Rule #17](https://github.com/G-ACE-inc/server-core/issues/17)のみが所有し、提供範囲・優先順位・公開可否はMasterの判断に従う。SERVER_AIへGPT CHATのNotion・会話・設計検討手順を追加しない。別AI・サブエージェント・CIを経由して本節の変更境界を迂回してはならない。

## TGserver Integration

TGserverはProject導入時の通信・記録基盤として利用する。

導入時に定義する:

- Project identifier
- Topic naming
- Topic creation reason
- Log / notification category
- Severity level
- Retention policy
- Failure handling

TGserver ZEROの新規登録・上限・復旧・Runtime反映の正本は、所有Repoの [TGSERVER_ZERO_OPERATIONS.md](https://github.com/seigo-gace/TGserver/blob/main/docs/TGSERVER_ZERO_OPERATIONS.md)。Repo/stream対応表、Live Registry、Live Topic台帳、system収集対象を先に既存 `topics:onboarding-audit` で照合する。Reader mapの未登録や検索0件をTopic不存在と読み替えず、既存番号・バックアップ・Provider履歴を確認する。

1 Groupの運用上限は10 Project、各Project標準5 severity。20通/分は送信予算でありTopic数上限ではない。満杯Groupへの追加、一括Topic新設、既存Topicの削除・再作成で解決しない。system収集とCanonical開発ログは別Producerとして登録・実測し、コンテナのないProjectへ架空のsystem sourceを追加しない。

新規導入はRegistry／表示名／Repo+stream map／必要なsystem manifestを加算同期し、起動時読込のRegistryと開発ログ対応表をRuntimeでも照合する。Source登録、台帳一致、Gateway受領、Telegram保存、Reader検索を別判定にし、同一eventIdの実配送まで確認する。CHATからサーバーAIへこの作業を委任する場合は、既存どおりMasterの個別許可が必要。必要なTopicのみ追加し、用途不明のTopicを作成しない。

### TGserver ZERO v1.5 実Runtime・Topic台帳の運用契約

Gateway同様、TGserverは**Source・稼働Runtime・Telegram Providerの物理Topic**を別のAuthorityとして扱う。詳細の所有者はTGserver側の [ZERO Operations](https://github.com/seigo-gace/TGserver/blob/main/docs/TGSERVER_ZERO_OPERATIONS.md) とし、本契約で全Project導入時の必須条件を共通化する。変更状況と実証は [TGserver Current #50](https://github.com/seigo-gace/TGserver/issues/50) で確認する。過去PR番号を現行実装やRuntime反映の証拠にしない。

管理入口は `python3 /home/admin1/server-core/scripts/tgzero_admin.py`。初動は `lookup --repo OWNER/REPO --stream STREAM` で既存Project番号・Topic ID・実機上の正本ファイルを確かめ、通常の追加依頼は `register --request /private/request.json` でSource登録→既存provisioner→既存Compose反映→実プロセス読込SHA照合まで進める。Group登録は `register-group`、照合は `runtime-status`。発見契約は `operations/tgzero-registration.json` とし、server-coreへ二重台帳を作らない。低位のplan/apply/provisionは復旧用で、チャットへ毎回手動分割を要求しない。未確認の既存欠落を新設で埋めず、失敗後は同じrequestの保存済み処理を再開する。登録用の管理反映以外のenv/mount変更、Project移動、無人Group作成、別AI起動を許可しない。詳細schema・正本5ファイル・rollbackはTGserver ZERO Operationsのみで管理する。

- **台帳の役割:** `storage-registry.json` = Project/Groupの承認済み割当、VPS Live `.tgs-state/topics.json` = Topic ID/Router向け現行State、Telegram Group = 実物Topic。GitHubにあるTopic stateは本番実IDの証拠ではない。Group ID、Topic ID、旧Projectの割当は推測しない。
- **既存資産を優先:** 新設・改名よりも、まずLive State、過去の実バックアップ、Providerの既存Topic IDと実履歴を照合する。Stateから欠落していてもProvider Topicが消滅したと推定しない。既存Topicの再作成・丸ごとState置換・Projectの重複追加は禁止。既存65/70ルート完成等の歴史Evidenceと現Liveが不一致の場合は `STATE_HISTORY_DIVERGED` として保護変更を停止し、読取監査で回復候補を作る。
- **番号と画面表示は別:** 内部 `Pxxx` / `Pxxx_severity` キーと既存 `topic_id` を保持し、Telegram UIは `P013｜Webhook Gateway｜エラー` / `P014｜G-ACE 開発KB｜警告` のようにProject名とLog区分を示す。表示名を変更する際は実Providerの既存Topic IDに対する改名だけを使用し、既存Topicの新設・削除はしない。Source表示名を修正したことをProvider改名完了と扱わない。
- **上限の混同禁止:** Telegramの既存ZERO設計は1 Group **20通/分**の送信予算、通常1 Group最大10 Projects × 5 severity。20 Topic上限ではない。開発が行われない期間のLog 0件は故障ではない。
- **保護された変更:** 新Project/Topic追加時は単一Projectスコープ、事前のread-only監査、Live State・BackupのSHA256/readback、既存Routeへの非破壊差分、Provider重複防止、rollbackを揃える。Topicの一括Provision、未確認Topicの機械的再作成、Secretの公開やAPIの無断外部公開は禁止。Registry反映後は必要な既存TGserverの管理されたrestart/readbackを別途確かめる。
- **証拠の段階:** `SOURCE_REGISTERED`→`LIVE_REGISTRY_LOADED`→`TOPIC_ID_MATCH_VERIFIED`→`DISPLAY_TITLE_VERIFIED`→`GATEWAY_RECEIVED`→`TGS_ACCEPTED`→`TELEGRAM_RAW_VERIFIED`→`SEARCH_VERIFIED`。Gateway 202・legacy TGS accepted・Meili hit単独をTelegram原本保存と混同しない。0件検索も不存在証明ではない。登録Projectが休止中なら`NO_PRODUCER_ACTIVITY`と障害を区別する。
- **責務:** TGserverのRuntime台帳とProvider操作はTGserver Owner、Gateway配送設定と認証はGateway Owner、Producerアプリのイベント作成は対象Project Owner。CHATは横断整合とCurrent記録を担う。プロジェクト別変更と実サーバー効果の許可境界を混同しない。



## Cloudflare domain boundary (Master fixed 2026-10-29)

Cross-project deployment, Gateway Producer integration, DNS/Tunnel/Access changes and outgoing live tests must respect the **owning product domain**, not merely a working shared URL.

- Gserver and general G-ACE applications use the designated **G-ACE primary domain**; the **Astera product domain** (including its subdomains) is reserved for Astera-related applications only.
- Using any Astera-owned domain/hostname for a non-Astera application, even through the existing shared Webhook Gateway, **requires the Master's explicit *advance* approval for the named host, purpose, and effects**. A prior 202, Cloudflare Access credential, DNS record, working Tunnel, older CHAT instruction or successful SSH test is **not** approval.
- For each new connection or live test, resolve its owner, hostname, private route, Access policy and Gateway Bearer separately. If owner/permission is unverified, do not send traffic, persist credentials, deploy or add a public route. Continue independent project work and ask only for the protected domain exception when truly needed.
- **Do not destroy or retarget existing Astera DNS/Tunnel/Access** to solve an ownership violation. Reuse the same Gateway application and its `POST /internal/events`, Event/Delivery/Outbox and Worker; split only the access path when necessary, not the Gateway product.
- The exact domain map belongs to the private Gserver/Gateway integration Current and authorized private deployment contract. [Notion Gserver/TGserver handoff](https://app.notion.com/p/407cdcf128e4810f9fc8d7f3d97aba8c) under "Cloudflareドメイン所有区分・Gserver優先・事前承認" is GPT CHAT context/history, not a SERVER_AI read/write prerequisite. SERVER_AI verifies an accessible owner Current/repository contract or authorized Host configuration; if unavailable, keep DOMAIN_OWNER_UNVERIFIED and hold only that domain operation. Do not copy active Hostnames or Secrets to public Source/issues. Use only the applicable [Rule #16](https://github.com/G-ACE-inc/server-core/issues/16) or [Rule #17](https://github.com/G-ACE-inc/server-core/issues/17).
- Past Gserver-to-Astera-zone canary evidence remains historical fact. It does not authorize any **new** cross-zone send, even a read-only-looking HTTP probe. Live migration/activation is NOT_VERIFIED until the correct G-ACE path is tested and allowed.

## webhook gateway Integration

webhook gatewayはEvent連携入口として利用する。

導入時に定義する:

- Event name
- Producer
- Consumer
- Endpoint contract
- Payload schema
- Authentication method
- Retry behavior
- Failure handling

### Internal Event API 利用契約

内部Producerは既存の `POST /internal/events` を使用する。API仕様の正本は [webhook-gateway / INTERNAL_EVENT_API.md](https://github.com/seigo-gace/webhook-gateway/blob/main/docs/INTERNAL_EVENT_API.md)、実装は同Repositoryの `src/system/internal-event-api.ts` と配送先設定とする。導入・変更時だけ該当範囲を確認し、Sourceの対応を稼働環境へ推測で適用しない。

- **発行主体と利用単位**：server-coreを司令室として、GPT／SERVER_AIが許可済みの発行・運用範囲内で既存Gatewayの生成手段を使い、内部Projectごとに独立したAPIキーを発行・登録・更新・失効する。旧共通キー1本を全Projectへ使い回す運用を新規導入の前提にしない。API利用の衝突を調査する際はキーの利用単位と `sourceId + eventId` の重複を分けて確認する。キー分離だけでevent ID競合や宛先権限の分離が保証されるとは扱わない。発行・登録の実値は既存Secret注入経路だけで扱い、会話・Git・ログへ残さない。
- **認証**：既存 `INTERNAL_EVENT_API_TOKEN` と任意の `INTERNAL_EVENT_API_PROJECT_KEYS_JSON` に登録したプロジェクト別キーを、同じ `Authorization: Bearer ...` または `x-internal-api-token` で利用する。既存 `npm run secret` で生成し、実値はprivate deployment環境へ注入する。キー名は運用ラベルであり、プロジェクト別の宛先権限・scope・bodyの本人性を保証しない。新しいログイン・承認・キー発行HTTP APIは作らない。環境変更の反映には既存APIプロセスの再起動／再デプロイが必要で、旧共通キーは別途廃止するまで有効。
- **宛先とdata**：呼出側は登録・有効化済み `destinationId` とAPI schemaのevent/dataを指定する。URL・credential・outbound header・retry policyはdeployment所有とする。`payloadMode=json` は `data` のみを配送するが、原文保持を意味しない。`internalDataPolicy` 省略／`sanitize` は従来の秘匿置換・文字列制限、`preserve` は完全な内部data保持であり、JSON配送・private-network許可・署名付き配送先への明示設定が必要。callerはこのpolicyを選べず、ログ・audit・errorの秘匿は維持する。コマンドへcredential実値を埋め込まない。
- **受領と重複**：`202` はEvent／Delivery／OutboxのDB commit済み受領であり、配送・Host実行・TGserver保存完了ではない。`sourceId + eventId` を重複キーとし、新規受付のfingerprintはその宛先policy適用後の意味内容を対象とする。同一キー・同一内容はduplicate、異なる内容は `409 IDEMPOTENCY_KEY_PAYLOAD_CONFLICT`。fingerprintのない旧行は旧duplicate動作を維持する。policy変更後の409を新IDの自動再送で回避せず、元操作の実行状態を確認する。
- **反映証拠**：Source／CI／Runtimeを分離し、適用済みimage・設定・env注入を対象環境で確認する。実機だけの配送先を保存し、Sourceだけの配送先を意図せず有効化しない。利用可否・原文一致・最終結果は対象Currentと実配送証拠で確認し、仕様追記だけでAVAILABLE_VERIFIEDへ昇格しない。

## Libral Vault Usage

Libral Vaultはserver-core共通Capabilityであり、Project利用契約は本Documentで定義する。

Project側で管理する:

- Required secret contract identifier
- Consumer service
- Injection point
- Runtime usage

Secret実値は保存しない。

## MCP / Tool Usage

ProjectがMCPまたはToolを利用する場合:

- Owner
- Interface
- Permission boundary
- Mutation boundary
- Verification method

を明確化する。

## Registration

導入後:

- Workspace Registry更新
- Project README更新
- Design Delta記録
- Verification結果記録

を行う。


## Project開始・登録runbook（Contabo / Gserver共通）

この節は新規Repo、既存RepoのWorkspace導入、共通サービスの接続開始・変更時に必ず使う。通常の小さな修正で全仕様の再読込を要求せず、所有Currentと変更に必要な契約だけを更新確認する。APIの完全なschema・実装・Runtime台帳は各所有Repoが正本であり、本手順へ複製しない。

### 1. 開始前：目的・場所・実行者を固定する

1. server-core README → LOAD_SCOPE → Rule Plane Manifest → 適用Profile → 所有Current → 対象README/設計を確認する。Codex/Composer/SERVER_AIは#16、GPT CHATは#17。別Profileの確認票を自分の実行証拠として作らない。
2. Owner/Repo、目的、既存CU、Mutation Owner、branch/PR、実HEAD、dirty/stash、正規Project親と実checkoutを確認する。同じ仕事の既存Repo/CUがあれば再利用し、日付名・タスク名の兄弟Projectを増やさない。
3. `Host target`をContaboかGserverか明示する。Workspace表示名、同じRepo名、成功した過去URLをHost実行権限に読み替えない。Gserverの通常Core/Storage/appはGitHub/Contabo不通でも動く設計を維持する。
4. 新しい独立Projectの作成意図と、公開範囲・費用・外部効果の許可を確認してから作成する。文書整備や「登録方法を調べる」という依頼だけで新Repo/Topic/キーを作らない。通常の承認済み実装は再確認で止めない。

### 2. 登録は用途ごとに別々に照合する

| 登録面 | 正本・操作 | 登録だけでは得られないもの |
|---|---|---|
| GitHub Repo | Ownerの既存Repoを先に検索し、必要時のみ既存GitHub認証で作成。README、Current Issue、既存branch/PRを確定 | Project #1登録、Host実行権限 |
| GitHub Project #1 | 既存ItemをURLで照合し、未登録時だけ正規GitHub UI/API/既存`gh project item-add`で同じCurrent Issueを追加。ProjectのOwner/番号/Itemをreadback | Issue作成だけでProject登録済みとはしない。4 Control Field更新CLIはItem追加の代替ではない |
| Workspace | `WORKSPACE_REGISTRY.md`にOwner/Repo/用途/確認済みHost入口を登録。既存親内の正規checkoutか承認されたnested worktreeを使い、origin/toplevel/Git common-dirを照合 | cloneやフォルダ表示から遠隔権限を推定しない |
| ServerTerminal | 既存`operations/github-project-bounded-host.json`とHost-local admissionを対象Hostで照合。read-only/dev.job/host.command/reflect/deployを個別評価 | `dev.job`登録はHost shell/本番Deployの許可ではない。保護Registryへ権限を一括追記しない |
| TGserver | 既存Repo+streamをlookupし、必要な登録だけ正式管理CLIから実施 | Topic新設、原本保存、検索完了 |
| Gateway | 正式な既存destination、data policy、Project用認証、到達経路をOwnerと照合 | APIキー名からdestination別権限を推定しない |
| Vault | 既存secret ID、allowed consumer、TTL、許可origin、注入方法を正式契約で照合 | Repo/Project登録はSecret利用許可ではない |

GitHub Item追加のCLI例は、既存`gh`が認証済みで、対象Issueと登録先を確認した場合だけ使う。例中の値をそのまま本番へ送らない。

```text
既存Item一覧でCurrent Issue URLを照合
→ 未登録の場合のみ gh project item-add <確認済み番号> --owner <確認済みOwner> --url <Current Issue URL>
→ 同じProject/Issue URLのItem IDと既存Fieldをreadback
```

Repo名変更・移動・廃止では、Project Item、Host root、Repo+stream map、Producer sourceId、destination、Vault consumerの影響を個別確認する。同じ名前へ新規作成して旧割当を乗っ取らない。

### 3. Host別の入口・実行・配置

| 項目 | Contabo | Gserver |
|---|---|---|
| server-core | Registryで確認する既存VPS checkout | 同じupstreamを参照する既存WSL checkout。別指令室/別Rule Planeを作らない |
| Project root | 実VPSの登録済み親/root | 実WSLの既存親/root。Windows drive/旧copyを勝手に移動しない |
| 実行 | SERVER_AIは検証済みの非root SSH/既存ローカルtool。GPT CHATは既存Actions→Gateway→Receiver→Writer→Sinkの実admissionに従う | ローカルSERVER_AIは既存WSL shell。CHAT遠隔操作はGserver専用Receiver/Writer/結果経路の実受入が必要 |
| shared API | 実Providerのruntime contractで到達性/認証を確認 | 同じ契約でも別Host。WSLのlocalhostはVPSのlocalhostではない |
| 障害 | 元requestのWriter/Sink/配送状態を調査 | PC/WSL offlineを識別し、誤ってVPSへ送らない。無断wake/直接WAN fallbackなし |

VPS用initializerやbootstrapにHost固定path・特定SHA・固定Registry hashがある場合、WSLでそのまま実行しない。既存`init_dev_workspace_project_gate.py`は登録済み既存checkoutを選ぶ検査であり、Repo作成/権限付与器ではない。Host側の対応が未実装なら未対応として保持し、root名の文字列置換や一括`cp`で突破しない。GserverのWorkspace配置adapterもremote admissionは作らない。

SSHでは既存設定/鍵/agent/known_hostsを再利用し、接続先を確認する。Host鍵照合無効化、rootへの切替、資格情報の複製、新キー発行を接続失敗時の自動Fallbackにしない。初めは正本SHA・変更状態・serviceのread-only確認だけを行う。

遠隔操作前は登録Host target、dispatcher SHA、対象Repo SHA、command digest、権限/影響範囲を照合する。実行後は元request ID、Run、Host実結果、exit、出力hash、対象状態と不変条件を照合する。結果未着だけで新requestへ同じ変更を再送しない。既存の[Host route](GITHUB_PROJECT_CHAT_HOST_ROUTE.md)を使い、新workflow/常駐AI/別Terminalを増設しない。

### 4. Libral Vault：内部仕様を守る利用手順

正本：[Libral Vault README / Module Interface / Internal API Adapter](https://github.com/seigo-gace/Libral-Vault/blob/main/README.md)、共通利用は[WORKSPACE_SHARED_SECRETS](WORKSPACE_SHARED_SECRETS.md)。

1. Module APIを使う同一Trust Boundary内か、既存Internal API Adapterの利用側かを決める。`@libral/vault`と既存Adapterを使い、GPG process、GNUPGHOME、内部State/Secret file/DBへ直接接続しない。Project別Vaultや新HTTP入口を作らない。
2. secret identifier、consumer ACL、TTL、allowed origin、Internal API認証とprivate routeを確認する。Internal Bearer認証、consumer、Cloudflare Access認証は別物。既存のshared consumer名を無条件で自称して全Secretを使わない。
3. 認証済みhealth/Manifestと必要な代表操作を確認する。`initializing/ready/blocked/stopped`を区別し、health 200だけで必要Secret/consumer利用をPASSにしない。Hostごとの到達性・認証・API対応版を確認する。
4. Provider HTTPは既存`POST /internal/v1/actions/http`でVault内にHeader注入させ、利用側へProvider tokenを取り出さない。origin allowlist、URL credentials拒否、redirect拒否、timeout/応答byte上限、Secret反射遮断を維持する。Moduleの`useSecret`ではcallback内だけ利用し、復号bufferを外へ保持しない。
5. Secret登録/置換/削除、鍵rotation、Recovery export/restoreはそれぞれ変更権限とrollbackが必要。通常のProject開始や接続失敗の対策として勝手に実施しない。原本/dataDirの二重起動、消去、別鍵bootstrapで復旧を代用しない。
6. Consumer拒否、期限切れ、Secret不在、破損、Provider 401/403とVault全体障害を分ける。失敗しても平文tokenコピー、暗号化解除、allowlist拡大へfallbackしない。復旧は所有Repoの既存transaction/recovery手順で行う。

認証値は承認済みprivate注入経路から実行時だけ渡す。CLI引数、URL、会話、公開Issue、環境全dumpへ出さない。Compose常駐と永続Volumeを維持し、ホストの直接npm/systemd常駐へ置換しない。

### 5. TGserver ZERO：既存登録から原本・検索まで

正本：[ZERO Operations](https://github.com/seigo-gace/TGserver/blob/main/docs/TGSERVER_ZERO_OPERATIONS.md)、Current #50、発見契約`operations/tgzero-registration.json`。実Topic IDをserver-coreへ二重管理しない。

1. 管理操作は**TGserverの実checkoutと権限があるHost**で行う。server-coreの正式routerで`lookup --repo OWNER/REPO --stream STREAM`→`runtime-status`を実施し、既存番号/Group/Topic/Repo+stream mapと稼働Sourceを照合する。WSLでVPS pathのrouterを動かして「Topicなし」と判定しない。
2. 既存Projectなら再登録・Topic再作成をしない。検索0件、Reader map欠落、idle時のLog 0件はTopic不存在の証拠ではない。履歴とLive Stateが食い違えば変更を止め、既存Backup/Provider台帳を読取照合する。
3. 新規の必要が確認された範囲だけ、Owner schemaのprivate requestを使う`register --request ...`へ渡す。Group追加は必要容量と承認を確認して既存`register-group`を使う。request fieldやTopic IDを推測しない。低位plan/apply/provisionを毎回手分けで作り直さない。
4. 1 Group最大10 Projects・標準5 severityと、20通/分の送信予算を区別する。満杯をTopic削除/再作成や無人Group作成で解決しない。
5. 正本5fileの非破壊差分、Backup、Source→実Runtime読込SHA、既存番号/route不変、Provider Topic ID/表示名を確認する。失敗は保存済み同一requestから正式recoverで再開し、一括State上書きはしない。
6. Producerから承認済みcanaryを送り、同一event IDでGateway受領→Delivery→TGS受付→Telegram原文→Reader/検索を照合する。system収集と開発ログProducerは別に確認し、存在しないcontainerのsystem sourceを作らない。内部commandやprivate情報をpublic canaryへ入れない。

GserverのP015は既存登録履歴がある。新規番号・Topicを発行せず、現在の実lookup/readbackを先に行う。20通/分/10Projectの値や上限変更はTGserver正本と実Runtimeで再確認し、単なる手順追記で稼働へ反映済みとしない。

### 6. Webhook Gateway：認証・配送・冪等性

正本：[INTERNAL_EVENT_API](https://github.com/seigo-gace/webhook-gateway/blob/main/docs/INTERNAL_EVENT_API.md)、実稼働destinationとOwner Current。

1. 内部Producerは`POST /internal/events`、第三者Webhook受信は既存外部Ingress契約で扱う。内部APIをInternet向け無認証入口にしない。実hostnameのOwner、TLS、Access、private到達性、Gateway Bearerをそれぞれ確認する。G-ACE用途へAstera zoneを流用する承認は過去202から推定しない。
2. 既存キーの登録/有効状態とProject分離を確認する。新規発行・rotation/revokeが許可された場合だけ既存`npm run secret`とprivate deployment mappingを使う。既存共通キーは別途廃止するまで有効で、Project別キー追加だけでは無効化されない。生成値を表示/公開せず、新キー発行APIを作らない。
3. callerが指定するのは登録済みenabled destination IDとevent schema。配送URL/header/signing secret/timeout/retry/private-network policyはGateway Owner設定。Projectキーの名前はdestination別ACLでも、body sourceIdの本人性保証でもない。
4. `payloadMode=json`は原文保持保証ではない。`internalDataPolicy`の既定sanitizeと、署名/private-network/JSONを要するOwner明示preserveを区別する。callerがpreserveを要求して強制しない。Credentialはどちらのdataにも埋め込まず、観測ログは常に秘匿する。
5. `sourceId + eventId`は安定させる。202はEvent/Delivery/OutboxのDB commit、同一内容duplicateは再配送なし、409は内容衝突であり新IDへの自動差替えをしない。配送はat-least-onceなので受信側も冪等にする。DB commit失敗を外部Ingress用spoolへ迂回しない。
6. 401=認証、403=IP制約、429=Retry-After、422=destination不明/disabled等を実応答で分類し、400/413も必要範囲で確認する。配送失敗は同じ元event/Delivery/Outboxを正式な再試行・replay手順で追跡する。
7. Source例のdestinationsはLive inventoryではない。反映前に実機専用destination/Secret mappingを保全し、意図した差分だけ反映・process再読込・配送readback・rollbackを行う。設定更新だけで配達成功と扱わない。

### 7. 開始・引継ぎで残す最小情報

以下を所有Current/PRの必要な箇所へ記録し、別trackerやサービス台帳を増やさない。private root/Host情報はprivate記録へ分離する。

```text
目的 / Owner Repo / Current Issue・Project Item / Mutation Owner
Host target / canonical parent・実checkout / branch・HEAD・dirty/stash
今回許可された操作 / 保護された未承認変更 / 適用Rule Profile
利用するサービスと正本 / consumer・stream・destination等の非秘密契約
Source・Test・CI・Host・Runtime・Provider・最終結果の個別判定
既存状態の不変条件 / 失敗時の復旧・rollback / 次の実行可能な操作
```

使わないサービスは`NOT_REQUIRED`、不明は`NOT_VERIFIED`とし、全ProjectへVault/TGserver/Gatewayを無条件で導入しない。通常のProject接続許可を提供元変更許可へ読み替えない。提供元変更が必要なら本書冒頭の具体案・利用者影響・互換性/移行/復旧策を示す。Masterが直接依頼・承認した範囲では通常作業を続け、同じ承認を繰り返し求めない。

### 8. 適用と検査の実効範囲

server-core/ProjectのREADME・AGENTS・既存client adapterから本runbookへ条件付きroutingする。既存のProject selector、Host admission、Gateway validator/認証、Vault ACL、TGserver登録/provisionerの実チェックを使い、拒否を別経路で迂回しない。

文書を読ませる入口と、実行を強制遮断する仕組みは別である。これらの検査がすべての会話/任意shellを監視しているとは主張しない。Contabo/Gserverそれぞれで、現在のSource、実client読込、Host登録、認証、代表操作、拒否・再送・復旧を検証した範囲だけを利用可能とする。新しい監視daemon、強制AI呼出し、自動PRレビューを開始要件にしない。
