# Knowledge Manager 콘텐츠 추출 스킬

> Knowledge Manager 에이전트의 다양한 소스별 콘텐츠 추출 절차

---

## 소스별 추출 방법 개요

| 소스 유형 | 필수 도구 | 참조 스킬 |
|----------|----------|----------|
| **소셜 미디어** | `hyperbrowser scrape_webpage (stealth)` | → km-social-media.md |
| **일반 웹 페이지** | `playwright` or `hyperbrowser` | 이 문서 |
| **PDF** | `marker_single` 또는 `Read` | → pdf.md 스킬 |
| Word (DOCX) | `Read` 도구 | 이 문서 |
| Excel/CSV | `Read` 도구 | 이 문서 |
| PowerPoint | `Read` 도구 | 이 문서 |
| **이미지 (OCR)** | `Read` 도구 (Vision) | 이 문서 |
| Notion | `mcp__notion__API-get-block-children` | 이 문서 |

---

## 병렬 입력 처리 (Parallel Processing)

### 병렬 처리 조건

```
병렬 처리 가능:
✅ 여러 URL 동시 크롤링
✅ 여러 소셜 미디어 포스트 동시 수집
✅ 여러 파일 동시 읽기
✅ PDF 섹션별 병렬 변환 (목차 기반)

순차 처리 필요:
❌ 단일 브라우저 세션에서 연속 페이지 이동
❌ 의존성 있는 데이터 (A 결과로 B 결정)
```

### PDF 목차 기반 병렬 처리

```
시나리오: 100페이지 PDF 처리

Step 1: PDF 목차/구조 파악
  - 목차 페이지 탐색 (보통 1-5페이지)
  - 목차가 없으면 → 헤딩 스캔으로 자동 목차 생성

Step 2: 섹션별 페이지 범위 결정
  - 섹션 1 "서론": 페이지 0-9
  - 섹션 2 "방법론": 페이지 10-24
  - 섹션 3 "결과": 페이지 25-49
  - 섹션 4 "결론": 페이지 50-59

Step 3: 섹션별 병렬 변환 (Marker)
  marker_single "doc.pdf" --page_range "0-9" --output_dir ./section1
  marker_single "doc.pdf" --page_range "10-24" --output_dir ./section2
  ...

Step 4: 결과 통합
```

---

## PDF 파일 처리 (Claude Code)

> **Antigravity 사용자**: 자체 PDF 처리 기능 사용. 이 섹션 건너뛰기.

### 권장: Marker로 Markdown 변환 (토큰 50-70% 절감)

```bash
# PDF → Markdown 변환
marker_single "document.pdf" --output_format markdown --output_dir ./converted

# 옵션:
# --page_range "0-10"  : 처음 10페이지만 (빠른 처리)
# --force_ocr          : 스캔/수식 많은 PDF에 적합
# --use_llm            : 최고 품질 (API 키 필요)
```

**출력**: `./converted/{filename}/{filename}.md` + 이미지 폴더

### 토큰 비교

| 방법 | 페이지당 토큰 | 절감 |
|------|-------------|------|
| PDF 직접 (Claude Vision) | 1,500-3,000 | - |
| Marker → Markdown | 850-1,000 | **50-70%** |

### 스캔된 PDF OCR (pytesseract)

```python
import pytesseract
from pdf2image import convert_from_path

# PDF → 이미지 변환
images = convert_from_path('scanned.pdf', dpi=300)

# 각 페이지 OCR
text = ""
for i, image in enumerate(images):
    text += f"--- Page {i+1} ---\n"
    text += pytesseract.image_to_string(image, lang='kor+eng')  # 한국어+영어
    text += "\n\n"
```

---

## 이미지 분석 및 OCR (Claude Vision)

Claude Code에서 이미지 파일을 `Read` 도구로 로드하면 자동으로 Vision 모드로 분석됩니다.

```
Step 1: 이미지 파일 읽기
  Read("/path/to/image.png")

Step 2: Claude가 자동으로 분석
  - 다이어그램: 구조 및 관계 설명
  - 차트: 데이터 포인트 및 트렌드 추출
  - 스크린샷: UI 요소 및 텍스트 추출
  - 텍스트 이미지: OCR 수행 (텍스트 추출)

Step 3: 분석 결과를 노트에 포함
```

### 지원 이미지 형식

| 형식 | 지원 | 용도 |
|------|------|------|
| PNG | ✅ | 스크린샷, 다이어그램 |
| JPG/JPEG | ✅ | 사진, 문서 스캔 |
| GIF | ✅ | 정적 이미지 |
| WebP | ✅ | 웹 이미지 |

---

## 웹 크롤링

### 브라우저 선택 (설정 기반)

```javascript
provider = config.browser.provider  // "playwright" | "hyperbrowser"
```

### Playwright 사용 시 (기본)

```
Step 1: mcp__playwright__browser_navigate(url="[URL]")
Step 2: mcp__playwright__browser_wait_for(time=3)
Step 3: mcp__playwright__browser_snapshot()
```

### Hyperbrowser 사용 시

```javascript
mcp__hyperbrowser__scrape_webpage({
  url: "[URL]",
  outputFormat: ["markdown"]
})

// 소셜 미디어 (스텔스 모드)
mcp__hyperbrowser__scrape_webpage({
  url: "https://threads.net/@user/post/123",
  outputFormat: ["markdown"],
  sessionOptions: { useStealth: true }
})
```

---

## Word 문서 (DOCX)

```
Step 1: Read 도구로 파일 읽기
  Read("/path/to/document.docx")

Step 2: Claude가 자동으로 내용 추출
  - 헤딩, 리스트, 테이블 구조 인식
  - 스타일 정보 보존

Step 3: 구조화된 정보 추출
  - 섹션별 콘텐츠 분리
  - 메타데이터 추출
```

---

## Excel/CSV 파일

```
Step 1: Read 도구로 파일 읽기
  Read("/path/to/data.xlsx")

Step 2: 데이터 분석
  - 트렌드 및 패턴 식별
  - 통계 요약 생성
  - 차트/시각화 데이터 추출

Step 3: 인사이트 도출
  - 주요 발견사항 정리
  - 노트용 텍스트 형식으로 변환
```

---

## Notion 가져오기

```
Step 1: Notion URL에서 Page ID 추출
  https://www.notion.so/[workspace]/[page-title]-[page-id]

Step 2: Notion MCP로 콘텐츠 가져오기
  mcp__notion__API-retrieve-a-page(page_id="...")
  mcp__notion__API-get-block-children(block_id="...")

Step 3: Notion 블록 파싱
  - paragraph → 문단
  - heading_1, heading_2, heading_3 → 헤딩
  - bulleted_list_item → 불릿 리스트
  - numbered_list_item → 번호 리스트
  - code → 코드 블록
  - quote → 인용
```

---

## 에러 처리

### 병렬 처리 중 일부 실패 시

```
원칙: 실패한 항목만 건너뛰고 나머지 계속 진행

예시:
- URL 3개 중 1개 실패 → 2개 결과로 진행
- PDF 섹션 5개 중 1개 실패 → 4개 섹션 결과 + 실패 섹션 스킵

사용자 보고:
"3개 URL 중 2개 성공, 1개 실패 (example.com - 접근 불가)
성공한 2개 콘텐츠로 분석을 진행합니다."
```

---

## 스킬 참조

- **pdf.md**: PDF 상세 처리 (OCR 포함)
- **km-social-media.md**: 소셜 미디어 전용 추출
- **km-workflow.md**: 전체 워크플로우
- **km-export-formats.md**: 내보내기 형식
