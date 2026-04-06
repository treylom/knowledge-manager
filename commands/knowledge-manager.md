---
description: 지식 관리 에이전트 - 단일 에이전트 순차 처리 (Agent Teams 미지원 환경용)
allowedTools: Read, Write, Bash, Glob, Grep, mcp__obsidian__*, mcp__notion__*, mcp__playwright__*, mcp__hyperbrowser__*, WebFetch, AskUserQuestion
---

# Knowledge Manager 호출 (단일 에이전트)

> **이 명령어는 단일 에이전트가 모든 작업을 순차적으로 직접 수행합니다.**
> Agent Teams 풀스케일 버전: `/knowledge-manager-at` (tmux + .team-os 필요)
> 에이전트 정의: `.claude/agents/knowledge-manager.md` 참조
> **⚡ Karpathy Pipeline**: `km-karpathy-pipeline.md` — Linting + Filed Back + Q&A 오버레이

---

## 아키텍처

```
Main (Opus 1M, 단일 세션) — Karpathy 7-Layer Fusion
 └── Phase 0: /using-superpowers 게이트 + 환경 감지 + 모드/선호도
 └── Phase 1: DATA INGEST — 콘텐츠 추출
 └── Phase 2: EXTRA TOOLS — Vault 탐색 + GraphRAG (Mode I에서도 항상)
 └── Phase 3: COMPILE — raw→wiki 컴파일 + Q&A 양방향 [NEW]
 └── Phase 4: LINTING — /autoresearch 지식 Health Check [NEW]
 └── Phase 5: KNOWLEDGE STORE — 저장 + 연결 강화 + Cross-phase 검증
 └── Phase 6: OUTPUTS + FILED BACK — 산출 + Wiki 환류 [NEW]
```

**어디서든 동작** (tmux 없어도, Agent Teams 없어도, VS Code/SDK에서도).

---

## STEP 0: 스킬 게이트 + 환경 확인

> **⚠️ MANDATORY: 아래 두 스킬을 반드시 호출한 후 진행.**

### 0-PRE. 필수 스킬 활성화 (생략 금지)

```
MUST: Skill("/using-superpowers") 호출
  → 적용 가능 스킬 목록 식별, 작업 순서에 매핑
  → 이 호출 없이 STEP 1 이후 진행 금지

참조: km-karpathy-pipeline.md (Karpathy Pipeline 오버레이)
  → STEP 4.5에서 /autoresearch 패턴 적용 (lint 루프)
```

### 0-0. 환경 확인 (간소화)

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

### 0-1. 파이프라인 상태 초기화 (HARD GATE)

```
Bash("python3 agent-office/km-tools/km-tools.py state init")
→ JSON 응답에서 session_id 확인
→ 이후 모든 STEP 완료 시 state complete 호출 필수:
  Bash("python3 agent-office/km-tools/km-tools.py state complete STEP-N")
→ error 응답(STEP_SKIP_DETECTED) 시 즉시 중단, 누락된 STEP 실행
```

---

## STEP 0.5: 모드 감지 (Mode Detection)

**STEP 1 진행 전에 사용자 요청을 분석하여 모드를 결정합니다.**

| 사용자 표현 | 모드 |
|------------|------|
| URL, "정리해줘", "분석해줘", 외부 콘텐츠 | **Mode I** (Content Ingestion) — 기존 워크플로우 |
| "아카이브 정리", "카테고리 재편", "일괄 링크", "대규모 재편" | **Mode R** (Archive Reorganization) |
| 기존 vault 폴더 50+ 파일 지칭 | **Mode R 제안** (사용자에게 확인) |
| "그래프 구축", "GraphRAG", "지식그래프", "인사이트 분석", "커뮤니티 탐색", "그래프 업데이트", "프론트매터 동기화" | **Mode G** (GraphRAG) |

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

### Mode G 감지 시

```
사용자 요청이 Mode G에 해당합니다.
그래프 구축 모드(Mode G)로 진행할까요?

Mode G는 다음을 수행합니다:
- Phase G0: Delta 감지 (frontmatter_hash 비교, 변경 노트 확인)
- Phase G1: 온톨로지 설계 (엔티티 타입, 관계 타입 정의)
- Phase G2: 엔티티 추출 (노트 → 그래프 엔티티 변환)
- Phase G3: 관계 구축 (엔티티 간 typed 관계 생성)
- Phase G4: 커뮤니티 탐지 (클러스터링, 커뮤니티 ID 부여)
- Phase G5: 인사이트 분석 (커뮤니티 요약, 글로벌 인사이트)
- Phase G6: Frontmatter 동기화 (graph_entity/community/connections 갱신)

참조 스킬: km-graphrag-workflow.md
```

