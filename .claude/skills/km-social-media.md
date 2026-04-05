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
Run: python3 scripts/scrapling-crawl.py fetch "[URL]" --mode dynamic --output markdown
Run: python3 scripts/scrapling-crawl.py fetch "[URL]" --mode stealth --output markdown
```

### Playwright MCP — Do Not Use for SNS

Use `playwright-cli` (Bash) exclusively for social media. See km-content-extraction for non-SNS sources.
MCP is unstable with SNS dynamic loading and scroll control.
