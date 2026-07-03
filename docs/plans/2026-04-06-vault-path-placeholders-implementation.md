# Vault Path Placeholders Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace all hardcoded personal vault paths in knowledge-manager deploy repo with a 5-placeholder system (`{{VAULT_PATH}}`, `{{VAULT_NAME}}`, `{{OBSIDIAN_CLI}}`, `{{ZETTELKASTEN_ROOT}}`, `{{RESEARCH_ROOT}}`) that auto-substitutes via Node.js-based shell script triggered by `/knowledge-manager-setup`.

**Architecture:** In-place sed substitution driven by `km-config.json`. Skip-worktree git flag prevents local modifications from appearing as dirty. `/km-update` command automates upstream pull + re-substitution.

**Tech Stack:** bash, Node.js (already required for MCP), sed, git skip-worktree, markdown.

**Branch:** `feature/vault-path-placeholders` (Phase 0 complete: backup branch + Group A commit + design doc committed)

**Worker parallelization:** 5 parallel workers (α Infrastructure, β Docs, γ Skills-Large, δ Skills-Small, ε Agents-Commands) via `/tofu-at-codex`, followed by Lead-driven Phase 2 verification and merge.

---

## Conventions

- All file paths relative to `/home/tofu/AI/knowledge-manager/`
- Every skill/agent/command modification must keep `.claude/` mirror in sync — each task edits both atomically
- Each worker creates a sub-branch `feature/vp-worker-{name}` off `feature/vault-path-placeholders`
- Commits use conventional prefixes: `feat:`, `refactor:`, `docs:`, `test:`, `chore:`

## Placeholder Rules

```
{{VAULT_PATH}}         — absolute vault path (from storage.obsidian.vaultPath)
{{VAULT_NAME}}         — vault basename (derived)
{{OBSIDIAN_CLI}}       — Obsidian CLI executable (from obsidianCli.path)
{{ZETTELKASTEN_ROOT}}  — vault-relative path (default: "Zettelkasten")
{{RESEARCH_ROOT}}      — vault-relative path (default: "Research")
```

**Substitution guidance per pattern:**
- `/home/tofu/AI/AI_Second_Brain` → `{{VAULT_PATH}}`
- `/path/to/your/vault` → `{{VAULT_PATH}}`
- `C:\Users\YourName\OneDrive\Desktop\AI\AI_Second_Brain` → `{{VAULT_PATH}}`
- `AI_Second_Brain` (standalone, as vault name) → `{{VAULT_NAME}}`
- `Zettelkasten/` (as root folder, 1-depth) → `{{ZETTELKASTEN_ROOT}}/`
- `Research/` (as root folder, 1-depth) → `{{RESEARCH_ROOT}}/`
- Obsidian CLI paths → `{{OBSIDIAN_CLI}}`

**Exception:** `skills/km-storage-abstraction.md` line ~63 is an intentional anti-pattern example. Do NOT placeholder. Rewrite the literal vault name to `YourVaultName` (generic).

---

# Worker α — Infrastructure

**Branch:** `feature/vp-worker-alpha` (from `feature/vault-path-placeholders`)
**Scope:** 8 files
**Dependencies:** none (can start immediately)

### Task α-1: Create scripts/ directory and _lib-config.sh

**Files:**
- Create: `scripts/_lib-config.sh`

**Step 1: Create directory**

```bash
mkdir -p scripts
```

**Step 2: Write _lib-config.sh**

