# 소셜 미디어 콘텐츠 스크래핑 스킬

> Knowledge Manager 에이전트용 소셜 미디어 URL 자동 감지 및 playwright MCP 스크래핑 스킬

---

## 🚨 MANDATORY ACTIONS (필수 행동!)

**소셜 미디어 URL 감지 시 반드시 다음 도구들을 실제로 호출해야 합니다:**

| 순서 | 필수 도구 호출 | 목적 |
|------|--------------|------|
| 1️⃣ | `mcp__playwright__browser_navigate` | 페이지 이동 |
| 2️⃣ | `mcp__playwright__browser_wait_for` | 동적 콘텐츠 로드 대기 |
| 3️⃣ | `mcp__playwright__browser_snapshot` | 콘텐츠 추출 |

### ❌ 절대 금지 패턴

```
❌ WebFetch 사용 금지 - JavaScript 렌더링 불가
❌ 도구 호출 없이 내용 추측/생성 금지
❌ 이전 대화 기억에만 의존 금지
❌ 콘텐츠 크롤링 없이 노트 작성 금지
```

### ✅ 필수 검증

```
□ playwright 도구를 실제로 호출했는가?
□ browser_snapshot 결과에서 콘텐츠를 추출했는가?
□ 추출된 실제 텍스트를 사용했는가?
```

⚠️ **도구 호출 없이 응답하면 작업 실패로 간주됩니다!**

---

## URL 패턴 자동 감지

### 지원 플랫폼 및 패턴

사용자 입력 URL이 다음 패턴과 일치하면 **자동으로** playwright MCP 사용:

| 플랫폼 | URL 패턴 | 예시 |
|--------|----------|------|
| **Threads** | `threads.net/@*` | `threads.net/@username/post/C123...` |
| **Threads** | `threads.net/t/*` | `threads.net/t/C123...` |
| **Instagram Post** | `instagram.com/p/*` | `instagram.com/p/ABC123/` |
| **Instagram Reel** | `instagram.com/reel/*` | `instagram.com/reel/ABC123/` |
| **Instagram Profile** | `instagram.com/@*` | `instagram.com/@username/` |

### 패턴 매칭 로직

```python
# 소셜 미디어 URL 감지 pseudocode
if URL contains any of:
   - "threads.net/"
   - "instagram.com/p/"
   - "instagram.com/reel/"
   - "instagram.com/@"

   → Use playwright MCP (NOT WebFetch)
   → Reason: 동적 콘텐츠, JavaScript 렌더링 필요
```

---

## 스크래핑 워크플로우 (🚨 MUST FOLLOW!)

### Step 1: 플랫폼 식별

```
URL 분석:
├─ threads.net/* → Threads 포스트/프로필
├─ instagram.com/p/* → Instagram 포스트
├─ instagram.com/reel/* → Instagram 릴스
└─ instagram.com/@* → Instagram 프로필
```

### Step 2: 브라우저 탐색 (🚨 ACTION REQUIRED!)

**YOU MUST CALL THIS TOOL:**

```tool-call
mcp__playwright__browser_navigate
- url: [소셜 미디어 URL]
```

**즉시 검증:**
- [ ] 도구 호출 완료?
- [ ] 페이지 이동 성공?

⚠️ **이 도구를 호출하지 않으면 다음 단계로 진행 불가!**

### Step 3: 동적 콘텐츠 대기 (🚨 ACTION REQUIRED!)

**YOU MUST CALL THIS TOOL:**

```tool-call
mcp__playwright__browser_wait_for
옵션 1: 텍스트 기반 대기
- text: "좋아요" 또는 "replies" (콘텐츠 로드 확인용 텍스트)

옵션 2: 시간 기반 대기 (권장)
- time: 3 (3초 대기)
```

**즉시 검증:**
- [ ] 대기 완료?

### Step 4: 콘텐츠 추출 (🚨 ACTION REQUIRED - CRITICAL!)

**YOU MUST CALL THIS TOOL:**

```tool-call
mcp__playwright__browser_snapshot
- 전체 페이지 accessibility 스냅샷 수집
- 텍스트, 작성자, 상호작용 수치 추출
```

**즉시 검증:**
- [ ] 스냅샷 수집 완료?
- [ ] 포스트 본문 텍스트 확인 가능?
- [ ] 작성자 정보 확인 가능?

⚠️ **이 스냅샷 결과 없이 노트 작성 절대 금지!**

### Step 5: 스크린샷 (선택적)

```
mcp__playwright__browser_take_screenshot
- 시각적 레퍼런스 저장
- 이미지/미디어 콘텐츠 캡처
```

### Step 6: 브라우저 정리 (선택적)

