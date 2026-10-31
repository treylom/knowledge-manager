#!/bin/bash
# test_search_graph_expansion.sh — /km:search DEEP graph expansion contract (1.8.5).
#  ① Phase 2.5-B block lives in both entry files (not only in a lazy-load reference), identical,
#     and its BACKLINKS_N is a real count: linked note → its backlink file count, orphan note → 0.
#  ② Receipt block passes --graph-expansion/--backlinks only when the helper's --help knows them:
#     new helper gets them · old helper does not (and the run still succeeds) · QUICK never passes.
#     Pair: the old helper given --backlinks directly exits 2 (why the check exists).
#  ③ Section order: "Phase 0.4" sits after the Tier 1 success contract, before Tier 1-S.
#  ④ Final-line rule: DEEP and not other → graph field may not be omitted (both files).
# Spec: CHANGELOG.md 1.8.5. Runs blocks under bash, and under zsh when present.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PASS_COUNT=0
FAIL_COUNT=0
pass() { echo "PASS ${1}"; PASS_COUNT=$(( PASS_COUNT + 1 )); }
fail() { echo "FAIL ${1} — ${2}" >&2; FAIL_COUNT=$(( FAIL_COUNT + 1 )); }

A="commands/search.md"
B=".agent/skills/km-search/SKILL.md"
FIX="${SCRIPT_DIR}/fixtures"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SHELLS="bash"
command -v zsh >/dev/null 2>&1 && SHELLS="bash zsh"

section_b() { awk '/^### B\. backlinks 1-hop/{f=1} /^### C\. /{f=0} /^## /{f=0} f' "$1"; }
first_bash_block() { awk '/^```bash$/{if(!done){f=1;next}} /^```$/{if(f){f=0;done=1;next}} f'; }
receipt_section() { awk '/^## 영수증/{f=1;next} /^## /{f=0} /^### 결과 없음/{f=0} f' "$1"; }
trim_trailing_blank() { sed -e :a -e '/^\n*$/{$d;N;ba' -e '}'; }

# ── ① graph block: present, identical, counts ─────────────────────────────
VAULT="${WORK}/vault"
cp -R "${FIX}/km-link-gate-vault" "$VAULT"
mkdir -p "${VAULT}/010-Notes/b"
printf -- '---\ntitle: orphan\n---\n\nno links in or out\n' > "${VAULT}/010-Notes/b/orphan-zz.md"
# hub with 12 backlinks — more than the 10-line list cut, so a count taken after `head` would show
mkdir -p "${VAULT}/010-Notes/c"
printf -- '---\ntitle: hub\n---\n\nhub note\n' > "${VAULT}/010-Notes/c/hub-zz.md"
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do printf 'see [[hub-zz]]\n' > "${VAULT}/010-Notes/c/leaf-${i}.md"; done
# independent count (python, not grep): files whose text contains "[[<stem>"
indep_count() {
  python3 - "$VAULT" "$1" <<'PY'
import pathlib, sys
root, stem = pathlib.Path(sys.argv[1]), sys.argv[2]
print(sum(1 for p in root.rglob("*.md") if f"[[{stem}" in p.read_text(encoding="utf-8")))
PY
}
for F in "$A" "$B"; do
  BLK="${WORK}/$(basename "$(dirname "$F")")-graph.sh"
  section_b "$F" | first_bash_block > "$BLK"
  if grep -q 'BACKLINKS_N=\$(grep -rl' "$BLK"; then pass "graph-block-present ${F}"; else fail "graph-block-present ${F}" "Phase 2.5-B block with BACKLINKS_N not found in the entry file"; continue; fi
  for SH in $SHELLS; do
    for NOTE in "010-Notes/a/note-a1.md" "010-Notes/b/orphan-zz.md" "010-Notes/c/hub-zz.md"; do
      STEM="$(basename "$NOTE" .md)"
      WANT="$(indep_count "$STEM")"
      OUT="$(env -i PATH="$PATH" HOME="$WORK" OBSIDIAN_CLI=true VAULT_PATH="$VAULT" NOTE_PATH="$NOTE" "$SH" "$BLK" 2>/dev/null)"
      GOT="$(printf '%s\n' "$OUT" | sed -n 's/^GRAPH_EXPANSION=done BACKLINKS_N=\([0-9]*\)$/\1/p')"
      if [ -n "$GOT" ] && [ "$GOT" = "$WANT" ]; then pass "graph-count ${F}@${SH} ${STEM} (BACKLINKS_N=${GOT} = independent ${WANT})"; else fail "graph-count ${F}@${SH} ${STEM}" "want ${WANT}, got '${GOT}'"; fi
    done
    OUT="$(env -i PATH="$PATH" HOME="$WORK" OBSIDIAN_CLI=true VAULT_PATH="$VAULT" NOTE_PATH="" "$SH" "$BLK" 2>/dev/null)"
    printf '%s\n' "$OUT" | grep -qx 'GRAPH_EXPANSION=skipped:no-top-note BACKLINKS_N=' \
      && pass "graph-no-note ${F}@${SH} (skipped, no count)" || fail "graph-no-note ${F}@${SH}" "got '$(printf '%s' "$OUT" | tail -1)'"
  done
