---
name: Zettelkasten Note Creation
description: Create atomic, interconnected notes following Zettelkasten methodology
---

# Zettelkasten Note Creation

> Create atomic, self-contained, interconnected notes

---

## Core Principles

### 1. Atomicity
- One idea per note
- If you can split it, split it
- Note should be about ONE concept

### 2. Self-Contained
- Note must be understandable without context
- Include enough background information
- Reader shouldn't need to read other notes first

### 3. Connectivity
- Link to related notes with `[[wikilinks]]`
- Explain the relationship in the link
- Build a knowledge network

---

## Note Structure

```markdown
---
tags: [{domain}, {topic}, {type}]
created: {YYYY-MM-DD}
source: {url_or_reference}
type: zettelkasten
---

# {Concept Name}

> {One-sentence definition or summary}

## Explanation

{2-3 paragraphs explaining the concept}
{Include examples if helpful}

## Key Characteristics

- Characteristic 1
- Characteristic 2
- Characteristic 3

## Connections

- [[Related Concept A]] - {how they relate}
- [[Related Concept B]] - {how they relate}
- [[Contrasting Concept]] - {how they differ}

## Examples

{Concrete examples or applications}

## Source

- {Original source with link}
```

---

## Folder Organization

```
Vault/
├── Zettelkasten/
│   ├── AI-Research/
│   ├── Programming/
│   └── Productivity/
├── Research/
│   └── Papers/
├── Threads/
└── Inbox/
```

---

## Naming Convention

`{Topic} - {Specific Concept}.md`

Examples:
- `MCP - Protocol Overview.md`
- `Zettelkasten - Atomicity Principle.md`
- `Claude Code - Hooks System.md`