```
mcp__playwright__browser_close
- 세션 완료 후 브라우저 닫기
```

### 워크플로우 최종 검증

**모든 Step 완료 후 체크:**

```
✅ Step 2: browser_navigate 호출 완료?
✅ Step 3: browser_wait_for 호출 완료?
✅ Step 4: browser_snapshot 호출 완료?
✅ 스냅샷에서 실제 콘텐츠 추출 완료?

위 항목 중 하나라도 미완료 시 → 워크플로우 재시작!
```

---

## Threads 답글 병렬 크롤링 (Thread Replies) ⭐

Threads 포스트의 하위 답글들을 병렬로 수집하는 워크플로우입니다.

### 언제 사용하나요?

```
트리거 조건:
- Threads URL 크롤링 시
- 포스트에 답글이 있는 경우
- 사용자가 "답글까지 정리해줘", "전체 스레드 정리" 등 요청 시
```

### Step 1: 메인 포스트 크롤링 + 답글 수 확인

```
mcp__playwright__browser_navigate → 메인 URL
mcp__playwright__browser_wait_for → 콘텐츠 로드 대기
mcp__playwright__browser_snapshot → 스냅샷 수집

스냅샷에서 확인:
- replies: 45 → 답글 존재 확인
- 답글 영역의 링크들 파싱
```

### Step 2: 사용자에게 Depth 선택 요청 (매번!)

```
📋 답글 크롤링 범위를 선택해주세요:

1) depth=1: 직접 답글만 (빠름)
   - 메인 포스트의 1차 답글만 수집
   - 예상 시간: ~10초

2) depth=2: 답글의 답글까지 (더 완전한 맥락)
   - 1차 답글 + 그 답글들까지 수집
   - 예상 시간: ~30초+

답글 수: 약 N개
```

### Step 3: 답글 URL 수집

```
스냅샷에서 답글 링크 파싱:

예시 URL 패턴:
- threads.net/@user/post/ABC → 메인 포스트
- threads.net/@replier1/post/DEF → 1차 답글
- threads.net/@replier2/post/GHI → 1차 답글
- ...

수집 결과:
reply_urls = [
  "threads.net/@replier1/post/DEF",
  "threads.net/@replier2/post/GHI",
  ...
]
```

### Step 4: 답글 병렬 크롤링

```
병렬 처리 (동시 최대 5개):

같은 메시지에서 여러 도구 호출:

[도구 1] mcp__playwright__browser_navigate(url="threads.net/@replier1/post/DEF")
[도구 2] mcp__playwright__browser_navigate(url="threads.net/@replier2/post/GHI")
[도구 3] mcp__playwright__browser_navigate(url="threads.net/@replier3/post/JKL")
...

각 답글 페이지에서:
- mcp__playwright__browser_snapshot
- 작성자, 본문, 반응 수 추출
- 해당 답글의 하위 답글 URL 수집 (depth=2인 경우)

Rate Limit 주의:
- 동시 5개 이하 권장
- 답글이 많으면 배치 처리 (5개씩)
- 배치 간 3-5초 딜레이
```

### Step 5: 중첩 답글 처리 (depth=2인 경우)

```
depth=2 선택 시:

1차 답글 처리 완료 후:
→ 각 1차 답글의 하위 답글 URL 수집
→ 2차 답글들도 병렬 크롤링

예시 구조:
메인 포스트
├─ 1차 답글 A
│   ├─ 2차 답글 A-1
│   └─ 2차 답글 A-2
├─ 1차 답글 B
│   └─ 2차 답글 B-1
└─ 1차 답글 C
```

### Step 6: 결과 통합 및 구조화

```
통합 데이터 구조:

{
  "platform": "threads",
  "type": "thread_with_replies",
  "main_post": {
    "author": "@original_author",
    "text": "원본 포스트 내용",
    "engagement": { ... }
  },
  "replies": [
    {
      "author": "@replier1",
      "text": "1차 답글 내용",
      "engagement": { ... },
      "nested_replies": [
        {
          "author": "@nested_replier",
          "text": "2차 답글 내용",
          "engagement": { ... }
        }
      ]
    }
  ],
  "metadata": {
    "total_replies_collected": 15,
    "depth": 2,
    "crawl_time": "2026-01-03T14:30:00"
  }
}
```

### 노트 생성 시 대화 흐름 유지