**Mode G 선택 시** → `km-graphrag-workflow.md` 스킬의 Phase G0-G6 실행. 아래 STEP 1-6 대신 Mode G 워크플로우를 따릅니다.

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

### 이미지 추출 판별 (키워드 감지 시에만 활성화)

| 사용자 표현 | image_extraction | 근거 |
|------------|-----------------|------|
| "이미지", "이미지도", "이미지 포함" | **true** (모든 콘텐츠 이미지, 최대 15개) | 명시적 요청 |
| "그래프", "차트", "다이어그램", "그래프 포함" | **auto** (차트/다이어그램만, 최대 10개) | 시각 자료 요청 |
| "텍스트만", "이미지 제외" | **false** | 명시적 제외 |
| (키워드 없음) | **false** | 기본값 — 텍스트만 추출 |

> **이미지 추출은 사용자가 관련 키워드를 명시할 때만 활성화됩니다.**
> `/knowledge-manager-at`은 항상 자동 추출합니다.
> 참조 스킬: `km-image-pipeline.md`

> **퀵 프리셋은 `/knowledge-manager-m` 전용입니다.** 이 커맨드에서는 항상 STEP 1 질문을 수행합니다.

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
| **소셜 미디어 (Threads/Instagram)** | `playwright-cli open → snapshot` ⭐ **1순위** (scrapling은 첫 포스트만 반환, SNS에서 MCP 사용 금지) |
| **일반 웹 URL** | `scrapling-crawl.py --mode dynamic` (1순위) → `--mode stealth` (2순위) → `playwright-cli` (3순위) → `WebFetch` (정적) |
| **PDF (작은)** | Read 직접 시도 (< 5MB, < 20p) |
| **PDF (큰)** | /pdf 스킬 또는 marker_single |
| **DOCX/XLSX/PPTX** | Read 또는 해당 스킬 도구 |
| **Notion URL** | mcp__notion__API-get-block-children |
| **Vault 종합 ("종합해줘")** | CLI: `"$OBSIDIAN_CLI" search` + 순차 `read` / MCP 폴백: search_vault + read_multiple_notes |

### 증분 처리 — 중복 소스 감지 + 변경점 자동 추출 (Incremental Processing)

> **Karpathy 원칙: "새 소스가 도착하면 LLM이 읽고, 핵심 정보를 추출하고, 기존 위키에 통합한다."**
> 단순히 "있는지 없는지"만 보는 게 아니라, **"뭐가 바뀌었는지"까지 자동으로 추출**해야 한다.

```
추출 완료 직후, vault에 동일 소스가 이미 존재하는지 확인:

1. 소스 감지 (3단계 탐색):
   a) URL 매칭: Grep("source: {추출된_URL}", vault_path)
   b) 제목/키워드 매칭: CLI: "$OBSIDIAN_CLI" search query="{소스 제목}" format=json
   c) 폴더 매칭: 소스명에서 프로젝트명 추출 → vault 내 동명 폴더 탐색
      (예: "CC101" → Library/Research/CC101-Guide/ 폴더 발견)

2. 판정:
   - 기존 노트 없음 → 신규 처리 (기존 흐름 계속)
   - 기존 노트 발견 → 사용자에게 질문:
     "이 소스는 이미 처리된 적이 있습니다: {기존_노트_경로}
      1) 업데이트 (변경점 추출 → 기존 노트에 반영)
      2) 새로 생성 (별도 노트로 생성)
      3) 스킵 (처리 중단)"

3. 업데이트 모드 — 변경점 자동 추출 (km-tools diff):
   a) 기존 노트를 임시 파일로 저장, 새 추출 콘텐츠도 임시 파일로 저장
   b) km-tools diff 실행:
      Bash("python3 agent-office/km-tools/km-tools.py diff {existing_tmp} {new_tmp}")
      → JSON 응답의 sections 배열: NEW/CHANGED/REMOVED/RENAMED 자동 분류
      → markdown 필드: "## 변경점 요약" 섹션 텍스트 (draft에 직접 삽입 가능)
   c) 변경점 분류 (km-tools가 자동 수행):
      - [NEW] 새로 추가된 섹션/콘텐츠
      - [CHANGED] 내용이 수정된 섹션 (유사도 점수 포함)
      - [REMOVED] 삭제된 섹션
      - [RENAMED] 이름/번호가 변경된 섹션
   d) 변경점 요약을 STEP 4로 전달 (draft에 "## 변경점 요약" 섹션 자동 생성)
```

### 추출 결과 정리

