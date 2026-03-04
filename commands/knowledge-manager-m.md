---
description: 지식 관리 에이전트 (모바일/헤드리스) - AskUserQuestion 없이 키워드 기반 자동 프리셋 + 카카오 전송
allowedTools: Read, Write, Bash, Glob, Grep, mcp__obsidian__*, mcp__notion__*, mcp__playwright__*, mcp__hyperbrowser__*, WebFetch, AskUserQuestion
---

# Knowledge Manager Mobile 호출 (모바일/헤드리스)

> **이 명령어는 키워드 기반 자동 프리셋으로 동작합니다.**
> 콘텐츠 설정(상세/중점/분할/연결)은 AskUserQuestion 없이 자동 결정됩니다.
> 카카오 수신자만 필요 시 1회 질문합니다 (배포 환경 대응).
> 데스크톱 대화형 버전: `/knowledge-manager` (전체 AskUserQuestion 사용)
> 에이전트 정의: `.claude/agents/knowledge-manager.md` 참조

---

## 아키텍처

```
Main (단일 세션, AskUserQuestion 없음)
 └── 키워드 기반 자동 프리셋 → 순차 실행:
      0. 환경 확인
      0.5. 모드 감지 + 자동 프리셋 결정
      2. 콘텐츠 추출
      3. Vault 그래프 탐색
      4. 콘텐츠 분석 + 노트 구조 설계
      5. 노트 생성
      6. 연결 강화 + 결과 보고
      7. 카카오 전송 (설정 시)
```

**어디서든 동작** (tmux 없어도, Agent Teams 없어도, 모바일/SSH/headless에서도).

---

## STEP 0-PRE: Config 읽기 (가장 먼저!)

**반드시 다른 모든 단계 전에 실행합니다.**

```
config = Read("km-config.json")

# 핵심 설정 추출
vaultPath = config.storage.obsidian.vaultPath    # 예: "/home/user/Documents/MyVault"
kakaoSelfName = config.kakao.selfName            # 예: "홍길동" (빈 문자열이면 카카오 비활성화)
ntfyTopic = config.notification.ntfyTopic        # 예: "my-km-alerts" (빈 문자열이면 알림 비활성화)

# Obsidian CLI 크로스 플랫폼 감지
Bash:
  if which obsidian >/dev/null 2>&1; then
    OBSIDIAN_CLI="obsidian"
  elif [ -f "/mnt/c/Program Files/Obsidian/Obsidian.com" ]; then
    OBSIDIAN_CLI="/mnt/c/Program Files/Obsidian/Obsidian.com"
  else
    OBSIDIAN_CLI=""
  fi
→ OBSIDIAN_CLI가 비어있으면 CLI Tier 스킵 (MCP/filesystem으로 폴백)

# marker_single 크로스 플랫폼 감지
Bash("which marker_single 2>/dev/null || echo NOT_FOUND")
→ PATH에 있으면: marker_single (그대로 사용)
→ NOT_FOUND: PDF Read 도구 폴백
```

---

## STEP 0: 환경 확인 (간소화)

**사용자에게 표시할 필요 없음. 내부적으로 판단만 수행.**

### Obsidian 접근 방식 확인 (3-Tier)

```bash
# OBSIDIAN_CLI는 STEP 0-PRE에서 크로스 플랫폼 감지 완료

# Tier 1: CLI 확인 (OBSIDIAN_CLI가 비어있지 않으면)
"$OBSIDIAN_CLI" version 2>/dev/null
→ 응답 있으면: obsidian_method = "cli"

# Tier 2: CLI 실패 시 MCP 확인 (모바일에서 Obsidian 미실행 시 중요!)
mcp__obsidian__list_notes({}) → 응답 여부
→ 응답 있으면: obsidian_method = "mcp"

# Tier 3: 둘 다 실패 시
→ obsidian_method = "filesystem"
→ Write/Read/Grep 도구로 직접 파일 저장
```

---

## STEP 0.5: 자동 프리셋 결정 (AskUserQuestion 대체 — 핵심!)

