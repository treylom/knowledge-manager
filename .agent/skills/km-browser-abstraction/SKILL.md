---
name: Browser Abstraction Layer
description: Unified browser interface for Playwright and Hyperbrowser providers
---

# Browser Abstraction Layer

> Unified interface for web content extraction across browser providers

---

## Provider Selection

```javascript
function get_browser_provider() {
  config = Read("km-config.json")
  return config?.browser?.provider || "playwright"
}
```

## Provider Mapping

| Feature | Playwright | Hyperbrowser |
|---------|-----------|--------------|
| Simple scraping | `navigate` → `snapshot` | `scrape_webpage` |
| Stealth mode | Not supported | `useStealth: true` |
| Social media | May be blocked | Recommended |
| Cost | Free | API key required |

---

## Unified Scraping Function

```javascript
function scrape_url(url, options = {}) {
  provider = get_browser_provider()

  if (provider === "hyperbrowser") {
    return mcp__hyperbrowser__scrape_webpage({
      url: url,
      outputFormat: ["markdown"],
      sessionOptions: {
        useStealth: options.stealth || false
      }
    })
  }

  // Default: Playwright
  mcp__playwright__browser_navigate({ url: url })
  mcp__playwright__browser_wait_for({ time: 3 })
  return mcp__playwright__browser_snapshot()
}
```

---

## Social Media Detection

```javascript
function requires_stealth(url) {
  const patterns = [
    /threads\.net\//,
    /instagram\.com\/p\//,
    /instagram\.com\/reel\//
  ]
  return patterns.some(p => p.test(url))
}
```

If stealth is required but Hyperbrowser is not configured, warn user and attempt with Playwright.
