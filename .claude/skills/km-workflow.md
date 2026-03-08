# Knowledge Manager 워크플로우 스킬

> Knowledge Manager 에이전트의 6단계 워크플로우 정의

---

## 🚨 CRITICAL PHASES (필수 도구 호출!)

다음 Phase에서는 반드시 도구를 실제로 호출해야 합니다:

| Phase | 필수 행동 | 절대 금지 |
|-------|----------|----------|
| **Phase 2: 콘텐츠 추출** | `scrapling-crawl.py` 또는 `playwright` 도구 호출하여 실제 크롤링 | 도구 없이 추측 |
| **Phase 5: 내보내기** | `create_note` 또는 `Write` 도구 호출 | JSON만 출력 |

⚠️ **Phase 2/5에서 도구 호출 없이 다음 단계 진행 금지!**

---

## 워크플로우 개요

```
Phase 0: 환경 감지 (→ km-environment-detection.md) ⭐ NEW
    ↓
Phase 1: 입력 소스 감지
    ↓
Phase 1.5: 사용자 선호도 수집
    ↓
★ 병렬 검색 자동 구성 (복잡도 판정 → 병렬 Task 또는 Agent Teams)
    ↓
Phase 2: 콘텐츠 추출 (→ km-content-extraction.md) [병렬 실행]
    ↓
Phase 3: 콘텐츠 분석 [결과 통합]
    ↓
Phase 3.5: 시각화 기회 감지
    ↓
Phase 4: 출력 형식 선택
    ↓
Phase 5: 내보내기 실행 (→ km-export-formats.md) [Main 직접 실행]
    ↓
Phase 5.25: 이미지 저장 + 임베딩 (→ km-image-pipeline.md) [Main 직접 실행]
    ↓
Phase 5.5: 연결 강화 (→ km-link-strengthening.md) [Main 직접 실행]
    ↓
Phase 6: 검증 및 보고 [Main 통합 검증]
```

---

## Phase 0: 환경 감지 ⭐ NEW

**상세 내용**: `km-environment-detection.md` 참조

### 자동 실행 조건

| 조건 | 동작 |
|------|------|
| **첫 실행** | 전체 감지 프로세스 (스펙 → 티어 → 안내 → 활성화 제안) |
| **이후 실행** | 현재 설정 요약만 표시 (1줄) |
| **"환경 감지" 키워드** | 전체 프로세스 재실행 |

### 감지 결과가 이후 Phase에 미치는 영향

| Phase | Basic 모드 | Standard 모드 | Advanced 모드 |
|-------|-----------|--------------|---------------|
| **Phase 2** (검색) | search_vault + Grep | + Chroma 벡터 검색 | + Neo4j 그래프 순회 |
| **Phase 5.5** (연결) | 키워드 + wikilink Grep | + 벡터 유사도 추천 | + 그래프 경로 연결 |

### 병렬 검색 오케스트레이션 (환경별 자동 분기)

> **검증 결과 (2026-02-06)**: Agent Teams는 **터미널 CLI 전용** 기능입니다.
> VS Code / Claude Agent SDK 환경에서는 **병렬 Task 서브에이전트**를 사용합니다.
> 두 방식 모두 병렬 실행으로 속도 향상을 제공하며, 환경에 따라 자동 분기합니다.

**상세 환경 설정**: `km-environment-detection.md` Phase 5 참조

#### 환경별 실행 모드 (자동 감지)

| 환경 | 실행 모드 | 병렬화 방법 | 쓰기 안전성 |
|------|----------|-----------|-----------|
| **터미널 CLI** (`claude` interactive) | Agent Teams | Teammate 생성 + Mailbox 통신 | 안전 (독립 인스턴스) |
| **VS Code / SDK** | 병렬 Task 서브에이전트 | Task 도구 병렬 호출 | 읽기만 위임, **쓰기는 Main** |

```
감지 로직:
  IF 터미널 CLI interactive 모드:
    → Agent Teams 사용 (Teammate 생성)
  ELSE (VS Code, SDK, Task 도구 내부):
    → 병렬 Task 서브에이전트 사용
```

#### 작업 복잡도 판정 (Phase 1 완료 후)

| 복잡도 | 트리거 | 병렬화 수준 |
|--------|--------|-----------|
| **Simple** | 단일 URL/파일 → 단일 노트 (①) | 병렬화 **스킵** (단일 에이전트) |
| **Standard** | 다중 소스 또는 주제별 분할 (②) | **2개** 병렬 검색 (Wikilink + Keyword) |
| **Complex** | 종합/연구보고서/3-tier (③④), Vault Synthesis | **3개** 병렬 검색 (Wikilink + Keyword + Hub/추출) |