```bash
#!/bin/bash
# _lib-config.sh — km-config.json parser using Node.js (no jq dependency)
# Sourced by other scripts. Not meant to be executed directly.

CONFIG_FILE="${CONFIG_FILE:-km-config.json}"

# Read a dot-path value from km-config.json.
# Usage: config_get "storage.obsidian.vaultPath" "/default/path"
config_get() {
  local path="$1"
  local default="${2:-}"
  node -e "
    try {
      const c = require('./$CONFIG_FILE');
      const parts = '$path'.split('.');
      let v = c;
      for (const p of parts) v = v == null ? undefined : v[p];
      console.log(v == null ? '$default' : v);
    } catch (e) {
      console.log('$default');
    }
  "
}

# Extract vault name (basename) from vault path.
# Usage: vault_name "/path/to/MyVault"
vault_name() {
  local vp="$1"
  node -e "
    const p = ('$vp').replace(/\\\\/g, '/').replace(/\\/+\$/, '');
    const parts = p.split('/').filter(Boolean);
    console.log(parts[parts.length - 1] || 'MyVault');
  "
}

# Normalize path (Windows backslash → forward slash).
# Usage: path_normalize 'C:\Users\foo'
path_normalize() {
  node -e "console.log(('$1').replace(/\\\\/g, '/'))"
}
```

**Step 3: Verify syntax**

```bash
bash -n scripts/_lib-config.sh
```
Expected: no output (syntax OK)

**Step 4: Test helpers with a mock config**

```bash
mkdir -p scripts/tests/fixtures
cat > scripts/tests/fixtures/mock-km-config.json <<'EOF'
{
  "storage": {
    "obsidian": {
      "vaultPath": "/home/testuser/MyVault",
      "zettelkastenRoot": "Zettelkasten",
      "researchRoot": "Research"
    }
  },
  "obsidianCli": {
    "path": "/usr/local/bin/obsidian"
  }
}
EOF

# Run a smoke test from scripts/tests/fixtures directory
cd scripts/tests/fixtures
CONFIG_FILE=mock-km-config.json
source ../../_lib-config.sh
test "$(config_get 'storage.obsidian.vaultPath' '')" = "/home/testuser/MyVault"
test "$(vault_name '/home/testuser/MyVault')" = "MyVault"
test "$(path_normalize 'C:\\Users\\foo')" = "C:/Users/foo"
cd ../../..
echo "✅ _lib-config.sh helpers OK"
```
Expected: `✅ _lib-config.sh helpers OK`

**Step 5: Commit**

```bash
git checkout -b feature/vp-worker-alpha
git add scripts/_lib-config.sh scripts/tests/fixtures/mock-km-config.json
git commit -m "feat(scripts): add _lib-config.sh with Node.js-based config parser"
```

---

### Task α-2: Create configure-vault-paths.sh

**Files:**
- Create: `scripts/configure-vault-paths.sh`

**Step 1: Write the script**

```bash
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
```

**Step 2: Verify syntax**

```bash
bash -n scripts/configure-vault-paths.sh
```
Expected: no output

**Step 3: Make executable**

```bash
chmod +x scripts/configure-vault-paths.sh
```

**Step 4: Commit**

```bash
git add scripts/configure-vault-paths.sh
git commit -m "feat(scripts): add configure-vault-paths.sh substitution engine"
```

---

### Task α-3: Create km-update.sh

**Files:**
- Create: `scripts/km-update.sh`

**Step 1: Write the script**

```bash
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
```

**Step 2: Verify + executable**

```bash
bash -n scripts/km-update.sh
chmod +x scripts/km-update.sh
```

**Step 3: Commit**

```bash
git add scripts/km-update.sh
git commit -m "feat(scripts): add km-update.sh orchestrator (pull + re-configure)"
```

---

### Task α-4: Extend km-config.example.json schema

**Files:**
- Modify: `km-config.example.json`

**Step 1: Read current file**

```bash
sed -n '10,25p' km-config.example.json
```

**Step 2: Add 2 new fields via edit**

Inside `storage.obsidian` object, immediately after `vaultPath` and its `_vaultPath_examples` block, add:

```json
      "zettelkastenRoot": "Zettelkasten",
      "_zettelkastenRoot_help": "Zettelkasten 노트 루트 (vault 상대경로). 예: 'Zettelkasten' 또는 'Library/Zettelkasten'",
      "researchRoot": "Research",
      "_researchRoot_help": "Research 노트 루트 (vault 상대경로). 예: 'Research' 또는 'Library/Research'",
```

Also add `wsl` example to `_vaultPath_examples`:
```json
        "wsl": "/mnt/c/Users/YourName/Documents/MyVault"
```

