#!/bin/bash
# test_install_to_project.sh — contract tests for scripts/install-to-project.sh
# Contract under test: after the installer runs, every file this repository ships
# must exist in the project, and files the project already had must be untouched.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INSTALLER="${REPO_ROOT}/scripts/install-to-project.sh"
GREP="/usr/bin/grep"

TMP_ROOT="$(mktemp -d)"
cleanup() {
  rm -rf "${TMP_ROOT}"
}
trap cleanup EXIT

PASS_COUNT=0

pass() {
  echo "PASS ${1}"
  PASS_COUNT=$(( PASS_COUNT + 1 ))
}

fail() {
  echo "FAIL ${1} — ${2}"
}

# The expected number of files is counted from this repository, never hard-coded.
EXPECTED_TREE="$(find "${REPO_ROOT}/commands" "${REPO_ROOT}/skills" "${REPO_ROOT}/agents" -type f | wc -l | tr -d ' ')"
EXPECTED_TOTAL=$(( EXPECTED_TREE + 2 ))  # + scripts/send_kakao.py + km-config.example.json

# Prints how many expected files are missing from the given project directory.
missing_expected() {
  local proj="${1}"
  local missing=0
  local dir_name rel file_path
  for dir_name in commands skills agents; do
    while IFS= read -r -d '' file_path; do
      rel="${file_path#"${REPO_ROOT}/${dir_name}"/}"
      if [ ! -f "${proj}/.claude/${dir_name}/${rel}" ]; then
        missing=$(( missing + 1 ))
      fi
    done < <(find "${REPO_ROOT}/${dir_name}" -type f -print0)
  done
  if [ ! -f "${proj}/.claude/scripts/send_kakao.py" ]; then
    missing=$(( missing + 1 ))
  fi
  if [ ! -f "${proj}/km-config.example.json" ]; then
    missing=$(( missing + 1 ))
  fi
  echo "${missing}"
}

# T1 — empty project: exits 0 and every expected file is in place.
T1_PROJ="${TMP_ROOT}/t1-project"
mkdir -p "${T1_PROJ}"
set +e
T1_OUT="$(bash "${INSTALLER}" "${T1_PROJ}" 2>&1)"
T1_RC=$?
set -e
T1_MISSING="$(missing_expected "${T1_PROJ}")"
if [ "${T1_RC}" -eq 0 ] && [ "${T1_MISSING}" -eq 0 ]; then
  pass "T1"
else
  fail "T1" "exit=${T1_RC} missing=${T1_MISSING} of ${EXPECTED_TOTAL} expected"
fi

# T2 — a file the project already had survives, and the run still reports success once.
T2_PROJ="${TMP_ROOT}/t2-project"
mkdir -p "${T2_PROJ}/.claude/commands"
printf 'keep me\n' > "${T2_PROJ}/.claude/commands/my-own.md"
set +e
T2_OUT="$(bash "${INSTALLER}" "${T2_PROJ}" 2>&1)"
T2_RC=$?
set -e
T2_KEPT="$(cat "${T2_PROJ}/.claude/commands/my-own.md")"
T2_BANNER="$(printf '%s\n' "${T2_OUT}" | ${GREP} -o 'all expected files present' | wc -l | tr -d ' ' || true)"
T2_MISSING="$(missing_expected "${T2_PROJ}")"
# Running it again on the same project stays green and still counts the config file as present.
set +e
T2_OUT_AGAIN="$(bash "${INSTALLER}" "${T2_PROJ}" 2>&1)"
T2_RC_AGAIN=$?
set -e
T2_CONFIG_AGAIN="$(printf '%s\n' "${T2_OUT_AGAIN}" | ${GREP} -o 'km-config.example.json 1' | wc -l | tr -d ' ' || true)"
T2_KEPT_AGAIN="$(cat "${T2_PROJ}/.claude/commands/my-own.md")"
if [ "${T2_RC}" -eq 0 ] && [ "${T2_KEPT}" = "keep me" ] && [ "${T2_BANNER}" -eq 1 ] \
   && [ "${T2_MISSING}" -eq 0 ] && [ "${T2_RC_AGAIN}" -eq 0 ] \
   && [ "${T2_CONFIG_AGAIN}" -eq 1 ] && [ "${T2_KEPT_AGAIN}" = "keep me" ]; then
  pass "T2"