```
추출 완료 후 다음 정보를 정리:
- 제목, 저자, 날짜
- 전체 콘텐츠 (Markdown)
- 섹션 구조
- 미디어/이미지 URL
- 인용/참조
- [증분 모드 시] 기존 노트 대비 변경된 부분만 표시
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
     Grep({ pattern: "\\[\\[.*{키워드}.*\\]\\]", path: "/mnt/c/Users/treyl/Documents/Obsidian/Second_Brain" })
   - 가장 많이 참조되는 노트 = Hub 노트 (최소 2개 식별)

2. 1-hop 추적:
   - Hub 노트 Read → 내부의 모든 [[wikilink]] 추출
   - 각 링크된 노트의 제목, 태그, 첫 3줄 확인
   - CLI: `"$OBSIDIAN_CLI" read path="..."` / MCP: mcp__obsidian__read_note / Tier 3: Read

3. 2-hop 추적 (3-tier/원자적 선택 시):
   - 1-hop 노트들의 wikilink를 한 번 더 추적
   - 간접 연결 노트 목록 생성
```

### Phase A-G: GraphRAG 하이브리드 검색 (Dense + Sparse + Reranker)

> **⚡ Mode I에서도 항상 실행.** GraphRAG 검색은 Mode G 전용이 아니다.
> Karpathy 원칙: "Search/CLI tools는 모든 컴파일에 참여한다."
> DB 미존재 시에만 스킵 (graceful fallback).

```
DB_PATH=".team-os/graphrag/index/vault_graph.db"
INDEX_DIR=".team-os/graphrag/index"

IF DB 존재 (Mode I, Mode G 모두 해당):
  1. 하이브리드 검색 (Dense Embedding + FTS5 Sparse + Reranker):
     Bash("python3 .team-os/graphrag/scripts/graph_search.py hybrid '{키워드}' --top-k 20 2>/dev/null || echo '[]'")
     → JSON 결과 파싱: results[].entity, results[].source_note, results[].score, results[].source
     → 실패 시 기존 LIKE 폴백:
       Bash("python3 -c \"import sqlite3; c=sqlite3.connect('{DB_PATH}').cursor(); [print(r) for r in c.execute(\\\"SELECT name, type, description, source_note FROM entities WHERE name LIKE '%{키워드}%' OR name_ko LIKE '%{키워드}%' LIMIT 20\\\")]\"")

  2. 관계 탐색 (1-2홉):
     발견된 엔티티의 source/target 관계 조회:
     Bash("python3 -c \"import sqlite3; c=sqlite3.connect('{DB_PATH}').cursor(); [print(r) for r in c.execute(\\\"SELECT r.type, e2.name, e2.source_note FROM relationships r JOIN entities e2 ON r.target_id=e2.id WHERE r.source_id IN (SELECT id FROM entities WHERE name LIKE '%{키워드}%') LIMIT 30\\\")]\"")

  3. 커뮤니티 연관 노트:
     엔티티가 속한 커뮤니티의 다른 멤버 조회:
     Bash("python3 -c \"import sqlite3; c=sqlite3.connect('{DB_PATH}').cursor(); [print(r) for r in c.execute(\\\"SELECT DISTINCT e2.name, e2.source_note FROM entities e1 JOIN entities e2 ON e1.community_id=e2.community_id WHERE e1.name LIKE '%{키워드}%' AND e2.name!=e1.name LIMIT 15\\\")]\"")

  > sqlite3 CLI가 미설치된 환경에서도 Python sqlite3 모듈로 동작합니다.

  4. 결과를 graphrag_results에 저장 → Phase C 교차 검증에 포함

ELSE:
  → GraphRAG DB 미존재. Phase A-G 스킵.
  → 안내: "GraphRAG 빌드가 필요합니다. /km Mode G 또는 매일 20:00 자동 빌드를 기다려주세요."
```

> **Phase A-G는 Phase A(wikilink)와 병행 실행 가능.** 둘 다 읽기 전용이므로 충돌 없음.
> 하이브리드 검색이 Dense Embedding(시멘틱) + FTS5(키워드) + Reranker를 자동 결합합니다.
> embedding index 미존재 시 기존 LIKE 검색으로 graceful fallback합니다.

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
   - Library/Zettelkasten/ 하위 관련 폴더 식별
   - Library/Research/ MOC 파일 검색
   - Mine/ 하위 사용자 직접 작성 콘텐츠 검색
```

### Phase C: 교차 검증

```
3-way 교차 검증: Graph(A) ∩ GraphRAG(A-G) ∩ Retrieval(B):

- 3가지 모두 발견 → 최우선 핵심 노트 (강한 확신)
- 2가지에서 발견 → 핵심 노트 (높은 확신) → 우선 처리
- Graph(A)에만 있음 → wikilink 기반 발견 (구조적 연결) → 보조 참조
- GraphRAG(A-G)에만 있음 → 의미적 연관 발견 (엔티티/커뮤니티 기반) → 보조 참조
- Retrieval(B)에만 있음 → 고립 노트 (키워드 매칭, 연결 없음) → 링크 후보

