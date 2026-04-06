---
name: km-graphrag-search
description: Use when needing GraphRAG 검색 전략. Global(맵-리듀스)/Local(hop 탐색) 이분법 자동 라우팅, L0-L3 쿼리 분류기, 분석공간 필터, 메타엣지 탐색, hop 하드가딩.
---

# GraphRAG 검색 전략 스킬

> Knowledge Manager GraphRAG Mode G의 Global/Local 이분법 기반 검색 전략 명세
> 이론 기반: [[GraphRAG-Global-vs-Local-Search]], [[Depth-Hop-필터링과-하드가딩]], [[6개-분석공간-개요]], [[메타엣지-정의와-4가지-의미]]

---

## 핵심 원칙: Global/Local 이분법

GraphRAG는 쿼리 복잡도에 따라 **두 가지 완전히 다른 검색 전략**을 사용한다.

| 전략 | 대상 쿼리 | 탐색 방식 | 결과 특성 |
|------|---------|---------|---------|
| **Local Search** (L0~L2) | 특정 엔티티/관계 질문 | 그래프 hop 기반 탐색 | 정밀하고 구체적 |
| **Global Search** (L3) | 코퍼스 전체 범위 질문 | 커뮤니티 맵-리듀스 | 포괄적이고 종합적 |

> "특정 엔티티/관계 언급 → 로컬. 코퍼스 전체 범위 → 글로벌" — 이 분기가 GraphRAG의 핵심 설계 결정이다.

---

## 쿼리 분류기 (L0~L3 자동 라우팅)

### 복잡도 등급 정의

| 등급 | 예시 쿼리 | Depth | 처리 전략 |
|-----|---------|-------|---------|
| **L0** | "GraphRAG가 무엇인가?", "이 노트는 어디 있는가?" | 1 | Local: 직접 조회 (quick_search) |
| **L1** | "GraphRAG를 개발한 조직은?", "이 개념의 연관 개념은?" | 1~2 | Local: 1~2홉 탐색 (insight_forge 또는 quick_search) |
| **L2** | "GraphRAG와 Neo4j 통합의 비즈니스 임팩트는?" | 2~3 + DRIFT | Local + DRIFT 하이브리드 (insight_forge) |
| **L3** | "이 vault의 주요 테마와 상호 연관성은?" | N/A (맵-리듀스) | Global: 커뮤니티 전체 처리 (panorama_search) |

### 자동 분류 알고리즘

```python
def classify_query_complexity(query: str) -> QueryLevel:
    """
    쿼리의 복잡도를 분석하여 L0~L3 분류 및 Depth 하드가딩 결정
    - 코퍼스 전체 범위 키워드 감지 → L3 (글로벌)
    - 단일 엔티티 + 단순 조회 → L0
    - 관계 체인 1~2 → L1
    - 관계 체인 3+ 또는 DRIFT 필요 → L2
    """
    # L3 감지: 글로벌 범위 키워드
    GLOBAL_KEYWORDS = ["전체", "모든", "주요 테마", "코퍼스 전반", "vault 전체", "전반적으로"]
    if any(kw in query for kw in GLOBAL_KEYWORDS):
        return QueryLevel.L3

    # 엔티티 수와 관계 체인 분석
    entities = extract_query_entities(query)
    relation_hops = estimate_relation_chain_length(query)

    if len(entities) == 1 and relation_hops <= 1:
        return QueryLevel.L0
    elif relation_hops <= 2:
        return QueryLevel.L1
    else:
        return QueryLevel.L2

# Depth 하드가딩 매핑
DEPTH_MAP = {
    QueryLevel.L0: 1,
    QueryLevel.L1: 2,
    QueryLevel.L2: 3,
}
```

### 라우팅 결정 트리