**Step 3: Validate JSON**

```bash
node -e "JSON.parse(require('fs').readFileSync('km-config.example.json'))" && echo "✅ Valid JSON"
```
Expected: `✅ Valid JSON`

**Step 4: Commit**

```bash
git add km-config.example.json
git commit -m "feat(config): add zettelkastenRoot, researchRoot fields to schema"
```

---

### Task α-5: Create commands/km-update.md slash command

**Files:**
- Create: `commands/km-update.md`
- Create: `.claude/commands/km-update.md` (mirror)

**Step 1: Write command file**

```markdown
---
description: Knowledge Manager 업데이트 — upstream pull + vault 경로 재적용
allowed-tools: Bash
---

# /km-update — Knowledge Manager 업데이트

배포 repo의 최신 버전을 받고, 기존 vault 설정을 자동으로 재적용합니다.

## 실행

```bash
bash scripts/km-update.sh
```

## 동작 순서

1. skip-worktree 설정된 파일들의 잠금 해제
2. placeholder 템플릿으로 복원 (`git checkout HEAD`)
3. `git pull origin <current-branch>` 로 upstream 업데이트
4. `scripts/configure-vault-paths.sh` 재실행
5. skip-worktree 재설정

## 주의사항

- km-config.json 이외의 파일을 수동 편집했다면 stash 또는 commit 후 실행
- vault 경로를 **변경**하고 싶다면 `/km-update` 대신 `/knowledge-manager-setup` 재실행
- `/km-update` 실행 전 권장: `git status` 로 예상치 못한 로컬 변경 확인

## 에러 대응

| 에러 | 원인 | 해결 |
|---|---|---|
| "Uncommitted changes detected" | skip-worktree 바깥에서 수동 편집함 | `git stash` 또는 `git commit` 후 재실행 |
| "Merge conflict" | upstream이 치환 구간을 수정했음 | `git mergetool` 또는 수동 해결 후 `bash scripts/configure-vault-paths.sh` |
| "km-config.json not found" | setup 미실행 | `/knowledge-manager-setup` 먼저 실행 |
```

**Step 2: Create mirror**

```bash
mkdir -p .claude/commands
cp commands/km-update.md .claude/commands/km-update.md
```

**Step 3: Verify mirror**

```bash
diff -q commands/km-update.md .claude/commands/km-update.md
```
Expected: no output (silent)

**Step 4: Commit**

```bash
git add commands/km-update.md .claude/commands/km-update.md
git commit -m "feat(commands): add /km-update slash command"
```

---

### Task α-6: Update knowledge-manager-setup.md Phase 4

**Files:**
- Modify: `commands/knowledge-manager-setup.md` (Phase 4 section, append after km-config.json creation)
- Modify: `.claude/commands/knowledge-manager-setup.md` (mirror, if it exists)

**Step 1: Check if .claude/ mirror exists**

```bash
ls -la .claude/commands/knowledge-manager-setup.md 2>/dev/null && echo "mirror exists" || echo "no mirror"
```

**Step 2: Locate Phase 4 in current file**

```bash
grep -n "## Phase 4" commands/knowledge-manager-setup.md
```
Expected: finds "Phase 4: 설정 파일 생성"

**Step 3: Add script invocation after `km-config.json 생성 완료` log**

Find the section ending with:
```
Write({
  file_path: "km-config.json",
  content: JSON.stringify(config, null, 2)
})

console.log(`
✅ 설정 파일 생성 완료: km-config.json
`)
```

Append immediately after:

```javascript
// NEW: Apply vault paths to skill files
console.log(`
⏳ vault 경로를 스킬 파일들에 적용하고 있어요...
(skills/, agents/, commands/ 아래의 모든 .md 파일 업데이트)
`)

const substResult = Bash(`bash scripts/configure-vault-paths.sh 2>&1`)
console.log(substResult)

console.log(`
✅ 모든 스킬 파일에 vault 경로가 적용되었어요.

