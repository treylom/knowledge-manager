---
name: km-graphrag-sync
description: Use when needing GraphRAG frontmatter 양방향 동기화. TBox/ABox 분리, Named Graph 컨텍스트, 메타엣지 reified 표현, Graph DB ↔ Obsidian frontmatter 3개 필드 + meta 동기화.
---

# km-graphrag-sync: GraphRAG Frontmatter 양방향 동기화

> Graph DB ↔ Obsidian frontmatter 간 동기화, delta 감지, 충돌 해결
> 이론 기반: [[메타엣지-정의와-4가지-의미]], [[온톨로지-TBox와-ABox]] (참고: Named Graph = Quad 구조)

---

## 핵심 개념: TBox vs ABox 분리

> "RDF의 Named Graph(Quad: 주어-술어-목적어-컨텍스트)로의 진화가 메타엣지의 가장 단순한 구현이다." — §5.14

| 계층 | 개념 | Obsidian 대응 | 동기화 대상 |
|------|------|-------------|-----------|
| **TBox** (Type Box) | 개념/관계 정의, 메타데이터 스키마 | frontmatter 필드 | `graph_entity`, `graph_community`, `graph_connections` |
| **ABox** (Assertion Box) | 구체적 사실, 실제 링크 | 노트 본문 + wikilink | 본문 내 `[[wikilink]]`, 섹션 참조 |

**TBox/ABox 동기화 원칙**:
- TBox(frontmatter): Graph DB의 엔티티/커뮤니티 메타데이터 → frontmatter에 구조화
- ABox(본문): 노트 간 wikilink 패턴 → Graph DB의 엣지로 추출
- 양방향 동기화: TBox ↔ Graph DB (frontmatter 갱신), ABox → Graph DB (wikilink 추출)

---

## 동기화 대상 필드 (확장: 3+1개)

| 필드 | 타입 | 계층 | 설명 |
|------|------|------|------|
| `graph_entity` | string | TBox | 노트의 GraphRAG 엔티티 ID |
| `graph_community` | string | TBox | 소속 커뮤니티 ID |
| `graph_connections` | list | TBox + 메타엣지 | 관련 엔티티 연결 목록 (Named Graph 컨텍스트 포함) |
| `graph_meta_edges` | list | 메타엣지 전용 | reified 관계 (관계에 대한 관계) 저장 |

### graph_connections 형식 (Named Graph 컨텍스트 포함)

```yaml
graph_connections:
  - target: "entity-id-001"
    relation: "CITES"
    weight: 0.85
    # Named Graph 컨텍스트 (관계별 출처/신뢰도/추출일)
    context:
      source_note: "Library/Zettelkasten/AI-연구/note1.md"
      confidence: 0.91
      extracted_at: "2026-03-16"
      extraction_method: "wikilink"    # wikilink / co-occurrence / explicit
  - target: "entity-id-002"
    relation: "RELATED_TO"
    weight: 0.72
    context:
      source_note: "Library/Research/GraphRAG-Theory/paper.md"
      confidence: 0.78
      extracted_at: "2026-03-16"
      extraction_method: "co-occurrence"
```

상위 5개만 저장 (weight 기준 내림차순).

### graph_meta_edges 형식 (Reified 관계)

> 이론: 메타엣지 의미 1 — "엣지 자체가 노드가 되고(Reification), 그 노드들 사이에 새 엣지가 생기는 구조"

```yaml
graph_meta_edges:
  - edge_id: "edge_042_to_087"          # reified 엣지 ID
    source_entity: "entity-042"
    target_entity: "entity-087"
    relation: "contrasts"
    # 이 관계(엣지) 자체의 메타 속성
    meta_properties:
      rule_applied: "min_confidence_0.7"  # 이 엣지를 생성한 메타 규칙
      coexists_with: ["extends", "evolved_from"]  # 동일 쌍에 공존하는 관계
      leverage_effect: "high"             # 레버리지 효과 수준
    context:
      source_note: "Library/Research/note.md"
      confidence: 0.88
      extracted_at: "2026-03-16"
```

---

## Phase G6: Graph DB → Frontmatter 동기화

> 그래프 구축 완료(G6) 후 frontmatter 자동 갱신

### 실행 방식 (km-batch-python 프로토콜)

