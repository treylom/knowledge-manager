---
name: Browser Abstraction Layer
description: Unified browser interface for Antigravity native, Playwright, and Hyperbrowser providers
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
  return config?.browser?.provider || "playwright"
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
    default:
      mcp__playwright__browser_navigate({ url: url })
      mcp__playwright__browser_wait_for({ time: 3 })
      return mcp__playwright__browser_snapshot()
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
