# Cloudflare Tunnel 統合設計 v1.1 — Astera v8

実運用正本。管理者の明示指示がない限りAI・作業者は変更しない。

## 1. 目的

Astera v8（`http://127.0.0.1:7373`）を `api.asterav8.jp` として安全に外部公開する。
HTTPS終端、Cloudflare WAF、DDoS保護を Cloudflare Tunnel 経由で実現する。
VPS側はポート公開・証明書管理・Nginx不要の最小構成とする。

## 2. 責務境界

| 責務 | 担当 |
|---|---|
| Tunnel の作成・設定・DNS管理 | 管理者（Cloudflare ダッシュボード） |
| Token の GPG 暗号化と Runtime File 生成 | GPG-Core（`secure_up.sh`） |
| cloudflared Container の定義 | astera_v8（`docker-compose.yml`） |
| 運用手順・Plan・State 管理 | server-core（`scripts/cloudflare_ops.py`） |
| HTTP サービス本体 | astera_v8（`astera-v8` container） |

## 3. 所有 Repository

| Repository | 役割 |
|---|---|
| `/home/admin1/server-core` | 運用定義・スクリプト・本正本 |
| `/home/admin1/projects/astera_v8` | Compose 定義・アプリ実装 |
| `/home/admin1/projects/GPG-Core` | GPG 暗号化・復号・Secret 生成 |

## 4. server-core の役割

- `operations/cloudflare.json`：Project 設定の正本（認証情報を含まない）
- `scripts/cloudflare_ops.py`：Subcommand 形式の運用スクリプト
- `docs/CLOUDFLARE_OPERATIONS.md`：本正本
- `.cursor/rules/cloudflare-operations.mdc`：AI 作業ルール

**server-core に Tunnel Container や Secret を置かない理由**:
server-core は全 Project 共通の統治領域であり、特定 Application の Runtime 資材（Container・Token・GPG 暗号化ファイル）を持つべきでない。
Application 固有の起動・Secret・Container 定義は astera_v8 に置き、server-core は運用観点の定義・手順・状態管理だけを担う。
これにより server-core を Application の実行時依存にせず、統治領域としての責務を維持できる。

## 5. Astera v8 の役割

- `docker-compose.yml`：`astera-v8-cloudflared` Service の定義（profile: cloudflare）
- `.env.example`：`CLOUDFLARE_TUNNEL_TOKEN_FILE` のパス契約の説明
- `astera-v8` Container：HTTP サービス本体（既存・変更なし）

astera_v8 は HTTP サービスとして `127.0.0.1:7373` でのみ待機する。
Tunnel の有無に関わらず、既存の astera-v8 起動は profile なし Compose で完結する。

## 6. GPG-Core の役割

- `.env.gpg` の復号
- Tunnel Token の Runtime Secret File 生成（`/run/user/<uid>/` 配下）
- Docker Compose Secret Source の環境変数設定
- Compose 起動後の一時 File 削除

GPG 秘密鍵・GPG-Core ライブラリは cloudflared Container にマウントしない。

## 7. Cloudflare 側 Resource

| Resource | 値 |
|---|---|
| Account | Info@g-acebot.com's Account |
| Zone | asterav8.jp |
| Tunnel 名 | astera-v8-prod |
| Preview hostname | preview.asterav8.jp |
| Production hostname | api.asterav8.jp |
| Origin | http://127.0.0.1:7373 |
| Metrics | http://127.0.0.1:20241/metrics |

すべての Cloudflare Resource 作成・変更は管理者が承認後に手動で実行する。
`cloudflare_ops.py` は Cloudflare API を直接変更しない。

## 8. Credential 境界

| 種別 | 保管場所 | Git 管理 |
|---|---|---|
| Tunnel Token | astera_v8/.env.gpg（GPG 暗号化）| 暗号化済みのみ可 |
| Runtime Secret File | `/run/user/<uid>/astera_v8_cloudflare_tunnel_token` | 禁止 |
| Token File Path | 環境変数 `CLOUDFLARE_TUNNEL_TOKEN_FILE` | 禁止（値として） |
| Account ID / Zone ID | 記録しない | 禁止 |
| Personal API Token | cloudflare_ops.py に渡さない | 禁止 |

- Token 値を Chat・Terminal・Log・Git Diff に出力しない。
- Personal API Token を常駐処理に渡さない。
- Tunnel 専用 Token だけを cloudflared に渡す。

## 9. Preview 運用

1. 管理者が Cloudflare ダッシュボードで Tunnel `astera-v8-prod` を作成する（`preview_apply` 承認）
2. Tunnel Token を取得し、`CLOUDFLARE_TUNNEL_TOKEN` として `.env` に追記する
3. `secure_up.sh --profile cloudflare --secret CLOUDFLARE_TUNNEL_TOKEN:CLOUDFLARE_TUNNEL_TOKEN_FILE:astera_v8_cloudflare_tunnel_token <project-path>` を実行する
4. cloudflare Profile が起動する
5. `cloudflare_ops.py verify` で疎通を確認する
6. `preview.asterav8.jp` でアクセスを確認する

## 10. 本番昇格

1. Preview 運用で問題がないことを確認する
2. 管理者が `production_apply` を承認する
3. DNS に `api.asterav8.jp` CNAME を追加する
4. `/signup` のブロックを解除するかを管理者が判断する
5. `cloudflare_ops.py verify` で本番疎通を確認する

## 11. 通常運用

