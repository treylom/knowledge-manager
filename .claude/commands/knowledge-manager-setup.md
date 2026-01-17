---
description: Knowledge Manager 셋업 위저드 - 친절한 초기 설정 가이드
allowed-tools: Read, Write, Bash, Glob, AskUserQuestion
---

# Knowledge Manager 셋업 위저드

초보자도 쉽게 따라할 수 있는 친절한 설정 가이드입니다.

---

## 실행 시작

다음 메시지를 출력하고 셋업을 시작합니다:

```
═══════════════════════════════════════════════════════════
  🧠 Knowledge Manager 셋업 위저드
═══════════════════════════════════════════════════════════

안녕하세요! Knowledge Manager를 처음 사용하시는군요.
저와 함께 차근차근 설정해봐요. 어렵지 않아요! 😊

이 에이전트는 웹페이지, 문서, 소셜 미디어 등에서
콘텐츠를 가져와서 깔끔하게 정리해드립니다.

설정할 내용:
  📁 노트 저장 위치 (어디에 정리된 노트를 저장할지)
  🔌 필요한 도구 설치 (자동으로 도와드릴게요)

예상 소요 시간: 3-5분

준비되셨나요?
```

---

## Phase 1: Obsidian 사용 여부 확인

### 사용자 질문

```
AskUserQuestion:
  question: "혹시 Obsidian을 사용하고 계신가요?"
  header: "Obsidian"
  options:
    - label: "네, 사용하고 있어요"
      description: "이미 Obsidian vault가 있어요"
    - label: "아니요, 처음 들어봐요"
      description: "Obsidian이 뭔지 모르겠어요"
    - label: "설치는 했는데 잘 몰라요"
      description: "설치만 했고 사용법을 모르겠어요"
```

---

## Phase 2-A: Obsidian 사용자 (이미 vault 있음)

### Vault 경로 확인

```
좋아요! 이미 Obsidian을 사용하고 계시군요. 👍

Obsidian vault 경로를 알려주세요.
(Obsidian 앱에서 좌측 하단 ⚙️ → 'Vault 정보' 에서 확인할 수 있어요)

예시:
  Windows: C:/Users/이름/Documents/MyVault
  Mac: /Users/이름/Documents/MyVault
```

경로 입력 후:
- 경로 존재 확인
- `.obsidian` 폴더 존재 확인 (vault 검증)

---

## Phase 2-B: Obsidian 미사용자 (처음이거나 잘 모름)

### Obsidian 소개

```
📚 Obsidian이란?

Obsidian은 메모 앱이에요!
일반 메모 앱과 다른 점은 노트들끼리 서로 연결할 수 있다는 거예요.

예를 들어:
  "AI 프롬프트" 노트에서 "GPT-5" 노트를 언급하면
  클릭 한 번으로 이동할 수 있어요.
  마치 위키피디아처럼요!

Knowledge Manager가 정리해주는 노트도
이런 식으로 서로 연결되어 있어요.

📂 Vault란?

Vault(볼트)는 그냥 "노트를 저장하는 폴더"예요.
어렵게 생각하지 마세요!

컴퓨터에 있는 아무 폴더나 Vault로 지정할 수 있어요.
Obsidian은 그 폴더 안에 있는 .md 파일들을 노트로 보여줘요.
```

### 선택지 제공

```
AskUserQuestion:
  question: "어떻게 하시겠어요?"
  header: "Setup"
  options:
    - label: "Obsidian 없이 사용할래요 (권장)"
      description: "일단 폴더만 지정하고, 나중에 Obsidian 연결해도 돼요"
    - label: "Obsidian을 설치하고 싶어요"
      description: "Obsidian 설치부터 도와드릴게요"
```

---

## Phase 2-B-1: Obsidian 없이 시작 (권장)

### 저장 폴더 지정

```
좋아요! 일단 간단하게 시작해볼게요.

노트를 저장할 폴더를 지정해주세요.
(나중에 이 폴더를 Obsidian vault로 열면 바로 사용할 수 있어요!)

💡 추천 위치:
  Windows: C:/Users/사용자이름/Documents/MyNotes
  Mac: /Users/사용자이름/Documents/MyNotes

원하는 폴더 경로를 알려주세요:
(폴더가 없으면 자동으로 만들어드릴게요)
```

