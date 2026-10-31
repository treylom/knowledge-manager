#!/bin/bash
# test_search_tier0_mb.sh — /km:search Tier 0 (memory-bank) block contract.
# Extracts the Tier 0 bash block from commands/search.md and .agent/skills/km-search/SKILL.md
# and runs it against a fake memory-bank CLI (fixtures/fake-memory-bank.js) under a temp HOME.
# Pair in the same run: the pre-1.8.5 block (default both mode, --limit 3) on the same fake
# must give 6 — that is the bug this block fixes.
# Spec: CHANGELOG.md 1.8.5. Needs node (missing node = FAIL rc 1); runs each block under bash, and under zsh
# when present. Population authority: recorded cell ids must equal expected_ids() exactly.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PASS_COUNT=0
FAIL_COUNT=0
SEEN_IDS=""
pass() { SEEN_IDS="${SEEN_IDS}${1}"$'\n'; echo "PASS ${1}${2:+ (${2})}"; PASS_COUNT=$(( PASS_COUNT + 1 )); }
fail() { SEEN_IDS="${SEEN_IDS}${1}"$'\n'; echo "FAIL ${1} — ${2}" >&2; FAIL_COUNT=$(( FAIL_COUNT + 1 )); }

# node is required: a missing runtime is a failed contract run, not a pass (no SKIP rc 0).
if ! command -v node >/dev/null 2>&1; then
  echo "FAIL tier0-mb — node not found: the Tier 0 block cannot be exercised" >&2
  echo "PASS_COUNT=0 FAIL_COUNT=1"
  exit 1
fi

A="commands/search.md"
B=".agent/skills/km-search/SKILL.md"
FAKE="${SCRIPT_DIR}/fixtures/fake-memory-bank.js"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

extract_tier0_section() { awk '/^## Tier 0/{f=1;next} /^## /{f=0} f' "$1"; }
extract_tier0_block() {
  extract_tier0_section "$1" | awk '/^```bash$/{if(!done){f=1;next}} /^```$/{if(f){f=0;done=1;next}} f'
}

# Pre-1.8.5 block, kept verbatim as the regression reference (do not "fix" it).
OLD_BLOCK='MB_CLI="$(ls -d "$HOME/.claude/plugins/cache/memory-bank-dev/memory-bank"/*/cli/memory-bank.js 2>/dev/null | sort -V | tail -1)"
MB_OUT=""; MB_STATE=absent; MB_HITS=0
if [ -n "$MB_CLI" ]; then
  MB_OUT="$(node "$MB_CLI" search "${QUERY}" --limit 3 2>/dev/null | grep -vE '"'"'^(Loading|Embedding)'"'"')" && MB_STATE=ok || MB_STATE=error
  MB_HITS=$(printf '"'"'%s\n'"'"' "$MB_OUT" | grep -cE '"'"'^[0-9]+\. \['"'"' || true)
fi
echo "MB_STATE=${MB_STATE} mb_hits=${MB_HITS}"'

# Fake HOME with the CLI at the path the block looks up; an empty HOME = CLI absent.
HOME_WITH="${WORK}/home-with"
HOME_NONE="${WORK}/home-none"
mkdir -p "${HOME_WITH}/.claude/plugins/cache/memory-bank-dev/memory-bank/1.6.0/cli" "${HOME_NONE}"
cp "$FAKE" "${HOME_WITH}/.claude/plugins/cache/memory-bank-dev/memory-bank/1.6.0/cli/memory-bank.js"

# run_block <shell> <block-file> <home> [VAR=val ...] → prints the block's stdout
run_block() {
  local sh="$1" file="$2" home="$3"; shift 3
  env -i PATH="$PATH" HOME="$home" QUERY="deck-flow 순서 검수" LANG="${LANG:-C.UTF-8}" "$@" "$sh" "$file" 2>/dev/null
}
state_of() { printf '%s\n' "$1" | sed -n 's/^MB_STATE=\([a-z]*\) mb_hits=\([0-9]*\)$/\1 \2/p' | tail -1; }
count_of() { printf '%s\n' "$1" | grep -c -e "$2" || true; }

