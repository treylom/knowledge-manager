# Knowledge Manager 출력 형식 스킬

> Knowledge Manager 에이전트의 다양한 출력 형식 및 내보내기 절차

---

## 🚨 FILE SAVE PROTOCOL (최우선 - 반드시 읽기!)

**모든 노트/파일 생성 시 반드시 도구를 실제로 호출해야 합니다!**

### ✅ MUST DO (필수 행동) — 3-Tier 저장 프로토콜

**Tier 1: Obsidian CLI (최우선)**
```bash
"/mnt/c/Program Files/Obsidian/Obsidian.com" create path="Zettelkasten/카테고리/노트제목 - YYYY-MM-DD-HHmm.md" content="[노트 전체 내용]"
```

**Tier 2: Obsidian MCP (CLI 실패 시)**
```tool-call
mcp__obsidian__create_note
- path: "Zettelkasten/카테고리/노트제목 - YYYY-MM-DD-HHmm.md"
- content: "[노트 전체 내용]"
```

**Tier 3: Write 도구 (MCP 실패 시)**
```tool-call
Write
- file_path: "C:\Users\treyl\OneDrive\Desktop\AI\AI_Second_Brain\Zettelkasten\카테고리\노트제목.md"
- content: "[노트 전체 내용]"
```

### ❌ NEVER DO (절대 금지!)

```json
// ❌ 이렇게 하면 실제 저장 안 됨!
{
  "path": "Zettelkasten/카테고리/노트.md",
  "content": "노트 내용..."
}
```

```
❌ JSON 형식으로 출력만 하고 끝내기
❌ "저장하겠습니다"라고만 말하고 도구 호출 안 함
❌ 노트 내용을 대화창에만 표시하고 파일 생성 안 함
❌ CLI/create_note/Write 도구 호출 없이 다음 단계 진행
```

### 저장 후 필수 검증

```
□ CLI, mcp__obsidian__create_note, 또는 Write 도구를 실제로 호출했는가?
□ 도구 응답에서 성공 메시지 확인했는가?
  - CLI: exit code 0 + 파일 경로 출력
  - MCP: "created successfully" / "Note created at..."
  - Write: 에러 없는 정상 응답
□ 모든 생성해야 할 노트에 대해 도구 호출을 완료했는가?
```

⚠️ **JSON 출력만 하고 끝내면 작업 실패로 간주됩니다!**
⚠️ **도구 호출 결과 확인 없이 "저장 완료"라고 보고하면 안 됩니다!**

---

## 지원 출력 형식 개요

| 형식 | 스킬 | 주요 용도 |
|------|------|----------|
| Obsidian | zettelkasten-note | 개인 지식 관리, 연결 노트 |
| Notion | notion-knowledge-capture | 팀 협업, 데이터베이스 |
| Markdown | 기본 | 범용, 이식성 |
| PDF | pdf | 공유, 보관, 인쇄 |
| 블로그 | 기본 | Medium, WordPress 게시 |
| 다이어그램 | drawio-diagram | 시각화, 아키텍처 |

---

## Notion 저장 (PowerShell 직접 호출 - Windows) ⚠️ CRITICAL

**MCP 도구(`mcp__notion__API-post-page`)는 파라미터 직렬화 버그로 사용 금지!**
**버그 리포트**: `Bug_Reports/Bug-2026-01-24-1905-Notion-MCP-API-post-page-이중직렬화.md`

### 워크플로우

**Step 1: JSON 페이로드 파일 생성**
```
Write 도구 사용:
- file_path: "C:\Users\treyl\OneDrive\Desktop\AI\km-temp\notion_payload.json"
- content: JSON 형식의 Notion API 페이로드
```

**Step 2: PowerShell 스크립트 생성**
```
Write 도구 사용:
- file_path: "C:\Users\treyl\OneDrive\Desktop\AI\km-temp\notion_upload.ps1"
- content: [아래 템플릿]
```

**PowerShell 템플릿:**
```powershell
$headers = @{
    'Authorization' = 'Bearer $env:NOTION_API_KEY'
    'Notion-Version' = '2022-06-28'
    'Content-Type' = 'application/json'
}
$body = Get-Content -Raw 'C:\Users\treyl\OneDrive\Desktop\AI\km-temp\notion_payload.json' -Encoding UTF8
$response = Invoke-RestMethod -Uri 'https://api.notion.com/v1/pages' -Method POST -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
$response | ConvertTo-Json -Depth 10
```