**CRITICAL**: 이 명령어는 콘텐츠 설정에 AskUserQuestion을 사용하지 않습니다.
상세/중점/분할/연결은 $ARGUMENTS 텍스트 분석으로 자동 결정됩니다.
유일한 예외: 카카오 수신자가 미정일 때 1회 질문 (배포 환경 대응).

### 0.5-1. 모드 감지 (Mode Detection)

$ARGUMENTS 텍스트를 분석하여 모드를 자동 결정합니다.

| $ARGUMENTS 패턴 | 모드 |
|----------------|------|
| URL, "정리해줘", "분석해줘", 외부 콘텐츠 | **Mode I** (Content Ingestion) |
| "아카이브 정리", "카테고리 재편", "일괄 링크", "대규모 재편" | **Mode R** (Archive Reorganization) |
| 기존 vault 폴더명 지칭 | **Mode R** (자동 진입) |

**Mode R 자동 파라미터 (질문 없이 기본값 적용):**

| 파라미터 | 기본값 | 오버라이드 키워드 |
|---------|--------|-----------------|
| 대상 폴더 | $ARGUMENTS에서 경로 추출 | 명시적 폴더 경로 |
| 재편 범위 | 풀 재편 | "링크만"→링크 강화, "카테고리만"→카테고리 재분류 |
| Auto-commit | 예 (매 배치 후 즉시 commit) | "커밋 안함", "no commit"→아니오 |

Mode R 선택 시 → `km-archive-reorganization.md` 스킬의 Phase R0-R5 실행.

### 0.5-2. 복합 프리셋 매칭 (최우선)

$ARGUMENTS에서 아래 키워드를 순서대로 매칭합니다. **첫 매칭이 적용됩니다.**

| $ARGUMENTS 키워드 | 상세 수준 | 중점 영역 | 노트 분할 | 연결 수준 |
|---|---|---|---|---|
| "빠르게", "간단히" | 요약 (1-2p) | 전체 균형 | 단일 노트 | 최소 |
| "요약해줘", "요약" | 요약 (1-2p) | 전체 균형 | 단일 노트 | 최대 |
| "상세하게 요약해줘", "상세 요약" | 보통 (3-5p) | 전체 균형 | 주제별 분할 | 최대 |
| "꼼꼼히", "자세히", "체계적으로" | 상세 (5p+) | 전체 균형 | 원자적 분할 | 최대 |
| "기본으로", "기본" | 상세 (5p+) | 전체 균형 | 3-tier | 최대 |
| "연구보고서", "논문정리" | 상세 (5p+) | 개념/이론 | 3-tier | 최대 |
| "실무용", "실용적으로" | 보통 (3-5p) | 실용/활용 | 주제별 분할 | 보통 |
| "레퍼런스", "참고용" | 보통 (3-5p) | 기술/코드 | 단일 노트 | 보통 |
| "공부용", "학습용" | 상세 (5p+) | 개념/이론 | 원자적 분할 | 최대 |

### 0.5-3. 개별 파라미터 오버라이드 (복합 미매칭 시)

복합 프리셋에 매칭되지 않은 경우, 개별 키워드로 각 파라미터를 결정합니다.

**상세 수준:**

| 키워드 | 값 |
|--------|---|
| "요약", "간략", "summary", "brief" | 요약 (1-2p) |
| "보통", "적당", "standard" | 보통 (3-5p) |
| "상세", "자세", "detailed", "comprehensive" | 상세 (5p+) |
| (매칭 없음) | **상세 (5p+)** |

**중점 영역:**

| 키워드 | 값 |
|--------|---|
| "실용", "활용", "사용법", "practical" | 실용/활용 |
| "이론", "개념", "concept" | 개념/이론 |
| "기술", "코드", "technical", "code" | 기술/코드 |
| "인사이트", "분석", "insight" | 인사이트 |
| (매칭 없음) | **전체 균형** |

**노트 분할 (상세 수준에 연동):**

