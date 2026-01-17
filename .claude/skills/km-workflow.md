# Knowledge Manager 워크플로우

> 전체 6단계 워크플로우 가이드

---

## 워크플로우 개요

```
Phase 0: 설정 로드
    ↓
Phase 1: 입력 소스 감지
    ↓
Phase 1.5: 사용자 선호도 수집
    ↓
Phase 2: 콘텐츠 추출
    ↓
Phase 3: 콘텐츠 분석
    ↓
Phase 4: 출력 형식 선택
    ↓
Phase 5: 내보내기 실행
    ↓
Phase 6: 검증 및 보고
```

---

## Phase 0: 설정 로드 (CRITICAL)

**모든 작업 전 반드시 실행**

```javascript
// 1. 설정 파일 읽기
config = Read("km-config.json")

// 2. 필수 항목 확인
if (!config) {
  // 설정 없음 → 셋업 위저드 안내
  return "설정 파일이 없습니다. /knowledge-manager setup 을 실행해주세요."
}

// 3. 저장소 설정 로드
storage = {
  primary: config.storage.primary,
  obsidian: config.storage.obsidian,
  notion: config.storage.notion,
  local: config.storage.local
}

// 4. 브라우저 설정 로드
browser = {
  provider: config.browser.provider,
  hyperbrowser: config.browser.hyperbrowser
}
```

---

## Phase 1: 입력 소스 감지

### 입력 유형 판별

| 입력 패턴 | 유형 | 처리 방법 |
|----------|------|----------|
| `https://threads.net/*` | 소셜 미디어 | → km-browser-abstraction (stealth 권장) |
| `https://instagram.com/*` | 소셜 미디어 | → km-browser-abstraction (stealth 권장) |
| `https://*` | 일반 웹 | → km-browser-abstraction |
| `*.pdf` | PDF 파일 | → Read 도구 |
| `*.docx` | Word 파일 | → Read 도구 |
| `*.xlsx` | Excel 파일 | → Read 도구 |
| `notion.so/*` | Notion 페이지 | → Notion MCP |
| "종합해줘" 키워드 | Vault 종합 | → 기존 노트 검색 |

### 소셜 미디어 URL 자동 감지

```javascript
function detect_input_type(input) {
  // 소셜 미디어 패턴
  const socialPatterns = [
    /threads\.net\//,
    /instagram\.com\/p\//,
    /instagram\.com\/reel\//
  ]

  if (socialPatterns.some(p => p.test(input))) {
    return {
      type: "social_media",
      platform: detect_platform(input),
      requiresStealth: true
    }
  }

  // 일반 URL
  if (/^https?:\/\//.test(input)) {
    return { type: "web_url" }
  }

  // 파일 경로
  if (/\.(pdf|docx|xlsx|pptx|md)$/i.test(input)) {
    return { type: "file", format: get_extension(input) }
  }

  // 키워드 감지
  if (/종합|인사이트|연결/.test(input)) {
    return { type: "vault_synthesis" }
  }

  return { type: "unknown" }
}
```

---

## Phase 1.5: 사용자 선호도 수집

### 기본 질문 (AskUserQuestion 사용)

```
AskUserQuestion:
  questions:
    - question: "얼마나 상세하게 정리할까요?"
      header: "Detail"
      options:
        - label: "간략하게"
          description: "핵심만 요약 (1-2개 노트)"
        - label: "보통 (권장)"
          description: "균형잡힌 상세도"
        - label: "상세하게"
          description: "모든 정보 포함 (다수 노트)"

    - question: "어떤 내용에 중점을 둘까요?"
      header: "Focus"
      options:
        - label: "이론/개념"
          description: "정의, 원리, 배경 중심"
        - label: "실용/적용"
          description: "사용법, 예시, 적용 중심"
        - label: "균형 (권장)"
          description: "이론과 실용 모두"
```

### 선호도 매핑

| 선호도 | 값 | 동작 |
|--------|------|------|
| 상세 수준 | 1-3 | 노트 분리 정도 결정 |
| 중점 영역 | T/P/E | 추출 내용 필터링 |
| 노트 구조 | 1-4 | 단일 vs 계층 구조 |
| 연결 수준 | min/normal/max | 기존 노트 연결 정도 |

---

## Phase 2: 콘텐츠 추출

### 브라우저 추상화 레이어 사용

→ `km-browser-abstraction.md` 참조

