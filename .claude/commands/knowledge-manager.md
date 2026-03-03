---
description: 지식 관리 에이전트 - 단일 에이전트 순차 처리 (Agent Teams 미지원 환경용)
allowedTools: Read, Write, Bash, Glob, Grep, mcp__obsidian__*, mcp__notion__*, mcp__playwright__*, mcp__hyperbrowser__*, WebFetch, AskUserQuestion
---

# Knowledge Manager 호출 (단일 에이전트)

> **이 명령어는 단일 에이전트가 모든 작업을 순차적으로 직접 수행합니다.**
> Agent Teams 풀스케일 버전: `/knowledge-manager-at` (tmux + .team-os 필요)
> 에이전트 정의: `.claude/agents/knowledge-manager.md` 참조

---

## 아키텍처

```
Main (사용자 선택 모델, 단일 세션)
 └── 모든 작업을 순차적으로 직접 수행:
      1. 콘텐츠 추출
      2. Vault 그래프 탐색
      3. 키워드/태그 검색
      4. 교차 검증
      5. 노트 구조 설계
      6. 노트 생성
      7. 연결 강화
```

**어디서든 동작** (tmux 없어도, Agent Teams 없어도, VS Code/SDK에서도).

---

## STEP 0: 환경 확인 (간소화)

**사용자에게 표시할 필요 없음. 내부적으로 판단만 수행.**

### Obsidian 접근 방식 확인 (3-Tier)

```bash
OBSIDIAN_CLI="/mnt/c/Program Files/Obsidian/Obsidian.com"

# Tier 1: CLI 확인 (우선)
"$OBSIDIAN_CLI" version 2>/dev/null
→ 응답 있으면: obsidian_method = "cli"

# Tier 2: CLI 실패 시 MCP 확인
mcp__obsidian__list_notes({}) → 응답 여부
→ 응답 있으면: obsidian_method = "mcp"

# Tier 3: 둘 다 실패 시
→ obsidian_method = "filesystem"
→ Write/Read/Grep 도구로 직접 파일 저장
```

---

## STEP 0.5: 모드 감지 (Mode Detection)

**STEP 1 진행 전에 사용자 요청을 분석하여 모드를 결정합니다.**

| 사용자 표현 | 모드 |
|------------|------|
| URL, "정리해줘", "분석해줘", 외부 콘텐츠 | **Mode I** (Content Ingestion) — 기존 워크플로우 |
| "아카이브 정리", "카테고리 재편", "일괄 링크", "대규모 재편" | **Mode R** (Archive Reorganization) |
| 기존 vault 폴더 50+ 파일 지칭 | **Mode R 제안** (사용자에게 확인) |

### Mode R 감지 시

```
사용자 요청이 Mode R에 해당합니다.
대규모 vault 재편 모드(Mode R)로 진행할까요?

Mode R은 다음을 수행합니다:
- Phase R0: 사전 정리 (merge conflict, dead link, 레거시 폴더)
- Phase R1: Progressive Reading + 분석
- Phase R2: 카테고리 설계 + DA 검증
- Phase R3: 규칙서 생성 + DA 검증
- Phase R4: Python 배치 실행
- Phase R5: 검증 + 보고

참조 스킬: km-archive-reorganization.md
```

**Mode R 선택 시** → `km-archive-reorganization.md` 스킬의 Phase R0-R5 실행. 아래 STEP 1-6 대신 Mode R 워크플로우를 따릅니다.

**Mode R 추가 질문:**

```json
AskUserQuestion({
  "questions": [
    {
      "question": "재편 대상 폴더와 범위를 알려주세요.",
      "header": "대상 폴더",
      "options": [
        {"label": "특정 폴더", "description": "vault 내 특정 폴더 지정"},
        {"label": "전체 vault", "description": "vault 전체 재편"}
      ]
    },
    {
      "question": "어떤 재편을 원하시나요?",
      "header": "재편 범위",
      "options": [
        {"label": "카테고리 재분류", "description": "파일을 새 카테고리로 재배치"},
        {"label": "링크 강화", "description": "기존 구조 유지, 교차 링크만 추가"},
        {"label": "풀 재편", "description": "카테고리 + 링크 + MOC + 시리즈 전체"}
      ]
    },
    {
      "question": "매 배치 후 auto-commit 할까요?",
      "header": "Auto-commit",
      "options": [
        {"label": "예 (권장)", "description": "매 Python 배치 후 즉시 commit+push (auto-sync 경합 방지)"},
        {"label": "아니오", "description": "모든 작업 완료 후 한 번에 커밋"}
      ]
    }
  ]
})
```

