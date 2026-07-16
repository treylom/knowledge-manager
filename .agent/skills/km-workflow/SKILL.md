---
name: km-workflow
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

## 🛑 MANDATORY WORKFLOW - 절대 건너뛰지 마세요!

**Antigravity/Gemini CLI에서 반드시 실행:**

### STEP 1: 사용자 선호도 확인 (Phase 1.5) - 필수!

콘텐츠 처리 전 **반드시** 아래 질문을 사용자에게 물어야 합니다:

```
📊 상세 수준: 1.요약 / 2.보통 / 3.상세
🎯 중점 영역: A.개념 / B.실용 / C.기술 / D.인사이트 / E.전체
📝 노트 분할: ①단일 / ②주제별 / ③원자적 / ④3-tier
🔗 연결 수준: 최소 / 보통 / 최대

기본값(3.상세, E.전체, ④3-tier, 최대)을 사용하시겠습니까?

💡 3-tier란? 개요 노트 + 주제별 노트 + 원자적 노트로 계층 구조화
```

**소셜 미디어(Threads/Instagram) URL인 경우 추가 질문:**

```
🔄 답글 수집 범위:
  1) depth=1: 직접 답글만 (빠름)
  2) depth=2: 답글의 답글까지 (더 완전한 맥락)
```

**⚠️ 이 단계를 건너뛰면 안 됩니다!**
- 사용자가 "빠르게", "기본으로" 등 퀵 프리셋 키워드를 사용한 경우만 생략 가능
- 그 외 모든 경우: 반드시 질문 후 진행

### STEP 2: Vault 검색 및 노트 연결 (Phase 3.5) - 필수!

노트 저장 전 **반드시** 관련 노트를 검색하고 연결합니다.

#### Step 2-1: 관련 키워드 추출
콘텐츠에서 핵심 키워드 추출:
- 주제 키워드 (예: "AI", "프롬프트", "Claude")
- 인물/계정명 (예: "@openai", "Anthropic")
- 기술 용어 (예: "LLM", "RAG", "embedding")

#### Step 2-2: Vault 검색 실행
```javascript
// Antigravity/Gemini CLI 도구명
keywords = ["AI", "프롬프트", "Claude"]

keywords.forEach(keyword => {
  mcp_obsidian_search_vault({ query: keyword })
})
```

#### Step 2-3: 관련 노트 읽기 및 분석
검색 결과에서 상위 노트들을 읽어 관련성 확인:
```javascript
// 검색 결과에서 상위 10개 노트 읽기
search_results.slice(0, 10).forEach(result => {
  mcp_obsidian_read_note({ path: result.path })
})
```

#### Step 2-4: 연결 수준에 따른 링크 추가
**Phase 1.5에서 선택한 "🔗 연결 수준"에 따라 링크 개수 결정:**

| 연결 수준 | 링크 개수 | 설명 |
|----------|----------|------|
| **최소** | 1-2개 | 가장 관련성 높은 노트만 연결 |
| **보통** (기본값) | 3-5개 | 주요 관련 노트 연결 |
| **최대** | 5-10개 | 관련 가능성 있는 모든 노트 연결 |

#### Step 2-5: Wikilink 형식으로 노트에 추가
```markdown
## 관련 노트
- [[AI-프롬프트-기초]]
- [[Claude-사용-가이드]]
- [[LLM-활용법]]
```

**⚠️ Vault 검색 없이 저장 = 잘못된 동작!**
**⚠️ 관련 노트 발견했는데 wikilink 안 함 = 잘못된 동작!**

### STEP 3: MCP 도구 사용 (Phase 5) - 필수!

| 환경 | 사용할 도구 | 절대 사용 금지 |
|------|------------|---------------|
| Antigravity | `mcp_obsidian_create_note` | `write_to_file` |
| Gemini CLI | `mcp_obsidian_create_note` | `write_to_file` |

**⚠️ MCP 도구 사용 가능한데 파일 시스템 도구 사용 = 잘못된 동작!**

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
