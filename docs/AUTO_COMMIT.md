# AUTO COMMIT

## 目的
AI作業後のcommit / pushを標準化し、作業履歴をGitHubへ確実に残す。

## 絶対ルール
**作業完了＝commit / push完了。これを省略した作業は「未完了」として扱う。**

AIおよび作業者は、ファイル変更を伴うすべての作業において、作業の最終ステップとして必ずcommit / pushを実行する。

確認・調査・読取のみで変更がない場合は除く。

## 標準コマンド
ファイル変更を伴う作業が完了したら、必ず次を実行する。

```bash
cd <対象リポジトリのルート>
scripts/ai-auto-commit.sh --push
```

commit messageを指定する場合:

```bash
scripts/ai-auto-commit.sh --push -m "Feat: xxxxxx"
```

## スクリプトが自動で行うこと
- 変更ファイルの確認
- `.env` 系ファイルのcommit拒否
- secretらしい代入値の簡易検出
- `git diff --check`
- shell scriptの `bash -n`
- `git add -A`
- commit作成
- `--push` 指定時の `git push origin <current-branch>`

## commit messageの形式
`<種別>: <変更内容が一文で分かる説明>`

種別:
- `Feat:` 新機能・新定義の追加
- `Fix:` バグ修正・誤り修正
- `Docs:` 文書のみの変更
- `Chore:` 設定・スクリプト・ツールの変更
- `Refactor:` 動作を変えないコード整理

## 複数リポジトリにまたがる場合
リポジトリごとに個別にcommit / pushする。まとめてcommitしない。

## 使わない場合（例外）
次の場合は自動commitを止め、管理者へ確認する。

- `.env` やsecretが関係する
- 本番起動、公開、切替を含む
- 未検証の途中状態を残す必要がある
- 管理者がcommit / push禁止を明示した

## 違反
次の行為は違反とする。

- ファイルを変更したのにcommit / pushせずに作業を終了すること
- `scripts/ai-auto-commit.sh` を使わずに手動でcommitすること（やむを得ない場合は理由をcommit messageに明記する）
- `PROJECT_STATUS.md` に作業履歴として記録すること（commit / PRを正本とする）
- 複数リポジトリの変更を1つのcommitにまとめること