| 키워드 | 값 |
|--------|---|
| "단일", "하나로", "single" | 단일 노트 |
| "분할", "나눠", "주제별", "split" | 주제별 분할 |
| "원자", "zettelkasten", "atomic" | 원자적 분할 |
| "3-tier", "계층", "tier" | 3-tier 계층 |
| (매칭 없음 + 요약) | **단일 노트** |
| (매칭 없음 + 보통) | **주제별 분할** |
| (매칭 없음 + 상세) | **3-tier 계층** |

**연결 수준:**

| 키워드 | 값 |
|--------|---|
| "연결 최소", "태그만", "minimal" | 최소 |
| "연결 보통", "moderate" | 보통 |
| (매칭 없음) | **최대** |

### 0.5-4. 부가 옵션 자동 판별

**이미지 추출:**

| 키워드 | 값 |
|--------|---|
| "이미지도", "이미지 포함", "차트 포함", "그래프 포함", "images" | **true** |
| "텍스트만", "이미지 빼고", "text only" | **false** |
| (매칭 없음) | **false** (기본값 — 텍스트만 추출) |

**PDF 처리 (PDF 입력 시만):**

```
PDF 파일 감지 시:
  → 파일 크기 > 5MB 또는 페이지 수 > 20 → marker_single (중량 처리)
  → 그 외 → Read 도구 직접 읽기 (경량 처리)
질문 없이 자동 분기합니다.
```

### 0.5-5. 카카오 수신자 결정

**$ARGUMENTS에서 수신자를 먼저 추출합니다:**

| $ARGUMENTS 키워드 | kakao_recipient | 질문 여부 |
|---|---|---|
| "카카오 나에게", "나한테 보내", "카톡 나에게" | **"{kakaoSelfName}"** | 질문 안 함 |
| "카카오 {이름}", "카톡 {이름}" | "{이름}" | 질문 안 함 |
| "카카오", "카톡" (이름 없음) | 미정 | **1회 질문** |
| (카카오/카톡 키워드 없음) | 미정 | **1회 질문 (첫 사용 시)** |

> **CRITICAL**: 카카오톡 셀프 채팅방 이름은 "나"가 아니라 **"{kakaoSelfName}"** (본인 실명)입니다.
> "나"로 검색하면 "나"가 포함된 다른 채팅방("~누나" 등)이 열려 혼란 발생.

**카카오 키워드 없는 경우 — 세션 첫 사용 시 AskUserQuestion 1회 (배포 환경 대응):**

> **변경 이력 (2026-02-28)**: 카카오/카톡 키워드가 없어도 세션 첫 KM 호출 시 반드시 1회 질문.
> 사용자가 매번 "카카오 나에게"를 입력하지 않아도 전송 옵션을 제공하기 위함.

**수신자 미정 시 — AskUserQuestion 1회:**

```
AskUserQuestion:
  question: "카카오톡 어느 채팅방으로 보낼까요?"
  header: "카카오 수신자"
  options:
    - label: "나에게 ({kakaoSelfName})"
      description: "본인 채팅방으로 전송"
    - label: "전송 안함"
      description: "카카오 전송 건너뛰기"
  multiSelect: false

→ "나에게 ({kakaoSelfName})" 선택 시: kakao_recipient = "{kakaoSelfName}"
→ "전송 안함" 선택 시: kakao_recipient = null
→ Other 입력 시: kakao_recipient = 입력한 채팅방 이름
```

> **이 질문은 AskUserQuestion이 유일하게 사용되는 지점입니다.**
> 콘텐츠 설정(상세/중점/분할/연결)은 절대 질문하지 않습니다.

### 0.5-6. 프리셋 결과 출력 (필수!)

자동 결정 완료 후 **반드시** 다음 테이블을 사용자에게 출력합니다 (확인용, 블로킹 아님):

