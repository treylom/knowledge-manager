# Knowledge Manager 이미지 파이프라인 스킬

> 웹/PDF/로컬 소스에서 이미지/차트/그래프를 추출하여 Obsidian/Notion에 임베딩하는 절차

---

## 이미지 저장 컨벤션

### 저장 위치

```
Resources/images/{topic-folder}/
```

- **topic-folder**: 주제를 kebab-case로 변환 (예: `ai-agent-basics-specal1849`, `mcp-protocol-guide`)
- vault 경로: `AI_Second_Brain/Resources/images/{topic-folder}/`
- 절대 경로 (Write/Bash 사용 시): `/home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/`

### 파일명 규칙

```
{NN}-{descriptive-name}.{ext}

예시:
00-cover-main-thumbnail.jpg
01-chatbot-vs-agent.jpg
02-five-core-concepts.png
03a-scaffolding-exosuit.jpg
```

| 요소 | 규칙 | 예시 |
|------|------|------|
| NN | 2자리 순번 (00부터) | `01`, `03a` |
| descriptive-name | 이미지 설명 kebab-case | `chatbot-vs-agent` |
| ext | 원본 확장자 유지 | `png`, `jpg`, `svg`, `gif` |

---

## Obsidian 임베드 구문

```markdown
![[Resources/images/{topic-folder}/{filename}]]
```

> **NOTE**: Alt-text를 사용하지 않습니다. 빈 wikilink 문법 `![[경로]]` 사용.

**예시:**
```markdown
![[Resources/images/ai-agent-basics-specal1849/01-chatbot-vs-agent.jpg]]
![[Resources/images/ai-agent-basics-specal1849/03a-scaffolding-exosuit.jpg]]
```

---

## 본문 흐름 배치 규칙 (CRITICAL)

이미지는 **개념-시각-상세** 흐름으로 본문에 배치합니다:

```
## 핵심 개념                     ← 섹션 헤딩
개념을 설명하는 단락...           ← 개념 설명 (WHAT)
                                 ← 빈 줄
![[Resources/images/.../image]]  ← 이미지 (시각적 보강)
                                 ← 빈 줄
## 구체적 설명                   ← 다음 섹션 (HOW/WHY)
상세 내용...
```

### 배치 원칙

| 규칙 | 설명 |
|------|------|
| **개념 뒤, 상세 앞** | 개념 소개 → 이미지 → 상세 설명 순서 |
| **빈 줄 필수** | 이미지 앞뒤로 반드시 빈 줄 1개 |
| **연속 배치 금지** | 이미지 사이에 반드시 텍스트(1섹션 이상) 삽입 |
| **별도 줄** | 이미지는 항상 단독 줄 (인라인 금지) |

### 수량 가이드

| 노트 유형 | 이미지 수 |
|----------|----------|
| 원자 노트 | 1-3개 |
| MOC | 2-4개 |
| 연구 보고서 | 5-10개 |

---

## Notion 이미지 블록 템플릿

### 외부 URL 이미지 (지원)

```json
{
  "object": "block",
  "type": "image",
  "image": {
    "type": "external",
    "external": {
      "url": "https://example.com/image.png"
    },
    "caption": [
      {
        "type": "text",
        "text": {
          "content": "Figure 1: 이미지 설명"
        }
      }
    ]
  }
}
```

### 로컬 전용 이미지 (대체 처리)

Notion API는 파일 업로드를 지원하지 않으므로, 로컬 전용 이미지는 텍스트 설명으로 대체:

```json
{
  "object": "block",
  "type": "callout",
  "callout": {
    "icon": { "type": "emoji", "emoji": "🖼️" },
    "rich_text": [
      {
        "type": "text",
        "text": {
          "content": "[이미지: {description}] — Obsidian vault Resources/images/{topic-folder}/{filename} 에서 확인"
        }
      }
    ]
  }
}
```

---

## 소스별 이미지 추출 방법

### A. 웹 URL

```
1. playwright navigate → 페이지 로드
2. browser_snapshot → 접근성 트리에서 img/figure 요소 파싱
3. 각 이미지 요소에서 수집:
   - src URL (절대 경로로 변환)
   - alt 텍스트
   - 주변 heading/caption 컨텍스트
   - 이미지 유형 판별 (photo, chart, diagram, icon)
4. canvas/SVG 차트 감지:
   - <canvas>, <svg> 요소 → browser_take_screenshot (요소 지정)
   - data-viz 클래스 (chart, graph, plot 등) 감지
5. Image Catalog 생성 → Lead에게 보고
```

### B. PDF (marker 출력)

