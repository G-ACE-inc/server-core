#!/usr/bin/env bash
set -u
set -o pipefail

SERVER_CORE_REPO="${GACE_SERVER_CORE_REPO:-/home/admin1/server-core}"
CONTRACT="${GACE_SERVER_GITOPS_CONTRACT:-$SERVER_CORE_REPO/operations/server-gitops.json}"
QUEUE="${GACE_SERVER_GITOPS_QUEUE_ROOT:-$SERVER_CORE_REPO/.gace-control/server-gitops}"
JQ_BIN="${GACE_SERVER_GITOPS_JQ_BIN:-jq}"
GIT_BIN="${GACE_SERVER_GITOPS_GIT_BIN:-git}"
GH_BIN="${GACE_SERVER_GITOPS_GH_BIN:-gh}"
TIMEOUT_BIN="${GACE_SERVER_GITOPS_TIMEOUT_BIN:-timeout}"
DATE_BIN="${GACE_SERVER_GITOPS_DATE_BIN:-date}"

err_code=""
request_id=""
request_action=""
target_id=""
target_path=""
target_repo=""
request_branch=""
expected_head=""
request_sha=""
approval_comment_id=""
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
  "$JQ_BIN" -e --arg t "$target_id" '.targets[$t].enabled==true' "$CONTRACT" >/dev/null || {
    fail SERVER_GITOPS_TARGET_NOT_ALLOWED
    return 1
  }
  env_name="$("$JQ_BIN" -er --arg t "$target_id" '.targets[$t].host_path_env // empty' "$CONTRACT")" || {
    fail SERVER_GITOPS_TARGET_NOT_ALLOWED
    return 1
  }
  default_path="$("$JQ_BIN" -er --arg t "$target_id" '.targets[$t].default_host_path // empty' "$CONTRACT")" || {
    fail SERVER_GITOPS_TARGET_NOT_ALLOWED
    return 1
  }
  target_repo="$("$JQ_BIN" -er --arg t "$target_id" '.targets[$t].github_repository // empty' "$CONTRACT")" || {
    fail SERVER_GITOPS_TARGET_REPOSITORY_INVALID
    return 1
  }
  [[ "$env_name" =~ ^[A-Z][A-Z0-9_]*$ ]] || {
    fail SERVER_GITOPS_TARGET_ENV_INVALID
    return 1
  }
  [[ "$target_repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || {
    fail SERVER_GITOPS_TARGET_REPOSITORY_INVALID
    return 1
  }
  target_path="${!env_name:-$default_path}"
  [ -d "$target_path/.git" ] || {
    fail SERVER_GITOPS_TARGET_REPO_INVALID
    return 1
  }
  target_path="$(cd "$target_path" && pwd -P)" || {
    fail SERVER_GITOPS_TARGET_REPO_INVALID
    return 1
  }
}
validate_request(){
  local file="$1" now_ms expires allowed
  "$JQ_BIN" -e '
    .schema=="gace.server-gitops-request/v1"
    and (.id|type=="string" and test("^gitops_[0-9a-f]{24}$"))
    and .action=="deploy"
    and (.target_id|type=="string" and length>0)
    and (.branch|type=="string" and length>0)
    and (.expected_head|type=="string" and test("^[0-9a-f]{40}$"))
    and (.sha|type=="string" and test("^[0-9a-f]{40}$"))
    and .sha==.expected_head
    and (.approval_comment_id|type=="number" and .>=1 and floor==.)
    and (.created_at|type=="number")
    and (.expires_at|type=="number")
    and ((keys|sort)==(["action","approval_comment_id","branch","created_at","expected_head","expires_at","id","schema","sha","target_id"]|sort))
  ' "$file" >/dev/null || {
    fail REQUEST_SCHEMA_OR_BOUNDARY_INVALID
    return 1
  }
  request_id="$("$JQ_BIN" -r '.id' "$file")"
  request_action="$("$JQ_BIN" -r '.action' "$file")"
  target_id="$("$JQ_BIN" -r '.target_id' "$file")"
  request_branch="$("$JQ_BIN" -r '.branch' "$file")"
  expected_head="$("$JQ_BIN" -r '.expected_head' "$file")"
  request_sha="$("$JQ_BIN" -r '.sha' "$file")"
  approval_comment_id="$("$JQ_BIN" -r '.approval_comment_id|floor' "$file")"
  expires="$("$JQ_BIN" -r '.expires_at|floor' "$file")"
  now_ms="$(date +%s%3N)"
  [ "$now_ms" -le "$expires" ] || {
    fail REQUEST_EXPIRED
    return 1
  }
  "$JQ_BIN" -e --arg a "$request_action" '.actions[$a].approval_class=="MASTER"' "$CONTRACT" >/dev/null || {
    fail SERVER_GITOPS_ACTION_NOT_ALLOWED
    return 1
  }
  resolve_target || return 1
  allowed="$("$JQ_BIN" -er --arg t "$target_id" --arg b "$request_branch" '.targets[$t].allowed_branches | index($b) != null' "$CONTRACT")" || {
    fail SERVER_GITOPS_BRANCH_NOT_ALLOWED
    return 1
  }
  [ "$allowed" = "true" ] || {
    fail SERVER_GITOPS_BRANCH_NOT_ALLOWED
    return 1
  }
}
verify_repo_identity(){
  local remote_url current_branch
  current_branch="$(cd "$target_path" && "$GIT_BIN" branch --show-current)" || {
    fail SERVER_GITOPS_CURRENT_BRANCH_READ_FAILED
    return 1
  }
  [ "$current_branch" = "$request_branch" ] || {
    fail SERVER_GITOPS_CURRENT_BRANCH_MISMATCH
    return 1
  }
  remote_url="$(cd "$target_path" && "$GIT_BIN" remote get-url origin)" || {
    fail SERVER_GITOPS_REMOTE_URL_READ_FAILED
    return 1
  }
  case "$remote_url" in
    "https://github.com/$target_repo"|"https://github.com/$target_repo.git"|"git@github.com:$target_repo"|"git@github.com:$target_repo.git")
      ;;
    *)
      fail SERVER_GITOPS_REMOTE_REPOSITORY_MISMATCH
      return 1
      ;;
  esac
}
verify_clean_worktree(){
  local dirty
  dirty="$(cd "$target_path" && "$GIT_BIN" status --porcelain --untracked-files=all)" || {
    fail SERVER_GITOPS_WORKTREE_READ_FAILED
    return 1
  }
  [ -z "$dirty" ] || {
    fail SERVER_GITOPS_WORKTREE_NOT_CLEAN
    return 1
  }
}
verify_remote_sha(){
  local remote_sha
  remote_sha="$(cd "$target_path" && run_timed 15s "$GIT_BIN" ls-remote origin "refs/heads/$request_branch" | awk 'NR==1{print $1}')" || {
    fail SERVER_GITOPS_REMOTE_HEAD_READ_FAILED
    return 1
  }
  [ "$remote_sha" = "$request_sha" ] || {
    fail SERVER_GITOPS_REMOTE_HEAD_MISMATCH
    return 1
  }
}
verify_approval(){
  local approval_repo approval_issue actor marker max_age expected_body payload created_at updated_at issue_url comment_actor comment_body now_s created_s age_s used_root used_file
  approval_repo="$(contract_value '.approval.repository')" || {
    fail SERVER_GITOPS_APPROVAL_CONTRACT_INVALID
    return 1
  }
  approval_issue="$(contract_value '.approval.issue_number')" || {
    fail SERVER_GITOPS_APPROVAL_CONTRACT_INVALID
    return 1
  }
  actor="$(contract_value '.approval.actor')" || {
    fail SERVER_GITOPS_APPROVAL_CONTRACT_INVALID
    return 1
  }
  marker="$(contract_value '.approval.marker')" || {
    fail SERVER_GITOPS_APPROVAL_CONTRACT_INVALID
    return 1
  }
  max_age="$(contract_value '.approval.max_age_seconds')" || {
    fail SERVER_GITOPS_APPROVAL_CONTRACT_INVALID
    return 1
  }
  used_root="$SERVER_CORE_REPO/$(contract_value '.approval.consumed_relative_root')" || {
    fail SERVER_GITOPS_APPROVAL_CONTRACT_INVALID
    return 1
  }
  used_file="$used_root/comment_${approval_comment_id}.used"
  [ ! -e "$used_file" ] || {
    fail SERVER_GITOPS_APPROVAL_ALREADY_USED
    return 1
  }
  payload="$(run_timed 15s "$GH_BIN" api "repos/$approval_repo/issues/comments/$approval_comment_id")" || {
    fail SERVER_GITOPS_APPROVAL_READ_FAILED
    return 1
  }
  issue_url="$(printf '%s' "$payload" | "$JQ_BIN" -er '.issue_url')" || {
    fail SERVER_GITOPS_APPROVAL_RESPONSE_INVALID
    return 1
  }
  comment_actor="$(printf '%s' "$payload" | "$JQ_BIN" -er '.user.login')" || {
    fail SERVER_GITOPS_APPROVAL_RESPONSE_INVALID
    return 1
  }
  comment_body="$(printf '%s' "$payload" | "$JQ_BIN" -er '.body')" || {
    fail SERVER_GITOPS_APPROVAL_RESPONSE_INVALID
    return 1
  }
  created_at="$(printf '%s' "$payload" | "$JQ_BIN" -er '.created_at')" || {
    fail SERVER_GITOPS_APPROVAL_RESPONSE_INVALID
    return 1
  }
  updated_at="$(printf '%s' "$payload" | "$JQ_BIN" -er '.updated_at')" || {
    fail SERVER_GITOPS_APPROVAL_RESPONSE_INVALID
    return 1
  }
  [ "$issue_url" = "https://api.github.com/repos/$approval_repo/issues/$approval_issue" ] || {
    fail SERVER_GITOPS_APPROVAL_ISSUE_MISMATCH
    return 1
  }
  [ "$comment_actor" = "$actor" ] || {
    fail SERVER_GITOPS_APPROVAL_ACTOR_MISMATCH
    return 1
  }
  [ "$updated_at" = "$created_at" ] || {
    fail SERVER_GITOPS_APPROVAL_EDITED
    return 1
  }
  expected_body="$marker action=$request_action target=$target_id sha=$request_sha"
  [ "$comment_body" = "$expected_body" ] || {
    fail SERVER_GITOPS_APPROVAL_BODY_MISMATCH
    return 1
  }
  created_s="$("$DATE_BIN" -u -d "$created_at" +%s 2>/dev/null)" || {
    fail SERVER_GITOPS_APPROVAL_TIME_INVALID
    return 1
  }
  now_s="$("$DATE_BIN" -u +%s)"
  age_s=$((now_s-created_s))
  [ "$age_s" -ge 0 ] && [ "$age_s" -le "$max_age" ] || {
    fail SERVER_GITOPS_APPROVAL_EXPIRED
    return 1
  }
  ensure_dir "$used_root" || return 1
  if ! (umask 077; set -o noclobber; printf '%s\n' "request=$request_id sha=$request_sha" >"$used_file") 2>/dev/null; then
    fail SERVER_GITOPS_APPROVAL_ALREADY_USED
    return 1
  fi
}
deploy_request(){
  local before_head after_head fetched_head
  verify_repo_identity || return 1
  verify_clean_worktree || return 1
  before_head="$(cd "$target_path" && "$GIT_BIN" rev-parse HEAD)" || {
    fail SERVER_GITOPS_CURRENT_HEAD_READ_FAILED
    return 1
  }
  [[ "$before_head" =~ ^[0-9a-f]{40}$ ]] || {
    fail SERVER_GITOPS_CURRENT_HEAD_INVALID
    return 1
  }
  verify_remote_sha || return 1
  (cd "$target_path" && run_timed 30s "$GIT_BIN" fetch --no-tags origin "refs/heads/$request_branch") >/dev/null 2>&1 || {
    fail SERVER_GITOPS_FETCH_FAILED
    return 1
  }
  fetched_head="$(cd "$target_path" && "$GIT_BIN" rev-parse FETCH_HEAD)" || {
    fail SERVER_GITOPS_FETCH_HEAD_READ_FAILED
    return 1
  }
  [ "$fetched_head" = "$request_sha" ] || {
    fail SERVER_GITOPS_FETCH_HEAD_MISMATCH
    return 1
  }
  (cd "$target_path" && "$GIT_BIN" merge-base --is-ancestor "$before_head" "$request_sha") >/dev/null 2>&1 || {
    fail SERVER_GITOPS_NON_FAST_FORWARD_TARGET
    return 1
  }
  verify_approval || return 1
  if [ "$before_head" != "$request_sha" ]; then
    (cd "$target_path" && run_timed 30s "$GIT_BIN" merge --ff-only "$request_sha") >/dev/null 2>&1 || {
      fail SERVER_GITOPS_FAST_FORWARD_FAILED
      return 1
    }
  fi
  after_head="$(cd "$target_path" && "$GIT_BIN" rev-parse HEAD)" || {
    fail SERVER_GITOPS_FINAL_HEAD_READ_FAILED
    return 1
  }
  [ "$after_head" = "$request_sha" ] || {
    fail SERVER_GITOPS_FINAL_HEAD_MISMATCH
    return 1
  }
  verify_clean_worktree || return 1
  result_json="$("$JQ_BIN" -n     --arg before "$before_head"     --arg after "$after_head"     --arg remote "$request_sha"     --arg target "$target_id"     --argjson approval_comment_id "$approval_comment_id"     '{before_head:$before,after_head:$after,remote_head:$remote,target_id:$target,approval_comment_id:$approval_comment_id,fast_forward_only:true}')"
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
  request_action=""
  target_id=""
  target_path=""
  target_repo=""
  request_branch=""
  expected_head=""
  request_sha=""
  approval_comment_id=""
  err_code=""
  result_json="{}"

  validate_request "$processing" && deploy_request || true
  finished="$(date +%s%3N)"
  id_for_status="$request_id"
  [[ "$id_for_status" =~ ^gitops_[0-9a-f]{24}$ ]] || id_for_status="invalid_${finished}"

  if [ -z "$err_code" ]; then
    status="$("$JQ_BIN" -n       --arg id "$request_id"       --arg action "$request_action"       --arg target_id "$target_id"       --argjson started "$started"       --argjson finished "$finished"       --argjson result "$result_json"       '{schema:"gace.server-gitops-status/v1",id:$id,action:$action,target_id:$target_id,started_at:$started,state:"PASS",finished_at:$finished,result:$result}')"
    atomic_json "$QUEUE/status/${id_for_status}.json" "$status" || return 1
    mv -- "$processing" "$done_dir/$(basename -- "$processing")"
  else
    status="$("$JQ_BIN" -n       --arg id "$id_for_status"       --arg action "$request_action"       --arg target_id "$target_id"       --argjson started "$started"       --argjson finished "$finished"       --arg error "${err_code:0:160}"       '{schema:"gace.server-gitops-status/v1",id:$id,action:$action,target_id:$target_id,started_at:$started,state:"FAIL",finished_at:$finished,error:$error}')"
    atomic_json "$QUEUE/status/${id_for_status}.json" "$status" || return 1
    mv -- "$processing" "$failed_dir/$(basename -- "$processing")"
  fi
}
main(){
  local request_dir lock_dir max_batch name count=0 cmd
  for cmd in "$JQ_BIN" "$GIT_BIN" "$GH_BIN" "$TIMEOUT_BIN" "$DATE_BIN"; do
    command -v "$cmd" >/dev/null 2>&1 || {
      printf 'gace-server-gitops-runner:DEPENDENCY_MISSING:%s\n' "$cmd" >&2
      return 1
    }
  done
  [ -f "$CONTRACT" ] || {
    printf 'gace-server-gitops-runner:CONTRACT_MISSING\n' >&2
    return 1
  }
  "$JQ_BIN" -e '.name=="gace-shared-server-gitops" and .schema_version=="1.0"' "$CONTRACT" >/dev/null || {
    printf 'gace-server-gitops-runner:CONTRACT_INVALID\n' >&2
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
  done < <(find "$request_dir" -maxdepth 1 -type f -name 'gitops_*.json' -printf '%f\n' | LC_ALL=C sort)
  trap - EXIT INT TERM
  rmdir -- "$lock_dir" 2>/dev/null || true
}
main "$@"