💡 향후 업데이트
   최신 버전을 받으려면: /km-update
   vault 경로를 바꾸려면: /knowledge-manager-setup 재실행
`)
```

**Step 4: Sync mirror if exists**

```bash
if [ -f .claude/commands/knowledge-manager-setup.md ]; then
  cp commands/knowledge-manager-setup.md .claude/commands/knowledge-manager-setup.md
  diff -q commands/knowledge-manager-setup.md .claude/commands/knowledge-manager-setup.md
fi
```

**Step 5: Commit**

```bash
git add commands/knowledge-manager-setup.md
[ -f .claude/commands/knowledge-manager-setup.md ] && git add .claude/commands/knowledge-manager-setup.md
git commit -m "feat(setup): auto-invoke configure-vault-paths.sh in Phase 4"
```

---

### Task α-7: Merge worker α back to feature branch

```bash
git checkout feature/vault-path-placeholders
git merge --no-ff feature/vp-worker-alpha -m "merge: worker α (infrastructure)"
```

---

# Worker β — Documentation

**Branch:** `feature/vp-worker-beta` (from `feature/vault-path-placeholders`)
**Scope:** 4 files
**Dependencies:** none (can start in parallel with α)

### Task β-1: Update README.md Installation section

**Files:**
- Modify: `README.md` (add new section after `## Requirements`)

**Step 1: Locate insertion point**

```bash
grep -n "## Requirements" README.md
```

**Step 2: Insert new `## Installation & Configuration` section after `## Requirements` block**

Use Edit tool with this content (full text in design doc Section 5 Subsection 1). Key sections:
- First-time setup (git clone, deps, /knowledge-manager-setup)
- Updating to latest version (/km-update)
- Re-configuring vault path
- Under the hood — placeholder system (5-row table)

**Step 3: Verify structure**

```bash
grep -c "Installation & Configuration\|placeholder" README.md
```
Expected: ≥ 3

**Step 4: Commit**

```bash
git checkout -b feature/vp-worker-beta
git add README.md
git commit -m "docs(readme): add installation + placeholder system section"
```

---

### Task β-2: Create CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

**Step 1: Write file with Claude Code project contract**

Content from design doc Section 5 Subsection 2. Key sections:
- Critical: Placeholder System
- Placeholders in source vs after setup
- Rules for editing skill files (5 rules)
- How to test your edits (5-step workflow)
- Directory Layout
- Commands for Users

**Step 2: Verify**

```bash
test -f CLAUDE.md && echo "created"
grep -c "{{VAULT_PATH}}" CLAUDE.md
```
Expected: `created` and ≥ 2

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md (Claude Code project contract)"
```

---

### Task β-3: Create AGENTS.md

**Files:**
- Create: `AGENTS.md`

**Step 1: Write file with generic AI agent contract**

Content from design doc Section 5 Subsection 3. Key sections:
- Repository Identity
- Read First (order: CLAUDE.md → README.md → docs/vault-path-configuration.md)
- Placeholder Contract (CRITICAL)
- Editing Workflow
- File Synchronization Invariant
- Verification Before Commit
- Out of Scope

**Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add AGENTS.md (generic AI agent contract)"
```

---

### Task β-4: Create docs/vault-path-configuration.md

**Files:**
- Create: `docs/vault-path-configuration.md`

**Step 1: Write technical reference**

Content from design doc Section 5 Subsection 4. Key sections:
- Overview
- Components (6-row table: config, parser, engine, orchestrator, wizard, command)
- Placeholder Reference (5-row table)
- Config Schema (JSON snippet)
- Substitution Algorithm (7 steps)
- Skip-worktree Mechanism
- Re-running Setup
- Troubleshooting (4 cases minimum)

**Step 2: Commit**

```bash
git add docs/vault-path-configuration.md
git commit -m "docs: add vault-path-configuration technical reference"
```

---

### Task β-5: Merge worker β back

```bash
git checkout feature/vault-path-placeholders
git merge --no-ff feature/vp-worker-beta -m "merge: worker β (documentation)"
```

---

# Worker γ — Skills Large Files