폴더 생성:
```javascript
// 폴더 존재 확인
exists = Bash(`ls -la "${folderPath}" 2>/dev/null || echo "NOT_FOUND"`)

if (exists.includes("NOT_FOUND")) {
  // 폴더 생성
  Bash(`mkdir -p "${folderPath}"`)

  console.log(`
✅ 폴더를 만들었어요: ${folderPath}

이 폴더 안에 정리된 노트들이 저장될 거예요.
파일들은 .md (마크다운) 형식으로 저장돼요.
  `)
}
```

### 기본 폴더 구조 생성

```javascript
// Obsidian 스타일 폴더 구조 생성
const folders = [
  "Zettelkasten",      // 원자적 노트
  "Zettelkasten/AI-연구",
  "Zettelkasten/프로그래밍",
  "Zettelkasten/생산성",
  "Research",          // 연구 문서
  "Inbox"              // 임시 저장
]

folders.forEach(folder => {
  Bash(`mkdir -p "${folderPath}/${folder}"`)
})

console.log(`
📁 기본 폴더 구조를 만들었어요:

${folderPath}/
├── Zettelkasten/     ← 주요 노트들
│   ├── AI-연구/
│   ├── 프로그래밍/
│   └── 생산성/
├── Research/         ← 연구 문서
└── Inbox/            ← 임시 저장

나중에 폴더는 자유롭게 추가/수정하셔도 돼요!
`)
```

### Obsidian 안내 (선택적)

```
💡 나중에 Obsidian으로 보고 싶다면?

1. Obsidian 다운로드: https://obsidian.md
2. 설치 후 "Open folder as vault" 선택
3. 방금 만든 폴더 선택: ${folderPath}
4. 끝! 모든 노트가 예쁘게 보여요 ✨

지금은 건너뛰고, 나중에 해도 전혀 문제없어요.
파일들은 어차피 일반 텍스트 파일이라서요!
```

---

## Phase 2-B-2: Obsidian 설치 가이드

### 설치 안내

```
Obsidian 설치를 도와드릴게요! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 Step 1: Obsidian 다운로드
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

아래 링크에서 Obsidian을 다운로드하세요:
👉 https://obsidian.md/download

운영체제에 맞는 버전을 선택하세요:
  - Windows: .exe 파일
  - Mac: .dmg 파일
  - Linux: .AppImage 또는 .deb

설치 파일을 다운로드했으면 알려주세요!
```

```
AskUserQuestion:
  question: "Obsidian 설치가 완료됐나요?"
  header: "Install"
  options:
    - label: "네, 설치했어요!"
      description: "다음 단계로 진행할게요"
    - label: "설치 중이에요"
      description: "잠시 기다려주세요"
    - label: "나중에 할래요"
      description: "일단 폴더만 지정하고 진행할게요"
```

### Vault 생성 가이드

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Step 2: Vault(저장소) 만들기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Obsidian을 실행하세요

2. 첫 화면에서 "Create new vault" 클릭

3. Vault 이름 입력
   예: MyNotes, SecondBrain, 지식저장소 등

4. 저장 위치 선택
   💡 추천: Documents 폴더 안

5. "Create" 버튼 클릭

완료되면 vault 경로를 알려주세요!
(Obsidian 좌측 하단 ⚙️ → Vault 정보에서 확인)
```

---

## Phase 3: MCP 서버 설치 (claude mcp add 사용)

### 환경 감지

```javascript
// Claude Code CLI 환경인지 확인
const isClaudeCodeCLI = Bash(`claude --version 2>/dev/null || echo "NOT_FOUND"`)

if (isClaudeCodeCLI.includes("NOT_FOUND")) {
  // Antigravity 또는 다른 환경 → 수동 안내
  console.log(`
⚠️ Claude Code CLI가 감지되지 않았어요.
Antigravity 또는 다른 환경을 사용 중이신 것 같아요.

MCP 서버를 수동으로 설정해야 해요.
README.md의 "Antigravity 설정" 섹션을 참고해주세요.
  `)
  // Phase 4로 건너뛰기 (설정 파일만 생성)
}
```

### Playwright 설치 (필수)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 필요한 도구 설치
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Knowledge Manager가 웹페이지를 읽으려면
Playwright라는 도구가 필요해요.

이건 웹 브라우저를 자동으로 제어하는 도구예요.
(크롬이나 파이어폭스 같은 브라우저를 코드로 조종!)

설치해드릴까요?
```

