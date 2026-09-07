#!/bin/bash
# test_search_tier2_axes.sh — Contract tests for /km:search Tier 2 Obsidian CLI 4-axis
# routing (backlinks/links/properties/search:context) + obsidianCli.vault config key.
# Static checks always run. Live smoke checks only run when a real obsidian-cli
# executable is found (SKIP + rc 0 otherwise).
# Spec: AI_Second_Brain/100-project/2026-09-01-graphrag-search-quality/31-p3-km-tier2-cli-axes-order.md §3

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

GREP=/usr/bin/grep
PASS_COUNT=0
FAIL_COUNT=0

pass() {
  echo "PASS ${1}"
  PASS_COUNT=$(( PASS_COUNT + 1 ))
}

fail() {
  echo "FAIL ${1} — ${2}" >&2
  FAIL_COUNT=$(( FAIL_COUNT + 1 ))
}

check_count() {
  # check_count <label> <file> <pattern> <expected>
  local label="$1" file="$2" pattern="$3" expected="$4"
  local actual
  actual=$("$GREP" -c "$pattern" "$file")
  if [ "$actual" -eq "$expected" ]; then
    pass "${label} (${file} '${pattern}' = ${actual})"
  else
    fail "${label}" "${file} '${pattern}' expected ${expected}, got ${actual}"
  fi
}

A="commands/search.md"
B=".agent/skills/km-search/SKILL.md"
C="km-config.example.json"
E=".claude-plugin/plugin.json"

# ── 정적: 양성 계수 (31 §3) ─────────────────────────────
for F in "$A" "$B"; do
  check_count "backlinks-count" "$F" 'backlinks file=' 2
  check_count "links-count" "$F" '" links file=' 1
  check_count "properties-count" "$F" 'properties file=' 1
  check_count "search-context-count" "$F" 'search:context' 1
  check_count "obsidian-vault-count" "$F" 'OBSIDIAN_VAULT' 11
  check_count "no-matches-count" "$F" 'No matches found\.' 1
  check_count "tags-vault-count" "$F" '" tags vault=' 1
  check_count "query-tag-count" "$F" 'query="tag:' 1
  check_count "tag-label-count" "$F" '\[tag:#' 1
done
check_count "config-vault-key" "$C" '"vault"' 1
check_count "plugin-version" "$E" '1.6.0' 1

# ── 정적: 음성 — 미끼 ZZQXTIER2 (같은 명령 안, 0 기대) ──────
for F in "$A" "$B" "$C"; do
  actual=$("$GREP" -c 'ZZQXTIER2' "$F")
  if [ "$actual" -eq 0 ]; then
    pass "decoy-ZZQXTIER2 (${F} = 0)"
  else
    fail "decoy-ZZQXTIER2" "${F} expected 0, got ${actual}"
  fi
done

# ── 사본 정합: A·B Tier 2 절 diff 0 ─────────────────────
extract_tier2() {
  awk '/^### Tier 2 — Obsidian CLI/{flag=1} /^### Tier 3 — Obsidian MCP/{flag=0} flag' "$1"
}
DIFF_TIER2=$(diff <(extract_tier2 "$A") <(extract_tier2 "$B"))
if [ -z "$DIFF_TIER2" ]; then
  pass "copy-parity-tier2 (A/B diff 0)"
else
  fail "copy-parity-tier2" "A/B Tier 2 section differs: ${DIFF_TIER2}"
fi

# ── 사본 정합: Phase 2.5-B backlinks 삽입 줄 동일 ───────────
LINE_A=$("$GREP" -F '"$OBSIDIAN_CLI" backlinks file="<top노트 basename(.md 제거)>"' "$A")
LINE_B=$("$GREP" -F '"$OBSIDIAN_CLI" backlinks file="<top노트 basename(.md 제거)>"' "$B")
if [ "$LINE_A" = "$LINE_B" ] && [ -n "$LINE_A" ]; then
  pass "copy-parity-25b-insert"
else
  fail "copy-parity-25b-insert" "A='${LINE_A}' B='${LINE_B}'"
fi

# ── Tier 1 불변: origin/master 대비 ### Tier 1 ~ ### Tier 2 직전 구간 내용 diff 0 ──
extract_tier1() {
  awk '/^### Tier 1 — GraphRAG/{flag=1} /^### Tier 2 — Obsidian CLI/{flag=0} flag' "$1"
}
if git rev-parse --verify origin/master >/dev/null 2>&1; then
  TIER1_DIFF=$(diff <(git show origin/master:"$A" | extract_tier1 /dev/stdin) <(extract_tier1 "$A"))
  if [ -z "$TIER1_DIFF" ]; then
    pass "tier1-unchanged (origin/master diff = 0)"
  else
    fail "tier1-unchanged" "Tier 1 section differs from origin/master: ${TIER1_DIFF}"
  fi
