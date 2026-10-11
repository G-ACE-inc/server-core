#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT='G-ACE Development Platform'
GATEWAY_ROOT='/home/admin1/projects/webhook-gateway'
SERVER_CORE_ROOT='/home/admin1/server-core'
GATEWAY_PROJECT='webhook-gateway'
NETWORK='gace-internal'
RECEIVER_NAME='server-core-project-control'
GH_DIR='/home/admin1/.config/gh'
rc=0
err='NONE'

state_file_key() {
  local file="$1" key="$2"
  if [ ! -f "$file" ]; then printf 'FILE_MISSING'; return 0; fi
  if awk -v k="$key" 'index($0,k "=")==1 {v=substr($0,length(k)+2); if(length(v)>0){found=1}} END{exit found?0:1}' "$file" >/dev/null 2>&1; then
    printf 'CONFIGURED'
  else
    printf 'MISSING'
  fi
}

git_value() {
  local root="$1" mode="$2"
  if [ ! -d "$root/.git" ]; then printf 'NOT_PRESENT'; return 0; fi
  case "$mode" in
    head) git -C "$root" rev-parse HEAD 2>/dev/null || printf 'UNKNOWN' ;;
    branch) git -C "$root" branch --show-current 2>/dev/null | head -n1 ;;
    dirty) if [ -n "$(git -C "$root" status --porcelain --untracked-files=no 2>/dev/null)" ]; then printf 'YES'; else printf 'NO'; fi ;;
  esac
}

has_repo_secret() {
  local name="$1" names
  names="$(GH_CONFIG_DIR="$GH_DIR" gh secret list -R G-ACE-inc/server-core --json name --jq '.[].name' 2>/dev/null)" || return 2
  grep -Fxq -- "$name" <<<"$names"
}

has_repo_variable() {
  local name="$1" names
  names="$(GH_CONFIG_DIR="$GH_DIR" gh variable list -R G-ACE-inc/server-core --json name --jq '.[].name' 2>/dev/null)" || return 2
  grep -Fxq -- "$name" <<<"$names"
}

bool_state() {
  if "$@" >/dev/null 2>&1; then printf 'PASS'; else printf 'FAIL'; fi
}

printf '%s\n' '========== GACE_RESULT_BEGIN =========='
printf 'PROJECT=%s\n' "$PROJECT"
printf 'ACTION=PROJECT_CONTROL_RUNTIME_READBACK\n'
printf 'HOST=%s\n' "$(hostname)"
printf 'PWD=%s\n' "$(pwd)"
printf 'GATEWAY_CHECKOUT=%s\n' "$([ -d "$GATEWAY_ROOT/.git" ] && echo PRESENT || echo MISSING)"
printf 'GATEWAY_HEAD=%s\n' "$(git_value "$GATEWAY_ROOT" head)"
printf 'GATEWAY_BRANCH=%s\n' "$(git_value "$GATEWAY_ROOT" branch)"
printf 'GATEWAY_TRACKED_DIRTY=%s\n' "$(git_value "$GATEWAY_ROOT" dirty)"
printf 'GATEWAY_ENV_PROJECT_CONTROL_URL=%s\n' "$(state_file_key "$GATEWAY_ROOT/.env" DEST_SERVER_CORE_PROJECT_CONTROL_URL)"
printf 'GATEWAY_ENV_PROJECT_CONTROL_SECRET=%s\n' "$(state_file_key "$GATEWAY_ROOT/.env" OUTBOUND_SERVER_CORE_PROJECT_CONTROL_SECRET)"
printf 'GATEWAY_ENV_INTERNAL_NETWORK=%s\n' "$(state_file_key "$GATEWAY_ROOT/.env" GACE_INTERNAL_NETWORK_NAME)"
gateway_count="$(docker ps --filter "label=com.docker.compose.project=$GATEWAY_PROJECT" --format '{{.Names}}' 2>/dev/null | wc -l | tr -d ' ')"
printf 'GATEWAY_RUNNING_CONTAINER_COUNT=%s\n' "$gateway_count"
api_state="$(docker inspect -f '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}NONE{{end}}' webhook-gateway-api-1 2>/dev/null || printf 'NOT_PRESENT')"
worker_state="$(docker inspect -f '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}NONE{{end}}' webhook-gateway-worker-1 2>/dev/null || printf 'NOT_PRESENT')"
printf 'GATEWAY_API_STATE=%s\n' "$api_state"
printf 'GATEWAY_WORKER_STATE=%s\n' "$worker_state"

