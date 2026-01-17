---
name: Storage Abstraction Layer
description: Unified storage interface for Obsidian, Notion, and local file systems
---

# Storage Abstraction Layer

> Unified interface for saving notes across different storage backends

---

## Storage Selection

```javascript
function get_storage_backend() {
  config = Read("km-config.json")
  return config?.storage?.primary || "local"
}
```

## Backend Mapping

| Feature | Obsidian | Notion | Local |
|---------|----------|--------|-------|
| Tool | `mcp__obsidian__create_note` | `mcp__notion__API-post-page` | `Write` |
| Path format | Relative to vault | Database/Page ID | File system path |
| Wikilinks | Supported | Converted to mentions | Supported |

---

## Unified Save Function

```javascript
function save_note(relativePath, content) {
  backend = get_storage_backend()
  config = Read("km-config.json")

  switch (backend) {
    case "obsidian":
      return mcp__obsidian__create_note({
        path: relativePath,
        content: content
      })

    case "notion":
      // Convert to Notion blocks
      return mcp__notion__API-post-page({
        parent: { page_id: config.storage.notion.parentPageId },
        properties: { title: [{ text: { content: getTitle(relativePath) } }] }
      })

    case "local":
    default:
      fullPath = `${config.storage.local.outputPath}/${relativePath}`
      return Write({ file_path: fullPath, content: content })
  }
}
```

---

## Path Normalization

```javascript
function normalize_path(path) {
  // Windows backslash → forward slash
  path = path.replace(/\\/g, '/')

  // Remove leading slash for relative paths
  path = path.replace(/^\//, '')

  return path
}
```

---

## Verification (CRITICAL)

After every save operation:

```
□ Did the tool actually execute? (no JSON-only output!)
□ Did we receive a success response?
□ Verify with Glob that file exists
```
