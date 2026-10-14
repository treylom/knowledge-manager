---
name: km-browser-abstraction
description: Unified browser interface for Aside (default), Antigravity native, Playwright, and Hyperbrowser providers
---

# Browser Abstraction Layer

> Unified interface for web content extraction across browser providers

---

## Provider Selection

```javascript
function get_browser_provider() {
  // 1. Check environment first
  if (is_antigravity_environment()) {
    return "antigravity"  // Use native browser agent
  }

  // 2. Fall back to config
  config = Read("km-config.json")
  return config?.browser?.provider || "aside"
}

function is_antigravity_environment() {
  // Antigravity provides built-in browser capabilities
  // Check if running inside Antigravity IDE
  return typeof antigravity !== 'undefined' ||
         process.env.ANTIGRAVITY_SESSION ||
         file_exists("~/.gemini/antigravity/")
}
```

---

## Aside (기본 - 재경님 10-14 강제)

```bash
# 0순위: Aside (재경님 10-14 강제 — 웹 페이지 열기·JS 렌더·로그인 페이지는 aside 먼저)
# 실행 이름: 맥 = aside · WSL = aside.exe (변수·$( ) 꼴은 명령 검사 훅이 막으므로 실행 이름을 그대로 적는다)
aside exec "[URL] 페이지를 열고 본문 텍스트를 요약 없이 그대로 돌려줘. 제목·작성자·날짜·이미지 설명 포함."
# 스크린샷·폼 입력·클릭도 같은 aside exec 지시문으로(예: "…열고 전체 화면 캡처를 [경로]에 저장")
# aside 가 없거나 실패하면: 실패 사유 1줄을 남기고 아래 순위로. playwright 계열은 aside 강제 훅이 막으므로 Bash 는 명령 앞 ASIDE_SKIP="<사유 12자+>" 표지가 필요.
```

```javascript
// 의사코드: 공통 블록의 exec 1줄
async function scrape_with_aside(url) {
  return Bash(`aside exec "${url} 페이지를 열고 본문 텍스트를 요약 없이 그대로 돌려줘. 제목·작성자·날짜·이미지 설명 포함."`)
}
```

- 장점: 로그인 세션 유지 · 실제 브라우저 · 훅 허용
- 단점: 실행 시간 김 · aside 앱 필요

---

## Provider Comparison

| Feature | Antigravity Native | Playwright | Hyperbrowser |
|---------|-------------------|-----------|--------------|
| Setup required | None (built-in) | MCP server | MCP + API key |
| Simple scraping | Natural language | `navigate` → `snapshot` | `scrape_webpage` |
| Stealth mode | Built-in | Not supported | `useStealth: true` |
| Social media | Excellent | May be blocked | Good |
| Cost | Free (with Antigravity) | Free | API key required |
| Authentication | Session-aware | Limited | Profile support |

---

## Unified Scraping Function

```javascript
function scrape_url(url, options = {}) {
  provider = get_browser_provider()

  switch (provider) {
    case "aside":
      return scrape_with_aside(url)

    case "antigravity":
      // Antigravity has built-in browser agent
      // Simply ask it to fetch and analyze the page
      return antigravity_browser_fetch(url, options)

    case "hyperbrowser":
      return mcp__hyperbrowser__scrape_webpage({
        url: url,
        outputFormat: ["markdown"],
        sessionOptions: {
          useStealth: options.stealth || false
        }
      })

    case "playwright":
      // aside 실패 시 - 사유 1줄 · ASIDE_SKIP 표지
      mcp__playwright__browser_navigate({ url: url })
      mcp__playwright__browser_wait_for({ time: 3 })
      return mcp__playwright__browser_snapshot()

    default:
      // 기본값: aside
      return scrape_with_aside(url)
  }
}
```

---

## Antigravity Native Browser

Antigravity has a powerful built-in browser agent. No MCP configuration needed.

### Usage in Antigravity

Instead of calling MCP tools, simply instruct the agent:

```
Browse to https://example.com/article and extract the main content.
```

Or for more structured extraction:

```
Go to this URL and summarize the key points:
https://example.com/article
```

### Advantages

1. **No setup**: Works out of the box
2. **Session-aware**: Can handle login states
3. **Smart extraction**: AI-powered content understanding
4. **Anti-bot bypass**: Better success with protected sites

### When to Use Playwright Instead

Even in Antigravity, you might want Playwright MCP for:
- Automated screenshot capture
- Specific DOM manipulation
- Programmatic form filling
- Headless batch processing

---

## Social Media Detection

```javascript
function requires_stealth(url) {
  const patterns = [
    /threads\.net\//,
    /instagram\.com\/p\//,
    /instagram\.com\/reel\//,
    /twitter\.com\//,
    /x\.com\//
  ]
  return patterns.some(p => p.test(url))
}
```

### Provider Recommendations by URL Type

| URL Pattern | Best Provider | Fallback |
|-------------|---------------|----------|
| threads.net | Antigravity / Hyperbrowser | - |
| instagram.com | Antigravity / Hyperbrowser | - |
| twitter.com/x.com | Antigravity | Hyperbrowser |
| Regular websites | Any | Playwright |
| Login-required sites | Antigravity | Hyperbrowser (with profile) |

---

## Fallback Strategy

```javascript
function scrape_with_fallback(url, options = {}) {
  provider = get_browser_provider()

  try {
    return scrape_url(url, options)
  } catch (error) {
    // If primary provider fails, try alternatives
    if (provider === "aside") {
      console.warn("Aside 실패(사유 1줄) → Playwright 시도(ASIDE_SKIP) → WebFetch 시도 (제한적)")
    }

    if (provider === "playwright" && requires_stealth(url)) {
      console.warn("Playwright blocked. Try Antigravity native or Hyperbrowser.")
    }

    if (provider === "antigravity") {
      // Antigravity native rarely fails, but if it does:
      console.warn("Browser fetch failed. Retrying with different approach.")
    }

    throw error
  }
}
```