**Step 3: PowerShell 실행**
```bash
powershell -ExecutionPolicy Bypass -File "C:\Users\treyl\OneDrive\Desktop\AI\km-temp\notion_upload.ps1"
```

### 데이터베이스 ID 참조

| 용도 | Database ID (UUID 형식!) |
|------|--------------------------|
| **AI Second Brain** | `2a6e5818-0d0e-80ae-a6e3-cc8853fda844` |

### Notion 블록 타입

| 블록 타입 | JSON 키 |
|----------|---------|
| 문단 | `paragraph` |
| 제목1 | `heading_1` |
| 제목2 | `heading_2` |
| 제목3 | `heading_3` |
| 글머리 기호 | `bulleted_list_item` |
| 번호 목록 | `numbered_list_item` |
| 코드 블록 | `code` |
| 인용 | `quote` |
| **이미지 (외부 URL)** | `image` |

### ❌ 금지 패턴

```
❌ mcp__notion__API-post-page 사용
❌ MCP 도구로 parent 객체 전달 시도
❌ Notion 저장 요청 시 JSON 출력만 하고 끝내기
```

---

## 병렬 출력 처리 (Parallel Output)

> 여러 형식/문서를 **동시에** 생성하여 내보내기 속도 향상

### 병렬 처리 원칙

```
핵심 규칙:
- 독립적인 도구 호출은 같은 메시지에서 병렬 실행
- 의존성 있는 작업은 순차 처리 (예: 폴더 생성 → 파일 저장)
- 일부 실패해도 나머지 작업은 계속 진행
```

### A. 다중 형식 동시 출력

하나의 콘텐츠를 Obsidian + Notion + 기타 형식으로 동시 저장:

```
시나리오: 웹 콘텐츠 → Obsidian + Notion 동시 저장

Step 1: 콘텐츠 준비 (공통)
  - 콘텐츠 분석 완료
  - Obsidian용 마크다운 준비
  - Notion용 블록 구조 준비

Step 2: 병렬 저장 (동시 실행!)
  같은 응답에서 두 도구 호출:

  [도구 1] Bash (Obsidian CLI — Tier 1)
    "/mnt/c/Program Files/Obsidian/Obsidian.com" create path="Zettelkasten/AI-연구/주제.md" content="[Obsidian 마크다운]"
    CLI 실패 시: mcp__obsidian__create_note (Tier 2) → Write (Tier 3)

  [도구 2] Bash (Notion curl 호출) ⚠️ MCP 도구 사용 금지!
    → 아래 "Notion 저장 (curl 직접 호출)" 섹션 참조

  → 두 작업이 동시에 실행됨!

Step 3: 결과 통합 보고
  - Obsidian: [경로] 저장 완료
  - Notion: [URL] 페이지 생성 완료
```

### B. 단일 형식 다중 문서

같은 형식으로 여러 문서를 동시 생성:

```
시나리오: 5개 Zettelkasten 노트 동시 생성

Step 1: 각 노트 콘텐츠 사전 준비
  - note_1: 개념 A 노트 내용
  - note_2: 개념 B 노트 내용
  - note_3: 개념 C 노트 내용
  - note_4: 개념 D 노트 내용
  - note_5: 개념 E 노트 내용

Step 2: 병렬 저장 (5개 동시 실행!)
  같은 응답에서 5개 도구 호출:

  [도구 1] mcp__obsidian__create_note
    path: "Zettelkasten/AI-연구/개념A.md"

  [도구 2] mcp__obsidian__create_note
    path: "Zettelkasten/AI-연구/개념B.md"

  [도구 3] mcp__obsidian__create_note
    path: "Zettelkasten/AI-연구/개념C.md"

  [도구 4] mcp__obsidian__create_note
    path: "Zettelkasten/AI-연구/개념D.md"

  [도구 5] mcp__obsidian__create_note
    path: "Zettelkasten/AI-연구/개념E.md"

Step 3: 결과 보고
  ✅ 5개 노트 생성 완료
  - 개념A.md
  - 개념B.md
  - 개념C.md
  - 개념D.md
  - 개념E.md
```

### C. Notion 다중 페이지

```
시나리오: 여러 Notion 페이지 동시 생성

같은 응답에서 다중 API 호출:

[도구 1] mcp__notion__API-post-page (페이지 1)
[도구 2] mcp__notion__API-post-page (페이지 2)
[도구 3] mcp__notion__API-post-page (페이지 3)

주의: Notion API rate limit 고려
- 동시 5개 이하 권장
- 대량 생성 시 배치 처리 (5개씩 병렬)
```

