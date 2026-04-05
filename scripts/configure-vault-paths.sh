#!/bin/bash
# configure-vault-paths.sh — Substitute {{PLACEHOLDERS}} in skill/agent/command files
# Reads values from km-config.json (via Node.js, no jq required).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=./_lib-config.sh
source "$SCRIPT_DIR/_lib-config.sh"

# ─── Step 1: Validate km-config.json ──────────────────────────────
if [ ! -f km-config.json ]; then
  echo "❌ km-config.json not found. Run '/knowledge-manager-setup' first." >&2
  exit 1
fi

# ─── Step 2: Extract values ───────────────────────────────────────
VAULT_PATH_RAW=$(config_get "storage.obsidian.vaultPath" "")
VAULT_PATH=$(path_normalize "$VAULT_PATH_RAW")
VAULT_NAME=$(vault_name "$VAULT_PATH")
OBSIDIAN_CLI=$(config_get "obsidianCli.path" "")
ZETTELKASTEN_ROOT=$(config_get "storage.obsidian.zettelkastenRoot" "Zettelkasten")
RESEARCH_ROOT=$(config_get "storage.obsidian.researchRoot" "Research")

# ─── Step 3: Validate required fields ─────────────────────────────
if [ -z "$VAULT_PATH" ]; then
  echo "❌ storage.obsidian.vaultPath is empty in km-config.json" >&2
  echo "   Run '/knowledge-manager-setup' to configure." >&2
  exit 1
fi

echo "Configuring vault paths:"
echo "  VAULT_PATH        = $VAULT_PATH"
echo "  VAULT_NAME        = $VAULT_NAME"
echo "  OBSIDIAN_CLI      = ${OBSIDIAN_CLI:-<not set>}"
echo "  ZETTELKASTEN_ROOT = $ZETTELKASTEN_ROOT"
echo "  RESEARCH_ROOT     = $RESEARCH_ROOT"
echo

# ─── Step 4: Restore templates first (idempotent re-run) ──────────
# Release skip-worktree on any previously configured files
SKIP_FILES=$(git ls-files -v 2>/dev/null | grep "^S " | cut -c3- || true)
if [ -n "$SKIP_FILES" ]; then
  echo "Releasing skip-worktree on previously configured files..."
  echo "$SKIP_FILES" | xargs -r git update-index --no-skip-worktree
  echo "$SKIP_FILES" | xargs -r git checkout HEAD --
fi

# ─── Step 5: Substitute placeholders ──────────────────────────────
SUBST_COUNT=0
while IFS= read -r -d '' f; do
  # Skip anti-pattern teaching file
  case "$f" in
    ./skills/km-storage-abstraction.md|./.claude/skills/km-storage-abstraction.md)
      continue ;;
  esac

  if grep -q "{{VAULT_PATH}}\|{{VAULT_NAME}}\|{{OBSIDIAN_CLI}}\|{{ZETTELKASTEN_ROOT}}\|{{RESEARCH_ROOT}}" "$f" 2>/dev/null; then
    sed -i \
      -e "s|{{VAULT_PATH}}|$VAULT_PATH|g" \
      -e "s|{{VAULT_NAME}}|$VAULT_NAME|g" \
      -e "s|{{OBSIDIAN_CLI}}|$OBSIDIAN_CLI|g" \
      -e "s|{{ZETTELKASTEN_ROOT}}|$ZETTELKASTEN_ROOT|g" \
      -e "s|{{RESEARCH_ROOT}}|$RESEARCH_ROOT|g" \
      "$f"
    SUBST_COUNT=$((SUBST_COUNT + 1))
  fi
done < <(find skills agents commands .claude -type f -name "*.md" -print0 2>/dev/null)

echo "✅ Substituted placeholders in $SUBST_COUNT files"

# ─── Step 6: Apply skip-worktree to tracked files ─────────────────
echo "Marking configured files as skip-worktree..."
MARKED=0
while IFS= read -r -d '' f; do
  # Strip leading ./
  f="${f#./}"
  case "$f" in
    skills/km-storage-abstraction.md|.claude/skills/km-storage-abstraction.md)
      continue ;;
  esac
  if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    git update-index --skip-worktree "$f" 2>/dev/null && MARKED=$((MARKED + 1)) || true
  fi
done < <(find skills agents commands .claude -type f -name "*.md" -print0 2>/dev/null)

echo "✅ skip-worktree enabled on $MARKED tracked files"
echo
echo "🎉 Vault path configuration complete."
