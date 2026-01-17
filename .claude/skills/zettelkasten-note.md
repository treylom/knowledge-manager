# Zettelkasten 노트 템플릿

> Obsidian 및 Markdown 노트의 표준 형식

---

## 기본 노트 템플릿

```markdown
---
id: {YYYYMMDDHHmm}
title: {노트 제목}
created: {YYYY-MM-DDTHH:mm:ss}
modified: {YYYY-MM-DDTHH:mm:ss}
tags: [{태그1}, {태그2}, {태그3}]
category: {카테고리}
source: {원본 URL 또는 파일명}
type: {atomic | moc | literature | permanent}
---

# {노트 제목}

## 핵심 개념

{2-3문장으로 핵심 아이디어 설명}

## 상세 설명

{필요시 추가 설명}

## 예시/적용

{구체적인 예시나 적용 방법}

## 관련 노트

- [[관련노트1]] - {연결 이유}
- [[관련노트2]] - {연결 이유}

## 참고문헌

- {원본 출처 정보}

---

*Source: {URL 또는 파일명}*
*Created: {날짜}*
```

---

## 노트 유형별 템플릿

### 1. Atomic Note (원자적 노트)

단일 아이디어/개념을 담는 기본 노트:

```markdown
---
type: atomic
tags: [{주제}, {키워드1}, {키워드2}]
---

# {개념명}

{개념의 정의 또는 핵심 설명 - 2-3문장}

## 왜 중요한가

{이 개념의 중요성}

## 어떻게 적용하는가

{실제 적용 방법}

## 관련 노트

- [[상위개념]] - 이 개념의 상위 범주
- [[하위개념]] - 이 개념의 구체적 사례
- [[관련개념]] - 함께 알면 좋은 개념
```

### 2. MOC (Map of Content)

여러 노트를 엮는 허브 노트:

```markdown
---
type: moc
tags: [MOC, {주제}]
---

# {주제} - MOC

## 개요

{주제에 대한 개괄적 설명}

## 핵심 개념

### 기초
- [[개념1]] - {한줄 요약}
- [[개념2]] - {한줄 요약}

### 심화
- [[개념3]] - {한줄 요약}
- [[개념4]] - {한줄 요약}

### 적용
- [[사례1]] - {한줄 요약}
- [[사례2]] - {한줄 요약}

## 학습 경로

1. 먼저 [[기초개념]]을 이해
2. 그 다음 [[심화개념]]으로
3. 마지막으로 [[적용사례]] 학습

## 관련 MOC

- [[상위MOC]]
- [[관련MOC]]
```

### 3. Literature Note (문헌 노트)

책, 논문, 아티클 요약:

```markdown
---
type: literature
tags: [{주제}, {저자}, {출처유형}]
source: {URL 또는 서지정보}
author: {저자명}
published: {발행일}
---

# {문헌 제목}

## 요약

{전체 요약 - 3-5문장}

## 핵심 인사이트

1. **{인사이트1 제목}**
   {설명}

2. **{인사이트2 제목}**
   {설명}

3. **{인사이트3 제목}**
   {설명}

## 인용구

> "{인상적인 인용문}"
> — {저자명}

## 내 생각

{이 문헌에 대한 개인적 반응/생각}

## 생성된 원자 노트

- [[원자노트1]] - {이 문헌에서 추출}
- [[원자노트2]] - {이 문헌에서 추출}
```

---

## 메타데이터 규칙

### 필수 필드

| 필드 | 형식 | 예시 |
|------|------|------|
| `id` | YYYYMMDDHHmm | 202601171430 |
| `title` | 문자열 | "MCP 프로토콜 개요" |
| `created` | ISO 8601 | 2026-01-17T14:30:00 |
| `tags` | 배열 | [AI, MCP, 프로토콜] |

### 선택 필드

| 필드 | 용도 |
|------|------|
| `source` | 원본 URL/파일 |
| `author` | 저자명 |
| `category` | 분류 폴더 |
| `parent` | 상위 MOC 링크 |
| `type` | 노트 유형 |

### 태그 규칙

```
형식: 소문자, 하이픈 연결
예시: ai-research, prompt-engineering, mcp-protocol

계층: 슬래시 사용
예시: ai/llm, ai/agent, programming/python

상태: status/ 접두사
예시: status/draft, status/review, status/done
```

---

## 파일명 규칙

### 기본 형식

```
{제목} - {YYYY-MM-DD-HHmm}.md

예시:
MCP 프로토콜 개요 - 2026-01-17-1430.md
```

### MOC 파일명

```
{주제}-MOC.md

예시:
AI-연구-MOC.md
프롬프트엔지니어링-MOC.md
```

### 금지 문자

```
/ \ : * ? " < > |

대체:
/ → -
: → -
```

---

## 폴더 구조

```
Zettelkasten/
├── AI-연구/
│   ├── MCP 프로토콜 개요 - 2026-01-17-1430.md
│   └── AI 에이전트 패턴 - 2026-01-15-1000.md
├── 프로그래밍/
│   └── ...
├── 생산성/
│   └── ...
└── _MOC/
    ├── AI-연구-MOC.md
    └── 프로그래밍-MOC.md

Research/
├── {프로젝트명}/
│   ├── {제목}-MOC.md
│   └── 01-{챕터}/
│       └── ...
```

---

## Wikilinks 규칙

### 기본 링크

```markdown
[[노트제목]]
```

### 별칭 사용

```markdown
[[노트제목|표시할 텍스트]]
```

### 폴더 포함

```markdown
[[폴더명/노트제목]]
```

### 헤딩 링크

```markdown
[[노트제목#섹션명]]
```

---

## 저장 경로 (설정 기반)

### Obsidian 사용 시

```javascript
// config.storage.obsidian.vaultPath 기준 상대 경로
path = `${config.storage.obsidian.defaultFolder}/${category}/${title} - ${timestamp}.md`

// 예: Zettelkasten/AI-연구/노트제목 - 2026-01-17-1430.md
```

### Local 사용 시

```javascript
// config.storage.local.outputPath 기준
path = `${config.storage.local.outputPath}/Zettelkasten/${category}/${title}.md`

// 예: ./km-output/Zettelkasten/AI-연구/노트제목.md
```

---

## 품질 체크리스트

```
메타데이터:
□ id 고유한가?
□ created 정확한가?
□ tags 적절한가? (3-5개)
□ source 포함되었나?

내용:
□ 제목이 명확한가?
□ 핵심 개념이 2-3문장으로 요약되었나?
□ 원자적인가? (하나의 아이디어)
□ 자기완결적인가?

연결:
□ 관련 노트가 링크되었나?
□ Wikilinks 형식이 올바른가?
□ 연결 이유가 명시되었나?
```