else
  fail "T2" "exit=${T2_RC}/${T2_RC_AGAIN} kept='${T2_KEPT}'/'${T2_KEPT_AGAIN}' success_line=${T2_BANNER} missing=${T2_MISSING} config_on_rerun=${T2_CONFIG_AGAIN}"
fi

# T3 — no argument: exits 1.
set +e
T3_OUT="$(bash "${INSTALLER}" 2>&1)"
T3_RC=$?
set -e
T3_USAGE="$(printf '%s\n' "${T3_OUT}" | ${GREP} -o 'Usage: bash scripts/install-to-project.sh' | wc -l | tr -d ' ' || true)"
if [ "${T3_RC}" -eq 1 ] && [ "${T3_USAGE}" -ge 1 ]; then
  pass "T3"
else
  fail "T3" "exit=${T3_RC} usage_line=${T3_USAGE}"
fi

# T4 — a source copy that lost one shipped file: exits 1 and names that file.
T4_SRC="${TMP_ROOT}/t4-source"
T4_PROJ="${TMP_ROOT}/t4-project"
mkdir -p "${T4_SRC}" "${T4_PROJ}"
( cd "${REPO_ROOT}" && cp -R commands skills agents scripts km-config.example.json "${T4_SRC}/" )
rm -f "${T4_SRC}/commands/search.md"
set +e
T4_OUT="$(KM_SOURCE_ROOT="${T4_SRC}" bash "${INSTALLER}" "${T4_PROJ}" 2>&1)"
T4_RC=$?
set -e
T4_HITS="$(printf '%s\n' "${T4_OUT}" | ${GREP} -o 'commands/search\.md' | wc -l | tr -d ' ' || true)"
T4_REPO_INTACT=0
if [ -f "${REPO_ROOT}/commands/search.md" ]; then
  T4_REPO_INTACT=1
fi
if [ "${T4_RC}" -eq 1 ] && [ "${T4_HITS}" -eq 1 ] && [ "${T4_REPO_INTACT}" -eq 1 ]; then
  pass "T4"
else
  fail "T4" "exit=${T4_RC} named_the_missing_file=${T4_HITS} repository_intact=${T4_REPO_INTACT}"
fi