```
쿼리 입력
├── 코퍼스 전체 범위 키워드? → L3 → Global Search (panorama_search, 맵-리듀스)
│                                     └── 커뮤니티 레벨 선택: C0(빠름) ~ C3(정밀)
└── 특정 엔티티/관계 질문?  → Local Search
    ├── 단순 조회 (1엔티티, 1홉) → L0 → quick_search (depth=1)
    ├── 관계 탐색 (1~2홉)       → L1 → insight_forge (depth=2)
    └── 복합 관계 (2~3홉)       → L2 → insight_forge + DRIFT (depth=3)
```

---

## 도구 상세 스펙

### Depth 하드가딩 원칙 (모든 Local Search에 적용)

> "분기 계수 b, 깊이 d이면 탐색 경로 수 = b^d. Depth 4 이상은 지수적 폭발." — §5.5
> Depth는 시스템 파라미터로 **명시적 고정(Hard-Guarding)**한다.

```python
# 절대 초과 금지 한도 (하드가딩)
MAX_DEPTH_ABSOLUTE = 3   # L2까지의 최대값
MAX_DEPTH_DEFAULT  = 2   # 명시 없을 때 기본값

def safe_local_search(query, start_entities, depth=None):
    complexity = classify_query_complexity(query)
    effective_depth = min(
        depth or DEPTH_MAP.get(complexity, MAX_DEPTH_DEFAULT),
        MAX_DEPTH_ABSOLUTE
    )
    subgraph = traverse_graph(start_entities, max_depth=effective_depth)
    return generate_answer(query, subgraph)
```

**신뢰도 기반 동적 조정 (Confidence-Based Adjustment):**
```
Depth 1 탐색 → 결과 신뢰도 평가
├── 신뢰도 ≥ 임계값 → 종료
├── 신뢰도 < 임계값 → Depth 2로 확장 → 재평가
└── 여전히 부족 → L3 Global Search로 폴백
```

---

### 1. quick_search(entity_name) — L0 단순 조회

**용도**: 특정 엔티티의 즉각적인 1-hop 이웃 및 관계 유형 확인 (L0)

**처리 흐름**:
```
① entity_name → entities 테이블 LIKE 검색 (부분 일치 지원)
② 매칭 엔티티의 모든 엣지(edges 테이블) 수집
③ 1-hop 이웃 노드 식별 (max_depth=1 하드가딩)
④ 관계 유형(rel_type)별 그룹화
⑤ 관계 강도(weight/frequency) 기준 정렬
⑥ 소속 커뮤니티 + 원본 노트 경로 포함 반환
```

**호출 예시**:
```bash
python .team-os/graphrag/scripts/graph_search.py \
  --tool quick_search \
  --query "GraphRAG" \
  --depth 1 \
  --format json
```

**반환 구조**:
```json
{
  "entity": "GraphRAG",
  "entity_id": "e_042",
  "description": "엔티티 설명",
  "community": "C08",
  "query_level": "L0",
  "effective_depth": 1,
  "neighbors": [
    {
      "name": "Neo4j",
      "rel_type": "implements",
      "strength": 0.9,
      "source_notes": ["Library/Research/GraphRAG-Theory/note1.md"]
    }
  ],
  "rel_type_summary": {
    "implements": 3,
    "contrasts": 2,
    "extends": 1
  }
}
```

---

### 2. insight_forge(query) — L1/L2 심층 합성

**용도**: 특정 쿼리에 대한 커뮤니티 기반 다차원 인사이트 생성 (L1: depth=2, L2: depth=3 + DRIFT)

**처리 흐름**:
```
① 쿼리 → 쿼리 복잡도 분류 (L1 or L2)
② 관련 엔티티 식별 (엔티티 임베딩 유사도)
③ 식별된 엔티티의 소속 커뮤니티 탐색
④ 커뮤니티 요약(community_summaries) 수집 및 관련성 필터링
⑤ N-hop 그래프 순회 (effective_depth에 따라 max 3홉)
   L1: 엔티티 → 1차 관계 → 2차 관계
   L2: 추가로 DRIFT 확장 (커뮤니티 요약 → 후속 질문 → 로컬 드릴다운)
⑥ 수집된 컨텍스트(엔티티 + 커뮤니티 요약 + 관계) → LLM 합성
⑦ 구조화된 인사이트 보고서 반환
```