```
AskUserQuestion:
  question: "Playwright MCP 서버를 설치할까요?"
  header: "Playwright"
  options:
    - label: "네, 설치해주세요 (권장)"
      description: "claude mcp add 명령어로 자동 설치"
    - label: "나중에 할게요"
      description: "웹 스크래핑 기능은 나중에 사용"
```

설치 승인 시:
```javascript
console.log(`
⏳ Playwright MCP 서버를 설치하고 있어요...
(처음이라 1-2분 정도 걸릴 수 있어요)
`)

// claude mcp add 명령어로 MCP 서버 등록
Bash(`claude mcp add playwright -s user -- npx -y @modelcontextprotocol/server-playwright`)

// 설치 확인
const mcpList = Bash(`claude mcp list`)
if (mcpList.includes("playwright")) {
  console.log(`
✅ Playwright MCP 서버 설치 완료!

이제 웹페이지에서 콘텐츠를 가져올 수 있어요.
  `)
  playwrightInstalled = true
} else {
  console.log(`
⚠️ 설치에 문제가 있었어요. 수동으로 설치해주세요:

터미널에서 실행:
  claude mcp add playwright -s user -- npx -y @modelcontextprotocol/server-playwright
  `)
}
```

### Obsidian MCP 설치 (vault 있는 경우)

vault가 설정된 경우에만:

```
AskUserQuestion:
  question: "Obsidian MCP 서버를 설치해서 vault와 연결할까요?"
  header: "Obsidian MCP"
  options:
    - label: "네, 연결해주세요 (권장)"
      description: "노트를 Obsidian vault에 직접 저장"
    - label: "아니요, 파일로 저장할게요"
      description: "일반 파일로 저장하고 나중에 연결"
```

연결 승인 시:
```javascript
console.log(`
⏳ Obsidian MCP 서버를 설치하고 있어요...
`)

// vault 경로를 환경변수로 설정하여 MCP 서버 등록
// Windows 경로는 슬래시로 변환
const normalizedPath = vaultPath.replace(/\\/g, '/')

Bash(`claude mcp add obsidian -s user -e OBSIDIAN_VAULT_PATH="${normalizedPath}" -- npx -y @huangyihe/obsidian-mcp`)

// 설치 확인
const mcpList = Bash(`claude mcp list`)
if (mcpList.includes("obsidian")) {
  console.log(`
✅ Obsidian MCP 서버 설치 완료!

이제 정리된 노트가 바로 Obsidian vault에 저장돼요.
Vault 경로: ${vaultPath}

Obsidian 앱에서 실시간으로 확인할 수 있어요! 🎉
  `)
  obsidianMcpInstalled = true
} else {
  console.log(`
⚠️ 설치에 문제가 있었어요. 수동으로 설치해주세요:

터미널에서 실행:
  claude mcp add obsidian -s user -e OBSIDIAN_VAULT_PATH="${normalizedPath}" -- npx -y @huangyihe/obsidian-mcp
  `)
}
```

### Notion MCP 설치 (선택)

```
AskUserQuestion:
  question: "Notion과도 연결하시겠어요?"
  header: "Notion"
  options:
    - label: "아니요, 괜찮아요"
      description: "Notion 없이 진행"
    - label: "네, Notion도 연결할래요"
      description: "Notion API 토큰이 필요해요"
```

Notion 연결 승인 시:
```
Notion 연결을 위해 API 토큰이 필요해요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Notion API 토큰 발급 방법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. https://www.notion.so/my-integrations 접속
2. "새 통합 만들기" 클릭
3. 이름 입력 (예: Knowledge Manager)
4. "제출" 클릭
5. "내부 통합 비밀 번호" 복사

토큰을 발급받으셨으면 알려주세요!
(형식: ntn_xxx... 또는 secret_xxx...)
```

```javascript
// 사용자가 토큰 입력 후
if (notionToken) {
  Bash(`claude mcp add notion -s user -e NOTION_TOKEN="${notionToken}" -- npx -y @notionhq/notion-mcp-server`)

  const mcpList = Bash(`claude mcp list`)
  if (mcpList.includes("notion")) {
    console.log(`✅ Notion MCP 서버 설치 완료!`)
    notionMcpInstalled = true
  }
}
```

---

## Phase 4: 설정 파일 생성

### km-config.json 생성

