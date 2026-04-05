#!/bin/bash
# km-update.sh — Pull latest from upstream + re-apply vault configuration
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "🔄 Knowledge Manager — Update"
echo

# ─── Step 1: Safety check ─────────────────────────────────────────
# Any modifications outside skip-worktree scope must be stashed first
UNTRACKED_CHANGES=$(git status --porcelain | grep -v "^??" || true)
if [ -n "$UNTRACKED_CHANGES" ]; then
  echo "⚠️  Uncommitted changes detected outside skip-worktree scope:"
  echo "$UNTRACKED_CHANGES"
  echo
  echo "Stash or commit them before running km-update.sh."
  exit 1
fi

# ─── Step 2: Release skip-worktree ────────────────────────────────
SKIP_FILES=$(git ls-files -v | grep "^S " | cut -c3- || true)
if [ -n "$SKIP_FILES" ]; then
  echo "Releasing skip-worktree locks..."
  echo "$SKIP_FILES" | xargs git update-index --no-skip-worktree
fi

# ─── Step 3: Restore placeholder templates ────────────────────────
if [ -n "$SKIP_FILES" ]; then
  echo "Restoring placeholder templates..."
  echo "$SKIP_FILES" | xargs git checkout HEAD --
fi

# ─── Step 4: Pull upstream ────────────────────────────────────────
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Pulling upstream: origin/$CURRENT_BRANCH..."
git pull origin "$CURRENT_BRANCH"

# ─── Step 5: Re-apply vault configuration ─────────────────────────
echo
echo "Re-applying vault configuration..."
bash "$SCRIPT_DIR/configure-vault-paths.sh"

echo
echo "✅ Update complete."
