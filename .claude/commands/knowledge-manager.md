---
description: 지식 관리 에이전트 - 다양한 소스에서 콘텐츠를 추출하고 여러 형식으로 내보내기
allowed-tools: Task, Read, Write, Bash, Glob, Grep, mcp__obsidian__*, mcp__notion__*, mcp__playwright__*, WebFetch, AskUserQuestion
---

# Knowledge Manager 호출

---

## 🛑 STEP 1: 사용자 선호도 확인 (필수 - 가장 먼저 실행!)

**⚠️ 콘텐츠 처리/읽기 전에 반드시 아래 AskUserQuestion을 그대로 호출하세요!**
**⚠️ 4개 질문을 한 번의 호출로 모두 물어봅니다!**

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

> 💡 3-tier란? 개요 노트 + 주제별 노트 + 원자적 노트로 계층 구조화

### 퀵 프리셋 (사용자 키워드 감지 시 질문 스킵)

| 사용자 표현 | 프리셋 | 질문 스킵 |
|------------|--------|----------|
| "빠르게", "간단히" | 1, E, ①, 최소 | ✅ |
| "꼼꼼히", "자세히" | 3, E, ③, 최대 | ✅ |
| "기본으로", "기본" | 3, E, ④, 최대 | ✅ |
| 키워드 없음 | - | ❌ 질문 필수 |

---

## 🔄 STEP 1.5: PDF 처리 방식 확인 (PDF인 경우 필수!)

**PDF 파일인 경우, STEP 1 직후 반드시 이 질문을 하세요:**

```json
AskUserQuestion({
  "questions": [
    {
      "question": "이전에 'Prompt is too long' 오류가 발생했거나 대용량 PDF입니까? /pdf 스킬로 처리하시겠습니까?",
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

**응답에 따른 처리:**
- **"아니오"** → STEP 2로 진행 (Read로 직접 읽기 시도)
- **"예"** → marker_single로 전체 PDF 변환 후 변환된 MD 읽기

---

## 🚨 STEP 2: PDF 처리

**STEP 1.5에서 "예"를 선택한 경우 marker_single로 변환:**

```bash
mkdir -p ./km-temp
marker_single "파일.pdf" --output_format markdown --output_dir ./km-temp
```

→ 변환 후 `Read("./km-temp/파일명/파일명.md")`로 읽기

---

## 📋 실행 순서 요약

```
1. STEP 1: AskUserQuestion으로 선호도 질문 (또는 퀵 프리셋 감지)
2. STEP 1.5: PDF인 경우 → PDF 처리 방식 질문 (필수!)
   - "아니오" → Read로 직접 읽기
   - "예" → marker_single로 전체 변환
3. STEP 2: PDF 처리 실행 (marker_single 변환)
4. 콘텐츠 추출/읽기 (변환된 Markdown)
5. Task 에이전트로 knowledge-manager 실행
```

## 사용자 요청 내용

$ARGUMENTS
