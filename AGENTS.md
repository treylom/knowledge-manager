# AGENTS.md — Generic AI agent contract

> This file is the vendor-neutral version of `CLAUDE.md`. If you are an AI coding assistant other than Claude Code (e.g. Codex, Cursor, Gemini, Antigravity, OpenCode, an autonomous agent framework, or a future model), read this file **before** you modify anything in this repository.

---

## Repository Identity

- **Name**: knowledge-manager
- **Type**: Claude Code / Antigravity skill + agent + command distribution repo
- **Primary purpose**: Ingest content (web, PDF, YouTube, social, chat logs) and file it as structured notes in the user's Obsidian vault (or Notion, or local markdown).
- **Deployment model**: Users `git clone` this repo, run a setup wizard, and the wizard rewrites placeholder tokens in every skill file with the user's personal paths.
- **Key invariant**: The committed source tree is **portable**. It contains `{{PLACEHOLDER}}` tokens, never one user's hardcoded paths.

---

## Read First

Read these files **in this order** before making any edit:

1. [`CLAUDE.md`](CLAUDE.md) — the same contract written for Claude Code, with a worked example of source-vs-substituted file forms.
2. [`README.md`](README.md) — end-user documentation; see the `## Installation & Configuration` section for how the placeholder system is presented to users.
3. [`docs/vault-path-configuration.md`](docs/vault-path-configuration.md) — full technical reference: config schema, substitution algorithm, skip-worktree mechanism, troubleshooting.

If you are unable to read those files for any reason, stop and ask the user to paste their contents rather than guessing.

---

## Placeholder Contract (CRITICAL)

The following 5 tokens appear verbatim in committed source files and **must be preserved** whenever you edit a skill, agent, or command file:

| Token | Semantic meaning |
|---|---|
| `{{VAULT_PATH}}` | Absolute path to the user's Obsidian vault directory |
| `{{VAULT_NAME}}` | Basename of `{{VAULT_PATH}}` (the vault folder name, used by Obsidian CLI `--vault` argument) |
| `{{OBSIDIAN_CLI}}` | Absolute path to the Obsidian CLI executable (may be empty string if not installed) |
| `{{ZETTELKASTEN_ROOT}}` | Vault-relative path to the Zettelkasten root folder (default: `Zettelkasten`) |
| `{{RESEARCH_ROOT}}` | Vault-relative path to the research/MOC root folder (default: `Research`) |

### Do

- Write placeholders in their exact `{{DOUBLE_BRACE_UPPERCASE}}` form.
- Compose placeholders for nested paths: `{{VAULT_PATH}}/{{ZETTELKASTEN_ROOT}}/AI/note.md`.
- Use `{{VAULT_NAME}}` when the Obsidian CLI needs a vault name rather than a path.
- Leave the one intentional exception in `skills/km-storage-abstraction.md` alone (it teaches users not to prefix paths with the vault name, using the generic string `YourVaultName`).

### Do not

- Do **not** hardcode any personal absolute path (any path containing a specific username, user home, or real vault name). Forbidden patterns include but are not limited to:
  - `/home/<anyname>/...`
  - `/Users/<anyname>/...`
  - `C:\Users\<anyname>\...`
  - `/mnt/c/Users/<anyname>/...`
