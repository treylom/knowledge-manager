---
name: km-social-media
description: Use when scraping social media content. Detects social media URLs and extracts content via Playwright CLI with scroll-based reply loading.
---

# 소셜 미디어 콘텐츠 스크래핑 스킬

> Knowledge Manager 파이프라인의 소셜 미디어 URL 자동 감지 및 Playwright 기반 콘텐츠 추출 스킬

---

## MANDATORY ACTIONS

Run the following tools in order when a social media URL is detected.

### Tool Priority (CRITICAL)

> Threads/Instagram use login walls and dynamic loading — scrapling returns only the first post.
> Use Playwright CLI as the primary tool.

```
# 1. Use Playwright CLI (Bash — required for SNS. Scrolls to load replies)
Run: playwright-cli open "[URL]"       # Open browser and navigate
Run: sleep 3                           # Wait for dynamic content
Run: playwright-cli snapshot           # Create accessibility snapshot
# Check the snapshot: Read(".playwright-cli/page-*.yml")
# If replies are truncated:
Run: playwright-cli press End          # Scroll to bottom
Run: sleep 2
Run: playwright-cli snapshot           # Add more content
Run: playwright-cli close              # Close browser

# 2. Use Scrapling only if CLI fails (may return first post only)
# scripts/scrapling-crawl.py 는 이 플러그인에 포함되지 않음 — 별도 준비, 없으면 playwright-cli
Run: python3 scripts/scrapling-crawl.py fetch "[URL]" --mode dynamic --output markdown
Run: python3 scripts/scrapling-crawl.py fetch "[URL]" --mode stealth --output markdown
```

### Playwright MCP — Do Not Use for SNS

Use `playwright-cli` (Bash) exclusively for social media. See km-content-extraction for non-SNS sources.
MCP is unstable with SNS dynamic loading and scroll control.


## 수집 결과 완결성 확인

소셜 원문 수집 결과를 저장·전달하기 직전에 확인한다. 메인 포스트에 저자의 스레드 표시 `🧵`가 있으면 본문뿐 아니라 저자가 이어 쓴 번호 답글(`1/`, `2/` 등)까지 수집됐는지 원문과 대조한다. 번호 답글을 확보하지 못했다면 같은 URL의 브라우저 스크롤·답글 펼치기로 재확인한다. 그래도 확인할 수 없으면 `본문만 확보·스레드 답글 미확인`이라고 기록하고 전체 수집 완료로 보고하지 않는다.

`🧵`가 없다는 이유만으로 완결을 단정하지 말고 요청받은 답글 수집 범위를 따른다. 이 확인은 소셜 수집 결과의 저장·전달에 한정하며, 무관한 `WebFetch`·`Bash` 실행을 차단하는 전역 훅으로 적용하지 않는다.