**자동 판정 로직:**
```
복잡도 = Simple (기본값)

IF 사용자 선택 = ③ 원자적 분할 OR ④ 3-tier:
    복잡도 = Complex
ELIF 사용자 선택 = ② 주제별 분할:
    복잡도 = Standard
ELIF 입력 소스 = "종합" 키워드 OR Vault Synthesis:
    복잡도 = Complex
ELIF 입력 소스가 2개 이상:
    복잡도 = Standard
```

#### GraphRAG 근사 팀 구성 (핵심 설계)

> **Agent Teams / 병렬 Task의 진짜 힘 = 단순 검색 병렬이 아닌, GraphRAG 파이프라인 근사**
> Neo4j/Chroma 없이도 병렬 에이전트로 Graph + Retrieval + Augmented Generation을 수행합니다.

```
GraphRAG = Graph traversal + Retrieval + Augmented Generation

병렬 에이전트로 근사:
  Graph     → @graph-navigator가 wikilink 체인 2-hop 추적
  Retrieval → @retrieval-specialist가 키워드+태그 넓은 검색
  Augmented → @deep-reader가 핵심 노트 깊이 읽기 + 요약
  Generation → Main이 교차 검증 후 종합 보고서 작성
```

##### 팀 구성 (3 에이전트 + Main)

```
Main Agent (Coordinator + Generator)
    │
    ├── @graph-navigator
    │   역할: Hub 노트 → wikilink 체인 2-hop 추적 → 관계 그래프 구축
    │   방법:
    │     1. Grep [[.*주제.*]] → Hub 노트 식별 (참조 횟수 TOP 5)
    │     2. Hub 노트를 Read → 내부 wikilinks 추출 (1-hop)
    │     3. 1-hop 노트를 Read → 내부 wikilinks 추출 (2-hop)
    │     4. 관계 맵 텍스트 생성: Hub → 1-hop → 2-hop (엣지 + 노드)
    │   출력: 노드 목록 + 엣지 목록 + Hub별 연결 구조
    │
    ├── @retrieval-specialist
    │   역할: 키워드 + 태그 + 폴더 기반 넓은 검색 → 고립 노트 발견
    │   방법:
    │     1. 핵심 키워드 5-7개로 vault 전체 Grep/search_vault
    │     2. 관련 태그 검색 (frontmatter tags)
    │     3. CLAUDE.md 네비게이션 맵 기반 관련 폴더 탐색
    │     4. Graph에서 안 잡히는 "고립 노트" 식별 (연결 없지만 관련)
    │   출력: 관련 파일 TOP 20 (관련성 점수 + 매칭 키워드)
    │
    └── @deep-reader
        역할: 핵심 노트 실제 읽기 + 내용 요약 + 간극 분석
        방법:
          1. Hub TOP 5~7 노트를 실제로 Read (전문 읽기)
          2. 각 노트의 핵심 주장 / 개념 / 인사이트 추출
          3. 노트 간 공통점 / 차이점 / 대립점 비교
          4. 지식 간극(gap) 식별: "다뤄지지 않은 영역"
        출력: 노트별 요약 + 교차 비교 + 간극 보고
```

##### 복잡도별 팀 규모

| 복잡도 | 에이전트 수 | 구성 |
|--------|-----------|------|
| **Simple** | 0 | Main 단독 (순차 검색) |
| **Standard** | 2 | graph-navigator + retrieval-specialist |
| **Complex** | 3 | graph-navigator + retrieval-specialist + deep-reader |

##### Main의 역할: 교차 검증 + Generation

```
Main Agent:
  1. 3 에이전트 결과 수집 (병렬 완료 후)
  2. Graph ∩ Retrieval 교차 검증:
     - 양쪽 모두 발견 → 핵심 노트 (확실히 관련)
     - Graph에만 있음 → 관계 기반 발견 (간접 연결된 노트)
     - Retrieval에만 있음 → 고립 노트 (키워드는 매칭되지만 연결 없음)
  3. Deep Reader 요약으로 보고서 구조 설계
  4. 노트 생성 (Main 직접 — 쓰기는 위임하지 않음)
  5. 연결 강화 (Main 직접 실행)
```

---

#### 모드 A: 병렬 Task 서브에이전트 (VS Code / SDK)

> VS Code 환경의 **기본 실행 모드**. 위 GraphRAG 근사 패턴을 Task 도구로 구현합니다.

##### 실제 호출 패턴