**DRIFT 확장 (L2 전용)**:
```
① 커뮤니티 요약에서 쿼리 관련 개요 획득 (글로벌 단계)
② 후속 질문(Follow-Up Questions) 자동 생성
③ 각 후속 질문에 대해 로컬 그래프 탐색 (로컬 단계)
④ 결과 통합 → 포괄적 응답
```

**호출 예시**:
```bash
# L1: depth 자동 결정 (2홉)
python .team-os/graphrag/scripts/graph_search.py \
  --tool insight_forge \
  --query "AI Safety와 alignment 연구의 핵심 접근법" \
  --format json

# L2: DRIFT 활성화
python .team-os/graphrag/scripts/graph_search.py \
  --tool insight_forge \
  --query "GraphRAG와 Neo4j 통합의 비즈니스 임팩트" \
  --drift true \
  --format json
```

**반환 구조**:
```json
{
  "query": "...",
  "query_level": "L1",
  "effective_depth": 2,
  "drift_used": false,
  "entities": ["엔티티1", "엔티티2"],
  "communities": [{"id": "C01", "summary": "..."}],
  "hop_paths": [["A", "relates_to", "B", "caused_by", "C"]],
  "synthesis": "LLM이 합성한 심층 인사이트 텍스트",
  "source_nodes": ["노트경로1", "노트경로2"]
}
```

---

### 3. panorama_search(query) — L3 글로벌 조감도

**용도**: 코퍼스 전체를 아우르는 글로벌 쿼리 처리 (L3). 맵-리듀스 패턴으로 모든 커뮤니티 처리.

**처리 흐름 (Map-Reduce)**:
```
Map 단계 (병렬):
  ① 모든 커뮤니티 요약 C_i에 대해 독립적으로 LLM 호출
  ② 각 커뮤니티: 중간 답변 A_i + 유용성 점수 H_i (0~1) 생성

필터링:
  ③ 유용성 점수 임계값(default: 0.5) 이하 제거
  ④ 상위 K개 선택 (H_i 내림차순)

Reduce 단계:
  ⑤ 필터링된 중간 답변들 → LLM으로 최종 통합 답변 생성
  ⑥ 커뮤니티 분포 + 상위 허브 엔티티 맵 생성
```

**커뮤니티 레벨 선택**:
```
C0 (루트): 최소 비용, 최고 추상화 — 빠른 개요 필요 시
C1 (default): 균형점 — 대부분의 글로벌 쿼리
C2: 중간 상세도 — 더 정밀한 포괄성 필요 시
C3 (리프): 최고 정밀도, 최대 비용 — 고정밀 전체 분석
```

**호출 예시**:
```bash
python .team-os/graphrag/scripts/graph_search.py \
  --tool panorama_search \
  --query "이 vault의 주요 AI 연구 테마" \
  --community-level 1 \
  --limit 10 \
  --format json
```

**반환 구조**:
```json
{
  "query": "...",
  "query_level": "L3",
  "strategy": "global_map_reduce",
  "community_level": 1,
  "community_map": [
    {
      "community_id": "C05",
      "summary": "커뮤니티 요약",
      "helpfulness_score": 0.87,
      "top_entities": ["엔티티A", "엔티티B"],
      "node_count": 23,
      "intermediate_answer": "이 커뮤니티의 중간 답변..."
    }
  ],
  "top_entities": [
    {"name": "엔티티A", "degree": 45, "communities": ["C05", "C12"]}
  ],
  "cross_community_edges": [["엔티티A", "rel_type", "엔티티B"]],
  "final_synthesis": "맵-리듀스로 생성된 최종 종합 답변"
}
```

---

### 4. interview(entity_name) — 엔티티 동기 분석

**용도**: 특정 엔티티가 vault 전체에서 어떤 맥락과 동기로 등장하는지 내러티브 분석