**Branch:** `feature/vp-worker-gamma` (from `feature/vault-path-placeholders`)
**Scope:** 6 files (3 × 2 mirrors)
**Dependencies:** none

### Task γ-1: Refactor skills/km-export-formats.md (16 occurrences)

**Files:**
- Modify: `skills/km-export-formats.md`
- Modify: `.claude/skills/km-export-formats.md` (mirror, keep identical)

**Step 1: List all personal-path patterns**

```bash
grep -nE "/home/tofu/AI/AI_Second_Brain|C:\\\\Users\\\\YourName|AI_Second_Brain" skills/km-export-formats.md
```

**Step 2: Apply substitutions via Edit tool (one Edit per pattern)**

For each occurrence:
- `/home/tofu/AI/AI_Second_Brain` → `{{VAULT_PATH}}`
- `C:\Users\YourName\OneDrive\Desktop\AI\AI_Second_Brain` → `{{VAULT_PATH}}`
- Standalone `AI_Second_Brain/` (as vault name prefix) → `{{VAULT_NAME}}/`
- `Zettelkasten/` root → `{{ZETTELKASTEN_ROOT}}/`
- `Research/` root → `{{RESEARCH_ROOT}}/`

**Step 3: Verify substitution**

```bash
grep -cE "{{VAULT_PATH}}|{{VAULT_NAME}}|{{ZETTELKASTEN_ROOT}}|{{RESEARCH_ROOT}}" skills/km-export-formats.md
grep -cE "/home/tofu|C:\\\\Users\\\\YourName" skills/km-export-formats.md
```
Expected: first > 0, second = 0

**Step 4: Sync mirror**

```bash
cp skills/km-export-formats.md .claude/skills/km-export-formats.md
diff -q skills/km-export-formats.md .claude/skills/km-export-formats.md
```

**Step 5: Commit**

```bash
git checkout -b feature/vp-worker-gamma
git add skills/km-export-formats.md .claude/skills/km-export-formats.md
git commit -m "refactor(skills): placeholder-ize km-export-formats.md"
```

---

### Task γ-2: Refactor skills/km-image-pipeline.md (8 occurrences)

Same pattern as γ-1. Key substitutions:
- `/home/tofu/AI/AI_Second_Brain` → `{{VAULT_PATH}}`
- `AI_Second_Brain/Resources/images/` → `{{VAULT_NAME}}/Resources/images/`
- `Zettelkasten/` → `{{ZETTELKASTEN_ROOT}}/`

**Verify + mirror sync + commit:**

```bash
grep -cE "/home/tofu|C:\\\\Users\\\\YourName" skills/km-image-pipeline.md  # expect 0
cp skills/km-image-pipeline.md .claude/skills/km-image-pipeline.md
diff -q skills/km-image-pipeline.md .claude/skills/km-image-pipeline.md
git add skills/km-image-pipeline.md .claude/skills/km-image-pipeline.md
git commit -m "refactor(skills): placeholder-ize km-image-pipeline.md"
```

---

### Task γ-3: Refactor skills/km-content-extraction.md (6 occurrences)

Same pattern. Key substitutions:
- `/home/tofu/AI/AI_Second_Brain` → `{{VAULT_PATH}}`
- `AI_Second_Brain/{path}` in Read examples → `{{VAULT_NAME}}/{path}` (if used as vault name prefix) or `{{VAULT_PATH}}/{path}` (if absolute)

**Verify + mirror sync + commit:**

```bash
grep -cE "/home/tofu|C:\\\\Users\\\\YourName" skills/km-content-extraction.md  # expect 0
cp skills/km-content-extraction.md .claude/skills/km-content-extraction.md
diff -q skills/km-content-extraction.md .claude/skills/km-content-extraction.md
git add skills/km-content-extraction.md .claude/skills/km-content-extraction.md
git commit -m "refactor(skills): placeholder-ize km-content-extraction.md"
```

---

### Task γ-4: Merge worker γ back

```bash
git checkout feature/vault-path-placeholders
git merge --no-ff feature/vp-worker-gamma -m "merge: worker γ (skills large)"
```