```
# Phase 2 시작 시, 아래를 **하나의 메시지에서 병렬** 호출:

Task 1 (@graph-navigator):
  subagent_type: "Explore"
  model: "sonnet"
  prompt: |
    vault에서 '{주제}' 관련 wikilink 그래프 탐색:
    1. CLI backlinks로 Hub 노트 식별:
       Bash: "/mnt/c/Program Files/Obsidian/Obsidian.com" backlinks path="{주제관련노트}" format=json
       CLI 실패 시: Grep [[.*{주제}.*]] → Hub 노트 TOP 5 식별
    2. 각 Hub 노트의 wikilinks 추출 (1-hop):
       Bash: "/mnt/c/Program Files/Obsidian/Obsidian.com" links path="{hub노트}"
       CLI 실패 시: Read로 노트 내용 확인 후 wikilink 파싱
    3. 1-hop 노트의 wikilinks 추출 (2-hop)
    4. 관계 그래프를 텍스트로 정리: 노드 목록 + 엣지 목록

Task 2 (@retrieval-specialist):
  subagent_type: "Explore"
  model: "sonnet"
  prompt: |
    vault에서 '{주제}' 키워드+태그+폴더 기반 넓은 검색:
    1. CLI search로 vault 전체 검색:
       Bash: "/mnt/c/Program Files/Obsidian/Obsidian.com" search query="{키워드}" format=json
       CLI 실패 시: mcp__obsidian__search_vault 또는 Grep 사용
    2. 관련 태그 검색, 관련 폴더 탐색
    3. 관련 파일 TOP 20을 관련성 순으로 정리
    4. Graph에서 안 잡히는 "고립 노트" 별도 표시

Task 3 (@deep-reader — Complex만):
  subagent_type: "Explore"
  model: "sonnet"  (깊은 분석 필요 시 "opus")
  prompt: |
    Hub 노트 TOP 5~7을 실제로 Read하고:
    1. 각 노트 핵심 내용 요약 (3-5줄)
    2. 노트 간 공통/차이/대립 분석
    3. 다뤄지지 않은 영역(지식 간극) 식별
```

##### 필수 규칙

```
□ 모든 Task를 하나의 메시지에서 병렬 호출 (순차 X)
□ Task 서브에이전트는 읽기(Explore)만 수행
□ 쓰기(create_note, update_note, Write)는 반드시 Main이 직접 실행
□ Task 결과를 Main이 수집 → 교차 검증 → Main이 노트 생성
```

---

#### 모드 B: Agent Teams (터미널 CLI 전용)

> **터미널 CLI**에서 동일한 GraphRAG 근사 패턴을 Agent Teams로 실행합니다.
> Teammate는 독립 인스턴스 — Mailbox 통신 + 쓰기 가능.

##### 터미널 CLI 프롬프트 예시

```
사용자 → Claude (터미널):
"'{주제}'에 대해 vault를 GraphRAG 방식으로 조사해줘:

Agent Team 구성:
  @graph-navigator: [[{주제}]] 관련 wikilink를 2-hop까지 추적하고 관계 그래프 만들어줘
  @retrieval-specialist: 키워드+태그로 넓게 검색하고, 그래프에 없는 고립 노트도 찾아줘
  @deep-reader: 가장 많이 참조되는 Hub 노트 TOP 5를 읽고 핵심 내용 + 간극 분석해줘

결과를 교차 검증하고 종합 보고서로 작성해줘."
```

##### Teammate 모델 선택

```
기본: Sonnet (비용 효율)
에스컬레이션 → Opus:
  - deep-reader가 논문 수준 비교 분석 필요 시
  - 3-tier Tier 1 MOC 작성 시
```

##### Agent Teams 제한사항

- **터미널 CLI 전용** — VS Code, SDK에서 미동작 (2026-02-06 검증)
- Research Preview (실험 기능)
- 세션 복원(/resume) 시 Teammate 소실 → 재생성 필요
- 1 세션 = 1 팀만 가능

---

#### Phase별 역할 배분

| Phase | 단일 에이전트 | 병렬 (VS Code / CLI) |
|-------|-------------|---------------------|
| **Phase 2: Graph** | Main 순차 | @graph-navigator (2-hop 추적) |
| **Phase 2: Retrieval** | Main 순차 | @retrieval-specialist (넓은 검색) |
| **Phase 2: Read** | Main 순차 | @deep-reader (노트 요약) |
| **Phase 3: 분석** | Main | Main (교차 검증 + 종합) |
| **Phase 5: 쓰기** | Main | **Main 직접** (VS Code) / Main or Teammate (CLI) |
| **Phase 5.25: 이미지** | Main | **Main 직접** (모든 모드) |
| **Phase 5.5: 링크** | Main | **Main 직접** (VS Code) / Main or Teammate (CLI) |
| **Phase 6: 검증** | Main | Main (집계) |

#### Fallback (병렬화 불가 시)

```
병렬 에이전트 생성 실패 시:
  → Main이 순차적으로 Graph → Retrieval → Read 수행
  → 기능적으로 동일한 GraphRAG 근사, 속도만 1x
```

