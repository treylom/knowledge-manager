# Storage Abstraction Layer

> Knowledge Manager의 저장소 추상화 레이어
> 설정에 따라 Obsidian, Notion, Local 중 선택

---

## 저장 대상과 설정 읽기 (CRITICAL)

저장 대상 root는 backend 설정보다 먼저 정한다. project-scoped file save에서는 workflow가 host의 primary project/workspace root를 `target_root`로 넘겨야 한다. `km-config.json`은 도구 설정이며 project root를 다른 볼트로 바꾸는 권한이 없다.

```javascript
target_root = options.target_root ? realpath(options.target_root) : null
config = Read("km-config.json") || {}
storage = config.storage || {}

primary = options.explicit_backend || (options.project_scoped ? "local" : storage.primary)
obsidian = storage.obsidian
notion = storage.notion
local = storage.local
```

---

## Provider별 도구 매핑

### 🛑 Target Root 일치 규칙 (CRITICAL)

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

우선순위: 사용자 명시 대상/backend > host가 제공한 primary project/workspace root > project-scoped 요청이 아닐 때만 configured backend. 사용자가 명시적으로 Notion을 고른 경우는 파일 containment 검증 대신 생성된 page URL/ID를 검증한다.

### 환경별 도구 이름

| 환경 | Obsidian 노트 생성 | Obsidian 검색 |
|------|-------------------|--------------|
| **Claude Code** | `mcp__obsidian__create_note` | `mcp__obsidian__search_vault` |
| **Antigravity** | `mcp_obsidian_create_note` | `mcp_obsidian_search_vault` |
| **Gemini CLI** | `mcp_obsidian_create_note` | `mcp_obsidian_search_vault` |

> **참고**: Antigravity와 Gemini CLI는 MCP 도구 이름에 더블 언더스코어(`__`) 대신 싱글 언더스코어(`_`)를 사용합니다.

---

### Obsidian (권장 - 로컬 지식 관리)

```javascript
// 설정 확인
if (!config?.storage?.obsidian?.enabled) {
  // Obsidian 미설정 → 폴백
}

vaultPath = realpath(config.storage.obsidian.vaultPath)
defaultFolder = config.storage.obsidian.defaultFolder  // "Zettelkasten"

// project-scoped save에서는 동일 root 확인이 선행 조건
if (options.project_scoped && !same_path(vaultPath, target_root)) {
  return save_to_target_root(relativePath, content, target_root)
}

// 노트 생성 (MCP 사용 - 상대 경로!)
mcp__obsidian__create_note({
  path: `${defaultFolder}/카테고리/노트제목 - YYYY-MM-DD-HHmm.md`,
  content: "[노트 내용]"
})

// 노트 읽기
mcp__obsidian__read_note({
  path: `${defaultFolder}/카테고리/노트.md`
})

// 노트 검색
mcp__obsidian__search_vault({
  query: "검색어"
})

// 노트 목록
mcp__obsidian__list_notes({
  folder: defaultFolder
})
```

**경로 규칙 (CRITICAL):**
```
✅ 올바름: Zettelkasten/AI-연구/노트.md  (vault root 기준 상대 경로)
❌ 틀림: /Users/.../vault/Zettelkasten/...  (절대 경로 금지)
❌ 틀림: YourVaultName/Zettelkasten/...  (vault 이름 중복 금지)
```

**장점:**
- 로컬 파일 기반
- Obsidian 앱과 완벽 통합
- Wikilinks 지원

---

### Notion (팀 협업용)

```javascript
// 설정 확인
if (!config.storage.notion.enabled) {
  // Notion 미설정 → 폴백
}

defaultDb = config.storage.notion.defaultDatabaseId

// 페이지 생성
mcp__notion__API-post-page({
  parent: { page_id: defaultDb },
  properties: {
    title: [{
      text: { content: "노트 제목" }
    }]
  }
})

// 블록 추가
mcp__notion__API-patch-block-children({
  block_id: pageId,
  children: [
    {
      type: "paragraph",
      paragraph: {
        rich_text: [{ text: { content: "내용" } }]
      }
    }
  ]
})

// 페이지 검색
mcp__notion__API-post-search({
  query: "검색어"
})
```

**장점:**
- 클라우드 기반
- 팀 협업 지원
- 데이터베이스 기능

**단점:**
- API 토큰 필요
- 인터넷 연결 필요

