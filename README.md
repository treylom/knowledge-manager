# Knowledge Manager Agent

> 📖 **English documentation is available at the bottom of this page.**

Claude Code용 종합 지식 관리 에이전트. 다양한 소스에서 콘텐츠를 수집하고, Zettelkasten 원칙에 따라 분석하여, Obsidian 또는 Notion에 저장합니다.

## ✨ 특징

- **다중 소스 입력**: 웹페이지, PDF, 소셜 미디어 (Threads/Instagram), Notion
- **YouTube 트랜스크립트**: YouTube 영상 자막 자동 추출 + 분석 + 노트 생성 ⭐ NEW
- **카카오톡 채팅 분석**: 카카오톡 채팅방 메시지를 읽고 분석 + 노트 생성 ⭐ NEW
- **PDF 및 이미지 OCR**: 스캔된 PDF와 이미지에서 텍스트 추출 (Claude Code용)
- **스마트 추출**: AI 기반 콘텐츠 분석 및 원자적 아이디어 추출
- **유연한 저장**: Obsidian, Notion, 또는 로컬 Markdown 파일
- **PPT/슬라이드 생성**: AI 이미지 기반 고퀄리티 프레젠테이션 (15+ 스타일)
- **간단한 설정**: 셋업 위저드가 모든 것을 안내
- **모바일/Remote 지원**: Claude Code Remote Control에서 키워드 기반 자동 프리셋으로 실행
- **카카오톡 전송**: 정리된 노트를 카카오톡으로 자동 전송 (Windows/WSL)
- **ntfy 완료 알림**: 작업 완료 시 모바일 푸시 알림

---

## 📱 모바일/Remote 버전 (`/knowledge-manager-m`)