**처리 흐름**:
```
① entity_name → 전체 엣지 수집 (소스/타겟 양방향)
② 관계 유형(rel_type)별 그룹핑
③ 각 그룹 내 패턴 분석:
   - 반복 등장 맥락
   - 주요 공동 등장 엔티티
   - 시간적 분포 (노트 생성일 기준) ← 시간공간 분석
④ LLM에 전체 맥락 전달 → 엔티티 "인터뷰" 내러티브 생성
⑤ 핵심 동기 패턴 + 이례적 등장 사례 포함
```

**호출 예시**:
```bash
python .team-os/graphrag/scripts/graph_search.py \
  --tool interview \
  --query "컨텍스트 엔지니어링" \
  --format markdown
```

**반환 구조**:
```json
{
  "entity": "컨텍스트 엔지니어링",
  "total_appearances": 34,
  "rel_type_groups": {
    "enables": ["프롬프트 최적화", "멀티에이전트 조율"],
    "contrasts": ["파인튜닝", "RAG"],
    "evolved_from": ["프롬프트 엔지니어링"]
  },
  "pattern_analysis": {
    "dominant_context": "AI 에이전트 성능 향상 논의",
    "cooccurrence_leaders": ["Claude Code", "MCP 프로토콜"],
    "temporal_trend": "2025-Q4부터 급증"
  },
  "narrative": "LLM이 생성한 엔티티 동기 분석 내러티브 텍스트..."
}
```

---

## 분석공간별 필터 (선택적 활성화)

> 이론: [[6개-분석공간-개요]] — 6개 분석공간 중 쿼리 특성에 따라 관련 차원을 활성화.

| 분석공간 | 활성화 조건 | GraphRAG 필터 |
|---------|-----------|-------------|
| **계층공간** (Hierarchy) | "수준", "계층", "하위 개념" | 커뮤니티 레벨 C0~C3 선택 + hop depth 제한 |
| **시간공간** (Temporal) | "최근", "언제", "변화 추이" | `note.created` / `note.mtime` 기준 시간 필터 |
| **구조공간** (Structural) | "연결", "클러스터", "그래프 구조" | 엣지 밀도 + 커뮤니티 내부 구조 분석 |
| **인과공간** (Causal) | "왜", "원인", "영향" | DAG 방향 탐색 + `caused_by` / `enables` rel_type 우선 |
| **재귀공간** (Recursive) | "반복 패턴", "자기 참조" | 서브쿼리 재귀 분해 + ReAct 루프 |
| **다중공간** (Cross-space) | 복합 질문 | 5개 공간 동시 활성화 |

### 공간 필터 적용 예시

```bash
# 시간공간 필터: 최근 30일 노트만 탐색
python .team-os/graphrag/scripts/graph_search.py \
  --tool insight_forge \
  --query "최근 AI 에이전트 트렌드" \
  --space temporal \
  --time-window 30d

# 인과공간 필터: 원인-결과 관계 우선 탐색
python .team-os/graphrag/scripts/graph_search.py \
  --tool quick_search \
  --query "GraphRAG 성능 저하 원인" \
  --space causal \
  --rel-priority caused_by,enables,impacts
```

---

## 메타엣지 탐색 도구

> 이론: [[메타엣지-정의와-4가지-의미]] — "관계에 대한 관계". 엣지 자체를 노드로 reify하여 탐색.

### meta_edge_search(relation_type) — 관계-간-관계 탐색

**용도**: 특정 관계 타입들이 서로 어떻게 연결되는지 메타 레벨 분석
- 예: `contrasts` 관계와 `extends` 관계가 어떤 엔티티 쌍에서 공존하는가?
- 예: 신뢰도 0.7 이상인 관계들의 공통 패턴은?

**처리 흐름**:
```
① 대상 관계 타입(rel_type) 선택
② 해당 rel_type의 모든 엣지를 노드로 reify (Named Graph 방식)
③ reified 엣지들 간의 공통 패턴 탐색
④ 메타 레벨 인사이트 생성:
   - 어떤 엔티티 쌍이 여러 관계 타입으로 동시에 연결되는가?
   - 신뢰도/빈도 상위 관계들의 구조적 패턴은?
```

