#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/ai-auto-commit.sh --authorize-server-core-mutation --file PATH [--file PATH ...] [--push] [-m "message"]

Commits only the explicitly listed server-core paths. Unrelated working-tree
changes are left untouched. The helper refuses main/master, unsafe paths,
credential-like content, concurrent helper commits, pre-staged intended files,
and execution without explicit server-core mutation authorization.
USAGE
}

push_mode="${AI_AUTO_PUSH:-0}"
message=""
authorized=0
intended_files=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --authorize-server-core-mutation) authorized=1; shift ;;
    --file)
      [[ $# -ge 2 ]] || { echo "ERROR: missing path after --file" >&2; exit 2; }
      intended_files+=("$2")
      shift 2
      ;;
    --push) push_mode=1; shift ;;
    --no-push) push_mode=0; shift ;;
    -m|--message)
      [[ $# -ge 2 ]] || { echo "ERROR: missing commit message after $1" >&2; exit 2; }
      message="$2"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ "$authorized" == "1" ]] || { echo "ERROR: server-core mutation is not explicitly authorized." >&2; exit 1; }
[[ ${#intended_files[@]} -gt 0 ]] || { echo "ERROR: at least one --file PATH is required; repository-wide staging is forbidden." >&2; exit 2; }

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
expected_root="$(cd -- "$script_dir/.." && pwd -P)"
repo_root="$(git -C "$expected_root" rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$repo_root" ]] || { echo "ERROR: server-core repository root could not be resolved." >&2; exit 1; }
repo_root="$(cd -- "$repo_root" && pwd -P)"
[[ "$repo_root" == "$expected_root" ]] || { echo "ERROR: repository identity mismatch." >&2; exit 1; }
cd "$repo_root"

branch="$(git branch --show-current)"
[[ -n "$branch" ]] || { echo "ERROR: detached HEAD is not supported." >&2; exit 1; }
case "$branch" in main|master) echo "ERROR: refusing direct auto-commit on protected branch: $branch" >&2; exit 1 ;; esac

command -v flock >/dev/null 2>&1 || { echo "ERROR: flock is required for serialized server-core commit safety." >&2; exit 1; }
git_dir="$(git rev-parse --git-dir)"
lock_file="${git_dir}/gace-ai-auto-commit.lock"
exec 9>"$lock_file"
flock -n 9 || { echo "ERROR: another server-core auto-commit change unit is active; refusing concurrent commit." >&2; exit 1; }

normalize_path() {
  python3 - "$1" <<'PY'
from pathlib import PurePosixPath
import sys
p=sys.argv[1]
q=PurePosixPath(p)
if not p or q.is_absolute() or '..' in q.parts or '.' in q.parts or '\\' in p:
    raise SystemExit(2)
print(q.as_posix())
PY
}

