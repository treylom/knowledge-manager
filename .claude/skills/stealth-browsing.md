---
name: stealth-browsing
description: |
  안티-디텍션 브라우저 자동화 스킬.
  봇 탐지를 우회하여 웹사이트에 접근하고 콘텐츠를 추출합니다.
  6가지 안티-디텍션 기능: 베지어 곡선 마우스, 랜덤 좌표 클릭, 클립보드 붙여넣기,
  headed 모드, 랜덤 딜레이, 타이핑 노이즈.
  openclaw/openclaw 브라우저 모듈 패턴 기반.
triggers:
  - stealth browsing
  - 스텔스 브라우징
  - 봇 탐지 우회
  - anti-detection
  - 안티-디텍션
  - 브라우저 자동화 우회
  - 네이버 로그인 자동화
  - 구글 검색 자동화
  - 소셜미디어 스크래핑
  - CloudFlare 우회
---

# Stealth Browsing Skill

봇 탐지를 우회하는 안티-디텍션 브라우저 자동화 도구.

## 빠른 판단: 어떤 도구를 사용할까?

```
단순 스크래핑 (봇 탐지 없음)
  → scrapling-crawl.py --mode dynamic (1순위, 가장 빠름)
  → 기존 Playwright MCP (폴백)

봇 탐지 있는 사이트 (소셜미디어, CloudFlare 등)
  → scrapling-crawl.py --mode stealth (1순위, 내장 안티봇)
  → 이 스킬의 TS 스텔스 스크립트 (폴백)

복잡한 클라우드 자동화 (API 키 필요)
  → Hyperbrowser MCP

단순 HTML 가져오기
  → scrapling-crawl.py --mode http (가장 빠름)
  → WebFetch (폴백)
```

## 사용법

### 방법 1: 콘텐츠 추출 (원샷)

```bash
npx tsx .claude/skills/stealth-browsing/scripts/stealth-navigate-and-extract.ts \
  "https://example.com" \
  --output markdown \
  --wait 3000

# JSON 형식으로 출력 (프로그래밍용)
npx tsx .claude/skills/stealth-browsing/scripts/stealth-navigate-and-extract.ts \
  "https://example.com" \
  --output markdown \
  --json

# 동적 콘텐츠 (무한 스크롤)
npx tsx .claude/skills/stealth-browsing/scripts/stealth-navigate-and-extract.ts \
  "https://threads.net/@user" \
  --scroll-to-bottom \
  --scroll-count 5 \
  --output text

# 특정 요소만 추출
npx tsx .claude/skills/stealth-browsing/scripts/stealth-navigate-and-extract.ts \
  "https://example.com" \
  --selector "article.main-content" \
  --output markdown
```

### 방법 2: 봇 탐지 테스트

```bash
npx tsx .claude/skills/stealth-browsing/scripts/stealth-browser.ts --test
```

### 방법 3: 수동 브라우저 열기

```bash
npx tsx .claude/skills/stealth-browsing/scripts/stealth-browser.ts --url "https://example.com"
```

## 안티-디텍션 기능 (6가지)

| # | 기능 | 설명 |
|---|------|------|
| 1 | 베지어 곡선 마우스 | ghost-cursor로 자연스러운 곡선 이동 |
| 2 | 랜덤 좌표 클릭 | 요소 정중앙이 아닌 랜덤 위치 클릭 |
| 3 | 클립보드 붙여넣기 | Ctrl+V로 텍스트 입력 (키스트로크 분석 우회) |
| 4 | Headed 모드 | 항상 브라우저 창 표시 (headless 탐지 우회) |
| 5 | 랜덤 딜레이 | 액션 간 500-2000ms 자연스러운 대기 |
| 6 | 타이핑 노이즈 | 75±50ms 가변 속도 + 5% 사고 정지 |

상세 기술 정보: `references/anti-detection-techniques.md`

## 스크립트 파일 구조

```
.claude/skills/stealth-browsing/
  scripts/
    stealth-browser.ts           # 스텔스 브라우저 런처
    stealth-actions.ts           # 6가지 안티-디텍션 액션 라이브러리
    stealth-navigate-and-extract.ts  # CLI 진입점 (URL → 콘텐츠)
  references/
    anti-detection-techniques.md # 기법 상세 참조
```

## npm 의존성

```bash
# 프로젝트 루트에서 설치 필요
npm install ghost-cursor-playwright playwright-extra puppeteer-extra-plugin-stealth
```

## Playwright MCP와 병행 사용

### 주의: Chrome 프로필 잠금
스텔스 스크립트와 Playwright MCP는 **같은 Chrome 프로필**을 사용합니다.
동시에 실행하면 프로필 잠금 충돌이 발생합니다.

**사용 순서:**
1. Playwright MCP로 시도 → 봇 탐지 시
2. MCP 브라우저 먼저 종료 (`browser_close`)
3. 스텔스 스크립트 실행

### MCP 도구에 스텔스 패턴 적용
기존 Playwright MCP를 사용할 때도 간단한 스텔스 효과를 줄 수 있습니다:

```
1. browser_navigate로 이동
2. 1-3초 랜덤 대기 (인간 행동 시뮬레이션)
3. browser_snapshot으로 페이지 분석
4. browser_press_key("End")로 스크롤 시뮬레이션
5. 다시 1-2초 대기
6. browser_click 등 상호작용
```

## Knowledge Manager 통합

stealth-browsing은 knowledge-manager의 브라우징 스택에서 Tier 4로 작동합니다:

```
우선순위:
1. scrapling-crawl.py --mode dynamic (Python, JS 렌더링, 3x 빠름)
2. scrapling-crawl.py --mode stealth (Python, 안티봇 우회)
3. playwright-cli (Bash, 폴백 + 스크린샷)
4. 스텔스 스크립트 (이 스킬) ← Scrapling stealth도 실패 시 사용
5. Playwright MCP
6. Hyperbrowser (클라우드, 유료)
```

knowledge-manager에서 사용 시:
```bash
# 소셜미디어 콘텐츠 추출
npx tsx .claude/skills/stealth-browsing/scripts/stealth-navigate-and-extract.ts \
  "https://threads.net/@user/post/abc" \
  --output markdown \
  --json \
  --scroll-to-bottom
```

## 한계점

- **TLS/JA3 핑거프린트**: Playwright 엔진 레벨 한계 → 수정 불가
- **CloudFlare 고급 Challenge**: 일부 케이스에서 여전히 차단될 수 있음
- **동시 실행 불가**: Playwright MCP와 동시 사용 시 프로필 충돌
- **Windows 전용 테스트**: macOS/Linux에서는 경로 수정 필요

## 참고

- openclaw 원본: https://github.com/openclaw/openclaw (src/browser/)
- openclaw 라이선스: MIT