```markdown
# [작성자]의 Threads 스레드

## 원본 포스트
> @original_author:
> "원본 포스트 전체 텍스트"

## 답글 흐름

### @replier1의 답글
> "1차 답글 내용"
> 👍 23 | 💬 5

#### @nested_replier의 답글
> "2차 답글 내용 - 1차 답글에 대한 반응"
> 👍 8

### @replier2의 답글
> "다른 1차 답글 내용"
> 👍 45 | 💬 12

## 핵심 논점 정리
- [토론에서 도출된 핵심 포인트 1]
- [토론에서 도출된 핵심 포인트 2]

## 메타데이터
- 총 수집 답글: 15개
- 크롤링 depth: 2
- 원본 URL: [링크]
```

### 에러 처리

```
일부 답글 크롤링 실패 시:

원칙: 실패한 답글만 스킵, 나머지 계속 진행

사용자 보고:
"15개 답글 중 13개 성공, 2개 실패
- 실패 1: threads.net/@user/post/XYZ (삭제된 포스트)
- 실패 2: threads.net/@user/post/ABC (비공개 계정)

성공한 13개 답글로 정리를 진행합니다."
```

---

## 추출 데이터 구조

### Threads 포스트

```json
{
  "platform": "threads",
  "type": "post",
  "url": "https://threads.net/@username/post/C123...",
  "author": {
    "username": "@username",
    "display_name": "표시 이름",
    "verified": true
  },
  "content": {
    "text": "포스트 본문 텍스트",
    "media": ["이미지 URL 1", "이미지 URL 2"],
    "media_type": "image" | "video" | "carousel"
  },
  "engagement": {
    "likes": 123,
    "replies": 45,
    "reposts": 12,
    "quotes": 3
  },
  "metadata": {
    "timestamp": "2026-01-03T12:00:00",
    "extracted_at": "2026-01-03T14:30:00"
  }
}
```

### Instagram 포스트

```json
{
  "platform": "instagram",
  "type": "post",
  "url": "https://instagram.com/p/ABC123/",
  "author": {
    "username": "@username",
    "display_name": "표시 이름",
    "verified": true
  },
  "content": {
    "caption": "캡션 텍스트",
    "media": ["미디어 URL들"],
    "media_type": "image" | "video" | "carousel",
    "alt_text": "이미지 대체 텍스트"
  },
  "engagement": {
    "likes": 1234,
    "comments": 56,
    "views": 10000
  },
  "metadata": {
    "timestamp": "2026-01-03T12:00:00",
    "location": "장소명",
    "extracted_at": "2026-01-03T14:30:00"
  }
}
```

### Instagram 릴스

```json
{
  "platform": "instagram",
  "type": "reel",
  "url": "https://instagram.com/reel/ABC123/",
  "author": {
    "username": "@username",
    "display_name": "표시 이름",
    "verified": true
  },
  "content": {
    "caption": "캡션 텍스트",
    "video_url": "비디오 URL",
    "duration": "00:30",
    "audio": "사용된 오디오 정보"
  },
  "engagement": {
    "likes": 5000,
    "comments": 120,
    "views": 50000,
    "shares": 200
  },
  "metadata": {
    "timestamp": "2026-01-03T12:00:00",
    "extracted_at": "2026-01-03T14:30:00"
  }
}
```

---

## 주의사항 및 에러 처리

### 로그인 필요 콘텐츠

일부 콘텐츠는 로그인이 필요합니다:

**감지 패턴:**
- 페이지에 "로그인" 또는 "Log in" 버튼만 표시
- 콘텐츠 영역이 비어있거나 블러 처리
- "비공개 계정입니다" 메시지

**사용자 안내 메시지:**
```
⚠️ 로그인이 필요한 콘텐츠입니다.

다음 방법 중 하나를 시도해주세요:
1. 브라우저에서 Instagram/Threads에 로그인한 상태에서 다시 시도
2. 공개 계정의 콘텐츠 URL 제공
3. 콘텐츠를 직접 복사하여 텍스트로 제공

참고: 비공개 계정의 게시물은 스크래핑할 수 없습니다.
```

### Rate Limiting

- 연속 요청 시 **3-5초 딜레이** 권장
- 동일 세션에서 **10개 이상** 연속 스크래핑 시 경고
- 과도한 요청 시 **임시 차단** 가능성 안내

```
⚠️ Rate Limit 주의

여러 포스트를 연속으로 스크래핑하고 있습니다.
IP 차단 방지를 위해 요청 간 딜레이를 추가합니다.

진행 상황: [3/10] 포스트 처리 중...
```

### 콘텐츠 로드 실패

**재시도 전략:**
```
1차 시도: 기본 대기 (3초)
   ↓ 실패
2차 시도: 스크롤 + 대기 (5초)
   ↓ 실패
3차 시도: 페이지 새로고침 + 대기 (5초)
   ↓ 실패
→ 사용자에게 수동 확인 요청
```