```bash
# 状態確認
python3 /home/admin1/server-core/scripts/cloudflare_ops.py status

# 事前確認
python3 /home/admin1/server-core/scripts/cloudflare_ops.py preflight

# 起動（Token File が必要、--confirm 必須）
python3 /home/admin1/server-core/scripts/cloudflare_ops.py local-up --confirm

# 疎通確認
python3 /home/admin1/server-core/scripts/cloudflare_ops.py verify

# 停止（--confirm 必須）
python3 /home/admin1/server-core/scripts/cloudflare_ops.py stop --confirm
```

ホスト再起動後は Runtime File が消えるため、`secure_up.sh` を再実行して Token File を再生成してから `local-up` を行う。

## 12. Token Rotation

1. Cloudflare ダッシュボードで Token を再発行する
2. astera_v8/.env.gpg を新 Token で再暗号化する（既存 .env.gpg を上書き）
3. `stop --confirm` で Container を停止する
4. `secure_up.sh --profile cloudflare --secret ...` で新 Token File を生成する
5. `local-up --confirm` で再起動する
6. `verify` で疎通を確認する

## 13. 障害・復旧

**Container が起動しない場合**:
- `cloudflare_ops.py status` で状態を確認する
- `docker logs astera-v8-cloudflared` でログを確認する
- Token File が存在するか確認する（`CLOUDFLARE_TUNNEL_TOKEN_FILE` 環境変数）
- `preflight` を実行して事前条件を確認する

**Tunnel 接続が切れた場合**:
- cloudflared は `restart: unless-stopped` で自動再起動する
- 復旧しない場合は `stop --confirm` → `local-up --confirm` を行う

**astera-v8 が不健全な場合**:
- cloudflared は `depends_on.astera-v8.condition: service_healthy` で起動しない
- astera-v8 の healthcheck が回復するまで待つ

## 14. Rollback

1. `cloudflare_ops.py rollback --confirm` を実行する（Container 停止 + State 記録）
2. Cloudflare ダッシュボードで Ingress 設定を手動で戻す
3. DNS CNAME を削除または変更する（管理者が判断）
4. 必要に応じて前の Token File に戻す

## 15. 検証

`verify` サブコマンドが確認する項目:
- origin `http://127.0.0.1:7373/healthz` の応答（HTTP 200）
- metrics `http://127.0.0.1:20241/metrics` の応答（HTTP 200）

次だけでは合格にしない:
- Container が起動した
- エラーが出なかった
- `docker compose up` が終了した

## 16. 承認 Gate

管理者の明示承認なしに、以下の Gate を通過しない。Gate は番号順に扱い、各 Gate の承認対象を満たした場合のみ次の Gate に進む。

| Gate | 承認対象 | 実施内容 |
|---|---|---|
| `Gate 1` | 差分レビュー | server-core と astera_v8 の変更差分を確認し、作業範囲を固定する |
| `Gate 2` | modular-catalog正本確認 | modular-catalog の正本を確認し、依存関係と参照元を確定する |
| `Gate 3` | GPG Dummy Secret正常系 | GPG Dummy Secret の正常系を確認し、暗号化・復号の前提を満たす |
| `Gate 4` | cloudflared実起動互換検証 | cloudflared の実起動互換性を確認し、Compose 定義の整合を検証する |
| `Gate 5` | Commit | 変更を commit する |
| `Gate 6` | Push | commit とは別に push する |
| `Gate 7` | Tunnelだけ作成 | Cloudflare Tunnel のみを作成する |
| `Gate 8` | Token暗号化・Runtime Secret生成 | Tunnel Token を暗号化し、Runtime Secret を生成する |
| `Gate 9` | Preview Route・Access作成 | Preview 用 Route と Access を作成する |
| `Gate 10` | Docker起動 | cloudflared Container を起動する |
| `Gate 11` | Preview実利用・障害復旧検証 | preview.asterav8.jp での実利用と障害復旧を検証する |
| `Gate 12` | api.asterav8.jp本番公開 | api.asterav8.jp を本番公開する |
| `Gate 13` | /signup公開可否の個別判断 | `/signup` の公開可否を個別に判断する（正式仕様確定まで遮断継続） |

- Gate 1〜6 は事前確認・変更統制用の Gate とする。
- Gate 7〜13 は Cloudflare / Docker / 公開運用の実行 Gate とする。

## 17. 禁止事項

- Cloudflare API を直接変更すること（`cloudflare_ops.py` は変更しない）
- Token 値を Chat・Terminal・Log・Git Diff に出力すること
- Personal API Token を常駐処理に渡すこと
- Tunnel Token 以外の Token を cloudflared に渡すこと
- server-core に Container・Token・GPG 暗号化ファイルを置くこと
- Read-only 確認だけで書き込み権限を断定すること
- 実利用テストを行わず完成扱いにすること
- 既存 astera-v8・TGserver・SQLite・Outbox を変更すること
- Rollback 手順を作成前に確認しないこと

## 18. 完了条件

すべて通過した場合だけ「完了」とする。

- [ ] `cloudflare_ops.py preflight` が全チェック通過
- [ ] cloudflare Profile で Container が起動する
- [ ] `cloudflare_ops.py verify` が PASS
- [ ] `preview.asterav8.jp` でアクセスが確認できる（preview_apply 承認後）
- [ ] Profile なしの既存 astera-v8 起動に影響がない
- [ ] Token が Container 環境変数・Log・Git Diff に出ていない
- [ ] State File が mode 0600 で作成されている
- [ ] 本番昇格は別承認（production_apply）後
