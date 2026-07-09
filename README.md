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
2. `SERVER_CORE_PROTOCOL.md`
3. `CORE.md`
4. `KB.md`
5. `PROJECT_STATUS.md`

## 正本の役割
- `CORE.md`: 共通思想
- `SERVER_CORE_PROTOCOL.md`: 共通運用規則
- `KB.md`: Server Core上の確認済み知識・判断記録
- `PROJECT_STATUS.md`: 現在状態と正本入口
- TGServer詳細: `/home/admin1/projects/TGserver` 側の正本文書

## 主要原則
- AIは管理者承認なしに正本を変更しない。
- Telegramを生ログの永続正本とする。
- VPSを永続ログ保管庫にしない。
- `/home/admin1/logs` は全体共通の分離ディスクキャッシュとする。
- KBシステムは未実装である。
- TGServerからKBへ直接送信しない。
- 本番運用はDocker / Docker Composeで確定済みである。

## PROJECT_STATUS運用
`PROJECT_STATUS.md` は現在状態と正本入口だけを記載する。

自動追記、毎作業終了時の無条件追記、AI独自判断による追記を禁止する。

管理者から明示的な状態更新指示がある場合だけ更新する。

`add-status.sh` による自動追記運用は廃止する。

## GitHub運用
作業履歴の正本は GitHub上のcommit / PR とする。

ファイル変更を伴う作業は、作業完了時に `git diff` を確認し、意味のある作業単位でcommitを作成する。

pushは、管理者が許可したリポジトリ、ブランチ、対象範囲で実行する。

## 最重要
記録されていない作業は存在しないものとして扱う。

ただし、AIが独自判断で記録を追記してはならない。

記録更新は、管理者の明示指示がある場合だけ行う。