```python
# graphrag-sync-g6.py — batch 100개 / 2초 대기
BATCH_SIZE = 100
BATCH_DELAY = 2  # seconds

def sync_graph_to_frontmatter(notes_list):
    for i in range(0, len(notes_list), BATCH_SIZE):
        batch = notes_list[i:i + BATCH_SIZE]
        for note_path in batch:
            entity_data = graph_db.get_entity(note_path)
            if entity_data:
                # TBox 동기화: 엔티티/커뮤니티 메타데이터
                tbox_fields = {
                    "graph_entity": entity_data["id"],
                    "graph_community": entity_data["community"],
                    "graph_connections": get_top5_connections_with_context(entity_data),
                }
                # 메타엣지 동기화: reified 관계
                meta_edges = get_meta_edges(entity_data)
                if meta_edges:
                    tbox_fields["graph_meta_edges"] = meta_edges[:3]  # 상위 3개

                update_frontmatter(note_path, tbox_fields)
                # G6 후 frontmatter_hash 즉시 갱신
                update_hash(note_path, hash_type="frontmatter")
        if i + BATCH_SIZE < len(notes_list):
            time.sleep(BATCH_DELAY)
```

### Named Graph 컨텍스트 포함 연결 추출

```python
def get_top5_connections_with_context(entity_data) -> list:
    """
    Named Graph 방식: 관계별 출처/신뢰도/추출일을 context로 포함
    TBox 메타데이터(frontmatter) ↔ ABox 사실(wikilink+본문) 연결
    """
    connections = entity_data.get("connections", [])
    sorted_conns = sorted(connections, key=lambda x: x["weight"], reverse=True)
    return [
        {
            "target": c["target_id"],
            "relation": c["relation_type"],
            "weight": round(c["weight"], 2),
            "context": {
                "source_note": c.get("source_note", ""),
                "confidence": round(c.get("confidence", 0.0), 2),
                "extracted_at": c.get("extracted_at", ""),
                "extraction_method": c.get("extraction_method", "co-occurrence"),
            }
        }
        for c in sorted_conns[:5]
    ]

def get_meta_edges(entity_data) -> list:
    """
    Reified 관계 추출: 관계에 대한 관계(메타엣지) 표현
    동일 엔티티 쌍에 여러 rel_type이 공존하면 메타엣지 후보
    """
    meta_edges = []
    # 동일 타겟 엔티티에 대한 여러 관계 탐지
    target_groups = group_by_target(entity_data["connections"])
    for target_id, rels in target_groups.items():
        if len(rels) >= 2:  # 2개 이상 관계 공존 = 메타엣지
            meta_edges.append({
                "edge_id": f"{entity_data['id']}_to_{target_id}",
                "source_entity": entity_data["id"],
                "target_entity": target_id,
                "relation": rels[0]["relation_type"],
                "meta_properties": {
                    "coexists_with": [r["relation_type"] for r in rels[1:]],
                    "leverage_effect": "high" if len(rels) >= 3 else "medium",
                },
                "context": {
                    "source_note": rels[0].get("source_note", ""),
                    "confidence": round(rels[0].get("confidence", 0.0), 2),
                    "extracted_at": rels[0].get("extracted_at", ""),
                }
            })
    return sorted(meta_edges, key=lambda x: x["meta_properties"].get("leverage_effect", ""), reverse=True)
```

### G6 완료 후 필수 작업

```
1. 각 노트 frontmatter에 TBox 필드 기록:
   - graph_entity, graph_community, graph_connections (Named Graph 컨텍스트 포함)
   - graph_meta_edges (reified 관계, 2개 이상 공존 시)
2. frontmatter_hash 즉시 계산 및 저장 (graph_* 필드만 포함)
3. 배치 로그: .team-os/graphrag/sync_log.jsonl에 source="g6_sync" 기록
```

---

## Phase G0 Delta: Frontmatter → Graph DB 동기화

> G0 (delta detect) 단계에서 변경된 frontmatter를 Graph DB에 반영
> ABox 사실(wikilink+본문) 변경도 감지하여 엣지 추출 갱신

### TBox/ABox 분리 Delta 감지

