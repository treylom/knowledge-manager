---
name: Export Formats
description: Output format specifications for Obsidian, Notion, and Markdown exports
---

# Export Formats

> Format specifications for different output targets

---

## Obsidian / Zettelkasten Format

### Note Template

```markdown
---
tags: [{category}, {topic}]
created: {YYYY-MM-DD}
source: {original_url}
type: {zettelkasten/reference/literature}
---

# {Title}

> {One-sentence summary}

## Core Concept

{Main content - one atomic idea}

## Key Points

- Point 1
- Point 2

## Connections

- [[Related Note 1]] - {relationship}
- [[Related Note 2]] - {relationship}

## Source

- Original: {url}
- Author: {if available}
- Date: {if available}
```

---

## Notion Format

### Page Structure

```javascript
{
  parent: { page_id: "..." },
  properties: {
    title: { title: [{ text: { content: "Note Title" } }] },
    Tags: { multi_select: [{ name: "tag1" }] },
    Source: { url: "https://..." },
    Created: { date: { start: "2026-01-17" } }
  },
  children: [
    {
      type: "heading_2",
      heading_2: { rich_text: [{ text: { content: "Summary" } }] }
    },
    {
      type: "paragraph",
      paragraph: { rich_text: [{ text: { content: "..." } }] }
    }
  ]
}
```

---

## Local Markdown Format

Same as Obsidian format, saved to local file system with Write tool.

Default output path: `./km-notes/`

---

## Detail Level Mapping

| Level | Notes | Detail |
|-------|-------|--------|
| 1 (Brief) | 1-2 | Core summary only |
| 2 (Normal) | 3-5 | Main concepts separated |
| 3 (Detailed) | 5-10+ | All ideas as atomic notes |
