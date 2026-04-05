# CLAUDE.md — Claude Code project contract

> This file is read automatically by Claude Code when it opens the knowledge-manager repo. It tells Claude how the placeholder system works and how to edit skill, agent, and command files without breaking portability for other users.

## Repository purpose

knowledge-manager is a **deployment repo**. End users clone it, run `/knowledge-manager-setup`, and the wizard substitutes their personal paths into the skill/agent/command files. The source tree in this repo must stay portable — meaning it must contain `{{PLACEHOLDER}}` tokens, **not** one specific user's hardcoded vault path.

If you hardcode `/home/tofu/AI/AI_Second_Brain` (or any other personal path) into a skill file, every downstream user who pulls that change is broken until they manually reset it.

---

## Critical: Placeholder System

Every file under `skills/`, `agents/`, `commands/`, and their `.claude/` mirrors is either:

1. **Pristine source** (what lives in git) — contains placeholder tokens like `{{VAULT_PATH}}`.
2. **Substituted local copy** (what the user actually uses) — tokens replaced with real values from `km-config.json`, and marked `git update-index --skip-worktree` so the changes don't show up as dirty.

### The 5 placeholders

| Placeholder | Replaced with | Source config field |
|---|---|---|
| `{{VAULT_PATH}}` | Absolute vault path, e.g. `/home/user/Documents/MyVault` | `storage.obsidian.vaultPath` |
| `{{VAULT_NAME}}` | Basename of vault path, e.g. `MyVault` | *(derived)* |
| `{{OBSIDIAN_CLI}}` | Path to Obsidian CLI executable, or empty | `obsidianCli.path` |
| `{{ZETTELKASTEN_ROOT}}` | Vault-relative folder, e.g. `Zettelkasten` | `storage.obsidian.zettelkastenRoot` |
| `{{RESEARCH_ROOT}}` | Vault-relative folder, e.g. `Research` | `storage.obsidian.researchRoot` |

### Placeholders in source vs after setup

```markdown
# IN SOURCE (what you commit):
Save the extracted note to {{VAULT_PATH}}/{{ZETTELKASTEN_ROOT}}/AI/note.md

# AFTER /knowledge-manager-setup (local user view):
Save the extracted note to /home/user/Documents/MyVault/Zettelkasten/AI/note.md
```

You will sometimes read files where the substituted form is visible in your working tree because skip-worktree is active. **Do not confuse that with source content.** Run `git show HEAD:<file>` to see the committed form.

---

## Rules for editing skill / agent / command files

1. **Never hardcode a personal vault path.** If you need to reference a vault location, use `{{VAULT_PATH}}`. If you need to reference a vault-relative subfolder, use `{{VAULT_PATH}}/{{ZETTELKASTEN_ROOT}}/...` or similar composition.

2. **Never hardcode a personal Obsidian CLI path.** Use `{{OBSIDIAN_CLI}}`. Example:
   ```bash
   "{{OBSIDIAN_CLI}}" create --vault "{{VAULT_NAME}}" "Zettelkasten/note.md"
   ```

3. **Mirror `skills/` ↔ `.claude/skills/` atomically.** Every file under `skills/`, `agents/`, or `commands/` has a byte-identical twin under `.claude/`. If you edit one, edit both in the same commit. Use `diff -q skills/foo.md .claude/skills/foo.md` to verify.

4. **Do not edit `skills/km-storage-abstraction.md`'s anti-pattern example** to use placeholders. That file intentionally teaches users **not** to prefix paths with the vault name, and the literal vault-name example is pedagogical. It uses the generic string `YourVaultName` instead.

5. **Do not touch `km-config.json`.** That file is gitignored and holds the user's personal values. The `km-config.example.json` is the template you commit to.

---

## How to test your edits

Before committing any change that touches a skill, agent, or command file:

1. **Grep for personal paths** to make sure you haven't accidentally introduced one:
   ```bash
   grep -rE "/home/[^/]+/|/Users/[^/]+/|C:\\\\Users\\\\" skills/ agents/ commands/ .claude/
   ```
   Expected: 0 hits.

2. **Verify mirror sync**:
   ```bash
   for f in skills/*.md agents/*.md commands/*.md; do
     diff -q "$f" ".claude/$f" || echo "OUT OF SYNC: $f"
   done
   ```
   Expected: no `OUT OF SYNC` lines.

3. **Dry-run the substitution engine** against a sample `km-config.json`:
   ```bash
   bash scripts/configure-vault-paths.sh --dry-run
   ```
   Inspect the output; no errors, every placeholder should be replaced.

4. **Check the skip-worktree state** of files you edited:
   ```bash
   git ls-files -v skills/ | grep '^S'
   ```
   If a file you want to commit is marked `S`, you must `git update-index --no-skip-worktree <file>` before the change can be staged.

5. **Run the `/knowledge-manager-setup` wizard end-to-end** in a scratch clone if you changed the substitution logic, wizard Phase 4, or the placeholder taxonomy.

---

## Directory Layout

```
knowledge-manager/
├── km-config.example.json        # Template schema (committed)
├── km-config.json                # User's local config (gitignored)
├── README.md                     # End-user docs
├── CLAUDE.md                     # THIS FILE
├── AGENTS.md                     # Generic AI agent contract
├── docs/
│   ├── vault-path-configuration.md   # Technical reference
│   └── plans/                    # Design docs
├── scripts/
│   ├── _lib-config.sh            # JSON parser (Node.js-backed)
│   ├── configure-vault-paths.sh  # Substitution engine
│   └── km-update.sh              # Update orchestrator
├── skills/                       # Skill .md files (placeholder form in HEAD)
├── agents/                       # Agent .md files
├── commands/                     # Slash command .md files
└── .claude/                      # Mirror of skills/ + agents/ + commands/
    ├── skills/
    ├── agents/
    └── commands/
```

---

## Commands for Users

| Slash command | What it does |
|---|---|
| `/knowledge-manager-setup` | Runs the setup wizard. Generates `km-config.json`, detects Obsidian CLI, then calls `scripts/configure-vault-paths.sh` to substitute all placeholders and lock the files with `skip-worktree`. |
| `/km-update` | Unlocks placeholder files, restores pristine placeholder form, `git pull`, re-substitutes, re-locks. Safe replacement for raw `git pull`. |
| `/knowledge-manager` | Main knowledge-management agent (content ingestion, summarization, note creation). |
| `/knowledge-manager-at` | Agent-team variant (parallel Category Lead + RALPH + DA). |
| `/knowledge-manager-m` | Mobile/headless variant (no AskUserQuestion, keyword-based presets). |

---

## For Contributors

If you are opening a PR against knowledge-manager:

- **Never commit `km-config.json`.** It is in `.gitignore` for good reason.
- **Always grep for personal paths** before pushing (see step 1 above).
- **Keep `.claude/` mirrors in sync** — CI (when enabled) will reject out-of-sync mirrors.
- **When adding a new skill file**, use placeholders from day one, even if you're the only person who will ever read it. Future contributors will thank you.
- **When editing an existing skill file**, if you see a raw personal path left over from before the placeholder refactor, replace it with the correct placeholder token and note it in your commit message.

See [`AGENTS.md`](AGENTS.md) for the same contract in vendor-neutral form, and [`docs/vault-path-configuration.md`](docs/vault-path-configuration.md) for the full technical reference.