# T5 — a source copy that lost one shipped file in the second directory: exits 1 and the project is unchanged.
T5_SRC="${TMP_ROOT}/t5-source"
T5_PROJ="${TMP_ROOT}/t5-project"
mkdir -p "${T5_SRC}" "${T5_PROJ}/.claude/commands"
printf 'keep me\n' > "${T5_PROJ}/.claude/commands/my-own.md"
( cd "${REPO_ROOT}" && cp -R commands skills agents scripts km-config.example.json "${T5_SRC}/" )
rm -f "${T5_SRC}/skills/km-workflow.md"
set +e
T5_OUT="$(KM_SOURCE_ROOT="${T5_SRC}" bash "${INSTALLER}" "${T5_PROJ}" 2>&1)"
T5_RC=$?
set -e
T5_HITS="$(printf '%s\n' "${T5_OUT}" | ${GREP} -o 'skills/km-workflow\.md' | wc -l | tr -d ' ' || true)"
T5_FILES="$(find "${T5_PROJ}/.claude" -type f | wc -l | tr -d ' ')"
T5_KEPT="$(cat "${T5_PROJ}/.claude/commands/my-own.md")"
T5_STAGING="$(find "${T5_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
T5_NO_CONFIG=0
if [ ! -e "${T5_PROJ}/km-config.example.json" ]; then
  T5_NO_CONFIG=1
fi
T5_REPO_INTACT=0
if [ -f "${REPO_ROOT}/skills/km-workflow.md" ]; then
  T5_REPO_INTACT=1
fi
if [ "${T5_RC}" -eq 1 ] && [ "${T5_HITS}" -eq 1 ] && [ "${T5_FILES}" -eq 1 ] \
   && [ "${T5_KEPT}" = "keep me" ] && [ "${T5_STAGING}" -eq 0 ] \
   && [ "${T5_NO_CONFIG}" -eq 1 ] && [ "${T5_REPO_INTACT}" -eq 1 ]; then
  pass "T5"
else
  fail "T5" "exit=${T5_RC} named_the_missing_file=${T5_HITS} project_files=${T5_FILES} kept='${T5_KEPT}' staging_left=${T5_STAGING} no_config=${T5_NO_CONFIG} repository_intact=${T5_REPO_INTACT}"
fi

# T6 — .claude/skills is a symbolic link to a directory outside the project: exits 1, nothing is written outside, the link is kept.
T6_PROJ="${TMP_ROOT}/t6-project"
T6_OUT_DIR="${TMP_ROOT}/t6-outside"
mkdir -p "${T6_PROJ}/.claude" "${T6_OUT_DIR}"
ln -s "${T6_OUT_DIR}" "${T6_PROJ}/.claude/skills"
set +e
T6_OUT="$(bash "${INSTALLER}" "${T6_PROJ}" 2>&1)"
T6_RC=$?
set -e
T6_NAMED="$(printf '%s\n' "${T6_OUT}" | ${GREP} -o '\.claude/skills' | wc -l | tr -d ' ' || true)"
T6_LINK_MSG="$(printf '%s\n' "${T6_OUT}" | ${GREP} -o 'symbolic link' | wc -l | tr -d ' ' || true)"
T6_OUTSIDE="$(find "${T6_OUT_DIR}" -type f | wc -l | tr -d ' ')"
T6_INSIDE="$(find "${T6_PROJ}/.claude" -type f | wc -l | tr -d ' ')"
T6_LINK_KEPT=0
if [ -L "${T6_PROJ}/.claude/skills" ]; then
  T6_LINK_KEPT=1
fi
T6_STAGING="$(find "${T6_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
if [ "${T6_RC}" -eq 1 ] && [ "${T6_NAMED}" -ge 1 ] && [ "${T6_LINK_MSG}" -ge 1 ] \
   && [ "${T6_OUTSIDE}" -eq 0 ] && [ "${T6_INSIDE}" -eq 0 ] \
   && [ "${T6_LINK_KEPT}" -eq 1 ] && [ "${T6_STAGING}" -eq 0 ]; then
  pass "T6"
else
  fail "T6" "exit=${T6_RC} named_the_link=${T6_NAMED} link_message=${T6_LINK_MSG} files_outside=${T6_OUTSIDE} files_inside=${T6_INSIDE} link_kept=${T6_LINK_KEPT} staging_left=${T6_STAGING}"
fi

# T7 — .claude itself is a symbolic link to a directory outside the project: exits 1, nothing is written outside, the link is kept.
T7_PROJ="${TMP_ROOT}/t7-project"
T7_OUT_DIR="${TMP_ROOT}/t7-outside"
mkdir -p "${T7_PROJ}" "${T7_OUT_DIR}"
ln -s "${T7_OUT_DIR}" "${T7_PROJ}/.claude"
set +e
T7_OUT="$(bash "${INSTALLER}" "${T7_PROJ}" 2>&1)"
T7_RC=$?
set -e
T7_NAMED="$(printf '%s\n' "${T7_OUT}" | ${GREP} -F -o "${T7_PROJ}/.claude is a symbolic link" | wc -l | tr -d ' ' || true)"
T7_OUTSIDE="$(find "${T7_OUT_DIR}" -type f | wc -l | tr -d ' ')"
T7_LINK_KEPT=0
if [ -L "${T7_PROJ}/.claude" ]; then
  T7_LINK_KEPT=1
fi
if [ "${T7_RC}" -eq 1 ] && [ "${T7_NAMED}" -eq 1 ] && [ "${T7_OUTSIDE}" -eq 0 ] && [ "${T7_LINK_KEPT}" -eq 1 ]; then
  pass "T7"
else
  fail "T7" "exit=${T7_RC} named_the_link=${T7_NAMED} files_outside=${T7_OUTSIDE} link_kept=${T7_LINK_KEPT}"
fi

# T8 — a single file (.claude/commands/search.md) is a symbolic link to a file outside the project: exits 1, the outside file is untouched.
T8_PROJ="${TMP_ROOT}/t8-project"
T8_OUT_DIR="${TMP_ROOT}/t8-outside"
mkdir -p "${T8_PROJ}/.claude/commands" "${T8_OUT_DIR}"
printf 'outside\n' > "${T8_OUT_DIR}/search.md"
ln -s "${T8_OUT_DIR}/search.md" "${T8_PROJ}/.claude/commands/search.md"
set +e
T8_OUT="$(bash "${INSTALLER}" "${T8_PROJ}" 2>&1)"
T8_RC=$?
set -e
T8_NAMED="$(printf '%s\n' "${T8_OUT}" | ${GREP} -o 'commands/search\.md' | wc -l | tr -d ' ' || true)"
T8_LINK_MSG="$(printf '%s\n' "${T8_OUT}" | ${GREP} -o 'symbolic link' | wc -l | tr -d ' ' || true)"
T8_OUTSIDE_CONTENT="$(cat "${T8_OUT_DIR}/search.md")"
T8_INSIDE="$(find "${T8_PROJ}/.claude" -type f | wc -l | tr -d ' ')"
T8_STAGING="$(find "${T8_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
if [ "${T8_RC}" -eq 1 ] && [ "${T8_NAMED}" -ge 1 ] && [ "${T8_LINK_MSG}" -ge 1 ] \
   && [ "${T8_OUTSIDE_CONTENT}" = "outside" ] && [ "${T8_INSIDE}" -eq 0 ] && [ "${T8_STAGING}" -eq 0 ]; then
  pass "T8"
else
  fail "T8" "exit=${T8_RC} named_the_link=${T8_NAMED} link_message=${T8_LINK_MSG} outside_content='${T8_OUTSIDE_CONTENT}' files_inside=${T8_INSIDE} staging_left=${T8_STAGING}"
fi

# Failure injection for T9–T11: a fake `mv` first in PATH that refuses one specific rename
# (the same method as the PR #7 review reproduction) and otherwise defers to /bin/mv.
FAKE_BIN="${TMP_ROOT}/fake-bin"
mkdir -p "${FAKE_BIN}"
cat > "${FAKE_BIN}/mv" <<'FAKE'
#!/bin/bash
case "${KM_TEST_FAIL_AT:-}:$1" in
  skills:*/.km-install-staging.*/skills|undo:*/.km-install-staging.*/skills) echo "TEST_INJECTED_RENAME_FAILURE" >&2; exit 71 ;;
  config:*/.km-install-staging.*/km-config.example.json) echo "TEST_INJECTED_RENAME_FAILURE" >&2; exit 71 ;;
  undo:*/.km-install-staging.*.old-commands) echo "TEST_INJECTED_RENAME_FAILURE" >&2; exit 71 ;;
