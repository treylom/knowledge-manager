---
name: km-workflow
description: 6-phase workflow for content extraction, analysis, and export to Obsidian/Notion
---

# Knowledge Manager Workflow

> Complete 6-phase workflow guide for content processing

---

## Workflow Overview

```
Phase 0: Load Configuration
    ↓
Phase 1: Detect Input Source
    ↓
Phase 1.5: Collect User Preferences
    ↓
Phase 2: Extract Content
    ↓
Phase 3: Analyze Content
    ↓
Phase 4: Select Output Format
    ↓
Phase 5: Execute Export
    ↓
Phase 6: Verify and Report
```

---

## 🛑 MANDATORY WORKFLOW - 절대 건너뛰지 마세요!

**Antigravity/Gemini CLI에서 반드시 실행:**

### STEP 1: 사용자 선호도 확인 (Phase 1.5) - 필수!

콘텐츠 처리 전 **반드시** 아래 질문을 사용자에게 물어야 합니다:

```
📊 상세 수준: 1.요약 / 2.보통 / 3.상세
🎯 중점 영역: A.개념 / B.실용 / C.기술 / D.인사이트 / E.전체
📝 노트 분할: ①단일 / ②주제별 / ③원자적 / ④3-tier
🔗 연결 수준: 최소 / 보통 / 최대

기본값(3.상세, E.전체, ④3-tier, 최대)을 사용하시겠습니까?

💡 3-tier란? 개요 노트 + 주제별 노트 + 원자적 노트로 계층 구조화
```

**소셜 미디어(Threads/Instagram) URL인 경우 추가 질문:**

```
🔄 답글 수집 범위:
  1) depth=1: 직접 답글만 (빠름)
  2) depth=2: 답글의 답글까지 (더 완전한 맥락)
```

**⚠️ 이 단계를 건너뛰면 안 됩니다!**
- 사용자가 "빠르게", "기본으로" 등 퀵 프리셋 키워드를 사용한 경우만 생략 가능
- 그 외 모든 경우: 반드시 질문 후 진행

### STEP 2-0: 저장 루트·위치 결정 (Phase 3.4) - 필수! 🔴

**저장 루트는 backend 설정이 아니라 사용자가 연 프로젝트가 정한다.** ChatGPT Work 로컬 프로젝트에서는 host가 제공하는 **primary 연결 폴더**, Codex CLI에서는 대화를 시작한 작업 디렉터리, IDE에서는 선택한 workspace root를 `target_root`로 기록한다. ChatGPT 프로젝트(로컬 프로젝트 아님)는 컴퓨터 폴더에 직접 접근하지 못하므로 `target_root`를 추측하지 않는다.

우선순위: **사용자가 이번 요청에서 명시한 대상 폴더 > host가 제공한 primary project/workspace root > project-scoped 요청이 아닐 때만 `km-config.json` backend**. 사용자가 명시적으로 다른 연결 폴더나 Notion을 선택한 경우는 그 지시를 따른다.

1. **루트 확정**: `target_root = realpath(host_project_root)`로 canonicalize한다. host가 primary root와 shell cwd를 구분하면 cwd를 프로젝트 루트로 추정하지 않는다. project-scoped 요청인데 root를 확인할 수 없으면 저장을 중단하고 대상 폴더를 요청한다.
2. **구조 선독 (MUST-read)**: `${target_root}/VAULT-STRUCTURE.md`가 있으면 **경로를 정하기 전에 반드시 read**하고 그 구조(예: 직군/사업/연도/문서종류)에 맞는 폴더를 결정한다. 있으면 `${target_root}/MOC-Map.md`도 read하여 기존 허브·관련 문서 연결에 사용한다. 사용자가 경로를 지정했으면 그 지시가 우선이다. read 실패·부재 시 새 최상위 폴더를 추정 생성하지 말고, 명시 경로가 없으면 target root에 저장하고 그 fallback을 보고한다.
3. **경로 봉쇄**: `relativePath`를 정규화한 뒤 `candidate_path = realpath(parent) + filename`을 계산한다. `candidate_path`가 `target_root` 밖이면 저장하지 않는다(`..`, 절대경로, symlink escape 포함).
4. **도구는 루트 뒤에 선택**: Obsidian CLI/MCP의 실제 연결 볼트를 canonicalize하여 `target_root`와 동일하다고 확인한 때만 사용한다. 불일치·확인 불가면 파일 쓰기 도구로 target root 안에 저장한다.
5. **Provenance**: 최종 보고에 구조 문서 read 결과, `target_root`, 선택한 상대 경로, 저장 후 관측한 `actual_saved_path`를 남긴다.

**⚠️ VAULT-STRUCTURE.md 가 있는데 안 읽고 저장 = 잘못된 동작!**
**⚠️ target_root 밖(다른 볼트)에 저장 = 잘못된 동작!**