**Mode I 선택 시** → 아래 STEP 1부터 기존 워크플로우 계속.

---

## STEP 1: 사용자 선호도 확인 (필수!)

**콘텐츠 처리/읽기 전에 반드시 AskUserQuestion을 호출하세요!**
**4개 질문을 한 번의 호출로 모두 물어봅니다!**

```json
AskUserQuestion({
  "questions": [
    {
      "question": "콘텐츠를 얼마나 상세하게 정리할까요?",
      "header": "상세 수준",
      "options": [
        {"label": "요약 (1-2p)", "description": "핵심만 간략히"},
        {"label": "보통 (3-5p)", "description": "주요 내용 + 약간의 설명"},
        {"label": "상세 (5p+) (권장)", "description": "모든 내용을 꼼꼼히"}
      ],
      "multiSelect": false
    },
    {
      "question": "어떤 영역에 중점을 둘까요?",
      "header": "중점 영역",
      "options": [
        {"label": "전체 균형 (권장)", "description": "모든 영역을 균형있게"},
        {"label": "개념/이론", "description": "핵심 아이디어와 원리"},
        {"label": "실용/활용", "description": "사용법, 예시, 튜토리얼"},
        {"label": "기술/코드", "description": "구현, 아키텍처, 코드"}
      ],
      "multiSelect": false
    },
    {
      "question": "노트를 어떻게 분할할까요?",
      "header": "노트 분할",
      "options": [
        {"label": "단일 노트", "description": "모든 내용을 하나의 노트에"},
        {"label": "주제별 분할", "description": "주요 주제마다 별도 노트 (MOC 포함)"},
        {"label": "원자적 분할", "description": "최대한 작은 단위로 분할 (Zettelkasten)"},
        {"label": "3-tier 계층 (권장)", "description": "메인MOC + 카테고리MOC + 원자노트"}
      ],
      "multiSelect": false
    },
    {
      "question": "기존 노트와 얼마나 연결할까요?",
      "header": "연결 수준",
      "options": [
        {"label": "최소", "description": "태그만 추가"},
        {"label": "보통", "description": "태그 + 관련 노트 링크 제안"},
        {"label": "최대 (권장)", "description": "태그 + 링크 + 기존 노트와 자동 연결 탐색"}
      ],
      "multiSelect": false
    }
  ]
})
```

> 단일 에이전트 버전에서는 RALPH/DA 관련 질문이 없습니다 (미사용).

### 이미지 추출 자동 판별 (STEP 1 이후, 질문 불필요)

| 소스 유형 | image_extraction | 근거 |
|----------|-----------------|------|
| 웹 URL (일반) | **auto** (차트/다이어그램만, 최대 10개) | 기본 활성화 |
| PDF | **auto** (차트/다이어그램만, 최대 10개) | 기본 활성화 |
| 소셜 미디어 | **false** | 미디어 별도 처리 |
| Vault 종합 | **false** | 기존 Resources/images 참조 |
| 사용자 "이미지도", "이미지 포함" | **true** (전체, 제한 없음) | 명시적 요청 |
| 사용자 "텍스트만", "이미지 제외" | **false** | 명시적 제외 |

> 참조 스킬: `km-image-pipeline.md`

### 퀵 프리셋 (사용자 키워드 감지 시 질문 스킵)

| 사용자 표현 | 프리셋 | 질문 스킵 |
|------------|--------|----------|
| "빠르게", "간단히" | 요약, 전체균형, 단일노트, 최소 | O |
| "꼼꼼히", "자세히" | 상세, 전체균형, 원자적분할, 최대 | O |
| "기본으로", "기본" | 상세, 전체균형, 3-tier, 최대 | O |
| 키워드 없음 | - | X (질문 필수) |

---

## STEP 1.5: PDF 처리 방식 확인 (PDF인 경우만!)