### D. 의존성 처리 규칙

```
병렬 가능 (동시 실행):
├── Obsidian 노트 A + Obsidian 노트 B
├── Obsidian 노트 + Notion 페이지
├── 다이어그램 + 텍스트 노트
└── PDF 생성 + Markdown 저장

순차 필수 (의존성):
├── 폴더 생성 → 해당 폴더에 파일 저장
├── 메인 노트 생성 → MOC에 링크 추가
├── Notion 페이지 생성 → 블록 추가 (patch-block-children)
└── 다이어그램 생성 → 노트에 임베드 링크 추가
```

### E. 에러 핸들링

```
일부 실패 시 처리:

1. 실패한 항목 기록
2. 성공한 항목은 정상 보고
3. 실패 원인 분석 및 안내
4. 재시도 옵션 제공

예시 보고:
  ✅ 성공: 노트A.md, 노트B.md, 노트C.md
  ❌ 실패: 노트D.md (경로 오류)
  ⚠️ 재시도 필요: 노트D.md

  실패 원인: 폴더 "XYZ/"가 존재하지 않음
  해결 방법: 폴더 생성 후 재시도
```

### F. 병렬 출력 예시 템플릿

```
## 다중 형식 내보내기 완료!

### 생성된 파일
| 플랫폼 | 경로/URL | 상태 |
|--------|----------|------|
| Obsidian | Zettelkasten/AI-연구/주제.md | ✅ |
| Notion | notion.so/page/xxx | ✅ |
| PDF | exports/주제.pdf | ✅ |

### 처리 방식
- 병렬 처리: 3개 형식 동시 생성
- 소요 시간: ~2초 (순차 대비 ~66% 단축)
```

---

## 3-Tier 계층적 내보내기 ⭐ NEW

대용량 문서(연구보고서, 논문, 책)를 체계적으로 정리하는 3단계 계층 구조입니다.

### 구조 개요

```
Research/[프로젝트명]/
├── [제목]-MOC.md                    ← 레벨 1: 메인 MOC
│
├── 01-[챕터1명]/
│   ├── [챕터1]-MOC.md               ← 레벨 2: 카테고리 MOC
│   ├── [원자노트1].md               ← 레벨 3: 원자적 노트
│   ├── [원자노트2].md
│   └── [원자노트3].md
│
├── 02-[챕터2명]/
│   ├── [챕터2]-MOC.md
│   ├── [원자노트4].md
│   └── [원자노트5].md
│
└── ... (추가 챕터)
```

### 생성 워크플로우 (CRITICAL)

**Phase 1: 문서 구조 분석**
```
1. 전체 문서 읽기
2. 챕터/섹션 구조 파악
3. 각 챕터별 핵심 개념 추출
4. 폴더 구조 계획 수립
```

**Phase 2: 원자적 노트 생성 (Bottom-Up)**
```
각 챕터별로:
1. 핵심 개념 목록화 (개념당 1노트)
2. 원자적 노트 생성 (병렬 처리 가능)
3. 노트 간 wikilinks 추가
```

**Phase 3: 카테고리 MOC 생성 (각 챕터당 1개)**
```
각 챕터별로:
1. 챕터 개요 작성
2. 해당 챕터의 원자 노트들 링크
3. 핵심 발견사항 요약
```

**Phase 4: 메인 MOC 생성**
```
1. 문서 전체 개요
2. 모든 카테고리 MOC 링크
3. 주요 발견/인사이트 요약
4. 메타데이터 (출처, 날짜 등)
```

### 노트 템플릿

#### 레벨 1: 메인 MOC

```markdown
---
created: YYYY-MM-DDTHH:mm:ss
tags: [MOC, 주제, 연구보고서]
type: main-moc
source: [원본 출처]
---

# [문서제목] - MOC

## 개요
[문서 전체 요약 2-3문단]

## 핵심 발견
1. [발견 1]
2. [발견 2]
3. [발견 3]

## 챕터별 정리

### 1. [[챕터1-MOC|챕터1 제목]]
[챕터1 한줄 요약]

### 2. [[챕터2-MOC|챕터2 제목]]
[챕터2 한줄 요약]

### 3. [[챕터3-MOC|챕터3 제목]]
[챕터3 한줄 요약]

## 메타데이터
- **출처**: [URL/파일명]
- **발행일**: YYYY-MM-DD
- **저자/기관**: [저자명]
- **정리일**: YYYY-MM-DD

---

## 📍 네비게이션

### 현재 위치
```
📚 [문서제목] ← 현재 보고 있는 문서
```

### 전체 목차
| # | 챕터 | 노트 수 |
|---|------|---------|
| 1 | [[01-챕터명/챕터1-MOC\|챕터1]] | N개 |
| 2 | [[02-챕터명/챕터2-MOC\|챕터2]] | N개 |
| 3 | [[03-챕터명/챕터3-MOC\|챕터3]] | N개 |
```

