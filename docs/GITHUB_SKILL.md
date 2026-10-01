# GITHUB SKILL

## Purpose

GitHub関連Skillの参照Pathを固定versionに依存せず解決するためのresolver contract。

## Boundary

Skill実体は外部client/plugin環境が所有する。server-coreは固定cache version/pathをCurrent Authorityとして持たず、resolver scriptの利用方法だけを管理する。

## Standard Commands

GitHub umbrella skillのPathを解決する。

```bash
scripts/github-skill-path.sh
```

本文を読む。

```bash
scripts/github-skill-path.sh github --read
```

特定Skill名を解決する場合:

```bash
scripts/github-skill-path.sh <skill-name> --read
```

汎用resolverを使う場合:

```bash
scripts/resolve-codex-skill.sh github:<skill-name> --read
```

## Operation Rule

- 固定version directoryをDocumentやScriptへ埋め込まない。
- Skill名が不明な場合は、利用client/plugin側のCurrent inventoryを確認する。
- resolverが失敗した場合は、固定Pathを推測せず、client/pluginのCurrent installation stateをreadbackする。
- Skillの存在、client登録、実行可否は別状態として扱う。
- GitHub操作自体のAuthority/permissionは対象Repositoryと利用clientのCurrent contractを正とする。

## Non-goals

- 特定client versionの固定
- 特定Skill一覧のCurrent Authority化
- plugin cache内部構造のserver-core ownership
- GitHub Repository policyやapproval条件の上書き
