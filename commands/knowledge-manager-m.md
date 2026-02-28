---
description: 지식 관리 에이전트 (모바일/Remote) - 키워드 기반 자동 프리셋 + 카카오톡 전송 + ntfy 완료 알림
allowed-tools: Read, Write, Bash, Glob, Grep, mcp__obsidian__*, mcp__notion__*, mcp__playwright__*, WebFetch, AskUserQuestion
---

# Knowledge Manager Mobile (모바일/Remote Control용)

> **모바일, Remote Control, headless 환경에 최적화된 버전입니다.**
> 콘텐츠 설정은 키워드 기반 자동 프리셋으로 결정됩니다 (AskUserQuestion 최소화).
> 카카오톡 전송 + ntfy 완료 알림을 지원합니다.
> 대화형 데스크톱 버전: `/knowledge-manager`

---

## 아키텍처

```
Main (단일 세션, 자동 프리셋)
 └── 키워드 분석 → 순차 실행:
      0. 환경 + 설정 확인
      0.5. 모드 감지 + 자동 프리셋 결정
      1. 콘텐츠 추출
      2. Vault 탐색 + 교차 검증
      3. 콘텐츠 분석 + 노트 구조 설계
      4. 노트 생성
      5. 연결 강화 + 결과 보고
      6. 카카오톡 전송 + ntfy 완료 알림
```

---

## STEP 0: 환경 + 설정 확인

### 0-1. 저장소 확인

```
Obsidian MCP 확인:
  mcp__obsidian__list_notes({}) → 응답 여부 확인
  사용 불가 시 → Write 도구 폴백 모드

Notion MCP 확인 (km-config.json에 enabled 시):
  mcp__notion__API-post-search → 응답 여부 확인
```

### 0-2. km-config.json 로드

```
Glob("km-config.json") → 존재하면 Read로 설정 로드

로드할 항목:
- storage.primary → obsidian / notion / local
- storage.obsidian.vaultPath → vault 경로
- storage.obsidian.defaultFolder → 기본 저장 폴더
- defaults.* → 사용자 기본 프리셋 (자동 프리셋의 기본값으로 사용)
- kakao.recipient → 카카오 기본 수신자 (없으면 질문)
- kakao.scriptPath → send_kakao.py 경로
- notification.ntfyTopic → ntfy 토픽명

설정 파일 없으면 → 기본값 사용
```

---

## STEP 0.5: 자동 프리셋 결정 (핵심)

**콘텐츠 설정은 AskUserQuestion 없이 $ARGUMENTS 텍스트로 자동 결정됩니다.**

### 0.5-1. 모드 감지

| $ARGUMENTS 패턴 | 모드 |
|----------------|------|
| 일반 URL, "정리해줘", "분석해줘", 외부 콘텐츠 | **Mode I** (Content Ingestion) |
| YouTube URL (`youtube.com`, `youtu.be`) | **Mode Y** (YouTube) |
| "카톡방 읽어", "채팅방 분석", 오픈채팅방 이름 | **Mode K** (KakaoTalk Read) |
| "아카이브 정리", "카테고리 재편", "대규모 재편" | **Mode R** (Archive Reorganization) |

**Mode Y**: `km-youtube-transcript.md` 스킬 참조 → 트랜스크립트 추출 후 프리셋 기반 분석
**Mode K**: `km-kakao-chat-read.md` 스킬 참조
  - macOS: kmsg 자동 수집
  - Windows: **자동 수집 불가** — 사용자에게 "대화 내보내기" TXT 경로 요청 → 파싱

### 0.5-2. 복합 프리셋 매칭 (최우선 — 첫 매칭 적용)

| $ARGUMENTS 키워드 | 상세 | 중점 | 분할 | 연결 |
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

**상세 수준:** "요약"→요약, "보통"/"적당"→보통, "상세"/"자세"→상세, (없음)→**km-config defaults 또는 상세**
**중점 영역:** "실용"→실용, "이론"/"개념"→개념, "기술"/"코드"→기술, (없음)→**전체 균형**
**노트 분할:** "단일"→단일, "분할"/"주제별"→주제별, "원자"→원자적, "3-tier"/"계층"→3-tier, (없음)→**상세 수준에 연동**
**연결 수준:** "연결 최소"/"태그만"→최소, (없음)→**최대**

### 0.5-4. PDF 자동 판별 (질문 없이)