normalized=()
for path in "${intended_files[@]}"; do
  clean="$(normalize_path "$path")" || { echo "ERROR: unsafe --file path: $path" >&2; exit 2; }
  [[ "$clean" != ".git" && "$clean" != .git/* ]] || { echo "ERROR: .git paths are forbidden" >&2; exit 2; }
  normalized+=("$clean")
done
mapfile -t intended_files < <(printf '%s\n' "${normalized[@]}" | sort -u)

for path in "${intended_files[@]}"; do
  if [[ -z "$(git status --porcelain=v1 --untracked-files=all -- "$path")" ]]; then
    echo "ERROR: intended file is not currently changed: $path" >&2
    exit 1
  fi
done

pre_staged="$(git diff --cached --name-only -- "${intended_files[@]}")"
if [[ -n "$pre_staged" ]]; then
  echo "ERROR: intended file already has staged content; refusing to mix an existing staged change unit." >&2
  printf '%s\n' "$pre_staged" >&2
  exit 1
fi

blocked_env="$(printf '%s\n' "${intended_files[@]}" | grep -E '(^|/)\.env($|\.)' | grep -Ev '(^|/)\.env\.example$' || true)"
[[ -z "$blocked_env" ]] || { echo "ERROR: refusing environment/secret file paths." >&2; printf '%s\n' "$blocked_env" >&2; exit 1; }

python3 - "${intended_files[@]}" <<'PY'
import pathlib,re,sys
patterns=[
    re.compile(r'(?i)["\'\s]*(api[_-]?key|secret|token|password|credential|session)["\'\s]*[:=]\s*["\']?([A-Za-z0-9_./+=:-]{12,})'),
    re.compile(r'(?i)authorization["\'\s]*[:=]\s*["\']?bearer\s+([A-Za-z0-9_./+=:-]{12,})'),
]
findings=[]
for raw in sys.argv[1:]:
    p=pathlib.Path(raw)
    if not p.exists():
        continue
    if not p.is_file():
        print(f'ERROR: refusing non-regular intended path: {raw}', file=sys.stderr)
        raise SystemExit(1)
    try:
        text=p.read_text(encoding='utf-8')
    except (UnicodeDecodeError,OSError):
        print(f'ERROR: refusing unreadable or non-UTF-8 intended file: {raw}', file=sys.stderr)
        raise SystemExit(1)
    for lineno,line in enumerate(text.splitlines(),1):
        if any(rx.search(line) for rx in patterns):
            findings.append(f'{raw}:{lineno}')
if findings:
    print('ERROR: refusing likely credential material in:', file=sys.stderr)
    for item in findings:
        print(item, file=sys.stderr)
    raise SystemExit(1)
PY

if [[ -n "$message" ]]; then
  python3 - "$message" <<'PY'
import re,sys
s=sys.argv[1]
if re.search(r'(?i)(bearer\s+[A-Za-z0-9_./+=:-]{12,}|(api[_-]?key|secret|token|password|credential|session)\s*[:=]\s*[A-Za-z0-9_./+=:-]{12,})',s):
    raise SystemExit('ERROR: commit message appears to contain credential material')
PY
fi

git diff --check -- "${intended_files[@]}"
for path in "${intended_files[@]}"; do [[ "$path" == *.sh && -f "$path" ]] && bash -n "$path"; done

staged_by_helper=0
committed=0
cleanup_stage() {
  rc=$?
  trap - EXIT
  if [[ "$staged_by_helper" == "1" && "$committed" == "0" ]]; then
    git reset -q -- "${intended_files[@]}" >/dev/null 2>&1 || true
  fi
  exit "$rc"
}
trap cleanup_stage EXIT

git add -- "${intended_files[@]}"
staged_by_helper=1
mapfile -t staged < <(git diff --cached --name-only | sort)
[[ ${#staged[@]} -gt 0 ]] || { echo "ERROR: no staged changes after intended-file staging." >&2; exit 1; }
if [[ "$(printf '%s\n' "${staged[@]}" | sort)" != "$(printf '%s\n' "${intended_files[@]}" | sort)" ]]; then
  echo "ERROR: staged set differs from intended file set; refusing commit." >&2
  exit 1
fi

git diff --cached --check

if [[ -z "$message" ]]; then
  summary="$(printf '%s\n' "${staged[@]:0:3}" | paste -sd ', ' -)"
  (( ${#staged[@]} > 3 )) && summary="$summary and $((${#staged[@]} - 3)) more"
  message="server-core: ${summary}"
fi

git commit -m "$message"
committed=1
commit_sha="$(git rev-parse HEAD)"
if [[ "$push_mode" == "1" ]]; then
  if ! git push origin "$branch"; then
    echo "RESULT=PARTIAL COMMIT=PASS PUSH=FAIL SHA=$commit_sha" >&2
    exit 1
  fi
  echo "RESULT=PASS COMMIT=PASS PUSH=PASS SHA=$commit_sha"
else
  echo "RESULT=PASS COMMIT=PASS PUSH=NOT_REQUESTED SHA=$commit_sha"
fi
exit 0
