# SERVER CORE STRUCTURE

## 目的
本ファイルは `/home/admin1/server-core` 自身の構造正本である。

## ルート直下
- `README.md`: 入口と要約
- `SERVER_CORE_PROTOCOL.md`: 共通運用規則
- `CORE.md`: LibralCore共通思想
- `KB.md`: 確認済み知識と判断記録
- `PROJECT_STATUS.md`: 現在状態と正本入口
- `add-status.sh`: PROJECT_STATUS自動追記を禁止するための互換スクリプト
- `docs/`: 手順、テンプレート、用語表
- `archive/`: 旧版、退避ファイル

## docs
- `STRUCTURE.md`: Server Core自身の構造
- `GLOSSARY.md`: 用語と正式表記
- `PROJECT_TEMPLATE.md`: 新規Project用テンプレート
- `DEPLOY_RUNBOOK.md`: 承認後のデプロイ手順
- `OPERATION_CHECKLIST.md`: 作業前後の確認手順

## archive
`archive/YYYY-MM-DD/` を基本形式とする。

秘密情報を含むファイルはarchiveへ退避しない。

## 禁止
- ルート直下への一時ファイル作成
- 用途不明なdocs追加
- 正本と重複する別名ファイルの作成
- archiveへ秘密情報を保存すること
