# SERVER CORE LOAD SCOPE / ROUTER

## 目的

G-ACE Workspace内のAI / Developerが必ずserver-coreを入口にしつつ、今回の作業に必要な情報だけを段階的に読み、Context・Token・探索時間を増やさず確実に作業する。

## 最小開始範囲

Workspace内の作業開始時は次の順を固定する。

```text
1. server-core/README.md
2. server-core/docs/LOAD_SCOPE.md
3. 今回の作業に必要なserver-core正本だけ
4. 対象Project README
5. 対象Project内の必要なDesign / Tree / Delta / System Document / Source / Testだけ
```

README以外のserver-core正本を新CHAT/新Taskで一括読込しない。

同じTask範囲で一度確認済みの正本は、変更や情報不足が無い限り毎ターン再読込しない。

## Task Routing

| Task | server-coreで追加読込するAuthority |
|---|---|
| 開発方法論 / 責務 / 5段 / Module / 再利用 | `CORE.md` |
| 共通運用 / 禁止事項 / Server境界 | `SERVER_CORE_PROTOCOL.md` |
| Workspace設定・入口 | `docs/G_ACE_WORKSPACE.md` |
| Git / Commit / Push | `docs/AUTO_COMMIT.md` |
| Deploy | `docs/DEPLOY_RUNBOOK.md` |
| 新規Project / Document構成 | `docs/PROJECT_TEMPLATE.md` |
| Cloudflare | `docs/CLOUDFLARE_OPERATIONS.md` |
| Shared Secret / Token | `docs/WORKSPACE_SHARED_SECRETS.md` |
| 用語 | `docs/GLOSSARY.md` |
| server-core構造 | `docs/STRUCTURE.md` |
| server-core設計判断 | `docs/SERVER_CORE_DESIGN.md` |
| Current Project / Runtime入口 | `PROJECT_STATUS.md` + 必要な実Runtime readback |

複合作業では必要なAuthorityだけ組み合わせる。

## Target Repository Loading

対象Projectへ入った後はREADMEを入口とする。

### Level 0: Repository Entry
- README Current State
- Designへのリンク
- Project Treeへのリンク
- Design Deltaへのリンク
- Completed System / Feature-bundle Documentへのリンク

存在しないDocumentを推測で作成済み扱いしない。

### Level 1: 対象
- 対象Source
- Input / Output
- 直接依存
- 関連Test
- 明示された再利用候補

読込はLevel 1から開始する。通常変更もLevel 1で閉じられるならそこで止める。

### Level 2: 境界
次の場合だけ拡張する。
- 呼出元 / 呼出先が必要
- Config / State ownerが不明
- Interface / Schema契約の確認が必要
- 近接再利用候補の確認が必要

### Level 3: 再利用単位
次の場合だけModule / Component範囲へ拡張する。
- 同じ責務の既存実装比較が必要
- Adapter / shared contract検討が必要
- 責務混在 / 循環依存の可能性がある

### Level 4: System
次の場合だけSystem / Repository全体へ拡張する。
- 複数Component / Moduleへ影響
- 影響範囲を局所情報で閉じられない
- Masterが全体監査 / 全コード確認 / 横断調査を明示

## 再利用探索

新規Code・Module・Document作成前に、必要範囲で次を確認する。

```text
対象Project内
  -> Workspace内の既存共有資産
  -> 登録済みKB / Tool / MCP（利用可能な場合）
  -> 必要な場合だけ公式外部資料
```

再利用判断:

```text
そのまま利用
  -> 設定 / 引数 / 型調整
  -> 薄いAdapter
  -> 共通部分抽出
  -> 新規実装
```

## Normal Context Exclusions

以下は通常Contextへ入れない。
- `archive/`
- `.github/`（GitHub Actions / PR / Issue等がTask対象の場合を除く）
- `scripts/`（Script自体がTask対象の場合を除く）
- `.git/`
- `node_modules/`
- `dist/` / `build/` / `.next/`
- logs / dumps / cache
- backups
- Secret / credential実値

Task対象になった場合だけ必要Fileへ限定して読む。

## Documentation Read Rule

READMEはCurrent State入口。DesignはBaseline。Design Deltaは意図的差分と理由。Commitは実作業履歴。

DesignとCurrent実装が違う場合、DesignをCurrentへ合わせて履歴を消さない。

完成したFeature束 / System / reusable ModuleについてREADMEだけでは引継ぎ不能な場合、既存Documentを更新するかSystem/Module Documentを作成しREADMEから到達可能にする。

## Runtime / Registry Rule

`PROJECT_STATUS.md`、registry、READMEに書かれたContainer / Port / Domain / Runtime状態は探索入口であり、実Runtimeの代用ではない。

Current状態が必要なら対象Provider / Docker / GitHub / Endpoint等をreadbackする。

## 読込完了条件

作業開始に必要な読込は、次を説明・確認できた時点で止める。
- 目的と期待結果
- 対象責務
- Design上の基準線（必要な場合）
- 入力 / 出力
- 直接依存 / 制約
- 再利用候補
- 関連Test / Verify方法
- 影響範囲

不足が発生した場合だけ次Levelへ進む。
