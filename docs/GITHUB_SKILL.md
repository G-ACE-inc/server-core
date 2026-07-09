# GITHUB SKILL

## 目的
Codex GitHub plugin skillの参照パスを固定バージョンに依存せず解決する。

## 背景
GitHub skillはCodex plugin cache配下に配置される。

cacheのバージョンディレクトリは更新されるため、次のような固定パスを正本にしてはならない。

```text
/home/admin1/.codex/plugins/cache/openai-curated-remote/github/0.1.7-.../skills/github/SKILL.md
```

実環境では `0.1.8-...` のように変わる。

## 標準コマンド
GitHub umbrella skillのパスを表示する。

```bash
scripts/github-skill-path.sh
```

本文を読む。

```bash
scripts/github-skill-path.sh github --read
```

専門skillを読む。

```bash
scripts/github-skill-path.sh gh-fix-ci --read
scripts/github-skill-path.sh gh-address-comments --read
scripts/github-skill-path.sh yeet --read
```

汎用resolverを使う場合:

```bash
scripts/resolve-codex-skill.sh github:github --read
```

## 現在確認済みのGitHub skill
- `github`
- `gh-address-comments`
- `gh-fix-ci`
- `yeet`

## 運用
GitHub作業を行う場合、まず `github` skillを読み、必要に応じて専門skillへ進む。

固定パスが失敗した場合は、直接探し直すのではなく `scripts/github-skill-path.sh` を使う。

GitHub connectorが利用可能な場合はconnectorを優先し、ローカル `git` と `gh` は不足分に限定する。
