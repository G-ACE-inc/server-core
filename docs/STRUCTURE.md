# SERVER CORE STRUCTURE

## 目的
本ファイルは `/home/admin1/server-core` 自身の構造正本である。

## ルート直下
- `README.md`: 入口と要約
- `.aiignore`: AI向けの通常読込除外ヒント
- `.cursorignore`: Cursor系ツール向けの通常読込除外ヒント
- `SERVER_CORE_PROTOCOL.md`: 共通運用規則
- `CORE.md`: LibralCore共通思想
- `KB.md`: 確認済み知識と判断記録
- `PROJECT_STATUS.md`: 現在状態と正本入口
- `add-status.sh`: PROJECT_STATUS自動追記を禁止するための互換スクリプト
- `scripts/`: 作業自動化スクリプト
- `.github/`: GitHub上のPR、Issue、Actions、Dependabot設定
- `docs/`: 手順、テンプレート、用語表
- `archive/`: 旧版、退避ファイル

## docs
- `LOAD_SCOPE.md`: AIが読む範囲と読まない範囲
- `STRUCTURE.md`: Server Core自身の構造
- `GLOSSARY.md`: 用語と正式表記
- `PROJECT_TEMPLATE.md`: 新規Project用テンプレート
- `DEPLOY_RUNBOOK.md`: 承認後のデプロイ手順
- `OPERATION_CHECKLIST.md`: 作業前後の確認手順
- `AUTO_COMMIT.md`: AI作業後の自動commit手順
- `GITHUB_FREE_MAX.md`: GitHub無料枠の最大活用設定
- `GITHUB_SKILL.md`: Codex GitHub skillの参照方法
- `G_ACE_WORKSPACE.md`: G-ACE.code-workspaceの正規仕様

## archive
`archive/YYYY-MM-DD/` を基本形式とする。

秘密情報を含むファイルはarchiveへ退避しない。

archive配下は通常読込禁止とする。

archive内の文書を現在状態、現在仕様、現在ルールとして扱わない。

## 禁止
- ルート直下への一時ファイル作成
- 用途不明なdocs追加
- 正本と重複する別名ファイルの作成
- archiveへ秘密情報を保存すること
- 実ファイル変更後にREADMEと該当正本文書を同期しないこと