```
PDF 파일 감지 시:
  파일 크기 > 5MB 또는 페이지 > 20 → marker_single
  그 외 → Read 직접 읽기
```

### 0.5-5. 카카오 수신자 결정

**$ARGUMENTS에서 먼저 추출:**

| $ARGUMENTS 키워드 | kakao_recipient | 질문 여부 |
|---|---|---|
| "카카오 나에게", "카톡 나에게" | km-config의 `kakao.selfName` | 질문 안 함 |
| "카카오 {이름}", "카톡 {이름}" | "{이름}" | 질문 안 함 |
| "카카오", "카톡" (이름 없음) | 미정 | **1회 질문** |
| (카카오/카톡 키워드 없음) | null (전송 안함) | 질문 안 함 |

**수신자 미정 시 — AskUserQuestion 1회 (유일한 질문 지점):**

```json
AskUserQuestion({
  "questions": [
    {
      "question": "카카오톡 어느 채팅방으로 보낼까요?",
      "header": "카카오 수신자",
      "options": [
        {"label": "나에게 보내기", "description": "본인 채팅방으로 전송"},
        {"label": "전송 안함", "description": "카카오 전송 건너뛰기"}
      ],
      "multiSelect": false
    }
  ]
})
```

- "나에게 보내기" → `kakao.selfName` 사용 (km-config.json에서)
- "전송 안함" → kakao_recipient = null
- Other 입력 → 입력한 채팅방 이름 사용

> **이 질문이 AskUserQuestion의 유일한 사용 지점입니다.**

### 0.5-6. 프리셋 결과 출력 (필수)

```
**자동 프리셋 적용 결과:**

| 항목 | 설정값 | 감지 키워드 |
|------|--------|-----------|
| 모드 | {Mode I / Mode R} | {감지 근거} |
| 상세 수준 | {값} | {매칭 키워드 또는 "기본값"} |
| 중점 영역 | {값} | {매칭 키워드 또는 "기본값"} |
| 노트 분할 | {값} | {매칭 키워드 또는 "기본값"} |
| 연결 수준 | {값} | {매칭 키워드 또는 "기본값"} |
| 카카오 전송 | {수신자 또는 "안함"} | {매칭 키워드} |
| ntfy 알림 | {토픽명 또는 "미설정"} | {km-config} |

진행합니다...
```

---

## STEP 1: 콘텐츠 추출

스킬 참조: `km-content-extraction.md`, `km-social-media.md`

| 입력 유형 | 추출 방법 |
|----------|----------|
| **소셜 미디어 (Threads/Instagram)** | mcp__playwright__* (1순위) → WebFetch (2순위) |
| **일반 웹 URL** | mcp__playwright__* (1순위) → WebFetch (2순위) |
| **YouTube URL** | youtube-transcript-api → yt-dlp 폴백 (km-youtube-transcript.md) |
| **카카오톡 채팅** | kmsg (macOS) / 대화 내보내기 TXT 파싱 (Windows) (km-kakao-chat-read.md) |
| **PDF (작은)** | Read 직접 (< 5MB, < 20p) |
| **PDF (큰)** | marker_single |
| **Notion URL** | mcp__notion__API-get-block-children |
| **Vault 종합** | mcp__obsidian__search_vault + read_multiple_notes |

---

## STEP 2: Vault 탐색 + 교차 검증

### Phase A: 그래프 탐색

```
1. Grep으로 [[키워드]] 패턴 검색 → Hub 노트 식별 (최소 2개)
2. Hub 노트 Read → 내부 [[wikilink]] 추출 → 1-hop 추적
3. 3-tier/원자적 선택 시 → 2-hop 추적
```

### Phase B: 키워드 검색

```
1. mcp__obsidian__search_vault({ query: "{핵심 키워드}" })
2. Grep으로 tags: 패턴 검색
3. 관련 폴더 탐색 (Zettelkasten/, Research/)
```

### Phase C: 교차 검증

```
Graph ∩ Retrieval = 핵심 노트 (우선 처리)
Graph only = 관계 기반 발견 (보조 참조)
Retrieval only = 고립 노트 (링크 후보)
```

---

## STEP 3: 콘텐츠 분석 + 노트 구조 설계

자동 프리셋에 따라 깊이/초점 조정 → 노트 구조 설계 → 태그 추천

