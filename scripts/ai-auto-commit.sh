#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ai-auto-commit.sh --authorize-server-core-mutation [--push] [-m "message"]

Stages, validates, commits, and optionally pushes changes for the server-core
repository only. It refuses to run without an explicit server-core mutation
authorization flag and refuses protected-branch direct commits.

Options:
  --authorize-server-core-mutation
                  Required. Use only when server-core itself has explicit
                  owner authorization for mutation in the current task.
  --push          Push the created commit to origin/current-branch.
  --no-push       Commit only. This is the default unless AI_AUTO_PUSH=1.
  -m, --message   Commit message. If omitted, a message is generated.
  -h, --help      Show this help.
USAGE
}

push_mode="${AI_AUTO_PUSH:-0}"
message=""
authorized=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --authorize-server-core-mutation)
      authorized=1
      shift
      ;;
    --push)
      push_mode=1
      shift
      ;;
    --no-push)
      push_mode=0
      shift
      ;;
    -m|--message)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: missing commit message after $1" >&2
        exit 2
      fi
      message="$2"
      shift 2
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

if [[ "$authorized" != "1" ]]; then
  echo "ERROR: server-core is read-only unless server-core mutation is explicitly authorized." >&2
  echo "Re-run only after explicit authorization with: --authorize-server-core-mutation" >&2
  exit 1
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
expected_root="$(cd -- "$script_dir/.." && pwd -P)"
repo_root="$(git -C "$expected_root" rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -z "$repo_root" ]]; then
  echo "ERROR: server-core repository root could not be resolved from script location." >&2
  exit 1
fi

repo_root="$(cd -- "$repo_root" && pwd -P)"
if [[ "$repo_root" != "$expected_root" ]]; then
  echo "ERROR: repository identity mismatch." >&2
  echo "EXPECTED=$expected_root" >&2
  echo "ACTUAL=$repo_root" >&2
  exit 1
fi

cd "$repo_root"

branch="$(git branch --show-current)"
if [[ -z "$branch" ]]; then
  echo "ERROR: detached HEAD is not supported for auto-commit." >&2
  exit 1
fi

case "$branch" in
  main|master)
    echo "ERROR: refusing direct auto-commit on protected branch: $branch" >&2
    exit 1
    ;;
esac

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No changes to commit."
  exit 0
fi

changed_files="$(git status --porcelain=v1 | sed -E 's/^...//' | sed -E 's/^.* -> //' | sort -u)"

blocked_env="$(printf '%s\n' "$changed_files" | grep -E '(^|/)\.env($|\.)' | grep -Ev '(^|/)\.env\.example$' || true)"
if [[ -n "$blocked_env" ]]; then
  echo "ERROR: refusing to commit environment/secret files:" >&2
  printf '%s\n' "$blocked_env" >&2
  exit 1
fi

scan_files=()
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  [[ -f "$path" ]] || continue
  scan_files+=("$path")
done <<< "$changed_files"

if [[ ${#scan_files[@]} -gt 0 ]]; then
  secret_hits="$(
    grep -nEI '(api[_-]?key|secret|token|password|credential|session)[[:alnum:]_ -]*[:=][[:space:]]*[\"]?[A-Za-z0-9_./+=-]{12,}' "${scan_files[@]}" 2>/dev/null || true
  )"
  if [[ -n "$secret_hits" ]]; then
    echo "ERROR: refusing to commit likely secret material:" >&2
    printf '%s\n' "$secret_hits" >&2
    exit 1
  fi
fi

git diff --check
git add -A
git diff --cached --check

shell_files=()
while IFS= read -r path; do
  [[ -f "$path" ]] || continue
  case "$path" in
    *.sh) shell_files+=("$path") ;;
  esac
done < <(git diff --cached --name-only)

for shell_file in "${shell_files[@]}"; do
  bash -n "$shell_file"
done

if [[ -z "$message" ]]; then
  mapfile -t staged < <(git diff --cached --name-only | sort)
  count="${#staged[@]}"
  summary="$(printf '%s\n' "${staged[@]:0:3}" | paste -sd ', ' -)"
  if [[ "$count" -gt 3 ]]; then
    summary="$summary and $((count - 3)) more"
  fi
  message="server-core: ${summary}"
fi

git commit -m "$message"

if [[ "$push_mode" == "1" ]]; then
  git push origin "$branch"
fi