#### 레벨 2: 카테고리 MOC

```markdown
---
created: YYYY-MM-DDTHH:mm:ss
tags: [MOC, 주제, 챕터명]
type: category-moc
parent: "[[메인-MOC]]"
chapter: N
---

# [챕터제목] - MOC

## 개요
[챕터 요약 1-2문단]

## 핵심 내용

### [[원자노트1]]
[한줄 요약]

### [[원자노트2]]
[한줄 요약]

### [[원자노트3]]
[한줄 요약]

## 주요 데이터/통계
[해당 챕터의 핵심 수치]

## 관련 노트
- [[다른챕터-MOC]] - [연결 이유]

---

## 📍 네비게이션

### 현재 위치
```
📚 [[메인-MOC|문서제목]]
  └── 📂 [현재 챕터명] ← 현재 위치
```

### 이 챕터의 노트
| # | 노트 | 요약 |
|---|------|------|
| 1 | [[원자노트1]] | 요약 |
| 2 | [[원자노트2]] | 요약 |
| 3 | [[원자노트3]] | 요약 |

### 전체 목차
| # | 챕터 | 현재 |
|---|------|------|
| 1 | [[챕터1-MOC\|챕터1]] | ✅ |
| 2 | [[챕터2-MOC\|챕터2]] | ⬜ |
| 3 | [[챕터3-MOC\|챕터3]] | ⬜ |

---
← [[메인-MOC|메인으로]]
```

#### 레벨 3: 원자적 노트

```markdown
---
created: YYYY-MM-DDTHH:mm:ss
tags: [주제, 키워드1, 키워드2]
type: atomic
parent: "[[챕터-MOC]]"
source: [원본 출처]
chapter: N
---

# [개념 제목]

## 핵심 내용
[2-3문장으로 핵심 설명]

## 상세 설명
[필요시 추가 설명]

## 데이터/근거
[통계, 인용, 차트 등]

## 관련 노트
- [[관련노트1]] - [연결 이유]
- [[관련노트2]] - [연결 이유]

---

## 📍 네비게이션

### 현재 위치
```
📚 [[메인-MOC|문서제목]]
  └── 📂 [[챕터-MOC|챕터명]]
        └── 📄 [현재 노트] ← 현재 위치
```

### 같은 챕터의 노트
| # | 노트 | 현재 |
|---|------|------|
| 1 | [[노트1]] | ⬜ |
| 2 | [[노트2]] | ✅ |
| 3 | [[노트3]] | ⬜ |

### 전체 목차
| # | 챕터 | 현재 |
|---|------|------|
| 1 | [[챕터1-MOC\|챕터1]] | ✅ |
| 2 | [[챕터2-MOC\|챕터2]] | ⬜ |
| 3 | [[챕터3-MOC\|챕터3]] | ⬜ |

---
← [[챕터-MOC|챕터로]] | [[메인-MOC|메인으로]]
```

### 병렬 생성 전략

```
Step 1: 모든 원자 노트 병렬 생성 (N개 동시)
  [도구 1] Bash: "/mnt/c/Program Files/Obsidian/Obsidian.com" create path="..." content="..." (원자노트1)
  [도구 2] Bash: "/mnt/c/Program Files/Obsidian/Obsidian.com" create path="..." content="..." (원자노트2)
  [도구 3] Bash: "/mnt/c/Program Files/Obsidian/Obsidian.com" create path="..." content="..." (원자노트3)
  ... (최대 10개 병렬)
  CLI 실패 시: mcp__obsidian__create_note (Tier 2) → Write (Tier 3)

Step 2: 모든 카테고리 MOC 병렬 생성
  [도구 1] Bash: CLI create (챕터1-MOC)
  [도구 2] Bash: CLI create (챕터2-MOC)
  ... (챕터 수만큼)

Step 3: 메인 MOC 생성
  [도구 1] Bash: CLI create (메인-MOC)
```

### 파일명 규칙

