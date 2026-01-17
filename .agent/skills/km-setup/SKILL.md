---
name: Knowledge Manager Setup
description: Automated setup wizard for Knowledge Manager - configures MCP servers and creates config files
---

# Knowledge Manager Setup

> Automated setup wizard that configures MCP servers and creates configuration files

---

## Overview

This skill automates the Knowledge Manager setup process:
1. Detects your environment (Antigravity, Claude Code, etc.)
2. Asks for your preferences (Obsidian vault path, etc.)
3. Automatically configures MCP servers
4. Creates km-config.json
5. Verifies the setup

---

## Setup Flow

### Step 1: Environment Detection

```javascript
function detect_environment() {
  // Check for Antigravity
  if (file_exists("~/.gemini/antigravity/mcp_config.json")) {
    return "antigravity"
  }

  // Check for Claude Code
  if (command_exists("claude")) {
    return "claude-code"
  }

  return "unknown"
}
```

### Step 2: User Preferences

Ask the user:

```
=================================================
  Knowledge Manager Setup Wizard
=================================================

Where would you like to save your notes?

  [1] Obsidian (Recommended for personal knowledge management)
  [2] Local Markdown files only
  [3] Both Obsidian and local backup

Selection: _
```

If Obsidian selected:

```
Please provide your Obsidian vault path:

Examples:
  Windows: C:/Users/YourName/Documents/MyVault
  Mac: /Users/YourName/Documents/MyVault
  Linux: /home/yourname/Documents/MyVault

Vault path: _
```

---

## Step 3: MCP Server Configuration

### For Antigravity (Simplified!)

**Antigravity has a built-in browser agent**, so playwright MCP is **optional**.
Only Obsidian MCP is required if you want to save to Obsidian.

**Config file location:** `~/.gemini/antigravity/mcp_config.json`

```javascript
function configure_antigravity_mcp(vaultPath, options = {}) {
  // 1. Read existing config
  configPath = expand_path("~/.gemini/antigravity/mcp_config.json")
  existingConfig = Read(configPath) || { "mcpServers": {} }

  // 2. Add required servers (Obsidian only for Antigravity)
  newServers = {
    "obsidian": {
      "command": "npx",
      "args": ["-y", "@huangyihe/obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": vaultPath
      }
    }
  }

  // 3. Optionally add Playwright (for screenshots, batch processing, etc.)
  if (options.includePlaywright) {
    newServers["playwright"] = {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-playwright"]
    }
  }

  // 4. Merge with existing
  existingConfig.mcpServers = {
    ...existingConfig.mcpServers,
    ...newServers
  }

  // 5. Write back
  Write(configPath, JSON.stringify(existingConfig, null, 2))

  return true
}
```

#### Antigravity Browser Options

Ask the user (only in Antigravity):

```
=================================================
  Browser Configuration
=================================================

Antigravity has a powerful built-in browser agent.
For most use cases, you don't need additional browser tools.

Do you want to add Playwright MCP? (optional)

  [1] No, use Antigravity's built-in browser (Recommended)
  [2] Yes, add Playwright for advanced features
      (screenshots, batch processing, DOM manipulation)

Selection: _
```

### For Claude Code

Claude Code doesn't have a built-in browser, so Playwright is required.

```javascript
function configure_claude_mcp(vaultPath) {
  // Use claude mcp add command
  Bash(`claude mcp add playwright -s user -- npx -y @modelcontextprotocol/server-playwright`)

  Bash(`claude mcp add obsidian -s user -e OBSIDIAN_VAULT_PATH="${vaultPath}" -- npx -y @huangyihe/obsidian-mcp`)

  return true
}
```

---

## Step 4: Create km-config.json

```javascript
function create_km_config(options) {
  config = {
    "storage": {
      "primary": options.storage || "obsidian",
      "obsidian": {
        "enabled": options.obsidianEnabled || true,
        "vaultPath": options.vaultPath,
        "defaultFolder": "Zettelkasten"
      },
      "local": {
        "enabled": options.localEnabled || true,
        "outputPath": "./km-notes"
      }
    },
    "browser": {
      // Antigravity uses native browser by default
      "provider": options.environment === "antigravity" ? "antigravity" : "playwright"
    },
    "defaults": {
      "detailLevel": 2
    }
  }

  Write("km-config.json", JSON.stringify(config, null, 2))
}
```

---

## Step 5: Verification & Next Steps

### For Antigravity

```
=================================================
  Setup Complete!
=================================================

Configuration files created:
  [OK] ~/.gemini/antigravity/mcp_config.json (updated)
  [OK] ./km-config.json (created)

MCP servers configured:
  [OK] obsidian - For saving notes to your vault

Browser configuration:
  [OK] Using Antigravity's built-in browser agent
       (No additional MCP needed!)

IMPORTANT: To activate the MCP servers:

  1. Open Antigravity
  2. Click the Agent panel
  3. Click [...] (three dots) > MCP Servers
  4. Click "Manage MCP Servers"
  5. Click "Refresh"
  6. Verify that "obsidian" appears in the list

You can now use Knowledge Manager:

  "이 페이지를 정리해줘: https://example.com/article"
  "Process this article: https://example.com/article"

=================================================
```

### For Claude Code

```
=================================================
  Setup Complete!
=================================================

Configuration:
  [OK] MCP servers added (playwright, obsidian)
  [OK] ./km-config.json created

You can now use Knowledge Manager:

  /knowledge-manager https://example.com/article

=================================================
```

---

## Troubleshooting

### MCP Server Not Appearing (Antigravity)

1. Check config file syntax:
   ```bash
   cat ~/.gemini/antigravity/mcp_config.json | python -m json.tool
   ```

2. Restart Antigravity completely (not just refresh)

3. Check for conflicting server names

### Permission Errors

If you see permission errors when writing to config:

```
The setup wizard couldn't write to the config file automatically.

Please manually add this to your mcp_config.json:

{config content here}

File location: ~/.gemini/antigravity/mcp_config.json
```

---

## Environment-Specific Notes

### Windows Paths

Use forward slashes in config files:
```
"vaultPath": "C:/Users/YourName/Documents/MyVault"
```

### Mac/Linux Paths

Standard Unix paths work:
```
"vaultPath": "/Users/yourname/Documents/MyVault"
```

### OneDrive/Cloud Sync

Cloud-synced vaults work fine:
```
"vaultPath": "C:/Users/YourName/OneDrive/Documents/MyVault"
```

---

## Summary: MCP Requirements by Environment

| Environment | Obsidian MCP | Playwright MCP | Browser |
|-------------|--------------|----------------|---------|
| **Antigravity** | Required (if using Obsidian) | Optional | Built-in |
| **Claude Code** | Required (if using Obsidian) | Required | MCP |
| **Claude Desktop** | Required (if using Obsidian) | Required | MCP |
