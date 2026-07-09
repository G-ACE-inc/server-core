# AUTO COMMIT

## 目的
AI作業後のcommit / pushを標準化し、作業履歴をGitHubへ確実に残す。

## 標準コマンド
ファイル変更を伴う作業が完了したら、原則として次を実行する。

```bash
scripts/ai-auto-commit.sh --push
```

commit messageを指定する場合:

```bash
scripts/ai-auto-commit.sh --push -m "Improve server-core GitHub automation"
```

## 自動で行うこと
- 変更ファイルの確認
- `.env` 系ファイルのcommit拒否
- secretらしい代入値の簡易検出
- `git diff --check`
- shell scriptの `bash -n`
- `git add -A`
- commit作成
- `--push` 指定時の `git push origin <current-branch>`

## 使わない場合
次の場合は自動commitを止め、管理者へ確認する。

- 変更範囲が複数Projectにまたがる
- `.env` やsecretが関係する
- 本番起動、公開、切替を含む
- 未検証の途中状態を残す必要がある
- 管理者がcommit / push禁止を明示した

## 運用
AI・作業者は、管理者が明示的に禁止した場合を除き、作業完了時にこのスクリプトでcommit / pushする。

作業履歴の正本はGitHub上のcommit / PRであり、`PROJECT_STATUS.md` には作業履歴を蓄積しない。
