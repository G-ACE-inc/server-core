# GITHUB SKILL

## Purpose

GitHub関連Skillの参照Pathを固定versionに依存せず解決するためのresolver contract。

## Boundary

Skill実体は外部client/plugin環境が所有する。server-coreは固定cache version/pathをCurrent Authorityとして持たず、resolver scriptの利用方法だけを管理する。

resolverはSkillのPath/本文を見つけるためのread-only helperであり、GitHub Repository mutation permission、server-core mutation permission、client/plugin installation mutation permissionを付与しない。

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
- Skillの存在、Path解決、本文readback、client登録、実行可否、GitHub write permissionは別状態として扱う。
- resolver実行またはSkill本文を読むことを、対象Repositoryへのwrite/commit/push/merge permissionとして扱わない。
- GitHub操作自体のAuthority/permissionは対象Repositoryと利用clientのCurrent contractを正とする。
- server-core外Projectからresolverを利用しても、server-coreは参照元のままでありmutation対象へ昇格しない。

## Non-goals

- 特定client versionの固定
- 特定Skill一覧のCurrent Authority化
- plugin cache内部構造のserver-core ownership
- client/plugin installation stateの変更
- GitHub Repository policyやapproval条件の上書き
