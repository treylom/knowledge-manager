# Storage Abstraction Layer

> Knowledge Manager의 저장소 추상화 레이어
> 설정에 따라 Obsidian, Notion, Local 중 선택

---

## 설정 읽기 (CRITICAL)

작업 시작 전 `km-config.json`에서 저장소 설정 확인:

```javascript
// 설정 파일 읽기
config = Read("km-config.json")

primary = config.storage.primary  // "obsidian" | "notion" | "local"
obsidian = config.storage.obsidian
notion = config.storage.notion
local = config.storage.local
```

---

## Provider별 도구 매핑

### Obsidian (권장 - 로컬 지식 관리)

```javascript
// 설정 확인
if (!config.storage.obsidian.enabled) {
  // Obsidian 미설정 → 폴백
}

vaultPath = config.storage.obsidian.vaultPath
defaultFolder = config.storage.obsidian.defaultFolder  // "Zettelkasten"

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
❌ 틀림: MyVault/Zettelkasten/...  (vault 이름 중복 금지)
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
function save_note(relativePath, content, options = {}) {
  // 1. Primary 저장소 시도
  primary = config.storage.primary

  switch (primary) {
    case "obsidian":
      if (config.storage.obsidian.enabled) {
        try {
          return mcp__obsidian__create_note({
            path: relativePath,
            content: content
          })
        } catch (e) {
          // MCP 실패 → Local 폴백
          return save_to_local(relativePath, content)
        }
      }
      break

    case "notion":
      if (config.storage.notion.enabled) {
        try {
          return save_to_notion(relativePath, content)
        } catch (e) {
          // Notion 실패 → Local 폴백
          return save_to_local(relativePath, content)
        }
      }
      break

    case "local":
    default:
      return save_to_local(relativePath, content)
  }

  // Primary 미설정 → Local 폴백
  return save_to_local(relativePath, content)
}

function save_to_local(relativePath, content) {
  outputPath = config.storage.local.outputPath || "./km-output"
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
저장: Write(file_path: "./km-output/Zettelkasten/AI-연구/노트.md")
결과: {cwd}/km-output/Zettelkasten/AI-연구/노트.md
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
1. Primary 저장소 시도
   ↓ 실패
2. Local 폴백 시도
   ↓ 실패
3. 콘텐츠를 응답에 출력
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
```