**사용자 안내:**
```
⚠️ 콘텐츠 로드에 실패했습니다.

가능한 원인:
- 삭제된 게시물
- 서버 일시 오류
- 네트워크 문제

대안:
1. URL을 다시 확인해주세요
2. 잠시 후 다시 시도해주세요
3. 콘텐츠를 직접 복사하여 텍스트로 제공해주세요
```

---

## Knowledge Manager 통합

### Phase 1 입력 감지 확장

```
User input analysis:
├─ URL (http/https)
│   ├─ threads.net/* → **소셜 미디어 스크래핑** (이 스킬) ⭐
│   ├─ instagram.com/p/* → **소셜 미디어 스크래핑** (이 스킬) ⭐
│   ├─ instagram.com/reel/* → **소셜 미디어 스크래핑** (이 스킬) ⭐
│   └─ 기타 URL → 일반 Web Crawling (playwright-stealth)
├─ File path → File Processing
├─ Notion URL → Notion Import
└─ Text → Direct Processing
```

### Phase 2 콘텐츠 추출 시 활용

소셜 미디어 URL 감지 시:
1. 이 스킬의 워크플로우 자동 적용
2. playwright MCP 도구 사용
3. 추출 데이터 구조에 맞춰 파싱
4. 나머지 Phase (분석, 저장 등)는 일반 워크플로우 따름

### 출력 변환

추출된 소셜 미디어 콘텐츠 → Zettelkasten 노트:

```markdown
---
id: 202601031430
title: [작성자] - [콘텐츠 요약]
category: Social-Media
tags: [threads, 인사이트, 토론]
source: threads.net/@username/post/...
created: 2026-01-03
---

# [작성자]의 Threads 포스트

## 원문
> [포스트 전체 텍스트]

## 핵심 인사이트
- [추출된 핵심 포인트 1]
- [추출된 핵심 포인트 2]

## 반응
- 좋아요: 123 | 답글: 45 | 리포스트: 12

## 연결된 개념
- [[관련 노트 1]]
- [[관련 노트 2]]

## 메타데이터
- 플랫폼: Threads
- 원본 URL: [링크]
- 추출 시간: 2026-01-03 14:30
```

---

## 사용 예시

### 예시 1: Threads 단일 포스트

```
User: "https://threads.net/@tofukyung/post/C123abc 정리해줘"

1. URL 패턴 감지: threads.net/@* → 소셜 미디어
2. playwright 세션 시작
3. 페이지 탐색 및 대기
4. 콘텐츠 스냅샷 추출
5. 데이터 파싱 (작성자, 텍스트, 반응 수)
6. 사용자 선호도 수집 (Phase 1.5)
7. Zettelkasten 노트 생성
8. Obsidian vault에 저장
```

### 예시 2: Instagram 릴스 분석

```
User: "instagram.com/reel/ABC123 → 핵심 내용 요약"

1. URL 패턴 감지: instagram.com/reel/* → 소셜 미디어
2. playwright로 릴스 페이지 로드
3. 캡션, 반응 수치 추출
4. 비디오 스크린샷 (선택적)
5. 콘텐츠 분석
6. 요약 노트 생성
```

### 예시 3: 여러 포스트 배치 처리

```
User: "다음 Threads 포스트들 정리해줘:
- threads.net/@user1/post/A
- threads.net/@user2/post/B
- threads.net/@user3/post/C"

1. 3개 URL 모두 소셜 미디어로 감지
2. 순차 처리 (각 요청 간 3-5초 딜레이)
3. 각 포스트별 콘텐츠 추출
4. 공통 주제/인사이트 분석
5. 개별 노트 + 종합 MOC 생성
```

---

## 기술 참고사항

### Playwright MCP vs WebFetch

| 특성 | WebFetch | Playwright MCP |
|------|----------|----------------|
| JavaScript 렌더링 | ❌ | ✅ |
| 동적 콘텐츠 | ❌ | ✅ |
| 로그인 세션 유지 | ❌ | ✅ |
| 스크린샷 | ❌ | ✅ |
| 상호작용 | ❌ | ✅ (클릭, 스크롤) |
| 속도 | 빠름 | 느림 |
| 리소스 사용 | 낮음 | 높음 |

**결론**: 소셜 미디어는 **반드시 Playwright MCP** 사용

### 사용 가능한 Playwright 도구

```
mcp__playwright__browser_navigate      # 페이지 이동
mcp__playwright__browser_wait_for      # 대기 (텍스트/시간)
mcp__playwright__browser_snapshot      # 접근성 스냅샷
mcp__playwright__browser_take_screenshot  # 스크린샷
mcp__playwright__browser_click         # 클릭
mcp__playwright__browser_scroll        # 스크롤
mcp__playwright__browser_close         # 브라우저 닫기
```
