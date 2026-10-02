# G-ACE WORKSPACE

Version: 2026-10-03
Role: G-ACE Workspaceでserver-core司令室を必ず起点にして作業するための正規運用契約。

## 1. Purpose

標準Workspace `/home/admin1/workspace/G-ACE.code-workspace` では、AI / Developerはserver-coreを共通Command Centerとして使用する。

server-coreはTask routing、共通Authority、shared capability discovery、GitHub work history、operations boundaryを管理する。Project固有Design / Source / Test / Runtime logic / Project Documentは各Projectが所有する。

## 2. Mandatory Entry

Workspace作業は必ず次から開始する。

```text
/home/admin1/server-core/README.md
  -> /home/admin1/server-core/docs/LOAD_SCOPE.md
  -> 今回必要なserver-core Authorityだけ
  -> 対象Project README
  -> 対象Projectの必要Authority / Source / Testだけ
```

Masterが新規チャット冒頭でこの指示を繰り返さなくてもAI側で適用されることをWorkspace要件とする。Cursorは `/home/admin1/server-core/.cursor/rules/00_agent_runtime.mdc` の `alwaysApply: true` を正とする。VS Code / GitHub Copilot系は `/home/admin1/server-core/.github/copilot-instructions.md`、複数Agent互換入口は `/home/admin1/server-core/AGENTS.md` を正とし、Workspace初期化時に `/home/admin1/projects` ルートへ同一正本のSymlinkを作成する。Workspace checkerはこれらのリンクとAI instruction設定を検証する。

Instruction Fileが存在することだけを実Client適用済みの証明にはしない。Current live WorkspaceではClient側の実読込/readbackも別に確認する。

server-core全正本の一括読込は禁止する。同一Taskで既に確認済みのAuthorityは、変更・矛盾・情報不足が無い限り繰り返し読まない。

## 3. Command-Center Dispatch

Taskを受けたAI / Developerは、作業開始前に必要範囲で次を確定する。

```text
PURPOSE
EXPECTED_RESULT
TARGET_PROJECT
TARGET_RESPONSIBILITY
TARGET_REPOSITORY
MUTATION_REPOSITORIES
READ_ONLY_REPOSITORIES
SERVER_CORE_MUTATION_AUTHORIZED
REQUIRED_SERVER_CORE_AUTHORITY
REQUIRED_PROJECT_AUTHORITY
REUSE_CANDIDATES
VERIFY_PATH
APPROVAL_BOUNDARY
CHANGE_BOUNDARY
CONTEXT_SCOPE
BLOCKER
```

対象Projectや責務が不明な場合は `docs/WORKSPACE_REGISTRY.md` でownerを確認する。既存owner / reusable assetを確認せず新規Project / Module / Tool / Documentを作らない。

不明項目を推測で埋めない。作業開始に必要な項目が未確定なら、必要なAuthority/readbackだけ追加取得してから固定ルーティーンへ進む。

## 4. Repository Mutation Ownership

Project Taskの既定mutation先は対象Project Repository。

```text
Target Project source/docs/config = target Project ownership
server-core = routing/reference; server-core自体の明示許可が無い限りread-only
Shared Capability owner = ordinary use/integrationではread-only
Provider/service owner = owner-side changeが実際に必要と確認されるまでread-only
```

`SERVER_CORE_MUTATION_AUTHORIZED=YES` が明示的に成立しない限り、server-coreを `MUTATION_REPOSITORIES` に入れない。

複数Repository変更が必要な場合は、Repositoryごとに変更理由・範囲・verification・Git historyを分離する。

複数Project / Agent / change unitが同時進行し得るため、別Taskのuncommitted diffをstage / overwriteしない。shared checkoutのswitch/reset/rebaseは他Taskへの影響を閉じられない限り行わない。readbackだけならGit object/API inspectionを優先する。

## 5. Workspace Folders

通常Folder:
- `/home/admin1/server-core`
- `/home/admin1/projects`

通常Workspace Contextへ含めない:
- `/home/admin1/workspace`
- `/home/admin1/logs`
- `/home/admin1/backups`
- archive / build / dist / dependency / cache / dump領域

Task対象になった場合だけ必要範囲を開く。

## 6. Project Entry

対象ProjectではREADMEを入口にする。

READMEから、存在する場合は次へ直接到達できる状態を標準とする。
- Design
- Project Tree
- Design Delta
- completed System / Feature-bundle / Module documents
- run / test / verify entry points

これらは対象Project側のAuthorityである。対象ProjectのREADMEやREADME-linked Document更新をserver-core Document更新へ読み替えない。

対象Source、直接依存、関連Testから開始し、必要時だけ `docs/LOAD_SCOPE.md` のLevelに従ってContextを広げる。

## 7. Development Routine

```text
server-core command center
  -> target Project README
  -> required Design / Tree / Delta / System Document
  -> repository / branch / HEAD / status
  -> Source / direct dependency / tests
  -> reuse check
  -> implementation / debug
  -> diff
  -> verification
  -> documentation gate
  -> GitHub commit as work report
  -> push / remote readback
  -> PR / CI when required
  -> approval boundary
  -> deploy/runtime only when authorized
```

この順序を通常ルーティーンとして維持し、必要工程を理由なく省略しない。
