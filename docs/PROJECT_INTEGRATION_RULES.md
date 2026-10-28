# PROJECT INTEGRATION RULES

Version: 2026-10-17
Role: Projectへ共通基盤を導入するときの接続・利用ルール。

## Purpose

server-coreは共通Capabilityの司令室であり、Project固有実装は所有しない。

本Documentは、各Projectが共通基盤を利用するときの導入契約を定義する。

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

必要なTopicのみ追加する。用途不明のTopicを作成しない。

### TGserver ZERO v1.5 実Runtime・Topic台帳の運用契約

Gateway同様、TGserverは**Source・稼働Runtime・Telegram Providerの物理Topic**を別のAuthorityとして扱う。詳細の所有者はTGserver側の [ZERO Operations](https://github.com/seigo-gace/TGserver/blob/main/docs/TGSERVER_ZERO_OPERATIONS.md) とし、本契約で全Project導入時の必須条件を共通化する。現在の変更提案・検証先：[TGserver PR #132](https://github.com/seigo-gace/TGserver/pull/132)。PRがmainへ入るまでSource運用の新機能を本番実装済みと扱わない。

- **台帳の役割:** `storage-registry.json` = Project/Groupの承認済み割当、VPS Live `.tgs-state/topics.json` = Topic ID/Router向け現行State、Telegram Group = 実物Topic。GitHubにあるTopic stateは本番実IDの証拠ではない。Group ID、Topic ID、旧Projectの割当は推測しない。
- **既存資産を優先:** 新設・改名よりも、まずLive State、過去の実バックアップ、Providerの既存Topic IDと実履歴を照合する。Stateから欠落していてもProvider Topicが消滅したと推定しない。既存Topicの再作成・丸ごとState置換・Projectの重複追加は禁止。既存65/70ルート完成等の歴史Evidenceと現Liveが不一致の場合は `STATE_HISTORY_DIVERGED` として保護変更を停止し、読取監査で回復候補を作る。
- **番号と画面表示は別:** 内部 `Pxxx` / `Pxxx_severity` キーと既存 `topic_id` を保持し、Telegram UIは `P013｜Webhook Gateway｜エラー` / `P014｜G-ACE 開発KB｜警告` のようにProject名とLog区分を示す。表示名を変更する際は実Providerの既存Topic IDに対する改名だけを使用し、既存Topicの新設・削除はしない。Source表示名を修正したことをProvider改名完了と扱わない。
- **上限の混同禁止:** Telegramの既存ZERO設計は1 Group **20通/分**の送信予算、通常1 Group最大10 Projects × 5 severity。20 Topic上限ではない。開発が行われない期間のLog 0件は故障ではない。
- **保護された変更:** 新Project/Topic追加時は単一Projectスコープ、事前のread-only監査、Live State・BackupのSHA256/readback、既存Routeへの非破壊差分、Provider重複防止、rollbackを揃える。Topicの一括Provision、未確認Topicの機械的再作成、Secretの公開やAPIの無断外部公開は禁止。Registry反映後は必要な既存TGserverの管理されたrestart/readbackを別途確かめる。
- **証拠の段階:** `SOURCE_REGISTERED`→`LIVE_REGISTRY_LOADED`→`TOPIC_ID_MATCH_VERIFIED`→`DISPLAY_TITLE_VERIFIED`→`GATEWAY_RECEIVED`→`TGS_ACCEPTED`→`TELEGRAM_RAW_VERIFIED`→`SEARCH_VERIFIED`。Gateway 202・legacy TGS accepted・Meili hit単独をTelegram原本保存と混同しない。0件検索も不存在証明ではない。登録Projectが休止中なら`NO_PRODUCER_ACTIVITY`と障害を区別する。
- **責務:** TGserverのRuntime台帳とProvider操作はTGserver Owner、Gateway配送設定と認証はGateway Owner、Producerアプリのイベント作成は対象Project Owner。CHATは横断整合とCurrent記録を担う。プロジェクト別変更と実サーバー効果の許可境界を混同しない。



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

- **発行主体と利用単位**：server-coreを司令室として、GPT／SERVER_AIが既存Gatewayの生成手段を使い、内部Projectごとに独立したAPIキーを発行・登録・更新・失効する。旧共通キー1本を全Projectへ使い回す運用を新規導入の前提にしない。API利用の衝突を調査する際はキーの利用単位と `sourceId + eventId` の重複を分けて確認する。キー分離だけでevent ID競合や宛先権限の分離が保証されるとは扱わない。発行・登録の実値は既存Secret注入経路だけで扱い、会話・Git・ログへ残さない。
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
