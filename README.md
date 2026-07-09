# SERVER-CORE MANAGEMENT INDEX

## 概要
`/home/admin1/server-core/` は、全Projectに適用される最上位の共通ルール・共通コンテキストを置く領域である。

## 管理者
本環境の管理者はユーザーである。

AI・作業者は、管理者の明示的な変更指示がない限り、Server Core正本を書き換え・追記・削除・置換してはならない。

管理者から明示的な変更指示がある場合は、指定された対象と範囲に限って変更する。

質問、疑問、検討、提案、操作方法の説明は、それだけでは変更指示として扱わない。

## 読込順序
作業開始時は、以下の順に確認する。

1. `README.md`
2. `docs/LOAD_SCOPE.md`
3. `SERVER_CORE_PROTOCOL.md`
4. `CORE.md`
5. `KB.md`
6. `PROJECT_STATUS.md`

`docs/LOAD_SCOPE.md` に通常読込対象外と書かれたファイル、ディレクトリを、AIが作業開始時に読んではならない。

## 正本の役割
- `CORE.md`: 共通思想
- `SERVER_CORE_PROTOCOL.md`: 共通運用規則
- `KB.md`: Server Core上の確認済み知識・判断記録
- `PROJECT_STATUS.md`: 現在状態と正本入口
- `docs/LOAD_SCOPE.md`: AIが読む範囲と読まない範囲
- `docs/STRUCTURE.md`: Server Core自身の構造定義
- `docs/GLOSSARY.md`: 用語と正式表記
- `docs/PROJECT_TEMPLATE.md`: Project新規作成テンプレート
- `docs/DEPLOY_RUNBOOK.md`: 承認後のデプロイ手順
- `docs/OPERATION_CHECKLIST.md`: 作業前後の確認手順
- `docs/AUTO_COMMIT.md`: AI作業後の自動commit手順
- `docs/GITHUB_FREE_MAX.md`: GitHub無料枠の最大活用設定
- `docs/GITHUB_SKILL.md`: Codex GitHub skillの参照方法
- `docs/G_ACE_WORKSPACE.md`: G-ACE.code-workspaceの正規仕様
- `scripts/ai-auto-commit.sh`: 自動commit / push支援スクリプト
- `scripts/github-skill-path.sh`: GitHub skill参照パス解決スクリプト
- TGserver詳細: `/home/admin1/projects/TGserver` 側の正本文書

## 主要原則
- 詳細な運用規則は `SERVER_CORE_PROTOCOL.md` を正とする。
- READMEは入口と要約だけを持ち、詳細ルールを重複させない。
- 通常作業で読む範囲は `docs/LOAD_SCOPE.md` に限定する。
- Server Coreの構造、運用、手順、自動化を変更した場合は、READMEと該当正本文書を変更後の正規仕様として更新してから作業を終える。

## 正本文書同期
変更内容は、作業報告や改善メモとして残さない。

変更後に有効な仕様、手順、構造、制約として、READMEと該当する正本文書へ反映する。

READMEは常に現在有効な入口、読込順序、正本一覧を示す。

詳細は `SERVER_CORE_PROTOCOL.md` と `docs/OPERATION_CHECKLIST.md` を正とする。

## PROJECT_STATUS運用
`PROJECT_STATUS.md` は現在状態と正本入口だけを記載する。

自動追記、毎作業終了時の無条件追記、AI独自判断による追記を禁止する。

管理者から明示的な状態更新指示がある場合だけ更新する。

`add-status.sh` による自動追記運用は廃止する。

## GitHub運用
作業履歴の正本は GitHub上のcommit / PR とする。

ファイル変更を伴う作業は、作業完了時に `git diff` を確認し、意味のある作業単位でcommitを作成する。

pushは、管理者が許可したリポジトリ、ブランチ、対象範囲で実行する。

詳細なcommit / push / PR基準は `SERVER_CORE_PROTOCOL.md` と `docs/OPERATION_CHECKLIST.md` を正とする。

## 最重要
記録されていない作業は存在しないものとして扱う。

ただし、AIが独自判断で記録を追記してはならない。

記録更新は、管理者の明示指示がある場合だけ行う。