PDF 파일이 입력된 경우에만 이 질문을 합니다:

```json
AskUserQuestion({
  "questions": [
    {
      "question": "대용량 PDF입니까? /pdf 스킬로 처리하시겠습니까?",
      "header": "PDF 처리",
      "options": [
        {"label": "아니오 (기본)", "description": "Read로 직접 읽기 시도"},
        {"label": "예", "description": "/pdf 스킬로 전체 변환 후 처리"}
      ],
      "multiSelect": false
    }
  ]
})
```

- **"아니오"** → Read로 직접 읽기
- **"예"** → `marker_single "파일.pdf" --output_format markdown --output_dir ./km-temp`

---

## STEP 2: 콘텐츠 추출 (Main 직접)

Main이 입력 소스를 직접 추출합니다. 스킬 참조: `km-content-extraction.md`, `km-youtube-transcript.md`, `km-social-media.md`

### 소스 유형별 추출

| 입력 유형 | 추출 방법 |
|----------|----------|
| **YouTube** | `youtube-transcript-api` → `yt-dlp` 폴백 → 스킬: `km-youtube-transcript.md` |
| **소셜 미디어 (Threads/Instagram)** | `playwright-cli open → snapshot` (1순위) → `mcp__playwright__*` (fallback) |
| **일반 웹 URL** | `playwright-cli` (1순위) → `WebFetch` (fallback) → `mcp__playwright__*` |
| **PDF (작은)** | Read 직접 시도 (< 5MB, < 20p) |
| **PDF (큰)** | /pdf 스킬 또는 marker_single |
| **DOCX/XLSX/PPTX** | Read 또는 해당 스킬 도구 |
| **Notion URL** | mcp__notion__API-get-block-children |
| **Vault 종합 ("종합해줘")** | CLI: `"$OBSIDIAN_CLI" search` + 순차 `read` / MCP 폴백: search_vault + read_multiple_notes |

### 추출 결과 정리

```
추출 완료 후 다음 정보를 정리:
- 제목, 저자, 날짜
- 전체 콘텐츠 (Markdown)
- 섹션 구조
- 미디어/이미지 URL
- 인용/참조
```

### 이미지 URL 수집 (image_extraction != false 일 때)

콘텐츠 추출과 **동시에** 이미지 정보도 수집합니다:

```
1. 웹 URL: browser_snapshot에서 img/figure 요소의 src, alt, 주변 heading 수집
   - 필터링: km-image-pipeline.md 기준 (< 100x100px 제외, 광고 도메인 제외)
   - auto 모드: 차트/다이어그램만 (우선순위 1-2), 최대 10개
   - 차트/그래프 감지: canvas/SVG → browser_take_screenshot
2. PDF: marker 출력의 images/ 폴더 스캔
3. 수집 결과를 메모리에 보관 (별도 파일 불필요):
   collected_images = [
     { type: "chart", url: "...", context: "...", placement: "..." },
     ...
   ]
```

> 참조 스킬: `km-content-extraction.md` 2F, `km-image-pipeline.md`

---

## STEP 3: Vault 탐색 (Main 직접 - 순차)

### Phase A: 그래프 탐색 (graph-navigator 로직)

```
1. Hub 노트 식별:
   - Grep으로 [[키워드]] 패턴 검색
     Grep({ pattern: "\\[\\[.*{키워드}.*\\]\\]", path: "/mnt/c/Users/treyl/OneDrive/Desktop/AI/AI_Second_Brain" })
   - 가장 많이 참조되는 노트 = Hub 노트 (최소 2개 식별)

2. 1-hop 추적:
   - Hub 노트 Read → 내부의 모든 [[wikilink]] 추출
   - 각 링크된 노트의 제목, 태그, 첫 3줄 확인
   - CLI: `"$OBSIDIAN_CLI" read path="..."` / MCP: mcp__obsidian__read_note / Tier 3: Read

3. 2-hop 추적 (3-tier/원자적 선택 시):
   - 1-hop 노트들의 wikilink를 한 번 더 추적
   - 간접 연결 노트 목록 생성
```

### Phase B: 키워드 검색 (retrieval-specialist 로직)

