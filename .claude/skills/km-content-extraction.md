# Knowledge Manager 콘텐츠 추출 스킬

> Knowledge Manager 에이전트의 다양한 소스별 콘텐츠 추출 절차

---

## 🚨 MANDATORY TOOL CALLS (필수 도구 호출!)

**이 Phase에서 반드시 도구를 실제로 호출해야 합니다!**

### 소셜 미디어 URL (🚨 CRITICAL!)

**Threads/Instagram URL 감지 시 반드시 다음 호출:**

```tool-call
mcp__hyperbrowser__scrape_webpage({
  url: "[URL]",
  outputFormat: ["markdown"],
  sessionOptions: { useStealth: true }  // 소셜 미디어는 stealth 필수!
})
```

### ❌ 절대 금지

```
❌ WebFetch 사용 - JavaScript 렌더링 불가
❌ 도구 호출 없이 내용 추측/생성
❌ 이전 대화 기억에만 의존
❌ hyperbrowser 결과 없이 노트 작성
```

⚠️ **도구 호출 없이 응답하면 작업 실패로 간주됩니다!**

---

## 소스별 추출 방법 개요

| 소스 유형 | 🚨 필수 도구 호출 | 참조 스킬 |
|----------|------------------|----------|
| **소셜 미디어** | `hyperbrowser scrape_webpage (stealth)` ⭐ | → km-social-media.md |
| **일반 웹 페이지** | `hyperbrowser scrape_webpage` | 이 문서 |
| PDF | `marker_single` 또는 `Read` | → pdf 스킬 |
| Word (DOCX) | `Read` 도구 | → docx 스킬 |
| Excel/CSV | `Read` 도구 | → xlsx 스킬 |
| PowerPoint | `Read` 도구 | → pptx 스킬 |
| 이미지 | `Read` 도구 (Vision) | 이 문서 |
| Notion | `mcp__notion__API-get-block-children` | 이 문서 |
| Vault 종합 | `mcp__obsidian__search_vault` | 이 문서 |

---

## 병렬 입력 처리 (Parallel Input Processing) ⭐

### 개요

다중 소스 입력 시 **병렬 처리**로 속도를 높일 수 있습니다.

### 병렬 처리 조건

```
병렬 처리 가능:
✅ 여러 URL 동시 크롤링
✅ 여러 Threads/Instagram 포스트 동시 수집
✅ 여러 파일 동시 읽기
✅ 여러 Notion 페이지 동시 가져오기
✅ 여러 검색 쿼리 동시 실행

순차 처리 필요:
❌ 단일 브라우저 세션에서 연속 페이지 이동
❌ 의존성 있는 데이터 (A 결과로 B 결정)
```

### 1. 다중 URL 동시 크롤링

```
시나리오: 사용자가 3개 URL 제공
- https://example1.com/article
- https://threads.net/@user/post/123
- https://example2.com/docs

→ 3개 playwright 호출 병렬 실행:

동일 메시지에서 3개 도구 호출:
1. mcp__playwright__browser_navigate(url="example1.com/...")
2. mcp__playwright__browser_navigate(url="threads.net/...")
3. mcp__playwright__browser_navigate(url="example2.com/...")

각 결과 수집 후 통합 분석
```

### 2. PDF 목차 기반 병렬 처리 ⭐

> 페이지 번호가 아닌 **목차/섹션 구조**에 따라 분할하여 논리적 단위로 처리

