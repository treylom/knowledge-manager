---
name: km-graphrag-report
description: Use when needing GraphRAG ReAct 보고서 생성 스킬. Thought→Action→Observation 루프, 명시적 종료 조건, 무한 루프 방지, 글로벌 맵-리듀스 보고서 포맷, 분석공간 섹션 포함.
---

# GraphRAG ReAct 보고서 생성 스킬

> GraphRAG 검색 결과를 기반으로 구조화된 분석 보고서를 생성하고 Obsidian vault에 저장
> 이론 기반: [[ReAct-패턴-추론과-행동의-교차]], [[GraphRAG-Map-Reduce-쿼리-전략]], [[6개-분석공간-개요]]

---

## ReAct 패턴 개요

GraphRAG 보고서는 **ReAct(Reasoning + Acting) 패턴**을 통해 생성됩니다.
단순 검색 결과 나열이 아닌, Thought→Action→Observation 사이클로 심층 인사이트를 추출합니다.

> "순수 추론(CoT)만으로는 외부 세계와 상호작용할 수 없고, 순수 행동만으로는 복잡한 다단계 계획을 세울 수 없다. ReAct는 두 능력을 교차 수행해 시너지를 만든다." — §F06

### ReAct 루프 구조

```
┌────────────────────────────────────────────────────────────┐
│  ReAct LOOP (최대 MAX_ITER회, 기본 5회)                      │
│                                                            │
│  Thought  → 현재까지 수집한 정보 분석                         │
│       ↓      "어떤 정보가 더 필요한가? 어떤 도구를 쓸까?"       │
│  Action   → 검색 도구 호출                                   │
│       ↓      quick_search / insight_forge /                │
│              panorama_search / interview / meta_edge_search│
│  Observation → 검색 결과 수집 및 평가                        │
│       ↓      "새로운 인사이트가 있는가?"                      │
│              "종료 조건이 충족되었는가?" ← 반드시 확인!         │
│  [종료 조건 충족 → 최종 보고서 생성]                           │
│  [미충족 → 다음 Thought]                                     │
└────────────────────────────────────────────────────────────┘
```

---

## ReAct 실행 절차

### Step 0: 쿼리 분류 (필수 선행)

```
쿼리 복잡도 분류 (km-graphrag-search.md 참조):
├── L3 → Global 전략: panorama_search 우선 + 맵-리듀스 결과 집계
└── L0~L2 → Local 전략: quick_search / insight_forge 중심

분석공간 선택:
├── "언제", "최근" → 시간공간 필터 활성화
├── "왜", "원인" → 인과공간 필터 활성화
├── "연결", "구조" → 구조공간 필터 활성화
└── 복합 질문 → 다중공간 활성화
```

### Step 1: 초기 Thought (Reasoning)

```
목표 분석:
- 사용자가 원하는 인사이트 유형 파악 (L0~L3 분류)
- 활성화할 분석공간 결정
- 필요한 검색 도구 선택 (km-graphrag-search.md 도구 매트릭스 참조)

초기 질문 설정:
Q1: "이 주제의 전체 분포는?" → panorama_search (L3이면 필수)
Q2: "핵심 개념들의 관계는?" → insight_forge (L1/L2)
Q3: "특정 엔티티의 역할은?" → quick_search / interview
Q4: "관계들의 메타 패턴은?" → meta_edge_search (필요 시)
```

### Step 2: Action (도구 호출)

```bash
# 1차 Action 예시 (L3 글로벌 쿼리)
python .team-os/graphrag/scripts/graph_search.py \
  --tool panorama_search \
  --query "<주제>" \
  --community-level 1 \
  --format json

# 2차 Action 예시 (Observation 기반 조정, L1/L2)
python .team-os/graphrag/scripts/graph_search.py \
  --tool insight_forge \
  --query "<Observation에서 발견된 핵심 질문>" \
  --drift true \
  --format json
```

### Step 3: Observation 평가 및 종료 조건 판단

**종료 조건 (Termination Conditions) — 하나라도 충족 시 루프 종료:**

```python
TERMINATION_CONDITIONS = [
    # TC1: 수렴 조건
    lambda obs: obs.new_entity_ratio < 0.05,          # 새 엔티티 5% 미만 증가
    # TC2: 커버리지 조건
    lambda obs: obs.community_coverage >= 0.80,        # 핵심 커뮤니티 80% 커버
    # TC3: 답변 품질 조건
    lambda obs: obs.faithfulness_score > 0.80,         # 신뢰도 점수 > 0.8
    # TC4: 반복 한도 (무한 루프 방지 — 절대 한도)
    lambda obs: obs.iteration >= MAX_ITER,             # MAX_ITER=5 초과 방지
]

# 무한 루프 방지: TC4는 다른 조건과 독립적으로 항상 확인
if iteration >= MAX_ITER:
    log_warning(f"MAX_ITER({MAX_ITER}) 도달: 강제 종료")
    break
```

