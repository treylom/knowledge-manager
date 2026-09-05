#!/bin/bash
# install-to-project.sh — Copy knowledge-manager commands, skills, and agents into a project.
# Usage: bash scripts/install-to-project.sh <project-dir>
# Files the project already has are kept; only files with the same path are replaced.
# Nothing is written into the project until every expected file has been staged and checked;
# a symbolic link at any path this script would write through is refused.
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
  echo "  Files are staged and checked first; if anything fails, the project is left unchanged and you can simply run it again." >&2
  echo "  Symbolic links at .claude/, its commands/skills/agents/scripts directories, or any path this script writes are refused." >&2
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

# --- Symbolic-link refusal: never write through a link to somewhere outside the project. ---
refuse_symlink() {
  if [ -L "${1}" ]; then
    echo "Error: ${1} is a symbolic link (-> $(readlink "${1}")). This installer does not follow links; replace it with a real directory or file, or choose another project." >&2
    exit 1
  fi
}

refuse_symlink "${CLAUDE_DIR}"
for DIR_NAME in commands skills agents scripts; do
  refuse_symlink "${CLAUDE_DIR}/${DIR_NAME}"
done
# Every directory and file this repository ships must not be a link at the destination either.
for DIR_NAME in commands skills agents; do
  EXPECTED_SRC="${REPO_ROOT}/${DIR_NAME}"
  if [ ! -d "${EXPECTED_SRC}" ]; then
    echo "Error: source directory is missing: ${EXPECTED_SRC}" >&2
    exit 1
  fi
  while IFS= read -r -d '' ENTRY; do
    REL="${ENTRY#${EXPECTED_SRC}/}"
    refuse_symlink "${CLAUDE_DIR}/${DIR_NAME}/${REL}"
  done < <(find "${EXPECTED_SRC}" -mindepth 1 -print0)
done
refuse_symlink "${CLAUDE_DIR}/scripts/send_kakao.py"
refuse_symlink "${PROJECT_DIR}/km-config.example.json"

echo "Installing knowledge-manager into: ${PROJECT_DIR}"
echo "Files with the same name under ${CLAUDE_DIR} are replaced; anything else there is left alone."

CREATED_CLAUDE_DIR=0
if [ ! -d "${CLAUDE_DIR}" ]; then
  mkdir "${CLAUDE_DIR}"
  CREATED_CLAUDE_DIR=1
fi

# Staging area on the same filesystem as .claude/ so the final step is a rename, not a copy.
STAGE_ROOT="${CLAUDE_DIR}/.km-install-staging.$$"
cleanup_on_failure() {
  rm -rf "${STAGE_ROOT}"
  if [ "${CREATED_CLAUDE_DIR}" -eq 1 ]; then
    rmdir "${CLAUDE_DIR}" 2>/dev/null || true
  fi
}
trap cleanup_on_failure EXIT
mkdir "${STAGE_ROOT}"
echo "Staging in ${STAGE_ROOT}; the project is changed only after every expected file is verified."

SUMMARY=""

for DIR_NAME in commands skills agents; do
  SRC="${SOURCE_ROOT}/${DIR_NAME}"
  EXPECTED_SRC="${REPO_ROOT}/${DIR_NAME}"
  DEST="${CLAUDE_DIR}/${DIR_NAME}"
  STAGE="${STAGE_ROOT}/${DIR_NAME}"

  if [ ! -d "${SRC}" ]; then
    echo "Error: source directory is missing: ${SRC}" >&2
    exit 1
  fi

  mkdir -p "${STAGE}"
  # Start from what the project already has, then lay the shipped files on top.
  if [ -d "${DEST}" ]; then
    cp -R "${DEST}/." "${STAGE}/"
  fi
  cp -R "${SRC}/." "${STAGE}/"

  # Coverage check: every file this repository ships must exist in the staged tree.
  # Other files already in the project are neither counted nor removed.
  EXPECTED=0
  PRESENT=0
  while IFS= read -r -d '' FILE_PATH; do
    REL="${FILE_PATH#${EXPECTED_SRC}/}"
    EXPECTED=$(( EXPECTED + 1 ))
    if [ -f "${STAGE}/${REL}" ]; then
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
mkdir -p "${STAGE_ROOT}/scripts"
if [ -d "${CLAUDE_DIR}/scripts" ]; then
  cp -R "${CLAUDE_DIR}/scripts/." "${STAGE_ROOT}/scripts/"
fi
cp "${SOURCE_ROOT}/scripts/send_kakao.py" "${STAGE_ROOT}/scripts/send_kakao.py"
if [ ! -f "${STAGE_ROOT}/scripts/send_kakao.py" ]; then
  echo "Error: expected file is missing: ${CLAUDE_DIR}/scripts/send_kakao.py" >&2
  exit 1
fi
echo "  scripts: 1/1 expected files in place (send_kakao.py)"
SUMMARY="${SUMMARY}scripts 1/1 · "

# Config example: staged only when the project does not have one yet.
CONFIG_STAGED=0
if [ -f "${PROJECT_DIR}/km-config.example.json" ]; then
  echo "  km-config.example.json already exists — left untouched."
else
  cp "${SOURCE_ROOT}/km-config.example.json" "${STAGE_ROOT}/km-config.example.json"
  if [ ! -f "${STAGE_ROOT}/km-config.example.json" ]; then
    echo "Error: expected file is missing: ${PROJECT_DIR}/km-config.example.json" >&2
    exit 1
  fi
  CONFIG_STAGED=1
fi
SUMMARY="${SUMMARY}km-config.example.json 1"

# --- Everything verified: move the staged trees into place (renames only). ---
for DIR_NAME in commands skills agents scripts; do
  DEST="${CLAUDE_DIR}/${DIR_NAME}"
  OLD="${STAGE_ROOT}.old-${DIR_NAME}"
  if [ -d "${DEST}" ]; then
    mv "${DEST}" "${OLD}"
  fi
  if ! mv "${STAGE_ROOT}/${DIR_NAME}" "${DEST}"; then
    if [ -d "${OLD}" ]; then
      mv "${OLD}" "${DEST}"
    fi
    echo "Error: could not move ${DIR_NAME} into place; the project was restored." >&2
    exit 1
  fi
  if [ -d "${OLD}" ]; then
    chmod -R u+w "${OLD}" 2>/dev/null || true
    rm -rf "${OLD}" || echo "Warning: could not remove the previous copy at ${OLD}; remove it by hand." >&2
  fi
done
if [ "${CONFIG_STAGED}" -eq 1 ]; then
  mv "${STAGE_ROOT}/km-config.example.json" "${PROJECT_DIR}/km-config.example.json"
fi
trap - EXIT
rm -rf "${STAGE_ROOT}"

echo "Next: run /knowledge-manager setup inside your project."
echo "Installed: ${SUMMARY} — all expected files present (existing files in ${CLAUDE_DIR} are kept)"