```javascript
// 설정된 provider에 따라 자동 선택
content = scrape_url(url, {
  stealth: inputType.requiresStealth
})
```

### 파일 처리

```javascript
// PDF/DOCX 등
content = Read(filePath)
```

### 추출 검증

```
□ 도구가 실제로 호출되었는가?
□ 콘텐츠가 비어있지 않은가?
□ 에러 메시지가 없는가?
```

---

## Phase 3: 콘텐츠 분석

### Zettelkasten 원칙 적용

1. **원자성**: 하나의 아이디어 = 하나의 노트
2. **자기완결성**: 노트만 봐도 이해 가능
3. **연결성**: 관련 개념 간 링크

### 분석 절차

```
1. 핵심 개념 추출
   - 정의, 원리, 방법론
   - 예시, 사례, 적용

2. 구조 파악
   - 계층 관계
   - 인과 관계
   - 비교/대조

3. 연결점 식별
   - 기존 지식과의 연결
   - 관련 주제
```

### 상세 수준별 처리

| 수준 | 노트 수 | 상세도 |
|------|---------|--------|
| 1 (간략) | 1-2개 | 핵심만 |
| 2 (보통) | 3-5개 | 주요 개념별 |
| 3 (상세) | 5-10+개 | 모든 아이디어 |

---

## Phase 4: 출력 형식 선택

### 설정 기반 자동 선택

```javascript
// Primary 저장소 확인
primary = config.storage.primary

switch (primary) {
  case "obsidian":
    format = "zettelkasten"
    break
  case "notion":
    format = "notion"
    break
  case "local":
    format = "markdown"
    break
}
```

### 사용자 선택 (옵션)

```
AskUserQuestion:
  question: "어떤 형식으로 저장할까요?"
  header: "Format"
  options:
    - label: "Obsidian"
      description: "Zettelkasten 노트로 저장"
    - label: "Notion"
      description: "Notion 페이지로 저장"
    - label: "Markdown"
      description: "로컬 Markdown 파일로 저장"
```

---

## Phase 5: 내보내기 실행

### 저장소 추상화 레이어 사용

→ `km-storage-abstraction.md` 참조

```javascript
// 설정된 저장소에 자동 저장
save_note(relativePath, content)
```

### 병렬 저장 (다중 노트)

```javascript
// 여러 노트를 동시에 저장
notes.forEach(note => {
  save_note(note.path, note.content)
})
```

### 저장 검증 (CRITICAL)

```
□ 실제 도구가 호출되었는가? (JSON 출력만 금지!)
□ 성공 응답을 받았는가?
□ 모든 노트가 저장되었는가?
```

---

## Phase 6: 검증 및 보고

### 최종 보고 템플릿

```markdown
## ✅ 처리 완료!

### 입력
- 소스: {url 또는 파일명}
- 유형: {웹 / 파일 / 소셜 미디어}

### 추출된 콘텐츠
- 주요 개념: {N}개
- 핵심 인사이트: {요약}

### 저장된 노트
| 제목 | 경로 | 상태 |
|------|------|------|
| {노트1} | {경로1} | ✅ |
| {노트2} | {경로2} | ✅ |

### 연결된 기존 노트
- [[관련노트1]]
- [[관련노트2]]
```

### 에러 발생 시

```markdown
## ⚠️ 일부 문제 발생

### 성공
- {노트1}: ✅ 저장됨

### 실패
- {노트2}: ❌ 저장 실패
  - 원인: {에러 메시지}
  - 대안: 콘텐츠가 아래에 출력됨

### 수동 저장이 필요한 콘텐츠
```{노트 내용}```
```

---

## 특수 키워드 처리

| 키워드 | 동작 |
|--------|------|
| "종합해줘" | Vault 노트 종합 분석 |
| "도식화해줘" | 다이어그램 생성 |
| "연결 감사" | 고아 노트/깨진 링크 검사 |
| "상세하게" | 3-Tier 계층 구조 적용 |

---

## 품질 체크리스트

```
입력 처리:
□ 입력 유형 정확히 감지?
□ 적절한 도구 선택?

콘텐츠 분석:
□ 원자적 아이디어 추출?
□ 메타데이터 완전?

저장:
□ 도구 실제 호출? (JSON만 금지)
□ 성공 응답 확인?
□ 올바른 경로?

보고:
□ 사용자에게 결과 안내?
□ 에러 발생 시 대안 제시?
```