```
**자동 프리셋 적용 결과:**

| 항목 | 설정값 | 감지 키워드 |
|------|--------|-----------|
| 모드 | {Mode I / Mode R} | {감지 근거} |
| 상세 수준 | {값} | {매칭 키워드 또는 "기본값"} |
| 중점 영역 | {값} | {매칭 키워드 또는 "기본값"} |
| 노트 분할 | {값} | {매칭 키워드 또는 "기본값"} |
| 연결 수준 | {값} | {매칭 키워드 또는 "기본값"} |
| 이미지 추출 | {auto/true/false} | {매칭 키워드 또는 "기본값"} |
| 카카오 전송 | {수신자 또는 "안함"} | {매칭 키워드 또는 "없음"} |

진행합니다...
```

---

## STEP 2: 콘텐츠 추출 (Main 직접)

Main이 입력 소스를 직접 추출합니다. 스킬 참조: `km-content-extraction.md`, `km-youtube-transcript.md`, `km-social-media.md`

### 소스 유형별 추출

| 입력 유형 | 추출 방법 |
|----------|----------|
| **YouTube** | `youtube-transcript-api` → `yt-dlp` 폴백 → 스킬: `km-youtube-transcript.md` |
| **소셜 미디어 (Threads/Instagram)** | playwright-cli open → snapshot (1순위) → mcp__playwright__* (2순위) → WebFetch (3순위) |
| **일반 웹 URL** | playwright-cli open → snapshot (1순위) → mcp__playwright__* (2순위) → WebFetch (3순위) |
| **PDF (작은)** | Read 직접 시도 (< 5MB, < 20p) |
| **PDF (큰)** | /pdf 스킬 또는 marker_single |
| **DOCX/XLSX/PPTX** | Read 또는 해당 스킬 도구 |
| **Notion URL** | mcp__notion__API-get-block-children |
| **Vault 종합 ("종합해줘")** | CLI: `"$OBSIDIAN_CLI" search` + 순차 `read` / MCP 폴백: search_vault + read_multiple_notes |

### 이미지 URL 수집 (image_extraction != false 시)

```
콘텐츠 추출과 동시에 이미지 URL 수집 (인라인 모드):

1. browser_snapshot HTML에서 img/figure 태그 파싱
2. 필터링: < 100x100px 제외, 광고/트래커 제외, 아이콘 제외
3. 우선순위 분류:
   - auto: 차트/다이어그램/인포그래픽만 (우선순위 1-2)
   - true: 모든 콘텐츠 이미지 (우선순위 1-4)
4. 모바일 제한: auto 최대 5개, true 최대 10개
5. 차트/SVG → browser_take_screenshot으로 캡처
6. 메모리 내 리스트로 보관 (Catalog 불필요)
```

### 추출 결과 정리

```
추출 완료 후 다음 정보를 정리:
- 제목, 저자, 날짜
- 전체 콘텐츠 (Markdown)
- 섹션 구조
- 미디어/이미지 URL (수집된 이미지 리스트 포함)
- 인용/참조
```

---

## STEP 3: Vault 탐색 (Main 직접 - 순차)

### Phase A: 그래프 탐색 (graph-navigator 로직)

```
1. Hub 노트 식별:
   - Grep으로 [[키워드]] 패턴 검색
     Grep({ pattern: "\\[\\[.*{키워드}.*\\]\\]", path: "{vaultPath}" })
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
2. 자동 프리셋 반영한 깊이/초점 조정
3. 기존 vault 노트와의 관계 분석
```

### 4-2. 노트 구조 설계

```
자동 프리셋 결과에 따라:

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

### 5-3.5. 이미지 저장 및 임베딩 (image_extraction != false 시)

**참조 스킬**: `km-image-pipeline.md`

```
1. Resources/images/{topic-folder}/ 디렉토리 생성:
   Bash("mkdir -p {vaultPath}/Resources/images/{topic-folder}/")

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

**모바일 제한**: auto 최대 5개, true 최대 10개, > 2MB 이미지 스킵

### 5-4. 카카오 전송용 콘텐츠 저장

```
kakao_recipient가 설정된 경우:
  → 생성된 노트 중 전송 대상 콘텐츠를 변수에 보관
  → 단일 노트: 전체 내용
  → 다중 노트 (3-tier): 메인 MOC 내용
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

### 6-2. 결과 보고

```
## 처리 결과 보고

