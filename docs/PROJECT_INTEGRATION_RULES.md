# PROJECT INTEGRATION RULES

Version: 2026-09-30
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