---

### Local (폴백 - 항상 가능)

```javascript
// 설정
outputPath = config.storage.local.outputPath  // 예: "./km-output"

// 폴더 구조
// km-output/
//   ├── Zettelkasten/
//   │   └── 카테고리/
//   ├── Research/
//   └── Threads/

// 파일 저장
Write({
  file_path: `${outputPath}/Zettelkasten/카테고리/노트.md`,
  content: "[노트 내용]"
})

// 파일 읽기
Read(`${outputPath}/Zettelkasten/카테고리/노트.md`)

// 파일 목록
Glob({ pattern: `${outputPath}/**/*.md` })
```

**장점:**
- 항상 사용 가능
- 설정 최소화
- MCP 서버 불필요

**단점:**
- Obsidian/Notion 기능 미지원
- Wikilinks 작동 안 함

---

## 추상화 함수

### save_note(path, content, options)

```pseudo
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
    current = canonical(next)  // resolve every existing symlink component
    assert(is_within(current, canonical_root))
  }
  return join(current, basename(relativePath))
}

function save_note(relativePath, content, options = {}) {
  config = Read("km-config.json") || {}
  primary = options.explicit_backend || (options.project_scoped ? "local" : config?.storage?.primary)
  target_root = options.target_root

  if (options.project_scoped && !target_root) {
    throw Error("target_root is required for a project-scoped save")
  }

  canonical_target_root = target_root ? canonical(target_root) : null
  safe_relative_path = normalize_path(relativePath)
  if (is_absolute(safe_relative_path) || has_parent_escape(safe_relative_path)) {
    throw Error("relativePath escapes target_root")
  }
  target_candidate = options.project_scoped
    ? resolve_within(canonical_target_root, safe_relative_path)
    : null

  switch (primary) {
    case "obsidian":
      if (config?.storage?.obsidian?.enabled) {
        obsidian_root = config.storage.obsidian.vaultPath || get_obsidian_connected_root()
        if (options.project_scoped && (!obsidian_root || !same_path(obsidian_root, canonical_target_root))) {
          result = save_to_target_root(safe_relative_path, content, canonical_target_root)
          break
        }
        try {
          response = mcp__obsidian__create_note({
            path: safe_relative_path,
            content: content
          })
          result = {
            ...response,
            path: options.project_scoped
              ? target_candidate
              : join(canonical(obsidian_root), safe_relative_path)
          }
          break
        } catch (e) {
          result = options.project_scoped
            ? save_to_target_root(safe_relative_path, content, canonical_target_root)
            : save_to_local(safe_relative_path, content)
          break
        }
      }
      break

    case "notion":
      if (config?.storage?.notion?.enabled) {
        if (options.project_scoped && options.explicit_backend !== "notion") {
          result = save_to_target_root(safe_relative_path, content, canonical_target_root)
          break
        }
        try {
          return save_to_notion(safe_relative_path, content)
        } catch (e) {
          result = options.project_scoped
            ? save_to_target_root(safe_relative_path, content, canonical_target_root)
            : save_to_local(safe_relative_path, content)
          break
        }
      }
      break

    case "local":
    default:
      result = options.project_scoped
        ? save_to_target_root(safe_relative_path, content, canonical_target_root)
        : save_to_local(safe_relative_path, content)
  }

  if (!result) {
    result = options.project_scoped
      ? save_to_target_root(safe_relative_path, content, canonical_target_root)
      : save_to_local(safe_relative_path, content)
  }

  actual_saved_path = canonical(result.path)
  assert(file_exists(actual_saved_path))
  if (options.project_scoped && !is_within(actual_saved_path, canonical_target_root)) {
    throw Error(`Save escaped target_root: ${actual_saved_path}`)
  }
  return { ...result, actual_saved_path }
}

function save_to_target_root(relativePath, content, canonical_target_root) {
  fullPath = resolve_within(canonical_target_root, relativePath)
  assert(is_within(fullPath, canonical_target_root))
  response = Write({ file_path: fullPath, content: content })
  return { ...response, path: fullPath }
}

function save_to_local(relativePath, content) {
  outputPath = config?.storage?.local?.outputPath || "./km-output"
  fullPath = `${outputPath}/${relativePath}`
  return Write({ file_path: fullPath, content: content })
}
```

---

## 다중 저장소 동시 저장

여러 저장소에 동시 저장할 수 있습니다:

