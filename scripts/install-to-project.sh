#!/bin/bash
# install-to-project.sh — Copy knowledge-manager commands, skills, and agents into a project.
# Usage: bash scripts/install-to-project.sh <project-dir>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  echo "Usage: bash scripts/install-to-project.sh <project-dir>" >&2
  echo "  Copies commands/, skills/, and agents/ into <project-dir>/.claude/," >&2
  echo "  plus scripts/send_kakao.py and km-config.example.json." >&2
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
echo "Files with the same name under ${CLAUDE_DIR} are overwritten."

TOTAL=0
SUMMARY=""

for DIR_NAME in commands skills agents; do
  SRC="${REPO_ROOT}/${DIR_NAME}"
  DEST="${CLAUDE_DIR}/${DIR_NAME}"

  if [ ! -d "${SRC}" ]; then
    echo "Error: source directory is missing: ${SRC}" >&2
    exit 1
  fi

  mkdir -p "${DEST}"
  cp -R "${SRC}/." "${DEST}/"

  # Check what should be there: every source file must exist at the destination.
  EXPECTED=0
  PRESENT=0
  while IFS= read -r -d '' FILE_PATH; do
    REL="${FILE_PATH#${SRC}/}"
    EXPECTED=$(( EXPECTED + 1 ))
    if [ -f "${DEST}/${REL}" ]; then
      PRESENT=$(( PRESENT + 1 ))
    else
      echo "Error: missing after copy: ${DEST}/${REL}" >&2
    fi
  done < <(find "${SRC}" -type f -print0)

  if [ "${PRESENT}" -ne "${EXPECTED}" ]; then
    echo "Error: ${DIR_NAME} — expected ${EXPECTED} files, found ${PRESENT}." >&2
    exit 1
  fi

  echo "  ${DIR_NAME}: ${PRESENT}/${EXPECTED} files"
  TOTAL=$(( TOTAL + PRESENT ))
  SUMMARY="${SUMMARY}${DIR_NAME}=${PRESENT} "
done

# KakaoTalk helper — km-config.example.json points at .claude/scripts/send_kakao.py
mkdir -p "${CLAUDE_DIR}/scripts"
cp "${REPO_ROOT}/scripts/send_kakao.py" "${CLAUDE_DIR}/scripts/send_kakao.py"
if [ ! -f "${CLAUDE_DIR}/scripts/send_kakao.py" ]; then
  echo "Error: missing after copy: ${CLAUDE_DIR}/scripts/send_kakao.py" >&2
  exit 1
fi
echo "  scripts: 1/1 files (send_kakao.py)"
TOTAL=$(( TOTAL + 1 ))
SUMMARY="${SUMMARY}scripts=1 "

CONFIG_COPIED=0
if [ -f "${PROJECT_DIR}/km-config.example.json" ]; then
  echo "  km-config.example.json already exists — left untouched."
else
  cp "${REPO_ROOT}/km-config.example.json" "${PROJECT_DIR}/km-config.example.json"
  if [ ! -f "${PROJECT_DIR}/km-config.example.json" ]; then
    echo "Error: missing after copy: ${PROJECT_DIR}/km-config.example.json" >&2
    exit 1
  fi
  CONFIG_COPIED=1
  TOTAL=$(( TOTAL + 1 ))
fi
SUMMARY="${SUMMARY}km-config.example.json=${CONFIG_COPIED}"

echo "Next: run /knowledge-manager setup inside your project."
echo "Copied ${TOTAL} files: ${SUMMARY}"