else
  echo "SKIP tier1-unchanged — origin/master not resolvable in this checkout"
fi

# ── 라이브 스모크 (31 §3) — OBSIDIAN_CLI 있음 + KM_TEST_VAULT 지정 시만 ─
CLI="/Applications/Obsidian.app/Contents/MacOS/obsidian-cli"
VAULT="${KM_TEST_VAULT:-}"
if [ -x "$CLI" ] && [ -n "$VAULT" ]; then
  OUT1=$("$CLI" search query="GraphRAG" vault="$VAULT" format=json limit=3); RC1=$?
  [ "$RC1" -eq 0 ] && [ -n "$OUT1" ] && pass "smoke-1-search" || fail "smoke-1-search" "rc=$RC1 bytes=${#OUT1}"

  OUT2=$("$CLI" backlinks file="MOC-Map" vault="$VAULT" format=json); RC2=$?
  FIRST2="${OUT2:0:1}"
  [ "$RC2" -eq 0 ] && [ -n "$OUT2" ] && [ "$FIRST2" = "[" ] && pass "smoke-2-backlinks" || fail "smoke-2-backlinks" "rc=$RC2 bytes=${#OUT2} first='${FIRST2}'"

  OUT3=$("$CLI" links file="MOC-Map" vault="$VAULT"); RC3=$?
  [ "$RC3" -eq 0 ] && [ -n "$OUT3" ] && pass "smoke-3-links" || fail "smoke-3-links" "rc=$RC3 bytes=${#OUT3}"

  OUT4=$("$CLI" properties file="MOC-Map" vault="$VAULT" format=json); RC4=$?
  FIRST4="${OUT4:0:1}"
  [ "$RC4" -eq 0 ] && [ "$FIRST4" = "{" ] && pass "smoke-4-properties" || fail "smoke-4-properties" "rc=$RC4 first='${FIRST4}'"

  OUT5=$("$CLI" search:context query="GraphRAG" vault="$VAULT" limit=3); RC5=$?
  [ "$RC5" -eq 0 ] && [ -n "$OUT5" ] && pass "smoke-5-search-context" || fail "smoke-5-search-context" "rc=$RC5 bytes=${#OUT5}"

  DECOY6="ZZQX$(date +%s)R${RANDOM}"  # 런타임 무작위 — 고정 리터럴은 spec note 에 실려 vault 에 존재하게 됨(2026-09-07 자기오염)
  OUT6=$("$CLI" search query="$DECOY6" vault="$VAULT" format=json); RC6=$?
  if [ "$RC6" -eq 0 ] && [ "$OUT6" = "No matches found." ]; then
    pass "smoke-6-decoy-no-matches"
  else
    fail "smoke-6-decoy-no-matches" "rc=$RC6 out='${OUT6}'"
  fi

  OUT7=$("$CLI" tags vault="$VAULT" counts format=json); RC7=$?
  FIRST7="${OUT7:0:1}"
  [ "$RC7" -eq 0 ] && [ "$FIRST7" = "[" ] && pass "smoke-7-tags-counts" || fail "smoke-7-tags-counts" "rc=$RC7 first='${FIRST7}'"

  OUT8=$("$CLI" search query="tag:graphrag" vault="$VAULT" format=json limit=50); RC8=$?
  TOTAL8=$(printf '%s' "$OUT8" | python3 -c 'import json,sys
try:
    print(len(json.load(sys.stdin)))
except Exception:
    print(0)' 2>/dev/null)
  [ "$RC8" -eq 0 ] && [ -n "$TOTAL8" ] && [ "$TOTAL8" -ge 1 ] && pass "smoke-8-tag-search-total" || fail "smoke-8-tag-search-total" "rc=$RC8 total=${TOTAL8}"
else
  echo "SKIP live-smoke — OBSIDIAN_CLI not found/executable at ${CLI}, or KM_TEST_VAULT not set (run: KM_TEST_VAULT=<vault name> bash $0)"
fi

echo "----"
echo "PASS_COUNT=${PASS_COUNT} FAIL_COUNT=${FAIL_COUNT}"
if [ "$FAIL_COUNT" -eq 0 ]; then
  exit 0
else
  exit 1
fi
