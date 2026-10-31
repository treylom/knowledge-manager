#!/bin/bash
# test_search_graph_expansion.sh — /km:search DEEP graph expansion contract (1.8.5).
#  ① Phase 2.5-B block lives in both entry files (not only in a lazy-load reference), identical.
#     Effects are checked per axis against independent counts: BACKLINKS_N (files linking to the note)
#     and OUTLINKS_N (links the note makes, read from the vault-relative NOTE_FILE), block rc 0.
#     Fail-closed cells: missing vault / missing note / unreadable note / unreadable subtree
#     → GRAPH_EXPANSION=failed:<reason>, BACKLINKS_N empty, block rc 1 (never done/0).
#  ② Receipt block passes --graph-expansion/--backlinks only when the helper's --help knows them:
#     new helper gets them · old helper does not (and the run still succeeds) · QUICK never passes ·
#     a failed expansion passes the state without a count.
#     Pair: the old helper given --backlinks directly exits 2 (why the check exists).
#  ③ Section order: "Phase 0.4" sits after the Tier 1 success contract, before Tier 1-S.
#  ④ Final-line rule: DEEP and not other → graph field may not be omitted (both files).
# Population + body authority = OUTSIDE this file: scripts/tests/cells.manifest (canonical cell ids and the
# sha256 of every `# @cell` region of this file), judged by scripts/tests/seal_cells.py check <this file>.
# This file only emits one `@@CELL<TAB>PASS|FAIL<TAB><id>` line per cell; it does not judge its own population.
# Spec: CHANGELOG.md 1.8.5. Runs blocks under bash, and under zsh when present (shells= line).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PASS_COUNT=0
FAIL_COUNT=0
pass() { printf '@@CELL\tPASS\t%s\n' "$1"; echo "PASS ${1}${2:+ (${2})}"; PASS_COUNT=$(( PASS_COUNT + 1 )); }
fail() { printf '@@CELL\tFAIL\t%s\n' "$1"; echo "FAIL ${1} — ${2}" >&2; FAIL_COUNT=$(( FAIL_COUNT + 1 )); }

A="commands/search.md"
B=".agent/skills/km-search/SKILL.md"
FIX="${SCRIPT_DIR}/fixtures"
WORK="$(mktemp -d)"
trap 'chmod -R u+rwx "$WORK" 2>/dev/null; rm -rf "$WORK"' EXIT
SHELLS="bash"
command -v zsh >/dev/null 2>&1 && SHELLS="bash zsh"
echo "shells=${SHELLS}"
# KM_TEST_REQUIRE_SHELLS="bash zsh" (set in CI) = a missing shell fails the run instead of shrinking the population
for _req in ${KM_TEST_REQUIRE_SHELLS:-}; do
  case " ${SHELLS} " in *" ${_req} "*) ;; *) echo "FAIL required shell missing: ${_req} (KM_TEST_REQUIRE_SHELLS)" >&2; echo "PASS_COUNT=0 FAIL_COUNT=1"; exit 1 ;; esac
done

GOOD_NOTES="010-Notes/a/note-a1.md 010-Notes/b/orphan-zz.md 010-Notes/c/hub-zz.md 010-Notes/c/leaf-1.md -dash-zz.md"
stem_of() { local x="${1##*/}"; printf '%s' "${x%.md}"; }
CLOSED_STATES="done failed:backlink-scan failed:no-note failed:no-vault failed:outlink-scan failed:unreadable-note skipped:no-top-note"

# @cell helpers
section_b() { awk '/^### B\. backlinks 1-hop/{f=1} /^### C\. /{f=0} /^## /{f=0} f' "$1"; }
first_bash_block() { awk '/^```bash$/{if(!done){f=1;next}} /^```$/{if(f){f=0;done=1;next}} f'; }
receipt_section() { awk '/^## 영수증/{f=1;next} /^## /{f=0} /^### 결과 없음/{f=0} f' "$1"; }
trim_trailing_blank() { sed -e :a -e '/^\n*$/{$d;N;ba' -e '}'; }

