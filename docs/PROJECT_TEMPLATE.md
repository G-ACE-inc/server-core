# PROJECT TEMPLATE

## 目的
新規Projectを作成するときの最小構成を定義する。

## 必須ファイル
- `PROJECT_INDEX.md`
- `README.md`
- `docs/STRUCTURE.md`
- `docs/DOC_INDEX.md`
- `docs/SPEC.md` または `docs/SPEC_vX.Y.md`
- `.gitignore`
- `.env.example` が必要なProjectでは値なしで作成する

## 推奨ファイル
- `docs/DEPLOY_RUNBOOK.md`
- `docs/OPERATION_CHECKLIST.md`
- `docs/SECURITY.md`
- `archive/YYYY-MM-DD/`

## PROJECT_INDEX.md 最小項目
- Project名
- 目的
- 正本パス
- 主要Module
- 正本文書一覧
- 現在フェーズ
- 本番運用可否
- 管理者承認が必要な操作

## docs/STRUCTURE.md 最小項目
- ルート直下の役割
- `src/` または実装ディレクトリの役割
- `docs/` の役割
- `archive/` の扱い
- 一時ファイル、cache、logsの保存場所と削除条件
- 作成禁止ファイルまたは作成禁止ディレクトリ

## 5層アーキテクチャ必須項目

新規Projectの `docs/STRUCTURE.md` には、次を必ず含める。

- Layer 1〜Layer 5 の定義と各Layerの責務
- 依存方向は高層から低層への一方向のみ
- Layer 1はLayer 2以上をimportしない
- Layer 2はLayer 3以上をimportしない
- Layer 3はLayer 4以上をimportしない
- Layer 4はLayer 5以上をimportしない
- 循環依存、層の省略、層の改名、層の統合を禁止する

## docs/DOC_INDEX.md 最小項目
- 正本文書
- 補助文書
- 旧版または退避文書
- 読込順序

## 環境変数
`.env` はcommit禁止とする。

共有が必要なキーは `.env.example` に値なしで記載する。

例:

```env
SERVICE_TOKEN=
REDIS_URL=
```

## GitHub
初回作成時は、最小構成をcommitしてから実装を開始する。

作業履歴はcommit / PRを正本とする。

## 禁止
- 構成図なしで実装を始めること
- READMEだけに仕様を書くこと
- 作業履歴をPROJECT_STATUSへ蓄積すること
- 秘密情報をcommitすること