스킬 참조: `km-export-formats.md`, `zettelkasten-note.md`

---

## STEP 4: 노트 생성 (Main 직접!)

**CRITICAL**: 노트 생성은 **반드시 Main이 직접** 수행합니다.

```
mcp__obsidian__create_note 또는 Write 도구 사용

저장 검증 (필수):
1. 응답 확인
2. Glob으로 파일 존재 확인
3. 실패 시 Write 도구 폴백
```

3-tier 선택 시: 원자노트 → 카테고리 MOC → 메인 MOC 순서로 생성.
모든 노트에 네비게이션 푸터 포함 (km-export-formats.md 참조).

---

## STEP 5: 연결 강화 + 결과 보고

### 5-1. 연결 강화 (연결 수준 "보통" 또는 "최대"일 때)

스킬 참조: `km-link-strengthening.md`

### 5-2. 결과 보고

```
## 처리 결과

| 항목 | 값 |
|------|---|
| 소스 | {URL/파일} |
| 프리셋 | {상세}, {중점}, {분할}, {연결} |
| 생성 노트 | {수}개 |
| 추가 링크 | {수}개 |
| 카카오 | {수신자 또는 안함} |
| ntfy | {전송 여부} |

### 출력 위치
| 노트 | 경로 | 상태 |
|------|------|------|
| ... | ... | 성공 |
```

---

## STEP 6: 카카오톡 전송 + ntfy 완료 알림

### 6-1. 카카오톡 전송 (kakao_recipient 설정 시만)

```
플랫폼 확인:
  Bash("which powershell.exe > /dev/null 2>&1 && echo WSL_OK || echo NO_WINDOWS")
  NO_WINDOWS → 스킵

전송 콘텐츠:
  단일 노트 → 전체 내용
  다중 노트 → 메인 MOC 내용

임시 파일 생성 → send_kakao.py 호출 → 결과 확인 → 임시 파일 삭제

send_kakao.py 경로: km-config.json의 kakao.scriptPath
  미설정 시: ".claude/scripts/send_kakao.py"
```

> 카카오톡 "나와의 채팅"은 본인 메시지에 대해 **푸시 알림이 울리지 않습니다.**
> ntfy 알림이 별도로 작업 완료를 알려줍니다.

### 6-2. ntfy 완료 알림 (항상 — 카카오 전송 여부 무관)

```
ntfy 토픽 확인:
  km-config.json의 notification.ntfyTopic → 설정값 사용
  미설정 시 → ntfy 알림 스킵

Bash:
curl -s \
  -H "Title: KM 완료" \
  -H "Priority: high" \
  -H "Tags: white_check_mark,brain" \
  -d "{노트 제목} - {노트 수}개 노트, {링크 수}개 링크" \
  ntfy.sh/{ntfyTopic}

실패해도 중단하지 않음 (best-effort).
```

---

## 참조 스킬

| 기능 | 스킬 |
|------|------|
| 전체 워크플로우 | `km-workflow.md` |
| 콘텐츠 추출 | `km-content-extraction.md` |
| 소셜 미디어 | `km-social-media.md` |
| YouTube 트랜스크립트 | `km-youtube-transcript.md` |
| 카카오톡 채팅 읽기 | `km-kakao-chat-read.md` |
| 출력 형식 | `km-export-formats.md` |
| 연결 강화 | `km-link-strengthening.md` |
| 연결 감사 | `km-link-audit.md` |
| Obsidian 노트 형식 | `zettelkasten-note.md` |

---

## 사용 예시

```bash
# 기본 URL 정리 (자동 프리셋: 상세, 전체균형, 3-tier, 최대)
/knowledge-manager-m https://example.com/article

# 빠른 요약 + 카카오 전송
/knowledge-manager-m https://example.com 요약해줘 카카오 나에게

# 상세 분석 + 특정인에게 전송
/knowledge-manager-m https://arxiv.org/paper 꼼꼼히 카카오 홍길동

# 실용 중심 정리
/knowledge-manager-m https://docs.example.com 실무용

# YouTube 영상 요약
/knowledge-manager-m https://youtube.com/watch?v=XXX 요약해줘

# 카카오톡 채팅방 분석
/knowledge-manager-m 카톡방 "AI 오픈채팅" 이번 주 정리해줘
```

---

## 사용자 요청 내용

$ARGUMENTS
