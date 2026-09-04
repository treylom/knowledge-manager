#!/bin/bash
# install-to-project.sh — Copy knowledge-manager commands, skills, and agents into a project.
# Usage: bash scripts/install-to-project.sh <project-dir>
# Files the project already has are kept; only files with the same path are replaced.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# KM_SOURCE_ROOT overrides only where files are copied from (used by tests); the list of files that must exist is always taken from this repository.
SOURCE_ROOT="${KM_SOURCE_ROOT:-${REPO_ROOT}}"

usage() {
  echo "Usage: bash scripts/install-to-project.sh <project-dir>" >&2
  echo "  Copies commands/, skills/, and agents/ into <project-dir>/.claude/," >&2
  echo "  plus scripts/send_kakao.py and km-config.example.json." >&2
  echo "  Existing files in the project's .claude/ are overwritten only when they have the same path; other files are left as they are." >&2
  echo "  If it stops midway, some files may already be copied — re-running is safe." >&2
}

if [ "$#" -ne 1 ]; then
  echo "Error: expected exactly one argument (the project directory)." >&2
  usage
  exit 1
fi

PROJECT_DIR="${1}"

if [ ! -d "${PROJECT_DIR}" ]; then
  echo "Error: project directory not found: ${PROJECT_DIR}" >&2
  usage
  exit 1
fi

PROJECT_DIR="$(cd "${PROJECT_DIR}" && pwd)"
CLAUDE_DIR="${PROJECT_DIR}/.claude"

echo "Installing knowledge-manager into: ${PROJECT_DIR}"
echo "Files with the same name under ${CLAUDE_DIR} are replaced; anything else there is left alone."

SUMMARY=""

for DIR_NAME in commands skills agents; do
  SRC="${SOURCE_ROOT}/${DIR_NAME}"
  EXPECTED_SRC="${REPO_ROOT}/${DIR_NAME}"
  DEST="${CLAUDE_DIR}/${DIR_NAME}"

  if [ ! -d "${SRC}" ]; then
    echo "Error: source directory is missing: ${SRC}" >&2
    exit 1
  fi

  mkdir -p "${DEST}"
  cp -R "${SRC}/." "${DEST}/"

  # Coverage check: every file this repository ships must exist at the destination.
  # Other files already in the project are neither counted nor removed.
  EXPECTED=0
  PRESENT=0
  while IFS= read -r -d '' FILE_PATH; do
    REL="${FILE_PATH#${EXPECTED_SRC}/}"
    EXPECTED=$(( EXPECTED + 1 ))
    if [ -f "${DEST}/${REL}" ]; then
      PRESENT=$(( PRESENT + 1 ))
    else
      echo "Error: expected file is missing: ${DEST}/${REL}" >&2
    fi
  done < <(find "${EXPECTED_SRC}" -type f -print0)

  if [ "${PRESENT}" -ne "${EXPECTED}" ]; then
    echo "Error: ${DIR_NAME} — ${PRESENT} of ${EXPECTED} expected files are in place." >&2
    exit 1
  fi

  echo "  ${DIR_NAME}: ${PRESENT}/${EXPECTED} expected files in place"
  SUMMARY="${SUMMARY}${DIR_NAME} ${PRESENT}/${EXPECTED} · "
done

# KakaoTalk helper — km-config.example.json points at .claude/scripts/send_kakao.py
mkdir -p "${CLAUDE_DIR}/scripts"
cp "${SOURCE_ROOT}/scripts/send_kakao.py" "${CLAUDE_DIR}/scripts/send_kakao.py"
if [ ! -f "${CLAUDE_DIR}/scripts/send_kakao.py" ]; then
  echo "Error: expected file is missing: ${CLAUDE_DIR}/scripts/send_kakao.py" >&2
  exit 1
fi
echo "  scripts: 1/1 expected files in place (send_kakao.py)"
SUMMARY="${SUMMARY}scripts 1/1 · "

if [ -f "${PROJECT_DIR}/km-config.example.json" ]; then
  echo "  km-config.example.json already exists — left untouched."
else
  cp "${SOURCE_ROOT}/km-config.example.json" "${PROJECT_DIR}/km-config.example.json"
fi
if [ ! -f "${PROJECT_DIR}/km-config.example.json" ]; then
  echo "Error: expected file is missing: ${PROJECT_DIR}/km-config.example.json" >&2
  exit 1
fi
SUMMARY="${SUMMARY}km-config.example.json 1"

echo "Next: run /knowledge-manager setup inside your project."
echo "Installed: ${SUMMARY} — all expected files present (existing files in ${CLAUDE_DIR} are kept)"
