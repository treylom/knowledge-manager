# Knowledge Manager 연결 감사 스킬

> Vault 전체의 노트 연결 상태 진단 및 개선 제안

---

## 스킬 개요

이 스킬은 사용자 요청 시 실행되어:
1. Vault 전체 노트 목록 수집
2. 각 노트의 연결 상태 분석
3. 문제점 식별 (고아 노트, 깨진 링크, 허브 부재 등)
4. 개선 제안 생성
5. 진단 리포트 작성

---

## 실행 트리거

| 키워드 | 동작 |
|--------|------|
| "연결 감사해줘", "링크 감사" | 전체 감사 실행 |
| "고아 노트 찾아줘" | 고아 노트만 검색 |
| "깨진 링크 검사해줘" | 깨진 링크만 검색 |
| "연결 부족한 노트" | 연결 부족 노트만 검색 |
| "vault 상태 진단" | 전체 진단 + 리포트 저장 |

---

## Phase 1: Vault 스캔

### 1.1 전체 노트 목록 수집

```
Tier 1: Obsidian CLI files (최우선)
  Bash: "$OBSIDIAN_CLI" files folder="{폴더}" ext=md

CLI 실패 시 Tier 2: Obsidian MCP
  도구: mcp__obsidian__list_notes

Tier 3: Glob 폴백
  Glob: "AI_Second_Brain/**/*.md"

수집 정보:
- 모든 노트 경로
- 폴더 구조
- 파일 수
```

### 1.2 폴더별 분류

```
폴더 구조 분석:
- Zettelkasten/ (하위 폴더별 분류)
  - AI-성능최적화/
  - AI-연구/
  - AI-도구/
  - AI-활용/
  - AI-Safety/
  - Insights/
- Research/
- Threads/
- Skills/
- Bug_Reports/
- Changelog/
```

### 1.3 노트별 메타데이터 수집

```
각 노트에서 추출:
- 태그 (YAML frontmatter)
- 생성일 (파일명 또는 frontmatter)
- Outgoing wikilinks ([[...]])
- 파일 크기
```

---

## Phase 2: 연결 상태 분석

### 2.1 연결 그래프 구축

```
분석 항목:
- 각 노트의 outgoing links (이 노트 → 다른 노트)
- 각 노트의 incoming links (다른 노트 → 이 노트)
- 연결 밀도 (총 링크 수 / 노트 수)
```

### 2.2 wikilink 파싱

```python
# Wikilink 추출 정규식
pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'

# 예시:
# [[노트이름]] → "노트이름"
# [[노트이름|표시텍스트]] → "노트이름"
# [[폴더/노트이름]] → "폴더/노트이름"
```

### 2.3 연결 지표 계산

```
주요 지표:
1. 총 노트 수
2. 총 링크 수 (wikilinks)
3. 평균 링크 수/노트
4. 고아 노트 수 (in = 0, out = 0)
5. 데드엔드 노트 수 (out = 0, in > 0)
6. 허브 노트 수 (links > 10)
7. 단방향 링크 비율
```

---

## Phase 3: 문제점 식별

### 3.1 고아 노트 (Orphan Notes)

```
Tier 1: Obsidian CLI orphans (네이티브 — 최우선!)
  Bash: "$OBSIDIAN_CLI" orphans
  → 고아 노트 목록을 직접 반환 (파싱 불필요)

CLI 실패 시 Tier 2: 수동 분석
  정의: 다른 노트로부터 링크되지 않고, 다른 노트로 링크하지도 않는 노트

  식별 조건:
  - incoming_links = 0
  - outgoing_links = 0

제외 대상:
- MOC 노트 (허브 역할)
- 템플릿 파일
- Bug_Reports 폴더 (의도적 독립)
```

### 3.2 깨진 링크 (Broken Links)

```
Tier 1: Obsidian CLI unresolved (네이티브 — 최우선!)
  Bash: "$OBSIDIAN_CLI" unresolved
  → 깨진 링크 목록을 직접 반환 (파싱 불필요)

CLI 실패 시 Tier 2: 수동 분석
  정의: 존재하지 않는 노트를 참조하는 wikilink

  식별 방법:
  1. 모든 노트에서 [[링크]] 파싱
  2. 링크된 노트 경로 추출
  3. 해당 파일 존재 여부 확인
  4. 없으면 깨진 링크로 분류

  검사 패턴:
  - [[노트이름]] → "노트이름.md" 존재?
  - [[폴더/노트]] → "폴더/노트.md" 존재?
```

### 3.3 단방향 링크 (One-way Links)

