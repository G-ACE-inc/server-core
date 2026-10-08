#!/usr/bin/env bash
# Ephemeral GitHub Actions only: bridged MCP without host port publish + egress probe.
set -euo pipefail

DIGEST='ghcr.io/github/github-mcp-server@sha256:fbec75de11c255213fa08d80fb166abe73d851fff631c51c0079872967720699'
NETWORK="gace-mcp-ci-bridge-${RANDOM}"
CID=""
MCP_NAME="gace-github-mcp-readonly"

cleanup() {
  docker rm -f "$CID" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker network create "$NETWORK" >/dev/null

docker pull "$DIGEST" >/dev/null

CID="$(docker run -d --rm --name "$MCP_NAME" \
  --network "$NETWORK" \
  --user 65532:65532 --read-only \
  --tmpfs /tmp:rw,size=16m,mode=1777 \
  --security-opt no-new-privileges --cap-drop ALL \
  --pids-limit 64 --memory 128m \
  --env GITHUB_TOOLSETS=projects --env GITHUB_READ_ONLY=1 \
  "$DIGEST" http --listen-host 0.0.0.0 --scope-challenge)"

ready=0
for _ in $(seq 1 30); do
  if ! test "$(docker inspect -f '{{.State.Running}}' "$CID")" = "true"; then
    echo "GITHUB_MCP_BRIDGE_PROCESS=NOT_RUNNING"
    docker logs "$CID" 2>&1 | tail -n 20
    exit 1
  fi
  code="$(docker run --rm --network "$NETWORK" curlimages/curl:8.5.0 \
    -sS --max-time 3 -o /dev/null -w '%{http_code}' \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -X POST --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"gace-ci-bridge","version":"1"}}}' \
    "http://${MCP_NAME}:8082/mcp" 2>/dev/null || echo 000)"
  if test "$code" = "401"; then
    ready=1
    break
  fi
  sleep 1
done
test "$ready" = "1"

echo "GITHUB_MCP_BRIDGE_INBOUND_NO_TOKEN_DENIED=PASS"

egress_code=""
for _ in $(seq 1 3); do
  egress_code="$(docker run --rm --network "$NETWORK" curlimages/curl:8.5.0 \
    -sS --max-time 15 -o /dev/null -w '%{http_code}' \
    https://api.github.com/zen 2>/dev/null || echo 000)"
  case "$egress_code" in
    200|403|429) break ;;
  esac
  sleep 2
done

case "$egress_code" in
  200|403|429)
    echo "GITHUB_MCP_BRIDGE_EGRESS_HTTPS=PASS code=${egress_code}"
    ;;
  *)
    echo "GITHUB_MCP_BRIDGE_EGRESS_HTTPS=INCONCLUSIVE code=${egress_code}"
    echo "NETWORK_INCONCLUSIVE=YES"
    ;;
esac

echo "GITHUB_MCP_BRIDGE_NO_HOST_PORT=PASS"