| 레벨 | 파일명 패턴 | 예시 |
|------|-------------|------|
| 메인 MOC | `[제목]-MOC.md` | `Our-Life-with-AI-2026-MOC.md` |
| 카테고리 MOC | `[챕터명]-MOC.md` | `AI-채택-현황-MOC.md` |
| 원자 노트 | `[개념명].md` | `AI-채택률-2023-2025-추이.md` |

### 폴더명 규칙

```
[NN]-[챕터명]/

예시:
01-채택현황/
02-교육학습/
03-인식태도/
04-사회적영향/
05-거버넌스신뢰/
```

### 검증 체크리스트

```
□ 모든 원자 노트가 생성되었는가?
□ 각 카테고리 MOC가 해당 원자 노트를 링크하는가?
□ 메인 MOC가 모든 카테고리 MOC를 링크하는가?
□ 양방향 링크 (parent 필드)가 설정되었는가?
□ 폴더 구조가 올바른가?
□ 태그가 일관성 있게 적용되었는가?
□ 네비게이션 푸터가 모든 노트에 포함되었는가? ⭐
```

---

## 네비게이션 푸터 (MANDATORY) ⭐ NEW

**모든 형식(Obsidian, Notion, Markdown 등)에 필수 적용**

### 목적
- 현재 읽고 있는 위치를 명확히 표시
- 같은 챕터의 다른 노트로 쉽게 이동
- 전체 문서 구조를 한눈에 파악

### 네비게이션 푸터 구조

```markdown
---

## 📍 네비게이션

### 현재 위치
```
📚 [[메인-MOC|문서제목]]
  └── 📂 [[챕터-MOC|현재 챕터명]]
        └── 📄 [현재 노트 제목] ← 현재 위치
```

### 같은 챕터의 노트
| # | 노트 | 상태 |
|---|------|------|
| 1 | [[노트1]] | ⬜ |
| 2 | [[노트2]] | ✅ 현재 |
| 3 | [[노트3]] | ⬜ |

### 전체 목차
| # | 챕터 | 현재 |
|---|------|------|
| 1 | [[챕터1-MOC\|챕터1]] | ✅ |
| 2 | [[챕터2-MOC\|챕터2]] | ⬜ |
| 3 | [[챕터3-MOC\|챕터3]] | ⬜ |

---

← [[챕터-MOC|챕터로]] | [[메인-MOC|메인으로]]
```

### 레벨별 네비게이션 내용

| 노트 레벨 | 포함 내용 |
|----------|----------|
| **메인 MOC** | 현재 위치 + 전체 목차 (챕터 목록) |
| **카테고리 MOC** | 현재 위치 + 이 챕터의 노트 목록 + 전체 목차 |
| **원자 노트** | 현재 위치 + 같은 챕터 노트 목록 + 전체 목차 |

### Notion 변환 규칙

Notion에서는 wikilinks 대신 Notion 링크로 변환:

| Obsidian | Notion |
|----------|--------|
| `[[노트명]]` | `[노트명](notion-page-url)` |
| `[[폴더/노트명\|표시명]]` | `[표시명](notion-page-url)` |
| `✅ 현재` | 볼드 처리 + 배경색 |

---

## 5A. Obsidian (Zettelkasten) 내보내기

### 사용 스킬
`zettelkasten-note.md` 참조

### 생성 절차

```
Step 1: 노트 ID 생성
  - 형식: YYYYMMDDHHmm
  - 예: 202601031430

Step 2: YAML 프론트매터 생성
  ---
  id: [타임스탬프]
  title: [노트 제목]
  category: [카테고리]
  tags: [tag1, tag2, ...]
  created: YYYY-MM-DD
  source: [원본 소스]
  ---

Step 3: 콘텐츠 구조화
  # [제목]

  ## 핵심 개념
  [원자적 아이디어 설명]

  ## 상세 설명
  [상세 설명]

  ## 연결된 개념
  - [[관련-노트-1]]
  - [[관련-노트-2]]

  ## 참고문헌
  [소스 정보]

Step 3.5: 이미지 저장 및 임베딩 (이미지 추출 활성 시)
  - 참조 스킬: km-image-pipeline.md
  - 디렉토리 생성:
    Bash: mkdir -p {vaultPath}/Resources/images/{topic-folder}/
  - 웹 이미지 다운로드:
    Bash: curl -sLo "{vaultPath}/Resources/images/{topic-folder}/{NN}-{descriptive-name}.{ext}" "{url}"
  - PDF 이미지 복사:
    Bash: cp km-temp/{name}/images/{file} "{vaultPath}/Resources/images/{topic-folder}/{NN}-{descriptive-name}.{ext}"
  - 다운로드 실패(403/404) 시 Playwright 스크린샷 폴백:
    mcp__playwright__browser_take_screenshot({ ref: "{element-ref}", filename: "{path}" })
  - 노트 콘텐츠에 임베드 구문 삽입 (본문 흐름 배치):
    개념 설명 → (빈 줄) → ![[Resources/images/{topic-folder}/{filename}]] → (빈 줄) → 상세 설명
  - 검증: Glob("AI_Second_Brain/Resources/images/{topic-folder}/*") → 파일 존재 확인

Step 4: Vault에 저장
  - 경로: Zettelkasten/[category]/[title] - YYYY-MM-DD-HHmm.md
  - CRITICAL: vault root가 이미 AI_Second_Brain 폴더
  - "AI_Second_Brain/" 접두사 절대 사용 금지!
  - Obsidian MCP 또는 Write 도구 사용
```

