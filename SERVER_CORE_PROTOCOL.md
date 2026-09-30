# SERVER CORE OPERATION PROTOCOL

## 目的

本規則はG-ACE Workspace全体で共通に適用する運用・変更権限・GitHub・Runtime・Secret・Storage境界だけを定める。

詳細な開発方法論、Project構成、Context routing、Deploy、Storage lifecycle等をここへ重複記載しない。Taskに応じて `README.md` -> `docs/LOAD_SCOPE.md` から該当Authorityを読む。

人間、AI、自動処理のすべてに適用する。

## Authority / Approval

最終決定者はMaster。

質問、検討、提案、操作説明を変更承認として扱わない。未確認状態を推測で補完しない。

Masterの明示指示なしに次を実行しない。
- main / PR merge
- Production deploy / 公開 / 切替
- Force push / Branch削除 / destructive reset / rebase
- 稼働中Serviceの停止 / recreate
- Secret追加・削除・rotation
- Provider resourceの作成・変更・削除
- 新規Model download

## Workspace Entry

Workspace作業は必ず次から開始する。

```text
server-core/README.md
  -> server-core/docs/LOAD_SCOPE.md
  -> 今回必要なserver-core Authorityだけ
  -> 対象Project README
  -> 必要なProject Authority / Source / Testだけ
```

全正本の一括読込を行わない。

標準Workspaceは `/home/admin1/workspace/G-ACE.code-workspace`。

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

通常Contextに含めない:
- `/home/admin1/logs`
- `/home/admin1/backups`
- `/home/admin1/kb`
- `/home/admin1/workspace`
- archive / build / dist / node_modules / cache / dumps

Workspace正規仕様は `docs/G_ACE_WORKSPACE.md`。

## Development Boundary

開発方法論・再利用・5段Architecture・Module判断は `CORE.md` を正とする。

Project構成、README / Design / Project Tree / Design Delta / System Document作成条件、Documentation Gateは `docs/PROJECT_TEMPLATE.md` を正とする。

DesignをCurrent実装へ合わせて履歴が消える形で上書きしない。

公開契約は可能な限りCode上のInterface / Type / Schemaを正本とし、Project固有の詳細は各Projectに置く。

## Validation

変更の合否は、必要範囲で以下を確認する。
- Input
- execution condition
- expected output
- changed state
- state that must not change
- regression
- major failure cases
- Runtime / Provider readback when relevant

Process起動、Error無し、`True`、空配列、HTTP 200、Build成功、CI greenだけではPASSとしない。

未実行・未確認・未検証は `NOT_EXECUTED / UNKNOWN / NOT_VERIFIED` を維持する。

## Documentation / Work History

Current仕様を示す正本文書へ作業日誌を混在させない。

作業履歴の正本はGitHub commit / PR。

完成・検証状態、Project構造、Designとの差、完成System等が変わった場合はDocumentation Gateに従い該当文書を更新する。

Commit作業報告、Push、Remote Readbackは `docs/AUTO_COMMIT.md` を正とする。

## GitHub / Deploy

GitHubへ保存されたrevisionとServer Runtimeを別状態として扱う。

標準経路:

```text
implementation / fix
 -> verify
 -> documentation gate
 -> commit as work report
 -> push
 -> remote readback
 -> PR / CI when required
 -> confirmed GitHub revision
 -> required Master approval
 -> Server deploy
 -> Runtime verification
```

Deploy詳細は `docs/DEPLOY_RUNBOOK.md`。

Server上の直接Source修正を正式開発履歴の代替にしない。Runtimeで修正が必要になった場合も、原則としてRepository開発Loopへ戻す。

## Shared Capability Discovery

Workspace共通Project / MCP / Tool / Secret Contract / Runtime入口は `docs/WORKSPACE_REGISTRY.md` をDiscovery Authorityとする。

Registry記載だけでCurrent Runtimeを証明しない。必要時は実設定・実Provider・Endpoint・Docker・GitHub等をreadbackする。