expect() {
  # expect <label> <output> <want "state hits"> [<want vec> <want txt>]
  local label="$1" out="$2" want="$3" got
  got="$(state_of "$out")"
  if [ "$got" = "$want" ]; then pass "$label" "MB_STATE/mb_hits = ${got}"; else fail "$label" "want '${want}', got '${got}'"; fi
  if [ $# -ge 5 ]; then
    local v t
    v="$(count_of "$out" '^\[mb:의미\] ')"; t="$(count_of "$out" '^\[mb:글자\] ')"
    if [ "$v" = "$4" ] && [ "$t" = "$5" ]; then pass "${label} labels" "의미 ${v} · 글자 ${t}"; else fail "${label} labels" "want 의미 $4 · 글자 $5, got 의미 ${v} · 글자 ${t}"; fi
  fi
}

SHELLS="bash"
command -v zsh >/dev/null 2>&1 && SHELLS="bash zsh"
echo "shells=${SHELLS}"
# KM_TEST_REQUIRE_SHELLS="bash zsh" (set in CI) = a missing shell fails the run instead of shrinking the population
for _req in ${KM_TEST_REQUIRE_SHELLS:-}; do
  case " ${SHELLS} " in *" ${_req} "*) ;; *) echo "FAIL required shell missing: ${_req} (KM_TEST_REQUIRE_SHELLS)" >&2; echo "PASS_COUNT=0 FAIL_COUNT=1"; exit 1 ;; esac
done

# Population authority: every cell records its fixed id; the run fails unless the recorded ids equal
# this list exactly (same set, same count) — deleting or skipping a cell turns the run RED.
expected_ids() {
  local F SH tag c
  for F in "$A" "$B"; do
    echo "extract ${F}"
    for SH in $SHELLS; do
      tag="${F}@${SH}"
      echo "s1-calls ${tag}"; echo "s1-score-only-on-vector ${tag}"; echo "s1-no-chatter ${tag}"
      for c in s1-no-overlap s2-overlap s3-absent s4-error s4b-partial-error s4c-vector-error s6-cli-ignores-limit s5-empty; do
        echo "${c} ${tag}"; echo "${c} ${tag} labels"
      done
    done
  done
  for SH in $SHELLS; do echo "old-block-both-limit3 @${SH}"; done
  echo "copy-parity-tier0-mb"
}

for F in "$A" "$B"; do
  BLK="${WORK}/$(basename "$(dirname "$F")")-tier0.sh"
  extract_tier0_block "$F" > "$BLK"
  if grep -q -- '--vector --limit 2' "$BLK" && grep -q -- '--text --limit 1' "$BLK"; then
    pass "extract ${F}" "two calls present"
  else
    fail "extract ${F}" "Tier 0 bash block missing --vector --limit 2 / --text --limit 1"
  fi
  for SH in $SHELLS; do
    tag="${F}@${SH}"
    # ① 의미 2 · 글자 1 · 겹침 0 → 3
    LOG="${WORK}/calls.log"; : > "$LOG"
    OUT="$(run_block "$SH" "$BLK" "$HOME_WITH" FAKE_MB_LOG="$LOG")"
    expect "s1-no-overlap ${tag}" "$OUT" "ok 3" 2 1
    CALLS="$(tr '\n' ',' < "$LOG")"
    [ "$CALLS" = "vector 2,text 1," ] && pass "s1-calls ${tag}" "${CALLS}" || fail "s1-calls ${tag}" "want 'vector 2,text 1,', got '${CALLS}'"
    n="$(count_of "$OUT" '% match')"; [ "$n" = "2" ] && pass "s1-score-only-on-vector ${tag}" "${n}" || fail "s1-score-only-on-vector ${tag}" "want 2 '% match', got ${n}"
    n="$(count_of "$OUT" '^Loading\|^Found ')"; [ "$n" = "0" ] && pass "s1-no-chatter ${tag}" || fail "s1-no-chatter ${tag}" "Loading/Found lines leaked: ${n}"
    # ② 겹침 1 → 2 (text block dropped, vector block with the score kept)
    OUT="$(run_block "$SH" "$BLK" "$HOME_WITH" FAKE_MB_OVERLAP=1)"
    expect "s2-overlap ${tag}" "$OUT" "ok 2" 2 0
    # ③ CLI 없음 → absent · 0
    OUT="$(run_block "$SH" "$BLK" "$HOME_NONE")"
    expect "s3-absent ${tag}" "$OUT" "absent 0" 0 0
    # ④ CLI 오류 → error
    OUT="$(run_block "$SH" "$BLK" "$HOME_WITH" FAKE_MB_FAIL=1)"
    expect "s4-error ${tag}" "$OUT" "error 0" 0 0
    # ④' 한쪽만 오류 → error, 살아 있는 쪽 블록은 그대로 보임
    OUT="$(run_block "$SH" "$BLK" "$HOME_WITH" FAKE_MB_FAIL_MODE=text)"
    expect "s4b-partial-error ${tag}" "$OUT" "error 2" 2 0
    # ④'' 의미 쪽만 오류 → error, 글자 블록은 보임
    OUT="$(run_block "$SH" "$BLK" "$HOME_WITH" FAKE_MB_FAIL_MODE=vector)"
    expect "s4c-vector-error ${tag}" "$OUT" "error 1" 0 1
    # ⑥ --limit 을 무시하는 CLI(모드마다 5) → 그래도 합계 3 (상한 n<3 이 실제로 일함)
    OUT="$(run_block "$SH" "$BLK" "$HOME_WITH" FAKE_MB_IGNORE_LIMIT=5)"
    expect "s6-cli-ignores-limit ${tag}" "$OUT" "ok 3" 3 0
    # ⑤ 결과 없음 → ok · 0
    OUT="$(run_block "$SH" "$BLK" "$HOME_WITH" FAKE_MB_EMPTY=1)"
    expect "s5-empty ${tag}" "$OUT" "ok 0" 0 0
  done