### Vault 구조 참조 규칙

**CRITICAL**: vault 탐색 시 반드시 다음 순서를 따릅니다:
1. CLAUDE.md의 "Vault 구조 네비게이션 맵" 섹션을 먼저 참조
2. 관련 폴더/태그를 파악한 후 targeted 검색
3. CLI backlinks/links로 기존 관계 먼저 확인:
   ```bash
   "/mnt/c/Program Files/Obsidian/Obsidian.com" backlinks path="{노트}" format=json
   "/mnt/c/Program Files/Obsidian/Obsidian.com" links path="{노트}"
   ```
   CLI 실패 시: Wikilink Grep 패턴(`\[\[키워드\]\]`)으로 기존 관계 확인
4. 그 후 키워드 검색으로 보완

---

## Phase 1: 입력 소스 감지

사용자 입력을 분석하여 소스 유형을 결정합니다.

### 입력 유형 분류

```
User input analysis:
├─ URL (http/https)
│   ├─ threads.net/* → 소셜 미디어 (→ km-social-media.md) ⭐
│   ├─ instagram.com/p/* → 소셜 미디어 (→ km-social-media.md) ⭐
│   ├─ instagram.com/reel/* → 소셜 미디어 (→ km-social-media.md) ⭐
│   ├─ notion.so/* → Notion Import
│   └─ 기타 URL → Web Crawling (playwright MCP)
│
├─ File path
│   ├─ .pdf → PDF Processing (Marker 우선)
│   ├─ .docx, .doc → Word Processing
│   ├─ .xlsx, .xls, .csv → Excel Processing
│   ├─ .pptx, .ppt → PowerPoint Processing
│   ├─ .txt, .md → Text Processing
│   └─ .png, .jpg, .jpeg → Image Analysis
│
├─ "Notion:" prefix 또는 Notion URL → Notion Import
│
├─ 종합 키워드 (NEW!)
│   - "종합해줘", "인사이트", "synthesize"
│   - 주제 키워드 + "정리", "분석", "트렌드"
│   → Vault Synthesis (기존 노트 종합)
│
└─ 일반 텍스트 → Direct Text Processing
```

### 소셜 미디어 URL 자동 감지 규칙

**CRITICAL**: 다음 패턴 감지 시 자동으로 playwright MCP 사용

```python
social_media_patterns = [
    "threads.net/",        # Threads 모든 URL
    "instagram.com/p/",    # Instagram 포스트
    "instagram.com/reel/", # Instagram 릴스
    "instagram.com/@"      # Instagram 프로필
]

if any(pattern in url for pattern in social_media_patterns):
    use_skill("km-social-media")  # 소셜 미디어 스킬 사용
else:
    use_default_web_crawling()    # 일반 웹 크롤링
```

---

## Phase 1.5: 사용자 선호도 수집

**CRITICAL**: 콘텐츠 추출 전 반드시 사용자 선호도 확인

### 선호도 질문 프롬프트

```
사용자 확인 프롬프트:

"콘텐츠를 어떻게 정리할지 몇 가지 확인이 필요합니다:

📊 **상세 수준 (Detail Level)**
   1. 요약 (Summary) - 핵심만 간략히 (1-2 페이지)
   2. 보통 (Standard) - 주요 내용 + 약간의 설명 (3-5 페이지)
   3. 상세 (Detailed) - 모든 내용을 꼼꼼히 (5+ 페이지)

🎯 **중점 영역 (Focus Area)** - 여러 개 선택 가능
   A. 개념/이론 (Concepts) - 핵심 아이디어와 원리
   B. 실용/활용 (Practical) - 사용법, 예시, 튜토리얼
   C. 기술/코드 (Technical) - 구현, 아키텍처, 코드
   D. 인사이트 (Insights) - 시사점, 의견, 분석
   E. 전체 균형 (Balanced) - 모든 영역 균형있게

📝 **노트 분할 방식 (Note Structure)**
   ① 단일 노트 - 모든 내용을 하나의 노트에
   ② 주제별 분할 - 주요 주제마다 별도 노트 (MOC 포함)
   ③ 원자적 분할 - 최대한 작은 단위로 분할 (Zettelkasten 원칙)
   ④ 3-tier 계층적 분할 (권장) - 메인 MOC + 카테고리 MOC + 원자적 노트 ⭐

🔗 **연결 수준 (Connection Level)**
   - 최소: 태그만 추가
   - 보통: 태그 + 관련 노트 링크 제안
   - 최대: 태그 + 링크 + 기존 노트와 자동 연결 탐색

예시 답변: '2, A+B, ②, 보통' 또는 '상세하게, 실용 위주로, 주제별 분할'

원하시는 옵션을 알려주세요! (기본값: 3.상세, E.전체, ④3-tier, 최대)

💡 3-tier란? 개요 노트 + 주제별 노트 + 원자적 노트로 계층 구조화"
```