```
1. 키워드 검색:
   - CLI: `"$OBSIDIAN_CLI" search query="{핵심 키워드}" format=json limit=20` → 파일 목록 반환
   - 컨텍스트 필요 시: MCP `mcp__obsidian__search_vault` 사용 (매칭 라인 컨텍스트 포함)
   - ⚠️ CLI `search:context`는 v1.12.4에서 불안정 (exit 255) → CLI `search` + MCP 컨텍스트로 대체
   - Grep으로 vault 전체 검색 (한국어 + 영어 키워드)
   - 결과 TOP 20 정리

2. 태그 검색:
   - CLI: `"$OBSIDIAN_CLI" tags counts sort=count format=json` → vault 전체 태그 + 빈도
   - CLI: `"$OBSIDIAN_CLI" tags path="{관련폴더}" format=json` → 폴더 한정 태그
   - Grep으로 tags: 또는 #태그 패턴 검색 (폴백)
   - 관련 태그 식별 및 해당 노트 수집

3. 폴더 기반 검색:
   - Zettelkasten/ 하위 관련 폴더 식별
   - Research/ MOC 파일 검색
```

### Phase C: 교차 검증

```
Graph 결과 ∩ Retrieval 결과:

- 양쪽 모두 발견 → 핵심 노트 (확실히 관련) → 우선 처리
- Graph에만 있음 → 관계 기반 발견 (간접 연결) → 보조 참조
- Retrieval에만 있음 → 고립 노트 (키워드 매칭, 연결 없음) → 링크 후보

교차 검증 결과 테이블:
| Category | Count | Notes |
|----------|-------|-------|
| Core (양쪽 발견) | N | ... |
| Graph Only | N | ... |
| Retrieval Only | N | ... |
```

---

## STEP 4: 콘텐츠 분석 + 노트 구조 설계

### 4-1. 콘텐츠 분석

```
추출된 콘텐츠 + vault 탐색 결과를 종합하여:

1. 핵심 개념 추출 및 분류
2. 사용자 선호도 반영한 깊이/초점 조정
3. 기존 vault 노트와의 관계 분석
```

### 4-2. 노트 구조 설계

```
사용자 선택에 따라:

단일 노트:
  → 하나의 포괄 노트 설계

주제별 분할:
  → 주요 주제마다 별도 노트 + MOC

원자적 분할:
  → 각 개념당 1개 노트 + MOC

3-tier 계층:
  → 메인MOC + 카테고리MOC + 원자노트
  → Research/[프로젝트명]/ 디렉토리 구조
```

### 4-3. 태그 추천

```
기존 vault 태그 체계 기반:
- 상태: status/open, status/resolved
- 도메인: AI-Safety, ai-agent, MCP, claude-code
- 유형: MOC, research
```

### 4-4. 시각화 기회 감지

```
프로세스 감지 → Flowchart 제안
시스템 구조 감지 → Architecture 제안
비교 데이터 → 비교 테이블 제안
```

---

## STEP 5: 노트 생성 (Main 직접!)

**CRITICAL**: 노트 생성은 **반드시 Main이 직접** 수행합니다.

### 5-1. Obsidian 노트 생성

```
# Tier 1: CLI (우선)
"$OBSIDIAN_CLI" create path="적절한/경로/파일명.md" content="YAML frontmatter + 노트 내용"

# Tier 2: MCP (CLI 실패 시)
mcp__obsidian__create_note({
  path: "적절한/경로/파일명.md",
  content: "YAML frontmatter + 노트 내용"
})

# Tier 3: Write (MCP 실패 시)
Write({ file_path: "{vault_absolute_path}/적절한/경로/파일명.md", content: "..." })
```

**경로 규칙** (CLAUDE.md 참조):
- Vault root = `AI_Second_Brain`
- 경로는 vault root 기준 상대 경로
- `AI_Second_Brain/`를 prefix로 붙이지 말 것!

### 5-2. 3-tier 구조 (해당 시)

3-tier 선택 시 다음 순서로 생성:
1. 원자적 노트들 (각 개념당 1개)
2. 카테고리 MOC (각 챕터당 1개)
3. 메인 MOC (전체 요약 + 모든 카테고리 MOC 링크)

**모든 노트에 네비게이션 푸터 포함!** (km-export-formats.md 참조)