교차 검증 결과 테이블:
| Category | Count | Notes |
|----------|-------|-------|
| Core (양쪽 발견) | N | ... |
| Graph Only | N | ... |
| Retrieval Only | N | ... |
```

---

## STEP 4: COMPILE — raw→wiki 컴파일 (draft 생성)

> **Karpathy 핵심: "raw → wiki는 컴파일이다."**
> 이 단계의 출력은 **draft** — 아직 확정이 아니다.
> draft는 STEP 4.5 Linting을 통과해야만 STEP 5에서 저장된다.

### 4-1. 콘텐츠 분석 (Compile Phase 1)

```
추출된 콘텐츠 (STEP 2) + vault 탐색 결과 (STEP 3)를 종합하여:

1. 핵심 개념 추출 및 분류
2. 사용자 선호도 반영한 깊이/초점 조정
3. 기존 vault 노트와의 관계 분석
4. [NEW] 모순 즉시 표기 (Karpathy Ingest 패턴):
   - STEP 3 교차검증 Core 노트의 핵심 주장 추출
   - 새 소스의 주장과 비교
   - 모순 발견 시 draft에 인라인 표기:
     "⚠️ 모순: 기존 [[노트명]]에서는 ~라고 했으나, 이 소스에서는 ~"
   - lint 단계를 기다리지 않고 컴파일 시점에 바로 표기
   - 참고: 이미 표기된 모순은 STEP 4.5 lint 규칙 1에서 중복 탐지하지 않음 (dedupe)
```

### 4-2. 노트 구조 설계 (Compile Phase 2)

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

### 4-5. Draft 노트 생성 (Compile Phase 3)

```
위 분석 결과를 바탕으로 draft Wiki 노트를 메모리에 생성.
(아직 Vault에 저장하지 않는다 — STEP 5에서 lint 통과 후 저장)

draft 생성 시 포함:
- YAML frontmatter (tags, author, date, source)
- 본문 (Markdown, wikilink 포함)
- Mine/ vs Library/ 경로 결정 (5-0 라우팅 규칙 사전 적용)

[증분 모드 시 필수] "## 변경점 요약" 섹션:
  이 섹션이 없으면 draft는 lint 불통과. 반드시 포함해야 한다.
  ---
  ## 변경점 요약 (vs 기존 노트)
  ### 추가된 내용 [NEW]
  - {섹션/내용}: {요약}
  ### 수정된 내용 [CHANGED]
  - {섹션}: {기존} → {변경}
  ### 삭제된 내용 [REMOVED]
  - {섹션}: (삭제됨)
  ### 구조 변경 [RENAMED/REORDERED]
  - {변경 사항}
  ---
```

### 4-6. Q&A 양방향 보강

```
컴파일된 draft에서 추가 질문을 도출하여 품질을 높인다:

1. draft에서 "아직 답하지 못한 질문" 3개 도출
   - 본문에서 언급되었으나 설명이 부족한 개념
   - 관련 주제인데 draft가 다루지 않은 영역
   - 기존 vault 노트와 연결 가능하지만 근거가 불충분한 주장

2. STEP 3 enriched_context에서 답변 탐색
   - 교차 검증 Core 노트에서 답변 검색
   - GraphRAG 커뮤니티 관련 노트에서 보강 정보 확인

3. 답변 발견 시 → draft에 반영 (본문 보강)
   답변 미발견 시 → draft에 "## Open Questions" 섹션 추가
   - Open Questions는 다음 KM 세션의 탐색 시드가 된다
```

---

## STEP 4.5: LINTING — 지식 Health Check

> **⚠️ Karpathy 핵심: "지식에도 Linting이 필요하다."**
> draft 노트의 품질을 검증하고 자동 수정하는 health check 루프.
> **lint 통과 전까지 STEP 5 저장 진행 금지.**
> 참조 스킬: `km-karpathy-pipeline.md`

### 4.5-1. Lint 규칙 6가지

```
1. Find inconsistencies (모순 탐지)
   - draft 노트 vs 기존 vault 노트 간 모순/불일치
   - 같은 개념에 대한 상충 설명, 날짜 오류, 사실관계 충돌
   - STEP 3 교차검증 Core 노트와 비교

2. Impute missing data (누락 보완)
   - frontmatter 누락 필드 (tags, author, date, source)
   - 본문에서 언급되었으나 정의되지 않은 용어
   - wikilink 대상이 vault에 존재하지 않는 경우 → forward ref 표시

3. Suggest new articles (신규 노트 제안)
   - draft가 다루지 않은 관련 주제 식별
   - "이 노트가 있으면 vault 그래프가 더 촘촘해질 것" 후보
   - Open Questions에서 파생 가능한 독립 노트 주제