### 입력 요약
- 소스: [URL/파일/vault종합]
- 모드: 모바일 단일 에이전트 (자동 프리셋)

### 자동 프리셋
- 상세 수준: {값}
- 중점 영역: {값}
- 노트 분할: {값}
- 연결 수준: {값}

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

### 카카오 전송
- 수신자: {kakao_recipient 또는 "전송 안함"}
- 상태: {성공/실패/스킵}
```

---

## STEP 7: 카카오 전송 (kakao_recipient 설정 시만)

**kakao_recipient가 null이면 이 STEP을 완전히 스킵합니다.**

### 7-1. 플랫폼 확인

```
Bash("which powershell.exe > /dev/null 2>&1 && echo WSL_OK || echo NO_WINDOWS")

NO_WINDOWS → "카카오 전송: 건너뜀 (Windows 환경 아님)" 출력 후 스킵
```

### 7-2. 전송 콘텐츠 준비

```
STEP 5-4에서 보관한 콘텐츠를 임시 파일에 저장:

Write("/tmp/km-kakao-msg.md", kakao_content)
```

### 7-3. send_kakao.py 호출

```
Bash:
powershell.exe -Command "python '{send_kakao_wsl_path}' -r '{kakao_recipient}' -f '\\\\wsl.localhost\\Ubuntu\\tmp\\km-kakao-msg.md' --convert-md"
# send_kakao_wsl_path는 STEP 0-PRE에서 config.kakao.scriptPath를 WSL UNC 경로로 변환하여 획득
```

**send_kakao.py가 처리하는 것:**
- Markdown → 플레인 텍스트 변환 (--convert-md)
- 메시지 분할 (4500자 기준 자동)
- 채팅방 검색 + 전송
- 포커스 복원

### 7-4. 결과 확인

```
stdout에 "OK" 포함 → 성공
그 외 → 실패 로그 출력 (중단하지 않음 — 노트 생성은 이미 완료)
```

### 7-5. 임시 파일 정리

```
Bash("rm -f /tmp/km-kakao-msg.md")
```

### 7-6. ntfy 완료 알림 (항상 — 카카오 전송 여부 무관)

**STEP 7의 마지막 단계로 항상 실행합니다.**

```
Bash:
curl -s \
  -H "Title: KM 완료" \
  -H "Priority: high" \
  -H "Tags: white_check_mark,brain" \
  -d "{생성된 노트 제목} - {노트 수}개 노트, {링크 수}개 링크 추가" \
  ntfy.sh/{ntfyTopic}
```

- ntfyTopic이 빈 문자열이면 이 단계를 스킵합니다 (알림 비활성화)
- kakao_recipient가 null(카카오 전송 안 함)이어도 ntfy는 발송
- kakao_recipient가 설정되어 카카오 전송을 했어도 ntfy는 발송 (셀프 채팅 알림 안 울리므로)
- 실패해도 중단하지 않음 (best-effort)

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
| **카카오 전송 스크립트** | `.claude/scripts/send_kakao.py` |

---

## 사용 예시

```bash
# 기본 URL 정리 (기본 프리셋: 상세, 전체균형, 3-tier, 최대)
/knowledge-manager-m https://example.com/article

# 빠른 요약 + 카카오 전송
/knowledge-manager-m https://threads.net/@user/post/123 요약해줘 카카오 나에게

# 상세 분석 + 특정인에게 전송
/knowledge-manager-m https://arxiv.org/paper 꼼꼼히 카카오 {kakaoSelfName}

# 실용 중심 정리
/knowledge-manager-m https://docs.example.com 실무용

# 아카이브 재편 (Mode R)
/knowledge-manager-m Research/얼룩소-아카이브 아카이브 재편

# vault 종합
/knowledge-manager-m AI-Safety 주제 종합해줘 간단히 카카오 나에게
```

---

## 사용자 요청 내용

$ARGUMENTS
