#!/usr/bin/env bash
# Smartly HTTP evidence capture for CS543 Assignments 1, 4, 5 and 6.
# Run from the project root while `python app.py` is running in another terminal.
# This captures actual curl responses from your local app into curl-transcript.txt.
set -u
BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
OUT="${1:-curl-transcript.txt}"
TOKEN="${SMARTLY_DEMO_TOKEN:-local-demo}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
: > "$OUT"

run() {
  label="$1"; shift
  {
    printf '\n\n================================================================\n'
    printf '%s\n' "$label"
    printf '================================================================\n'
    printf '$ curl -i'
    printf ' %q' "$@"
    printf '\n\n'
    curl --silent --show-error -i "$@"
    printf '\n'
  } >> "$OUT" 2>&1
}

run "A1: health endpoint — expect 200" "$BASE_URL/health"
run "A1: list rooms — expect 200" "$BASE_URL/rooms"
run "A1: known room — expect 200 with ETag" "$BASE_URL/rooms/1"
run "A1/A6: XML content negotiation — expect XML" -H "Accept: application/xml" "$BASE_URL/health"
run "A1/A6: unknown room — expect 404 Problem Details" "$BASE_URL/rooms/999"
run "A5/A6: unsupported Accept — expect 406" -H "Accept: text/csv" "$BASE_URL/health"
run "A5/A6: missing bearer token — expect 401" -H "Content-Type: application/json" -d '{}' -X POST "$BASE_URL/bookings"

BODY='{"roomId":1,"date":"2026-11-01","startTime":"10:00","endTime":"11:00","purpose":"CS543 transcript test"}'
run "A4/A5/A6: create booking — expect 201 + Location" \
  -X POST "$BASE_URL/bookings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Idempotency-Key: smartly-transcript-001" \
  -d "$BODY"

run "A5: replay same create request with same Idempotency-Key" \
  -X POST "$BASE_URL/bookings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Idempotency-Key: smartly-transcript-001" \
  -d "$BODY"

run "A6: invalid booking fields — expect 422 Problem Details" \
  -X POST "$BASE_URL/bookings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"roomId":"bad","date":"","startTime":"12:00","endTime":"10:00","purpose":""}'

# Conditional GET: discover current ETag from the actual response, then request it.
ETAG="$(curl --silent --show-error -i "$BASE_URL/rooms/1" | awk 'BEGIN{IGNORECASE=1} /^ETag:/ {sub(/\r$/,""); sub(/^[^:]*:[[:space:]]*/,""); print; exit}')"
if [ -n "$ETAG" ]; then
  run "A5/A6: conditional GET using actual room ETag — expect 304" \
    -H "If-None-Match: $ETAG" "$BASE_URL/rooms/1"
else
  {
    printf '\n\n================================================================\n'
    printf 'A5/A6: conditional GET skipped — no ETag was returned by GET /rooms/1\n'
  } >> "$OUT"
fi

# Stale If-Match demonstration. The starter API checks If-Match on PATCH /admin/rooms/1.
run "A5/A6: stale If-Match — expect 412 Problem Details" \
  -X PATCH "$BASE_URL/admin/rooms/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H 'If-Match: "room-1-stale"' \
  -d '{"name":"Lab A renamed by stale update"}'

# Capture a CORS preflight / Allow header.
run "A5: OPTIONS preflight — expect 204 and Allow/CORS headers" \
  -X OPTIONS "$BASE_URL/bookings" \
  -H 'Origin: https://client.example.edu' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: authorization,content-type,idempotency-key'

printf 'Captured local curl responses in %s\n' "$OUT"
printf 'Review statuses and headers; if a case differs from expected, fix the API before submitting.\n'
