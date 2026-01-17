# Knowledge Manager Agent

> 📖 **English documentation is available at the bottom of this page.**

Claude Code용 종합 지식 관리 에이전트. 다양한 소스에서 콘텐츠를 수집하고, Zettelkasten 원칙에 따라 분석하여, Obsidian 또는 Notion에 저장합니다.

## ✨ 특징

- **다중 소스 입력**: 웹페이지, PDF, 소셜 미디어 (Threads/Instagram), Notion
- **스마트 추출**: AI 기반 콘텐츠 분석 및 원자적 아이디어 추출
- **유연한 저장**: Obsidian, Notion, 또는 로컬 Markdown 파일
- **간단한 설정**: 셋업 위저드가 모든 것을 안내

---

## 🚀 설치 방법

### 방법 1: Claude Code 플러그인 (권장)

Claude Code 1.0.33 이상에서 플러그인으로 설치할 수 있습니다.

```bash
# 마켓플레이스 추가
/plugin marketplace add treylom/knowledge-manager

# 플러그인 설치
/plugin install knowledge-manager
```

설치 후 `/km:setup`으로 셋업 위저드를 실행하세요.

### 방법 2: 수동 복사 (Claude Code / Claude Desktop)

```bash
# 저장소 클론
git clone https://github.com/treylom/knowledge-manager.git
cd knowledge-manager

# .claude 폴더를 프로젝트에 복사
cp -r .claude /your/project/.claude
cp km-config.example.json /your/project/
```

복사 후 `/knowledge-manager setup`으로 셋업 위저드를 실행하세요.

### 방법 3: Antigravity 설정

Antigravity(Google)는 Agent Skills 표준을 지원합니다. `.agent/skills/` 폴더를 사용하면 스킬이 자동으로 인식됩니다.

> **장점**: Antigravity는 강력한 **내장 브라우저 에이전트**가 있어서 Playwright MCP가 필요 없습니다!
> Obsidian MCP만 설정하면 됩니다.

#### Step 1: 저장소 클론 및 스킬 복사

```bash
# 저장소 클론
git clone https://github.com/treylom/knowledge-manager.git

# .agent 폴더를 프로젝트에 복사 (Antigravity 스킬)
cp -r knowledge-manager/.agent /your/antigravity/project/

# .claude 폴더도 복사 (에이전트 및 명령어)
cp -r knowledge-manager/.claude /your/antigravity/project/
```

> **참고**: `.agent/skills/` 폴더는 Antigravity, Gemini CLI, Claude Code, OpenCode 등 Agent Skills 표준을 지원하는 모든 도구에서 호환됩니다.

#### Step 2: 자동 설정 (권장)

복사 후 Antigravity에서 다음과 같이 요청하세요:

**Windows:**
```
Knowledge Manager 설정을 도와줘.
내 Obsidian vault는 C:/Users/내이름/Documents/MyVault 야.
```

**Mac:**
```
Knowledge Manager 설정을 도와줘.
내 Obsidian vault는 /Users/내이름/Documents/MyVault 야.
```

**Linux:**
```
Knowledge Manager 설정을 도와줘.
내 Obsidian vault는 /home/내이름/Documents/MyVault 야.
```

에이전트가 자동으로:
1. MCP 설정 파일에 서버 추가
   - Windows: `%USERPROFILE%\.gemini\antigravity\mcp_config.json`
   - Mac/Linux: `~/.gemini/antigravity/mcp_config.json`
2. `km-config.json` 생성
3. 설정 완료 후 Refresh 방법 안내

#### Step 2 (대안): 수동 설정

자동 설정이 작동하지 않으면 수동으로 설정할 수 있습니다.

<details>
<summary>📋 수동 설정 방법 (클릭하여 펼치기)</summary>

**MCP 서버 설정:**

1. Antigravity에서 Agent 패널 열기
2. 우측 상단 **⋯** (점 세 개) 클릭
3. **MCP Servers** 선택
4. **Manage MCP Servers** 클릭
5. **View raw config** 클릭

설정 파일 위치: `C:\Users\<사용자명>\.gemini\antigravity\mcp_config.json`