### 기본값 (사용자가 "기본" 또는 스킵 시)

| 항목 | 기본값 |
|------|--------|
| Detail Level | 3 (상세) |
| Focus Area | E (전체) |
| Note Structure | ④ (3-tier) |
| Connection Level | 최대 |

### 퀵 프리셋

사용자 키워드에 따른 자동 프리셋 적용:

| 사용자 표현 | 프리셋 |
|------------|--------|
| "빠르게", "간단히" | 1, E, ①, 최소 |
| "꼼꼼히", "자세히" | 3, E, ③, 최대 |
| "실무용", "실용적으로" | 2, B+C, ②, 보통 |
| "공부용", "학습용" | 3, A+D, ③, 최대 |
| "레퍼런스", "참고용" | 2, C, ①, 보통 |
| **"상세하게", "체계적으로"** | **3, E, ④, 최대** ⭐ |
| **"연구보고서", "논문정리"** | **3, A+D, ④, 최대** ⭐ |

---

## Phase 2: 콘텐츠 추출 (🚨 MANDATORY TOOL CALLS!)

**상세 내용**: `km-content-extraction.md` 참조

### ⚠️ CRITICAL: 이 Phase에서 반드시 도구 호출 필요!

```
❌ 도구 호출 없이 콘텐츠 추측 금지
❌ 이전 대화 기억에만 의존 금지
❌ "콘텐츠를 분석하면..." 형태의 가정 금지
✅ 반드시 아래 도구 중 하나를 실제로 호출!
```

### 추출 방법 요약

| 소스 유형 | 🚨 필수 도구 호출 |
|----------|------------------|
| **소셜 미디어 (Threads/Instagram)** | `mcp__playwright__browser_navigate` → `wait_for` → `snapshot` ⭐ |
| **일반 웹 페이지** | `mcp__playwright__browser_navigate` → `snapshot` |
| PDF | `marker_single` 또는 `Read` |
| DOCX/TXT/MD | `Read` 도구 |
| Excel/CSV | `Read` 도구 |
| PowerPoint | `Read` 도구 |
| 이미지 | `Read` 도구 (Vision) |
| Notion | `mcp__notion__API-get-block-children` |
| Vault 종합 | CLI search → `mcp__obsidian__search_vault` 폴백 → `read_multiple_notes` |

### Phase 2 완료 검증 (필수!)

```
□ 해당 소스 유형에 맞는 도구를 실제로 호출했는가?
□ 도구 응답에서 콘텐츠를 확인했는가?
□ 추출된 실제 텍스트가 있는가 (추측 아님)?

⚠️ 위 항목 미완료 시 → Phase 3로 진행 금지!
```

---

## Phase 3: 콘텐츠 분석

Phase 1.5에서 수집한 사용자 선호도에 따라 분석 수행

### 3.1 상세 수준별 처리

#### 요약 (Summary) - Level 1
- 상위 3-5개 핵심 포인트만 추출
- 한 문장 설명
- 부가 설명 및 예시 생략
- 목표: 1-2 페이지

#### 보통 (Standard) - Level 2
- 주요 개념 + 간략한 설명
- 핵심 예시 포함
- 중간 깊이 분석
- 목표: 3-5 페이지

#### 상세 (Detailed) - Level 3
- 모든 개념 + 상세 설명
- 모든 예시, 엣지 케이스 포함
- 깊이 있는 분석 및 시사점
- 목표: 5+ 페이지

### 3.2 중점 영역별 처리

| 영역 | 우선 추출 항목 | 특징 |
|------|--------------|------|
| A. 개념/이론 | 정의, 원리, 이론, 배경 | "무엇"과 "왜" 집중 |
| B. 실용/활용 | How-to, 튜토리얼, 예시, 사용법 | 단계별 가이드 집중 |
| C. 기술/코드 | 코드, 아키텍처, 스펙, 구현 | 기술 상세 집중 |
| D. 인사이트 | 의견, 분석, 시사점, 전망 | 해석과 연결 집중 |
| E. 전체 균형 | 모든 영역 균등 | 종합적 커버리지 |

### 3.3 노트 구조 결정

#### ① 단일 노트
- 모든 콘텐츠를 하나의 노트에 통합
- 섹션 헤더로 구분
- MOC 생성 안 함

#### ② 주제별 분할
- MOC (Map of Content) 생성
- 주요 주제/섹션별 별도 노트 (3-7개)
- 모든 노트는 MOC에 링크

#### ③ 원자적 분할
- 최대 Zettelkasten 원칙 적용
- 하나의 개념 = 하나의 노트
- 10개 이상 노트 생성 가능
- MOC + 노트 간 교차 링크