```python
def detect_delta(note_path) -> dict:
    """
    TBox delta: graph_* frontmatter 필드 변경
    ABox delta: 본문 wikilink 패턴 변경 (content_hash 비교)
    """
    current_fm = read_frontmatter(note_path)
    current_body = read_body(note_path)

    # TBox delta (graph_* 필드)
    tbox_changed = _detect_tbox_delta(current_fm)

    # ABox delta (wikilink + 본문)
    abox_changed = _detect_abox_delta(note_path, current_body)

    return {
        "tbox_changed": tbox_changed,   # → Graph DB TBox 갱신
        "abox_changed": abox_changed,    # → 엣지 재추출 필요
    }

def _detect_tbox_delta(frontmatter) -> bool:
    """graph_* 필드 해시 비교"""
    stored_hash = frontmatter.get("frontmatter_hash", "")
    graph_fields = {k: v for k, v in frontmatter.items() if k.startswith("graph_")}
    return compute_hash(graph_fields) != stored_hash

def _detect_abox_delta(note_path, body) -> bool:
    """본문 내 wikilink 패턴 변경 감지"""
    stored_hash = get_stored_content_hash(note_path)
    return compute_content_hash(body) != stored_hash
```

### sync_log 필터링

```python
# source=system_update 항목은 무시 (시스템 자동 갱신, 충돌 아님)
def should_sync_to_graph(log_entry):
    return log_entry.get("source") != "system_update"
```

### G0 Delta 실행 순서

```
1. TBox delta 감지 (frontmatter_hash 비교)
   → 변경 시: Graph DB의 엔티티/커뮤니티 메타데이터 갱신

2. ABox delta 감지 (content_hash 비교)
   → 변경 시: wikilink 재추출 → 엣지 갱신 → TBox도 갱신 필요

3. source=system_update 항목 제외

4. 변경된 노트만 Graph DB에 반영

5. 반영 후 frontmatter_hash + content_hash 갱신
```

---

## 충돌 해결 (Conflict Resolution)

| 상황 | 판정 | 해결 방법 |
|------|------|----------|
| DB만 변경 (FM 변경 없음) | DB 우선 | DB 값을 frontmatter에 적용 (Named Graph 컨텍스트 포함) |
| FM만 변경 (`user_edit` 감지) | FM 우선 | frontmatter 값을 Graph DB에 반영 |
| 양쪽 모두 변경 | DB 우선 (부분 예외) | DB 적용, 단 user 수동 추가 항목 보존 |
| ABox(본문) 변경 | ABox 우선 | 엣지 재추출 → TBox 자동 갱신 |

### user_edit 감지

```python
def is_user_edit(log_entry):
    return log_entry.get("source") == "user_edit"
```

### 양쪽 변경 시 병합 규칙 (메타엣지 보존 포함)

```python
def merge_connections(db_connections, fm_connections):
    """
    DB 연결 기반 + FM에서 user가 수동 추가한 항목 보존
    user 수동 추가는 Named Graph 컨텍스트의 extraction_method="manual"로 식별
    """
    db_set = {c["target"] for c in db_connections}
    user_added = [
        c for c in fm_connections
        if c["target"] not in db_set
        and c.get("context", {}).get("extraction_method") == "manual"
    ]

    merged = db_connections[:5]  # DB 기준 상위 5개
    merged.extend(user_added)    # user 수동 추가 보존
    return merged

def merge_meta_edges(db_meta_edges, fm_meta_edges):
    """
    메타엣지 병합: DB에서 새로 감지된 reified 관계 + user 수동 추가 보존
    """
    db_edge_ids = {e["edge_id"] for e in db_meta_edges}
    user_added_meta = [
        e for e in fm_meta_edges
        if e["edge_id"] not in db_edge_ids
    ]
    merged = db_meta_edges[:3]       # DB 기준 상위 3개
    merged.extend(user_added_meta)   # user 추가 보존
    return merged
```

---

## content_hash vs frontmatter_hash 구분

| 해시 | 대상 | 용도 |
|------|------|------|
| `content_hash` | graph_* 필드 **제외** + 본문(ABox) | 콘텐츠 변경 감지 → 엣지 재추출 트리거 |
| `frontmatter_hash` | graph_* 필드만 (TBox) | 그래프 동기화 상태 추적 |

### 해시 계산

```python
def compute_content_hash(note) -> str:
    """ABox: graph_* 필드 제외한 frontmatter + 본문"""
    fm = {
        k: v for k, v in note.frontmatter.items()
        if not k.startswith("graph_") and k not in ("frontmatter_hash", "content_hash")
    }
    content = note.body_text
    return hashlib.md5(f"{fm}{content}".encode()).hexdigest()[:16]

def compute_frontmatter_hash(note) -> str:
    """TBox: graph_* 필드만 (Named Graph 컨텍스트 포함)"""
    graph_fields = {
        "graph_entity": note.frontmatter.get("graph_entity", ""),
        "graph_community": note.frontmatter.get("graph_community", ""),
        "graph_connections": note.frontmatter.get("graph_connections", []),
        "graph_meta_edges": note.frontmatter.get("graph_meta_edges", []),
    }
    return hashlib.md5(str(graph_fields).encode()).hexdigest()[:16]
```