**루프 계속 조건:**

```
🔄 루프 계속:
  - 새로운 커뮤니티 발견 → panorama_search 추가 실행
  - 핵심 엔티티의 동기 불명확 → interview 실행
  - 상충하는 인사이트 발견 → insight_forge로 재합성
  - 메타엣지 패턴 미분석 → meta_edge_search 추가

⚠️ 루프 중단 경고:
  - 동일 쿼리 반복 감지 → 다른 도구/파라미터로 변경
  - Observation이 이전과 90% 이상 동일 → 조기 종료
```

### Step 4: 최종 보고서 생성

루프 종료 후 수집된 모든 Observation을 통합하여 보고서 작성.
**쿼리 분류(L0~L3)에 따라 보고서 형식이 달라집니다.**

---

## 보고서 출력 템플릿

### 공통 프론트매터

```yaml
---
tags:
  - graphrag
  - analysis
  - research
created: YYYY-MM-DD
graph_query: "<사용자 원본 쿼리>"
query_level: "L1"          # L0/L1/L2/L3
graph_tools_used:
  - panorama_search
  - insight_forge
  - quick_search
  - interview
  - meta_edge_search
react_iterations: 3        # 실제 실행 횟수
termination_reason: "community_coverage_80"  # 종료 조건 명시
analysis_spaces_used:      # 활성화된 분석공간
  - hierarchy              # 계층공간 (커뮤니티 레벨 C0~C3)
  - structural             # 구조공간 (엣지 밀도 분석)
source_communities: ["C01", "C05", "C12"]
---
```

### A. Local 보고서 템플릿 (L0~L2)

```markdown
# GraphRAG 분석: <주제> [Local]

## 요약 (Executive Summary)

<2-3문장 핵심 인사이트 요약>

주요 발견:
- **[발견1]**: 설명
- **[발견2]**: 설명
- **[발견3]**: 설명

---

## ReAct 실행 로그

```
Iteration 1 [Thought]: <현황 분석>
Iteration 1 [Action]: <도구 호출>
Iteration 1 [Observation]: <결과 요약, 새 엔티티 N개 발견>
---
Iteration 2 [Thought]: <이전 Observation 기반 판단>
Iteration 2 [Action]: <도구 호출>
Iteration 2 [Observation]: <결과 요약>
---
종료 조건: <TC1~TC4 중 충족된 조건>
```

---

## 분석공간별 발견

> 활성화된 분석공간: [계층공간 / 시간공간 / 구조공간 / 인과공간 / 재귀공간 / 다중공간]

### 계층공간 (Hierarchy) — 적용 시
커뮤니티 계층 C0~C3에서 이 주제가 어느 레벨에 위치하는지:
- C<N>: <주제 위치 설명>

### 시간공간 (Temporal) — 적용 시
이 주제가 시간적으로 어떻게 변화했는지:
- <시기>: <변화 내용>

### 구조공간 (Structural) — 적용 시
이 주제의 내부 클러스터 구조:
- 허브 엔티티: [[엔티티A]] (degree: N)
- 주요 클러스터: <설명>

### 인과공간 (Causal) — 적용 시
원인-결과 체인:
- <원인> → <결과>

---

## 핵심 발견 (Key Findings)

### 1. <발견 제목>

<상세 설명>

근거:
- 출처 커뮤니티: [[커뮤니티 ID]]
- 관련 엔티티: [[엔티티A]], [[엔티티B]]
- 원본 노트: [[노트경로1]], [[노트경로2]]
- 탐색 depth: <N>홉 (L<등급> 하드가딩)

### 2. <발견 제목>

<상세 설명>

---

## 메타엣지 패턴 (적용 시)

> meta_edge_search 사용 시 추가

| 관계 패턴 | 발견 내용 | 레버리지 효과 |
|---------|---------|------------|
| <rel_type 조합> | <패턴 설명> | <그래프 영향> |

---

## 추가 탐색 제안

- [ ] **<탐색 주제1>**: `insight_forge("<구체 쿼리>")` 로 L1/L2 심화 가능
- [ ] **<탐색 주제2>**: `interview("<엔티티명>")` 로 동기 분석 가능
- [ ] **<탐색 주제3>**: vault에서 미탐색된 관련 커뮤니티 존재

---

## 소스

| 노트 | 기여 내용 | 커뮤니티 |
|------|---------|---------|
| [[노트경로1]] | <기여 설명> | C01 |
| [[노트경로2]] | <기여 설명> | C05 |

### 그래프 메타데이터
- 분석된 엔티티 수: N개
- 분석된 엣지 수: N개
- 커버된 커뮤니티: N개
- 최대 탐색 depth: N홉
- 분석 시간: YYYY-MM-DD HH:mm
```