---

# Worker δ — Skills Small + Anti-pattern

**Branch:** `feature/vp-worker-delta` (from `feature/vault-path-placeholders`)
**Scope:** 10 files (5 × 2 mirrors)
**Dependencies:** none

### Task δ-1: Refactor skills/km-glm-ocr.md (4 occurrences)

Same substitution pattern as γ. Verify, mirror, commit.

```bash
git checkout -b feature/vp-worker-delta
# ... edit, verify, mirror sync ...
git add skills/km-glm-ocr.md .claude/skills/km-glm-ocr.md
git commit -m "refactor(skills): placeholder-ize km-glm-ocr.md"
```

### Task δ-2: Refactor skills/km-workflow.md (1 occurrence, Windows path)

Line ~679: `file_path: "C:\Users\YourName\OneDrive\Desktop\AI\AI_Second_Brain\..."` → `file_path: "{{VAULT_PATH}}/..."` (use forward slashes in replacement).

Verify, mirror, commit.

### Task δ-3: Refactor skills/km-link-audit.md (1 occurrence)

Line ~42: `Glob: "AI_Second_Brain/**/*.md"` → `Glob: "{{VAULT_NAME}}/**/*.md"`

Verify, mirror, commit.

### Task δ-4: Refactor skills/km-archive-reorganization.md (1 occurrence)

Line ~317: `mv "/mnt/c/Users/YourName/.../Second_Brain/Library/Zettelkasten/AI-연구/old-note.md" "/mnt/c/Users/YourName/.../Second_Brain/Library/Zettelkasten/AI-도구/old-note.md"` → both paths use `{{VAULT_PATH}}/Library/...`

Verify, mirror, commit.

### Task δ-5: Rewrite km-storage-abstraction.md anti-pattern (NO placeholder)

**Files:**
- Modify: `skills/km-storage-abstraction.md`
- Modify: `.claude/skills/km-storage-abstraction.md`

**Step 1: Locate line 63**

```bash
grep -n "AI_Second_Brain" skills/km-storage-abstraction.md
```

**Step 2: Edit — replace concrete vault name with generic placeholder text**

Change:
```
❌ 틀림: AI_Second_Brain/Zettelkasten/...  (vault 이름 중복 금지)
```

To:
```
❌ 틀림: YourVaultName/Zettelkasten/...  (vault 이름 중복 금지)
```

**Step 3: Verify no placeholder introduced**

```bash
grep -c "{{" skills/km-storage-abstraction.md
```
Expected: 0 (anti-pattern file must NOT have placeholders)

**Step 4: Mirror sync + commit**

```bash
cp skills/km-storage-abstraction.md .claude/skills/km-storage-abstraction.md
git add skills/km-storage-abstraction.md .claude/skills/km-storage-abstraction.md
git commit -m "refactor(skills): rewrite km-storage-abstraction anti-pattern as generic"
```

### Task δ-6: Merge worker δ back

```bash
git checkout feature/vault-path-placeholders
git merge --no-ff feature/vp-worker-delta -m "merge: worker δ (skills small + anti-pattern)"
```

---

# Worker ε — Agents + Commands

**Branch:** `feature/vp-worker-epsilon` (from `feature/vault-path-placeholders`)
**Scope:** 8 files (4 × 2 mirrors)
**Dependencies:** none
**IMPORTANT:** `commands/knowledge-manager{,-m}.md` already has Group A edits (SNS crawling). Preserve them.

### Task ε-1: Refactor agents/knowledge-manager.md (11 occurrences)

Includes Windows paths like `C:\Users\Public\AI_Second_Brain\AI_Second_Brain`. Substitute to `{{VAULT_PATH}}` (normalized).

```bash
git checkout -b feature/vp-worker-epsilon
# ... edits ...
cp agents/knowledge-manager.md .claude/agents/knowledge-manager.md
diff -q agents/knowledge-manager.md .claude/agents/knowledge-manager.md
git add agents/knowledge-manager.md .claude/agents/knowledge-manager.md
git commit -m "refactor(agents): placeholder-ize knowledge-manager.md"
```