```
시나리오: 100페이지 PDF 처리

Step 1: PDF 목차/구조 파악

  a) 목차 페이지 탐색 (보통 1-5페이지)
     - "목차", "Table of Contents", "Contents" 텍스트 검색
     - 페이지 번호가 포함된 목차 구조 파싱

  b) 목차가 없으면 → 헤딩 스캔 (자동 목차 생성)
     - PDF 전체를 빠르게 스캔
     - 큰 제목(H1, H2 수준 폰트)을 찾아 자동 목차 생성
     - 페이지 번호와 제목 매핑

  c) 결과 예시:
     목차 구조:
     - 1. 서론 (페이지 1-10)
     - 2. 방법론 (페이지 11-25)
     - 3. 결과 (페이지 26-50)
     - 4. 결론 (페이지 51-60)
     - 부록 (페이지 61-100)

Step 2: 섹션별 페이지 범위 결정

  목차 → 페이지 범위 매핑:
  - 섹션 1 "서론": 페이지 0-9 (10페이지)
  - 섹션 2 "방법론": 페이지 10-24 (15페이지)
  - 섹션 3 "결과": 페이지 25-49 (25페이지)
  - 섹션 4 "결론": 페이지 50-59 (10페이지)
  - 섹션 5 "부록": 페이지 60-99 (40페이지)

Step 3: 섹션별 병렬 변환 (marker_single)

  동시 실행:
  marker_single "doc.pdf" --page_range "0-9" --output_dir ./section1_서론
  marker_single "doc.pdf" --page_range "10-24" --output_dir ./section2_방법론
  marker_single "doc.pdf" --page_range "25-49" --output_dir ./section3_결과
  marker_single "doc.pdf" --page_range "50-59" --output_dir ./section4_결론
  marker_single "doc.pdf" --page_range "60-99" --output_dir ./section5_부록

Step 4: 결과 통합

  각 섹션 Markdown을 원래 목차 순서로 병합:
  1. 서론.md
  2. 방법론.md
  3. 결과.md
  4. 결론.md
  5. 부록.md

  → 전체 문서 또는 섹션별 개별 노트 생성
```

#### 목차 기반 처리의 장점

| 기존 (페이지 청크) | 개선 (목차 기반) |
|-------------------|-----------------|
| 논리적 단위 무시 | 논리적 단위 유지 |
| 문장 중간에서 잘릴 수 있음 | 섹션 완결성 보장 |
| 맥락 손실 가능 | 맥락 보존 |
| 단순 병합만 가능 | 섹션별 분석/노트 가능 |

#### 헤딩 스캔 방법 (목차 없는 PDF)

```
헤딩 스캔 로직:

1. PDF 전체 페이지 빠르게 스캔
2. 큰 폰트 사이즈 텍스트 감지 (상위 10%)
3. 패턴 매칭:
   - "1.", "1.1", "Chapter", "Section" 등 번호 패턴
   - 볼드/굵은 텍스트
   - 독립 라인 (문단 시작이 아닌 단독 라인)

4. 자동 목차 구성:
   - 감지된 헤딩들의 페이지 번호 기록
   - 계층 구조 추정 (폰트 크기 기준)
   - 섹션 범위 계산

결과 예시:
자동 생성 목차:
├─ Introduction (p.1)
├─ Literature Review (p.8)
├─ Methodology (p.22)
├─ Results (p.45)
├─ Discussion (p.78)
└─ Conclusion (p.95)
```

### 3. 다중 파일 동시 읽기

```
시나리오: 5개 문서 파일 분석 요청

→ 5개 Read 도구 병렬 호출:

동일 메시지에서:
1. Read(file_path="doc1.pdf")
2. Read(file_path="doc2.docx")
3. Read(file_path="doc3.xlsx")
4. Read(file_path="doc4.pptx")
5. Read(file_path="doc5.md")

각 결과 수집 후 통합 분석
```

### 4. 다중 Notion 페이지 동시 가져오기

```
시나리오: 관련 Notion 페이지 5개 수집

Step 1: 검색으로 관련 페이지 ID 확보
mcp__notion__API-post-search(query="AI 에이전트")

Step 2: 페이지 내용 병렬 가져오기
동일 메시지에서:
1. mcp__notion__API-get-block-children(block_id="page1_id")
2. mcp__notion__API-get-block-children(block_id="page2_id")
3. mcp__notion__API-get-block-children(block_id="page3_id")
...

Step 3: 결과 통합
```

### 5. Vault 검색 병렬화

```
시나리오: 여러 키워드로 관련 노트 검색

→ 여러 검색 쿼리 병렬 실행:

동일 메시지에서:
1. mcp__obsidian__search_vault(query="AI 에이전트")
2. mcp__obsidian__search_vault(query="MCP 프로토콜")
3. mcp__obsidian__search_vault(query="프롬프트 엔지니어링")

결과 병합 후 중복 제거
→ mcp__obsidian__read_multiple_notes로 일괄 읽기
```

### 에러 처리

```
병렬 처리 중 일부 실패 시:

원칙: 실패한 항목만 건너뛰고 나머지 계속 진행

예시:
- URL 3개 중 1개 실패 → 2개 결과로 진행
- PDF 섹션 5개 중 1개 실패 → 4개 섹션 결과 + 실패 섹션 재시도 또는 스킵

사용자 보고:
"3개 URL 중 2개 성공, 1개 실패 (example.com - 접근 불가)
성공한 2개 콘텐츠로 분석을 진행합니다."
```