---

### B. Global 보고서 템플릿 (L3 — 맵-리듀스)

```markdown
# GraphRAG 분석: <주제> [Global Map-Reduce]

## 요약 (Executive Summary)

<2-3문장 핵심 인사이트 요약 — 전체 커뮤니티 관점>

전체 커뮤니티 커버리지: N개 / M개 (XX%)
글로벌 발견:
- **[발견1]**: 설명
- **[발견2]**: 설명

---

## 맵-리듀스 실행 결과

### Map 단계 (병렬 커뮤니티 처리)

| 커뮤니티 | 주제 | 유용성 점수 | 중간 답변 요약 |
|---------|------|-----------|------------|
| C01 | <주제 설명> | 0.92 | <중간 답변 요약> |
| C05 | <주제 설명> | 0.87 | <중간 답변 요약> |
| C12 | <주제 설명> | 0.71 | <중간 답변 요약> |
| C08 | <주제 설명> | 0.23 | (유용성 임계값 미달 — 제외) |

필터링: 유용성 점수 < 0.50 제거, 최종 K=N개 선택

### Reduce 단계 (최종 통합 답변)

<LLM이 중간 답변들을 통합한 포괄적 최종 답변>

---

## 커뮤니티 맵

> vault에서 이 주제를 다루는 커뮤니티 분포

| 커뮤니티 | 핵심 주제 | 노트 수 | 유용성 |
|---------|---------|--------|-------|
| C01 | <주제 설명> | N개 | ████████░░ 85% |
| C05 | <주제 설명> | N개 | ██████░░░░ 60% |
| C12 | <주제 설명> | N개 | ████░░░░░░ 40% |

### 커뮤니티 간 연결 (Cross-Community Edges)

```
C01 ──[bridges]──→ C05
C05 ──[contrasts]──→ C12
C01 ←──[extends]── C08
```

---

## ReAct 실행 로그 (글로벌)

```
Iteration 1 [Thought]: L3 글로벌 쿼리 감지 → panorama_search 선택
Iteration 1 [Action]: panorama_search(community_level=1)
Iteration 1 [Observation]: N개 커뮤니티 처리, 유용성 임계값 이상 M개
---
Iteration 2 [Thought]: C01, C05 핵심 커뮤니티 발견 → 심화 필요
Iteration 2 [Action]: insight_forge(L2, DRIFT 활성화)
Iteration 2 [Observation]: 추가 인사이트 발견, 새 엔티티 3%
---
종료 조건: TC1 충족 (새 엔티티 5% 미만)
```

---

## 분석공간별 발견

### 계층공간 — C0~C3 레벨별 인사이트
- **C0 (루트)**: <전체 코퍼스 수준 패턴>
- **C1/C2 (중간)**: <중간 수준 주제 클러스터>
- **C3 (리프)**: <세부 주제 분포>

### 구조공간 — 커뮤니티 간 연결 구조
허브 커뮤니티 (cross_community_edges 기준):
- [[C01]] ↔ [[C05]]: N개 공유 엔티티

---

## 상위 엔티티 (Hub Entities)

| 엔티티 | 커뮤니티 분포 | 연결 수 | 역할 |
|-------|-----------|--------|------|
| [[엔티티A]] | C01, C05, C12 | 45 | 허브 연결자 |
| [[엔티티B]] | C08 | 23 | 도메인 전문가 |

---

## 추가 탐색 제안

- [ ] **C01 심화**: `insight_forge("C01 핵심 주제 심화 분석")` (L2 DRIFT)
- [ ] **허브 엔티티 분석**: `interview("엔티티A")` 동기 분석
- [ ] **메타엣지 패턴**: `meta_edge_search("contrasts,bridges")` 커뮤니티 간 관계 분석

---

## 소스

### 분석에 사용된 커뮤니티 (N개)
C01, C03, C05, C08, C12, ...

### 그래프 메타데이터
- 처리된 커뮤니티 수: N개 (Map) → M개 (필터 후)
- 커뮤니티 레벨: C<N>
- 유용성 임계값: 0.50
- 분석된 엔티티 수: N개
- 분석 시간: YYYY-MM-DD HH:mm
```

