#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."

failures=0

pass() {
  printf 'PASS: %s\n' "$1"
}

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  failures=$((failures + 1))
}

contains() {
  local file="$1"
  local needle="$2"
  local label="$3"
  if grep -Fq -- "$needle" "$file"; then
    pass "$label"
  else
    fail "$label ($file lacks: $needle)"
  fi
}

not_contains() {
  local file="$1"
  local needle="$2"
  local label="$3"
  if grep -Fq -- "$needle" "$file"; then
    fail "$label ($file still contains: $needle)"
  else
    pass "$label"
  fi
}

same_file() {
  local left="$1"
  local right="$2"
  local label="$3"
  if cmp -s "$left" "$right"; then
    pass "$label"
  else
    fail "$label ($left != $right)"
  fi
}

appears_before() {
  local file="$1"
  local first="$2"
  local second="$3"
  local label="$4"
  local first_line second_line
  first_line="$(grep -nF -- "$first" "$file" | head -1 | cut -d: -f1 || true)"
  second_line="$(grep -nF -- "$second" "$file" | head -1 | cut -d: -f1 || true)"
  if [[ -n "$first_line" && -n "$second_line" && "$first_line" -lt "$second_line" ]]; then
    pass "$label"
  else
    fail "$label ($file order: ${first_line:-missing} !< ${second_line:-missing})"
  fi
}

is_within_reference() {
  local candidate="$1"
  local root="$2"
  local canonical_candidate canonical_root
  canonical_candidate="$(realpath "$candidate")"
  canonical_root="$(realpath "$root")"
  [[ "$canonical_candidate" == "$canonical_root"/* ]]
}

# Harness controls: prove that both positive and negative assertions execute.
contains ".agent/skills/km-workflow/SKILL.md" "# Knowledge Manager Workflow" \
  "positive control finds a known workflow heading"
not_contains ".agent/skills/km-workflow/SKILL.md" "__KM_TEST_NEGATIVE_BAIT__" \
  "negative control rejects an absent sentinel"

workflow_files=(
  ".agent/skills/km-workflow/SKILL.md"
  "skills/km-workflow.md"
)

for file in "${workflow_files[@]}"; do
  save_anchor="save_note("
  if ! grep -Fq -- "$save_anchor" "$file"; then
    save_anchor="## Phase 5: 내보내기 실행"
  fi
  contains "$file" "target_root" "$file resolves an explicit target_root"
  contains "$file" "VAULT-STRUCTURE.md" "$file pre-reads VAULT-STRUCTURE.md"
  contains "$file" "MOC-Map.md" "$file pre-reads MOC-Map.md when present"
  contains "$file" "actual_saved_path" "$file reports the observed saved path"
  contains "$file" "target_root 밖" "$file rejects target-root escape"
  appears_before "$file" "VAULT-STRUCTURE.md" "$save_anchor" \
    "$file places structure pre-read before the save call"
  appears_before "$file" "MOC-Map.md" "$save_anchor" \
    "$file places MOC pre-read before the save call"
done

storage_files=(
  ".agent/skills/km-storage-abstraction/SKILL.md"
  "skills/km-storage-abstraction.md"
)

for file in "${storage_files[@]}"; do
  contains "$file" "target_root" "$file receives target_root from the workflow"
  contains "$file" "canonical_target_root" "$file canonicalizes the target root"
  contains "$file" "actual_saved_path" "$file verifies the observed saved path"
  contains "$file" "same_path" "$file gates Obsidian tools on root equality"
  not_contains "$file" "MCP 도구가 사용 가능한 환경에서는 반드시 MCP 사용" \
    "$file no longer makes MCP availability override the target root"
done

# Executable boundary fixture: the reference containment predicate must accept
# an in-root result and reject both a direct outside result and a symlink escape.
fixture_root="$(mktemp -d)"
trap 'rm -rf -- "$fixture_root"' EXIT
project_root="$fixture_root/project"
outside_root="$fixture_root/outside"
mkdir -p "$project_root/01_행정직/사업/2026/10-기안문" "$outside_root"
touch "$project_root/VAULT-STRUCTURE.md" "$project_root/MOC-Map.md"
touch "$project_root/01_행정직/사업/2026/10-기안문/inside.md"
touch "$outside_root/outside.md"
ln -s "$outside_root" "$project_root/linked-outside"

if is_within_reference "$project_root/01_행정직/사업/2026/10-기안문/inside.md" "$project_root"; then
  pass "containment fixture accepts an actual in-project save"
else
  fail "containment fixture rejected an actual in-project save"
fi

if is_within_reference "$outside_root/outside.md" "$project_root"; then
  fail "containment fixture accepted a direct target_root escape"
else
  pass "containment fixture rejects a direct target_root escape"
fi

if is_within_reference "$project_root/linked-outside/outside.md" "$project_root"; then
  fail "containment fixture accepted a symlink target_root escape"
else
  pass "containment fixture rejects a symlink target_root escape"
fi

if (( failures > 0 )); then
  printf '\n%d project-root save contract check(s) failed.\n' "$failures" >&2
  exit 1
fi

printf '\nAll project-root save contract checks passed.\n'
