# ?�셜 미디??콘텐�??�크?�핑 ?�킬

> Knowledge Manager ?�이?�트???�셜 미디??URL ?�동 감�? �?Playwright MCP ?�크?�핑 ?�킬

---

## ?�� MANDATORY ACTIONS (?�수 ?�동!)

**?�셜 미디??URL 감�? ??반드???�음 ?�구?�을 ?�제�??�출?�야 ?�니??**

### ?�구 ?�선?�위 (CRITICAL!)

```
# 1순위: Playwright CLI (Bash)
playwright-cli open "[URL]"            # 페이지 이동
playwright-cli press End               # 스크롤
playwright-cli snapshot                # 접근성 스냅샷
playwright-cli screenshot              # 스크린샷
playwright-cli close                   # 브라우저 닫기

# 2순위: Playwright MCP (CLI 실패 시)
mcp__playwright__browser_navigate      # 페이지 이동
mcp__playwright__browser_wait_for      # 대기(초/시간)
mcp__playwright__browser_snapshot      # 접근성 스냅샷
mcp__playwright__browser_take_screenshot  # 스크린샷
mcp__playwright__browser_click         # 클릭
mcp__playwright__browser_scroll        # 스크롤
mcp__playwright__browser_close         # 브라우저 닫기
```