---

## 저장 위치

**보고서 저장 경로 (CRITICAL)**:
```
Library/Research/GraphRAG-Analysis/
├── GraphRAG-Analysis-MOC.md          ← MOC (자동 업데이트)
├── GraphRAG-YYYY-MM-DD-<slug>.md     ← 개별 보고서
└── ...
```

**파일명 규칙**:
```
GraphRAG-{YYYY-MM-DD}-{slug}.md

예시:
GraphRAG-2026-03-16-ai-safety-alignment-local.md    (L1/L2)
GraphRAG-2026-03-16-vault-theme-analysis-global.md  (L3)
```

**저장 프로토콜 (3-Tier)**:
```
Tier 1: Obsidian CLI
  "/mnt/c/Program Files/Obsidian/Obsidian.com" create \
    path="Library/Research/GraphRAG-Analysis/GraphRAG-{date}-{slug}.md" \
    content="{보고서 내용}"

Tier 2: Obsidian MCP
  mcp__obsidian__create_note({
    path: "Library/Research/GraphRAG-Analysis/...",
    content: "보고서 내용"
  })

Tier 3: Write 도구
  Write({
    file_path: "/mnt/c/Users/treyl/Documents/Obsidian/Second_Brain/Library/Research/GraphRAG-Analysis/...",
    content: "보고서 내용"
  })
```

---

## MOC 자동 업데이트

보고서 저장 후 **반드시** `GraphRAG-Analysis-MOC.md`를 업데이트합니다.

**MOC 항목 추가 형식**:
```markdown
| YYYY-MM-DD | [[GraphRAG-YYYY-MM-DD-slug\|주제명]] | L<등급>/도구 | <분석공간> | C01,C05 |
```

**MOC 테이블 컬럼 (업데이트된 형식)**:
```markdown
| 날짜 | 보고서 | 전략 | 분석공간 | 커뮤니티 |
```

---

## 보고서 생성 체크리스트

```
□ 쿼리 분류(L0~L3) 수행?
□ 분석공간 선택?
□ ReAct 루프 최소 2회 실행?
□ 종료 조건 명시적 확인? (TC1~TC4)
□ MAX_ITER 초과 방지 확인?

[Local 보고서 (L0~L2)]
□ insight_forge or quick_search 호출?
□ depth 하드가딩 준수 (max 3홉)?
□ 분석공간 섹션 작성?

[Global 보고서 (L3)]
□ panorama_search 맵-리듀스 실행?
□ Map 단계 결과 테이블 포함?
□ 유용성 점수 필터링 기록?
□ Reduce 단계 최종 답변 포함?
□ 커뮤니티 맵 포함?

[공통]
□ frontmatter 완성?
  □ query_level 기록
  □ react_iterations 횟수
  □ termination_reason 명시
  □ analysis_spaces_used 목록
□ 추가 탐색 제안 포함?
□ Library/Research/GraphRAG-Analysis/ 에 저장?
□ GraphRAG-Analysis-MOC.md 업데이트?
□ Second_Brain/ prefix 없이 저장?
```

---

## 에러 처리

| 에러 | 대응 |
|------|------|
| 그래프 검색 결과 없음 | 쿼리 확장 후 재시도, L3 panorama_search로 폴백 |
| MOC 파일 없음 | 신규 MOC 생성 후 업데이트 |
| 저장 실패 (Tier 1) | Tier 2 → Tier 3 순차 시도 |
| 커뮤니티 맵 비어있음 | quick_search로 엔티티 확인 후 수동 맵 작성 |
| MAX_ITER 초과 | 강제 종료 후 현재까지 수집된 Observation으로 보고서 생성 |
| 글로벌 유용성 점수 전부 미달 | 임계값 0.50 → 0.30으로 낮춰 재시도 |

---

## 스킬 참조

- **km-graphrag-search.md**: Global/Local 이분법 + L0~L3 분류기 + hop 하드가딩
- **km-graphrag-sync.md**: 보고서 생성 후 frontmatter 동기화
- **km-graphrag-workflow/SKILL.md**: GraphRAG Mode G 전체 워크플로우
- **zettelkasten-note.md**: Obsidian 노트 형식 (일반 노트)
