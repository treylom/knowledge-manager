---
name: km-browser-abstraction
description: Unified browser interface for browser auto-detect (default: ego lite → Aside → Playwright), Antigravity native, Playwright, and Hyperbrowser providers
---

# Browser Abstraction Layer

> Unified interface for web content extraction across browser providers
> This provider (automatic browser detection) is the first choice for ordinary web page extraction — see the order in km-content-extraction. Scrapling is optional and only tried before it when installed separately.

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
  return config?.browser?.provider || "auto"
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

## Browser auto-detect (1.8.6 — default · no user setup)

Run this block once, at the moment a page has to be opened in a real browser (the «browser» slot of the order below). It picks the first of ego lite → Aside → the existing order (Playwright CLI → Playwright MCP → WebFetch) that is installed and answers. The user does not choose or configure a browser.

```bash
KM_BD="${CLAUDE_PLUGIN_ROOT}/scripts/km_browser_detect.py"
[ -f "$KM_BD" ] || KM_BD="$(find "$HOME/.claude/plugins" "$HOME/.codex/plugins" -name km_browser_detect.py 2>/dev/null | sort | tail -1)"
if [ -f "$KM_BD" ]; then python3 "$KM_BD" --config "./km-config.json" --config "${VAULT_PATH:-.}/km-config.json"; else echo '{"provider":"fallback","reason":"detector missing"}'; fi
```
- The script reads `browser.provider` from km-config.json itself (`--config`; missing, `auto` or `playwright` → auto order). `ego` / `aside` are tried first but fall through to the auto order when that tool is missing.
- If this file was read with Read and `${CLAUDE_PLUGIN_ROOT}` is still literal, replace it in the first line with this plugin's folder (this file's path up to `.agent/` / `skills/`).
- Output = one JSON line. `provider` = `ego` | `aside` | `fallback` | (explicit `hyperbrowser` / `antigravity`) · `bin` = absolute path of the CLI.
- **`provider=ego`** → open with ego lite, using the printed `bin` absolute path as the command (works even when its folder is not on PATH). If the ego lite app is closed, this command opens its window (measured on macOS; other OSes not yet checked). ego lite runs this work in a separate task space, so the first time in a conversation tell the user in one line: "Click the number button at the top right of the ego lite window, then the ‘km read’ space, to watch the page I am reading." (measured on macOS)
  ```bash
  "<bin>" nodejs -e '
  const task = await taskSpace("km read");
  const page = task.page("p1");
  await page.goto("[URL]");
  console.log(await page.evaluate(() => document.title + "\n\n" + document.body.innerText));
  '
  ```
  For clicks, input or screenshots read `"<bin>" skill` first and use only the APIs it lists (do not guess Playwright methods). One task = one TaskSpace.
- **`provider=aside`** → `"<bin>" exec "Open [URL] and return the page body text verbatim, without summarizing. Include title, author, date, and image descriptions."`
- **`provider=fallback`** → the existing order (Playwright CLI → Playwright MCP → WebFetch).
- If the chosen browser fails while running, log the reason in one line and move to the next slot (ego → aside → fallback).
- **Exception: when ego lite stops for the user, do not move to the next slot.** If the error mentions `permission prompt`, `user now controls` or `takeOverTaskSpace` (a site's notification/location permission prompt, a device chooser, etc.), it is not a failure. Tell the user and stop: "In the ego lite window, click the number button at the top right → click the space marked ‘Need your action’ → click ‘Block’ (or handle the prompt) → click ‘Return to agent’ at the bottom, then tell me it is done." (measured on macOS; on a Korean-language Mac the button reads ‘차단’) When the user confirms, resume the same space with `const task = await takeOverTaskSpace(<id>)` (`<id>` = the `id` from the error or `listTaskSpaces()`). Never click ‘Allow’ on the user's behalf.
- Never open someone else's login wall, paywall, CAPTCHA, or robots/ToS-forbidden page with any browser.

## Aside (auto-detect slot 2 — when ego lite is missing)

```bash
# Aside (since 1.8.4) — where Playwright used to be needed: public pages anyone can view in a browser but static fetching (WebFetch) cannot open, social media, browser actions.
# Command name: macOS = aside · WSL/Windows = aside.exe (write the command name literally)
aside exec "Open [URL] and return the page body text verbatim, without summarizing. Include title, author, date, and image descriptions."
# Screenshots, form input, and clicks use the same aside exec prompt (e.g. "…open and save a full-page capture to [path]")
# Do not use it to get past someone else's login wall, paywall, CAPTCHA, or pages that robots.txt / ToS prohibit.
# If Aside is missing or fails, log the reason and fall through to Playwright.
```

```javascript
// Pseudocode: the single exec line from the common block
async function scrape_with_aside(url) {
  return Bash(`aside exec "Open ${url} and return the page body text verbatim, without summarizing. Include title, author, date, and image descriptions."`)
}
```

- Pros: keeps login session · real browser
- Cons: slow to run · requires the aside app

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
      // on aside failure — log the reason
      mcp__playwright__browser_navigate({ url: url })
      mcp__playwright__browser_wait_for({ time: 3 })
      return mcp__playwright__browser_snapshot()

    default:
      // default: aside
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
      console.warn(`Aside failed (${error.message}) → trying Playwright → WebFetch (limited)`)
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
