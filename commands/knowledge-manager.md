---
description: 지식 관리 에이전트 - 다양한 소스에서 콘텐츠를 추출하고 여러 형식으로 내보내기
allowed-tools: Task, Read, Write, Bash, Glob, Grep, mcp__obsidian__*, mcp__notion__*, mcp__playwright__*, WebFetch, AskUserQuestion
---

# Knowledge Manager 호출

---

## 🛑 STEP 1: 사용자 선호도 확인 (필수 - 먼저 실행!)

**⚠️ 콘텐츠 처리/읽기 전에 반드시 AskUserQuestion으로 아래 질문을 먼저 하세요!**

```
콘텐츠를 어떻게 정리할지 몇 가지 확인이 필요합니다:

📊 **상세 수준 (Detail Level)**
   1. 요약 (Summary) - 핵심만 간략히 (1-2 페이지)
   2. 보통 (Standard) - 주요 내용 + 약간의 설명 (3-5 페이지)
   3. 상세 (Detailed) - 모든 내용을 꼼꼼히 (5+ 페이지)

🎯 **중점 영역 (Focus Area)** - 여러 개 선택 가능
   A. 개념/이론 (Concepts) - 핵심 아이디어와 원리
   B. 실용/활용 (Practical) - 사용법, 예시, 튜토리얼
   C. 기술/코드 (Technical) - 구현, 아키텍처, 코드
   D. 인사이트 (Insights) - 시사점, 의견, 분석
   E. 전체 균형 (Balanced) - 모든 영역 균형있게

📝 **노트 분할 방식 (Note Structure)**
   ① 단일 노트 - 모든 내용을 하나의 노트에
   ② 주제별 분할 - 주요 주제마다 별도 노트 (MOC 포함)
   ③ 원자적 분할 - 최대한 작은 단위로 분할 (Zettelkasten 원칙)
   ④ 3-tier 계층적 - 메인MOC + 카테고리MOC + 원자노트 (대용량 문서 권장)

🔗 **연결 수준 (Connection Level)**
   - 최소: 태그만 추가
   - 보통: 태그 + 관련 노트 링크 제안
   - 최대: 태그 + 링크 + 기존 노트와 자동 연결 탐색

예시 답변: '3, A+B, ④, 최대' 또는 '상세하게, 실용 위주로, 3-tier'

기본값(3.상세, E.전체, ④3-tier, 최대)을 사용하시겠습니까?

💡 3-tier란? 개요 노트 + 주제별 노트 + 원자적 노트로 계층 구조화
```

### 퀵 프리셋 (사용자 키워드 감지 시 자동 적용)

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