Claude Code [Remote Control](https://code.claude.com/docs/en/remote-control)로 스마트폰에서 실행할 수 있는 경량 버전입니다.

### 일반 버전과의 차이

| | `/knowledge-manager` | `/knowledge-manager-m` |
|---|---|---|
| 콘텐츠 설정 | AskUserQuestion 4문항 | **키워드 자동 프리셋** |
| 카카오톡 전송 | 없음 | 지원 (선택) |
| ntfy 완료 알림 | 없음 | 지원 (선택) |
| 환경 | 데스크톱 | 모바일/Remote/headless |

### 사용 예시

```bash
# 빠른 요약
/knowledge-manager-m https://example.com 요약해줘

# 상세 분석 + 카카오 전송
/knowledge-manager-m https://example.com 꼼꼼히 카카오 나에게

# 실무용 정리
/knowledge-manager-m https://example.com 실무용
```

### 키워드 프리셋

| 키워드 | 상세 | 중점 | 분할 | 연결 |
|---|---|---|---|---|
| "요약해줘" | 요약 | 전체 균형 | 단일 | 최대 |
| "꼼꼼히" | 상세 | 전체 균형 | 원자적 | 최대 |
| "기본" | 상세 | 전체 균형 | 3-tier | 최대 |
| (키워드 없음) | 상세 | 전체 균형 | 3-tier | 최대 |

### 카카오톡 전송 설정

카카오톡 자동 전송은 [kmsg](https://github.com/channprj/kmsg)에서 영감을 받아 제작되었습니다.

| 플랫폼 | 도구 | 설치 |
|--------|------|------|
| **macOS** | [kmsg](https://github.com/channprj/kmsg) (원본) | `brew install channprj/tap/kmsg` |
| **Windows/WSL** | `send_kakao.py` (동봉) | 추가 설치 불필요 |

> **Windows/WSL**: KakaoTalk PC 버전이 실행 중이어야 합니다. `send_kakao.py`는 Win32 SendInput API로 메시지를 전송합니다.
>
> **macOS**: kmsg는 macOS용 Swift 바이너리입니다. 자세한 사용법은 [kmsg README](https://github.com/channprj/kmsg#readme)를 참고하세요.

#### km-config.json 설정

```json
{
  "kakao": {
    "enabled": true,
    "selfName": "홍길동"
  }
}
```

- `selfName`: 본인 카카오톡 채팅방 이름 (실명). **"나"가 아닌 본인 이름을 입력하세요!**
- 카카오톡 "나와의 채팅"은 본인 메시지에 대해 **푸시 알림이 울리지 않습니다.** ntfy 설정을 권장합니다.

### ntfy 완료 알림 설정

[ntfy](https://ntfy.sh/)는 무료 오픈소스 푸시 알림 서비스입니다. 작업 완료 시 스마트폰에 알림을 보냅니다.

**설정 방법 (1회):**

1. 스마트폰에 ntfy 앱 설치: [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/us/app/ntfy/id1625396347)
2. 앱에서 고유한 토픽 구독 (예: `my-km-alerts-xyz`)
3. `km-config.json`에 토픽 설정:

```json
{
  "notification": {
    "ntfyTopic": "my-km-alerts-xyz"
  }
}
```

### Claude Code Remote Control 설정 권장사항

모바일에서 Remote Control 사용 시 다음 설정을 권장합니다:

```json
// ~/.claude/settings.json
{
  "skipDangerousModePermissionPrompt": true,
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "curl -s -H 'Title: Claude 확인필요' -d '확인 필요' ntfy.sh/YOUR_TOPIC 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

- `skipDangerousModePermissionPrompt`: bypass 모드 시작 블로킹 제거
- `Notification` hook: permission 프롬프트나 idle 시 ntfy 알림
- Plan mode 자동 승인은 현재 미지원 ([GitHub #18523](https://github.com/anthropics/claude-code/issues/18523))
  - 우회: bypass 모드 사용 또는 `tmux send-keys`로 원격 승인

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

## 💡 Obsidian Vault 경로 찾기

Vault 경로를 모르시면 아래 방법으로 확인하세요.

### 방법 1: Obsidian 앱에서 확인

1. Obsidian 앱 실행
2. 좌측 하단 ⚙️ (설정) 클릭
3. **"파일 및 링크"** 메뉴 선택
4. 상단에 표시된 **"Vault 경로"** 복사

### 방법 2: AI에게 요청

Claude Code 또는 Antigravity에게 직접 물어보세요:

```
내 Obsidian vault 경로 찾는 법 알려줘
```

### OS별 일반적인 경로 예시

| OS | 경로 예시 |
|----|----------|
| **Windows** | `C:/Users/YourName/Documents/MyVault` |
| **Mac** | `/Users/YourName/Documents/MyVault` |
| **Linux** | `/home/yourname/Documents/MyVault` |

> ⚠️ **Windows 사용자**: 역슬래시(`\`) 대신 슬래시(`/`)를 사용하세요!
> - ❌ `C:\Users\...`
> - ✅ `C:/Users/...`

---

## 📋 요구사항

### 필수

| 항목 | 설명 |
|------|------|
| Claude Code / Antigravity | CLI, Desktop, 또는 Antigravity |
| Node.js 18+ | MCP 서버 실행용 |

### Playwright MCP 설치 (Claude Code 필수)

> **Antigravity 사용자**: 내장 브라우저가 있어 Playwright MCP 불필요. 이 섹션 건너뛰기.

Claude Code 환경에서 웹 콘텐츠를 추출하려면 **Playwright MCP 서버**가 필요합니다.

```bash
# Playwright MCP 자동 설치 (권장)
claude mcp add playwright -- npx -y @anthropic-ai/mcp-playwright

# 설치 확인
claude mcp list
# → playwright 서버가 표시되어야 함
```

**웹 크롤링 도구 우선순위:**

| 콘텐츠 유형 | 1순위 도구 | 2순위 (Fallback) |
|------------|-----------|------------------|
| SNS (Threads, Instagram) | Playwright MCP (필수) | - |
| 일반 웹 | WebFetch | Playwright MCP |

### YouTube 트랜스크립트 (선택)

| 항목 | 설치 명령 | 용도 |
|------|----------|------|
| youtube-transcript-api | `pip install youtube-transcript-api` | YouTube 자막 추출 (필수) |
| yt-dlp | `pip install yt-dlp` | 자막 폴백 + 메타데이터 (권장) |

### 카카오톡 채팅 분석 (선택)

| 플랫폼 | 도구 | 설치 |
|--------|------|------|
| macOS | [kmsg](https://github.com/channprj/kmsg) | `brew install channprj/tap/kmsg` |
| Windows/WSL | 대화 내보내기 TXT → 파싱 | 추가 설치 불필요 |
| (대안) | kakaotalk_msg_preprocessor | `pip install kakaotalk_msg_preprocessor` |

### 선택 (셋업 위저드가 안내)

| 항목 | 용도 |
|------|------|
| Obsidian | 로컬 지식 관리 앱 (무료) |
| Notion 계정 | 팀 협업용 |

### PDF/OCR 처리용 (Claude Code 환경)

> **Antigravity 사용자**: 자체 내장 PDF/이미지 처리 기능 사용. 아래 설치 불필요.

| 항목 | 설치 명령 | 용도 |
|------|----------|------|
| Marker | `pip install marker-pdf` | PDF → Markdown 변환 (권장) |
| pytesseract | `pip install pytesseract pdf2image` | 스캔 PDF OCR |
| Tesseract OCR | [설치 가이드](https://github.com/tesseract-ocr/tesseract) | OCR 엔진 |
| pdfplumber | `pip install pdfplumber` | 테이블 추출 |

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

# YouTube 영상 트랜스크립트 정리
/knowledge-manager https://youtube.com/watch?v=XXX

# 카카오톡 채팅방 분석 (대화 내보내기 TXT 파일)
/knowledge-manager 카톡방 "AI 오픈채팅" 이번 주 내용 정리해줘
```

### 플러그인으로 설치한 경우

```
# 셋업 위저드
/km:setup

# 웹 아티클 정리
/km https://example.com/article
```

---

## 🎨 PPT/슬라이드 생성 (NEW!)

AI 이미지 생성 기반의 고퀄리티 프레젠테이션을 만들 수 있습니다.

> 📦 **Powered by [baoyu-slide-deck](https://github.com/JimLiu/baoyu-skills)** - JimLiu의 baoyu-skills에서 제공하는 슬라이드 생성 스킬입니다.

### 사용법

```bash
# 콘텐츠에서 PPT 생성
/knowledge-manager https://example.com/article PPT로 만들어줘

# 스타일 지정
/knowledge-manager content.md sketch-notes 스타일로 슬라이드 생성

# 직접 슬라이드 생성
/baoyu-slide-deck content.md --style corporate
```

### 스타일 가이드

| 스타일 | 용도 | 추천 상황 |
|--------|------|----------|
| `sketch-notes` | 교육/튜토리얼 | 강의, 워크샵 |
| `blueprint` | 기술 문서 | 아키텍처, 시스템 설계 |
| `corporate` | 비즈니스 | 투자 발표, 경영 보고 |
| `minimal` | 미니멀 | 심플한 발표 |
| `chalkboard` | 강의실 | 교육 콘텐츠 |
| `notion` | SaaS 대시보드 | 제품 데모, B2B |

### 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--style <name>` | 비주얼 스타일 | `--style corporate` |
| `--audience <type>` | 대상 청중 | `--audience executives` |
| `--lang <code>` | 출력 언어 | `--lang ko` |
| `--slides <number>` | 슬라이드 수 | `--slides 15` |
| `--outline-only` | 아웃라인만 생성 | - |

### 출력물

```
slide-deck/{topic}/
├── outline.md           # 아웃라인
├── 01-slide-cover.png   # 개별 슬라이드 이미지
├── ...
├── {topic}.pptx         # PowerPoint 파일
└── {topic}.pdf          # PDF 파일
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

### Hyperbrowser (선택적 대안)

> ⚠️ **권장하지 않음**: 기본적으로 Playwright MCP를 사용하세요. Hyperbrowser는 Playwright가 차단당하는 특수한 경우에만 고려하세요.

Playwright MCP가 특정 사이트에서 지속적으로 차단당하는 경우에만 Hyperbrowser를 고려하세요.

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

**주의**: Hyperbrowser는 유료 서비스이며, 설정이 복잡해질 수 있습니다. 대부분의 경우 Playwright MCP로 충분합니다.

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
- **YouTube Transcripts**: Auto-extract YouTube subtitles + analyze + generate notes
- **KakaoTalk Chat Analysis**: Read and analyze KakaoTalk chat messages + generate notes
- **PDF & Image OCR**: Extract text from scanned PDFs and images (Claude Code)
- **Smart Extraction**: AI-powered content analysis and atomic idea extraction
- **Flexible Storage**: Obsidian, Notion, or local Markdown files
- **Mobile/Remote Support**: Run via Claude Code Remote Control with keyword-based auto presets
- **KakaoTalk Send**: Auto-send notes to KakaoTalk (Windows/WSL)
- **ntfy Notifications**: Mobile push notifications on task completion
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

## 💡 Finding Your Obsidian Vault Path

If you don't know your vault path, here's how to find it.

### Method 1: From Obsidian App

1. Open Obsidian app
2. Click ⚙️ (Settings) in the bottom left
3. Select **"Files & Links"**
4. Copy the **"Vault path"** shown at the top

### Method 2: Ask AI

Ask Claude Code or Antigravity directly:

```
Help me find my Obsidian vault path
```

### Typical Paths by OS

| OS | Example Path |
|----|--------------|
| **Windows** | `C:/Users/YourName/Documents/MyVault` |
| **Mac** | `/Users/YourName/Documents/MyVault` |
| **Linux** | `/home/yourname/Documents/MyVault` |

> ⚠️ **Windows users**: Use forward slashes (`/`) instead of backslashes (`\`)!
> - ❌ `C:\Users\...`
> - ✅ `C:/Users/...`

---

## Requirements

### Required

| Item | Description |
|------|-------------|
| Claude Code / Antigravity | CLI, Desktop, or Antigravity |
| Node.js 18+ | For running MCP servers |

### Playwright MCP Installation (Required for Claude Code)

> **Antigravity users**: Has built-in browser, Playwright MCP not needed. Skip this section.

To extract web content in Claude Code, you need the **Playwright MCP server**.

```bash
# Auto-install Playwright MCP (recommended)
claude mcp add playwright -- npx -y @anthropic-ai/mcp-playwright

# Verify installation
claude mcp list
# → playwright server should appear
```

**Web Crawling Tool Priority:**

| Content Type | Primary Tool | Fallback |
|--------------|-------------|----------|
| SNS (Threads, Instagram) | Playwright MCP (required) | - |
| General Web | WebFetch | Playwright MCP |

### YouTube Transcripts (Optional)

| Item | Install Command | Purpose |
|------|-----------------|---------|
| youtube-transcript-api | `pip install youtube-transcript-api` | YouTube subtitle extraction (required) |
| yt-dlp | `pip install yt-dlp` | Subtitle fallback + metadata (recommended) |

### KakaoTalk Chat Analysis (Optional)

| Platform | Tool | Install |
|----------|------|---------|
| macOS | [kmsg](https://github.com/channprj/kmsg) | `brew install channprj/tap/kmsg` |
| Windows/WSL | Chat export TXT → parsing | No additional install needed |
| (Alternative) | kakaotalk_msg_preprocessor | `pip install kakaotalk_msg_preprocessor` |

### Optional (Setup wizard will guide you)

| Item | Purpose |
|------|---------|
| Obsidian | Local knowledge management app (free) |
| Notion account | For team collaboration |

### For PDF/OCR Processing (Claude Code)

> **Antigravity users**: Use built-in PDF/image processing. No installation required.

| Item | Install Command | Purpose |
|------|-----------------|---------|
| Marker | `pip install marker-pdf` | PDF → Markdown (recommended) |
| pytesseract | `pip install pytesseract pdf2image` | Scanned PDF OCR |
| Tesseract OCR | [Install Guide](https://github.com/tesseract-ocr/tesseract) | OCR engine |
| pdfplumber | `pip install pdfplumber` | Table extraction |

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

# YouTube video transcript
/knowledge-manager https://youtube.com/watch?v=XXX

# KakaoTalk chat analysis
/knowledge-manager Analyze "AI Chat Room" messages from this week
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

### Hyperbrowser (Optional Alternative)

> ⚠️ **Not recommended**: Use Playwright MCP by default. Only consider Hyperbrowser if Playwright is consistently blocked.

Only consider Hyperbrowser if Playwright MCP is consistently blocked on specific sites.

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

**Note**: Hyperbrowser is a paid service and may add configuration complexity. Playwright MCP is sufficient for most cases.

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
- [baoyu-skills](https://github.com/JimLiu/baoyu-skills) - PPT/슬라이드 생성 스킬 원본
- [kmsg](https://github.com/channprj/kmsg) - KakaoTalk 메시지 전송 CLI (macOS)
