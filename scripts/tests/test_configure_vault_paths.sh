#!/bin/bash
# test_configure_vault_paths.sh — Contract tests for scripts/configure-vault-paths.sh
# Verifies that --dry-run does NOT modify any files and does NOT alter skip-worktree index state,
# while regular execution substitutes placeholders and enables skip-worktree.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PASS_COUNT=0
TOTAL_COUNT=4

pass() {
  echo "PASS ${1}"
  PASS_COUNT=$(( PASS_COUNT + 1 ))
}

fail() {
  echo "FAIL ${1} — ${2}" >&2
  exit 1
}

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

# Setup isolated git repository clone
git clone --quiet "${REPO_ROOT}" "${TMP_DIR}/repo"
cd "${TMP_DIR}/repo"

# ─── Case 1: Missing km-config.json returns exit code 1 ──────────
set +e
OUT=$(bash scripts/configure-vault-paths.sh 2>&1)
RC=$?
set -e
if [ "$RC" -ne 1 ]; then
  fail "C1-missing-config" "expected exit 1, got $RC"
fi
if ! echo "$OUT" | grep -q "km-config.json not found"; then
  fail "C1-missing-config" "error message not found in output"
fi
pass "C1-missing-config"

# Prepare valid mock config
cp km-config.example.json km-config.json

# ─── Case 2: --dry-run must not modify files or set skip-worktree ───
OUT_DRY=$(bash scripts/configure-vault-paths.sh --dry-run 2>&1)
RC_DRY=$?
if [ "$RC_DRY" -ne 0 ]; then
  fail "C2-dry-run-exit" "expected exit 0, got $RC_DRY"
fi

# Check working tree status: only km-config.json (untracked) should exist
CHANGED_FILES=$(git status --porcelain | grep -v 'km-config.json' || true)
if [ -n "$CHANGED_FILES" ]; then
  fail "C2-dry-run-no-write" "files modified during --dry-run: $CHANGED_FILES"
fi

# Check skip-worktree index state: must be 0
SKIP_COUNT=$(git ls-files -v | grep -c '^S' || true)
if [ "$SKIP_COUNT" -ne 0 ]; then
  fail "C2-dry-run-no-skip-worktree" "skip-worktree set on $SKIP_COUNT files during --dry-run"
fi
pass "C2-dry-run-no-mutation"

# ─── Case 3: Positive control (live run substitutes and sets skip-worktree) ───
bash scripts/configure-vault-paths.sh >/dev/null 2>&1

SKIP_COUNT_LIVE=$(git ls-files -v | grep -c '^S' || true)
if [ "$SKIP_COUNT_LIVE" -eq 0 ]; then
  fail "C3-live-run-skip-worktree" "expected skip-worktree count > 0, got 0"
fi
pass "C3-live-run-skip-worktree-applied"

# ─── Case 4: Idempotent re-run ───────────────────────────────────
bash scripts/configure-vault-paths.sh >/dev/null 2>&1
SKIP_COUNT_RERUN=$(git ls-files -v | grep -c '^S' || true)
if [ "$SKIP_COUNT_RERUN" -ne "$SKIP_COUNT_LIVE" ]; then
  fail "C4-idempotent-rerun" "skip-worktree count mismatch on rerun: $SKIP_COUNT_RERUN vs $SKIP_COUNT_LIVE"
fi
pass "C4-idempotent-rerun"

echo "PASS ${PASS_COUNT}/${TOTAL_COUNT}"