`mcp_config.json`에 다음 내용을 추가하세요:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "npx",
      "args": ["-y", "@huangyihe/obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "C:/Users/YourName/Documents/YourVault"
      }
    }
  }
}
```

> **참고**: `OBSIDIAN_VAULT_PATH`를 실제 Obsidian vault 경로로 변경하세요.
>
> **Playwright는 선택 사항입니다.** Antigravity 내장 브라우저가 웹 스크래핑을 처리합니다.
> 스크린샷 캡처, DOM 조작 등 고급 기능이 필요한 경우에만 Playwright를 추가하세요.

**설정 새로고침:**

1. **Manage MCP Servers** 창에서 **Refresh** 클릭
2. obsidian 서버가 목록에 표시되는지 확인

**km-config.json 생성:**

프로젝트 폴더에 `km-config.json` 파일을 생성하세요:

```json
{
  "storage": {
    "primary": "obsidian",
    "obsidian": {
      "enabled": true,
      "vaultPath": "C:/Users/YourName/Documents/YourVault",
      "defaultFolder": "Zettelkasten"
    },
    "local": {
      "enabled": true,
      "outputPath": "./km-notes"
    }
  },
  "browser": {
    "provider": "antigravity"
  }
}
```

</details>

#### Step 3: 설정 확인

설정이 완료되면:

1. **Manage MCP Servers** 창에서 **Refresh** 클릭
2. obsidian 서버가 목록에 표시되는지 확인
3. 테스트: "https://example.com 이 페이지를 정리해줘"

---

## 📋 요구사항

### 필수

| 항목 | 설명 |
|------|------|
| Claude Code / Antigravity | CLI, Desktop, 또는 Antigravity |
| Node.js 18+ | MCP 서버 실행용 |

### 선택 (셋업 위저드가 안내)

| 항목 | 용도 |
|------|------|
| Obsidian | 로컬 지식 관리 앱 (무료) |
| Notion 계정 | 팀 협업용 |

---

## 📖 사용법

### Claude Code에서

```
# 셋업 위저드 (최초 1회)
/knowledge-manager setup

# 웹 아티클 정리
/knowledge-manager https://example.com/article

# PDF 파일 처리
/knowledge-manager /path/to/document.pdf

# Threads 포스트 정리
/knowledge-manager https://threads.net/@user/post/123
```

### 플러그인으로 설치한 경우

```
# 셋업 위저드
/km:setup

# 웹 아티클 정리
/km https://example.com/article
```

---

## 📁 저장 방식

### Obsidian 사용자

Obsidian vault에 Zettelkasten 스타일 노트로 저장됩니다.

```
Your-Vault/
├── Zettelkasten/
│   └── AI-연구/
│       └── MCP 프로토콜 개요 - 2026-01-17.md
├── Research/
└── Threads/
```

### Obsidian 없이 사용

로컬 폴더에 Obsidian 호환 Markdown 파일로 저장됩니다.

```
km-notes/
├── Zettelkasten/
├── Research/
└── Threads/
```

---

## 🔧 문제 해결

### Claude Code: MCP 서버 상태 확인

```bash
claude mcp list
```

### Antigravity: MCP 서버 확인

1. Agent 패널 → **⋯** → **MCP Servers**
2. 서버 목록에서 playwright, obsidian 상태 확인
3. 연결 실패 시 **Refresh** 클릭

### 설정 파일 위치

| 환경 | 설정 파일 |
|------|----------|
| Claude Code CLI | 프로젝트 폴더의 `.mcp.json` |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` |
| Antigravity | `C:\Users\<사용자명>\.gemini\antigravity\mcp_config.json` |

---

## 고급 옵션

### Hyperbrowser (소셜 미디어용)

기본 Playwright가 소셜 미디어 스크래핑에서 차단당하면 Hyperbrowser 사용을 고려하세요.

