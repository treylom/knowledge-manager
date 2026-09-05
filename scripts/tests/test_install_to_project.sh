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
      rel="${file_path#${REPO_ROOT}/${dir_name}/}"
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

echo "PASS ${PASS_COUNT}/8"
if [ "${PASS_COUNT}" -ne 8 ]; then
  exit 1
fi
