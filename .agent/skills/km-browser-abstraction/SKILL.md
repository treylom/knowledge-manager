---
name: km-browser-abstraction
description: Unified browser interface for Aside (default), Antigravity native, Playwright, and Hyperbrowser providers
---

# Browser Abstraction Layer

> Unified interface for web content extraction across browser providers
> This provider is only for when a browser is needed — for ordinary pages, the Scrapling / WebFetch order in km-content-extraction comes first.

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

## Aside (default since 1.8.4)

```bash
# Aside (since 1.8.4) — where Playwright used to be needed: sites the lightweight path cannot reach, social media, browser actions.
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