---

## 2A. 웹 크롤링 (🚨 Playwright MCP MANDATORY!)

### 소셜 미디어 URL (🚨 CRITICAL - MUST USE PLAYWRIGHT!)

**다음 URL 패턴은 반드시 playwright MCP 사용:**
- `threads.net/*` → km-social-media.md 스킬 참조
- `instagram.com/p/*` → km-social-media.md 스킬 참조
- `instagram.com/reel/*` → km-social-media.md 스킬 참조

```
⚠️ WebFetch 절대 사용 금지! (JavaScript 렌더링 불가)
⚠️ 도구 호출 없이 내용 추측 금지!
```

**YOU MUST CALL 순서:**
```tool-call
1. mcp__playwright__browser_navigate(url="[URL]")
2. mcp__playwright__browser_wait_for(time=3)
3. mcp__playwright__browser_snapshot()
```

### 일반 웹 페이지 (🚨 ACTION REQUIRED!)

**Step 1: 페이지 탐색 - YOU MUST CALL:**
```tool-call
mcp__playwright__browser_navigate
- url: [사용자 제공 URL]
```

**Step 2: 동적 콘텐츠 처리 - YOU MUST CALL:**
```tool-call
mcp__playwright__browser_wait_for
- time: 3  # 3초 대기 (JavaScript 렌더링)
```

필요 시 스크롤:
```tool-call
mcp__playwright__browser_press_key
- key: "End"  # 페이지 하단으로
```

**Step 3: 시각적 요소 캡처 (선택적):**
```tool-call
mcp__playwright__browser_take_screenshot
- 그래프, 차트, 다이어그램 분석용
```

**Step 4: 콘텐츠 추출 - YOU MUST CALL:**
```tool-call
mcp__playwright__browser_snapshot
- 전체 페이지 접근성 스냅샷
- 구조화된 텍스트 콘텐츠 획득
```

### 웹 크롤링 완료 검증 (필수!)

```
□ browser_navigate 호출 완료?
□ browser_wait_for 호출 완료?
□ browser_snapshot 호출 완료?
□ 스냅샷에서 실제 콘텐츠 확인 가능?

⚠️ 위 항목 미완료 시 → 콘텐츠 분석 단계 진행 금지!
```

### 웹 크롤링 에러 처리

| 에러 | 대응 |
|------|------|
| 봇 감지/차단 | 스텔스 모드 사용, 사용자에게 보고 |
| 콘텐츠 미로드 | 대기 시간 증가, 추가 스크롤 |
| 네트워크 오류 | 지수 백오프로 재시도 |

---

## 2B. 로컬 파일 처리

### PDF 파일 (CRITICAL: Marker 우선 사용!)

```
🚀 PDF는 항상 Marker로 먼저 변환! (토큰 50-70% 절감)

Step 1: Marker로 PDF → Markdown 변환
  marker_single "document.pdf" --output_format markdown --output_dir ./converted --disable_multiprocessing

  옵션:
  - --page_range "0-10"  : 처음 10페이지만 (빠른 처리)
  - --force_ocr          : 스캔/수식 많은 PDF에 적합
  - --use_llm            : 최고 품질 (API 키 필요)

Step 2: 생성된 Markdown 파일 읽기
  - 출력 경로: ./converted/{filename}/{filename}.md
  - 이미지: ./converted/{filename}/_page_*_Figure_*.jpeg

Step 3: Markdown 구조 파싱
  - ##, ### 헤딩 기준으로 섹션 분리
  - 테이블, 코드 블록 보존
```

#### 토큰 비교

| 방법 | 페이지당 토큰 | 절감 |
|------|-------------|------|
| PDF 직접 (Claude Vision) | 1,500-3,000 | - |
| Marker → Markdown | 850-1,000 | **50-70%** |

### Word 문서 (DOCX)

```
Step 1: 파일 내용 읽기
  - Read 도구 또는 docx 스킬 사용

Step 2: 마크업 파싱
  - 헤딩, 리스트, 테이블 구조 추출
  - 스타일 정보 보존 (필요 시)

Step 3: 구조화된 정보 추출
  - 섹션별 콘텐츠 분리
  - 메타데이터 추출 (작성자, 날짜 등)
```