### 5-3. 저장 검증 (필수!)

```
모든 create_note 호출 후:
1. 응답에서 "created successfully" 확인
2. Glob으로 파일 존재 확인
3. 실패 시 Write 도구로 폴백
```

### 5-4. 이미지 저장 및 임베딩 (image_extraction != false 시)

**참조 스킬**: `km-image-pipeline.md`

```
1. Resources/images/{topic-folder}/ 디렉토리 생성:
   Bash("mkdir -p /home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/")

2. 수집된 이미지 다운로드:
   웹 이미지: Bash("curl -sLo '{경로}' '{url}'")
   PDF 이미지: Bash("cp km-temp/{name}/images/{file} '{경로}'")
   실패 시: Playwright 스크린샷 폴백

3. 노트 콘텐츠에 이미지 임베드 삽입 (본문 흐름 배치!):
   - 개념 설명 → (빈 줄) → ![[Resources/images/{topic-folder}/{filename}]] → (빈 줄) → 상세 설명
   - 이미지 연속 배치 금지 (반드시 텍스트로 분리)

4. 검증:
   Glob("AI_Second_Brain/Resources/images/{topic-folder}/*") → 파일 존재 확인
```

**auto 모드 제한**: 차트/다이어그램만, 최대 10개, > 2MB 이미지 스킵

---

## STEP 6: 연결 강화 + 결과 보고

### 6-1. 연결 강화 (연결 수준 "보통" 또는 "최대"일 때)

상세 워크플로우: `km-link-strengthening.md` 참조

```
1. 새 노트 핵심 키워드 추출
2. CLI `"$OBSIDIAN_CLI" search` / MCP search_vault로 관련 노트 탐색
   - CLI `"$OBSIDIAN_CLI" deadends` → 나가는 링크 없는 파일 = 연결 강화 우선 후보 (format 옵션 미지원, 플레인 텍스트 목록 반환)
3. 관련성 점수 3점 이상인 노트와 양방향 링크 생성
4. CLI `"$OBSIDIAN_CLI" append` / MCP update_note로 기존 노트에 역방향 링크 추가
   - CLI `"$OBSIDIAN_CLI" prepend` → 네비게이션 헤더 추가 시 사용
```

### 6-2. 결과 보고

```
## 처리 결과 보고

### 입력 요약
- 소스: [URL/파일/vault종합]
- 모드: 단일 에이전트 순차 처리

### Vault 탐색 결과
| 카테고리 | 수 | 비고 |
|----------|---|------|
| 핵심 노트 (교차검증) | N | Graph ∩ Retrieval |
| 관계 기반 발견 | N | Graph only |
| 키워드 매칭 | N | Retrieval only |

### 처리 요약
- 검색된 관련 노트: N개
- 교차 검증 핵심 노트: N개
- 생성된 노트: N개
- 추가된 양방향 링크: N개

### 이미지 처리 (image_extraction != false 시)
- 수집 이미지: N개
- 다운로드 성공: N개
- 임베딩 완료: N개
- 저장 경로: Resources/images/{topic-folder}/

### 출력 위치
| 노트 | 경로 | 상태 |
|------|------|------|
| [MOC명] | Research/... | 성공 |
| ... | ... | ... |
```

---

## 참조 스킬 (상세 워크플로우)

| 기능 | 참조 스킬 |
|------|----------|
| 전체 워크플로우 | `km-workflow.md` |
| 콘텐츠 추출 | `km-content-extraction.md` |
| **YouTube 트랜스크립트** | `km-youtube-transcript.md` |
| 소셜 미디어 | `km-social-media.md` |
| 출력 형식 | `km-export-formats.md` |
| 연결 강화 | `km-link-strengthening.md` |
| 연결 감사 | `km-link-audit.md` |
| Obsidian 노트 형식 | `zettelkasten-note.md` |
| 다이어그램 | `drawio-diagram.md` |
| **이미지 파이프라인** | `km-image-pipeline.md` |
| **Mode R: 아카이브 재편** | `km-archive-reorganization.md` |
| **Mode R: 규칙 엔진** | `km-rules-engine.md` |
| **Mode R: 배치 실행** | `km-batch-python.md` |

---

## 사용자 요청 내용

$ARGUMENTS