**호출 예시**:
```bash
python .team-os/graphrag/scripts/graph_search.py \
  --tool meta_edge_search \
  --relation-type "contrasts,extends" \
  --format json
```

**반환 구조**:
```json
{
  "relation_types_analyzed": ["contrasts", "extends"],
  "reified_edge_count": 145,
  "co_occurrence_patterns": [
    {
      "entity_pair": ["GraphRAG", "벡터 RAG"],
      "relations": ["contrasts", "evolved_from"],
      "meta_insight": "이 쌍은 대조와 진화 관계를 동시에 가짐 — 패러다임 전환 시그널"
    }
  ],
  "meta_rules_detected": [
    {
      "rule": "contrasts 관계는 동일 커뮤니티 내에서 72% 발생",
      "meta_edge_type": "엣지를 정의하는 규칙"
    }
  ]
}
```

---

## 도구 선택 매트릭스

| 사용자 의도 | L등급 | 추천 도구 |
|------------|-------|---------|
| "~이 뭔지 빠르게 확인" | L0 | `quick_search` (depth=1) |
| "~와 연관된 개념은?" | L1 | `quick_search` or `insight_forge` (depth=2) |
| "~에 대해 깊이 분석" | L1/L2 | `insight_forge` (depth=2 or 3+DRIFT) |
| "~가 왜 이 노트들에 나오는지" | L1 | `interview` |
| "~의 전체 그림" | L3 | `panorama_search` (map-reduce, C1) |
| "~에 관한 모든 관점" | L3 | `panorama_search` (C2/C3) |
| "어떤 관계들이 연결되어 있나" | — | `meta_edge_search` |

### 도구 복합 사용 패턴

```
L3 심층 분석 (글로벌→로컬):
  panorama_search → L3 전체 조감도 (커뮤니티 맵)
      ↓
  insight_forge (L2) → 핵심 커뮤니티 DRIFT 탐색
      ↓
  interview → 핵심 엔티티 동기 분석

L1 빠른 탐색 (로컬→확장):
  quick_search (L0) → 엔티티 존재 확인
      ↓
  insight_forge (L1) → 2홉 관계 탐색
      ↓
  (신뢰도 미달 시) panorama_search (L3) → 글로벌 폴백
```

---

## 에러 처리

| 에러 | 대응 |
|------|------|
| 그래프 DB 미초기화 | `python .team-os/graphrag/scripts/build_graph.py` 실행 후 재시도 |
| 엔티티 미발견 | `quick_search`로 유사 엔티티 탐색, 키워드 변경 |
| 커뮤니티 0개 반환 | 쿼리 범위 확대, L3 `panorama_search`로 전환 |
| LLM 합성 실패 | raw 결과(entities + edges)만 반환하여 수동 분석 |
| depth 초과 시도 | MAX_DEPTH_ABSOLUTE(=3)로 자동 클램핑, 경고 로그 |
| 신뢰도 미달 | Confidence-Based Adjustment로 depth 확장 또는 L3 폴백 |

---

## AT 모드 워커 역할 분담

| 워커 역할 | 담당 도구 | L등급 | 책임 |
|---------|----------|-------|------|
| **@quick-explorer** | `quick_search` | L0 | 단순 엔티티 확인, 1홉 이웃 |
| **@insight-researcher** | `insight_forge` | L1/L2 | 심층 합성, DRIFT 탐색 |
| **@panorama-scanner** | `panorama_search` | L3 | 맵-리듀스 글로벌 조망 |
| **@narrative-analyst** | `interview` | L1 | 엔티티 동기 분석 |
| **@meta-analyst** | `meta_edge_search` | — | 관계-간-관계 탐색 |

---

## 스킬 참조

- **km-graphrag-report.md**: 검색 결과 기반 ReAct 보고서 생성
- **km-graphrag-workflow/SKILL.md**: GraphRAG Mode G 전체 워크플로우
- **km-graphrag-sync.md**: 검색 결과 → frontmatter 동기화
- **km-graphrag-ontology.md**: 관계 타입 온톨로지 정의