#### ④ 3-tier 계층적 분할 (권장) ⭐ NEW

**구조:**
```
Research/[프로젝트명]/
├── [제목]-MOC.md                    ← 메인 MOC (전체 개요)
│
├── 01-[챕터1명]/
│   ├── [챕터1]-MOC.md               ← 카테고리 MOC
│   ├── [원자노트1].md               ← 원자적 노트들
│   ├── [원자노트2].md
│   └── [원자노트3].md
│
├── 02-[챕터2명]/
│   ├── [챕터2]-MOC.md               ← 카테고리 MOC
│   ├── [원자노트4].md
│   └── [원자노트5].md
│
└── ... (추가 챕터)
```

**생성 순서:**
1. 문서 전체 분석 → 챕터/섹션 구조 파악
2. 각 챕터별 원자적 개념 추출
3. **원자적 노트 생성** (각 개념당 1개)
4. **카테고리 MOC 생성** (각 챕터당 1개, 해당 챕터의 원자노트 링크)
5. **메인 MOC 생성** (전체 요약 + 모든 카테고리 MOC 링크)

**특징:**
- 대용량 문서(PDF, 연구보고서, 논문)에 최적
- 3단계 계층으로 탐색 용이
- 메인 MOC → 카테고리 MOC → 원자 노트 순으로 drill-down
- 각 레벨에서 적절한 상세도 제공

**적합한 문서 유형:**
- 연구 보고서 (Our Life with AI 등)
- 학술 논문
- 기술 문서/매뉴얼
- 책 챕터 정리

### 3.4 연결 수준 처리

| 수준 | 처리 내용 |
|------|----------|
| 최소 | 관련 태그만 추가 |
| 보통 | 태그 + 2-3개 관련 노트 제안 + wikilinks 생성 |
| 최대 | 태그 + vault 전체 검색 + 양방향 링크 + 기존 노트 업데이트 |

---

## Phase 3.5: 시각화 기회 감지

콘텐츠 분석 후 다이어그램 생성 기회를 자동 감지합니다.

### 자동 감지 트리거

| 콘텐츠 패턴 | 추천 다이어그램 |
|------------|----------------|
| 3단계 이상 순차 프로세스 | Flowchart |
| 3개 이상 시스템 컴포넌트 | Architecture Diagram |
| 계층적 개념 구조 | Mind Map |
| API/통신 흐름 | Sequence Diagram |
| 데이터 엔티티 관계 | ERD |

### 자동 감지 시 프롬프트

```
분석된 콘텐츠에서 시각화하면 좋을 부분을 발견했습니다:

📊 **추천 다이어그램**
- **유형**: [Flowchart/Architecture/Mind Map/Sequence/ERD]
- **대상**: [시각화할 콘텐츠 요약]
- **이유**: [왜 이 유형이 적합한지]

다이어그램을 생성할까요? (예/아니오/나중에)
```

### 명시적 요청 감지

다음 키워드 감지 시 즉시 다이어그램 생성:
- "도식화해줘", "다이어그램 만들어줘", "시각화해줘"
- "flowchart", "diagram", "visualize", "그림으로 보여줘"

→ drawio-diagram 스킬 로드 및 실행

---

## Phase 4: 출력 형식 선택

**CRITICAL**: 항상 사용자에게 출력 형식 확인

### 출력 형식 선택 프롬프트

```
어떤 형식으로 저장할까요?

1. Obsidian (제텔카스텐) - 기본 Zettelkasten 형식, wikilinks 포함
2. Notion - Notion 데이터베이스 형식
3. Markdown (.md) - 표준 마크다운, 별도 위치 저장
4. PDF - 포맷된 PDF 문서
5. 블로그 - Medium/WordPress 호환 형식
6. 다이어그램 - drawio 다이어그램 생성

여러 형식을 동시에 선택 가능합니다 (예: 1,6 → 노트 + 다이어그램)
```

### 형식별 스킬 매핑

| 형식 | 사용 스킬 |
|------|----------|
| Obsidian | zettelkasten-note |
| Notion | notion-knowledge-capture |
| PDF | pdf 스킬 (reportlab) |
| Word | docx 스킬 |
| Excel | xlsx 스킬 |
| PowerPoint | pptx 스킬 |
| 다이어그램 | drawio-diagram |

---

## Phase 5: 내보내기 실행 (🚨 MANDATORY TOOL CALLS!)

**상세 내용**: `km-export-formats.md` 참조

### ⚠️ CRITICAL: 이 Phase에서 반드시 도구 호출 필요!

```
❌ JSON 형식으로 출력만 하고 끝내기 금지
❌ "저장하겠습니다"라고만 말하고 실제 저장 안 함 금지
❌ 노트 내용을 대화창에만 표시하고 파일 생성 안 함 금지
✅ 반드시 아래 도구 중 하나를 실제로 호출!
```