4. Find connections (숨겨진 연결 발견)
   - draft와 기존 vault 노트 사이의 숨겨진 연결
   - 태그 공유, 개념 유사, 동일 GraphRAG 커뮤니티 소속
   - STEP 3 교차검증에서 "Retrieval Only"였던 고립 노트와의 연결 시도

5. Source coverage check (원문 커버리지 검증) ← LKB self-improve 패턴
   [신규 모드] 원문 키포인트 → draft 커버리지 매핑 → MISSING 보충
   [증분 모드] 원문 변경점 → 기존 노트 반영 여부 검증 → 미반영 항목 표기
   - 증분 시 "## 변경점 요약" 섹션이 draft에 없으면 → lint 실패 (HARD GATE)

6. Orphan detection (고아 페이지 탐지) ← Karpathy Lint 패턴
   - CLI: "$OBSIDIAN_CLI" orphans → 들어오는 링크(inbound) 없는 페이지 목록
   - CLI: "$OBSIDIAN_CLI" deadends → 나가는 링크(outbound) 없는 페이지 목록
   - 고아 페이지 중 draft와 관련된 것 → wikilink 연결 제안
   - 장기 고아 (30일+ 미연결) → 삭제 또는 통합 제안
   - STEP 2에서 추출한 원문의 주요 섹션/키포인트 목록 생성
   - draft의 각 섹션이 원문 키포인트를 커버하는지 매핑
   - 커버리지 매트릭스: 원문 섹션 × COVERED/MISSING
   - 미커버 포인트 → lint 이슈로 등록 → draft에 보충 또는 Open Questions로 이동
   - "원문에서 이 부분을 빠뜨렸습니다: {섹션명}" 피드백
   - 웹 소스 시: 빠뜨린 부분에 대해 WebSearch로 보충 정보 자동 탐색 (선택적)
```

### 4.5-2. lint_score 채점 (km-tools 자동 계산)

```
LLM이 3개 지표를 0.0-1.0으로 평가한 후 km-tools로 실제 계산:

Bash("python3 agent-office/km-tools/km-tools.py lint {draft_path} --consistency {X} --suggestions {Y} --coverage {Z}")

→ completeness (frontmatter 5필드) + connections (wikilink 수)는 Python이 자동 계산
→ consistency, suggestions, coverage는 LLM이 인자로 전달
→ 가중 합산: consistency×0.25 + completeness×0.20 + connections×0.20 + suggestions×0.15 + coverage×0.20
→ passed=true (≥ 0.7) 시 STEP 5 진행
→ passed=false 시 수정 후 재실행 (최대 3회)
→ LLM 인자 누락 시 해당 지표 0.0 + warnings 배열에 경고
```

### 4.5-3. Lint 반복 루프 (/autoresearch 패턴)

```
baseline = lint_score(draft)   # 초기 측정

FOR round IN 1..3:             # 최대 3회 반복 (무한루프 방지)
  IF lint_score ≥ 0.7:
    → PASS. "Lint 통과 (score={lint_score}, round={round})"
    → STEP 5로 진행
    → BREAK

  # 6가지 규칙 실행 → 문제 목록 생성
  issues = run_lint_rules(draft)

  # draft 수정 (가장 심각한 이슈부터)
  draft = fix_issues(draft, issues)

  # 재측정
  new_score = lint_score(draft)

  # /autoresearch 판정: 개선 시 keep, 악화 시 discard
  IF new_score > prev_score:
    → keep: "Lint R{round}: {prev_score} → {new_score} (+{delta})"
    prev_score = new_score
  ELSE:
    → discard: 수정 롤백, 다른 접근 시도 (keep/discard 단순 판정)
    draft = rollback(draft)

IF lint_score < 0.7 after 3 rounds:
  → lint_status = "WARN" (미통과이나 lint는 실행됨)
  → "Lint 미통과 (score={lint_score}). 최선 draft로 진행합니다."
  → STEP 5 진행 가능 (lint를 실행했으므로 게이트 통과)
  → 단, 보고서에 lint 미통과 사유 + 잔여 이슈 목록 필수 포함
```

---

## STEP 5: STORE — 노트 저장 (lint 통과된 draft만!)

**CRITICAL**: 노트 생성은 **반드시 Main이 직접** 수행합니다.
**CRITICAL**: **STEP 4.5 lint를 실행한 draft만 저장한다.** lint 미실행(스킵) 시 이 단계 진입 금지.
> lint_status가 "PASS" 또는 "WARN"이면 진행 가능. lint 자체를 실행하지 않은 경우만 차단.

### 5-PRE. Cross-phase 검증 (저장 직전 최종 확인)

```
저장 전 3가지 Cross-phase 검증 수행:

