#!/usr/bin/env bash
# URL smoke tests. Start the server first:
#   uvicorn assistant_api.main:create_app --factory --reload
set -uo pipefail

BASE="${BASE:-http://127.0.0.1:8000}"
ADMIN="${API_ADMIN_KEY:-change-me}"
RESPONSE_FILE="$(mktemp)"
FAILURES=0
TOTAL=0

cleanup() {
  rm -f "$RESPONSE_FILE"
}
trap cleanup EXIT

contains_status() {
  local expected="$1"
  local actual="$2"
  local value
  IFS='|' read -r -a values <<< "$expected"
  for value in "${values[@]}"; do
    [[ "$value" == "$actual" ]] && return 0
  done
  return 1
}

check() {
  local name="$1"
  local method="$2"
  local path="$3"
  local expected="$4"
  local body="${5:-}"
  local header="${6:-}"
  local status
  local -a args=(
    --silent
    --show-error
    --output "$RESPONSE_FILE"
    --write-out '%{http_code}'
    --request "$method"
  )

  [[ -n "$body" ]] && args+=(--header 'Content-Type: application/json' --data "$body")
  [[ -n "$header" ]] && args+=(--header "$header")
  ((TOTAL += 1))

  if ! status="$(curl "${args[@]}" "$BASE$path")"; then
    printf 'FAIL %-30s curl could not reach %s%s\n' "$name" "$BASE" "$path" >&2
    ((FAILURES += 1))
    return
  fi

  if contains_status "$expected" "$status"; then
    printf 'PASS %-30s HTTP %s\n' "$name" "$status"
  else
    printf 'FAIL %-30s expected %s, got %s\n' "$name" "$expected" "$status" >&2
    sed 's/^/  response: /' "$RESPONSE_FILE" >&2
    printf '\n' >&2
    ((FAILURES += 1))
  fi
}

check 'health' GET '/health' '200'
check 'chat fee' POST '/v1/chat' '200' '{"message":"tuition for 18 credits and 2 retake","session_id":"demo"}'
check 'chat rule with source' POST '/v1/chat' '200' '{"message":"can I register my thesis with 118 credits"}'
check 'chat empty' POST '/v1/chat' '422' '{"message":""}'
check 'chat wrong type' POST '/v1/chat' '422' '{"message":123}'
check 'feedback add' POST '/v1/feedback' '201' '{"request_id":"abc123","rating":1,"comment":"clear answer"}'
check 'feedback bad rating' POST '/v1/feedback' '422' '{"request_id":"abc123","rating":7}'
check 'feedback without key' GET '/v1/feedback' '401'
check 'feedback with key' GET '/v1/feedback' '200' '' "X-API-Key: $ADMIN"
check 'weather' GET '/v1/weather' '200|503'
check 'unknown route' GET '/v1/nope' '404'

if ((FAILURES > 0)); then
  printf '\n%d/%d URL checks failed.\n' "$FAILURES" "$TOTAL" >&2
  exit 1
fi

printf '\nAll %d URL checks passed.\n' "$TOTAL"