Capability本体をserver-coreへ移植しない。server-coreは入口・契約・所有者・権限境界を管理する。

## DebugAI

DebugAIは独立Project/runtime。

Current verified shared accessはCLI / HTTP。DebugAI MCPはDebugAI側で実装・検証され、Workspace設定へ登録されるまで `NOT_IMPLEMENTED` とする。

## Knowledge Base

再利用開発KBのDesign Baselineは `docs/KB_REUSE_DESIGN.md`。

Target storageはMaster PC `F:` 1 TB drive。

server-coreはKB data本体を保持せず、Access / Registration / Lifecycle / Safety Contractを管理する。

Server/VPSからPC filesystemを直接読める前提を置かない。実装・検証済みAPI/MCP等のBridgeを使用する。

次を禁止する。
- 生ログの直接KB化
- 判定基準なしの自動知識化
- 未検証AI出力をvalidated assetとして登録
- Secret / Token / credentialのKB保存
- 未実装Bridgeを利用可能として扱う

## Log / Cache / Cleanup / Backup

詳細Design Baselineは `docs/STORAGE_LIFECYCLE.md`。

共通境界:
- Telegram: owning Project contractで定義されたdurable raw-log authority
- Meilisearch: rebuildable search index
- Redis: dedup / hot-cache
- `/home/admin1/logs`: temporary operational disk state
- VPS: processing/runtime environment
- `/home/admin1/backups`: backup area。単なるcleanup対象ではない

Generic automatic cleanupはfail-closedにする。

自動削除禁止:
- owner不明
- active use
- 未送信 / retry pending
- recovery required
- active transaction / lock
- restore/rebuild path不明
- Docker volumeを含むpersistent state

`docker system prune -a --volumes` の汎用定期実行は禁止する。

## Docker / Runtime

本番常駐の標準経路はDocker / Docker Compose。

本番常駐で次を原則禁止する。
- node直接常駐
- python直接常駐
- pm2 / nohup / screen / tmux常駐

短時間の診断・検証Commandと本番常駐を区別する。

Container起動だけでRuntime PASSとせず、必要なEndpoint / Output / State / side effectまで確認する。

## Secret / Token

Secret / Token / password / session / credentialをGit / Chat / Log / Documentへ保存しない。

`.env` はcommit禁止。共有が必要なkey名は値なし `.env.example` に記載できる。

Workspace共有Secretは `docs/WORKSPACE_SHARED_SECRETS.md` を正とし、各Projectへ実値を複製しない。

## Archive

旧版・退避は `archive/YYYY-MM-DD/` を基本とする。

- Secretをarchiveへ保存しない
- archiveをCurrent state / Design / Ruleとして扱わない
- 通常Contextへ入れない

## Absolute Prohibitions

- 推測を事実として扱う
- 未実行を実行済み、未検証をPASSにする
- Testをskip/deleteして完成扱いにする
- Design履歴を消す上書き
- 作業履歴をCurrent仕様文書へ混在
- 目的のないFile / Document / Module追加
- Secret / Token実値の保存・commit
- 未実装Capabilityを利用可能として扱う
- `/home/admin1/logs` を永続保管庫として使う
- KBへの無判定直接投入
- Server cleanupでowner不明・active・recovery dataを削除

## Related Authorities

- Development methodology: `CORE.md`
- Workspace routing: `docs/LOAD_SCOPE.md`
- Workspace contract: `docs/G_ACE_WORKSPACE.md`
- Project/document standard: `docs/PROJECT_TEMPLATE.md`
- Shared registry: `docs/WORKSPACE_REGISTRY.md`
- Reuse KB design: `docs/KB_REUSE_DESIGN.md`
- Storage lifecycle: `docs/STORAGE_LIFECYCLE.md`
- GitHub work report: `docs/AUTO_COMMIT.md`
- Deploy: `docs/DEPLOY_RUNBOOK.md`
- Shared secrets: `docs/WORKSPACE_SHARED_SECRETS.md`
