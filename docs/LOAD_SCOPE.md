# SERVER CORE LOAD SCOPE

## 目的
AIが作業開始時に読む範囲を固定し、古い履歴、補助スクリプト、GitHub設定を現在ルールとして誤読しないようにする。

## 通常読込対象
作業開始時に読むのは次に限定する。

1. `README.md`
2. `docs/LOAD_SCOPE.md`
3. `SERVER_CORE_PROTOCOL.md`
4. `CORE.md`
5. `KB.md`
6. `PROJECT_STATUS.md`

## 必要な時だけ読む
目的が一致する場合だけ、該当ファイルを限定して読む。

- 構造確認: `docs/STRUCTURE.md`
- 用語確認: `docs/GLOSSARY.md`
- 新規Project作成: `docs/PROJECT_TEMPLATE.md`
- デプロイ承認後: `docs/DEPLOY_RUNBOOK.md`
- 作業手順確認: `docs/OPERATION_CHECKLIST.md`
- 自動commit確認: `docs/AUTO_COMMIT.md`
- GitHub無料枠設定: `docs/GITHUB_FREE_MAX.md`
- GitHub skill確認: `docs/GITHUB_SKILL.md`
- 自動化実行: `scripts/ai-auto-commit.sh`
- GitHub skill path解決: `scripts/github-skill-path.sh`

## 通常読込禁止
作業開始時、次を読んではならない。

- `archive/`
- `.github/`
- `scripts/`

## 読込禁止の理由
- `archive/` は旧状態、旧判断、旧作業履歴であり、現在ルールではない。
- `.github/` はGitHub上の自動化設定であり、Server Core正本ではない。
- `scripts/` は実行用補助であり、現在状態や運用思想の正本ではない。

## 例外
ユーザーが明示した場合、または現在作業に直接必要な場合だけ、対象ファイルを限定して読む。

例:

- GitHub Actionsを修正する作業では `.github/workflows/server-core-guard.yml` を読む。
- 自動commitを修正する作業では `scripts/ai-auto-commit.sh` を読む。
- 旧履歴の確認を求められた場合だけ `archive/` 内の該当ファイルを読む。

## 禁止
- archive内の情報を現在状態として扱うこと
- archive内の旧ルールを現在ルールとして採用すること
- scriptsや.githubを作業開始時の通常コンテキストとして読むこと