```
1. marker_single 실행 후 km-temp/{name}/images/ 자동 생성
2. images/ 폴더 스캔: Glob("km-temp/{name}/images/*")
3. 마크다운 내 이미지 참조와 매핑:
   - ![](images/img001.png) → km-temp/{name}/images/img001.png
4. 각 이미지의 마크다운 위치(섹션/페이지) 기록
5. Image Catalog 생성
```

### C. 로컬 파일/이미지

```
1. Read 도구로 이미지 직접 분석 (Claude Vision)
2. 이미지 설명 생성
3. 원본 파일 경로 기록
4. vault Resources/images/{topic-folder}/로 복사 필요 여부 판단
```

---

## 이미지 필터링 규칙

### 제외 대상 (자동 필터링)

| 필터 | 기준 | 이유 |
|------|------|------|
| **아이콘** | 크기 < 100x100px | 콘텐츠 가치 없음 |
| **광고** | 도메인: `ads.`, `doubleclick.`, `googlesyndication.` 등 | 스팸 |
| **트래킹 픽셀** | 크기 = 1x1px | 무의미 |
| **네비게이션 UI** | class/id에 `nav`, `menu`, `header`, `footer` 포함 | UI 요소 |
| **소셜 아이콘** | class에 `social`, `share` 포함 | 반복 요소 |
| **base64 인라인** | src가 `data:image/` + 크기 < 5KB | 주로 아이콘 |

### 포함 우선순위

| 우선순위 | 유형 | 식별 방법 |
|---------|------|----------|
| 1 (필수) | **차트/그래프** | `<canvas>`, `<svg>`, class에 `chart`/`graph`/`plot` |
| 2 (필수) | **다이어그램** | `<figure>`, class에 `diagram`/`architecture`/`flow` |
| 3 (권장) | **스크린샷** | 큰 이미지 (>400px), class에 `screenshot`/`capture` |
| 4 (권장) | **사진/일러스트** | `<figure>` + `<figcaption>`, alt-text 있음 |
| 5 (선택) | **장식 이미지** | alt="" 또는 role="presentation" |

---

## 이미지 크기 최적화

| 조건 | 처리 |
|------|------|
| **< 2MB** | 원본 그대로 저장 |
| **2-5MB** | 사용자에게 리사이즈 안내 (ImageMagick 권장) |
| **> 5MB** | 저장 전 경고 + 리사이즈 강력 권장 |

```bash
# 리사이즈 예시 (ImageMagick 설치 시)
convert "{input}" -resize 1920x1920\> -quality 85 "{output}"
```

---

## Alt-text 생성 절차

### Claude Vision 활용

```
1. Read 도구로 이미지 파일 로드
2. Claude Vision이 자동으로 이미지 분석
3. alt-text 생성 프롬프트:
   "이 이미지를 1-2문장으로 설명해주세요.
    차트/그래프인 경우 데이터 트렌드를 포함하세요."
4. 결과를 Obsidian 임베드 구문의 alt-text로 사용
```

### Alt-text 작성 규칙

| 이미지 유형 | alt-text 형식 | 예시 |
|------------|--------------|------|
| 차트 | "{차트유형}: {주요 데이터}" | "막대 차트: 2023-2025 AI 채택률 30%→67% 상승" |
| 다이어그램 | "{다이어그램유형}: {핵심 구조}" | "아키텍처 다이어그램: MCP 클라이언트-서버 3계층 구조" |
| 스크린샷 | "{앱/화면}: {표시 내용}" | "Claude Code CLI: 멀티 에이전트 실행 화면" |
| 사진 | "{주제}: {장면 설명}" | "컨퍼런스 발표: Anthropic CEO 키노트" |

---

## Obsidian 노트 생성 (이미지 참조 포함 노트)

이미지 임베드가 포함된 노트를 Obsidian에 생성할 때의 도구 우선순위:

```bash
OBSIDIAN_CLI="/mnt/c/Program Files/Obsidian/Obsidian.com"

# 1순위: Obsidian CLI create
"$OBSIDIAN_CLI" create path="Zettelkasten/[카테고리]/[노트명].md" content="[이미지 임베드 포함 마크다운]"

# CLI 실패 시: Obsidian MCP fallback
mcp__obsidian__create_note({ path: "Zettelkasten/[카테고리]/[노트명].md", content: "[마크다운]" })

# MCP 실패 시: Write 도구 fallback
Write(file_path="/home/tofu/AI/AI_Second_Brain/Zettelkasten/[카테고리]/[노트명].md", content="[마크다운]")
```

> **경로 규칙**: CLI/MCP는 vault root 기준 상대 경로. Write 도구는 절대 경로.

---

## Main Lead 전용 저장 프로토콜 (CRITICAL)

### 파일 쓰기는 Main Lead만 수행!