```
정의: A→B 링크 있지만 B→A 없음

식별 방법:
1. 모든 링크 쌍 수집
2. 각 쌍의 역방향 존재 확인
3. 역방향 없으면 단방향으로 분류

출력:
| 소스 | 타겟 | 역링크 |
|------|------|--------|
| [[A]] | [[B]] | 없음 |
```

### 3.4 연결 부족 노트 (Under-connected)

```
정의: 동일 폴더/태그 노트 대비 연결이 현저히 적은 노트

기준:
- 폴더 평균 링크 수 계산
- 평균의 50% 이하면 "연결 부족"

예시:
- 폴더 평균: 4개 링크
- 해당 노트: 1개 링크
- 판정: 연결 부족 (1/4 = 25%)
```

### 3.5 허브 부재 (Missing Hub/MOC)

```
정의: 관련 노트들을 묶는 MOC가 없는 클러스터

식별 기준:
- 동일 태그 노트 5개 이상
- 해당 태그에 대한 MOC 노트 없음

예시:
- 태그 "AI-벤치마크" 노트: 6개
- "AI-벤치마크 MOC" 노트: 없음
- 판정: MOC 생성 권장
```

### 3.6 고립 클러스터 (Isolated Clusters)

```
정의: 다른 클러스터와 연결 없는 노트 그룹

식별 방법:
1. 연결 그래프 구축
2. 연결 컴포넌트 분석
3. 메인 그래프에서 분리된 클러스터 식별
```

---

## Phase 4: 개선 제안 생성

### 4.1 우선순위 분류

```
🔴 High Priority (즉시 조치):
- 깨진 링크 (데이터 무결성 문제)
- 완전 고아 노트 5개 이상

🟡 Medium Priority (권장):
- 단방향 링크 → 양방향 전환
- 연결 부족 노트 강화

🟢 Low Priority (선택):
- 허브 노트(MOC) 생성
- 추가 연결 제안
```

### 4.2 자동 수정 옵션

**사용자 확인 후 자동 수정 가능:**
- 양방향 링크 추가
- 고아 노트에 관련 링크 추가
- auto_backlink_vault 도구 활용

**수동 수정 필요:**
- 깨진 링크 (파일 생성 또는 링크 수정)
- MOC 생성 (콘텐츠 작성 필요)
- 노트 병합/정리

### 4.3 auto_backlink_vault 활용

```
Tier 1: Obsidian CLI 기반 커스텀 로직 (최우선)

  Step 1: 고아 노트 식별
    Bash: "$OBSIDIAN_CLI" orphans

  Step 2: 각 고아 노트에 대해 backlinks 확인 + 연결 후보 탐색
    Bash: "$OBSIDIAN_CLI" backlinks path="{orphan}" format=json
    Bash: "$OBSIDIAN_CLI" search query="{키워드}" format=json

  Step 3: 연결 추가
    Bash: "$OBSIDIAN_CLI" append path="{노트}" content="{링크}"

CLI 실패 시 Tier 2: Obsidian MCP
  도구: mcp__obsidian__auto_backlink_vault

  옵션:
  - dryRun: true (기본) - 미리보기
  - dryRun: false - 실제 적용
  - excludePatterns: ["templates/*", "assets/*"]
  - minLength: 3 (최소 노트명 길이)
  - wholeWords: true (전체 단어 매칭)
  - caseSensitive: false

  예시:
  mcp__obsidian__auto_backlink_vault
  - dryRun: true
  - excludePatterns: ["templates/*", "Bug_Reports/*"]
  - minLength: 4
```

---

## Phase 5: 리포트 생성

### 5.1 리포트 저장 위치

```
경로: Changelog/Vault-Link-Audit-{YYYY-MM-DD}.md

예시:
Changelog/Vault-Link-Audit-2026-01-03.md
```

### 5.2 리포트 템플릿

```markdown
---
tags: [audit, vault-health, report]
created: {YYYY-MM-DD HH:mm}
type: audit-report
---

# Vault 연결 감사 리포트

## 감사 정보
- 실행 일시: YYYY-MM-DD HH:mm
- 분석 범위: 전체 vault
- 총 분석 노트: N개

---

## 요약 통계

| 지표 | 값 | 평가 |
|------|-----|------|
| 총 노트 수 | 156 | - |
| 총 링크 수 | 438 | - |
| 평균 링크/노트 | 2.8 | ⚠️ 낮음 (권장: 3-5) |
| 고아 노트 | 28 (18%) | ⚠️ 개선 필요 |
| 깨진 링크 | 5 | ❌ 즉시 수정 |
| 단방향 링크 | 89 | ⚠️ 양방향 권장 |
| 허브 노트 | 8 | ✅ 양호 |

### 연결 건강도 점수

```
[████████░░] 75/100

