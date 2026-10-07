#!/usr/bin/env bash
set -u
set -o pipefail

SERVER_CORE_REPO="${GACE_SERVER_CORE_REPO:-/home/admin1/server-core}"
CONTRACT="${GACE_SERVER_COMMAND_CONTRACT:-$SERVER_CORE_REPO/operations/server-command.json}"
QUEUE="${GACE_SERVER_COMMAND_QUEUE_ROOT:-$SERVER_CORE_REPO/.gace-control/server-command}"
JQ_BIN="${GACE_SERVER_COMMAND_JQ_BIN:-jq}"
GIT_BIN="${GACE_SERVER_COMMAND_GIT_BIN:-git}"
TIMEOUT_BIN="${GACE_SERVER_COMMAND_TIMEOUT_BIN:-timeout}"
DF_BIN="${GACE_SERVER_COMMAND_DF_BIN:-df}"
GH_BIN="${GACE_SERVER_COMMAND_GH_BIN:-gh}"

err_code=""
request_id=""
command_id=""
target_id=""
target_path=""
target_repo=""
result_json="{}"

fail(){ err_code="${1:-ERROR}"; return 1; }
ensure_dir(){ mkdir -p -- "$1" && chmod 700 -- "$1"; }
atomic_json(){
  local target="$1" json="$2" tmp
  ensure_dir "$(dirname -- "$target")" || return 1
  tmp="${target}.tmp-$$-$(date +%s%N)"
  (umask 077; printf '%s\n' "$json" >"$tmp") || return 1
  mv -f -- "$tmp" "$target"
}
run_timed(){
  local seconds="$1"
  shift
  "$TIMEOUT_BIN" --signal=TERM --kill-after=2s "$seconds" "$@"
}
contract_value(){
  "$JQ_BIN" -er "$1" "$CONTRACT"
}
resolve_target(){
  local env_name default_path
  env_name="$("$JQ_BIN" -er --arg t "$target_id" '.targets[$t].host_path_env // empty' "$CONTRACT")" || {
    fail SERVER_COMMAND_TARGET_NOT_ALLOWED
    return 1
  }
  default_path="$("$JQ_BIN" -er --arg t "$target_id" '.targets[$t].default_host_path // empty' "$CONTRACT")" || {
    fail SERVER_COMMAND_TARGET_NOT_ALLOWED
    return 1
  }
  target_repo="$("$JQ_BIN" -er --arg t "$target_id" '.targets[$t].github_repository // empty' "$CONTRACT")" || {
    fail SERVER_COMMAND_TARGET_REPOSITORY_INVALID
    return 1
  }
  [[ "$env_name" =~ ^[A-Z][A-Z0-9_]*$ ]] || {
    fail SERVER_COMMAND_TARGET_ENV_INVALID
    return 1
  }
  [[ "$target_repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || {
    fail SERVER_COMMAND_TARGET_REPOSITORY_INVALID
    return 1
  }
  target_path="${!env_name:-$default_path}"
  [ -d "$target_path" ] || {
    fail SERVER_COMMAND_TARGET_MISSING
    return 1
  }
  target_path="$(cd "$target_path" && pwd -P)" || {
    fail SERVER_COMMAND_TARGET_INVALID
    return 1
  }
}
validate_request(){
  local file="$1" now_ms expires command_action command_args
  "$JQ_BIN" -e '
    .schema=="gace.server-command-request/v1"
    and (.id|type=="string" and test("^cmd_[0-9a-f]{24}$"))
    and .action=="read"
    and (.command_id|type=="string" and length>0)
    and (.target_id|type=="string" and length>0)
    and (.created_at|type=="number")
    and (.expires_at|type=="number")
    and ((keys|sort)==(["action","command_id","created_at","expires_at","id","schema","target_id"]|sort))
  ' "$file" >/dev/null || {
    fail REQUEST_SCHEMA_OR_BOUNDARY_INVALID
    return 1
  }
  request_id="$("$JQ_BIN" -r '.id' "$file")"
  command_id="$("$JQ_BIN" -r '.command_id' "$file")"
  target_id="$("$JQ_BIN" -r '.target_id' "$file")"
  expires="$("$JQ_BIN" -r '.expires_at|floor' "$file")"
  now_ms="$(date +%s%3N)"
  [ "$now_ms" -le "$expires" ] || {
    fail REQUEST_EXPIRED
    return 1
  }
  command_action="$("$JQ_BIN" -er --arg c "$command_id" '.commands[$c].action // empty' "$CONTRACT")" || {
    fail SERVER_COMMAND_NOT_ALLOWED
    return 1
  }
  command_args="$("$JQ_BIN" -er --arg c "$command_id" '.commands[$c].arguments // empty' "$CONTRACT")" || {
    fail SERVER_COMMAND_NOT_ALLOWED
    return 1
  }
  [ "$command_action" = "read" ] && [ "$command_args" = "none" ] || {
    fail SERVER_COMMAND_CONTRACT_ACTION_INVALID
    return 1
  }
  "$JQ_BIN" -e --arg t "$target_id" '.targets[$t] != null' "$CONTRACT" >/dev/null || {
    fail SERVER_COMMAND_TARGET_NOT_ALLOWED
    return 1
  }
  resolve_target
}
git_target_required(){
  [ -d "$target_path/.git" ] || {
    fail SERVER_COMMAND_TARGET_NOT_GIT_REPO
    return 1
  }
}
changed_paths(){
  (
    cd "$target_path" &&
    {
      "$GIT_BIN" diff --name-only
      "$GIT_BIN" diff --cached --name-only
      "$GIT_BIN" ls-files --others --exclude-standard
    } |
      sed '/^$/d;/^\.gace-control\//d;/^\.debugai-input\//d' |
      LC_ALL=C sort -u
  )
}
run_read_command(){
  local output timeout_s max_output byte_count branch dirty
  timeout_s="$("$JQ_BIN" -er --arg c "$command_id" '.commands[$c].timeout_seconds' "$CONTRACT")" || {
    fail SERVER_COMMAND_TIMEOUT_CONTRACT_INVALID
    return 1
  }
  max_output="$(contract_value '.queue.max_output_bytes')" || {
    fail SERVER_COMMAND_OUTPUT_CONTRACT_INVALID
    return 1
  }
  case "$command_id" in
    workspace.pwd)
      output="$target_path"
      ;;
    workspace.git_head)
      git_target_required || return 1
      output="$(cd "$target_path" && run_timed "${timeout_s}s" "$GIT_BIN" rev-parse HEAD)" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      ;;
    workspace.git_status)
      git_target_required || return 1
      branch="$(cd "$target_path" && run_timed "${timeout_s}s" "$GIT_BIN" branch --show-current)" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      dirty="$(changed_paths | wc -l | tr -d '[:space:]')" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      output="branch=$branch|dirty_count=$dirty"
      ;;
    workspace.git_changed_paths)
      git_target_required || return 1
      output="$(changed_paths | head -n 40)" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      ;;
    workspace.git_recent_commits)
      git_target_required || return 1
      output="$(cd "$target_path" && run_timed "${timeout_s}s" "$GIT_BIN" log -n 8 --format='%h %s')" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      ;;
    system.disk_usage)
      command -v "$DF_BIN" >/dev/null 2>&1 || {
        fail DF_UNAVAILABLE
        return 1
      }
      output="$("$DF_BIN" -Pk "$target_path" | awk 'NR==2 {print "blocks_kb="$2"|used_kb="$3"|available_kb="$4"|used_percent="$5}')" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      ;;
    github.auth_status)
      command -v "$GH_BIN" >/dev/null 2>&1 || {
        fail GH_CLI_UNAVAILABLE
        return 1
      }
      output="$("$GH_BIN" auth status -h github.com 2>&1 | sed -E 's/(Token: ).*/\1[REDACTED]/; s/(oauth_token: ).*/\1[REDACTED]/' | head -n 12)" || {
        fail GH_AUTH_UNAVAILABLE
        return 1
      }
      ;;
    github.repo_view)
      command -v "$GH_BIN" >/dev/null 2>&1 || {
        fail GH_CLI_UNAVAILABLE
        return 1
      }
      output="$(run_timed "${timeout_s}s" "$GH_BIN" repo view "$target_repo" --json nameWithOwner,defaultBranchRef,isPrivate,url 2>/dev/null)" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      ;;
    github.pr_current)
      command -v "$GH_BIN" >/dev/null 2>&1 || {
        fail GH_CLI_UNAVAILABLE
        return 1
      }
      git_target_required || return 1
      branch="$(cd "$target_path" && "$GIT_BIN" branch --show-current)" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      [ -n "$branch" ] || {
        fail GITHUB_CURRENT_BRANCH_MISSING
        return 1
      }
      output="$(run_timed "${timeout_s}s" "$GH_BIN" pr view "$branch" --repo "$target_repo" --json number,state,isDraft,mergeable,headRefName,headRefOid,baseRefName,url 2>/dev/null)" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      ;;
    github.actions_recent)
      command -v "$GH_BIN" >/dev/null 2>&1 || {
        fail GH_CLI_UNAVAILABLE
        return 1
      }
      git_target_required || return 1
      branch="$(cd "$target_path" && "$GIT_BIN" branch --show-current)" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      [ -n "$branch" ] || {
        fail GITHUB_CURRENT_BRANCH_MISSING
        return 1
      }
      output="$(run_timed "${timeout_s}s" "$GH_BIN" run list --repo "$target_repo" --branch "$branch" --limit 8 --json databaseId,name,status,conclusion,headSha,event,url 2>/dev/null)" || {
        fail COMMAND_EXEC_FAILED
        return 1
      }
      ;;
    *)
      fail COMMAND_NOT_ALLOWED
      return 1
      ;;
  esac
  byte_count="$(printf '%s' "$output" | wc -c | tr -d '[:space:]')"
  [ "$byte_count" -le "$max_output" ] || {
    fail COMMAND_OUTPUT_TOO_LARGE
    return 1
  }
  result_json="$("$JQ_BIN" -n     --arg command_id "$command_id"     --arg target_id "$target_id"     --arg stdout "$output"     '{command_id:$command_id,target_id:$target_id,stdout:$stdout,exit_code:0,read_only:true}')"
}
process_file(){
  local source="$1" processing done_dir failed_dir started finished status id_for_status
  started="$(date +%s%3N)"
  processing="$QUEUE/processing/$(basename -- "$source")"
  done_dir="$QUEUE/done"
  failed_dir="$QUEUE/failed"
  ensure_dir "$QUEUE/processing" || return 1
  ensure_dir "$done_dir" || return 1
  ensure_dir "$failed_dir" || return 1
  mv -- "$source" "$processing" || return 1

  request_id=""
  command_id=""
  target_id=""
  target_path=""
  target_repo=""
  err_code=""
  result_json="{}"

  validate_request "$processing" && run_read_command || true
  finished="$(date +%s%3N)"
  id_for_status="$request_id"
  [[ "$id_for_status" =~ ^cmd_[0-9a-f]{24}$ ]] || id_for_status="invalid_${finished}"

  if [ -z "$err_code" ]; then
    status="$("$JQ_BIN" -n       --arg id "$request_id"       --arg command_id "$command_id"       --arg target_id "$target_id"       --argjson started "$started"       --argjson finished "$finished"       --argjson result "$result_json"       '{schema:"gace.server-command-status/v1",id:$id,command_id:$command_id,target_id:$target_id,started_at:$started,state:"PASS",finished_at:$finished,result:$result}')"
    atomic_json "$QUEUE/status/${id_for_status}.json" "$status" || return 1
    mv -- "$processing" "$done_dir/$(basename -- "$processing")"
  else
    status="$("$JQ_BIN" -n       --arg id "$id_for_status"       --arg command_id "$command_id"       --arg target_id "$target_id"       --argjson started "$started"       --argjson finished "$finished"       --arg error "${err_code:0:120}"       '{schema:"gace.server-command-status/v1",id:$id,command_id:$command_id,target_id:$target_id,started_at:$started,state:"FAIL",finished_at:$finished,error:$error}')"
    atomic_json "$QUEUE/status/${id_for_status}.json" "$status" || return 1
    mv -- "$processing" "$failed_dir/$(basename -- "$processing")"
  fi
}
main(){
  local lock_dir request_dir name count=0 max_batch cmd
  for cmd in "$JQ_BIN" "$GIT_BIN" "$TIMEOUT_BIN"; do
    command -v "$cmd" >/dev/null 2>&1 || {
      printf 'gace-server-command-runner:DEPENDENCY_MISSING:%s\n' "$cmd" >&2
      return 1
    }
  done
  [ -f "$CONTRACT" ] || {
    printf 'gace-server-command-runner:CONTRACT_MISSING\n' >&2
    return 1
  }
  "$JQ_BIN" -e '.name=="gace-shared-server-command" and .schema_version=="1.0"' "$CONTRACT" >/dev/null || {
    printf 'gace-server-command-runner:CONTRACT_INVALID\n' >&2
    return 1
  }
  max_batch="$(contract_value '.queue.max_requests_per_run')" || return 1
  request_dir="$QUEUE/requests"
  ensure_dir "$request_dir" || return 1
  ensure_dir "$QUEUE/status" || return 1
  lock_dir="$QUEUE/.runner.lock"
  if ! mkdir -- "$lock_dir" 2>/dev/null; then
    return 0
  fi
  trap 'rmdir -- "$lock_dir" 2>/dev/null || true' EXIT INT TERM

  while IFS= read -r name; do
    [ -n "$name" ] || continue
    process_file "$request_dir/$name" || return 1
    count=$((count+1))
    [ "$count" -ge "$max_batch" ] && break
  done < <(find "$request_dir" -maxdepth 1 -type f -name 'cmd_*.json' -printf '%f\n' | LC_ALL=C sort)

  trap - EXIT INT TERM
  rmdir -- "$lock_dir" 2>/dev/null || true
}
main "$@"