### Task ε-2: Refactor commands/knowledge-manager.md (5 occurrences)

**CRITICAL:** Group A already modified this file (SNS crawling table row at ~line 250). Do NOT revert that change. Only placeholder the remaining hardcoded paths.

Verify SNS line preserved after refactor:
```bash
grep "playwright-cli open → snapshot" commands/knowledge-manager.md
```
Expected: match found.

Then mirror, commit.

### Task ε-3: Refactor commands/knowledge-manager-m.md (5 occurrences)

Same CRITICAL note as ε-2.

### Task ε-4: Refactor commands/knowledge-manager-at.md (6 occurrences)

This file was fully reverted in pre-phase work, so no Group A constraint.

### Task ε-5: Merge worker ε back

```bash
git checkout feature/vault-path-placeholders
git merge --no-ff feature/vp-worker-epsilon -m "merge: worker ε (agents + commands)"
```

---

# Phase 2 — Lead Verification + Merge

### Task V-1: Dry-run configure-vault-paths.sh with fixture

**Step 1: Create temporary test km-config.json (do not commit)**

```bash
cp scripts/tests/fixtures/mock-km-config.json km-config.json.bak 2>/dev/null || true
cat > km-config.json <<'EOF'
{
  "storage": {
    "obsidian": {
      "vaultPath": "/tmp/test/vault",
      "zettelkastenRoot": "Zettelkasten",
      "researchRoot": "Research"
    }
  },
  "obsidianCli": {
    "path": "/tmp/test/obsidian"
  }
}
EOF
```

**Step 2: Run script**

```bash
bash scripts/configure-vault-paths.sh
```
Expected:
- No errors
- "Substituted placeholders in N files" where N > 0
- "skip-worktree enabled on M tracked files" where M > 0

**Step 3: Verify substitution happened**

```bash
grep -rl "/tmp/test/vault" skills/ agents/ commands/ .claude/ | head -5
```
Expected: several files listed

**Step 4: Rollback test state**

```bash
# Release skip-worktree
git ls-files -v | grep "^S " | cut -c3- | xargs -r git update-index --no-skip-worktree
# Restore templates
git ls-files -v | grep "^H " | cut -c3- | grep -E "\.md$" | xargs -r git checkout HEAD --
# Or simpler: reset everything not tied to the commits on this branch
git checkout HEAD -- skills agents commands .claude
# Remove test config
rm km-config.json
```

**Step 5: Verify placeholders restored**

```bash
grep -c "{{VAULT_PATH}}" skills/km-image-pipeline.md
```
Expected: > 0 (template form)

---

### Task V-2: Grep verification — no personal paths leaked

```bash
grep -rE "/home/[a-z]+/|C:\\\\Users\\\\[a-zA-Z]+\\\\" skills/ agents/ commands/ .claude/ docs/ 2>/dev/null | grep -v "_examples\|_help\|docs/plans/" || echo "✅ No personal paths leaked"
```
Expected: `✅ No personal paths leaked`

---

### Task V-3: Mirror sync verification

```bash
FAIL=0
for f in skills/km-*.md; do
  mirror=".claude/$f"
  if [ -f "$mirror" ]; then
    diff -q "$f" "$mirror" >/dev/null 2>&1 || { echo "MISMATCH: $f"; FAIL=1; }
  fi
done
for f in agents/knowledge-manager.md commands/knowledge-manager{,-m,-at,-setup}.md commands/km-update.md; do
  mirror=".claude/$f"
  [ -f "$mirror" ] && { diff -q "$f" "$mirror" >/dev/null 2>&1 || { echo "MISMATCH: $f"; FAIL=1; }; }
done
[ $FAIL -eq 0 ] && echo "✅ All mirrors in sync"
```
Expected: `✅ All mirrors in sync`

---

### Task V-4: Group A preservation check

