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
  echo "  Not copied (available only in a repo clone or the plugin install): scripts/configure-vault-paths.sh, scripts/_lib-config.sh, scripts/km-update.sh, scripts/km_link_gate.py, templates/start-here/." >&2
  echo "  Existing files in the project's .claude/ are overwritten only when they have the same path; other files are left as they are." >&2
  echo "  Files are staged and checked first. If anything fails before the final swap the project is left unchanged; if the swap fails or HUP/INT/TERM interrupts it, the previous files are put back (anything that could not be put back is kept beside the new files and listed)." >&2
  echo "  SIGKILL and power loss cannot run cleanup. A retry refuses retained .km-install-staging.* paths until you review and recover them; this is not a disk-durability guarantee." >&2
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
# A prior process may have died without running its EXIT trap. Do not install
# over a partly swapped project, or remove any of its surviving old copies.
# Include dangling links; do not follow them to decide whether residue exists.
for LEFTOVER in "${CLAUDE_DIR}"/.km-install-staging.*; do
  if [ -e "${LEFTOVER}" ] || [ -L "${LEFTOVER}" ]; then
    echo "Error: unfinished install at ${LEFTOVER}; the project was left as found." >&2
    echo "Review and recover the retained staged/previous copies before retrying; this installer will not delete them automatically." >&2
    exit 1
  fi
done
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
    REL="${ENTRY#"${EXPECTED_SRC}"/}"
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
SWAP_STARTED=0
cleanup_on_failure() {
  # A second Ctrl-C (or another stop signal) while the previous files are being put back would leave
  # the project half-restored: ignore further signals until cleanup is done.
  trap '' HUP INT TERM
  if [ "${SWAP_STARTED}" -eq 1 ]; then
    # The install was interrupted while the previous files were moved aside: put them back first.
    undo_swap
    if [ -n "${NOT_RESTORED}" ]; then
      echo "Error: the install was interrupted, and the previous files could not all be put back." >&2
      echo "Left for you to sort out by hand:${NOT_RESTORED}" >&2
      echo "The staged copy is kept at ${STAGE_ROOT} so nothing is lost." >&2
      return 0
    fi
    echo "The install was interrupted; the previous files were put back." >&2
  fi
  rm -rf "${STAGE_ROOT}"
  if [ "${CREATED_CLAUDE_DIR}" -eq 1 ]; then
    rmdir "${CLAUDE_DIR}" 2>/dev/null || true
  fi
}
trap cleanup_on_failure EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
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
    REL="${FILE_PATH#"${EXPECTED_SRC}"/}"
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

# --- Everything verified: swap the staged trees into place (renames only, in two phases). ---
# Phase 1 moves every directory the project already has aside (to <staging>.old-<name>).
# Phase 2 moves every staged directory, then the config file, into place.
# Nothing is deleted until both phases have finished, so a failure in either phase is undone
# by moving things back; the previous copies are removed only after everything is in place.
SWAP_DIRS="commands skills agents scripts"
ASIDE=""        # directories whose previous copy was moved aside in phase 1, in order
PLACED=""       # directories already moved into place in phase 2, in order
CONFIG_PLACED=0
ASIDE_PENDING=""  # a directory whose previous copy is being moved aside right now (phase 1)
CONFIG_PENDING=0  # set while km-config.example.json is being moved into the project
NOT_RESTORED=""

reverse_words() {
  local out="" w
  for w in "$@"; do out="${w} ${out}"; done
  printf '%s' "${out}"
}