1. 제목 중복 체크:
   Grep("^# {draft_title}", vault_path) 또는
   CLI: "$OBSIDIAN_CLI" search query="{draft_title}" → 동일 제목 노트 존재 여부
   → 중복 시: 기존 노트에 append 또는 제목 변경 제안

2. 태그 일관성 체크:
   draft의 tags vs STEP 4.5에서 확정된 tags 비교
   → 불일치 시: lint 확정 태그로 교정

3. 이미지:임베딩 비율 체크 (image_extraction != false 시):
   수집된 이미지 수 vs 본문 ![[]] 임베딩 수
   → 불일치 시: 누락 임베딩 추가 또는 미사용 이미지 제거
```

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

### 5-0. 저장 경로 결정 (CRITICAL — 모든 노트 생성 전 필수!)

**Mine/ vs Library/ 라우팅**: 노트 생성 전 반드시 아래 규칙으로 경로를 결정합니다.

```
Q: "이 콘텐츠의 원저자가 tofukyung(김재경)인가?"

YES → Mine/ 하위:
  - 얼룩소 원문           → Mine/얼룩소/
  - @tofukyung Threads    → Mine/Threads/
  - 강의 자료             → Mine/Lectures/
  - 에세이/분석/에버그린  → Mine/Essays/
  - 업무 산출물 (CV 등)   → Mine/Projects/

NO → Library/ 하위 (기본):
  - YouTube/웹 정리       → Library/Zettelkasten/{적절한 주제폴더}/
  - 대규모 리서치 (3-tier) → Library/Research/{프로젝트명}/
  - 외부 Threads          → Library/Threads/
  - 학술 논문             → Library/Papers/
  - 웹 클리핑/가이드      → Library/Clippings/
  - 기타 외부 리소스      → Library/Resources/
```

**판별 시그널 (우선순위)**:
1. author 필드 = "tofukyung" 또는 "김재경" → Mine/
2. source URL에 "@tofukyung" 포함 → Mine/Threads/
3. tags에 "tofukyung" 포함 → Mine/
4. 위 해당 없음 → Library/

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

## STEP 5.5: PROPAGATE — 기존 노트 업데이트 (Karpathy Wiki Pattern)

> **Karpathy 핵심: "단일 소스가 10-15개 기존 위키 페이지를 터치한다."**
> 새 노트를 생성하는 것만으로는 지식이 복리로 쌓이지 않는다.
> 기존 노트에 새 정보를 반영해야 위키가 compounding artifact가 된다.

### 5.5-1. 핵심 엔티티/개념 추출

```
새로 저장된 draft에서 핵심 엔티티와 개념을 추출:

1. frontmatter tags에서 주요 키워드 추출
2. 본문 heading(##)에서 주제어 추출
3. wikilink 대상 노트 목록 수집
4. GraphRAG entities 테이블에서 관련 엔티티 조회 (DB 존재 시):
   Bash("python3 -c \"import sqlite3; c=sqlite3.connect('.team-os/graphrag/index/vault_graph.db').cursor(); [print(r) for r in c.execute(\\\"SELECT name, source_note FROM entities WHERE name LIKE '%{키워드}%' LIMIT 20\\\")]\"")
```

### 5.5-2. 기존 노트 업데이트 대상 식별

```
추출된 엔티티/개념으로 업데이트 대상 노트 탐색:

1. wikilink 역추적:
   Grep("\\[\\[{draft_title}\\]\\]", vault_path) → 이미 이 노트를 참조하는 기존 노트

2. 동일 태그 노트:
   CLI: "$OBSIDIAN_CLI" tags path="{관련폴더}" → 동일 태그를 가진 노트

3. GraphRAG 커뮤니티 소속 노트:
   같은 community_id를 가진 다른 엔티티의 source_note

4. MOC/인덱스 노트:
   해당 주제의 MOC에 새 노트가 아직 등록되지 않았으면 등록 대상

→ 업데이트 대상 목록 (최대 15개, 관련도순 정렬)
```

### 5.5-3. 업데이트 실행

```
FOR EACH target_note IN update_targets (최대 15개):

  1. target_note Read → 현재 내용 확인

  2. 업데이트 유형 판별:
     a) MOC/인덱스 → 새 노트 항목 추가 (append)
     b) 엔티티/개념 페이지 → "## 최근 업데이트" 또는 관련 섹션에 새 정보 추가
     c) 관련 주제 노트 → "## 관련 노트" 섹션에 wikilink 추가
     d) 모순 발견 → "⚠️ 모순" 인라인 표기 + 태그 추가

  3. 업데이트 실행:
     CLI: "$OBSIDIAN_CLI" append path="{target_path}" content="{추가 내용}"
     또는 MCP: mcp__obsidian__update_note (surgical edit 필요 시)
     또는 Write (폴백)

  4. 변경 기록:
     propagation_log에 추가: {target_note, update_type, content_added}