# @cell graph-fixtures
# ── ① graph block: present, identical, per-axis effects, fail-closed ──────
VAULT="${WORK}/vault"
cp -R "${FIX}/km-link-gate-vault" "$VAULT"
mkdir -p "${VAULT}/010-Notes/b"
printf -- '---\ntitle: orphan\n---\n\nno links in or out\n' > "${VAULT}/010-Notes/b/orphan-zz.md"
# hub with 12 backlinks — more than the 10-line list cut, so a count taken after `head` would show
mkdir -p "${VAULT}/010-Notes/c"
printf -- '---\ntitle: hub\n---\n\nhub note\n' > "${VAULT}/010-Notes/c/hub-zz.md"
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do printf 'see [[hub-zz]]\n' > "${VAULT}/010-Notes/c/leaf-${i}.md"; done
# a note whose name starts with a dash (basename would reject it) · 1 backlink · 1 outlink
# at the vault root, so NOTE_PATH itself starts with "-"
printf 'dash note -> [[note-a1]]\n' > "${VAULT}/-dash-zz.md"
printf 'see [[-dash-zz]]\n' > "${VAULT}/010-Notes/b/points-to-dash.md"
# outside the vault: a real note file next to it, and a symlink to the whole vault
printf 'outside -> [[note-a1]]\n' > "${WORK}/outside-zz.md"
ln -s "$VAULT" "${WORK}/vault-link"
# a sibling folder named "<vault><newline>" — $(pwd -P) would strip the newline and resolve it to the vault
NLSIB="${VAULT}"$'\n'
mkdir -p "$NLSIB"
printf 'sib -> [[note-a1]] [[hub-zz]] [[x]]\n' > "${NLSIB}/sib-zz.md"
# third vault for the final-component cells (P1): the last path component is a symlink.
# Kept apart so the existing independent counts do not change.
VAULT3="${WORK}/vault3"
cp -R "${FIX}/km-link-gate-vault" "$VAULT3"
mkdir -p "${VAULT3}/010-Notes/ln" "${WORK}/outdir"
printf 'outside canary -> [[outside-canary-zz]]\n' > "${WORK}/outside-canary.md"
printf 'outdir canary -> [[outside-canary-zz]]\n' > "${WORK}/outdir/x.md"
ln -s "${WORK}/outside-canary.md" "${VAULT3}/010-Notes/ln/link-out.md"
ln -s "../a/note-a1.md" "${VAULT3}/010-Notes/ln/link-in.md"
printf 'inside canary -> [[inside-canary-zz]]\n' > "${VAULT3}/010-Notes/ln/plain-in.md"
ln -s "loop-b.md" "${VAULT3}/010-Notes/ln/loop-a.md"
ln -s "loop-a.md" "${VAULT3}/010-Notes/ln/loop-b.md"
ln -s "${WORK}/outdir" "${VAULT3}/010-Notes/ln/outdir"
# a 9-link chain ending outside: after the 8-hop limit the path is still a link → must be refused
for i in 1 2 3 4 5 6 7 8; do ln -s "c$(( i + 1 )).md" "${VAULT3}/010-Notes/ln/c${i}.md"; done
ln -s "${WORK}/outside-canary.md" "${VAULT3}/010-Notes/ln/c9.md"
# PATH shims for the binding cells: one swaps the checked note for an outside symlink right before the real
# perl opens it (check→open race, made deterministic), one fails the read outright.
REAL_PERL="$(command -v perl)"
mkdir -p "${WORK}/shim-swap" "${WORK}/shim-fail"
printf '#!/bin/sh\nmv -f "$SWAP_NOTE" "$SWAP_NOTE.moved" && ln -s "$SWAP_TARGET" "$SWAP_NOTE" && exec "$REAL_PERL" "$@"\n' > "${WORK}/shim-swap/perl"
printf '#!/bin/sh\nexit 9\n' > "${WORK}/shim-fail/perl"
chmod +x "${WORK}/shim-swap/perl" "${WORK}/shim-fail/perl"
SWAP_N=0
# second vault for the unreadable cells (the main vault stays readable)
VAULT2="${WORK}/vault2"
cp -R "$VAULT" "$VAULT2"
mkdir -p "${VAULT2}/010-Notes/locked"
printf 'see [[note-a1]]\n' > "${VAULT2}/010-Notes/locked/hidden-link.md"
chmod 000 "${VAULT2}/010-Notes/locked"
cp "${VAULT}/010-Notes/b/orphan-zz.md" "${VAULT2}/010-Notes/b/sealed-zz.md"
chmod 000 "${VAULT2}/010-Notes/b/sealed-zz.md"
# independent counts (python, not grep)
indep_backlinks() {
  python3 - "$VAULT" "$1" <<'PY'
import pathlib, sys
root, stem = pathlib.Path(sys.argv[1]), sys.argv[2]
n = 0
for p in root.rglob("*.md"):
    try:
        n += f"[[{stem}" in p.read_text(encoding="utf-8")
    except PermissionError:
        pass
print(n)
PY
}
indep_outlinks() {
  python3 - "$VAULT/$1" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
print(len({m for m in re.findall(r"\[\[([^\]|#\n]*)", text) if m}))
PY
}
# run_graph <shell> <block> <vault> <note> → stdout in $GOUT, rc in $GRC (rc taken directly, no pipe)
# extra VAR=val words after <note> go into the environment (PATH included)
run_graph() {
  GOUT="$(env -i PATH="$PATH" HOME="$WORK" OBSIDIAN_CLI=true VAULT_PATH="$3" NOTE_PATH="$4" "${@:5}" "$1" "$2" 2>/dev/null)"
  GRC=$?
}
no_canary() { ! printf '%s\n' "$GOUT" | grep -q 'outside-canary-zz'; }
gline() { printf '%s\n' "$GOUT" | grep '^GRAPH_EXPANSION=' | tail -1; }
# expect_failed <id> <want state>: state exact, BACKLINKS_N empty, rc 1
expect_failed() {
  local l; l="$(gline)"
  case "$l" in
    "GRAPH_EXPANSION=$2 BACKLINKS_N= OUTLINKS_N= "*) if [ "$GRC" = 1 ]; then pass "$1" "$2 · rc 1"; else fail "$1" "state ok but rc=${GRC} (want 1)"; fi ;;
    *) fail "$1" "want '$2' with empty count and rc 1, got '${l}' rc=${GRC}" ;;
  esac
}
# @cell graph-block
for F in "$A" "$B"; do
  BLK="${WORK}/$(basename "$(dirname "$F")")-graph.sh"
  section_b "$F" | first_bash_block > "$BLK"
  # presence only — behaviour is judged by the cells below (a text anchor must not stand in for a behaviour check)
  if grep -q 'BL_LIST="$(command grep -rl' "$BLK"; then pass "graph-block-present ${F}"; else fail "graph-block-present ${F}" "Phase 2.5-B block with separate backlink/outlink scans not found"; continue; fi
  GOT_STATES="$(grep -oE "GRAPH_EXPANSION=(\"[^\"]*\"|'[^']*'|[A-Za-z][A-Za-z:-]*)" "$BLK" | sed -e 's/^GRAPH_EXPANSION=//' -e "s/^[\"']//" -e "s/[\"']$//" | grep . | sort -u | tr '\n' ' ' | sed 's/ $//')"
  [ "$GOT_STATES" = "$CLOSED_STATES" ] && pass "graph-closed-values ${F}" "${GOT_STATES}" || fail "graph-closed-values ${F}" "want '${CLOSED_STATES}', got '${GOT_STATES}'"
  for SH in $SHELLS; do
    tag="${F}@${SH}"
    for NOTE in $GOOD_NOTES; do
      STEM="$(stem_of "$NOTE")"
      WB="$(indep_backlinks "$STEM")"; WO="$(indep_outlinks "$NOTE")"
      run_graph "$SH" "$BLK" "$VAULT" "$NOTE"
      L="$(gline)"
      GB="$(printf '%s\n' "$L" | sed -n 's/^GRAPH_EXPANSION=done BACKLINKS_N=\([0-9][0-9]*\) OUTLINKS_N=\([0-9][0-9]*\) BL_RC=[01] OL_RC=[01]$/\1/p')"
      GO="$(printf '%s\n' "$L" | sed -n 's/^GRAPH_EXPANSION=done BACKLINKS_N=\([0-9][0-9]*\) OUTLINKS_N=\([0-9][0-9]*\) BL_RC=[01] OL_RC=[01]$/\2/p')"
      if [ "$GRC" = 0 ] && [ -n "$GB" ] && [ "$GB" = "$WB" ]; then pass "graph-backlinks ${tag} ${STEM}" "BACKLINKS_N=${GB} = independent ${WB} · rc 0"; else fail "graph-backlinks ${tag} ${STEM}" "want done/${WB} rc 0, got '${L}' rc=${GRC}"; fi
      if [ "$GRC" = 0 ] && [ -n "$GO" ] && [ "$GO" = "$WO" ]; then pass "graph-outlinks ${tag} ${STEM}" "OUTLINKS_N=${GO} = independent ${WO} · rc 0"; else fail "graph-outlinks ${tag} ${STEM}" "want done/outlinks ${WO} rc 0, got '${L}' rc=${GRC}"; fi
    done
    run_graph "$SH" "$BLK" "$VAULT" ""
    case "$(gline)" in "GRAPH_EXPANSION=skipped:no-top-note BACKLINKS_N= OUTLINKS_N= "*) [ "$GRC" = 0 ] && pass "graph-no-note ${tag}" "skipped, no count, rc 0" || fail "graph-no-note ${tag}" "rc=${GRC}" ;; *) fail "graph-no-note ${tag}" "got '$(gline)'" ;; esac
    run_graph "$SH" "$BLK" "$VAULT" "010-Notes/zz/no-such-note.md"; expect_failed "graph-missing-note ${tag}" "failed:no-note"
    run_graph "$SH" "$BLK" "${WORK}/no-such-vault" "010-Notes/a/note-a1.md"; expect_failed "graph-missing-vault ${tag}" "failed:no-vault"
    run_graph "$SH" "$BLK" "$VAULT2" "010-Notes/b/sealed-zz.md"; expect_failed "graph-unreadable-note ${tag}" "failed:unreadable-note"
    run_graph "$SH" "$BLK" "$VAULT2" "010-Notes/a/note-a1.md"; expect_failed "graph-unreadable-subtree ${tag}" "failed:backlink-scan"
    # symlinked vault root: grep -r does not descend a symlinked start dir on BSD → must still count (real path)
    run_graph "$SH" "$BLK" "${WORK}/vault-link" "010-Notes/c/hub-zz.md"
    case "$(gline)" in "GRAPH_EXPANSION=done BACKLINKS_N=$(indep_backlinks hub-zz) OUTLINKS_N=0 "*) [ "$GRC" = 0 ] && pass "graph-symlinked-vault ${tag}" "done/$(indep_backlinks hub-zz) via symlink" || fail "graph-symlinked-vault ${tag}" "rc=${GRC}" ;; *) fail "graph-symlinked-vault ${tag}" "got '$(gline)' rc=${GRC}" ;; esac
    # absolute NOTE_PATH inside the vault = accepted (pair of the outside cells)
    run_graph "$SH" "$BLK" "$VAULT" "${VAULT}/010-Notes/a/note-a1.md"
    case "$(gline)" in "GRAPH_EXPANSION=done BACKLINKS_N=$(indep_backlinks note-a1) OUTLINKS_N=$(indep_outlinks 010-Notes/a/note-a1.md) "*) [ "$GRC" = 0 ] && pass "graph-absolute-in-vault ${tag}" "done" || fail "graph-absolute-in-vault ${tag}" "rc=${GRC}" ;; *) fail "graph-absolute-in-vault ${tag}" "got '$(gline)' rc=${GRC}" ;; esac
    run_graph "$SH" "$BLK" "$VAULT" "${WORK}/outside-zz.md"; expect_failed "graph-absolute-outside-vault ${tag}" "failed:no-note"
    run_graph "$SH" "$BLK" "$VAULT" "../outside-zz.md"; expect_failed "graph-dotdot-outside-vault ${tag}" "failed:no-note"
    # relative path that exists under the current folder (repo root) but not in the vault — no cwd fallback
    run_graph "$SH" "$BLK" "$VAULT" "scripts/tests/fixtures/km-link-gate-vault/010-Notes/a/note-a1.md"; expect_failed "graph-cwd-decoy ${tag}" "failed:no-note"
    # newline in the note path: grep -F would split it into one pattern per line (near-every-file count)
    run_graph "$SH" "$BLK" "$VAULT" "010-Notes/c/x"$'\n'"y.md"; expect_failed "graph-newline-note ${tag}" "failed:no-note"
    run_graph "$SH" "$BLK" "$VAULT" "${NLSIB}/sib-zz.md"; expect_failed "graph-newline-vault-sibling ${tag}" "failed:no-note"