```
⚠️ Task 에이전트(content-extractor 등)는 이미지 다운로드/저장 금지!
⚠️ 워커는 Image Catalog만 생성하여 보고!
⚠️ 실제 파일 저장은 Main Lead가 Phase 5.25에서 직접 수행!
```

### Phase 5.25 저장 워크플로우

```bash
# 1. 디렉토리 생성
mkdir -p /home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/

# 2. 웹 이미지 다운로드
curl -sLo "/home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/{NN}-{desc}.{ext}" "{url}"

# 3. PDF 이미지 복사
cp km-temp/{name}/images/{file} "/home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/{NN}-{desc}.{ext}"

# 4. 다운로드 실패 시 Playwright 스크린샷 폴백
mcp__playwright__browser_take_screenshot({
  ref: "{element-ref}",
  element: "{element-description}",
  filename: "/home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/{NN}-screenshot.{ext}"
})
```

### 저장 후 검증

```
□ Glob("AI_Second_Brain/Resources/images/{topic-folder}/*") → 파일 존재 확인
□ 각 파일 크기 > 0 확인
□ 노트 내 ![[Resources/images/...]] 구문과 실제 파일 1:1 매핑 확인
```

---

## 단일 에이전트 인라인 모드 (Single-Agent / Mobile)

> AT 모드에서는 content-extractor가 Image Catalog를 생성하고 Lead가 Phase 5.25에서 소비합니다.
> 단일 에이전트 / 모바일에서는 같은 에이전트가 추출과 저장을 모두 수행하므로,
> Image Catalog 파일이 불필요합니다. 메모리 내 리스트로 처리합니다.

### 인라인 워크플로우

```
STEP 2 (콘텐츠 추출) 중:
  1. 페이지 크롤링 / PDF 변환과 동시에 이미지 정보 수집
  2. 필터링 규칙 적용 (위 "이미지 필터링 규칙" 참조)
  3. 결과를 메모리에 보관:
     collected_images = [
       { idx: 1, type: "chart", source: "web", url: "https://...",
         context: "Figure 1: ...", placement: "After 데이터 section" },
       ...
     ]

STEP 5 (노트 생성) 중:
  1. mkdir -p Resources/images/{topic-folder}/
  2. FOR each image in collected_images:
     a. 파일명 생성: {NN}-{desc}.{ext}
     b. 다운로드: curl -sLo "{path}" "{url}"
     c. 실패 시: Playwright 스크린샷 폴백
     d. 본문 흐름에 맞춰 삽입: ![[Resources/images/{topic-folder}/{filename}]]
  3. 검증: Glob + 파일 크기 > 0 확인
```

### image_extraction 모드별 제한

| 환경 | image_extraction | 최대 이미지 수 | 우선순위 | 파일 크기 제한 |
|------|-----------------|--------------|---------|--------------|
| **웹/PDF (기본)** | **auto** | 10개 | 1-2 (차트/다이어그램) | 2MB |
| **모바일** | **auto** | 5개 | 1-2 (차트/다이어그램) | 2MB |
| **AT (명시적 true)** | true | 무제한 | 1-4 | 5MB (경고) |
| **소셜미디어/Vault종합** | false | - | - | - |
| **"이미지도" 키워드** | true | 무제한 | 1-4 | 5MB |
| **"텍스트만" 키워드** | false | - | - | - |

> **auto가 기본값**: 웹/PDF 소스에서는 질문 없이 차트/다이어그램을 자동 추출합니다.

---

## Image Catalog 형식 (content-extractor → Lead 보고용)

```markdown
### Image Catalog
| # | Type | Source | URL/Path | Context | Alt-text Hint | Placement |
|---|------|--------|----------|---------|---------------|-----------|
| 1 | chart | web | https://... | "Figure 1: Revenue" | Revenue growth chart | After 데이터 section |
| 2 | diagram | pdf-p5 | km-temp/doc/images/005.png | "Architecture" | System architecture | In 아키텍처 note |
| 3 | screenshot | web | https://... | "UI Preview" | Dashboard interface | After UI section |
```

**컬럼 설명:**

| 컬럼 | 설명 |
|------|------|
| Type | `chart`, `diagram`, `screenshot`, `photo`, `illustration` |
| Source | `web`, `pdf-p{N}` (페이지 번호), `local` |
| URL/Path | 원본 이미지 URL 또는 로컬 경로 |
| Context | 이미지 주변 텍스트/캡션 |
| Alt-text Hint | 예상 alt-text (content-extractor가 제안) |
| Placement | 노트 내 삽입 위치 제안 |

---

## 스킬 참조

- **km-content-extraction.md**: 소스별 추출 방법 (2F. Image Extraction Pipeline)
- **km-export-formats.md**: Obsidian/Notion 이미지 임베딩 (5A/5B)
- **knowledge-manager-at.md**: Phase 5.25 이미지 저장 워크플로우
