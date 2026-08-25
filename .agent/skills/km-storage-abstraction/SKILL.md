---
name: km-storage-abstraction
description: Unified storage interface for Obsidian, Notion, and local file systems
---

# Storage Abstraction Layer

> Unified interface for saving notes across different storage backends

---

## Storage Selection and Target-Root Contract

```javascript
function get_storage_backend(options = {}) {
  config = Read("km-config.json") || {}
  if (options.explicit_backend) return options.explicit_backend
  if (options.project_scoped) return "local"
  return config?.storage?.primary || "local"
}
```

For project-scoped file saves, the workflow must pass `target_root`. The backend may choose a tool, but it must not choose or redirect the destination root.

Priority: user-explicit destination/backend → host-provided primary project/workspace root → configured backend only outside project-scoped requests.

## 🛑 Target Root 일치 규칙 (CRITICAL)

```
┌─────────────────────────────────────────────────────┐
│ 🛑 CRITICAL: target_root 보존 강제                   │
│                                                      │
│ Obsidian 도구는 연결 볼트와 target_root가 같을 때만!   │
│                                                      │
│ ❌ 잘못된 예:                                        │
│    - 연결 볼트 확인 없이 MCP로 상대경로 저장           │
│                                                      │
│ ✅ 올바른 예:                                        │
│    - roots 동일 → MCP / 다름·미확인 → target_root Write│
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
function canonical(path) {
  return realpath(path)
}

function same_path(left, right) {
  return canonical(left) === canonical(right)
}

function resolve_within(canonical_root, relativePath) {
  current = canonical_root
  for (component of dirname(relativePath).split('/')) {
    next = join(current, component)
    if (!exists(next)) mkdir(next)
    current = canonical(next) // resolve every existing symlink component
    assert(is_within(current, canonical_root))
  }
  return join(current, basename(relativePath))
}

function save_note(relativePath, content, options = {}) {
  config = Read("km-config.json") || {}
  backend = get_storage_backend(options)
  target_root = options.target_root

  if (options.project_scoped && !target_root) {
    throw new Error("target_root is required for a project-scoped save")
  }

  canonical_target_root = target_root ? canonical(target_root) : null
  safe_relative_path = normalize_path(relativePath)
  if (is_absolute(safe_relative_path) || has_parent_escape(safe_relative_path)) {
    throw new Error("relativePath escapes target_root")
  }
  target_candidate = options.project_scoped
    ? resolve_within(canonical_target_root, safe_relative_path)
    : null

  function save_to_target_root() {
    assert(is_within(target_candidate, canonical_target_root))
    result = write_to_file(target_candidate, content)
    return { ...result, path: target_candidate }
  }

  switch (backend) {
    case "obsidian":
      obsidian_root = config?.storage?.obsidian?.vaultPath || get_obsidian_connected_root()
      if (options.project_scoped && (!obsidian_root || !same_path(obsidian_root, canonical_target_root))) {
        result = save_to_target_root()
        break
      }
      result = mcp_obsidian_create_note({
        path: safe_relative_path,
        content: content
      })
      result.path = options.project_scoped
        ? target_candidate
        : join(canonical(obsidian_root), safe_relative_path)
      break

    case "notion":
      if (options.project_scoped && options.explicit_backend !== "notion") {
        result = save_to_target_root()
        break
      }
      return mcp_notion_API_post_page({
        parent: { page_id: config.storage.notion.parentPageId },
        properties: { title: [{ text: { content: getTitle(relativePath) } }] }
      })

    case "local":
    default:
      if (options.project_scoped) {
        result = save_to_target_root()
      } else {
        outputPath = config?.storage?.local?.outputPath || "./km-output"
        fullPath = `${outputPath}/${safe_relative_path}`
        result = write_to_file(fullPath, content)
        result.path = fullPath
      }
  }

  actual_saved_path = canonical(result.path)
  assert(file_exists(actual_saved_path))
  if (options.project_scoped && !is_within(actual_saved_path, canonical_target_root)) {
    throw new Error(`Save escaped target_root: ${actual_saved_path}`)
  }
  return { ...result, actual_saved_path }
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
□ Is actual_saved_path canonicalized and does the file exist there?
□ For a project-scoped save, is actual_saved_path inside canonical_target_root?
□ Does the final report include target_root, relative path, and actual_saved_path?
```