done
# the positive case must be non-zero, or the pair proves nothing
[ "$(indep_count note-a1)" -ge 1 ] && pass "graph-pair-is-a-pair (note-a1 ≥1 · orphan-zz = $(indep_count orphan-zz))" || fail "graph-pair-is-a-pair" "note-a1 has no backlinks in fixture"
DIFFB="$(diff <(section_b "$A" | trim_trailing_blank) <(section_b "$B" | trim_trailing_blank))"
[ -z "$DIFFB" ] && pass "copy-parity-phase25b (A/B diff 0)" || fail "copy-parity-phase25b" "$DIFFB"
n=$(grep -c 'BACKLINKS_N' commands/search-references/phase-2.5-graph.txt || true)
[ "$n" -ge 1 ] && grep -q '본문' commands/search-references/phase-2.5-graph.txt && ! grep -q 'grep -rl --include' commands/search-references/phase-2.5-graph.txt \
  && pass "reference-points-to-body (no duplicate B command left in reference)" || fail "reference-points-to-body" "phase-2.5-graph.txt still holds the B command or lacks the pointer"

# ── ② receipt block: graph args only for a helper that knows them ─────────
make_receipt_block() {
  # make_receipt_block <entry> <out>: first bash block of the receipt section, placeholders filled
  receipt_section "$1" | first_bash_block \
    | sed -e 's/"<상위 1건 source_note 경로 또는 no-hit>"/"no-hit"/' -e 's/<Tier 1~4 히트 수 정수>/3/' > "$2"
}
run_receipt() {
  # run_receipt <shell> <block> <helper> <km_mode> → stdout; argv lands in $WORK/argv.txt; rc kept in $WORK/rc
  local sh="$1" blk="$2" helper="$3" mode="$4" root="${WORK}/plugroot" home="${WORK}/rhome"
  rm -rf "$root" "$home" "${WORK}/argv.txt"
  mkdir -p "${root}/scripts" "$home"
  cp "$helper" "${root}/scripts/km-search-receipt.py"
  # the $HOME-relative fallback helper path, read from the block itself (the Codex skill uses only this one)
  local fb; fb="$(sed -n 's|.*"\$HOME/\([^"]*/km-search-receipt\.py\)".*|\1|p' "$blk" | head -1)"
  if [ -n "$fb" ]; then mkdir -p "$(dirname "${home}/${fb}")"; cp "$helper" "${home}/${fb}"; fi
  env -i PATH="$PATH" HOME="$home" CLAUDE_PLUGIN_ROOT="$root" FAKE_RCPT_ARGV="${WORK}/argv.txt" \
    QUERY="q" VAULT_MODE=other KM_MODE="$mode" GRAPH_EXPANSION=done BACKLINKS_N=4 MB_STATE=ok GRAPHRAG_STATE=ok \
    "$sh" "$blk" 2>/dev/null
  echo $? > "${WORK}/rc"
}
grep -v 'p.add_argument("--backlinks", type=int)' "${FIX}/fake-receipt-new.py" > "${WORK}/fake-receipt-half.py"
has_pair() { grep -qx -- "$1" "${WORK}/argv.txt" 2>/dev/null && grep -A1 -x -- "$1" "${WORK}/argv.txt" | tail -1 | grep -qx -- "$2"; }
for F in "$A" "$B"; do
  RB="${WORK}/$(basename "$(dirname "$F")")-receipt.sh"
  make_receipt_block "$F" "$RB"
  for SH in $SHELLS; do
    tag="${F}@${SH}"
    run_receipt "$SH" "$RB" "${FIX}/fake-receipt-new.py" DEEP > /dev/null
    if [ "$(cat "${WORK}/rc")" = 0 ] && has_pair --backlinks 4 && has_pair --graph-expansion done; then pass "receipt-new-helper-deep ${tag} (graph args passed)"; else fail "receipt-new-helper-deep ${tag}" "rc=$(cat "${WORK}/rc") argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
    OUT="$(run_receipt "$SH" "$RB" "${FIX}/fake-receipt-old.py" DEEP)"
    if [ "$(cat "${WORK}/rc")" = 0 ] && [ -s "${WORK}/argv.txt" ] && ! grep -q -- '--backlinks' "${WORK}/argv.txt" && printf '%s\n' "$OUT" | grep -qx 'KM_RECEIPT_GRAPH_FIELDS=unsupported'; then pass "receipt-old-helper-deep ${tag} (not passed · receipt still written · unsupported shown)"; else fail "receipt-old-helper-deep ${tag}" "rc=$(cat "${WORK}/rc") out=$(printf '%s' "$OUT" | tr '\n' ' ')"; fi
    # helper that knows only --graph-expansion (not --backlinks) → pass neither
    OUT="$(run_receipt "$SH" "$RB" "${WORK}/fake-receipt-half.py" DEEP)"
    if [ "$(cat "${WORK}/rc")" = 0 ] && [ -s "${WORK}/argv.txt" ] && ! grep -q -- '--backlinks\|--graph-expansion' "${WORK}/argv.txt" && printf '%s\n' "$OUT" | grep -qx 'KM_RECEIPT_GRAPH_FIELDS=unsupported'; then pass "receipt-half-helper-deep ${tag} (both args required)"; else fail "receipt-half-helper-deep ${tag}" "rc=$(cat "${WORK}/rc") argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
    run_receipt "$SH" "$RB" "${FIX}/fake-receipt-new.py" QUICK > /dev/null
    if [ "$(cat "${WORK}/rc")" = 0 ] && ! grep -q -- '--backlinks\|--graph-expansion' "${WORK}/argv.txt"; then pass "receipt-quick ${tag} (no graph args)"; else fail "receipt-quick ${tag}" "argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
  done
done
FAKE_RCPT_ARGV="${WORK}/argv-direct.txt" python3 "${FIX}/fake-receipt-old.py" --backlinks 4 >/dev/null 2>&1; rc=$?
[ "$rc" = 2 ] && pass "receipt-pair old helper + --backlinks directly → rc 2" || fail "receipt-pair" "want rc 2, got ${rc}"

# ── ③ section order ──────────────────────────────────────────────────────
order_ok() {
  # order_ok <file> <tier1 anchor regex>
  local p04 t1 t1s
  p04=$(grep -n '^#* *Phase 0\.4: 구조 문서 축' "$1" | head -1 | cut -d: -f1)
  t1=$(grep -n -e "$2" "$1" | head -1 | cut -d: -f1)
  t1s=$(grep -n '^#### Tier 1-S' "$1" | head -1 | cut -d: -f1)
  [ -n "$p04" ] && [ -n "$t1" ] && [ -n "$t1s" ] && [ "$p04" -gt "$t1" ] && [ "$p04" -lt "$t1s" ]
}
order_ok "$A" '^#### Tier 1 성공 계약' && pass "order ${A} (Phase 0.4 after Tier 1 success contract, before Tier 1-S)" || fail "order ${A}" "Phase 0.4 not between Tier 1 success contract and Tier 1-S"
order_ok "$B" '원문 확보 계약 (Tier 1 전용' && pass "order ${B} (Phase 0.4 after Tier 1 원문 확보 계약, before Tier 1-S)" || fail "order ${B}" "Phase 0.4 not between Tier 1 contract and Tier 1-S"
if git rev-parse --verify -q origin/master >/dev/null 2>&1; then
  git show origin/master:"$A" > "${WORK}/master-search.md" 2>/dev/null
  if order_ok "${WORK}/master-search.md" '^#### Tier 1 성공 계약'; then echo "INFO order-pair origin/master already in new order"; else echo "INFO order-pair origin/master ${A} = old order (check is discriminating)"; fi
fi

# ── ④ final-line rule ────────────────────────────────────────────────────
for F in "$A" "$B" commands/search-references/modes-output.txt; do
  n=$(grep -c 'DEEP 이고 `VAULT_MODE` 가 `other` 가 아니면 `+ 그래프 확장(backlinks N)` 생략 ❌' "$F" || true)
  [ "$n" = 1 ] && pass "final-line-rule ${F}" || fail "final-line-rule ${F}" "want 1, got ${n}"
  n=$(grep -c 'QUICK 얕은 질의, 또는 Tier 1 `VAULT_MODE=other` 로 Phase 2.5 를 생략한 경우' "$F" || true)
  [ "$n" = 0 ] && pass "final-line-old-wording-gone ${F}" || fail "final-line-old-wording-gone ${F}" "old omission wording still present (${n})"
done

echo "----"
echo "PASS_COUNT=${PASS_COUNT} FAIL_COUNT=${FAIL_COUNT}"
[ "$FAIL_COUNT" -eq 0 ]