### 내보내기 요약

각 형식에 맞는 스킬을 사용하여 콘텐츠를 변환하고 저장합니다.

### 파일 저장 필수 프로토콜 (🚨 MUST CALL! — 3-Tier)

**Tier 1: Obsidian CLI (최우선) - YOU MUST CALL:**
```bash
"/mnt/c/Program Files/Obsidian/Obsidian.com" create path="Zettelkasten/카테고리/파일명.md" content="노트 전체 내용"
```

**Tier 2: Obsidian MCP (CLI 실패 시) - YOU MUST CALL:**
```tool-call
mcp__obsidian__create_note
- path: "Zettelkasten/카테고리/파일명.md" (vault root 기준 상대경로)
- content: "노트 전체 내용"
```

**Tier 3: Write 도구 (MCP 실패 시) - YOU MUST CALL:**
```tool-call
Write 도구
- file_path: "C:\Users\treyl\OneDrive\Desktop\AI\AI_Second_Brain\Zettelkasten\카테고리\파일명.md"
- content: "노트 전체 내용"
```

### ❌ 절대 금지 패턴

```json
// ❌ 이렇게 하면 절대 안 됨 - 실제 저장 안 됨!
{
  "path": "Research/note.md",
  "content": "..."
}
```

```
❌ "노트를 저장하겠습니다:"라고 말하고 JSON만 보여주기
❌ 마크다운 형식으로 내용만 출력하고 도구 호출 안 함
❌ "완료되었습니다"라고 보고하지만 실제 저장 안 함
```

### Phase 5 완료 검증 (필수!)

```
□ CLI, mcp__obsidian__create_note, 또는 Write 도구를 실제로 호출했는가?
□ 도구 응답에서 성공 메시지 확인했는가? (CLI exit 0 / MCP success / Write 정상)
□ 모든 생성해야 할 노트에 대해 도구 호출을 완료했는가?
□ JSON만 출력하고 끝내지 않았는가?

⚠️ 위 항목 미완료 시 → Phase 5.5로 진행 금지!
⚠️ 도구 호출 없이 "저장 완료" 보고 금지!
```

---

## Phase 5.25: 이미지 저장 + 임베딩 (image_extraction 활성 시)

**상세 내용**: `km-image-pipeline.md` 참조

### 자동 실행 조건

| 조건 | 동작 |
|------|------|
| image_extraction = true | 전체 이미지 추출+저장 (우선순위 1-4) |
| image_extraction = "auto" (기본) | 차트/다이어그램만 (우선순위 1-2), 개수 제한 |
| image_extraction = false | 스킵 |

### 워크플로우 (단일 에이전트 / 모바일)

단일 에이전트에서는 Image Catalog 없이 직접 처리:

```
1. STEP 2에서 수집한 이미지 URL/경로 리스트 사용
2. Resources/images/{topic-folder}/ 디렉토리 생성
3. curl/cp로 다운로드 (실패 시 Playwright 스크린샷 폴백)
4. 본문 흐름에 맞춰 ![[Resources/images/{topic-folder}/{filename}]] 삽입
   - 개념 설명 → (빈 줄) → 이미지 → (빈 줄) → 상세 설명
   - 연속 배치 금지 (텍스트로 분리)
5. Glob으로 파일 존재 검증
```

### 워크플로우 (Agent Teams)

AT 모드에서는 content-extractor가 Image Catalog 생성 → Lead가 Phase 5.25 실행:
(상세: knowledge-manager-at.md STEP 5.25 참조)

---

## Phase 5.5: 연결 강화 ⭐ NEW

**CRITICAL**: 노트 생성 후 반드시 연결 강화 실행

**상세 내용**: → `km-link-strengthening.md`

### 자동 실행 조건

| 조건 | 설명 |
|------|------|
| Obsidian 노트 생성 완료 시 | 자동으로 연결 강화 실행 |
| 사용자 연결 수준이 "보통" 또는 "최대" | 기본 활성화 |
| 사용자 연결 수준이 "최소" | 스킵 (태그만 추가) |

### 워크플로우

