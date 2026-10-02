#!/usr/bin/env bash

_gace_shell_run_usage() {
  printf '%s\n' 'usage: source gace-shell-run.sh --project NAME --environment ENV --purpose PURPOSE --directory DIR [--action LABEL] -- command [args...]'
}

_gace_shell_run_emit() {
  local project="$1" environment="$2" host="$3" pwd_value="$4" purpose="$5" action="$6" exit_code="$7" verify="$8" error="$9"
  printf '%s\n' '========== GACE_RESULT_BEGIN =========='
  printf 'PROJECT=%s\n' "$project"
  printf 'ENVIRONMENT=%s\n' "$environment"
  printf 'HOST=%s\n' "$host"
  printf 'PWD=%s\n' "$pwd_value"
  printf 'PURPOSE=%s\n' "$purpose"
  printf 'ACTION=%s\n' "$action"
  printf 'EXIT_CODE=%s\n' "$exit_code"
  printf 'VERIFY=%s\n' "$verify"
  printf 'ERROR=%s\n' "$error"
  printf '%s\n' '========== GACE_RESULT_END =========='
}

_gace_shell_run_main() {
  local project='' environment='' purpose='' directory='' action='command'
  local host='' before_pwd='' rc=0 verify='FAIL' error=''

  while (($#)); do
    case "$1" in
      --project) project="${2-}"; shift 2 ;;
      --environment) environment="${2-}"; shift 2 ;;
      --purpose) purpose="${2-}"; shift 2 ;;
      --directory) directory="${2-}"; shift 2 ;;
      --action) action="${2-}"; shift 2 ;;
      --) shift; break ;;
      -h|--help) _gace_shell_run_usage; return 0 ;;
      *) printf 'gace-shell-run: unknown option: %s\n' "$1" >&2; _gace_shell_run_usage >&2; return 64 ;;
    esac
  done

  host="$(hostname -f 2>/dev/null || hostname 2>/dev/null || printf 'UNKNOWN')"
  before_pwd="$PWD"

  if [[ -z "$project" || -z "$environment" || -z "$purpose" || -z "$directory" ]]; then
    _gace_shell_run_emit "$project" "$environment" "$host" "$PWD" "$purpose" "$action" 64 'FAIL' 'missing_required_argument'
    return 64
  fi

  if (($# == 0)); then
    _gace_shell_run_emit "$project" "$environment" "$host" "$PWD" "$purpose" "$action" 64 'FAIL' 'missing_command'
    return 64
  fi

  if ! builtin cd -- "$directory"; then
    _gace_shell_run_emit "$project" "$environment" "$host" "$before_pwd" "$purpose" "$action" 66 'FAIL' 'directory_change_failed'
    return 66
  fi

  printf '%s\n' '========== GACE_RESULT_BEGIN =========='
  printf 'PROJECT=%s\n' "$project"
  printf 'ENVIRONMENT=%s\n' "$environment"
  printf 'HOST=%s\n' "$host"
  printf 'PWD=%s\n' "$PWD"
  printf 'PURPOSE=%s\n' "$purpose"
  printf 'ACTION=%s\n' "$action"
  printf '%s\n' 'OUTPUT_BEGIN'

  "$@"
  rc=$?

  printf '%s\n' 'OUTPUT_END'
  if ((rc == 0)); then
    verify='PASS'
    error=''
  else
    verify='FAIL'
    error='command_failed'
  fi
  printf 'EXIT_CODE=%s\n' "$rc"
  printf 'PWD=%s\n' "$PWD"
  printf 'VERIFY=%s\n' "$verify"
  printf 'ERROR=%s\n' "$error"
  printf '%s\n' '========== GACE_RESULT_END =========='
  GACE_LAST_EXIT_CODE="$rc"
  return "$rc"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  printf '%s\n' 'gace-shell-run: source this helper so the parent interactive shell remains in the target directory.' >&2
  printf '%s\n' 'example: source ./scripts/gace-shell-run.sh --project NAME --environment ENV --purpose CHECK --directory /confirmed/path --action status -- git status --short --branch' >&2
  exit 64
fi

_gace_shell_run_main "$@"
GACE_LAST_EXIT_CODE=$?
unset -f _gace_shell_run_main _gace_shell_run_usage _gace_shell_run_emit
return "$GACE_LAST_EXIT_CODE"