if docker network inspect "$NETWORK" >/dev/null 2>&1; then
  printf 'INTERNAL_NETWORK=PRESENT\n'
  members="$(docker network inspect -f '{{range $id,$c := .Containers}}{{$c.Name}} {{end}}' "$NETWORK" 2>/dev/null || true)"
  [[ " $members " == *" webhook-gateway-api-1 "* ]] && api_net='YES' || api_net='NO'
  [[ " $members " == *" webhook-gateway-worker-1 "* ]] && worker_net='YES' || worker_net='NO'
  [[ " $members " == *" server-core-project-control "* ]] && receiver_net='YES' || receiver_net='NO'
else
  printf 'INTERNAL_NETWORK=MISSING\n'
  api_net='NO'
  worker_net='NO'
  receiver_net='NO'
fi
printf 'GATEWAY_API_ON_INTERNAL_NETWORK=%s\n' "$api_net"
printf 'GATEWAY_WORKER_ON_INTERNAL_NETWORK=%s\n' "$worker_net"
printf 'RECEIVER_ON_INTERNAL_NETWORK=%s\n' "$receiver_net"

receiver_id="$(docker ps -q --filter "name=$RECEIVER_NAME" 2>/dev/null | head -n1)"
if [ -n "$receiver_id" ]; then
  receiver_state="$(docker inspect -f '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}NONE{{end}}' "$receiver_id" 2>/dev/null || printf 'UNKNOWN')"
  printf 'RECEIVER_RUNTIME=PRESENT\n'
  printf 'RECEIVER_STATE=%s\n' "$receiver_state"
else
  printf 'RECEIVER_RUNTIME=ABSENT\n'
  printf 'RECEIVER_STATE=NOT_PRESENT\n'
fi

printf 'SERVER_CORE_CHECKOUT=%s\n' "$([ -d "$SERVER_CORE_ROOT/.git" ] && echo PRESENT || echo MISSING)"
printf 'SERVER_CORE_HEAD=%s\n' "$(git_value "$SERVER_CORE_ROOT" head)"
printf 'SERVER_CORE_BRANCH=%s\n' "$(git_value "$SERVER_CORE_ROOT" branch)"
printf 'SERVER_CORE_TRACKED_DIRTY=%s\n' "$(git_value "$SERVER_CORE_ROOT" dirty)"
printf 'SERVER_UID=%s\n' "$(id -u)"
printf 'SERVER_GID=%s\n' "$(id -g)"
printf 'GH_CONFIG_DIR=%s\n' "$([ -d "$GH_DIR" ] && echo PRESENT || echo MISSING)"
printf 'GH_AUTH=%s\n' "$(bool_state env GH_CONFIG_DIR="$GH_DIR" gh auth status -h github.com)"
printf 'GH_PROJECT_READ=%s\n' "$(bool_state env GH_CONFIG_DIR="$GH_DIR" gh project view 1 --owner seigo-gace)"

if has_repo_secret GACE_EVENT_GATEWAY_TOKEN; then secret_state='CONFIGURED'; else s=$?; [ "$s" -eq 2 ] && secret_state='NOT_VERIFIED' || secret_state='MISSING'; fi
if has_repo_variable GACE_EVENT_GATEWAY_URL; then var_state='CONFIGURED'; else s=$?; [ "$s" -eq 2 ] && var_state='NOT_VERIFIED' || var_state='MISSING'; fi
printf 'ACTIONS_GATEWAY_TOKEN=%s\n' "$secret_state"
printf 'ACTIONS_GATEWAY_URL=%s\n' "$var_state"
printf 'SECRET_VALUE_EXPOSED=NO\n'
printf 'BOUNDED_HOST_RECEIVER_RUNTIME=%s\n' "$(docker ps -q --filter "name=server-core-bounded-host" 2>/dev/null | head -n1 | grep -q . && echo PRESENT || echo ABSENT)"
if [ -f "$SERVER_CORE_ROOT/scripts/servercore_bounded_host.py" ]; then
  head_sha="$(git_value "$SERVER_CORE_ROOT" head)"
  if bounded_out="$(python3 "$SERVER_CORE_ROOT/scripts/servercore_bounded_host.py" --command-id project.git_head --expected-sha "$head_sha" 2>/dev/null)"; then
    printf 'SERVERCORE_BOUNDED_HOST_LOCAL=PASS\n'
    printf 'SERVERCORE_BOUNDED_HOST_SHA=%s\n' "$head_sha"
  else
    printf 'SERVERCORE_BOUNDED_HOST_LOCAL=FAIL\n'
  fi
else
  printf 'SERVERCORE_BOUNDED_HOST_LOCAL=NOT_INSTALLED\n'
fi
printf 'MUTATION_PERFORMED=NO\n'
printf 'VERIFY=PROJECT_CONTROL_RUNTIME_READBACK_COMPLETE\n'
printf 'EXIT_CODE=%s\n' "$rc"
printf 'ERROR=%s\n' "$err"
printf 'PROJECT_END=%s\n' "$PROJECT"
printf '%s\n' '========== GACE_RESULT_END =========='
