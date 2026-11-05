# Gserver 第2 Host 接続 Change Plan

Status: PREPARED / NORMAL_SOURCE_WORK_CONTINUES / PROTECTED_EFFECTS_ISOLATED

## 2026-11-05 continuation: authenticated delivery and result return

The shared `servercore_gserver_target.receive_delivery` now reuses
`gace_internal_delivery_auth.verify_delivery` and the existing Host Writer
ledger primitives. It accepts the Gateway's signed JSON **data** payload (not
the producer event envelope), requires `HOST_ADMITTED` and the canonical root,
and persists a fingerprint and RUNNING receipt before invoking the existing
Gserver adapter. A completed duplicate reuses the stored result; changed content
under the same ID is rejected. An interrupted RUNNING claim requires outcome
reconciliation and is never automatically re-executed. Sink failure permits
delivery retry without rerunning the command.

The shared Result Sink accepts optional, strictly validated `target_evidence`
while retaining the legacy record contract. Raw streams remain private and
public comments contain only correlation metadata. Remote target evidence does
not consult the Contabo-local Writer ledger. Actions passes target/repository/
command pins to the existing result poller, which checks the returned metadata.

Verification: six signed-delivery/failure tests, 32 existing result-return tests,
13 poll tests, five target tests and 18 existing transport tests pass. An isolated
signed request using the real WSL Gserver adapter, temporary Writer/Sink storage,
public-record renderer and poll evaluator passed; two deliveries executed once.
Test admission and signing key existed only in memory. This is not a live
Gateway delivery, production admission, network listener or CHAT return.

Runtime integration still needs an admitted deployment caller to supply the
existing signature key, private ledger/lock paths, adapter and authenticated
Result Sink transport. None of these are caller-controlled request parameters.
The production target remains SOURCE_CONTRACT_ONLY. No service was started.

Correction to the historical steps below: the inspected Gateway contract uses
deployment configuration for destinations, not a destination-write Admin API.
The old prerequisite SHAs below are historical snapshots, not execution pins.
Resolve current PR/Host HEADs before reflection. Rollback for this increment is
a normal source revert; no production configuration or data migration occurred.

Owner: server-core Control #10 / SERVER_AI Rule #16

目的は、既存の共通 `host.command` 経路を使い、Gserverへ1件の実Requestを送り、
同一 request ID、target、Dispatcher SHA、repository SHA、command SHA、exit、
stdout hashをResult Sinkから読み戻すことである。独立Terminal、固定コマンド
Dispatcher、Gateway複製、別Control Planeは作らない。

## 既確認済みの前提

- server-core Source: PR #325 exact HEAD `e177bb0e7fc48d0dec847816316c801ce65ca793`
- Gserver Source: PR #15 exact HEAD `9f56b2d6a4aa951f3c4e28d2cdf2f11eb7a2ce28`
- Contabo Runtime read-only snapshot: `c688961d29a7485c9a4d949a95c1991a452c7ec8`
- 既存共通経路: `server-core-bounded-host` / `/internal/servercore-bounded-host`
- Gserver Source adapter: `scripts/gserver_host_adapter.py`
- Gserver target contract: `host_targets.gserver`, destination `gserver-bounded-host`

上記のCI、SSH、隔離E2Eは本計画の再実行対象ではない。

## 実行順

### 0. 変更前チェック（read-only）

対象はContabo、Gateway、Gserver WSL、Result Sinkである。次を保存する。

- active Source SHAとPR exact SHA
- protected Registryのdigest、dirty/untracked一覧、既存requestファイルの件数・hash
- `server-core-bounded-host` の状態、設定、既存destination
- Gateway API/workerの状態と既存destination名（Secret値は読まない）
- Gserver WSLのadapter、Receiver/Writer配置、Docker/Compose状態
- Result Sink socket、保存先、既存recordのrequest ID

dirty、未追跡、稼働中サービスは変更しない。

### 1. server-core Source反映

既存のPR、Source reflection、Host admission契約だけを使用する。通常のPR/Source/
CI/契約修正と、既存admissionが明示的に許可する可逆反映は通常開発として進める。
新規権限、Secret、外部公開、Provider内部変更、破壊的作用だけを保護Gateとして分離する。

- PR #325をexact HEADで通常の既存PR手順によりmainへ合流
- Host側は既存のff-only Source reflectionを使用
- before/after HEAD、active consumer、変更ファイルhashを読み戻す
- `git pull`、`reset --hard`、`clean`、無条件stashは使用しない

無停止可否: Source reflectionのみならサービス停止不要。ただしactive consumerが
再読込を必要とする場合、その限定reload/restartが既存承認範囲を超えるかを実行時に確認する。

rollback: 合流commitを通常のrevert手順で戻し、既存Source reflection経路のadmissionが
許可する直前の安全なSHAへ反映する。対象SHAがancestorでない場合にforce/resetはせず、
Source conflictとして停止する。dirty/untrackedを持つcheckoutには反映しない。

### 2. Gserver Host admission

既存のprotected Host/target Registryへ、次のtargetだけを追加する。

- target: `gserver`
- repository: `seigo-gace/G-ACEserver`
- command: `host.command`
- fixed command terminal: `false`
- destination: `gserver-bounded-host`
- endpoint: `/internal/gserver-bounded-host`
- canonical root: `/home/gace/Project/Gserver/repository`

既存Contabo targetのregistry entry、operation、branch、Secretは変更しない。

無停止可否: RegistryのSource更新は停止不要。ただしactive admission loaderの
再読込が必要なら、その方法と影響を確認してから実行する。