esac
# T12–T13 need both arguments: "interrupt" carries out the rename that places skills, then sends the installer SIGTERM;
# "interrupt2" also fires on the restore of skills, so the installer takes a second SIGTERM while the previous files are being put back (T14).
# "nested" refuses the config rename and then refuses to take the new skills back.
case "${KM_TEST_FAIL_AT:-}:$1:${2:-}" in
  interrupt:*/.km-install-staging.*/skills:*/.claude/skills) /bin/mv "$@"; kill -TERM "${PPID}"; exit 0 ;;
  interrupt2:*:*/.claude/skills) /bin/mv "$@"; kill -TERM "${PPID}"; exit 0 ;;
  nested:*/.km-install-staging.*/km-config.example.json:*) echo "TEST_INJECTED_RENAME_FAILURE" >&2; exit 71 ;;
  nested:*/.claude/skills:*/.km-install-staging.*/skills) echo "TEST_INJECTED_RENAME_FAILURE" >&2; exit 71 ;;
  aside:*/.claude/commands:*/.km-install-staging.*.old-commands) /bin/mv "$@"; kill -TERM "${PPID}"; exit 0 ;;
  configint:*/.km-install-staging.*/km-config.example.json:*/km-config.example.json) /bin/mv "$@"; kill -TERM "${PPID}"; exit 0 ;;
esac
exec /bin/mv "$@"
FAKE
chmod +x "${FAKE_BIN}/mv"

make_swap_fixture() {
  # $1 = project dir. A project that already has all four directories plus one file of its own in two of them.
  mkdir -p "$1/.claude/commands" "$1/.claude/skills" "$1/.claude/agents" "$1/.claude/scripts"
  printf 'ORIGINAL_COMMAND\n' > "$1/.claude/commands/search.md"
  printf 'ORIGINAL_SKILL\n' > "$1/.claude/skills/my-private.md"
}

