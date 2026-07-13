# SERVER CORE LOAD SCOPE

## 目的
AIが必要な情報だけを段階的に読み、古い履歴、対象外コード、補助スクリプトを現在仕様として誤読することと、不要なコンテキスト消費を防ぐ。

## 最小開始範囲
作業開始時に自動で読むのは次に限定する。

1. `README.md`
2. `docs/LOAD_SCOPE.md`
3. ユーザーが指定した対象ファイルまたは対象Projectの入口

全作業で `SERVER_CORE_PROTOCOL.md`、`CORE.md`、`KB.md`、`PROJECT_STATUS.md` を一律に全文読込してはならない。

## 目的別の正本読込
現在作業に必要な正本だけを読む。

- 5段、Module、Core、物理分離、公開契約: `CORE.md`
- 共通運用、GitHub、Docker、秘密情報、archive: `SERVER_CORE_PROTOCOL.md`
- 確認済み判断の照合: `KB.md`
- 現在状態またはProject入口: `PROJECT_STATUS.md`
- Server Core自身の構造: `docs/STRUCTURE.md`
- 用語または正式表記: `docs/GLOSSARY.md`
- 新規Project作成: `docs/PROJECT_TEMPLATE.md`
- デプロイ承認後: `docs/DEPLOY_RUNBOOK.md`
- 作業手順確認: `docs/OPERATION_CHECKLIST.md`
- 自動commit確認: `docs/AUTO_COMMIT.md`
- GitHub無料枠設定: `docs/GITHUB_FREE_MAX.md`
- GitHub skill確認: `docs/GITHUB_SKILL.md`
- G-ACE Workspace確認: `docs/G_ACE_WORKSPACE.md`

同じ目的の情報がコード、Manifest、文書へ重複している場合は、コード上のInterface、型、Schema、次に単一Manifest、次に正本文書の順で正本を判断する。

## AIへ渡す最小情報
通常変更では次の6項目を起点とする。

1. 変更目的
2. 対象Moduleまたは対象責務
3. 公開契約
4. 直接依存
5. 設定・状態の所有者
6. 期待結果と障害時動作

情報が既存コードから確認できる場合は、同じ内容を別文書へ複製しない。

## 段階的読込

### Level 1: 局所
- 対象コード
- 公開契約
- 直接依存
- 関連テスト

### Level 2: 境界
- 呼出元
- 呼出先
- 設定所有者
- 状態所有者

### Level 3: Module
- 対象Module全体
- Module登録情報
- Lifecycleと障害時動作

### Level 4: System
- 関連System
- 複数Moduleの連携
- 必要な場合だけ対象リポジトリ全体

最初からLevel 3またはLevel 4を読み込まない。

## 読込範囲を拡張する条件
次のいずれかを実際に確認した場合だけ、1段階ずつ拡張する。

- 責務、設定、状態の所有者を特定できない
- 宣言されていない依存が見つかった
- 変更対象外のテストが失敗した
- 循環依存または内部実装参照の可能性がある
- 公開契約変更が複数Moduleへ影響する
- 期待結果を満たすために対象外変更が必要である

拡張理由を説明できない読込は禁止する。

## 通常読込禁止
作業開始時、次を読んではならない。

- `archive/`
- `.github/`
- `scripts/`
- `.env`、secrets、credential
- `node_modules/`
- `dist/`、`build/`、`.next/`
- `logs/`、dumps、cache

## 例外
ユーザーが明示した場合、または現在作業に直接必要な場合だけ、対象ファイルを限定して読む。

例:
- GitHub Actions修正では対象workflowだけを読む。
- 自動commit修正では `scripts/ai-auto-commit.sh` だけを読む。
- 旧履歴確認では `archive/` 内の該当ファイルだけを読む。

## 禁止
- リポジトリ全体を既定でスキャンすること
- archive内の情報を現在状態として扱うこと
- scriptsや.githubを通常コンテキストとして読むこと
- 同じ情報を複数文書から重複読込すること
- 調査理由なしに読込Levelを拡張すること
