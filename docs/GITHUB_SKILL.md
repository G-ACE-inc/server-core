# GITHUB SKILL

## Purpose

GitHub関連Skillの参照Pathを固定versionに依存せず解決し、Workspace AIが利用可能なGitHub資源を重複実装・重複操作せず優先利用するためのresolver contract。

## Boundary

Skill実体は外部client/plugin環境が所有する。server-coreは固定cache version/pathをCurrent Authorityとして持たず、resolver scriptの利用方法と資源選択Ruleだけを管理する。

GitHub Skillを解決・読込・実行できることは、対象Repositoryへのwrite permission、server-core自体のmutation permission、client/plugin installation mutation permissionを意味しない。GitHub操作の前に対象Repositoryと許可されたOperationを別途確定する。

## Resource Priority

GitHub connectorがCurrent clientで利用可能な場合は、Repository / PR / Issue / CI / readback等の対応Operationをconnectorで行うことを優先する。local `git` / `gh` / Skillはconnectorで不足するOperation、Server-local state確認、または対象TaskのAuthorityが明示的に要求する範囲へ限定する。

同じGitHub情報をconnectorとlocal commandで理由なく重複取得しない。既に取得済みのCurrent Evidenceを再利用する。

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

## Known Skill Discovery Candidates

過去に確認されたGitHub Skill名は、Current inventoryを探すための候補として次を保持する。

- `github`
- `gh-address-comments`
- `gh-fix-ci`
- `yeet`

これらをCurrent利用可能と無条件に扱わない。実際に使うTaskではresolver / client inventoryでCurrent存在を確認する。Skill名やversionが変わった場合は固定Pathを推測しない。

## Operation Rule

- 固定version directoryをDocumentやScriptへ埋め込まない。
- Skill名が不明な場合は、利用client/plugin側のCurrent inventoryを確認する。
- resolverが失敗した場合は、固定Pathを推測せず、client/pluginのCurrent installation stateをreadbackする。
- Skillの存在、client登録、実行可否は別状態として扱う。
- GitHub Repository read/write、PR/Issue mutation、branch/ref mutation、Workflow mutation、server-core Repository mutationは別Operationとして扱う。
- GitHub操作自体のAuthority/permissionは対象Repositoryと利用clientのCurrent contractを正とする。
- resolverの存在・成功、Issue/PR template、owner label、Git history方針からmutation authorizationを推論しない。
- client/plugin installationやSkill inventoryを変更する場合は、そのclient側の明示的なchange boundaryを別途確認する。

## Non-goals

- 特定client versionの固定
- 過去のSkill候補をCurrent availableとして固定
- plugin cache内部構造のserver-core ownership
- GitHub Repository policyやapproval条件の上書き
