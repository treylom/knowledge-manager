#!/bin/bash
# Keep unverified API bodies inside this process, never in tool output.
set -u
GUARD="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/km_search_guard.py"
PYTHON_BIN="${KM_PYTHON:-python3}"
MODE="${1:-}"
ROOT="${2:-}"
SOURCE="${3:-}"
ENTITY="${4:-}"
ENDPOINT="${5:-}"
if [ "$MODE" = same ]; then
  "$PYTHON_BIN" -I -B "$GUARD" local --root "$ROOT" --expected "$SOURCE"
  exit $?
fi
if [ "$MODE" != other ]; then
  printf '%s\n' '{"status":"unmeasured","reason":"invalid_mode","body_available":false}'
  exit 3
fi
if CHECK_RESULT="$("$PYTHON_BIN" -I -B "$GUARD" check --expected "$SOURCE")"; then
  if NOTE_RAW="$(curl -fsS --connect-timeout 3 --max-time 15 --max-filesize 262144 \
    --get "${ENDPOINT%/}/api/note" --data-urlencode "name=$ENTITY" \
    --data-urlencode 'max_chars=2500')"; then
    printf '%s' "$NOTE_RAW" | "$PYTHON_BIN" -I -B "$GUARD" remote --expected "$SOURCE"
    exit $?
  fi
  printf '%s\n' '{"status":"unmeasured","reason":"note_request_failed","body_available":false}'
  exit 3
fi
printf '%s\n' "$CHECK_RESULT"
exit 3
