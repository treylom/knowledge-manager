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

echo "PASS ${PASS_COUNT}/4"
if [ "${PASS_COUNT}" -ne 4 ]; then
  exit 1
fi
