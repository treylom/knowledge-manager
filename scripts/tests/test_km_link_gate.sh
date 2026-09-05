#!/usr/bin/env bash
# test_km_link_gate.sh - scripts/km_link_gate.py 5케이스 (스펙 §8 D8 · 합격 G8)
# 실행: bash scripts/tests/test_km_link_gate.sh
# 안전: 픽스처 원본·실 vault 무수정 — mktemp -d 사본(cp -R)에서만 편집한다.
#
# 기대값 (선기입 · 실행 전에 적는다)
#   (a) 전건 실행                          -> exit 1 · failed 에 090-Raw/x.md (reason no-link)
#   (b) --notes 010-Notes/a/note-a1.md     -> exit 0
#   (c) x.md 끝에 [[Notes-MOC]] 추가 후 전건 -> exit 0
#   (d) 없는 vault 경로                    -> exit 2 (측정 불가 · 통과 취급 ❌)
#   (e) 미끼: note-a1.md 의 [[Notes-MOC]] 제거 후 전건 -> exit 1 로 전환
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
GATE="$HERE/../km_link_gate.py"
FIXTURE="${KM_LINK_GATE_FIXTURE:-$HERE/fixtures/km-link-gate-vault}"
[ -f "$GATE" ] || { echo "게이트 없음: $GATE" >&2; exit 2; }
[ -d "$FIXTURE" ] || { echo "픽스처 없음: $FIXTURE" >&2; exit 2; }

WORK=$(mktemp -d "${TMPDIR:-/tmp}/km-link-gate-test.XXXXXX")
cleanup() { [ -d "$WORK" ] && rm -rf "$WORK"; }
trap cleanup EXIT
cp -R "$FIXTURE" "$WORK/vault"
V="$WORK/vault"
NOTE_A="$V/010-Notes/a/note-a1.md"
NOTE_X="$V/090-Raw/x.md"

PASS=0
FAILS=""
report() { # name expected actual detail
  if [ "$2" = "$3" ] && [ -z "$4" ]; then
    PASS=$((PASS + 1))
    echo "[PASS] $1 · expected_exit=$2 actual_exit=$3"
  else
    FAILS="${FAILS}  - $1 (expected_exit=$2 actual_exit=$3${4:+ · $4})
"
    echo "[FAIL] $1 · expected_exit=$2 actual_exit=$3${4:+ · $4}"
  fi
}

echo "=== (a) 전건 실행 — 기대 exit 1 · failed 에 090-Raw/x.md(no-link)"
OUT=$(python3 "$GATE" "$V" --json 2>&1); RC=$?
echo "$OUT"
DETAIL=""
echo "$OUT" | command grep -qF '"note": "090-Raw/x.md"' || DETAIL="failed 에 x.md 없음"
echo "$OUT" | command grep -qF '"reason": "no-link"' || DETAIL="${DETAIL:+$DETAIL; }reason=no-link 없음"
report "a-전건" 1 "$RC" "$DETAIL"

echo "=== (b) --notes 010-Notes/a/note-a1.md — 기대 exit 0"
OUT=$(python3 "$GATE" "$V" --notes 010-Notes/a/note-a1.md 2>&1); RC=$?
echo "$OUT"
report "b-notes-단건" 0 "$RC" ""

echo "=== (c) x.md 에 [[Notes-MOC]] 추가 후 전건 — 기대 exit 0"
printf -- '\n[[Notes-MOC]]\n' >> "$NOTE_X"
OUT=$(python3 "$GATE" "$V" 2>&1); RC=$?
echo "$OUT"
report "c-x.md-보강후-전건" 0 "$RC" ""

echo "=== (d) 없는 vault 경로 — 기대 exit 2"
OUT=$(python3 "$GATE" "$V-does-not-exist" 2>&1); RC=$?
echo "$OUT"
DETAIL=""
echo "$OUT" | command grep -qF '측정 불가' || DETAIL="stderr 측정 불가 1줄 없음"
report "d-vault-부재" 2 "$RC" "$DETAIL"

echo "=== (e) 미끼: note-a1.md 의 [[Notes-MOC]] 제거 후 전건 — 기대 exit 1 로 전환"
sed 's/\[\[Notes-MOC\]\] //' "$NOTE_A" > "$WORK/edit.tmp" && cat "$WORK/edit.tmp" > "$NOTE_A"
command grep -qF '[[Notes-MOC]]' "$NOTE_A" && { echo "미끼 편집 실패: 링크가 남아있다" >&2; }
OUT=$(python3 "$GATE" "$V" --json 2>&1); RC=$?
echo "$OUT"
DETAIL=""
echo "$OUT" | command grep -qF '"note": "010-Notes/a/note-a1.md"' || DETAIL="failed 에 note-a1.md 없음"
report "e-미끼-링크제거" 1 "$RC" "$DETAIL"

echo "---"
if [ -n "$FAILS" ]; then
  printf 'FAILED:\n%s' "$FAILS"
fi
echo "PASS $PASS/5"
[ -z "$FAILS" ]
