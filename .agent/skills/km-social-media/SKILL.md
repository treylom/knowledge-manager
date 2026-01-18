---
name: Social Media Content Extraction
description: Extract content from Threads, Instagram with reply collection and depth control
---

# Social Media Content Extraction

> Threads, Instagram 등 소셜 미디어 콘텐츠 추출 가이드

---

## 🛑 MANDATORY - Depth 선택 질문 필수!

```
┌─────────────────────────────────────────────────────┐
│ ⚠️ MANDATORY CHECKPOINT                              │
│                                                      │
│ 소셜 미디어 URL 처리 시 반드시 depth를 물어야 합니다! │
│                                                      │
│ ⚠️ 이 질문 없이 스크래핑 시작 = 잘못된 동작!          │
│                                                      │
│ 자동 스킵 허용 조건:                                  │
│ - "빠르게" 키워드 → depth=1 자동 적용                 │
│ - "전체", "다" 키워드 → depth=2 자동 적용             │
│ - 키워드 없음 → 반드시 질문!                          │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 URL 정규화 (MANDATORY)

소셜 미디어 URL 처리 전 **반드시** 정규화 수행:

| 입력 URL | 정규화 결과 |
|----------|-------------|
| `threads.com/@user/post/...` | `threads.net/@user/post/...` |
| `www.threads.net/@user/post/...` | `threads.net/@user/post/...` |
| `m.threads.net/@user/post/...` | `threads.net/@user/post/...` |
| `instagram.com/p/...` | `instagram.com/p/...` (변경 없음) |
| `www.instagram.com/p/...` | `instagram.com/p/...` |
| `m.instagram.com/p/...` | `instagram.com/p/...` |

```javascript
function normalize_social_url(url) {
  // Threads 정규화
  url = url.replace(/threads\.com/g, 'threads.net')
  url = url.replace(/www\.threads\.net/g, 'threads.net')
  url = url.replace(/m\.threads\.net/g, 'threads.net')

  // Instagram 정규화
  url = url.replace(/www\.instagram\.com/g, 'instagram.com')
  url = url.replace(/m\.instagram\.com/g, 'instagram.com')

  return url
}
```

**⚠️ 정규화 없이 크롤링 시작 = 잘못된 동작!**

---

## Depth 선택 질문 (필수!)

소셜 미디어 URL 감지 시 **반드시** 물어야 합니다:

```
🔄 답글 수집 범위를 선택해주세요:

1) depth=1: 직접 답글만 (빠름)
   - 본문 + 직접 달린 답글만 수집

2) depth=2: 답글의 답글까지 (더 완전한 맥락)
   - 본문 + 모든 답글 + 중첩 답글까지 수집

기본값(depth=2)을 사용하시겠습니까?
```

---

## 지원 플랫폼

| Platform | URL Pattern | Stealth Required |
|----------|-------------|------------------|
| Threads | `threads.net/@*/post/*` | Yes |
| Instagram | `instagram.com/p/*` | Yes |

---

## 크롤링 워크플로우

### Step 1: 메인 포스트 접근

```javascript
// Hyperbrowser 사용 (스텔스 모드)
mcp_hyperbrowser_scrape_webpage({
  url: "https://threads.net/@user/post/ABC",
  outputFormat: ["markdown"],
  sessionOptions: {
    useStealth: true  // 소셜 미디어는 스텔스 필수
  }
})
```

### Step 2: Depth에 따른 답글 수집

**depth=1 (직접 답글만):**
```javascript
// 메인 포스트 페이지의 답글만 파싱
// 추가 크롤링 불필요
```

**depth=2 (답글의 답글까지):**
```javascript
// 각 답글 URL을 수집하여 병렬 크롤링
reply_urls.forEach(url => {
  mcp_hyperbrowser_scrape_webpage({
    url: url,
    outputFormat: ["markdown"],
    sessionOptions: { useStealth: true }
  })
})
```

---

## 출력 형식

```markdown
---
tags: [threads, 소셜미디어, {주제태그}]
source: {original_url}
author: {작성자}
created: {작성일}
captured: {수집일}
depth: {1 or 2}
---

# {제목 또는 첫 문장}

## 본문
{메인 포스트 내용}

## 답글
### @replier1
{답글 내용}

### @replier2
{답글 내용}

---

## 관련 노트
- [[연결된 노트]]
```

---

## MCP 도구 (Antigravity/Gemini CLI)

| 작업 | 도구 |
|------|------|
| 웹 스크래핑 | `mcp_hyperbrowser_scrape_webpage` |
| Vault 검색 | `mcp_obsidian_search_vault` |
| 노트 저장 | `mcp_obsidian_create_note` |

> **참고**: 싱글 언더스코어(`_`) 사용
