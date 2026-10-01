# PROJECT INTEGRATION RULES

Version: 2026-10-01
Role: ProjectへProject-owned service / Shared Capabilityを接続するときの共通Integration Contract。

## Purpose

server-coreは共通CapabilityのDiscovery / Contractを管理するが、Project固有実装は所有しない。

本Documentは、各Projectが既存service / Vault / MCP / Toolを利用するときに最低限そろえる接続情報を定義する。

## 1. Integration Record

Integrationごとに必要範囲で定義する。
- owner
- consumer Project
- purpose
- interface / endpoint / transport
- authentication / credential contract
- permission boundary
- mutation boundary
- retry / failure behavior
- health / verification method
- rollback / disable path when applicable

不要な項目を埋めるためだけにDocumentや設定を増やさない。

## 2. TGserver Integration

TGserverはProject-owned service。Project導入時に必要範囲で定義する。
- Project identifier
- topic/channel mapping
- log / notification category
- severity/priority when used
- retention / delivery acknowledgement
- retry / failure handling

用途不明のTopicを作成しない。TGserver内部実装はTGserver Project Authorityを正とする。

## 3. Webhook Gateway Integration

Webhook gatewayはProject-owned event gateway。導入時に必要範囲で定義する。
- event name
- producer
- consumer
- endpoint / route contract
- payload schema
- authentication method
- retry / idempotency behavior
- failure handling

Gateway内部実装はowning Project Authorityを正とする。

## 4. Libral Vault Usage

Libral VaultはShared Credential Capability。

Project側で定義する。
- required secret contract identifier
- consumer service
- injection/use point
- provider purpose
- runtime verification method

Credential実値はProjectへ保存しない。

## 5. MCP / Tool Usage

ProjectがMCP / Toolを利用する場合、必要範囲で次を明確化する。
- owner
- interface / command / tool surface
- registration/config authority
- permission boundary
- mutation behavior
- availability verification
- failure behavior

Project固有MCP/ToolをWorkspace globalとして扱う場合はserver-core Registry / Workspace MCP contract側にもownershipとregistration authorityを反映する。

## 6. Documentation / Registry Update

Integration変更後に**影響したAuthorityだけ**更新する。

- Project README: Current integration entry / usageが変わる場合
- Workspace Registry: owner / shared discovery / connection authorityが変わる場合
- Design Delta: architecture/responsibility baselineから正式に変わる場合だけ
- System/Operations document: stable interface / runtime / recovery理解に必要な場合

IntegrationしただけでDesign Deltaや新規Documentを必須にしない。

## 7. Verification

Integration完了判定はTaskに応じて必要範囲で確認する。
- config/registration presence
- authentication when required
- transport/connectivity
- interface/tool discovery
- representative call/event
- expected downstream state
- retry/failure behavior where material

設定ファイルが存在するだけでLive integration完成とは扱わない。
