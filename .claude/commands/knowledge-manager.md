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

## 🚨 STEP 2: PDF 처리 (Claude Code 전용 - 한글 경로 버그 주의!)

> **Antigravity 환경**: 자체 PDF 처리 기능이 있으므로 이 섹션 건너뛰기.
> **Claude Code 환경**: 아래 규칙 필수 적용.

**PDF 파일인 경우, 경로 확인 후 적절한 방법으로 변환합니다.**

### ❌ 절대 금지 (Claude Code에서 CRITICAL)
```
❌ 한글 경로 PDF를 Read로 직접 읽기 → UTF-8 에러 발생!
   예: Read("C:\바탕 화면\문서.pdf") → 실패!
✅ 영어 경로 PDF는 Read로 직접 읽기 가능
   예: Read("C:\Users\user\AI\doc.pdf") → 성공!
```

### 🔍 Step 2-0: 경로 확인 (한글/특수문자 감지) - 먼저 확인!

**Claude Code의 알려진 버그 (GitHub Issue #18285, #14392)**:
한글이 포함된 경로에서 Read/도구들이 UTF-8 인코딩 문제로 실패합니다.

| 경로 유형 | 예시 | 처리 방법 |
|----------|------|----------|
| **영어만 경로** | `C:\Users\user\AI\doc.pdf` | **Read로 직접 읽기** ✅ |
| **한글 포함 경로** | `C:\Users\user\바탕 화면\문서.pdf` | /pdf 스킬 또는 marker |

**한글 경로 감지 패턴:**
- 경로에 한글 포함 (가-힣, 예: 바탕 화면, 문서, 석사논문)
- 경로에 한글 폴더명 (예: `\바탕 화면\`, `\다운로드\`)

### ✅ Step 2-1: 영어 경로 → Read로 직접 읽기
```
Read("C:\Users\user\AI\document.pdf")
```
→ 영어 경로는 Read 도구가 정상 작동

### ✅ Step 2-2: 한글 경로 → /pdf 스킬 호출
```
/pdf "C:\Users\user\바탕 화면\문서.pdf"
```
→ 구조화된 Markdown으로 변환됨

### ✅ Step 2-3: /pdf 실패 시 → marker_single 사용
```bash
mkdir -p ./km-temp
marker_single "C:\Users\user\바탕 화면\문서.pdf" --output_format markdown --output_dir ./km-temp
```
→ marker는 한글 경로를 정상 처리함
→ 변환 후 `Read("./km-temp/파일명/파일명.md")`로 읽기

> ⚠️ **한글 경로에서 Read 직접 사용 금지! UTF-8 에러 발생!**
> ⚠️ **영어 경로는 Read로 바로 읽어도 됩니다.**

---

## 📋 실행 순서 요약

```
1. AskUserQuestion으로 선호도 질문 (또는 퀵 프리셋 감지)
2. 사용자 응답 대기
3. PDF인 경우 (Claude Code만):
   → 경로 확인 → 영어면 /pdf, 한글이면 marker
   (Antigravity는 자체 PDF 처리 사용)
4. 콘텐츠 추출/읽기 (변환된 Markdown)
5. Task 에이전트로 knowledge-manager 실행
```

## 사용자 요청 내용

$ARGUMENTS
