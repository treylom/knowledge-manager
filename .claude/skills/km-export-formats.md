# Knowledge Manager 출력 형식

> 다양한 출력 형식 및 내보내기 절차

---

## 🚨 FILE SAVE PROTOCOL (최우선!)

**모든 노트/파일 생성 시 반드시 도구를 실제로 호출해야 합니다!**

### ✅ 필수 패턴

```javascript
// Obsidian MCP:
mcp__obsidian__create_note({
  path: "Zettelkasten/카테고리/노트.md",
  content: "[노트 내용]"
})

// 또는 Write 도구 (Local):
Write({
  file_path: "./km-output/Zettelkasten/카테고리/노트.md",
  content: "[노트 내용]"
})
```

### ❌ 금지 패턴

```json
// JSON 출력만 하면 실제 저장 안 됨!
{ "path": "...", "content": "..." }
```

---

## 지원 출력 형식

| 형식 | 저장소 | 주요 용도 |
|------|--------|----------|
| Zettelkasten | Obsidian | 개인 지식 관리, 연결 노트 |
| Notion 페이지 | Notion | 팀 협업, 데이터베이스 |
| Markdown | Local | 범용, 이식성 |

---

## 저장소별 내보내기

### Obsidian 내보내기

→ `km-storage-abstraction.md` 및 `zettelkasten-note.md` 참조

```javascript
// 설정 확인
if (config.storage.obsidian.enabled) {
  // MCP 도구 사용 (상대 경로)
  mcp__obsidian__create_note({
    path: `${config.storage.obsidian.defaultFolder}/${category}/${title}.md`,
    content: noteContent
  })
}
```

### Notion 내보내기

```javascript
if (config.storage.notion.enabled) {
  // 페이지 생성
  mcp__notion__API-post-page({
    parent: { page_id: config.storage.notion.defaultDatabaseId },
    properties: {
      title: [{ text: { content: title } }]
    }
  })

  // 블록 추가
  mcp__notion__API-patch-block-children({
    block_id: pageId,
    children: convertToNotionBlocks(content)
  })
}
```

### Local 내보내기

```javascript
// 항상 사용 가능 (폴백)
Write({
  file_path: `${config.storage.local.outputPath}/${relativePath}`,
  content: noteContent
})
```

---

## 병렬 출력 처리

### 다중 노트 동시 생성

```javascript
// 여러 노트를 병렬로 생성
const notes = [
  { path: "note1.md", content: "..." },
  { path: "note2.md", content: "..." },
  { path: "note3.md", content: "..." }
]

// 동시 호출 (같은 응답에서)
notes.forEach(note => {
  mcp__obsidian__create_note({
    path: note.path,
    content: note.content
  })
})
```

### 다중 형식 동시 출력

```javascript
// Obsidian + Notion 동시 저장
if (config.storage.obsidian.enabled) {
  mcp__obsidian__create_note({...})
}

if (config.storage.notion.enabled) {
  mcp__notion__API-post-page({...})
}
```

---

## 3-Tier 계층적 내보내기

대용량 문서(연구보고서, 논문, 책)를 체계적으로 정리:

### 구조

```
[프로젝트명]/
├── [제목]-MOC.md                    ← 레벨 1: 메인 MOC
├── 01-[챕터1명]/
│   ├── [챕터1]-MOC.md               ← 레벨 2: 카테고리 MOC
│   ├── [원자노트1].md               ← 레벨 3: 원자적 노트
│   └── [원자노트2].md
└── 02-[챕터2명]/
    ├── [챕터2]-MOC.md
    └── [원자노트3].md
```

### 생성 워크플로우

```
Step 1: 원자 노트 병렬 생성
  → 모든 원자적 노트 동시 생성

Step 2: 카테고리 MOC 생성
  → 각 챕터별 MOC 생성
  → 해당 원자 노트 링크 포함

Step 3: 메인 MOC 생성
  → 전체 개요
  → 모든 카테고리 MOC 링크
```

### 트리거 키워드

| 키워드 | 동작 |
|--------|------|
| "상세하게", "체계적으로" | 3-Tier 구조 자동 적용 |
| "연구보고서", "논문정리" | 3-Tier 구조 자동 적용 |

---

## 네비게이션 푸터 (필수)

**모든 노트에 반드시 포함!**

```markdown
---

## 📍 네비게이션

### 현재 위치
```
📚 [[메인-MOC|문서제목]]
  └── 📂 [[챕터-MOC|챕터명]]
        └── 📄 [현재 노트] ← 현재 위치
```

### 같은 챕터의 노트
| # | 노트 | 상태 |
|---|------|------|
| 1 | [[노트1]] | ⬜ |
| 2 | [[노트2]] | ✅ 현재 |
| 3 | [[노트3]] | ⬜ |

---
← [[챕터-MOC|챕터로]] | [[메인-MOC|메인으로]]
```

---

## Markdown → Notion 변환

| Markdown | Notion Block |
|----------|-------------|
| `# Heading 1` | heading_1 |
| `## Heading 2` | heading_2 |
| `### Heading 3` | heading_3 |
| 문단 | paragraph |
| `- 불릿` | bulleted_list_item |
| `1. 숫자` | numbered_list_item |
| `` `code` `` | code |
| `> 인용` | quote |

### Wikilinks 변환

```
Obsidian: [[노트명]]
Notion: [노트명](notion-page-url)
Local: [노트명](./노트명.md)
```

---

## 에러 핸들링

### 일부 실패 시

```
✅ 성공: 노트A.md, 노트B.md
❌ 실패: 노트C.md (경로 오류)

실패한 콘텐츠:
```[노트 내용]```

수동으로 저장해주세요.
```

### 전체 실패 시

```
❌ 저장 실패

시도한 저장소:
- Obsidian MCP: 연결 실패
- Local Write: 권한 오류

콘텐츠가 아래에 출력됩니다.
복사해서 수동으로 저장해주세요.

---
[전체 노트 내용]
---
```

---

## 품질 체크리스트

```
저장 전:
□ 설정에서 저장소 확인?
□ 경로 형식 올바른가?

저장 중:
□ 실제 도구 호출? (JSON만 금지!)
□ 모든 노트에 대해 호출?

저장 후:
□ 성공 응답 확인?
□ 에러 있으면 폴백 시도?
□ 사용자에게 결과 보고?

3-Tier 구조:
□ 모든 원자 노트 생성?
□ 카테고리 MOC가 링크 포함?
□ 메인 MOC가 전체 링크?
□ 네비게이션 푸터 포함?
```
