---
name: Knowledge Manager Workflow
description: 6-phase workflow for content extraction, analysis, and export to Obsidian/Notion
---

# Knowledge Manager Workflow

> Complete 6-phase workflow guide for content processing

---

## Workflow Overview

```
Phase 0: Load Configuration
    ↓
Phase 1: Detect Input Source
    ↓
Phase 1.5: Collect User Preferences
    ↓
Phase 2: Extract Content
    ↓
Phase 3: Analyze Content
    ↓
Phase 4: Select Output Format
    ↓
Phase 5: Execute Export
    ↓
Phase 6: Verify and Report
```

---

## Phase 0: Load Configuration (CRITICAL)

**Must execute before all operations**

```javascript
// 1. Read config file
config = Read("km-config.json")

// 2. Check required items
if (!config) {
  return "Configuration file not found. Please run /knowledge-manager setup"
}

// 3. Load storage settings
storage = {
  primary: config.storage.primary,
  obsidian: config.storage.obsidian,
  notion: config.storage.notion,
  local: config.storage.local
}

// 4. Load browser settings
browser = {
  provider: config.browser.provider,
  hyperbrowser: config.browser.hyperbrowser
}
```

---

## Phase 1: Detect Input Source

### Input Type Detection

| Input Pattern | Type | Processing |
|--------------|------|------------|
| `https://threads.net/*` | Social Media | → km-browser-abstraction (stealth recommended) |
| `https://instagram.com/*` | Social Media | → km-browser-abstraction (stealth recommended) |
| `https://*` | Web URL | → km-browser-abstraction |
| `*.pdf` | PDF File | → Read tool |
| `*.docx` | Word File | → Read tool |
| `notion.so/*` | Notion Page | → Notion MCP |

---

## Phase 2: Extract Content

### Use Browser Abstraction Layer

→ See `km-browser-abstraction` skill

```javascript
// Auto-select based on configured provider
content = scrape_url(url, {
  stealth: inputType.requiresStealth
})
```

---

## Phase 3: Analyze Content

### Apply Zettelkasten Principles

1. **Atomicity**: One idea = One note
2. **Self-contained**: Note is understandable on its own
3. **Connectivity**: Links between related concepts

---

## Phase 4-6: Export and Verify

### Use Storage Abstraction Layer

→ See `km-storage-abstraction` skill

```javascript
// Auto-save to configured storage
save_note(relativePath, content)
```

### Final Report Template

```markdown
## ✅ Processing Complete!

### Input
- Source: {url or filename}
- Type: {web / file / social media}

### Saved Notes
| Title | Path | Status |
|-------|------|--------|
| {note1} | {path1} | ✅ |
```