```bash
# SNS crawling change preserved
grep -q "playwright-cli open → snapshot" commands/knowledge-manager.md && echo "✅ SNS change preserved"
grep -q "playwright-cli open → snapshot" commands/knowledge-manager-m.md && echo "✅ SNS change preserved (mobile)"
# km-social-media.md encoding OK (should have frontmatter, not mojibake)
head -5 skills/km-social-media.md | grep -q "^name: km-social-media" && echo "✅ km-social-media frontmatter OK"
```
Expected: 3 green lines

---

### Task V-5: km-storage-abstraction.md anti-pattern check

```bash
# Should have NO placeholders
grep -c "{{" skills/km-storage-abstraction.md
# Should have generic "YourVaultName"
grep "YourVaultName" skills/km-storage-abstraction.md
# Should NOT have literal "AI_Second_Brain"
grep "AI_Second_Brain" skills/km-storage-abstraction.md
```
Expected: first = 0, second = 1+, third = 0

---

### Task V-6: Merge feature → master

```bash
git log --oneline feature/vault-path-placeholders | head -20
git checkout master
git merge --no-ff feature/vault-path-placeholders \
  -m "feat: vault path placeholder system + /km-update command

- 5 placeholders ({{VAULT_PATH}}, {{VAULT_NAME}}, {{OBSIDIAN_CLI}},
  {{ZETTELKASTEN_ROOT}}, {{RESEARCH_ROOT}}) auto-substituted by
  scripts/configure-vault-paths.sh on /knowledge-manager-setup
- skip-worktree mechanism prevents git conflicts after configuration
- New /km-update command for upstream pull + re-configuration
- Docs: CLAUDE.md, AGENTS.md, docs/vault-path-configuration.md
- Anti-pattern teaching in km-storage-abstraction rewritten generic

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git push origin master
```

### Task V-7: Cleanup (optional, wait 1-2 weeks before deleting backup)

```bash
# After validation period, delete backup branch
# git branch -d backup/pre-vault-placeholders
# git push origin --delete backup/pre-vault-placeholders

# Delete worker sub-branches (already merged)
for b in feature/vp-worker-{alpha,beta,gamma,delta,epsilon}; do
  git branch -d "$b" 2>/dev/null || true
done
```

---

## Verification Criteria Summary

### Hard gates (must pass before merge to master)
- [x] Phase 0: backup branch + feature branch + Group A commit + design doc committed
- [ ] V-1: configure-vault-paths.sh dry-run produces expected substitutions
- [ ] V-2: No personal paths leaked (grep returns `✅ No personal paths leaked`)
- [ ] V-3: All mirror pairs in sync
- [ ] V-4: Group A functionality (SNS crawling) preserved
- [ ] V-5: km-storage-abstraction anti-pattern rewritten correctly
- [ ] All 5 worker sub-branches merged to feature branch

### Soft gates
- [ ] km-update.sh dry-run possible (TODO: add `--dry-run` flag in follow-up)
- [ ] docs/vault-path-configuration.md has ≥ 4 troubleshooting cases
- [ ] README.md Installation section visible in table of contents

---

## Rollback

If any Phase 2 verification fails:

```bash
git checkout master
git reset --hard backup/pre-vault-placeholders
# Do NOT push --force without explicit approval
```

## Worker Execution via /tofu-at-codex

After this plan is approved, Lead invokes `/tofu-at-codex` with:

```
Task: Execute implementation plan at docs/plans/2026-04-06-vault-path-placeholders-implementation.md

Workers (5 parallel):
  α — Worker α (Infrastructure), tasks α-1 to α-7
  β — Worker β (Documentation), tasks β-1 to β-5
  γ — Worker γ (Skills Large), tasks γ-1 to γ-4
  δ — Worker δ (Skills Small + Anti-pattern), tasks δ-1 to δ-6
  ε — Worker ε (Agents + Commands), tasks ε-1 to ε-5

Each worker:
  1. Creates its own sub-branch from feature/vault-path-placeholders
  2. Executes assigned tasks strictly in order
  3. Verifies each task before committing
  4. Reports back to Lead with commit SHA list

Lead handles Phase 2 (verification V-1 to V-7) after all workers report done.
```