# @cell graph-final-component
    # P1 pair — regular file in the vault (inside canary is read) vs final symlink to an outside file
    run_graph "$SH" "$BLK" "$VAULT3" "010-Notes/ln/plain-in.md"
    if [ "$GRC" = 0 ] && [ "$(gline)" = "GRAPH_EXPANSION=done BACKLINKS_N=0 OUTLINKS_N=1 BL_RC=1 OL_RC=0" ] && printf '%s\n' "$GOUT" | grep -qx 'inside-canary-zz'; then pass "graph-final-regular-inside ${tag}" "inside canary read · rc 0"; else fail "graph-final-regular-inside ${tag}" "got '$(gline)' rc=${GRC}"; fi
    run_graph "$SH" "$BLK" "$VAULT3" "010-Notes/ln/link-out.md"; no_canary && expect_failed "graph-final-symlink-outside ${tag}" "failed:no-note" || fail "graph-final-symlink-outside ${tag}" "outside canary consumed: $(gline)"
    run_graph "$SH" "$BLK" "$VAULT3" "${VAULT3}/010-Notes/ln/link-out.md"; no_canary && expect_failed "graph-final-symlink-outside-abs ${tag}" "failed:no-note" || fail "graph-final-symlink-outside-abs ${tag}" "outside canary consumed: $(gline)"
    run_graph "$SH" "$BLK" "$VAULT3" "010-Notes/ln/outdir/x.md"; no_canary && expect_failed "graph-dir-symlink-outside ${tag}" "failed:no-note" || fail "graph-dir-symlink-outside ${tag}" "outside canary consumed: $(gline)"
    run_graph "$SH" "$BLK" "$VAULT3" "010-Notes/ln/loop-a.md"; expect_failed "graph-final-symlink-loop ${tag}" "failed:no-note"
    run_graph "$SH" "$BLK" "$VAULT3" "010-Notes/ln/c1.md"; no_canary && expect_failed "graph-symlink-chain-over-limit ${tag}" "failed:no-note" || fail "graph-symlink-chain-over-limit ${tag}" "outside canary consumed: $(gline)"
    # final symlink that stays in the vault = followed to its real target (positive, not a blanket symlink ban)
    WO="$(python3 -c 'import re,sys; print(len({m for m in re.findall(r"\[\[([^\]|#\n]*)", open(sys.argv[1], encoding="utf-8").read()) if m}))' "${VAULT3}/010-Notes/a/note-a1.md")"
    run_graph "$SH" "$BLK" "$VAULT3" "010-Notes/ln/link-in.md"
    if [ "$GRC" = 0 ] && [ "$WO" -ge 1 ] && [ "$(gline)" = "GRAPH_EXPANSION=done BACKLINKS_N=0 OUTLINKS_N=${WO} BL_RC=1 OL_RC=0" ]; then pass "graph-final-symlink-inside ${tag}" "followed in vault · outlinks ${WO}"; else fail "graph-final-symlink-inside ${tag}" "want outlinks ${WO}, got '$(gline)' rc=${GRC}"; fi
    # bytes are bound to the checked file: swapped for an outside symlink after the checks → refused, canary unread
    SWAP_N=$(( SWAP_N + 1 )); SV="${WORK}/swap-${SWAP_N}"; mkdir -p "${SV}/n"; printf 'swap -> [[inside-swap-zz]]\n' > "${SV}/n/s.md"
    run_graph "$SH" "$BLK" "$SV" "n/s.md" PATH="${WORK}/shim-swap:${PATH}" REAL_PERL="$REAL_PERL" SWAP_NOTE="${SV}/n/s.md" SWAP_TARGET="${WORK}/outside-canary.md"
    if [ -L "${SV}/n/s.md" ] && no_canary; then expect_failed "graph-swap-after-check ${tag}" "failed:no-note"; else fail "graph-swap-after-check ${tag}" "swap did not happen or canary consumed: $(gline)"; fi
    run_graph "$SH" "$BLK" "$VAULT3" "010-Notes/ln/plain-in.md" PATH="${WORK}/shim-fail:${PATH}"; expect_failed "graph-outlink-scan-failed ${tag}" "failed:outlink-scan"
  done
done
# @cell graph-shadow-and-pairs
# a harness that replaces grep with a shell function (bash exported function here) must not change the counts
for F in "$A" "$B"; do
  BLK="${WORK}/$(basename "$(dirname "$F")")-graph.sh"
  GOUT="$(env -i PATH="$PATH" HOME="$WORK" OBSIDIAN_CLI=true VAULT_PATH="$VAULT" NOTE_PATH="010-Notes/c/hub-zz.md" 'BASH_FUNC_grep%%=() { return 1; }' bash "$BLK" 2>/dev/null)"; GRC=$?
  case "$(gline)" in "GRAPH_EXPANSION=done BACKLINKS_N=$(indep_backlinks hub-zz) OUTLINKS_N=0 "*) [ "$GRC" = 0 ] && pass "graph-grep-function-shadow ${F}" "grep function ignored · done/$(indep_backlinks hub-zz)" || fail "graph-grep-function-shadow ${F}" "rc=${GRC}" ;; *) fail "graph-grep-function-shadow ${F}" "got '$(gline)' rc=${GRC}" ;; esac
done
# the positive cases must be non-zero on both axes, or the pairs prove nothing
if [ "$(indep_backlinks note-a1)" -ge 1 ] && [ "$(indep_outlinks 010-Notes/a/note-a1.md)" -ge 1 ] && [ "$(indep_backlinks orphan-zz)" = 0 ] && [ "$(indep_outlinks 010-Notes/b/orphan-zz.md)" = 0 ]; then
  pass "graph-pair-is-a-pair" "note-a1 backlinks $(indep_backlinks note-a1) outlinks $(indep_outlinks 010-Notes/a/note-a1.md) · orphan-zz 0/0"
else
  fail "graph-pair-is-a-pair" "fixture lost its positive or negative side"
fi
DIFFB="$(diff <(section_b "$A" | trim_trailing_blank) <(section_b "$B" | trim_trailing_blank))"
[ -z "$DIFFB" ] && pass "copy-parity-phase25b" "A/B diff 0" || fail "copy-parity-phase25b" "$DIFFB"
n=$(grep -c 'BACKLINKS_N' commands/search-references/phase-2.5-graph.txt || true)
[ "$n" -ge 1 ] && grep -q '본문' commands/search-references/phase-2.5-graph.txt && ! grep -q 'grep -rl --include' commands/search-references/phase-2.5-graph.txt \
  && pass "reference-points-to-body" "no duplicate B command left in reference" || fail "reference-points-to-body" "phase-2.5-graph.txt still holds the B command or lacks the pointer"

# @cell receipt-block
# ── ② receipt block: graph args only for a helper that knows them ─────────
make_receipt_block() {
  # make_receipt_block <entry> <out>: first bash block of the receipt section, placeholders filled
  receipt_section "$1" | first_bash_block \
    | sed -e 's/"<상위 1건 source_note 경로 또는 no-hit>"/"no-hit"/' -e 's/<Tier 1~4 히트 수 정수>/3/' > "$2"
}
run_receipt() {
  # run_receipt <shell> <block> <helper> <km_mode> [<graph state> <backlinks>] → stdout; argv lands in $WORK/argv.txt; rc kept in $WORK/rc
  local sh="$1" blk="$2" helper="$3" mode="$4" ge="${5-done}" bn="${6-4}" root="${WORK}/plugroot" home="${WORK}/rhome"
  rm -rf "$root" "$home" "${WORK}/argv.txt"
  mkdir -p "${root}/scripts" "$home"
  cp "$helper" "${root}/scripts/km-search-receipt.py"
  # the $HOME-relative fallback helper path, read from the block itself (the Codex skill uses only this one)
  local fb; fb="$(sed -n 's|.*"\$HOME/\([^"]*/km-search-receipt\.py\)".*|\1|p' "$blk" | head -1)"
  if [ -n "$fb" ]; then mkdir -p "$(dirname "${home}/${fb}")"; cp "$helper" "${home}/${fb}"; fi
  local vm=(VAULT_MODE="${RCPT_VM-other}"); [ -z "${RCPT_VM-other}" ] && vm=()
  env -i PATH="$PATH" HOME="$home" CLAUDE_PLUGIN_ROOT="$root" FAKE_RCPT_ARGV="${WORK}/argv.txt" \
    QUERY="q" ${vm[@]+"${vm[@]}"} KM_MODE="$mode" GRAPH_EXPANSION="$ge" BACKLINKS_N="$bn" MB_STATE=ok GRAPHRAG_STATE=ok \
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
    if [ "$(cat "${WORK}/rc")" = 0 ] && has_pair --backlinks 4 && has_pair --graph-expansion done; then pass "receipt-new-helper-deep ${tag}" "graph args passed"; else fail "receipt-new-helper-deep ${tag}" "rc=$(cat "${WORK}/rc") argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
    # failed expansion: state passed, no count (BACKLINKS_N empty → --backlinks absent)
    run_receipt "$SH" "$RB" "${FIX}/fake-receipt-new.py" DEEP failed:no-note "" > /dev/null
    if [ "$(cat "${WORK}/rc")" = 0 ] && has_pair --graph-expansion failed:no-note && ! grep -q -- '--backlinks' "${WORK}/argv.txt"; then pass "receipt-new-helper-failed ${tag}" "state passed, no count"; else fail "receipt-new-helper-failed ${tag}" "rc=$(cat "${WORK}/rc") argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
    OUT="$(run_receipt "$SH" "$RB" "${FIX}/fake-receipt-old.py" DEEP)"
    if [ "$(cat "${WORK}/rc")" = 0 ] && [ -s "${WORK}/argv.txt" ] && ! grep -q -- '--backlinks' "${WORK}/argv.txt" && printf '%s\n' "$OUT" | grep -qx 'KM_RECEIPT_GRAPH_FIELDS=unsupported'; then pass "receipt-old-helper-deep ${tag}" "not passed · receipt still written · unsupported shown"; else fail "receipt-old-helper-deep ${tag}" "rc=$(cat "${WORK}/rc") out=$(printf '%s' "$OUT" | tr '\n' ' ')"; fi
    # helper that knows only --graph-expansion (not --backlinks) → pass neither
    OUT="$(run_receipt "$SH" "$RB" "${WORK}/fake-receipt-half.py" DEEP)"
    if [ "$(cat "${WORK}/rc")" = 0 ] && [ -s "${WORK}/argv.txt" ] && ! grep -q -- '--backlinks\|--graph-expansion' "${WORK}/argv.txt" && printf '%s\n' "$OUT" | grep -qx 'KM_RECEIPT_GRAPH_FIELDS=unsupported'; then pass "receipt-half-helper-deep ${tag}" "both args required"; else fail "receipt-half-helper-deep ${tag}" "rc=$(cat "${WORK}/rc") argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
    run_receipt "$SH" "$RB" "${FIX}/fake-receipt-new.py" QUICK > /dev/null
    if [ "$(cat "${WORK}/rc")" = 0 ] && ! grep -q -- '--backlinks\|--graph-expansion' "${WORK}/argv.txt"; then pass "receipt-quick ${tag}" "no graph args"; else fail "receipt-quick ${tag}" "argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
    # R1 shape: VAULT_MODE never observed (Tier 1 failed) → the helper is told «unknown», with DEEP, next to the graph state
    RCPT_VM="" run_receipt "$SH" "$RB" "${FIX}/fake-receipt-new.py" DEEP failed:no-note "" > /dev/null
    if [ "$(cat "${WORK}/rc")" = 0 ] && has_pair --vault-mode unknown && has_pair --km-mode DEEP && has_pair --graph-expansion failed:no-note && [ "$(grep -cx -- '--vault-mode' "${WORK}/argv.txt")" = 1 ]; then pass "receipt-vault-unobserved ${tag}" "--vault-mode unknown once"; else fail "receipt-vault-unobserved ${tag}" "argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
    # DEEP with no graph result (block not run): mode and vault still reach the helper, no graph args → helper records «미완»
    RCPT_VM="" run_receipt "$SH" "$RB" "${FIX}/fake-receipt-new.py" DEEP "" "" > /dev/null
    if [ "$(cat "${WORK}/rc")" = 0 ] && has_pair --km-mode DEEP && has_pair --vault-mode unknown && ! grep -q -- '--graph-expansion\|--backlinks' "${WORK}/argv.txt"; then pass "receipt-deep-no-graph ${tag}" "mode+vault passed, no graph args"; else fail "receipt-deep-no-graph ${tag}" "argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
    RCPT_VM=same run_receipt "$SH" "$RB" "${FIX}/fake-receipt-new.py" DEEP > /dev/null
    if [ "$(cat "${WORK}/rc")" = 0 ] && has_pair --vault-mode same && has_pair --km-mode DEEP && [ "$(grep -cx -- '--vault-mode' "${WORK}/argv.txt")" = 1 ]; then pass "receipt-vault-same ${tag}" "observed value passed once"; else fail "receipt-vault-same ${tag}" "argv=$(tr '\n' ' ' < "${WORK}/argv.txt" 2>/dev/null)"; fi
  done
done
FAKE_RCPT_ARGV="${WORK}/argv-direct.txt" python3 "${FIX}/fake-receipt-old.py" --backlinks 4 >/dev/null 2>&1; rc=$?
[ "$rc" = 2 ] && pass "receipt-pair-old-helper-direct" "old helper + --backlinks directly → rc 2" || fail "receipt-pair-old-helper-direct" "want rc 2, got ${rc}"

# @cell order
# ── ③ section order ──────────────────────────────────────────────────────
order_ok() {
  # order_ok <file> <tier1 anchor regex>
  local p04 t1 t1s
  p04=$(grep -n '^#* *Phase 0\.4: 구조 문서 축' "$1" | head -1 | cut -d: -f1)
  t1=$(grep -n -e "$2" "$1" | head -1 | cut -d: -f1)
  t1s=$(grep -n '^#### Tier 1-S' "$1" | head -1 | cut -d: -f1)
  [ -n "$p04" ] && [ -n "$t1" ] && [ -n "$t1s" ] && [ "$p04" -gt "$t1" ] && [ "$p04" -lt "$t1s" ]
}
order_ok "$A" '^#### Tier 1 성공 계약' && pass "order ${A}" "Phase 0.4 after Tier 1 success contract, before Tier 1-S" || fail "order ${A}" "Phase 0.4 not between Tier 1 success contract and Tier 1-S"
order_ok "$B" '원문 확보 계약 (Tier 1 전용' && pass "order ${B}" "Phase 0.4 after Tier 1 원문 확보 계약, before Tier 1-S" || fail "order ${B}" "Phase 0.4 not between Tier 1 contract and Tier 1-S"
if git rev-parse --verify -q origin/master >/dev/null 2>&1; then
  git show origin/master:"$A" > "${WORK}/master-search.md" 2>/dev/null
  if order_ok "${WORK}/master-search.md" '^#### Tier 1 성공 계약'; then echo "INFO order-pair origin/master already in new order"; else echo "INFO order-pair origin/master ${A} = old order (check is discriminating)"; fi
fi

# @cell final-line
# ── ④ final-line rule ────────────────────────────────────────────────────
for F in "$A" "$B" commands/search-references/modes-output.txt; do
  n=$(grep -c 'DEEP 이고 `VAULT_MODE` 가 `other` 가 아니면 `+ 그래프 확장(backlinks N)` 생략 ❌' "$F" || true)
  [ "$n" = 1 ] && pass "final-line-rule ${F}" || fail "final-line-rule ${F}" "want 1, got ${n}"
  n=$(grep -c 'QUICK 얕은 질의, 또는 Tier 1 `VAULT_MODE=other` 로 Phase 2.5 를 생략한 경우' "$F" || true)
  [ "$n" = 0 ] && pass "final-line-old-wording-gone ${F}" || fail "final-line-old-wording-gone ${F}" "old omission wording still present (${n})"
done

# @cell tail
echo "----"
echo "PASS_COUNT=${PASS_COUNT} FAIL_COUNT=${FAIL_COUNT}"
[ "$FAIL_COUNT" -eq 0 ]
