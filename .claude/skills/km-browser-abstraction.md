# Browser Abstraction Layer

> Knowledge Manager의 브라우저 자동화 추상화 레이어
> 설정에 따라 Playwright, Hyperbrowser, Antigravity 중 선택

---

## 설정 읽기 (CRITICAL)

작업 시작 전 `km-config.json`에서 브라우저 설정 확인:

```javascript
// 설정 파일 읽기
config = Read("km-config.json")
provider = config.browser.provider  // "playwright" | "hyperbrowser" | "antigravity"
```

---

## Provider별 도구 매핑

### Playwright (기본 - 무료, 로컬)

```javascript
// 단순 스크래핑 (3단계)
async function scrape_with_playwright(url) {
  // Step 1: 페이지 이동
  mcp__playwright__browser_navigate({ url: url })

  // Step 2: 로딩 대기
  mcp__playwright__browser_wait_for({ time: 3 })

  // Step 3: 콘텐츠 추출
  return mcp__playwright__browser_snapshot()
}

// 스크린샷
mcp__playwright__browser_take_screenshot({ fullPage: true })

// 폼 입력
mcp__playwright__browser_type({ ref: "...", text: "...", submit: true })

// 클릭
mcp__playwright__browser_click({ ref: "...", element: "..." })
```

**장점:**
- 무료, API 키 불필요
- 로컬 실행
- 전체 브라우저 제어

**단점:**
- 소셜 미디어에서 차단될 수 있음
- 스텔스 모드 미지원

---

### Hyperbrowser (클라우드 - API 키 필요)

```javascript
// 단순 스크래핑 (1회 호출)
mcp__hyperbrowser__scrape_webpage({
  url: "https://example.com",
  outputFormat: ["markdown"]
})

// 소셜 미디어 (스텔스 모드)
mcp__hyperbrowser__scrape_webpage({
  url: "https://threads.net/@user/post/123",
  outputFormat: ["markdown"],
  sessionOptions: { useStealth: true }
})

// 스크린샷 포함
mcp__hyperbrowser__scrape_webpage({
  url: "https://example.com",
  outputFormat: ["markdown", "screenshot"]
})

// 복잡한 상호작용 (AI 에이전트)
mcp__hyperbrowser__openai_computer_use_agent({
  task: "Navigate to the page and extract...",
  maxSteps: 10
})
```

**장점:**
- 스텔스 모드 지원 (소셜 미디어)
- 단일 호출로 완료
- 클라우드 기반 (리소스 절약)

**단점:**
- API 키 필요
- 비용 발생

---

### Antigravity (Antigravity 환경)

Antigravity 환경에서 제공하는 브라우저 도구 사용.
설정: `config.browser.antigravity.enabled = true`

---

## 추상화 함수

### scrape_url(url, options)

```pseudo
function scrape_url(url, options = {}) {
  // 1. 설정에서 provider 확인
  provider = config.browser.provider

  // 2. 소셜 미디어 URL 감지
  is_social = detect_social_media(url)

  // 3. Provider별 처리
  switch (provider) {
    case "playwright":
      if (is_social) {
        warn_user("소셜 미디어 URL입니다. 차단될 수 있습니다.")
      }
      return scrape_with_playwright(url)

    case "hyperbrowser":
      sessionOptions = {}
      if (is_social || options.stealth) {
        sessionOptions.useStealth = true
      }
      return mcp__hyperbrowser__scrape_webpage({
        url: url,
        outputFormat: options.format || ["markdown"],
        sessionOptions: sessionOptions
      })

    case "antigravity":
      return scrape_with_antigravity(url)

    default:
      // 기본값: playwright
      return scrape_with_playwright(url)
  }
}
```

### detect_social_media(url)

```javascript
function detect_social_media(url) {
  const patterns = [
    /threads\.net\//,
    /instagram\.com\/p\//,
    /instagram\.com\/reel\//,
    /twitter\.com\//,
    /x\.com\//,
    /facebook\.com\//
  ]
  return patterns.some(p => p.test(url))
}
```

---

## 소셜 미디어 처리 규칙

### URL 패턴별 권장 설정

| URL 패턴 | Playwright | Hyperbrowser | 권장 |
|----------|-----------|--------------|------|
| `threads.net/*` | 차단 가능 | stealth 필수 | Hyperbrowser |
| `instagram.com/p/*` | 차단 가능 | stealth 필수 | Hyperbrowser |
| `instagram.com/reel/*` | 차단 가능 | stealth 필수 | Hyperbrowser |
| `twitter.com/*` | 부분 지원 | stealth 권장 | Hyperbrowser |
| 일반 웹사이트 | OK | OK | Playwright |

### Hyperbrowser 미설정 시 경고

```markdown
⚠️ 소셜 미디어 URL이 감지되었습니다: {url}

현재 설정: Playwright (browser.provider = "playwright")

Playwright로 시도하지만, 다음 문제가 발생할 수 있습니다:
- 로그인 요구
- 콘텐츠 차단
- Rate limiting

더 안정적인 스크래핑을 위해 Hyperbrowser 설정을 권장합니다:

1. km-config.json 수정:
   "browser": { "provider": "hyperbrowser" }

2. .mcp.json에 hyperbrowser 서버 추가

3. Hyperbrowser API 키 발급:
   https://hyperbrowser.ai
```

---

## 에러 처리

### 스크래핑 실패 시

```
1. 첫 번째 시도 실패
   → 3초 대기 후 재시도

2. 두 번째 시도 실패
   → 다른 provider로 폴백 시도 (설정된 경우)

3. 모든 시도 실패
   → 사용자에게 에러 보고 + 대안 안내
```

### 폴백 체인

```
Hyperbrowser 실패 → Playwright 시도
Playwright 실패 → WebFetch 시도 (제한적)
모두 실패 → 에러 보고
```

---

## 사용 예시

### 예시 1: 일반 웹페이지

```
URL: https://example.com/article
Provider: playwright

→ mcp__playwright__browser_navigate
→ mcp__playwright__browser_wait_for
→ mcp__playwright__browser_snapshot
→ 콘텐츠 반환
```

### 예시 2: Threads 포스트 (Hyperbrowser 설정됨)

```
URL: https://threads.net/@user/post/123
Provider: hyperbrowser

→ 소셜 미디어 URL 감지
→ mcp__hyperbrowser__scrape_webpage (useStealth: true)
→ 콘텐츠 반환
```

### 예시 3: Instagram (Hyperbrowser 미설정)

```
URL: https://instagram.com/p/ABC123
Provider: playwright

→ 소셜 미디어 URL 감지
→ 경고 메시지 표시
→ Playwright로 시도
→ 성공 시: 콘텐츠 반환
→ 실패 시: Hyperbrowser 설정 가이드 표시
```

---

## 설정 검증 체크리스트

```
□ km-config.json에 browser.provider 설정됨?
□ 해당 MCP 서버가 .mcp.json에 설정됨?
□ MCP 서버 연결 상태 정상? (claude mcp list)
□ API 키 유효? (hyperbrowser 사용 시)
```
