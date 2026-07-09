# OPERATION CHECKLIST

## 作業開始前
1. `pwd` を確認する。
2. `git status --short --branch` を対象リポジトリで確認する。
3. `README.md` と `docs/LOAD_SCOPE.md` を読む。
4. Server Core正本を読む。
5. 対象Projectの正本文書を読む。
6. `docker ps` で稼働状態を確認する。

通常作業では、`archive/`, `.github/`, `scripts/` を読まない。

必要な場合だけ、目的に合う該当ファイルを限定して読む。

## 変更前
1. 変更対象ファイルを特定する。
2. 既存の未コミット差分を確認する。
3. ユーザーまたは他作業者の差分を巻き戻さない。
4. 秘密情報を読まない、表示しない、commitしない。

## commit前
1. `git diff` を確認する。
2. `git status --short` を確認する。
3. 対象外変更が含まれていないことを確認する。
4. `.env`, token, password, session, credentialが含まれていないことを確認する。
5. 意味のある作業単位に分けてstageする。
6. commit messageは変更内容が一文で分かるものにする。

標準では `scripts/ai-auto-commit.sh --push` を使う。

## push前
1. `git log -1 --oneline` を確認する。
2. `git status --short --branch` を確認する。
3. push先remoteとbranchを確認する。
4. 管理者が許可したリポジトリ、ブランチ、対象範囲であることを確認する。

## PROJECT_STATUS更新時
1. 作業履歴を書かない。
2. 現在状態と正本入口だけを書く。
3. 確認していない状態を断定しない。
4. 確認日と確認範囲を明記する。

## archive退避時
1. 退避対象が現行正本から参照されていないことを確認する。
2. `archive/YYYY-MM-DD/` へ置く。
3. ファイル名で元用途と退避理由が分かるようにする。
4. 秘密情報を含むファイルはarchiveへ置かない。
5. archive内の文書を通常読込対象にしない。
