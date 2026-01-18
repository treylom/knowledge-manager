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

## 🛑 MCP 도구 우선 사용 규칙 (CRITICAL)

```
┌─────────────────────────────────────────────────────┐
│ 🛑 CRITICAL: MCP 도구 사용 강제                      │
│                                                      │
│ MCP 도구가 사용 가능한 환경에서는 반드시 MCP 사용!    │
│                                                      │
│ ❌ 잘못된 예:                                        │
│    - write_to_file("vault/note.md", content)         │
│                                                      │
│ ✅ 올바른 예:                                        │
│    - mcp_obsidian_create_note(path, content)         │
└─────────────────────────────────────────────────────┘
```

## Backend Mapping (Antigravity/Gemini CLI)

| Feature | Obsidian | Notion | Local |
|---------|----------|--------|-------|
| Create | `mcp_obsidian_create_note` | `mcp_notion_API-post-page` | `write_to_file` |
| Search | `mcp_obsidian_search_vault` | `mcp_notion_API-post-search` | N/A |
| Read | `mcp_obsidian_read_note` | `mcp_notion_API-get-block-children` | `read_file` |
| Path format | Relative to vault | Database/Page ID | File system path |
| Wikilinks | Supported | Converted to mentions | Supported |

> **참고**: Antigravity는 MCP 도구 이름에 싱글 언더스코어(`_`)를 사용합니다.

### MCP 도구 사용 가이드 (Obsidian)

| 작업 | 도구명 | 설명 |
|------|--------|------|
| 노트 생성 | `mcp_obsidian_create_note` | 새 노트 생성 |
| 노트 검색 | `mcp_obsidian_search_vault` | Vault 내 키워드 검색 |
| 노트 읽기 | `mcp_obsidian_read_note` | 노트 내용 읽기 |
| 노트 목록 | `mcp_obsidian_list_notes` | 폴더 내 노트 목록 |

---

## Unified Save Function

```javascript
// Antigravity/Gemini CLI용 (싱글 언더스코어 사용)
function save_note(relativePath, content) {
  backend = get_storage_backend()
  config = Read("km-config.json")

  switch (backend) {
    case "obsidian":
      // ⚠️ 반드시 MCP 도구 사용!
      return mcp_obsidian_create_note({
        path: relativePath,
        content: content
      })

    case "notion":
      return mcp_notion_API_post_page({
        parent: { page_id: config.storage.notion.parentPageId },
        properties: { title: [{ text: { content: getTitle(relativePath) } }] }
      })

    case "local":
    default:
      fullPath = `${config.storage.local.outputPath}/${relativePath}`
      return write_to_file(fullPath, content)
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