# T9 — the rename of skills fails after commands was already swapped: exits 1, says the project was restored, and it is.
T9_PROJ="${TMP_ROOT}/t9-project"
make_swap_fixture "${T9_PROJ}"
set +e
T9_OUT="$(PATH="${FAKE_BIN}:${PATH}" KM_TEST_FAIL_AT=skills bash "${INSTALLER}" "${T9_PROJ}" 2>&1)"
T9_RC=$?
set -e
T9_INJECTED="$(printf '%s\n' "${T9_OUT}" | ${GREP} -c 'TEST_INJECTED_RENAME_FAILURE' || true)"
T9_RESTORED_MSG="$(printf '%s\n' "${T9_OUT}" | ${GREP} -c 'the project was restored' || true)"
T9_CMD="$(cat "${T9_PROJ}/.claude/commands/search.md")"
T9_SKILL="$(cat "${T9_PROJ}/.claude/skills/my-private.md")"
T9_NEW_SKILL=0; [ -e "${T9_PROJ}/.claude/skills/km-workflow.md" ] && T9_NEW_SKILL=1
T9_CONFIG=0; [ -e "${T9_PROJ}/km-config.example.json" ] && T9_CONFIG=1
T9_RESIDUE="$(find "${T9_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
if [ "${T9_RC}" -eq 1 ] && [ "${T9_INJECTED}" -eq 1 ] && [ "${T9_RESTORED_MSG}" -eq 1 ] \
   && [ "${T9_CMD}" = "ORIGINAL_COMMAND" ] && [ "${T9_SKILL}" = "ORIGINAL_SKILL" ] \
   && [ "${T9_NEW_SKILL}" -eq 0 ] && [ "${T9_CONFIG}" -eq 0 ] && [ "${T9_RESIDUE}" -eq 0 ]; then
  pass "T9"
else
  fail "T9" "exit=${T9_RC} injected=${T9_INJECTED} restored_message=${T9_RESTORED_MSG} command='${T9_CMD}' skill='${T9_SKILL}' new_skill_present=${T9_NEW_SKILL} config_present=${T9_CONFIG} residue=${T9_RESIDUE}"
fi

# T10 — the last rename (km-config.example.json) fails after all four directories were swapped: exits 1 and the project is restored.
T10_PROJ="${TMP_ROOT}/t10-project"
make_swap_fixture "${T10_PROJ}"
set +e
T10_OUT="$(PATH="${FAKE_BIN}:${PATH}" KM_TEST_FAIL_AT=config bash "${INSTALLER}" "${T10_PROJ}" 2>&1)"
T10_RC=$?
set -e
T10_INJECTED="$(printf '%s\n' "${T10_OUT}" | ${GREP} -c 'TEST_INJECTED_RENAME_FAILURE' || true)"
T10_RESTORED_MSG="$(printf '%s\n' "${T10_OUT}" | ${GREP} -c 'the project was restored' || true)"
T10_CMD="$(cat "${T10_PROJ}/.claude/commands/search.md")"
T10_SKILL="$(cat "${T10_PROJ}/.claude/skills/my-private.md")"
T10_NEW_SKILL=0; [ -e "${T10_PROJ}/.claude/skills/km-workflow.md" ] && T10_NEW_SKILL=1
T10_CONFIG=0; [ -e "${T10_PROJ}/km-config.example.json" ] && T10_CONFIG=1
T10_RESIDUE="$(find "${T10_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
if [ "${T10_RC}" -eq 1 ] && [ "${T10_INJECTED}" -eq 1 ] && [ "${T10_RESTORED_MSG}" -eq 1 ] \
   && [ "${T10_CMD}" = "ORIGINAL_COMMAND" ] && [ "${T10_SKILL}" = "ORIGINAL_SKILL" ] \
   && [ "${T10_NEW_SKILL}" -eq 0 ] && [ "${T10_CONFIG}" -eq 0 ] && [ "${T10_RESIDUE}" -eq 0 ]; then
  pass "T10"
else
  fail "T10" "exit=${T10_RC} injected=${T10_INJECTED} restored_message=${T10_RESTORED_MSG} command='${T10_CMD}' skill='${T10_SKILL}' new_skill_present=${T10_NEW_SKILL} config_present=${T10_CONFIG} residue=${T10_RESIDUE}"
fi

# T11 — the rename of skills fails AND the previous commands cannot be put back: exits 71, does not claim a restore, names the copy it left behind, and that copy still holds the original file.
T11_PROJ="${TMP_ROOT}/t11-project"
make_swap_fixture "${T11_PROJ}"
set +e
T11_OUT="$(PATH="${FAKE_BIN}:${PATH}" KM_TEST_FAIL_AT=undo bash "${INSTALLER}" "${T11_PROJ}" 2>&1)"
T11_RC=$?
set -e
T11_RESTORED_MSG="$(printf '%s\n' "${T11_OUT}" | ${GREP} -c 'the project was restored' || true)"
T11_HONEST_MSG="$(printf '%s\n' "${T11_OUT}" | ${GREP} -c 'could not all be put back' || true)"
T11_NAMED_OLD="$(printf '%s\n' "${T11_OUT}" | ${GREP} -c 'old-commands' || true)"
T11_OLD_DIR="$(find "${T11_PROJ}/.claude" -maxdepth 1 -name '.km-install-staging.*.old-commands' | head -n 1)"
T11_OLD_CONTENT=""; [ -n "${T11_OLD_DIR}" ] && [ -f "${T11_OLD_DIR}/search.md" ] && T11_OLD_CONTENT="$(cat "${T11_OLD_DIR}/search.md")"
T11_CMD_DIR=0; [ -e "${T11_PROJ}/.claude/commands" ] && T11_CMD_DIR=1
T11_SKILL="$(cat "${T11_PROJ}/.claude/skills/my-private.md" 2>/dev/null || echo MISSING)"
if [ "${T11_RC}" -eq 71 ] && [ "${T11_RESTORED_MSG}" -eq 0 ] && [ "${T11_HONEST_MSG}" -eq 1 ] && [ "${T11_NAMED_OLD}" -ge 1 ] \
   && [ "${T11_OLD_CONTENT}" = "ORIGINAL_COMMAND" ] && [ "${T11_CMD_DIR}" -eq 0 ] && [ "${T11_SKILL}" = "ORIGINAL_SKILL" ]; then
  pass "T11"
else
  fail "T11" "exit=${T11_RC} restored_message=${T11_RESTORED_MSG} honest_message=${T11_HONEST_MSG} named_old=${T11_NAMED_OLD} old_content='${T11_OLD_CONTENT}' commands_dir_present=${T11_CMD_DIR} skill='${T11_SKILL}'"
fi

# T12 — the installer is interrupted (SIGTERM) right after the new skills were moved into place: exits 143, says the previous files were put back, and they are; nothing is left behind.
T12_PROJ="${TMP_ROOT}/t12-project"
make_swap_fixture "${T12_PROJ}"
set +e
T12_OUT="$(PATH="${FAKE_BIN}:${PATH}" KM_TEST_FAIL_AT=interrupt bash "${INSTALLER}" "${T12_PROJ}" 2>&1)"
T12_RC=$?
set -e
T12_PUT_BACK_MSG="$(printf '%s\n' "${T12_OUT}" | ${GREP} -c 'the previous files were put back' || true)"
T12_CMD="$(cat "${T12_PROJ}/.claude/commands/search.md" 2>/dev/null || echo MISSING)"
T12_SKILL="$(cat "${T12_PROJ}/.claude/skills/my-private.md" 2>/dev/null || echo MISSING)"
T12_AGENTS=0; [ -d "${T12_PROJ}/.claude/agents" ] && T12_AGENTS=1
T12_SCRIPTS=0; [ -d "${T12_PROJ}/.claude/scripts" ] && T12_SCRIPTS=1
T12_RESIDUE="$(find "${T12_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
if [ "${T12_RC}" -eq 143 ] && [ "${T12_PUT_BACK_MSG}" -eq 1 ] \
   && [ "${T12_CMD}" = "ORIGINAL_COMMAND" ] && [ "${T12_SKILL}" = "ORIGINAL_SKILL" ] \
   && [ "${T12_AGENTS}" -eq 1 ] && [ "${T12_SCRIPTS}" -eq 1 ] && [ "${T12_RESIDUE}" -eq 0 ]; then
  pass "T12"
else
  fail "T12" "exit=${T12_RC} put_back_message=${T12_PUT_BACK_MSG} command='${T12_CMD}' skill='${T12_SKILL}' agents_dir=${T12_AGENTS} scripts_dir=${T12_SCRIPTS} residue=${T12_RESIDUE}"
fi

# T13 — the config rename fails AND the new skills cannot be taken back: exits 71, leaves the new skills in place, keeps the previous skills beside them (never inside them), and says where.
T13_PROJ="${TMP_ROOT}/t13-project"
make_swap_fixture "${T13_PROJ}"
set +e
T13_OUT="$(PATH="${FAKE_BIN}:${PATH}" KM_TEST_FAIL_AT=nested bash "${INSTALLER}" "${T13_PROJ}" 2>&1)"
T13_RC=$?
set -e
T13_RESTORED_MSG="$(printf '%s\n' "${T13_OUT}" | ${GREP} -c 'restored' || true)"
T13_STILL_AT_MSG="$(printf '%s\n' "${T13_OUT}" | ${GREP} -c 'the new copy is still at' || true)"
T13_NEW_SKILL=0; [ -e "${T13_PROJ}/.claude/skills/km-workflow.md" ] && T13_NEW_SKILL=1
# The new skills copy carries the project's own top-level my-private.md (staging starts from the project's files); nesting means a copy one level deeper.
T13_NESTED="$(find "${T13_PROJ}/.claude/skills" -mindepth 2 -name my-private.md | wc -l | tr -d ' ')"
T13_BESIDE="$(find "${T13_PROJ}/.claude" -maxdepth 2 -path '*/.claude/.km-install-staging.*.old-skills/my-private.md' | wc -l | tr -d ' ')"
if [ "${T13_RC}" -eq 71 ] && [ "${T13_RESTORED_MSG}" -eq 0 ] && [ "${T13_STILL_AT_MSG}" -eq 1 ] \
   && [ "${T13_NEW_SKILL}" -eq 1 ] && [ "${T13_NESTED}" -eq 0 ] && [ "${T13_BESIDE}" -eq 1 ]; then
  pass "T13"
else
  fail "T13" "exit=${T13_RC} restored_message=${T13_RESTORED_MSG} still_at_message=${T13_STILL_AT_MSG} new_skill_present=${T13_NEW_SKILL} nested_old_file=${T13_NESTED} old_file_beside=${T13_BESIDE}"
fi

# T14 — a second SIGTERM arrives while the previous files are being put back: same outcome as T12 (the restore is not interrupted).
T14_PROJ="${TMP_ROOT}/t14-project"
make_swap_fixture "${T14_PROJ}"
set +e
T14_OUT="$(PATH="${FAKE_BIN}:${PATH}" KM_TEST_FAIL_AT=interrupt2 bash "${INSTALLER}" "${T14_PROJ}" 2>&1)"
T14_RC=$?
set -e
T14_PUT_BACK_MSG="$(printf '%s\n' "${T14_OUT}" | ${GREP} -c 'the previous files were put back' || true)"
T14_CMD="$(cat "${T14_PROJ}/.claude/commands/search.md" 2>/dev/null || echo MISSING)"
T14_SKILL="$(cat "${T14_PROJ}/.claude/skills/my-private.md" 2>/dev/null || echo MISSING)"
T14_AGENTS=0; [ -d "${T14_PROJ}/.claude/agents" ] && T14_AGENTS=1
T14_SCRIPTS=0; [ -d "${T14_PROJ}/.claude/scripts" ] && T14_SCRIPTS=1
T14_RESIDUE="$(find "${T14_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
if [ "${T14_RC}" -eq 143 ] && [ "${T14_PUT_BACK_MSG}" -eq 1 ] \
   && [ "${T14_CMD}" = "ORIGINAL_COMMAND" ] && [ "${T14_SKILL}" = "ORIGINAL_SKILL" ] \
   && [ "${T14_AGENTS}" -eq 1 ] && [ "${T14_SCRIPTS}" -eq 1 ] && [ "${T14_RESIDUE}" -eq 0 ]; then
  pass "T14"
else
  fail "T14" "exit=${T14_RC} put_back_message=${T14_PUT_BACK_MSG} command='${T14_CMD}' skill='${T14_SKILL}' agents_dir=${T14_AGENTS} scripts_dir=${T14_SCRIPTS} residue=${T14_RESIDUE}"
fi

# T15 — the installer is interrupted (SIGTERM) right after the previous commands were moved aside in phase 1, before that move was recorded: exits 143, says the previous files were put back, and they are; nothing is left behind.
T15_PROJ="${TMP_ROOT}/t15-project"
make_swap_fixture "${T15_PROJ}"
set +e
T15_OUT="$(PATH="${FAKE_BIN}:${PATH}" KM_TEST_FAIL_AT=aside bash "${INSTALLER}" "${T15_PROJ}" 2>&1)"
T15_RC=$?
set -e
T15_PUT_BACK_MSG="$(printf '%s\n' "${T15_OUT}" | ${GREP} -c 'the previous files were put back' || true)"
T15_HONEST_MSG="$(printf '%s\n' "${T15_OUT}" | ${GREP} -c 'could not all be put back' || true)"
T15_CMD="$(cat "${T15_PROJ}/.claude/commands/search.md" 2>/dev/null || echo MISSING)"
T15_SKILL="$(cat "${T15_PROJ}/.claude/skills/my-private.md" 2>/dev/null || echo MISSING)"
T15_RESIDUE="$(find "${T15_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
if [ "${T15_RC}" -eq 143 ] && [ "${T15_PUT_BACK_MSG}" -eq 1 ] && [ "${T15_HONEST_MSG}" -eq 0 ] \
   && [ "${T15_CMD}" = "ORIGINAL_COMMAND" ] && [ "${T15_SKILL}" = "ORIGINAL_SKILL" ] \
   && [ "${T15_RESIDUE}" -eq 0 ]; then
  pass "T15"
else
  fail "T15" "exit=${T15_RC} put_back_message=${T15_PUT_BACK_MSG} honest_message=${T15_HONEST_MSG} command='${T15_CMD}' skill='${T15_SKILL}' residue=${T15_RESIDUE}"
fi

# T16 — the installer is interrupted (SIGTERM) right after km-config.example.json was moved into the project, before that move was recorded: exits 143, the new config file is gone again, the previous files are back, and nothing is left behind.
T16_PROJ="${TMP_ROOT}/t16-project"
make_swap_fixture "${T16_PROJ}"
set +e
T16_OUT="$(PATH="${FAKE_BIN}:${PATH}" KM_TEST_FAIL_AT=configint bash "${INSTALLER}" "${T16_PROJ}" 2>&1)"
T16_RC=$?
set -e
T16_PUT_BACK_MSG="$(printf '%s\n' "${T16_OUT}" | ${GREP} -c 'the previous files were put back' || true)"
T16_CONFIG=0; [ -e "${T16_PROJ}/km-config.example.json" ] && T16_CONFIG=1
T16_CMD="$(cat "${T16_PROJ}/.claude/commands/search.md" 2>/dev/null || echo MISSING)"
T16_SKILL="$(cat "${T16_PROJ}/.claude/skills/my-private.md" 2>/dev/null || echo MISSING)"
T16_NEW_SKILL=0; [ -e "${T16_PROJ}/.claude/skills/km-workflow.md" ] && T16_NEW_SKILL=1
T16_RESIDUE="$(find "${T16_PROJ}" -name '.km-install-*' | wc -l | tr -d ' ')"
if [ "${T16_RC}" -eq 143 ] && [ "${T16_PUT_BACK_MSG}" -eq 1 ] && [ "${T16_CONFIG}" -eq 0 ] \
   && [ "${T16_CMD}" = "ORIGINAL_COMMAND" ] && [ "${T16_SKILL}" = "ORIGINAL_SKILL" ] \
   && [ "${T16_NEW_SKILL}" -eq 0 ] && [ "${T16_RESIDUE}" -eq 0 ]; then
  pass "T16"
else
  fail "T16" "exit=${T16_RC} put_back_message=${T16_PUT_BACK_MSG} config_present=${T16_CONFIG} command='${T16_CMD}' skill='${T16_SKILL}' new_skill_present=${T16_NEW_SKILL} residue=${T16_RESIDUE}"
fi

echo "PASS ${PASS_COUNT}/16"
if [ "${PASS_COUNT}" -ne 16 ]; then
  exit 1
fi
