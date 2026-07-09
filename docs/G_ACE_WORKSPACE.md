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
- `codex.serverCore.requiredStartFiles`
- `codex.serverCore.finishRule`

これらはVS Code標準機能ではなく、AI・作業者向けの明示的な運用ヒントである。

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