```pseudo
function save_to_multiple(relativePath, content) {
  results = []

  // Obsidian
  if (config.storage.obsidian.enabled) {
    results.push(save_to_obsidian(relativePath, content))
  }

  // Notion
  if (config.storage.notion.enabled) {
    results.push(save_to_notion(relativePath, content))
  }

  // Local (항상)
  if (config.storage.local.enabled) {
    results.push(save_to_local(relativePath, content))
  }

  return results
}
```

---

## 경로 변환 규칙

### Obsidian 경로

```
입력: Zettelkasten/AI-연구/노트.md
저장: mcp__obsidian__create_note(path: "Zettelkasten/AI-연구/노트.md")
결과: {vaultPath}/Zettelkasten/AI-연구/노트.md
```

### Notion 경로

```
입력: Zettelkasten/AI-연구/노트.md
변환:
  - "Zettelkasten" → Zettelkasten 데이터베이스
  - "AI-연구" → 페이지 태그/속성
  - "노트.md" → 페이지 제목
```

### Local 경로

```
입력: Zettelkasten/AI-연구/노트.md
project-scoped 저장: Write(file_path: "{target_root}/Zettelkasten/AI-연구/노트.md")
결과: {canonical_target_root}/Zettelkasten/AI-연구/노트.md

project-scoped가 아닐 때만 기존 `config.storage.local.outputPath`를 사용한다.
```

---

## 폴더 구조 템플릿

사용자의 저장소에 생성될 폴더 구조:

```
[Root]/
├── Zettelkasten/          ← 원자적 노트
│   ├── AI-연구/
│   ├── 프로그래밍/
│   ├── 생산성/
│   └── ...
├── Research/              ← 연구 문서, MOC
│   └── [프로젝트명]/
│       ├── [제목]-MOC.md
│       └── 01-챕터/
├── Threads/               ← Thread 스타일 콘텐츠
└── Inbox/                 ← 미분류 노트
```

---

## 저장소별 기능 지원

| 기능 | Obsidian | Notion | Local |
|------|----------|--------|-------|
| Wikilinks | ✅ | ❌ (변환) | ❌ |
| 태그 | ✅ | ✅ | ✅ (YAML) |
| 폴더 계층 | ✅ | ✅ (페이지) | ✅ |
| 검색 | ✅ | ✅ | ⚠️ (Grep) |
| 백링크 | ✅ | ❌ | ❌ |
| 협업 | ❌ | ✅ | ❌ |

---

## 에러 처리

### 저장 실패 시 폴백 체인

```
1. target_root와 일치하는 도구 시도
   ↓ 실패·root 불일치·root 확인 불가
2. target_root 안에 Write 폴백
   ↓ 실패
3. 저장 성공으로 보고하지 않고 콘텐츠를 응답에 출력
   + 수동 저장 안내
```

### 에러 메시지 예시

```markdown
⚠️ Obsidian MCP 연결 실패

원인 가능성:
- MCP 서버가 실행 중이지 않음
- Vault 경로가 올바르지 않음
- 권한 문제

시도한 조치:
- Local 폴더에 저장 시도 → 성공

저장 위치: ./km-output/Zettelkasten/AI-연구/노트.md

Obsidian으로 가져오려면:
1. 위 파일을 Obsidian vault에 복사
2. 또는 MCP 설정 확인: claude mcp list
```

---

## 설정 검증 체크리스트

```
Obsidian 사용 시:
□ config.storage.obsidian.enabled = true?
□ config.storage.obsidian.vaultPath 설정됨?
□ 해당 경로가 실제로 존재?
□ obsidian MCP 서버 연결됨?

Notion 사용 시:
□ config.storage.notion.enabled = true?
□ config.storage.notion.token 설정됨?
□ 토큰이 유효? (만료 확인)
□ notion MCP 서버 연결됨?

Local 사용 시:
□ config.storage.local.outputPath 설정됨?
□ 해당 경로에 쓰기 권한 있음?

Project-scoped file save 시:
□ canonical_target_root가 host의 primary project/workspace root와 같은가?
□ VAULT-STRUCTURE.md와 MOC-Map.md(존재 시)를 경로 결정 전에 읽었는가?
□ actual_saved_path가 존재하고 canonical_target_root 안인가?
□ 최종 보고에 target_root·상대 경로·actual_saved_path를 명시했는가?
```