rollback: Gserver entryだけを削除/revertし、既存targetの順序・digest・値を
byte-preservingで戻す。

### 3. Gateway destinationと認証配送

既存Webhook Gatewayの正式API/CLIで、Gserver destinationを1件登録する。

- destination ID: `gserver-bounded-host`
- event type: `gace.servercore-bounded-host.requested`
- receiver path: `/internal/gserver-bounded-host`
- source: 既存server-core bounded-host sender契約
- auth: 既存Gateway delivery HMAC形式を再利用

Secretの値はIssue、PR、Source、ログへ出さない。既存Secretを再発行せず、
consumer/readbackで対応関係だけを確認する。新規Secretが不可避なら、登録前に
Master承認が必要。

無停止可否: destination登録はAPIの既存idempotent操作であれば停止不要。Gateway
再起動、Secret reload、Cloudflare/Vault変更が必要なら承認対象。

rollback: `gserver-bounded-host` destinationとそのconsumer mappingだけを無効化し、
既存destinationを触らない。

### 4. Gserver Receiver/Writer配置

Gserver側は `gserver_host_adapter.py` を呼ぶ薄いReceiver/Writerだけを配置する。

- 共通Dispatcherを複製しない
- 固定コマンドメニューを作らない
- Secret/Token storeを作らない
- Docker socket権限を追加しない
- 受信Requestをtarget/repository/SHA/command digestで検証する
- 結果はrequest ID、Host SHA、exit、stdout/stderr hashを返す

配置先・起動方法・公開bind addressは、既存Gserver Runtimeの現物とGateway
destinationが一致していることを確認してから決める。新規常駐service、公開domain、
Cloudflare tunnel変更はこの計画だけでは許可しない。

rollback: Gserver Receiver/Writerの追加ファイル・process・containerだけを撤去し、
既存Gserver app、Core、Storage、Bot/TGSを変更しない。

### 5. Result Sink相関

既存Result Sinkの固定socket/record contractを再利用する。

- request IDは元Requestと完全一致
- targetは `gserver`
- repositoryは `seigo-gace/G-ACEserver`
- repo SHAはRequestの`repo_sha`と一致
- host SHAを別フィールドで保存
- exit code、stdout SHA、stderr SHAを検証
- duplicateはfirst-terminal-result-wins

rollback: Gserver request recordだけを対象にし、既存Contabo result recordを削除・
上書きしない。

### 6. 非破壊canary

最初の実Requestは、Gserver正本に変更を加えないコマンドに限定する。

- request: `host.command`
- command例: `git rev-parse HEAD`
- write、deploy、Docker lifecycle、Secret read、外部通信は不可

検証順序:

```text
Actions/request receipt
  -> Gateway accepted/delivered
  -> Gserver Receiver admission
  -> adapter execution
  -> Result Sink record
  -> GPT CHAT-visible readback
```

PASS条件はHTTP 202ではなく、同一request ID、target、repo SHA、host SHA、command
SHA、exit、stdout hashの全一致である。

### 7. 回帰確認

Gserver canary後、既存Contabo targetに対する既存のread-only commandを1件実行し、
request/resultの相関、既存destination、既存Host SHA、既存service状態が変わらない
ことを確認する。Gserver canary失敗時は既存Contabo経路へ切り替えず、Gserver側だけ
rollbackする。

## 追加判断が必要な保護変更の一括提示

通常のSource/PR/CI/契約修正はこの表の追加判断を待たずに進める。次の操作だけは、
既存Rule/Provider/Host正本で新規権限・Secret・外部公開・破壊的効果が発生する場合に、
その操作単位で追加判断を要する。

| 変更 | 対象 | 影響 | 停止見込み | rollback |
| --- | --- | --- | --- | --- |
| PR #325合流/Source reflection | server-core main/Contabo checkout | 共通Source更新 | 原則なし | merge revert + admission済み旧SHAへ反映 |
| Gserver Host admission | protected Registry | Gserver targetの実行許可 | 原則なし | Gserver entryのみrevert |
| Gateway destination | webhook Gateway | 新destinationへの配送 | API登録のみならなし | destination/consumerのみ無効化 |
| Secret consumer/readback | Gateway/Gserver Receiver | 認証配送 | reload時のみ要確認 | consumer無効化、再発行なし |
| Receiver/Writer配置 | Gserver WSL Runtime | Gserver endpoint追加 | 起動方式による | 追加process/containerのみ撤去 |
| Result Sink mapping | server-core Result Sink | Gserver結果保存 | なし | Gserver mappingのみrevert |
| 限定再起動 | Gateway/Receiver | 対象サービスのみ | 影響時間を事前提示 | 既存image/configで再起動 |

Secret発行/再発行、既存Provider内部設定の変更、公開domain/外部公開、破壊的操作、
既存正本でMaster-onlyと明記された変更は、この表の対象影響・停止有無・rollbackを
一度に提示してから、その操作だけを保留する。その他のSource、テスト、CI、既存admission
内の可逆技術反映は継続する。

## Completion record

完成条件は次の全てである。

- SOURCE: exact SHA reflected
- CI: required workflows SUCCESS
- DEPLOY: active consumer and target admission readback PASS
- LIVE_REQUEST: non-destructive request accepted and delivered
- LIVE_RESULT: Result Sink record and GPT CHAT readback PASS
- REGRESSION: existing Contabo route remains PASS

どれか一つでも未確認なら、Gserver第2Hostは未完了と記録する。