### 경로 규칙

```
✅ 올바른 경로:
   Zettelkasten/AI-연구/노트제목 - 2026-01-03-1430.md
   Research/연구문서.md
   Threads/스레드-정리.md

❌ 잘못된 경로 (중첩 폴더 생성됨!):
   AI_Second_Brain/Zettelkasten/AI-연구/...
   AI_Second_Brain/Research/...
```

### 저장 도구 호출 (3-Tier)

```
Tier 1: Obsidian CLI (최우선)
Bash: "/mnt/c/Program Files/Obsidian/Obsidian.com" create path="Zettelkasten/AI-연구/노트제목 - 2026-01-03-1430.md" content="[전체 노트 내용]"

CLI 실패 시:
Tier 2: Obsidian MCP
mcp__obsidian__create_note
- path: "Zettelkasten/AI-연구/노트제목 - 2026-01-03-1430.md"
- content: "[전체 노트 내용]"

MCP 실패 시:
Tier 3: Write 도구
Write
- file_path: "C:\Users\treyl\OneDrive\Desktop\AI\AI_Second_Brain\Zettelkasten\AI-연구\노트제목 - 2026-01-03-1430.md"
- content: "[전체 노트 내용]"
```

---

## 5B. Notion 내보내기

### 사용 스킬
`notion-knowledge-capture.md` 참조

### 생성 절차

```
Step 1: 마크다운 → Notion 블록 변환

  Markdown → Notion Block Type:
  - # Heading 1 → heading_1
  - ## Heading 2 → heading_2
  - ### Heading 3 → heading_3
  - 문단 → paragraph
  - - 불릿 → bulleted_list_item
  - 1. 숫자 → numbered_list_item
  - `code` → code
  - > 인용 → quote
  - [[wikilink]] → mention (페이지 존재 시)

Step 1.5: 이미지 블록 처리 (이미지 추출 활성 시)
  - 참조 스킬: km-image-pipeline.md
  - 외부 URL 이미지: image 블록으로 삽입
    { "type": "image", "image": { "type": "external", "external": { "url": "{원본URL}" }, "caption": [{ "type": "text", "text": { "content": "{alt-text}" } }] } }
  - 로컬 전용 이미지 (PDF 추출 등): 텍스트 설명으로 대체
    { "type": "callout", "callout": { "icon": { "type": "emoji", "emoji": "🖼️" }, "rich_text": [{ "type": "text", "text": { "content": "[이미지: {alt-text}] — Obsidian vault Resources/images/{topic-folder}/{filename} 에서 확인" } }] } }

Step 2: 메타데이터 처리
  - YAML 프론트매터 → Notion 속성
  - tags → Multi-select 속성
  - category → Select 속성
  - created → Date 속성
  - title → 페이지 제목

Step 3: Notion 페이지 생성

  Notion MCP 사용:
  a) 새 페이지 생성 (또는 기존 업데이트)
     mcp__notion__API-post-page

  b) 페이지 제목 설정

  c) 속성 추가 (태그, 카테고리, 날짜)

  d) 콘텐츠 블록 순차 추가
     mcp__notion__API-patch-block-children

  e) 이미지/첨부파일 처리

Step 4: Wikilink 처리
  - Notion에서 링크된 페이지 검색
  - 페이지 존재 시 mention 생성
  - 미발견 시 일반 텍스트로 변환
  - 옵션: 플레이스홀더 페이지 생성

Step 5: 데이터베이스 통합 (해당 시)
  - Zettelkasten 카테고리 → DB 속성 매핑
  - DB 행 생성 + 속성 설정
  - 관련 DB 항목 연결

Step 6: 사용자에게 보고
  - Notion 페이지 URL
  - DB 항목 URL (해당 시)
  - 생성/업데이트 상태
  - 생성된 블록 수
```