### Excel/CSV 파일

```
Step 1: xlsx 스킬로 데이터 로드
  - pandas DataFrame으로 변환
  - 수식 및 포맷 정보 보존

Step 2: 데이터 분석
  - 트렌드 및 패턴 식별
  - 통계 요약 생성
  - 차트/시각화 데이터 추출

Step 3: 인사이트 도출
  - 주요 발견사항 정리
  - 노트용 텍스트 형식으로 변환

CRITICAL: 수식은 항상 그대로 사용!
✅ sheet['B10'] = '=SUM(B2:B9)'
❌ sheet['B10'] = 5000  # 하드코딩 금지
```

### PowerPoint 파일

```
Step 1: pptx 스킬로 텍스트 추출
  - markitdown 사용
  - 슬라이드별 콘텐츠 분리

Step 2: 구조 보존
  - 슬라이드 제목 → 섹션 헤딩
  - 불릿 포인트 → 리스트
  - 발표자 노트 포함

Step 3: 시각 요소 처리
  - 차트/다이어그램 설명 추출
  - 이미지 대체 텍스트 포함
```

### 텍스트 파일 (TXT/MD)

```
Step 1: 직접 파일 읽기
  - Read 도구 사용
  - 인코딩 자동 감지

Step 2: 마크다운 파싱 (MD 파일)
  - 헤딩, 링크, 이미지 파싱
  - 프론트매터 추출

Step 3: 구조화
  - 섹션 분리
  - 메타데이터 생성
```

---

## 2C. 이미지 분석

```
Step 1: 이미지 파일 읽기
  - Read 도구로 이미지 로드
  - Claude Vision으로 분석

Step 2: 콘텐츠 유형 식별
  - 다이어그램: 구조 및 관계 설명
  - 차트: 데이터 포인트 및 트렌드 추출
  - 스크린샷: UI 요소 및 텍스트 추출
  - 텍스트 이미지: OCR 수행

Step 3: 시각 요소 설명
  - 이미지 내용 상세 설명 생성
  - 텍스트가 있으면 추출
  - 맥락적 해석 제공

Step 4: 노트 통합
  - 이미지 설명을 노트에 포함
  - 필요 시 이미지 첨부 폴더에 저장
```

---

## 2D. Notion 가져오기

```
Step 1: Notion 소스 식별
  - URL 패턴: https://www.notion.so/...
  - Page ID 추출

Step 2: Notion 콘텐츠 가져오기
  Notion MCP 도구 사용:
  - mcp__notion__API-post-search: 페이지 검색
  - mcp__notion__API-retrieve-a-page: 페이지 조회
  - mcp__notion__API-get-block-children: 블록 내용 가져오기
  - mcp__notion__API-query-data-source: 데이터베이스 쿼리

Step 3: Notion 블록 파싱
  지원 블록 유형:
  - paragraph → 문단
  - heading_1, heading_2, heading_3 → 헤딩
  - bulleted_list_item → 불릿 리스트
  - numbered_list_item → 번호 리스트
  - code → 코드 블록
  - quote → 인용
  - toggle → 토글
  - callout → 콜아웃
  - image → 이미지
  - bookmark → 북마크

Step 4: 중간 형식으로 변환
  - 구조 보존
  - 메타데이터 추출 (제목, 태그, 속성)
  - 중첩 블록 처리
  - 관계/링크 유지
```

---

## 2E. Vault 지식 종합 (NEW!)

기존 Obsidian 노트들을 종합하여 새로운 인사이트 노트 생성

### Step 1: 사용자 의도 파악

```
파싱할 요소:
- 주제/테마 키워드: "AI Safety", "MCP", "에이전트"
- 종합 유형:
  * 종합 정리: 모든 관련 지식 통합
  * 인사이트 도출: 노트 간 새로운 연결 발견
  * 질문 답변: vault 지식 기반 답변
  * 트렌드 분석: 시간별 학습 변화 분석
- 범위: 전체 vault / 특정 폴더 / 특정 태그
```

### Step 2: 관련 노트 검색 및 수집