개선 영역:
- 고아 노트 해소: +10점
- 깨진 링크 수정: +5점
- 단방향→양방향: +10점
```

---

## 상세 문제점

### 🔴 High Priority (즉시 조치)

#### 깨진 링크 (N개)

| 깨진 링크 | 위치 노트 | 권장 조치 |
|-----------|----------|----------|
| [[없는노트1]] | [[노트A]] | 생성 또는 수정 |
| [[오타노트]] | [[노트B]] | 링크 수정 |

#### 고아 노트 (상위 10개)

| 고아 노트 | 폴더 | 생성일 | 권장 연결 |
|-----------|------|--------|----------|
| [[노트1]] | Research | 2025-12-15 | [[관련MOC]] |
| [[노트2]] | Threads | 2025-12-10 | [[관련노트]] |

---

### 🟡 Medium Priority (권장)

#### 단방향 링크 (상위 20개)

| 소스 노트 | 타겟 노트 | 역링크 추가 |
|-----------|----------|------------|
| [[A]] | [[B]] | B에 A 링크 추가 권장 |

#### 연결 부족 노트

| 노트 | 현재 링크 | 폴더 평균 | 권장 추가 |
|------|----------|----------|----------|
| [[노트X]] | 1 | 4 | +3개 |

---

### 🟢 Low Priority (선택)

#### 허브(MOC) 생성 권장

| 태그/주제 | 관련 노트 수 | MOC 상태 |
|----------|-------------|---------|
| AI-벤치마크 | 6 | 없음 - 생성 권장 |

---

## 자동 수정 제안

다음 항목에 대해 자동 수정을 실행할까요?

- [ ] 단방향 링크 89개 → 양방향 전환
- [ ] 고아 노트 28개 → 관련 노트 연결

### 실행 명령

```
Tier 1: CLI 기반 (최우선)
  "$OBSIDIAN_CLI" orphans → 대상 파악
  "$OBSIDIAN_CLI" backlinks path="{노트}" format=json → 후보 탐색
  "$OBSIDIAN_CLI" append path="{노트}" content="{링크}" → 연결 추가

CLI 실패 시 Tier 2: MCP
  mcp__obsidian__auto_backlink_vault 사용:
  - 먼저 dryRun: true로 미리보기
  - 확인 후 dryRun: false로 적용
```

---

## 다음 감사 권장
- 30일 후 재실행 권장
- 대량 노트 생성 후 실행 권장
- 주요 구조 변경 후 실행 권장

---

*이 리포트는 Knowledge Manager 연결 감사 스킬에 의해 자동 생성되었습니다.*
```

---

## 설정 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `include_folders` | ["*"] | 감사 대상 폴더 |
| `exclude_folders` | ["templates", "assets"] | 제외 폴더 |
| `orphan_threshold` | 0 | 고아 판정 링크 수 |
| `underconnected_ratio` | 0.5 | 연결 부족 판정 비율 |
| `save_report` | true | 리포트 저장 여부 |
| `report_path` | "Changelog/" | 리포트 저장 위치 |
| `auto_fix_prompt` | true | 자동 수정 제안 표시 |

---

## 사용 예시

### 전체 감사

```
사용자: "vault 연결 감사해줘"

→ 전체 Phase 1-5 실행
→ 리포트 생성 및 저장
→ 자동 수정 옵션 제안
```

### 부분 감사

```
사용자: "고아 노트만 찾아줘"

→ Phase 1-3 중 고아 노트만 검사
→ 간략 결과 보고 (리포트 미저장)
```

### 특정 폴더 감사

```
사용자: "Zettelkasten 폴더만 연결 감사해줘"

→ 해당 폴더만 대상으로 감사
→ 폴더별 상세 통계 제공
```

---

## 에러 처리

| 에러 유형 | 대응 |
|----------|------|
| 노트 목록 조회 실패 | 재시도 → 수동 폴더 지정 요청 |
| 노트 읽기 실패 | 스킵 후 로그 기록 |
| 리포트 저장 실패 | 콘솔 출력으로 대체 |
| 대용량 vault (1000+) | 배치 처리 적용 |

---

## 참고: 연결 강화 스킬과의 연동

감사 결과를 바탕으로 `km-link-strengthening.md` 스킬 호출 가능:

```
사용자: "감사 결과로 자동 연결 강화해줘"

→ 고아 노트 목록 추출
→ km-link-strengthening 배치 실행
→ 결과 보고
```