---

## 5C. 표준 Markdown 내보내기

### 생성 절차

```
Step 1: 클린 마크다운으로 변환
  - Obsidian 전용 문법 제거
  - [[wikilinks]] → [일반 링크](path) 변환
  - 표준 마크다운 포맷팅

Step 2: 지정 위치에 저장
  - 출력 디렉토리 확인
  - 파일명: [title].md
  - 프론트매터 포함 (선택적)

Step 3: 파일 경로 보고
  - 저장된 경로 안내
  - 추가 작업 안내
```

---

## 5D. PDF 내보내기

### 사용 스킬
`pdf.md` 참조 (reportlab)

### 생성 절차

```
Step 1: PDF용 콘텐츠 포맷팅
  - 타이틀 페이지 추가
  - 헤딩 계층적 포맷팅
  - 메타데이터 푸터 포함

Step 2: 마크다운 → PDF 변환
  - reportlab 또는 pandoc 사용
  - 스타일링 적용
  - 페이지 레이아웃 설정

Step 3: PDF 파일 저장
  - 출력 위치 확인
  - 파일명: [title].pdf

Step 4: 파일 경로 보고
```

---

## 5E. 블로그 플랫폼 내보내기

### Medium 형식

```
Step 1: Medium 호환 포맷팅
  - YAML 프론트매터 제거
  - Medium 호환 마크다운으로 변환
  - 이미지 참조 최적화
  - 코드 블록 포맷팅

Step 2: 내보내기 파일 생성
  - 포맷된 콘텐츠 저장
  - 게시 지침 포함

Step 3: 게시 가이드 제공
  - 복사-붙여넣기 지침
  - 이미지 업로드 안내
  - 태그/토픽 추천
```

### WordPress 형식

```
Step 1: WordPress 호환 포맷팅
  - HTML 변환
  - WordPress 숏코드 적용
  - 특성 이미지 지원

Step 2: 내보내기 파일 생성
  - HTML 파일 저장
  - 옵션: XML 내보내기

Step 3: 게시 가이드 제공
  - 대시보드 게시 방법
  - 미디어 업로드 안내
  - SEO 최적화 팁
```

---

## 5F. 다이어그램 내보내기

### 사용 스킬
`drawio-diagram.md` 참조

### 생성 절차

```
Step 1: 세션 시작
  mcp__drawio__start_session
  - 브라우저에서 실시간 프리뷰 열림 (port 6002-6020)

Step 2: 콘텐츠에서 다이어그램 구조 분석
  - 추출된 콘텐츠에서 다이어그램 요소 식별
  - 노드 (개념, 엔티티, 컴포넌트)
  - 연결 (관계, 흐름, 의존성)
  - 그룹/레이어 (분류, 계층)

Step 3: 다이어그램 생성
  mcp__drawio__create_new_diagram
  - 자연어 설명 또는 mxGraphModel XML 입력
  - 다이어그램 유형에 맞는 레이아웃 적용

Step 4: 사용자와 반복 (선택적)
  - 브라우저에서 프리뷰 확인
  - 사용자 수정 요청 반영
  mcp__drawio__edit_diagram  # 수정용

Step 5: 내보내기 및 저장
  mcp__drawio__export_diagram
  - 저장 경로: [관련노트폴더]/[주제]-diagram-[YYYY-MM-DD].drawio
  - 예: Zettelkasten/AI-연구/MCP-Architecture-diagram-2025-01-02.drawio
  - CRITICAL: vault root 기준 상대경로 (AI_Second_Brain/ 접두사 금지!)

Step 6: 노트에 링크 추가
  관련 노트에 다이어그램 참조:

  ## 시각화
  ![[주제-diagram-2025-01-02.drawio]]
  *다이어그램: [설명]*

  또는 독립 다이어그램 노트 생성 (type: diagram)
```

### 다이어그램 유형별 가이드

| 유형 | 용도 | 요소 |
|------|------|------|
| Flowchart | 프로세스, 워크플로우, 의사결정 | 시작/끝, 프로세스, 판단, 화살표 |
| Architecture | 시스템 구조, 컴포넌트 관계 | 컴포넌트, 레이어, 연결선 |
| Mind Map | 개념 관계, 지식 계층 | 중심 주제, 분기, 하위 개념 |
| Sequence | API 흐름, 상호작용 | 액터, 생명선, 메시지 |
| ERD | 데이터베이스 스키마 | 엔티티, 속성, 관계 |