### STEP 2: Vault 검색 및 노트 연결 (Phase 3.5) - 필수!

노트 저장 전 **반드시** 관련 노트를 검색하고 연결합니다.

`MOC-Map.md`가 있으면 검색 전에 먼저 읽고, 그 안의 기존 MOC·허브를 검색어와 wikilink 후보에 반영합니다. `MOC-Map.md`는 연결 지도이며 폴더 구조 정본은 `VAULT-STRUCTURE.md`입니다.

#### Step 2-1: 관련 키워드 추출
콘텐츠에서 핵심 키워드 추출:
- 주제 키워드 (예: "AI", "프롬프트", "Claude")
- 인물/계정명 (예: "@openai", "Anthropic")
- 기술 용어 (예: "LLM", "RAG", "embedding")

#### Step 2-2: Vault 검색 실행
```javascript
keywords = ["AI", "프롬프트", "Claude"]

if (obsidian_connected_root && same_path(obsidian_connected_root, target_root)) {
  keywords.forEach(keyword => mcp_obsidian_search_vault({ query: keyword }))
} else {
  // 다른 connector vault를 검색하지 말고 target_root 안에서만 검색
  keywords.forEach(keyword => search_files({ root: target_root, query: keyword }))
}
```

#### Step 2-3: 관련 노트 읽기 및 분석
검색 결과에서 상위 노트들을 읽어 관련성 확인:
```javascript
// 검색 결과에서 상위 10개 노트 읽기. 각 path도 target_root containment 확인.
search_results.slice(0, 10).forEach(result => {
  assert(is_within(realpath(result.path), realpath(target_root)))
  read_file(result.path)
})
```

**검색·읽기도 저장과 같은 root gate를 적용합니다.** Obsidian integration/config root가 `target_root`와 다르거나 확인 불가면 그 integration으로 검색하지 않습니다.

#### Step 2-4: 연결 수준에 따른 링크 추가
**Phase 1.5에서 선택한 "🔗 연결 수준"에 따라 링크 개수 결정:**

| 연결 수준 | 링크 개수 | 설명 |
|----------|----------|------|
| **최소** | 1-2개 | 가장 관련성 높은 노트만 연결 |
| **보통** (기본값) | 3-5개 | 주요 관련 노트 연결 |
| **최대** | 5-10개 | 관련 가능성 있는 모든 노트 연결 |

#### Step 2-5: Wikilink 형식으로 노트에 추가
```markdown
## 관련 노트
- [[AI-프롬프트-기초]]
- [[Claude-사용-가이드]]
- [[LLM-활용법]]
```

**⚠️ Vault 검색 없이 저장 = 잘못된 동작!**
**⚠️ 관련 노트 발견했는데 wikilink 안 함 = 잘못된 동작!**

### STEP 3: 저장 도구 선택 (Phase 5) - 필수!

**대원칙: 파일은 STEP 2-0에서 확정한 `target_root` 안 경로에 떨어져야 한다. 도구는 그 다음 문제다.**

| 환경 | 1순위 | 조건부 | 절대 금지 |
|------|------|--------|-----------|
| ChatGPT Work / Codex | 파일 쓰기 도구(`target_root` 상대 경로) | `mcp_obsidian_create_note` — Obsidian 볼트 = `target_root`일 때만 | `target_root` 밖 저장 |
| Antigravity | `mcp_obsidian_create_note` — 볼트 = 작업 대상 볼트 확인 후 | `write_to_file` (MCP 불가 시) | 작업 대상 밖 저장 |
| Gemini CLI | `mcp_obsidian_create_note` — 볼트 = 작업 대상 볼트 확인 후 | `write_to_file` (MCP 불가 시) | 작업 대상 밖 저장 |

**⚠️ Obsidian MCP가 연결한 볼트 ≠ `target_root`인데 MCP로 저장 = 잘못된 동작!**

---

## Phase 0: Load Configuration (CRITICAL)

**Must execute before all operations**

```javascript
// 1. Resolve the host-provided project root before storage config.
target_root = resolve_host_project_root()

// 2. Config is optional for a project-scoped local file save.
config = Read("km-config.json") || {}
if (is_project_scoped_request() && !target_root) {
  return "Project root could not be verified. Ask the user to select a target folder."
}

// 3. Load storage settings
storage_config = config.storage || {}
storage = {
  primary: storage_config.primary,
  obsidian: storage_config.obsidian,
  notion: storage_config.notion,
  local: storage_config.local
}

// 4. Load browser settings
browser_config = config.browser || {}
browser = {
  provider: browser_config.provider,
  hyperbrowser: browser_config.hyperbrowser
}
```

---

## Phase 1: Detect Input Source

### Input Type Detection

