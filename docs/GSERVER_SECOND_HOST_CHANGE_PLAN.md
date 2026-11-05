# Gserver 第2 Host 接続 Change Plan

Status: HOST_ADMITTED / RUNTIME_ACTIVATION_IN_PROGRESS / PROTECTED_EFFECTS_AUTHORIZED

## 2026-11-05 current checkpoint: bidirectional source complete

The source work described by this plan is no longer waiting on PR #325. The
current verified and reflected revisions are:

- server-core PR #333 final HEAD: `b8a54cbbb37b5312d0e1fee0bee71ef250c272b9`
- server-core merged main and Contabo checkout:
  `3b74f899130a701d51ad4c0d004d45abbbd7689a`
- Gserver PR #15 branch: `2ef0bfe5bd67f74ff6b3ce15d3fece0762a6a9d2`
- Gateway merged source: `fba869c` (production reflection/reload is not verified)

PR #333 exact-head `verify`, `server-core-guard`, and `windows-parser` checks
passed. The Contabo source reflection passed its dry-run and apply checks,
preserved the four existing untracked request files, left tracked files clean,
and did not restart the healthy bounded-host service.

The common Terminal now supports both initiation directions through the same
sender, Gateway, target selection, Receiver/Writer, and Result Sink. Gserver
commands run with the normal logged-in `gace` user's repository, Git/SSH, and
Docker authority. This is deliberately not a read-only or per-command approval
Terminal. Authentication, target/SHA binding, replay protection, and result
correlation remain mandatory machine checks; they do not ask Master to approve
ordinary commands one by one.

The remaining work is one-time Runtime activation, not additional Source
design: install the loopback Gserver user service, deliver the existing machine
credentials through mode-0600 external files, reflect/reload the existing
Gateway destination and private route, then perform one live request/result
round trip. On the inspected Gserver Host, the service unit, configuration
directory, credential files, and port 8790 listener are currently absent.
Creating or changing those production credentials/routes and starting the new
resident service are the protected effects still isolated by this plan. After
that one-time activation, ordinary registered requests do not return to Master
for routine technical approval.

## 2026-11-05 Master authorization: Host admission

Master explicitly authorized the one-time production connection work after the
source and protected-effect plan were presented. The canonical `gserver` target
is therefore promoted to `HOST_ADMITTED`. This admission is limited to the
existing common `host.command` route, repository
`seigo-gace/G-ACEserver`, canonical root
`/home/gace/Project/Gserver/repository`, signed Gateway delivery, durable replay
ledger, and correlated Result Sink return. It does not grant a second
Dispatcher, a fixed-command Terminal, root authority, another repository, or an
unregistered endpoint.

Gateway destination configuration, machine-key readback, active Receiver, live
request/result correlation, and Contabo regression remain independent Runtime
evidence. Until those checks pass, the connection is admitted but not complete.

## 2026-11-05 continuation: concrete Host boundary and return ingress

The Gserver branch now contains a loopback-only user service boundary which
loads `servercore_gserver_target.receive_delivery` from the existing local
same-upstream server-core checkout. It adds no dispatcher, command catalogue,
Docker authority or independent control plane. Request and result HMAC keys are
separate file-backed inputs. The service refuses startup while the canonical
target remains `SOURCE_CONTRACT_ONLY`, and remote result endpoints require TLS.

The existing Contabo bounded-host Receiver now has a result-only path
`/internal/gserver-bounded-result`. It uses the independent
`GACE_GSERVER_RESULT` key, forwards the unchanged signed record to the existing
UNIX Result Sink, and cannot accept commands on that path. The base deployment
remains unchanged when no second-Host key is configured. An activation-only
Compose overlay mounts that key without adding a published port. Once the key
environment is explicitly configured, unreadable or ambiguous key sources are
startup-fatal rather than silently disabling authentication.

Source verification: Gserver full Python regression passed 406 tests; focused
Host boundary tests passed 15. server-core result-return, delivery replay and
dependency tests passed 47, plus the existing target tests. A loopback HTTP E2E
used both repositories' real modules, temporary keys and a temporary ledger:
two deliveries of `req_999999999999999999999999` executed once and returned a
correlated PASS record with dispatcher, repository, command and stream hashes.

This is Source and isolated-runtime evidence only. The production contract is
still `SOURCE_CONTRACT_ONLY`; no real key was generated, no service was
installed or restarted, and no Cloudflare/Gateway route was changed. Activation
still requires the protected key/route/reload operations in sections 2-5. Source
rollback is a normal revert of the two repository commits. Runtime rollback,
after future activation, is to disable only the Gserver user service and remove
only the result overlay from the bounded-host deployment; existing Contabo
request handling and the Result Sink remain in place.

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

## 現在の確認済み前提

- server-core Source: merged main `3b74f899130a701d51ad4c0d004d45abbbd7689a`
- Gserver Source: PR #15 branch `2ef0bfe5bd67f74ff6b3ce15d3fece0762a6a9d2`
- Contabo checkout: `3b74f899130a701d51ad4c0d004d45abbbd7689a`
- 既存共通経路: `server-core-bounded-host` / `/internal/servercore-bounded-host`
- Gserver Source adapter: `scripts/gserver_host_adapter.py`
- Gserver target contract: `host_targets.gserver`, destination `gserver-bounded-host`

上記のSource CI、SSH、隔離E2Eは本計画の再実行対象ではない。Gateway本番反映、
Gserver Runtime起動、実Request/resultは未確認であり、Source成功と混同しない。

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

### 1. server-core Source反映（完了）

既存のPR、Source reflection、Host admission契約だけを使用する。通常のPR/Source/
CI/契約修正と、既存admissionが明示的に許可する可逆反映は通常開発として進める。
新規権限、Secret、外部公開、Provider内部変更、破壊的作用だけを保護Gateとして分離する。

- PR #333 final HEADをmainへ合流済み
- Host側は既存のff-only Source reflectionで `3b74f899` へ反映済み
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

既存Webhook Gatewayのdeployment所有設定で、Gserver destinationを1件登録する。
現物のREADMEとINTERNAL_EVENT_APIではdestination書込Admin APIは提供されていない。
環境変数名だけで管理APIが稼働していると判断しない。

- destination ID: `gserver-bounded-host`
- event type: `gace.servercore-bounded-host.requested`
- receiver path: `/internal/gserver-bounded-host`
- source: 既存server-core bounded-host sender契約
- auth: 既存Gateway delivery HMAC形式を再利用

Secretの値はIssue、PR、Source、ログへ出さない。既存Secretを再発行せず、
consumer/readbackで対応関係だけを確認する。新規Secretが不可避なら、登録前に
Master承認が必要。

無停止可否: 実deploymentの設定読込方式に依存する。Gateway
再起動、Secret reload、Cloudflare/Vault変更の必要性と既存承認範囲を確認する。

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

配置先は既存Sourceどおり `/home/gace/Project/Gserver/repository`、起動は
`gace` のuser service、bindはloopback `127.0.0.1:8790` とする。公開Listenerや
別Terminalは作らない。初回のservice配置・起動と既存private route/Gateway設定の
反映は一度だけの保護されたRuntime activationとして扱う。activation後の通常Commandを
Masterの都度承認へ戻してはならない。

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