```

### 5.5-4. Propagation 보고

```
## Propagation 결과
- 업데이트 대상 식별: N개
- 실제 업데이트: N개
  - MOC/인덱스 등록: N건
  - 정보 추가: N건
  - wikilink 추가: N건
  - 모순 표기: N건
- 스킵 (변경 불필요): N건
```

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

### 6-2. Filed Back — 환류 (Explorations add up)

> **Karpathy 핵심: "모든 탐색은 Wiki로 환류된다."**
> 이번 세션에서 생성된 산출물과 발견을 Wiki에 축적한다.

```
1. 이번 세션 산출물 목록화:
   - 생성된 노트 목록
   - STEP 4.5 lint에서 발견된 인사이트
   - STEP 4.5-1 규칙 3 "Suggest new articles" 결과

2. 환류 실행:
   - lint 과정에서 발견된 기존 노트 오류 → 해당 노트 수정
   - "Suggest new articles" 항목 → Open Questions 노트 생성
     경로: Library/Research/{프로젝트명}/Open-Questions-{날짜}.md
   - Open Questions는 다음 KM 세션의 탐색 시드가 된다

3. 환류 노트 생성 (Open Questions가 있을 때):
   ---
   title: "Open Questions — {주제}"
   tags: [status/open, research, open-questions]
   source_session: "{날짜} KM 세션"
   ---
   ## 탐색 시드 (다음 세션용)
   - [ ] {질문 1} — 출처: {관련 draft 노트}
   - [ ] {질문 2} — 출처: {lint 규칙 3에서 제안}
   - [ ] {질문 3} — 출처: {Q&A 미답변}
```

### 6-3. 결과 보고

```
## 처리 결과 보고

### 입력 요약
- 소스: [URL/파일/vault종합]
- 모드: 단일 에이전트 순차 처리 (Karpathy Pipeline)

### Vault 탐색 결과
| 카테고리 | 수 | 비고 |
|----------|---|------|
| 핵심 노트 (교차검증) | N | Graph ∩ GraphRAG ∩ Retrieval |
| GraphRAG 연관 | N | 커뮤니티 기반 발견 |
| 관계 기반 발견 | N | Graph only |
| 키워드 매칭 | N | Retrieval only |

### Lint 결과 (STEP 4.5)
- lint_score: {score} / 1.0 (통과 기준: 0.7)
- 반복 횟수: {round}/3
- 주요 수정: [inconsistency N건, missing data N건, connections N건]

### 처리 요약
- 검색된 관련 노트: N개
- 교차 검증 핵심 노트: N개
- 생성된 노트: N개
- 추가된 양방향 링크: N개

### Filed Back (환류)
- 기존 노트 수정: N건
- Open Questions 생성: N건 → {경로}
- 다음 세션 탐색 시드: N개

### 이미지 처리 (image_extraction != false 시)
- 수집 이미지: N개
- 다운로드 성공: N개
- 임베딩 완료: N개
- 저장 경로: Resources/images/{topic-folder}/

### 출력 위치
| 노트 | 경로 | 상태 |
|------|------|------|
| [MOC명] | Research/... | 성공 |
| [Open Questions] | Research/.../Open-Questions-... | 환류 |
| ... | ... | ... |

### 파이프라인 실행 체크 (STEP 스킵 방지)
> ⚠️ 아래 체크리스트에서 미실행 STEP이 있으면 보고 전에 반드시 실행.

- [ ] STEP 2: 콘텐츠 추출 (증분 감지 포함)
- [ ] STEP 3: Vault 탐색 (GraphRAG 포함)
- [ ] STEP 4: COMPILE (draft 생성 + Q&A + 모순 표기)
- [ ] STEP 4.5: LINTING (6가지 규칙 + lint_score)
- [ ] STEP 5: STORE (Cross-phase 검증 + 저장)
- [ ] STEP 5.5: PROPAGATE (기존 노트 업데이트)
- [ ] STEP 6-1: 연결 강화 (양방향 wikilink)
- [ ] STEP 6-2: Filed Back (환류 + Open Questions)
- [ ] STEP 6-4: 엔티티 페이지 제안
- [ ] STEP 6-5: 세션 로그 (_km-log.md append)
- [ ] STEP 7: Vault 동기화
```

### 6-4. 엔티티 페이지 자동 생성 제안

> **Karpathy 패턴: log.md는 시간순, 추가 전용(append-only), grep 파싱 가능.**

```
STEP 6 결과 보고 완료 후, vault의 _km-log.md에 자동 append:

LOG_PATH = "Library/Research/_km-log.md"

# 파일 미존재 시 생성:
IF NOT Glob(vault_path + "/" + LOG_PATH):
  CLI: "$OBSIDIAN_CLI" create path="{LOG_PATH}" content="---