1. [hyperbrowser.ai](https://hyperbrowser.ai)에서 API 키 발급
2. `km-config.json`에서 `browser.provider`를 `"hyperbrowser"`로 변경
3. MCP 설정에 hyperbrowser 서버 추가:

```json
"hyperbrowser": {
  "command": "npx",
  "args": ["-y", "hyperbrowser-mcp"],
  "env": {
    "HYPERBROWSER_API_KEY": "your-api-key"
  }
}
```

### 환경 변수 지원

```bash
export KM_OBSIDIAN_VAULT="/path/to/vault"
export KM_NOTION_TOKEN="ntn_xxx"
export KM_BROWSER_PROVIDER="playwright"
```

---

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포하세요.

## 🔗 관련 링크

- [Claude Code](https://code.claude.com)
- [Claude Code Plugins](https://claude.com/blog/claude-code-plugins)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Obsidian](https://obsidian.md)
- [Antigravity MCP 설정 가이드](https://composio.dev/blog/howto-mcp-antigravity)

---

# 🇺🇸 English Documentation

## What is Knowledge Manager?

A comprehensive knowledge management agent for Claude Code. It collects content from various sources, analyzes it using Zettelkasten principles, and saves it to Obsidian or Notion.

## Features

- **Multiple Input Sources**: Web pages, PDFs, social media (Threads/Instagram), Notion
- **Smart Extraction**: AI-powered content analysis and atomic idea extraction
- **Flexible Storage**: Obsidian, Notion, or local Markdown files
- **Easy Setup**: Setup wizard guides you through everything

---

## Installation

### Option 1: Claude Code Plugin (Recommended)

Available for Claude Code 1.0.33 and above.

```bash
# Add marketplace
/plugin marketplace add treylom/knowledge-manager

# Install plugin
/plugin install knowledge-manager
```

After installation, run `/km:setup` to start the setup wizard.

### Option 2: Manual Copy (Claude Code / Claude Desktop)

```bash
# Clone repository
git clone https://github.com/treylom/knowledge-manager.git
cd knowledge-manager

# Copy .claude folder to your project
cp -r .claude /your/project/.claude
cp km-config.example.json /your/project/
```

After copying, run `/knowledge-manager setup` to start the setup wizard.

### Option 3: Antigravity Setup

Antigravity (Google) supports the Agent Skills standard. The `.agent/skills/` folder is automatically recognized.

> **Advantage**: Antigravity has a powerful **built-in browser agent**, so Playwright MCP is not required!
> You only need to configure Obsidian MCP.

#### Step 1: Clone and Copy Skills

```bash
# Clone repository
git clone https://github.com/treylom/knowledge-manager.git

# Copy .agent folder (Antigravity skills)
cp -r knowledge-manager/.agent /your/antigravity/project/

# Also copy .claude folder (agents and commands)
cp -r knowledge-manager/.claude /your/antigravity/project/
```

> **Note**: The `.agent/skills/` folder is compatible with all tools supporting the Agent Skills standard, including Antigravity, Gemini CLI, Claude Code, and OpenCode.

#### Step 2: Automatic Setup (Recommended)

After copying, ask Antigravity:

**Windows:**
```
Help me set up Knowledge Manager.
My Obsidian vault is at C:/Users/MyName/Documents/MyVault.
```

**Mac:**
```
Help me set up Knowledge Manager.
My Obsidian vault is at /Users/MyName/Documents/MyVault.
```

**Linux:**
```
Help me set up Knowledge Manager.
My Obsidian vault is at /home/myname/Documents/MyVault.
```

The agent will automatically:
1. Add MCP servers to config file
   - Windows: `%USERPROFILE%\.gemini\antigravity\mcp_config.json`
   - Mac/Linux: `~/.gemini/antigravity/mcp_config.json`
2. Create `km-config.json`
3. Guide you to refresh the configuration

#### Step 2 (Alternative): Manual Setup

If automatic setup doesn't work, you can configure manually.

<details>
<summary>📋 Manual Setup Instructions (click to expand)</summary>

**Configure MCP Servers:**

1. Open Agent panel in Antigravity
2. Click **⋯** (three dots) in the top right
3. Select **MCP Servers**
4. Click **Manage MCP Servers**
5. Click **View raw config**

Config file location: `C:\Users\<username>\.gemini\antigravity\mcp_config.json`

Add the following to `mcp_config.json`:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "npx",
      "args": ["-y", "@huangyihe/obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "C:/Users/YourName/Documents/YourVault"
      }
    }
  }
}
```

> **Note**: Replace `OBSIDIAN_VAULT_PATH` with your actual Obsidian vault path.
>
> **Playwright is optional.** Antigravity's built-in browser handles web scraping.
> Only add Playwright if you need advanced features like screenshot capture or DOM manipulation.

**Refresh Configuration:**

1. Click **Refresh** in the Manage MCP Servers window
2. Verify that obsidian server appears in the list

**Create km-config.json:**

Create a `km-config.json` file in your project folder:

```json
{
  "storage": {
    "primary": "obsidian",
    "obsidian": {
      "enabled": true,
      "vaultPath": "C:/Users/YourName/Documents/YourVault",
      "defaultFolder": "Zettelkasten"
    },
    "local": {
      "enabled": true,
      "outputPath": "./km-notes"
    }
  },
  "browser": {
    "provider": "antigravity"
  }
}
```

</details>

#### Step 3: Verify Setup

After setup is complete:

1. Click **Refresh** in the Manage MCP Servers window
2. Verify that obsidian server appears in the list
3. Test: "Summarize this page: https://example.com"

---

## Requirements

### Required

| Item | Description |
|------|-------------|
| Claude Code / Antigravity | CLI, Desktop, or Antigravity |
| Node.js 18+ | For running MCP servers |

### Optional (Setup wizard will guide you)

| Item | Purpose |
|------|---------|
| Obsidian | Local knowledge management app (free) |
| Notion account | For team collaboration |

---

## Usage

### In Claude Code

```
# Setup wizard (first time only)
/knowledge-manager setup

# Process web article
/knowledge-manager https://example.com/article

# Process PDF file
/knowledge-manager /path/to/document.pdf

# Process Threads post
/knowledge-manager https://threads.net/@user/post/123
```

### If installed as plugin

```
# Setup wizard
/km:setup

# Process web article
/km https://example.com/article
```

---

## Storage

### For Obsidian Users

Notes are saved in Zettelkasten style in your Obsidian vault.

```
Your-Vault/
├── Zettelkasten/
│   └── AI-Research/
│       └── MCP Protocol Overview - 2026-01-17.md
├── Research/
└── Threads/
```

### Without Obsidian

Notes are saved as Obsidian-compatible Markdown files in a local folder.

```
km-notes/
├── Zettelkasten/
├── Research/
└── Threads/
```

---

## Troubleshooting

### Claude Code: Check MCP Server Status

```bash
claude mcp list
```

### Antigravity: Check MCP Servers

1. Agent panel → **⋯** → **MCP Servers**
2. Check status of playwright and obsidian in server list
3. Click **Refresh** if connection failed

### Config File Locations

| Environment | Config File |
|-------------|-------------|
| Claude Code CLI | `.mcp.json` in project folder |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` |
| Antigravity | `C:\Users\<username>\.gemini\antigravity\mcp_config.json` |

---

## Advanced Options

### Hyperbrowser (for Social Media)

If default Playwright gets blocked on social media scraping, consider using Hyperbrowser.

1. Get API key from [hyperbrowser.ai](https://hyperbrowser.ai)
2. Change `browser.provider` to `"hyperbrowser"` in `km-config.json`
3. Add hyperbrowser server to MCP config:

```json
"hyperbrowser": {
  "command": "npx",
  "args": ["-y", "hyperbrowser-mcp"],
  "env": {
    "HYPERBROWSER_API_KEY": "your-api-key"
  }
}
```

### Environment Variable Support

```bash
export KM_OBSIDIAN_VAULT="/path/to/vault"
export KM_NOTION_TOKEN="ntn_xxx"
export KM_BROWSER_PROVIDER="playwright"
```

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - Free to use, modify, and distribute.

## Related Links

- [Claude Code](https://code.claude.com)
- [Claude Code Plugins](https://claude.com/blog/claude-code-plugins)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Obsidian](https://obsidian.md)
- [Antigravity MCP Setup Guide](https://composio.dev/blog/howto-mcp-antigravity)