done

# Negative pair: the pre-1.8.5 block on the same fake gives 6 for --limit 3.
OLD="${WORK}/old-tier0.sh"
printf '%s\n' "$OLD_BLOCK" > "$OLD"
for SH in $SHELLS; do
  OUT="$(run_block "$SH" "$OLD" "$HOME_WITH")"
  expect "old-block-both-limit3 @${SH}" "$OUT" "ok 6"
done

# Parity: the memory-bank part of Tier 0 is identical in both files — the bash block up to its
# MB_STATE line, plus every prose line about [mb]/MB_/메모리뱅크. The rules-corpus axis (km_rules_route,
# RULES: lines) lives in the same section of commands/search.md only (Claude Code entry), so it is
# left out of this comparison on purpose.
mb_part() {
  extract_tier0_block "$1" | awk '{print} /^echo "MB_STATE=/{exit}'
  extract_tier0_section "$1" | grep -e '^- .*\[mb' -e '^- .*MB_' -e '메모리뱅크' -e '^1\.8\.5: memory-bank'
}
DIFF0="$(diff <(mb_part "$A") <(mb_part "$B"))"
n_mb="$(mb_part "$A" | grep -c -e 'MB_STATE=' -e '\[mb:의미\]' || true)"
[ -z "$DIFF0" ] && [ "$n_mb" -ge 3 ] && pass "copy-parity-tier0-mb" "A/B memory-bank part diff 0 · anchors ${n_mb}" || fail "copy-parity-tier0-mb" "${DIFF0:-anchors ${n_mb} < 3}"

expected_ids | sort > "${WORK}/ids.want"
printf '%s' "$SEEN_IDS" | sort > "${WORK}/ids.got"
NWANT=$(grep -c . "${WORK}/ids.want"); NGOT=$(grep -c . "${WORK}/ids.got")
if diff "${WORK}/ids.want" "${WORK}/ids.got" > "${WORK}/ids.diff"; then
  echo "POPULATION exact: ${NGOT}/${NWANT} cell ids (shells=${SHELLS})"
else
  echo "FAIL population — recorded ${NGOT} ids, expected ${NWANT}:" >&2
  sed 's/^/  /' "${WORK}/ids.diff" >&2
  FAIL_COUNT=$(( FAIL_COUNT + 1 ))
fi

echo "----"
echo "PASS_COUNT=${PASS_COUNT} FAIL_COUNT=${FAIL_COUNT}"
[ "$FAIL_COUNT" -eq 0 ]
