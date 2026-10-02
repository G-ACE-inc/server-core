# PROJECT INTEGRATION RULES

Version: 2026-10-02
Role: ProjectへProject-owned service / Shared Capabilityを接続するときの共通Integration Contract。

## Purpose

server-coreは共通CapabilityのDiscovery / Contractを管理するが、Project固有実装は所有しない。

本Documentは、各Projectが既存service / Vault / MCP / Toolを利用するときに最低限そろえる接続情報を定義する。

Generic mutation / state semanticsは `SERVER_CORE_PROTOCOL.md` を正とし、本DocumentはIntegration固有条件だけを追加する。

**複数Projectから共通利用されること自体は、Project-owned serviceをWorkspace Shared Capabilityへ再分類する根拠ではない。** 実装本体・Repository authority・Runtime ownershipが独立Projectにある場合、そのserviceは複数consumerから利用されてもProject Integrationとして扱う。利用範囲の広さとownership classificationを混同しない。

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

## 2. Mutation Ownership

Integration Taskでは、**consumer Project、service/capability owner、server-coreを別mutation domainとして扱う**。

通常の接続・利用Task:

```text
consumer Project = mutation candidate
service/capability owner Repository = read-only unless implementation change is required
server-core = read-only unless explicit owner authorization specifically permits server-core mutation
```

Workspace common contract自体に変更が必要と判明しても、それだけではserver-coreをmutation対象へ昇格しない。server-core変更は `SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示的に成立した場合だけ実行する。

「TGserverを使う」「DebugAI MCPを使う」「Vaultを使う」「Cloudflareへ接続する」のような利用指示だけで、service/capability ownerの実装やserver-coreを変更しない。

owner側変更が必要なのは、既存Interfaceでは要求を満たせないことがSource/Contract/verificationから確認され、owner Repository側の変更理由が明確になった場合だけ。ただしserver-coreは理由が明確でもexplicit owner authorizationが無ければread-onlyを維持する。

複数Repository変更が必要な場合は、Repositoryごとに目的、diff、test/verification、Git historyを分離する。server-coreを含める場合はserver-core自体の変更許可を別途確認する。

## 3. TGserver Integration

TGserverはProject-owned service。Project導入時に必要範囲で定義する。
- Project identifier
- topic/channel mapping
- log / notification category
- severity/priority when used
- retention / delivery acknowledgement
- retry / failure handling

用途不明のTopicを作成しない。TGserver内部実装はTGserver Project Authorityを正とする。

consumer側のmapping/config/document更新を、TGserver本体改修へ自動昇格しない。

## 4. Webhook Gateway Integration

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

consumer/producer側の接続変更だけで成立する場合、Gateway Repositoryはread-onlyとする。

## 5. Libral Vault Usage

Libral VaultはShared Credential Capability。

Project側で定義する。
- required secret contract identifier
- consumer service
- injection/use point
- provider purpose
- runtime verification method

Credential実値はProjectへ保存しない。

Vaultを利用するTaskとVault実装を変更するTaskを分離する。利用TaskだけならVault Repositoryはread-onlyとする。

## 6. MCP / Tool Usage

ProjectがMCP / Toolを利用する場合、必要範囲で次を明確化する。
- owner
- interface / command / tool surface
- registration/config authority
- permission boundary
- mutation behavior
- availability verification
- failure behavior

MCP/Toolを利用・登録・接続・検証するTaskだけでは、そのMCP/Tool実装Repositoryを変更しない。current Interfaceで要求を満たせないことが確認された場合だけowner側実装変更へ進む。

Project固有MCP/ToolをWorkspace globalとして扱う必要がある場合は、server-core Registry / Workspace MCP contract側の反映要否を判定する。ただしserver-core側反映が必要でも、`SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示成立するまではserver-coreはread-onlyとし、必要変更を報告・提案する。単なるProject内利用ではserver-core Registry更新を必須にしない。

## 7. Provider Integration

Cloudflare / Hugging Face等のProviderをProjectで利用するときも、次を分離する。
- Project-side config / integration
- Workspace shared credential/MCP contract
- Provider resource mutation
- Provider client/tool implementation

Providerを「使う」Taskを、Provider resource create/update/deleteやserver-core共通Contract変更へ自動変換しない。

## 8. Documentation / Registry Update

Integration変更後に**影響したAuthorityだけ**更新する。

- Project README: Current integration entry / usageが変わる場合
- Project System/Operations document: stable interface / runtime / recovery理解に必要な場合
- Workspace Registry: Workspace共通owner / discovery / connection authority自体が変わる場合の更新候補
- server-core Integration Contract: Workspace共通ルール自体が変わる場合の更新候補
- Design Delta: architecture/responsibility baselineから正式に変わる場合の更新候補

server-core内のRegistry / Integration Contract / Design Deltaを実際に更新するには、server-core自体についてexplicit owner authorizationが必要。影響があることや更新候補であることを、write permissionと扱わない。

consumer ProjectのREADME/付属Document更新を、server-core Document更新へ読み替えない。

IntegrationしただけでDesign Delta、新規Document、Workspace Registry更新を必須にしない。

## 9. Verification

Integration完了判定はTaskに応じて必要範囲で確認する。
- config/registration presence
- authentication when required
- transport/connectivity
- interface/tool discovery
- representative call/event
- expected downstream state
- retry/failure behavior where material

設定ファイルが存在するだけでLive integration完成とは扱わない。

Integration固有の状態は次へ自動昇格させない。

```text
CONFIG_PRESENT != REGISTRATION_VERIFIED
REGISTRATION_VERIFIED != AUTHENTICATION_VERIFIED
AUTHENTICATION_VERIFIED != TRANSPORT_VERIFIED
TRANSPORT_VERIFIED != INTERFACE_DISCOVERY_VERIFIED
INTERFACE_DISCOVERY_VERIFIED != REPRESENTATIVE_CALL_PASS
REPRESENTATIVE_CALL_PASS != INTEGRATION_COMPLETE unless Task acceptance is satisfied
```

上記は `SERVER_CORE_PROTOCOL.md` のgeneric State SemanticsをIntegration Domainへ適用した追加条件であり、別のgeneric state modelではない。

`HTTP 200`、process/container起動、client listing、config entry、過去の成功だけをIntegration完成の証拠にしない。逆にCurrent live再検証待ちだけを理由に、Source/implementation/interfaceの既検証状態を未実装へ降格しない。

Current live evidenceを記録する場合は、少なくとも対象Capability、確認経路、観測時点、証明範囲を区別する。Transientなlive statusをWorkspace Registryの恒久状態へ固定しない。

Verificationのためにowner Repositoryを参照したことを、そのRepositoryのmutation permissionと扱わない。