title: Knowledge Manager 세션 로그
type: log
tags: [km, log]
---
# KM Session Log
> 추가 전용. grep 파싱: grep '^## \[' _km-log.md | tail -10
"

# 세션 기록 append:
CLI: "$OBSIDIAN_CLI" append path="{LOG_PATH}" content="
## [{날짜}] {모드} | {소스 제목}
- 소스: {URL 또는 파일명}
- 생성: {N} notes, 업데이트: {N} notes, 링크: {N}
- lint_score: {score}, coverage: {rate}%
- propagation: {N} notes touched
- open_questions: {N}
- filed_back: {N} items
"
```

### 6-5. 세션 로그 자동 기록 (_km-log.md) — 모든 작업 완료 후 마지막

> **Karpathy 패턴: 엔티티별 전용 페이지가 있어야 새 소스마다 정보가 축적된다.**

```
STEP 5.5 Propagation 중 발견된 엔티티 중,
vault에 전용 페이지가 없는 주요 엔티티를 식별:

1. GraphRAG entities에서 centrality 상위 엔티티 추출
2. 각 엔티티에 대해 vault 노트 존재 여부 확인:
   Grep("^title:.*{entity_name}", vault_path) 또는
   CLI: "$OBSIDIAN_CLI" search query="{entity_name}" format=json limit=5

3. 전용 페이지 없는 엔티티 → 생성 제안 목록에 추가:
   "다음 엔티티에 대한 전용 페이지를 만들까요?"
   - {entity_name} (centrality: {score}, 언급 횟수: {count})

4. 사용자 승인 시 엔티티 페이지 생성:
   ---
   title: "{entity_name}"
   type: entity-page
   tags: [{관련 태그}]
   graph_entity: "{entity_id}"
   auto_generated: true
   ---
   # {entity_name}
   ## 개요 (자동 생성 — 관련 노트에서 종합)
   ## 관련 소스 (자동 누적)
   ## 연결
```

---

## STEP 7: Vault 동기화 (WSL→Windows)

**노트 생성/수정 후 반드시 실행.** WSL에서 `/mnt/c/` 경로로 직접 쓰면 Windows Obsidian이 즉시 감지하지 못할 수 있습니다.

```bash
# Obsidian vault 파일 시스템 동기화 (touch로 mtime 갱신)
find "/mnt/c/Users/treyl/Documents/Obsidian/Second_Brain" -name "*.md" -newer /tmp/.km-sync-marker -exec touch {} + 2>/dev/null

# 또는 rsync로 WSL→Windows 강제 동기화 (생성/수정된 파일만)
rsync -av --update --include="*.md" --exclude="*" \
  "/mnt/c/Users/treyl/Documents/Obsidian/Second_Brain/Library/" \
  "/mnt/c/Users/treyl/Documents/Obsidian/Second_Brain/Library/" \
  2>/dev/null || true
```

**간단 버전 (새로 생성한 파일만):**
```bash
# 생성한 노트의 mtime을 강제 갱신 → Obsidian 파일와쳐 트리거
for f in {새로 생성한 파일 경로들}; do
  touch "$f" 2>/dev/null
done
```

> 이 단계 이후 Obsidian에서 노트가 보이지 않으면 `Ctrl+R`(Obsidian 리로드) 안내.

---

## 참조 스킬 (상세 워크플로우)

| 기능 | 참조 스킬 |
|------|----------|
| **Karpathy Pipeline 오버레이** | `km-karpathy-pipeline.md` |
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
| **Mode G: GraphRAG 워크플로우** | `km-graphrag-workflow.md` |
| **Mode G: 온톨로지 설계** | `km-graphrag-ontology.md` |
| **Mode G: 그래프 검색** | `km-graphrag-search.md` |
| **Mode G: 인사이트 리포트** | `km-graphrag-report.md` |
| **Mode G: Frontmatter 동기화** | `km-graphrag-sync.md` |

---

## 사용자 요청 내용

$ARGUMENTS


## Auto-Learned Patterns

- [2026-04-04] STEP 0에 /using-superpowers 강제 게이트를 삽입해야 스킬 호출 누락을 방지할 수 있다 — 없으면 파이프라인 전체 무효화 위험 (source: 2026-04-04-1732.md)
- [2026-04-05] 증분 모드에서 소스 감지는 URL 매칭만이 아닌 3단계 탐색(URL + 제목 + 폴더)이 필요하다 — 단일 매칭 방식은 근본 결함 (source: 2026-04-05-0349.md)
- [2026-04-05] STEP 6-3 결과 보고에 파이프라인 실행 체크리스트를 포함해야 STEP 스킵을 방지할 수 있다 (source: 2026-04-05-0339.md)
