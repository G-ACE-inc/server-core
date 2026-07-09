# DEPLOY RUNBOOK

## 目的
管理者が本番起動、公開、切替を承認した後の標準手順を定義する。

本ファイルは承認を代替しない。

## 前提
- 管理者が対象Project、対象ブランチ、対象commit、実行範囲を明示していること。
- 対象Projectの `docs/STRUCTURE.md` と仕様書を確認済みであること。
- `.env` やsecretを表示、転記、commitしないこと。

## 事前確認
1. `pwd` で作業ディレクトリを確認する。
2. `git status --short --branch` で対象リポジトリを確認する。
3. `git log -1 --oneline` で対象commitを確認する。
4. `docker ps` で既存コンテナを確認する。
5. `git diff` と `git diff --cached` が意図通りであることを確認する。
6. `.env`, token, password, session, credentialがcommit対象に含まれないことを確認する。

## Docker Compose標準手順
対象Projectの手順が存在する場合は、Project側のrunbookを優先する。

標準手順:

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

## 起動後確認
1. `docker compose ps` で状態を確認する。
2. 必要なhealthcheck、疎通試験、ログ確認を行う。
3. 失敗時は自動で公開や切替を進めない。
4. 復旧が必要な場合は、管理者へ対象commit、失敗内容、復旧案を提示する。

## 禁止
- 管理者承認なしの本番起動、公開、切替
- 対象外Projectの同時変更
- `.env` の表示、転記、commit
- 未検証の途中状態のpush
- 失敗状態を成功として記録すること