| Input Pattern | Type | Processing |
|--------------|------|------------|
| `https://threads.net/*` | Social Media | → km-browser-abstraction (stealth recommended) |
| `https://instagram.com/*` | Social Media | → km-browser-abstraction (stealth recommended) |
| `https://*` | Web URL | → km-browser-abstraction |
| `*.hwp` `*.hwp3` `*.hwpx` `*.hwpml` | 한글 File | → km-content-extraction (`npx kordoc` 자동 변환) |
| `*.pdf` | PDF File | → km-content-extraction (Read 1순위) |
| `*.docx` `*.xlsx` | Office File | → km-content-extraction (anydoc 1순위) |
| 기타 로컬 파일 (`*.md` `*.txt` `*.csv` 등) | Local File | → km-content-extraction |
| `notion.so/*` | Notion Page | → Notion MCP |

---

## Phase 2: Extract Content

**입력 유형을 먼저 판정하고 라우팅한다** — 도구 호출 없이 콘텐츠 추측 금지.

### A. Local file input → Content Extraction Router

→ See `km-content-extraction` skill (로컬 문서 형식별 필수 도구 표)

핵심 규칙 요약:

| 파일 형식 | 필수 도구 |
|----------|----------|
| **한글 (HWP/HWPX)** | `npx kordoc <files> -d <outdir>` → 변환 md 를 `Read` (자동 — 사용자에게 수동 변환을 요구하지 않는다) |
| PDF | `Read` → 실패 시 km-content-extraction 의 다단 경로 |
| DOCX/XLSX | `npx -y @firecrawl/anydoc "[파일]"` → 깨지면 kordoc |
| TXT/MD/CSV/이미지 | `Read` |

### B. URL input → Browser Abstraction Layer

→ See `km-browser-abstraction` skill

```javascript
// Auto-select based on configured provider
content = scrape_url(url, {
  stealth: inputType.requiresStealth
})
```

---

## Phase 3: Analyze Content

### Apply Zettelkasten Principles

1. **Atomicity**: One idea = One note
2. **Self-contained**: Note is understandable on its own
3. **Connectivity**: Links between related concepts

---

## Phase 4-6: Export and Verify

### Use Storage Abstraction Layer

→ See `km-storage-abstraction` skill

```javascript
// Save to the already-resolved project root; config must not redirect it.
result = save_note(relativePath, content, {
  target_root: target_root,
  project_scoped: true
})

// A success response alone is insufficient.
actual_saved_path = realpath(result.path || `${target_root}/${relativePath}`)
assert(file_exists(actual_saved_path))
assert(is_within(actual_saved_path, realpath(target_root)))
```

### 노트 파일 형식 규칙 (frontmatter — 필수!)

frontmatter 가 "있는데 적용이 안 되는" 결함의 원인은 대부분 **파일 맨 앞이 `---` 가 아니어서**다. 저장하는 모든 노트에 강제:

1. **파일의 첫 줄 = `---`** — 그 앞에 빈 줄·제목·안내 문장·BOM 등 **어떤 것도 두지 않는다**. (한 글자라도 앞에 있으면 Obsidian 이 frontmatter 로 인식하지 않는다)
2. frontmatter 는 `---` … `---` 로 닫고, 내부는 유효한 YAML(탭 ❌ 스페이스 들여쓰기, 콜론 뒤 공백). **값에 콜론(`:`)·`#`·따옴표가 들어가면 값 전체를 `"…"` 로 감싼다** — 예: `title: "보고서: 8월분"` (무인용이면 파싱이 깨져 속성 전체가 미적용된다 — 실측 최다 원인).
3. 노트 전체를 ``` 코드펜스로 감싸서 저장 ❌ — 코드펜스 안의 `---` 는 frontmatter 가 아니다.
4. 저장 후 검증: 파일 첫 3바이트가 `---` 인지 확인(예: `head -c 3 <파일>`). 아니면 재저장.

### Final Report Template

```markdown
## ✅ Processing Complete!

### Input
- Source: {url or filename}
- Type: {web / file / social media}

### Saved Notes
| Title | Path | Status |
|-------|------|--------|
| {note1} | {path1} | ✅ |

### 📍 저장 위치 (Provenance — 필수!)
- 볼트(저장 루트): {저장 루트 절대 경로 또는 프로젝트 폴더명}
- 저장 경로: {볼트 기준 상대 경로 — 예: 03_통계직/2026/보도자료/노트.md}
- 실제 저장 경로: {존재 검증한 actual_saved_path}
- 적용 규칙: {VAULT-STRUCTURE.md 구조 / 사용자 지시 경로 / 기본 루트(구조 문서 없음)}
```

**⚠️ 「저장 위치」 섹션이 없는 완료 보고 = 미완성 보고!** 사용자는 이 줄로 파일이 «어떤 볼트의 어디에» 생겼는지 즉시 안다.