```
1. 새 노트 핵심 개념 추출
   - 제목 키워드
   - 태그
   - 본문 주요 개념
    ↓
2. Vault 전체 검색으로 관련 노트 탐색
   - Tier 1: CLI backlinks + search
     "/mnt/c/Program Files/Obsidian/Obsidian.com" backlinks path="{새노트}" format=json
     "/mnt/c/Program Files/Obsidian/Obsidian.com" search query="{키워드}" format=json
   - CLI 실패 시: mcp__obsidian__search_vault 사용
   - 관련성 점수 계산
    ↓
3. 관련 노트 필터링 (최대 5개)
   - 점수 3점 이상
   - 이미 연결된 노트 제외
    ↓
4. 새 노트에 "## 관련 노트" 섹션 추가
   - wikilinks 형식
   - 연결 이유 표시
    ↓
5. 관련 노트에 역방향 링크 추가
   - Tier 1: CLI append (섹션 추가용)
     "/mnt/c/Program Files/Obsidian/Obsidian.com" append path="{기존노트}" content="{링크텍스트}"
   - CLI 실패 시: mcp__obsidian__update_note 사용 (surgical edit)
   - 양방향 연결 완성
    ↓
6. 연결 결과 보고
```

### 관련성 점수 계산

| 기준 | 점수 |
|------|------|
| 제목 키워드 일치 | +3 |
| 태그 일치 | +2 |
| 동일 폴더 | +2 |
| 본문 키워드 일치 | +1 |
| 시간적 근접성 (30일 이내) | +1 |

**임계값**: 3점 이상인 노트만 연결

### 예시 결과

```
## 연결 강화 결과

새 노트: [[LLM 세션 종속성 - 2026-01-03]]

추가된 양방향 링크:
- [[AI 퍼포먼스 결정 요인의 4가지 차원]] (5점)
- [[프롬프트 엔지니어링의 지속적 중요성]] (4점)
- [[메모리 기능이 성능에 미치는 누적 효과]] (3점)
```

---

## Phase 6: 검증 및 보고

### 보고 구조

```
## 처리 결과 보고

### 1. 입력 요약
- 소스 유형: [web/file/notion/image/social-media]
- 소스 위치: [URL/경로]
- 콘텐츠 개요: [간략 설명]

### 2. 처리 요약
- 추출된 아이디어: [N]개
- 생성된 노트: [N]개
- 발견된 연결: [N]개

### 3. 출력 요약
| 형식 | 위치 | 상태 |
|------|------|------|
| [Obsidian/Notion/etc] | [경로/URL] | [성공/실패] |

### 4. 다음 단계
- 제안 작업
- 관련 콘텐츠 탐색 제안
- 품질 확인 권장사항
```

### 검증 체크리스트

```
□ 콘텐츠가 정확하게 추출되었는가?
□ 원자적 아이디어가 적절히 식별되었는가?
□ 메타데이터가 완전하고 정확한가?
□ 기존 노트와의 연결이 발견되었는가?
□ 출력 형식이 사용자 선호도와 일치하는가?
□ 파일이 올바른 위치에 저장되었는가?
□ 변환 중 데이터 손실이 없는가?
□ 사용자에게 모든 출력이 안내되었는가?

## 파일 저장 검증 (필수!)
□ CLI, mcp__obsidian__create_note, 또는 Write 도구를 실제로 호출했는가?
□ 도구 호출 결과에서 성공 확인했는가? (CLI exit 0 / MCP "created successfully" / Write 정상)
□ JSON 출력만 하고 끝내지 않았는가?
```

---

## 에러 처리 전략

### 복구 전략

```
1차 시도: 기본 방법
   ↓ 실패
2차 시도: 대안 방법
   ↓ 실패
3차 시도: raw 콘텐츠 저장
   ↓ 실패
→ 사용자에게 이슈 보고
```

### 에러 유형별 대응

| 에러 유형 | 대응 |
|----------|------|
| 웹 크롤링 실패 | 재시도, 스텔스 모드, 사용자 안내 |
| 파일 없음 | 정확한 경로 요청 |
| 지원 안 되는 형식 | 한계 설명, 대안 제안 |
| 권한 거부 | 권한 확인 요청 |
| API 에러 | 재시도, 수동 내보내기 제안 |
| PDF 생성 실패 | Markdown으로 폴백 |

---

## 스킬 참조

이 워크플로우는 다음 스킬들과 연동됩니다:

- **km-environment-detection.md**: 환경 감지 + RAG 최적화 (Phase 0) ⭐ NEW
- **km-social-media.md**: 소셜 미디어 스크래핑 (Phase 1, 2)
- **km-content-extraction.md**: 콘텐츠 추출 상세 (Phase 2)
- **km-export-formats.md**: 출력 형식 상세 (Phase 5)
- **km-image-pipeline.md**: 이미지 저장 + 임베딩 (Phase 5.25)
- **km-link-strengthening.md**: 연결 강화 (Phase 5.5)
- **km-link-audit.md**: 연결 감사 (수동 실행)
- **zettelkasten-note.md**: Obsidian 노트 형식
- **drawio-diagram.md**: 다이어그램 생성
- **pdf.md, xlsx.md, docx.md, pptx.md**: 문서 처리
- **notion-*.md**: Notion 연동
