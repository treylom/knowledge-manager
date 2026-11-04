# Browser Abstraction Layer

> Knowledge Manager의 브라우저 자동화 추상화 레이어
> 기본 = 브라우저 자동 탐색(ego lite → Aside → Playwright) · 설정으로 Hyperbrowser·Antigravity 지정 가능
> 이 공급자는 브라우저가 필요할 때만 쓴다 — 일반 페이지는 km-content-extraction 의 Scrapling 이 먼저.

---

## 설정 읽기 (CRITICAL)

작업 시작 전 `km-config.json`에서 브라우저 설정 확인:

```javascript
// 설정 파일 읽기
config = Read("km-config.json")
provider = config.browser.provider  // "auto"(기본) | "ego" | "aside" | "playwright" | "hyperbrowser" | "antigravity"
```

---

## Provider별 도구 매핑

### 브라우저 자동 탐색 (1.8.6 — 기본 · 사용자 설정 없음)

웹 페이지를 브라우저로 열어야 하는 순간(아래 순서표의 «브라우저» 칸)에 먼저 이 블록을 한 번 실행한다. ego lite → Aside → 기존 순서(Playwright CLI → Playwright MCP → WebFetch) 가운데 «깔려 있고 대답하는» 첫 번째를 고른다. 사용자가 브라우저를 따로 고르거나 설정할 일은 없다.

```bash
KM_BD="${CLAUDE_PLUGIN_ROOT}/scripts/km_browser_detect.py"
[ -f "$KM_BD" ] || KM_BD="$(find "$HOME/.claude/plugins" "$HOME/.codex/plugins" -name km_browser_detect.py 2>/dev/null | sort | tail -1)"
if [ -f "$KM_BD" ]; then python3 "$KM_BD" --config "./km-config.json" --config "${VAULT_PATH:-.}/km-config.json"; else echo '{"provider":"fallback","reason":"detector missing"}'; fi
```
- km-config.json 의 `browser.provider` 는 대본이 `--config` 로 직접 읽는다(없거나 `auto`·`playwright` 면 자동 순서). `ego`·`aside` 를 적어 둔 경우에도 그 도구가 없으면 자동 순서로 넘어간다.
- 이 문서를 Read 로 읽어 `${CLAUDE_PLUGIN_ROOT}` 가 글자 그대로 남아 있으면, 첫 줄의 그 자리를 «이 문서가 든 플러그인 폴더»(이 파일 경로에서 `commands/`·`skills/` 앞까지)로 바꿔 친다.
- 출력 = JSON 한 줄. `provider` = `ego` | `aside` | `fallback` | (명시한 `hyperbrowser`·`antigravity`) · `bin` = 실행 파일 절대 경로.
- **`provider=ego`** → ego lite 로 연다. 명령 이름 자리에 출력된 `bin` 절대 경로를 그대로 쓴다(사용자 PATH 에 그 폴더가 없어도 돈다). ego lite 앱이 꺼져 있어도 이 명령이 앱 창을 띄운다.
  ```bash
  "<bin>" nodejs -e '
  const task = await taskSpace("km read");
  const page = task.page("p1");
  await page.goto("[URL]");
  console.log(await page.evaluate(() => document.title + "\n\n" + document.body.innerText));
  '
  ```
  클릭·입력·스크린샷이 필요하면 먼저 `"<bin>" skill` 로 사용 안내를 읽고 거기 적힌 API 만 쓴다(Playwright 메서드를 짐작해 쓰지 않는다). 한 작업 = 작업 공간(TaskSpace) 하나.
- **`provider=aside`** → `"<bin>" exec "[URL] 페이지를 열고 본문 텍스트를 요약 없이 그대로 돌려줘. 제목·작성자·날짜·이미지 설명 포함."`
- **`provider=fallback`** → 기존 순서 그대로(Playwright CLI → Playwright MCP → WebFetch).
- 고른 브라우저가 실행 중 실패하면 실패 이유를 한 줄 남기고 다음 칸(ego → aside → fallback)으로 넘어간다.
- 남의 로그인 벽·페이월·CAPTCHA·robots/ToS 금지 페이지는 어느 브라우저로도 열지 않는다.

### Aside (자동 탐색 2순위 — ego lite 가 없을 때)

```bash
# Aside (1.8.4 — 예전에 playwright 로 읽던 자리: Scrapling 으로는 안 열리지만 브라우저로는 누구나 볼 수 있는 공개 페이지 · SNS · 브라우저 조작)
# 남의 로그인 벽·페이월·CAPTCHA·robots/ToS 금지 페이지는 aside 로도 열지 않는다.
# 실행 이름: macOS = aside · WSL/Windows = aside.exe (실행 이름을 그대로 적는다)
aside exec "[URL] 페이지를 열고 본문 텍스트를 요약 없이 그대로 돌려줘. 제목·작성자·날짜·이미지 설명 포함."
# 스크린샷·폼 입력·클릭도 같은 aside exec 지시문으로(예: "…열고 전체 화면 캡처를 [경로]에 저장")
# aside 가 없거나 실패하면: 실패 이유를 남기고 아래 순위로 넘어간다.
```

```javascript
// 의사코드: 공통 블록의 exec 1줄
async function scrape_with_aside(url) {
  return Bash(`aside exec "${url} 페이지를 열고 본문 텍스트를 요약 없이 그대로 돌려줘. 제목·작성자·날짜·이미지 설명 포함."`)
}
```

**장점:**
- 로그인 세션 유지
- 실제 브라우저

**단점:**
- 실행 시간 김
- aside 앱 필요

---

### Playwright (자동 탐색 브라우저 — ego lite·Aside — 가 없거나 실패했을 때 · 이유를 남긴 뒤)

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
    case "aside":
      return scrape_with_aside(url)

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
      // 기본값: aside
      return scrape_with_aside(url)
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
Hyperbrowser 실패 → Aside 시도
자동 탐색(ego lite → Aside) — ego lite 실패(이유 기록) → Aside 시도
Aside 실패(이유 기록) → Playwright 시도
Playwright 실패 → WebFetch 시도 (제한적)
모두 실패 → 에러 보고
```

---

## 사용 예시

### 예시 1: 일반 웹페이지

```
URL: https://example.com/article
Provider: aside

→ aside exec "[URL] 본문 그대로"
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
□ aside(맥) / aside.exe(WSL) 가 PATH 에 있음?
□ 해당 MCP 서버가 .mcp.json에 설정됨?
□ MCP 서버 연결 상태 정상? (claude mcp list)
□ API 키 유효? (hyperbrowser 사용 시)
```