```javascript
const config = {
  storage: {
    primary: obsidianMcpInstalled ? "obsidian" : "local",

    obsidian: {
      enabled: obsidianMcpInstalled,
      vaultPath: vaultPath || "",
      defaultFolder: "Zettelkasten"
    },

    notion: {
      enabled: notionMcpInstalled,
      token: notionToken || ""
    },

    local: {
      enabled: true,
      outputPath: localPath || "./km-notes"
    }
  },

  browser: {
    provider: "playwright"  // 기본값: Playwright
  },

  defaults: {
    detailLevel: 2,
    connectionLevel: "normal"
  }
}

Write({
  file_path: "km-config.json",
  content: JSON.stringify(config, null, 2)
})

console.log(`
✅ 설정 파일 생성 완료: km-config.json
`)
```

### MCP 설치 현황 확인

```javascript
console.log(`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 MCP 서버 설치 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`)

// 최종 MCP 목록 확인
Bash(`claude mcp list`)
```

---

## Phase 5: 완료!

```
═══════════════════════════════════════════════════════════
  🎉 축하해요! 설정이 완료됐어요!
═══════════════════════════════════════════════════════════

📋 설정 요약

  📁 노트 저장 위치
     ${hasObsidianMcp ? "Obsidian vault: " + vaultPath : "로컬 폴더: " + localPath}

  🔌 설치된 도구
     ✅ Playwright (웹 콘텐츠 추출)
     ${hasObsidianMcp ? "✅ Obsidian 연결" : "⬜ Obsidian (나중에 연결 가능)"}

═══════════════════════════════════════════════════════════

🚀 이제 사용해보세요!

  웹페이지 정리하기:
    /knowledge-manager https://example.com/article

  PDF 문서 정리하기:
    /knowledge-manager document.pdf

═══════════════════════════════════════════════════════════

💡 팁!

  • 정리된 노트는 ${hasObsidianMcp ? "Obsidian에서" : localPath + " 폴더에서"} 확인할 수 있어요
  • "상세하게 정리해줘" 라고 하면 더 자세한 노트를 만들어요
  • 도움이 필요하면 /knowledge-manager help 라고 해보세요

═══════════════════════════════════════════════════════════

🔧 고급 옵션 (선택사항)

  소셜 미디어(Threads, Instagram) 스크래핑이 필요하다면
  Hyperbrowser를 별도로 설치할 수 있어요.

  설치 방법:
    1. https://hyperbrowser.ai 에서 API 키 발급
    2. km-config.json에서 browser.provider를 "hyperbrowser"로 변경
    3. .mcp.json에 hyperbrowser 서버 추가

═══════════════════════════════════════════════════════════
```

---

## 에러 처리

### Node.js 미설치

```
❌ Node.js가 설치되어 있지 않은 것 같아요.

MCP 도구를 설치하려면 Node.js가 필요해요.

설치 방법:
  1. https://nodejs.org 접속
  2. LTS 버전 다운로드 (왼쪽 버튼)
  3. 설치 후 터미널/명령프롬프트 재시작

설치 후 다시 시도해주세요:
  /knowledge-manager setup
```

### 경로 오류

```
❌ 입력한 경로를 찾을 수 없어요: {path}

확인해주세요:
  • 경로가 정확한가요?
  • 오타는 없나요?
  • Windows에서는 역슬래시(\) 대신 슬래시(/)를 사용해주세요

다시 입력해주세요:
```

### MCP 설치 실패

```
⚠️ 도구 설치에 문제가 생겼어요.

괜찮아요! 일단 기본 설정으로 진행하고,
나중에 다시 시도할 수 있어요.

수동 설치 방법:
  터미널에서 실행:
  npx -y @modelcontextprotocol/server-playwright

계속 진행할까요?
```

---

## 재설정

기존 설정을 덮어쓰려면:

```
AskUserQuestion:
  question: "기존 설정 파일이 발견됐어요. 어떻게 할까요?"
  header: "Existing"
  options:
    - label: "기존 설정 유지"
      description: "아무것도 변경하지 않아요"
    - label: "기존 설정 백업 후 재설정"
      description: "기존 파일을 .backup으로 저장하고 새로 설정"
    - label: "기존 설정 덮어쓰기"
      description: "기존 파일을 삭제하고 새로 설정"
```

백업 선택 시:
```javascript
// 타임스탬프 백업
const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
Bash(`mv km-config.json km-config.backup.${timestamp}.json`)
Bash(`mv .mcp.json .mcp.backup.${timestamp}.json`)
```
