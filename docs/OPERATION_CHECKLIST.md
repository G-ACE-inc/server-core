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

## 正本文書同期
1. 変更が構造、仕様、手順、自動化、運用ルールへ影響するか確認する。
2. Server Coreを変更した場合は `README.md` を必ず確認する。
3. READMEの入口、読込順序、正本一覧、主要原則に影響がある場合は同時に更新する。
4. 該当する正本文書を、変更後の正規仕様として現在形で更新する。
5. 作業報告、改善内容、修繕内容、変更履歴を正本文書の本文に書かない。
6. 実ファイルの変更と正本文書の内容が一致していることを確認する。

Workspace設定を変更した場合は、`/home/admin1/workspace/G-ACE.code-workspace` と `docs/G_ACE_WORKSPACE.md` が一致していることを確認する。

## commit前
1. `git diff` を確認する。
2. `git status --short` を確認する。
3. 対象外変更が含まれていないことを確認する。
4. `.env`, token, password, session, credentialが含まれていないことを確認する。
5. 意味のある作業単位に分けてstageする。
6. READMEと該当正本文書が変更後の正規仕様に同期していることを確認する。
7. commit messageは変更内容が一文で分かるものにする。

標準では `scripts/ai-auto-commit.sh --push` を使う。

## push前
1. `git log -1 --oneline` を確認する。
2. `git status --short --branch` を確認する。
3. push先remoteとbranchを確認する。
4. 管理者が許可したリポジトリ、ブランチ、対象範囲であることを確認する。

## 作業終了条件（必須）
ファイル変更を伴う作業は、以下がすべて完了して初めて「終了」とする。

1. 変更ファイルがcommit済みであること
2. commitがorigin/mainへpush済みであること
3. `git status` が `nothing to commit, working tree clean` を示すこと
4. 複数リポジトリを変更した場合は、それぞれで上記が完了していること

上記を満たさずに作業を終了することを禁止する。

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

## サブエージェント委任フロー

### 役割分担（絶対ルール）
- GPT-4.5Mini: 設計 / 初回計画 / 方針決定 / ASTERA反映 / 実装指示作成 / 合否判定
- composer: ファイル編集 / 実装 / 検証（ai-auto-commit.sh --push まで）
- gemini-flash: 広い読取 / 構造確認 / 影響範囲の洗い出し（読取専用）
- log: 巨大ログ圧縮・重要エラー抽出のみ
- Sonnet 4.6: 指揮・調整・状態確認のみ。直接実装・直接Shell操作禁止

### 委任トリガー
| トリガー | 委任先 |
|---------|--------|
| 目的・設計・方針が曖昧 | GPT-4.5Mini |
| 対象周辺を広く読む | gemini-flash |
| ファイル編集・実装・コマンド実行 | composer |
| ログ圧縮 | log |
| 変更の成否判定 | GPT-4.5Mini |

### ai-auto-commit.sh 標準手順（composer必須）
```bash
# 1. 作業ディレクトリ確認
cd /home/admin1/server-core  # または対象リポジトリroot

# 2. スクリプト存在確認（必須）
test -f scripts/ai-auto-commit.sh && echo "OK" || echo "ERROR: not found"

# 3. commit/push
scripts/ai-auto-commit.sh --push -m "種別: 変更内容"
```
- `存在しない` と即断する前に、必ず作業ディレクトリを `cd <repo-root>` で再確認する
- `.env` 系・secret・本番系変更は自動commit停止して報告する
