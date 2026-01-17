# Knowledge Manager Agent

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
/plugin marketplace add yourname/knowledge-manager

# 플러그인 설치
/plugin install knowledge-manager
```

설치 후 `/km:setup`으로 셋업 위저드를 실행하세요.

### 방법 2: 수동 복사 (Claude Code / Claude Desktop)

```bash
# 저장소 클론
git clone https://github.com/yourname/knowledge-manager.git
cd knowledge-manager

# .claude 폴더를 프로젝트에 복사
cp -r .claude /your/project/.claude
cp km-config.example.json /your/project/
```

복사 후 `/knowledge-manager setup`으로 셋업 위저드를 실행하세요.

### 방법 3: Antigravity 설정

Antigravity(Google)에서 사용하려면 MCP 서버를 수동으로 설정해야 합니다.

#### Step 1: 에이전트 파일 복사

```bash
# 저장소 클론
git clone https://github.com/yourname/knowledge-manager.git

# .claude 폴더를 Antigravity 프로젝트에 복사
cp -r knowledge-manager/.claude /your/antigravity/project/
```

#### Step 2: MCP 설정 파일 열기

1. Antigravity에서 Agent 패널 열기
2. 우측 상단 **⋯** (점 세 개) 클릭
3. **MCP Servers** 선택
4. **Manage MCP Servers** 클릭
5. **View raw config** 클릭

설정 파일 위치: `C:\Users\<사용자명>\.gemini\antigravity\mcp_config.json`

#### Step 3: MCP 서버 추가

`mcp_config.json`에 다음 내용을 추가하세요:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-playwright"]
    },
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

#### Step 4: 설정 새로고침

1. **Manage MCP Servers** 창에서 **Refresh** 클릭
2. playwright, obsidian 서버가 목록에 표시되는지 확인

#### Step 5: km-config.json 생성

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
    "provider": "playwright"
  }
}
```

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