```
Obsidian MCP 사용:

mcp__obsidian__search_vault
- query: [주제 키워드]

mcp__obsidian__list_notes
- folder: [특정 폴더] (옵션)

필터링 기준:
- 태그 매칭
- 제목 키워드 포함
- 콘텐츠 관련성
- 날짜 범위 (지정 시)
```

### Step 3: 노트 읽기 및 분석

```
mcp__obsidian__read_multiple_notes
- paths: [관련 노트 경로 배열]

각 노트에서 추출:
- 핵심 개념 (핵심 개념 섹션)
- 주요 인사이트
- 제기된 질문
- 언급된 연결
- 메타데이터 (태그, 카테고리, 날짜)
```

### Step 4: 교차 노트 분석

```
패턴 식별:
- 반복되는 테마
- 모순 또는 긴장
- 시간에 따른 아이디어 발전
- 지식 격차
- 예상치 못한 연결
```

### Step 5: 종합 생성

#### A. 종합 정리 (Comprehensive Summary)
- 모든 관련 지식의 통합 개요
- 하위 주제별 정리
- 개념 발전 타임라인
- 핵심 시사점

#### B. 인사이트 도출 (Insight Generation)
- 노트 간 새로운 연결
- 개별 노트에서 보이지 않던 패턴
- 시사점 및 예측
- 추가 탐구를 위한 질문

#### C. 질문 답변 (Question Answering)
- vault 지식 기반 직접 답변
- 노트로부터의 근거 제시
- 확신도 수준
- 식별된 지식 격차

#### D. 트렌드 분석 (Trend Analysis)
- 시간에 따른 사고 변화
- 새롭게 떠오르는 패턴
- 초점 또는 이해의 변화
- 향후 방향

### 종합 노트 템플릿

```markdown
# [주제] - 지식 종합 노트

## 메타 정보
- 종합 일시: YYYY-MM-DD HH:mm
- 분석된 노트 수: N개
- 주요 출처 노트: [[노트1]], [[노트2]], ...

## 핵심 인사이트 (Key Insights)

### 1. [인사이트 제목]
[인사이트 설명]
- 근거: [[출처노트1]], [[출처노트2]]
- 확신도: 높음/중간/낮음

### 2. [인사이트 제목]
...

## 주제별 종합

### [하위주제 1]
[종합 내용]
관련 노트: [[노트A]], [[노트B]]

### [하위주제 2]
...

## 발견된 패턴

### 공통 주제
- [패턴 1]: 설명
- [패턴 2]: 설명

### 흥미로운 연결
- [[노트X]] ↔ [[노트Y]]: 연결 이유

### 긴장/모순점
- [모순 1]: 설명 및 해석

## 지식 격차 (Knowledge Gaps)
- [ ] 아직 탐구되지 않은 영역
- [ ] 더 깊이 파야 할 질문

## 다음 단계 제안
1. [제안 1]
2. [제안 2]

## 원본 노트 목록
| 노트 | 핵심 기여 | 날짜 |
|------|----------|------|
| [[노트1]] | 기여 내용 | YYYY-MM-DD |
| [[노트2]] | 기여 내용 | YYYY-MM-DD |
```

---

## 특수 처리

### 배치 처리

```
여러 소스 입력 시:

1. 각 소스 순차 처리
2. 소스 추적 유지
3. 소스 간 교차 참조 식별
4. 종합 연결 맵 생성
5. 요약 보고서 생성
```

### 대용량 문서 처리

```
대용량 문서 처리 전략:

1. 청크 단위 처리
   - 섹션별 분할
   - 순차 처리
   - 결과 통합

2. 진행 상황 표시
   - 처리 중인 섹션 안내
   - 예상 완료 시간 (가능 시)

3. 품질 유지
   - 청크 간 맥락 유지
   - 연결 정보 보존
```

### 혼합 소스 처리

```
여러 유형의 소스가 함께 제공될 때:

예: URL + PDF + "이전 노트도 참고해서"

처리 순서:
1. 각 소스 유형 식별
2. 개별 추출 수행
3. 추출 결과 통합
4. 교차 참조 분석
5. 통합 노트 생성
```

---

## 스킬 참조

- **km-social-media.md**: 소셜 미디어 전용 추출
- **pdf.md**: PDF 상세 처리
- **xlsx.md**: Excel 상세 처리
- **docx.md**: Word 상세 처리
- **pptx.md**: PowerPoint 상세 처리
- **notion-knowledge-capture.md**: Notion 상세 처리