undo_swap() {
  # Newest change first: take back what phase 2 placed, then return what phase 1 moved aside.
  # Safe to call twice: the bookkeeping is cleared at the end, so a second call does nothing.
  local d
  # Settle anything that was in flight when the install was interrupted: the rename may or may not have run.
  if [ -n "${ASIDE_PENDING}" ]; then
    if [ -e "${STAGE_ROOT}.old-${ASIDE_PENDING}" ]; then
      if [ -e "${CLAUDE_DIR}/${ASIDE_PENDING}" ]; then
        # Both copies exist: the move did not finish cleanly. Touch neither; say where the previous one is.
        NOT_RESTORED="${NOT_RESTORED} ${STAGE_ROOT}.old-${ASIDE_PENDING} (previous copy of ${ASIDE_PENDING}; ${CLAUDE_DIR}/${ASIDE_PENDING} was left as found)"
      else
        ASIDE="${ASIDE} ${ASIDE_PENDING}"   # the move ran: put it back like any recorded one
      fi
    fi                                        # otherwise the move never ran: nothing to undo
    ASIDE_PENDING=""
  fi
  if [ "${CONFIG_PENDING}" -eq 1 ]; then
    if [ -e "${PROJECT_DIR}/km-config.example.json" ]; then
      if [ -e "${STAGE_ROOT}/km-config.example.json" ]; then
        NOT_RESTORED="${NOT_RESTORED} ${PROJECT_DIR}/km-config.example.json (new file; the move did not finish cleanly, left as found)"
      else
        CONFIG_PLACED=1                       # the move ran: remove it like a recorded one
      fi
    fi
    CONFIG_PENDING=0
  fi
  if [ "${CONFIG_PLACED}" -eq 1 ]; then
    rm -f "${PROJECT_DIR}/km-config.example.json" || NOT_RESTORED="${NOT_RESTORED} ${PROJECT_DIR}/km-config.example.json (new file left in place)"
  fi
  for d in $(reverse_words ${PLACED}); do
    mv "${CLAUDE_DIR}/${d}" "${STAGE_ROOT}/${d}" || NOT_RESTORED="${NOT_RESTORED} ${CLAUDE_DIR}/${d} (new copy left in place)"
  done
  for d in $(reverse_words ${ASIDE}); do
    if [ -e "${CLAUDE_DIR}/${d}" ]; then
      # A new copy is still in the way: either the take-back above failed, or the install was
      # interrupted right after the move and before it was recorded. Try once more to take it back;
      # if that fails too, leave both copies side by side and say where the previous one is.
      if ! mv "${CLAUDE_DIR}/${d}" "${STAGE_ROOT}/${d}"; then
        NOT_RESTORED="${NOT_RESTORED} ${STAGE_ROOT}.old-${d} (previous copy of ${d}; the new copy is still at ${CLAUDE_DIR}/${d})"
        continue
      fi
    fi
    mv "${STAGE_ROOT}.old-${d}" "${CLAUDE_DIR}/${d}" || NOT_RESTORED="${NOT_RESTORED} ${STAGE_ROOT}.old-${d} (previous copy of ${d})"
  done
  PLACED=""; ASIDE=""; CONFIG_PLACED=0; SWAP_STARTED=0; ASIDE_PENDING=""; CONFIG_PENDING=0
}

swap_failed() {
  # $1 = what could not be moved
  undo_swap
  if [ -z "${NOT_RESTORED}" ]; then
    echo "Error: could not move $1 into place; the previous files were put back and the project was restored." >&2
    exit 1
  fi
  trap - EXIT
  echo "Error: could not move $1 into place, and the previous files could not all be put back." >&2
  echo "Left for you to sort out by hand:${NOT_RESTORED}" >&2
  echo "The staged copy is kept at ${STAGE_ROOT}." >&2
  exit 71
}

# Phase 1
SWAP_STARTED=1
for DIR_NAME in ${SWAP_DIRS}; do
  DEST="${CLAUDE_DIR}/${DIR_NAME}"
  if [ -d "${DEST}" ]; then
    ASIDE_PENDING="${DIR_NAME}"
    if ! mv "${DEST}" "${STAGE_ROOT}.old-${DIR_NAME}"; then
      swap_failed "the previous ${DIR_NAME}"
    fi
    ASIDE="${ASIDE} ${DIR_NAME}"
    ASIDE_PENDING=""
  fi
done

# Phase 2
for DIR_NAME in ${SWAP_DIRS}; do
  DEST="${CLAUDE_DIR}/${DIR_NAME}"
  if ! mv "${STAGE_ROOT}/${DIR_NAME}" "${DEST}"; then
    swap_failed "${DIR_NAME}"
  fi
  PLACED="${PLACED} ${DIR_NAME}"
done
if [ "${CONFIG_STAGED}" -eq 1 ]; then
  CONFIG_PENDING=1
  if ! mv "${STAGE_ROOT}/km-config.example.json" "${PROJECT_DIR}/km-config.example.json"; then
    swap_failed "km-config.example.json"
  fi
  CONFIG_PLACED=1
  CONFIG_PENDING=0
fi

# Everything is in place: only now remove the previous copies and the staging area.
trap - EXIT
for DIR_NAME in ${ASIDE}; do
  OLD="${STAGE_ROOT}.old-${DIR_NAME}"
  chmod -R u+w "${OLD}" 2>/dev/null || true
  rm -rf "${OLD}" || echo "Warning: could not remove the previous copy at ${OLD}; remove it by hand." >&2
done
rm -rf "${STAGE_ROOT}"

echo "Next: run /knowledge-manager-setup inside your project."
echo "Installed: ${SUMMARY} — all expected files present (existing files in ${CLAUDE_DIR} are kept)"
