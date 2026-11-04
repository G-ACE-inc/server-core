# Gserver 第2 Host 接続 Change Plan

Status: PREPARED / PRODUCTION_ACTIVATION_NOT_AUTHORIZED

Owner: server-core Control #10 / SERVER_AI Rule #16

目的は、既存の共通 `host.command` 経路を使い、Gserverへ1件の実Requestを送り、
同一 request ID、target、Dispatcher SHA、repository SHA、command SHA、exit、
stdout hashをResult Sinkから読み戻すことである。独立Terminal、固定コマンド
Dispatcher、Gateway複製、別Control Planeは作らない。

## 既確認済みの前提

- server-core Source: PR #325 exact HEAD `1e8205202e3d4b68d4c600e57e7131c7d9748f0c`
- Gserver Source: PR #15 exact HEAD `bf1daf6e160f78a15df0187494b9dd26a094022e`
- Contabo Runtime: `c688961d29a7485c9a4d949a95c1991a452c7ec8`
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

既存の承認済みPR/Source reflection経路だけを使用する。

- PR #325をexact HEADでmainへ合流
- Host側は既存のff-only Source reflectionを使用
- before/after HEAD、active consumer、変更ファイルhashを読み戻す
- `git pull`、`reset --hard`、`clean`、無条件stashは使用しない

無停止可否: Source reflectionのみならサービス停止不要。ただしactive consumerが
再読込を必要とする場合は、限定再起動の別承認が必要。

rollback: 合流commitのrevert後、既存Source reflection経路で直前の安全なSHAへ
ff-only反映する。dirty/untrackedを持つcheckoutには反映しない。

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

## 承認が必要な保護変更の一括提示

次の変更だけが追加承認対象である。

| 変更 | 対象 | 影響 | 停止見込み | rollback |
| --- | --- | --- | --- | --- |
| PR #325合流/Source reflection | server-core main/Contabo checkout | 共通Source更新 | 原則なし | merge commit revert + 旧SHAへff-only |
| Gserver Host admission | protected Registry | Gserver targetの実行許可 | 原則なし | Gserver entryのみrevert |
| Gateway destination | webhook Gateway | 新destinationへの配送 | API登録のみならなし | destination/consumerのみ無効化 |
| Secret consumer/readback | Gateway/Gserver Receiver | 認証配送 | reload時のみ要確認 | consumer無効化、再発行なし |
| Receiver/Writer配置 | Gserver WSL Runtime | Gserver endpoint追加 | 起動方式による | 追加process/containerのみ撤去 |
| Result Sink mapping | server-core Result Sink | Gserver結果保存 | なし | Gserver mappingのみrevert |
| 限定再起動 | Gateway/Receiver | 対象サービスのみ | 影響時間を事前提示 | 既存image/configで再起動 |

この表の承認なしに、Secret、Gateway、Host admission、サービス再起動、main merge、
本番deployは実行しない。

## Completion record

完成条件は次の全てである。

- SOURCE: exact SHA reflected
- CI: required workflows SUCCESS
- DEPLOY: active consumer and target admission readback PASS
- LIVE_REQUEST: non-destructive request accepted and delivered
- LIVE_RESULT: Result Sink record and GPT CHAT readback PASS
- REGRESSION: existing Contabo route remains PASS

どれか一つでも未確認なら、Gserver第2Hostは未完了と記録する。