---

## 파일 저장 필수 프로토콜

### CRITICAL: 반드시 도구 호출!

노트/파일 생성 시 JSON 출력만 하고 끝내면 **절대 안 됩니다!**

### ✅ 필수 패턴 (3-Tier)

```
// Tier 1: Obsidian CLI (최우선):
Bash: "/mnt/c/Program Files/Obsidian/Obsidian.com" create path="Research/note.md" content="..."

// CLI 실패 시 Tier 2: Obsidian MCP:
mcp__obsidian__create_note(path="Research/note.md", content="...")

// MCP 실패 시 Tier 3: Write 도구:
Write(file_path="C:\...\AI_Second_Brain\Research\note.md", content="...")
```

### ❌ 금지 패턴

```json
// 이렇게 하면 실제 저장 안 됨!
{
  "path": "Research/note.md",
  "content": "..."
}
```

### 저장 후 검증

```
1. 저장 도구 호출 (CLI → create_note → Write 순서)
2. 결과 확인 - CLI exit 0 / "created successfully" / 성공 메시지
3. 실패 시 다음 Tier로 폴백
4. 절대 JSON 출력만 하고 끝내지 말 것!
```

---

## 스킬 조합 예시

### 예시 1: PDF → Obsidian + Notion

```
1. marker_single로 PDF → Markdown 변환 (토큰 절감!)
2. Markdown 파일 읽기 및 분석
3. zettelkasten-note로 Obsidian 노트 생성
4. notion-knowledge-capture로 Notion 페이지 생성
```

### 예시 2: 웹 콘텐츠 → 노트 + 다이어그램

```
1. playwright로 웹 콘텐츠 추출
2. 시스템 컴포넌트/프로세스 감지
3. zettelkasten-note로 노트 생성
4. drawio-diagram으로 아키텍처/플로우차트 생성
5. 노트에 다이어그램 참조 링크 추가
```

### 예시 3: Excel 분석 → 리포트 + PDF

```
1. xlsx 스킬로 데이터 분석
2. 트렌드 및 인사이트 도출
3. 분석 노트 생성
4. pdf 스킬로 PDF 리포트 생성
```

### 예시 4: Notion 리서치 → 다중 포맷

```
1. notion-research-documentation으로 리서치 수행
2. 종합 문서 생성
3. Obsidian 노트로 저장
4. pdf 스킬로 PDF 버전 생성
5. pptx 스킬로 요약 프레젠테이션 생성
```

---

## 출력 품질 체크리스트

```
□ 콘텐츠가 정확하게 변환되었는가?
□ 구조가 원본과 일치하는가?
□ 메타데이터가 완전한가?
□ 링크/참조가 유효한가?
□ 포맷이 대상 플랫폼에 적합한가?
□ 파일이 올바른 위치에 저장되었는가?

## 파일 저장 검증 (필수!)
□ CLI, mcp__obsidian__create_note, 또는 Write 도구를 실제로 호출했는가?
□ 도구 호출 결과에서 성공 메시지 확인했는가? (CLI exit 0 / MCP success / Write 정상)
□ JSON 출력만 하고 끝내지 않았는가?
□ 모든 파일이 실제로 생성되었음을 확인했는가?

## 이미지 파이프라인 검증 (이미지 추출 활성 시!)
□ Image Catalog의 모든 이미지가 다운로드/복사 되었는가?
□ Resources/images/{topic-folder}/ 폴더에 파일이 실제로 존재하는가?
□ 노트 내 ![[Resources/images/...]] 구문과 실제 파일이 1:1 매핑되는가?
□ 본문 흐름 배치 규칙을 따르는가? (개념→빈줄→이미지→빈줄→상세, 연속 배치 없음)
□ Notion 외부 URL 이미지가 image 블록으로 삽입되었는가?
□ 로컬 전용 이미지는 텍스트 설명(callout)으로 대체되었는가?
```

---

## 스킬 참조

- **zettelkasten-note.md**: Obsidian 노트 형식 상세
- **pdf.md**: PDF 처리 상세
- **xlsx.md**: Excel 처리 상세
- **docx.md**: Word 처리 상세
- **pptx.md**: PowerPoint 처리 상세
- **drawio-diagram.md**: 다이어그램 생성 상세
- **notion-knowledge-capture.md**: Notion 지식 캡처
- **notion-research-documentation.md**: Notion 리서치 문서화
