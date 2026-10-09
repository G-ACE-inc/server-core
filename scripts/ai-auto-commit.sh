#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ai-auto-commit.sh [--push] [-m "message"]

Automatically stages, validates, commits, and optionally pushes the current
repository changes. Intended for AI-assisted work in server-core projects.

Options:
  --push          Push the created commit to origin/current-branch.
  --no-push       Commit only. This is the default unless AI_AUTO_PUSH=1.
  -m, --message   Commit message. If omitted, a message is generated.
  -h, --help      Show this help.
USAGE
}

push_mode="${AI_AUTO_PUSH:-0}"
message=""

while [[ $# -gt 0 ]]; do
  case "$1" in
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

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

branch="$(git branch --show-current)"
if [[ -z "$branch" ]]; then
  echo "ERROR: detached HEAD is not supported for auto-commit." >&2
  exit 1
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No changes to commit."
  exit 0
fi

changed_paths=()
rehydrate_collect="${repo_root}/scripts/gace_mutation_rehydrate_check.py"
if [[ -f "$rehydrate_collect" ]]; then
  mapfile -t changed_paths < <(python3 "$rehydrate_collect" --collect-changed-paths --repo-root "$repo_root" 2>/dev/null || true)
fi
if ((${#changed_paths[@]} == 0)); then
  while IFS= read -r -d '' record; do
    [[ ${#record} -lt 4 ]] && continue
    path="${record:3}"
    xy="${record:0:2}"
    case "$xy" in
      *R*|*C*)
        changed_paths+=("$path")
        if IFS= read -r -d '' oldpath; then
          changed_paths+=("$oldpath")
        fi
        continue
        ;;
    esac
    case "$path" in
      *" -> "*) path="${path#* -> }" ;;
    esac
    changed_paths+=("$path")
  done < <(git status --porcelain=v1 -z)
fi

blocked_env=""
for path in "${changed_paths[@]}"; do
  if [[ "$path" =~ (^|/)\.env($|\.) ]] && [[ ! "$path" =~ (^|/)\.env\.example$ ]]; then
    blocked_env+="${path}"$'\n'
  fi
done
if [[ -n "$blocked_env" ]]; then
  echo "ERROR: refusing to commit environment/secret files:" >&2
  printf '%s' "$blocked_env" >&2
  exit 1
fi

scan_files=()
for path in "${changed_paths[@]}"; do
  [[ -z "$path" ]] && continue
  [[ -f "$path" ]] || continue
  scan_files+=("$path")
done

if [[ ${#scan_files[@]} -gt 0 ]]; then
  secret_hits="$(
    grep -nEI '(api[_-]?key|secret|token|password|credential|session)[[:alnum:]_ -]*[:=][[:space:]]*["]?[A-Za-z0-9_./+=-]{12,}' "${scan_files[@]}" 2>/dev/null || true
  )"
  if [[ -n "$secret_hits" ]]; then
    echo "ERROR: refusing to commit likely secret material:" >&2
    printf '%s\n' "$secret_hits" >&2
    exit 1
  fi
fi

rehydrate_script="${repo_root}/scripts/gace_mutation_rehydrate_check.py"
if [[ -f "$rehydrate_script" ]]; then
  paths_file="$(mktemp)"
  if ((${#changed_paths[@]})); then
    printf '%s\n' "${changed_paths[@]}" >"$paths_file"
  else
    : >"$paths_file"
  fi
  if ! python3 "$rehydrate_script" --mode mutate --repo-root "$repo_root" --paths-file "$paths_file"; then
    rm -f "$paths_file"
    echo "ERROR: mutation rehydrate preflight denied (WRONG_MISSION_OR_CU / SCOPE_DRIFT / repo identity)." >&2
    exit 1
  fi
  rm -f "$paths_file"
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
  message="AI auto-commit: ${summary}"
fi

git commit -m "$message"

if [[ "$push_mode" == "1" ]]; then
  git push origin "$branch"
fi
