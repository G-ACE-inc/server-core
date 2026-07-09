#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/resolve-codex-skill.sh [plugin:]skill [--read]

Resolve a Codex plugin skill SKILL.md path without hard-coding the plugin
cache version. Defaults to the GitHub plugin when no plugin is supplied.

Examples:
  scripts/resolve-codex-skill.sh github
  scripts/resolve-codex-skill.sh github:gh-fix-ci --read
  scripts/resolve-codex-skill.sh github:yeet
USAGE
}

skill_ref="${1:-github}"
read_mode=0

if [[ "$skill_ref" == "-h" || "$skill_ref" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --read)
      read_mode=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

plugin="github"
skill="$skill_ref"

if [[ "$skill_ref" == *:* ]]; then
  plugin="${skill_ref%%:*}"
  skill="${skill_ref#*:}"
fi

if [[ -z "$plugin" || -z "$skill" ]]; then
  echo "ERROR: invalid skill reference: $skill_ref" >&2
  exit 2
fi

case "$plugin/$skill" in
  *".."*|*"/"*"/"*|*":"*)
    echo "ERROR: unsafe skill reference: $skill_ref" >&2
    exit 2
    ;;
esac

codex_home="${CODEX_HOME:-$HOME/.codex}"
cache_root="$codex_home/plugins/cache/openai-curated-remote/$plugin"
tmp_root="$codex_home/.tmp/plugins/plugins/$plugin"

candidates=()

if [[ -d "$cache_root" ]]; then
  while IFS= read -r path; do
    candidates+=("$path")
  done < <(find "$cache_root" -path "*/skills/$skill/SKILL.md" -type f | sort -V)
fi

if [[ ${#candidates[@]} -eq 0 && -d "$tmp_root" ]]; then
  while IFS= read -r path; do
    candidates+=("$path")
  done < <(find "$tmp_root" -path "*/skills/$skill/SKILL.md" -type f | sort -V)
fi

if [[ ${#candidates[@]} -eq 0 ]]; then
  echo "ERROR: skill not found: $plugin:$skill" >&2
  exit 1
fi

resolved="${candidates[-1]}"

if [[ "$read_mode" == "1" ]]; then
  sed -n '1,260p' "$resolved"
else
  printf '%s\n' "$resolved"
fi
