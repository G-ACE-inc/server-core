# G-ACE WORKSPACE

## 目的
`/home/admin1/workspace/G-ACE.code-workspace` を、全作業でServer Coreルールが先に効くWorkspaceとして定義する。

## 正本ファイル
Workspace実体:

```text
/home/admin1/workspace/G-ACE.code-workspace
```

Server Core上の正規仕様:

```text
/home/admin1/server-core/docs/G_ACE_WORKSPACE.md
```

## Workspace folders
通常作業で開くfolderは次に限定する。

- `/home/admin1/server-core`
- `/home/admin1/projects`

## 通常folderに含めないもの
次は通常作業のWorkspace folderに含めない。

- `/home/admin1/workspace`
- `/home/admin1/kb`
- `/home/admin1/logs`
- `/home/admin1/backups`

## 理由
- `server-core` を先頭に置き、AIが共通ルールを最初に確認できるようにする。
- `projects` を作業対象の集合として扱う。
- `logs`, `backups`, `kb`, `workspace` は、通常作業で誤読、誤検索、誤編集する危険があるため外す。

## Workspace settings
Workspaceには、次のServer Core情報を設定として持たせる。

- `codex.serverCore.loadScope`
- `codex.serverCore.workspaceRule`
- `codex.serverCore.requiredStartFiles`
- `codex.serverCore.requiredStartRule`
- `codex.serverCore.finishRule`
- `codex.serverCore.neverUseAsNormalContext`

これらはVS Code標準機能ではなく、AI・作業者向けの明示的な運用ヒントである。

## Workspace rule
`codex.serverCore.workspaceRule` は次を示す。

このG-ACE Workspace内の全作業は、必ずserver-coreの正本を先に読み、変更後はREADMEと該当正本文書を現在有効な正規仕様として同期し、GitHubへcommit / pushして終える。

## Required start rule
`codex.serverCore.requiredStartRule` は次を示す。

1. `README.md` を読む。
2. `docs/LOAD_SCOPE.md` を読む。
3. `SERVER_CORE_PROTOCOL.md` を読む。
4. `CORE.md`, `KB.md`, `PROJECT_STATUS.md` を読む。
5. `archive`, `.github`, `scripts` は通常読込しない。必要な場合だけ対象ファイルを限定して読む。

## Finish rule
`codex.serverCore.finishRule` は次を示す。

- 作業報告や改善メモではなく、変更後に有効な正規仕様としてREADMEと該当正本文書を更新する。
- 実ファイルと正本文書が一致していることを確認する。
- `scripts/ai-auto-commit.sh --push` でGitHubへcommit / pushする。
- 本番起動、公開、切替は管理者の明示承認なしに行わない。

## Normal context exclusions
`codex.serverCore.neverUseAsNormalContext` は次を示す。

- `archive/`
- `.github/`
- `scripts/`
- `/home/admin1/logs`
- `/home/admin1/backups`
- `/home/admin1/kb`
- `/home/admin1/workspace`

## Search / watcher除外
通常検索と監視から次を外す。

- `.git`
- `.github`
- `.tgs-state`
- `archive`
- `backups`
- `build`
- `coverage`
- `dist`
- `logs`
- `node_modules`

## Workspace tasks
Workspaceには次のtaskを置く。

- `server-core: show load scope`
- `server-core: auto commit and push`

## 変更時
`G-ACE.code-workspace` を変更した場合は、この文書と `README.md` を確認し、変更後の正規仕様として同期する。

旧Workspace設定を退避する場合は `/home/admin1/workspace/archive/YYYY-MM-DD/` へ置く。