---

## 메타엣지 동기화 상세

### 메타엣지 레버리지 효과 반영

> "한번더 메타계층이나온다 이게 레버다" — 세미나 줄 105
> 메타엣지(META_EDGE_RULES) 변경 시 전체 그래프 재인덱싱 트리거

```python
# 현재 적용 중인 메타엣지 규칙 (엣지 생성 기준)
META_EDGE_RULES = {
    "min_confidence": 0.7,      # 신뢰도 기준 메타엣지
    "max_age_days": 180,        # 최신성 기준 메타엣지
    "min_cooccurrence": 2,      # 빈도 기준 메타엣지
}

def trigger_reindex_on_meta_rule_change(old_rules, new_rules):
    """메타엣지 규칙 변경 시 전체 그래프 재인덱싱 트리거"""
    if old_rules != new_rules:
        log_info("메타엣지 규칙 변경 감지 → 전체 그래프 재인덱싱")
        # 레버리지 효과: 규칙 하나 변경 → 모든 엣지 재평가
        schedule_full_reindex(reason="meta_edge_rule_change")
```

### 온톨로지 변경 시 재동기화 트리거

```
km-graphrag-ontology.md 관계 타입 변경
    → META_EDGE_RULES 업데이트
    → 전체 wikilink 재추출 (ABox 재처리)
    → 모든 노트 content_hash 무효화
    → G6 동기화 재실행
```

---

## 동기화 로그 형식

```jsonl
{"ts": "2026-03-16T10:00:00Z", "note": "Library/Zettelkasten/AI-연구/note.md", "source": "g6_sync", "fields": ["graph_entity", "graph_community", "graph_connections", "graph_meta_edges"], "delta_type": "tbox", "status": "ok"}
{"ts": "2026-03-16T10:00:01Z", "note": "Library/Zettelkasten/AI-연구/note2.md", "source": "user_edit", "fields": ["graph_connections"], "delta_type": "tbox", "status": "ok"}
{"ts": "2026-03-16T10:00:02Z", "note": "Library/Research/note.md", "source": "abox_change", "fields": ["graph_connections"], "delta_type": "abox", "status": "ok", "edges_reextracted": 3}
{"ts": "2026-03-16T10:00:03Z", "note": "Library/Zettelkasten/note3.md", "source": "g6_sync", "fields": ["graph_meta_edges"], "delta_type": "meta_edge", "status": "ok", "meta_edges_added": 1}
```

**log source 값**:
- `g6_sync`: G6 그래프 구축 후 자동 동기화
- `user_edit`: 사용자 수동 frontmatter 수정
- `system_update`: 시스템 자동 갱신 (delta 무시)
- `abox_change`: 본문/wikilink 변경으로 인한 엣지 갱신

---

## 동기화 체크리스트

```
□ G6 완료 후 sync 실행?
□ TBox 필드 (graph_entity, graph_community, graph_connections) 갱신?
□ Named Graph 컨텍스트 (source_note, confidence, extracted_at, extraction_method) 포함?
□ graph_meta_edges 갱신 (reified 관계 2개 이상 공존 엔티티)?
□ frontmatter_hash 즉시 갱신?
□ content_hash 갱신 (ABox delta 시)?
□ source=system_update 항목 제외 확인?
□ user 수동 추가 항목 보존 (extraction_method=manual)?
□ 메타엣지 레버리지 효과 확인 (META_EDGE_RULES 변경 시)?
□ sync_log.jsonl 기록 완료?
```

---

## 연동 스킬

| 단계 | 참조 스킬 |
|------|----------|
| G0 delta 감지 | `km-graphrag-workflow.md` Phase G0 |
| G6 그래프 구축 완료 | `km-graphrag-workflow.md` Phase G6 |
| 배치 실행 프로토콜 | `km-batch-python.md` |
| Graph DB 온톨로지 | `km-graphrag-ontology.md` |
| 메타엣지 탐색 | `km-graphrag-search.md` (`meta_edge_search` 도구) |