- Do **not** rename, shorten, or invent new placeholder tokens. The set of 5 is fixed; adding new ones requires a design doc change and coordinated edits in `scripts/configure-vault-paths.sh`.
- Do **not** remove the `{{...}}` braces "because the local file already has the substituted value." That substituted value is a skip-worktree artifact; the committed HEAD still has the placeholder.
- Do **not** commit `km-config.json` (the user's personal config). It is gitignored.

---

## Editing Workflow

For any change that touches `skills/`, `agents/`, `commands/`, or `.claude/`:

1. **Identify the target file(s).** If the file has a mirror under `.claude/`, both must be edited together (see File Synchronization Invariant below).

2. **Read the committed form, not the working-tree form**, if you suspect skip-worktree may be active:
   ```bash
   git ls-files -v <file> | head -1   # leading 'S' = skip-worktree on
   git show HEAD:<file>               # pristine committed content
   ```

3. **Make your edit in placeholder form.** If you need to reference the vault root, write `{{VAULT_PATH}}`. If you need a file under Zettelkasten, write `{{VAULT_PATH}}/{{ZETTELKASTEN_ROOT}}/...`.

4. **Mirror the change** to the `.claude/` twin immediately, in the same commit.

5. **Run the verification commands** in the next section before `git commit`.

6. **Write a commit message** that explains the intent; if you replaced a hardcoded path, call out which placeholder you used.

---

## File Synchronization Invariant

Every file under `skills/`, `agents/`, or `commands/` has a byte-identical mirror under the matching `.claude/` path:

```
skills/km-workflow.md              ≡  .claude/skills/km-workflow.md
agents/knowledge-manager.md        ≡  .claude/agents/knowledge-manager.md
commands/knowledge-manager-at.md   ≡  .claude/commands/knowledge-manager-at.md
```

Check invariant:

```bash
for f in skills/*.md agents/*.md commands/*.md; do
  diff -q "$f" ".claude/$f" || echo "OUT OF SYNC: $f"
done
```

Expected output: nothing (no `OUT OF SYNC` lines).

If you add a new skill, create it in **both** locations. If you delete one, delete both. If you rename one, rename both.

---

## Verification Before Commit

Run these four checks and confirm the expected output before every commit that touches skill/agent/command files:

1. **No hardcoded personal paths**:
   ```bash
   grep -rE "/home/[^/]+/|/Users/[^/]+/|C:\\\\Users\\\\|/mnt/c/Users/[^/]+/" skills/ agents/ commands/ .claude/
   ```
   Expected: 0 matching lines (exit 1 from grep is the success case).

2. **Mirrors are in sync** (see command above). Expected: no output.

3. **Substitution engine still runs cleanly** against a sample config:
   ```bash
   bash scripts/configure-vault-paths.sh --dry-run
   ```
   Expected: no errors, summary of substitutions printed.

4. **Placeholder set unchanged**:
   ```bash
   grep -rhoE "\{\{[A-Z_]+\}\}" skills/ agents/ commands/ | sort -u
   ```
   Expected: exactly these 5 tokens (no more, no fewer):
   ```
   {{OBSIDIAN_CLI}}
   {{RESEARCH_ROOT}}
   {{VAULT_NAME}}
   {{VAULT_PATH}}
   {{ZETTELKASTEN_ROOT}}
   ```

If any check fails, fix the issue before committing. Do not disable a check to make it pass.

---

## Out of Scope

You should **not** take the following actions without explicit user confirmation:

- **Do not push to `origin/master`.** Always push to a feature branch and let the maintainer review.
- **Do not force-push** to any shared branch.
- **Do not modify `km-config.json`** (it is gitignored and private to the user's machine).
- **Do not modify `scripts/configure-vault-paths.sh` or `scripts/_lib-config.sh`** unless you are explicitly asked to change the substitution behavior. These scripts own the placeholder contract; accidentally breaking them breaks every downstream user.
- **Do not introduce a new placeholder token** without first updating `CLAUDE.md`, this file, `docs/vault-path-configuration.md`, and `scripts/configure-vault-paths.sh` together.
- **Do not remove the `km-storage-abstraction.md` anti-pattern** exclusion from the substitution engine. That file teaches a specific lesson and must stay in its generic-name form.
- **Do not run `/knowledge-manager-setup` inside this repo non-interactively** — it generates personal config files.
- **Do not edit or commit content under `docs/plans/`** unless the user is explicitly working on plan updates. Those are design artifacts.

---

## Quick Reference

| If you want to... | Do this |
|---|---|
| Reference the user's vault root | Write `{{VAULT_PATH}}` |
| Reference `<vault>/Zettelkasten/foo.md` | Write `{{VAULT_PATH}}/{{ZETTELKASTEN_ROOT}}/foo.md` |
| Call Obsidian CLI | Write `"{{OBSIDIAN_CLI}}" create --vault "{{VAULT_NAME}}" ...` |
| Add a new skill file | Create under both `skills/X.md` and `.claude/skills/X.md`, use placeholders |
| Update upstream | Tell the user to run `/km-update` (not raw `git pull`) |
| Check for hardcoded paths | `grep -rE "/home/[^/]+/|/Users/[^/]+/|C:\\\\Users\\\\" skills/ agents/ commands/ .claude/` |
| Check mirror sync | `diff -q skills/X.md .claude/skills/X.md` |

For deeper context — the config schema, the exact substitution algorithm, the skip-worktree rationale, troubleshooting recipes — read [`docs/vault-path-configuration.md`](docs/vault-path-configuration.md).
