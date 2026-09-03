"""Link scorer — score candidate wikilinks and tier them by strength.

Core is stdlib-only and has ZERO graphrag / embedding dependency: the public
Knowledge Manager repo works fully without any of our infrastructure. A
semantic signal can be added optionally through a SemanticAdapter (see
adapters/), which is disabled by default (config unset -> heuristic only).

Design SoT: Knowledge-Manager 고도화 설계 v1 (2026-07-03) §1.
Signals (weights, heuristic core):
    title/alias match   0.35   candidate named in target (or vice versa)
    tag overlap         0.15   Jaccard of tag sets
    folder/MOC proximity 0.15  same folder / shared hub
    body co-occurrence  0.20   significant-term overlap of bodies
    recency             0.05   candidate recently updated
    (adapter) semantic  +0.30  optional similarity, capped
Tiered placement (inline threshold configurable, default 0.6):
    score >= inline_threshold        -> inline [[link]]
    related_threshold <= s < inline  -> "관련 문서" section
    s < related_threshold            -> log only (candidate record)
Caps: inline <= 5, related <= 7 (over-linking = graph noise).
"""
import math
import re

# Weights (heuristic core — must sum to 1.0 without the optional adapter)
W_NAME = 0.35
W_TAG = 0.15
W_FOLDER = 0.15
W_COOCCUR = 0.20
W_RECENCY = 0.05
SEMANTIC_CAP = 0.30  # optional adapter additive ceiling

DEFAULT_INLINE_THRESHOLD = 0.6   # 재경님 확정 2026-07-03 (0.7 아님 — 과소링크 방지). 실측 후 잠금.
DEFAULT_RELATED_THRESHOLD = 0.4
MAX_INLINE = 5
MAX_RELATED = 7

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")
# very common ko/en stopwords — kept tiny + stdlib; drop from co-occurrence terms
_STOPWORDS = frozenset(
    """the a an of to in on for and or is are be this that it as with by at from
    있다 없다 하는 하고 그리고 그러나 또는 이런 저런 것 수 등 및 를 을 이 가 은 는 에 의 와 과 도 로 으로""".split()
)


def _norm(s):
    return (s or "").strip().lower()


def _tokens(text, *, drop_stop=True):
    toks = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    if drop_stop:
        toks = [t for t in toks if t not in _STOPWORDS and len(t) > 1]
    return toks


def _names(note):
    """Canonical name set for a note = title + aliases (normalized)."""
    out = set()
    if note.get("title"):
        out.add(_norm(note["title"]))
    for a in note.get("aliases") or []:
        if a:
            out.add(_norm(a))
    return {n for n in out if n}


def _name_match(target, cand):
    """0..1 — is the candidate named inside the target (title or body)?

    Bidirectional but target->candidate weighted higher (the new note referencing
    an existing concept is the primary link direction).
    """
    cand_names = _names(cand)
    if not cand_names:
        return 0.0
    hay_title = _norm(target.get("title", ""))
    hay_body = _norm(target.get("body", ""))
    best = 0.0
    for name in cand_names:
        if not name:
            continue
        # exact whole-name occurrence in target title = strongest
        if name and name in hay_title:
            best = max(best, 1.0)
        elif name and name in hay_body:
            best = max(best, 0.85)
        else:
            # token-subset: all candidate-name tokens present in target body
            nt = set(_tokens(name, drop_stop=False))
            if nt:
                bt = set(_tokens(hay_body, drop_stop=False))
                if nt <= bt:
                    best = max(best, 0.55)
    # reverse direction (target named in candidate body) — weaker
    if best < 0.85:
        tgt_names = _names(target)
        cand_body = _norm(cand.get("body", ""))
        for name in tgt_names:
            if name and name in cand_body:
                best = max(best, 0.6)
                break
    return best


def _jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _tag_overlap(target, cand):
    ta = {_norm(t) for t in (target.get("tags") or []) if t}
    tb = {_norm(t) for t in (cand.get("tags") or []) if t}
    return _jaccard(ta, tb)


def _folder_proximity(target, cand):
    """1.0 same folder, 0.5 shared top-level area, +0.5 shared MOC hub (capped 1)."""
    fa = _norm(target.get("folder", "")).strip("/")
    fb = _norm(cand.get("folder", "")).strip("/")
    score = 0.0
    if fa and fb:
        if fa == fb:
            score = 1.0
        else:
            top_a = fa.split("/")[0]
            top_b = fb.split("/")[0]
            if top_a and top_a == top_b:
                score = 0.5
    # shared MOC / hub membership (explicit signal if provided)
    ma = {_norm(m) for m in (target.get("mocs") or []) if m}
    mb = {_norm(m) for m in (cand.get("mocs") or []) if m}
    if ma & mb:
        score = min(1.0, score + 0.5)
    return score


def _cooccurrence(target, cand):
    """Significant-term Jaccard of the two bodies (bounded, de-noised)."""
    ta = set(_tokens(target.get("body", "")))
    tb = set(_tokens(cand.get("body", "")))
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    # normalize by the smaller doc so a long note doesn't dominate
    denom = min(len(ta), len(tb))
    raw = inter / denom if denom else 0.0
    # squash: modest shared vocab is common; reward genuine overlap
    return min(1.0, raw * 1.5)


def _recency(cand):
    """0..1 decay on candidate age in days (half-life ~45d)."""
    age = cand.get("mtime_days_ago")
    if age is None:
        return 0.0
    try:
        age = float(age)
    except (TypeError, ValueError):
        return 0.0
    if age < 0:
        age = 0.0
    return math.exp(-age / 45.0 * math.log(2))  # 1.0 at 0d, 0.5 at 45d


def score_candidate(target, cand, adapter=None):
    """Return {score, tier-less, signals{...}} for one candidate vs target."""
    s_name = _name_match(target, cand)
    s_tag = _tag_overlap(target, cand)
    s_folder = _folder_proximity(target, cand)
    s_co = _cooccurrence(target, cand)
    s_rec = _recency(cand)

    base = (
        W_NAME * s_name
        + W_TAG * s_tag
        + W_FOLDER * s_folder
        + W_COOCCUR * s_co
        + W_RECENCY * s_rec
    )

    semantic = 0.0
    if adapter is not None and getattr(adapter, "is_available", lambda: False)():
        sim = adapter.similarity(target, cand)
        if sim is not None:
            semantic = SEMANTIC_CAP * max(0.0, min(1.0, float(sim)))

    total = round(min(1.0, base + semantic), 4)
    return {
        "title": cand.get("title", ""),
        "score": total,
        "signals": {
            "name": round(s_name, 3),
            "tag": round(s_tag, 3),
            "folder": round(s_folder, 3),
            "cooccur": round(s_co, 3),
            "recency": round(s_rec, 3),
            "semantic": round(semantic, 3),
        },
    }


def score_links(
    target,
    candidates,
    *,
    inline_threshold=DEFAULT_INLINE_THRESHOLD,
    related_threshold=DEFAULT_RELATED_THRESHOLD,
    adapter=None,
    max_inline=MAX_INLINE,
    max_related=MAX_RELATED,
    scheme="v1",
    moc_gate="auto",
    graph_edges=None,
):
    """Score every candidate and split into inline / related / log tiers.

    Returns {"inline": [...], "related": [...], "log": [...], "params": {...}}.
    Each entry carries score + per-signal breakdown. Higher score first within tier.
    Caps drop the weakest over-cap entries down to the log tier so nothing is lost.

    scheme="v2" delegates to the 0~100 rubric (_score_links_v2); the default
    scheme="v1" path below is unchanged.
    """
    if scheme == "v2":
        return _score_links_v2(
            target,
            candidates,
            adapter=adapter,
            max_inline=max_inline,
            max_related=max_related,
            moc_gate=moc_gate,
            graph_edges=graph_edges,
        )

    scored = []
    self_title = _norm(target.get("title", ""))
    for c in candidates:
        if _norm(c.get("title", "")) == self_title and self_title:
            continue  # never link a note to itself
        scored.append(score_candidate(target, c, adapter=adapter))
    scored.sort(key=lambda x: (-x["score"], x["title"]))

    inline, related, log = [], [], []
    for entry in scored:
        s = entry["score"]
        if s >= inline_threshold:
            entry["tier"] = "inline"
            (inline if len(inline) < max_inline else related).append(entry)
        elif s >= related_threshold:
            entry["tier"] = "related"
            (related if len(related) < max_related else log).append(entry)
        else:
            entry["tier"] = "log"
            log.append(entry)
    # over-cap demotions may exceed the related cap too -> push remainder to log
    if len(related) > max_related:
        for e in related[max_related:]:
            e["tier"] = "log"
        log.extend(related[max_related:])
        related = related[:max_related]

    return {
        "inline": inline,
        "related": related,
        "log": log,
        "params": {
            "inline_threshold": inline_threshold,
            "related_threshold": related_threshold,
            "adapter": bool(adapter and getattr(adapter, "is_available", lambda: False)()),
            "max_inline": max_inline,
            "max_related": max_related,
        },
    }


# ---------------------------------------------------------------------------
# Scheme v2 — 0~100 배점 (구조 40 · 내용 45 · 의미 25)
# SoT: KM 인터뷰 개편 설계 §9 D11 · 링크 가중치 배점표 §3.
# 위쪽 v1 코드·상수는 손대지 않는다. v2 는 순수 추가분이며 scheme="v1"(기본값)
# 경로에서는 호출되지 않는다.
# ---------------------------------------------------------------------------
V2_STRUCTURE_CAP = 40
V2_MOC_SHARED = 15
V2_BACKLINK = 15
V2_FOLDER_SAME = 10
V2_FOLDER_TOP = 5

V2_CONTENT_CAP = 45
V2_NAME_EXACT = 20
V2_NAME_IN_TITLE = 17
V2_NAME_IN_BODY = 11
V2_COOCCUR = 15
V2_TAG = 10

V2_SEMANTIC_CAP = 25
V2_SEMANTIC_COSINE = 25
V2_GRAPH_EDGE = 10

V2_RECENCY_TIEBREAK = 2  # 점수 아님 — 동점 정렬에만 쓰는 ±2

V2_INLINE_THRESHOLD = 60
V2_RELATED_THRESHOLD = 40
V2_FRONTMATTER_THRESHOLD = 25

V2_CLUSTER_JACCARD = 0.6  # 후보끼리 제목 토큰 자카드 >= 이 값 = 같은 군집

DEFAULT_SCHEME = "v1"
DEFAULT_MOC_GATE = "auto"

_WIKILINK_RE = re.compile(r"\[\[([^\[\]|#]+)")


def _wikilink_targets(note):
    """Normalized [[wikilink]] targets found in a note body."""
    return {_norm(m) for m in _WIKILINK_RE.findall(note.get("body") or "")}


def _links_to(src, dst):
    """True if src's body already carries a [[link]] to dst (title or alias)."""
    return bool(_names(dst) & _wikilink_targets(src))


def _is_moc(note):
    """MOC 판정 — 명시 플래그 우선, 없으면 제목 토큰에 'moc'."""
    if note.get("is_moc"):
        return True
    return "moc" in _tokens(note.get("title", ""), drop_stop=False)


def _structure_points(target, cand):
    """구조 축(상한 40) — MOC 공유 15 · 위키링크 역추적 15 · 폴더 10/5."""
    ma = {_norm(m) for m in (target.get("mocs") or []) if m}
    mb = {_norm(m) for m in (cand.get("mocs") or []) if m}
    fa = _norm(target.get("folder", "")).strip("/")
    fb = _norm(cand.get("folder", "")).strip("/")
    folder = 0
    if fa and fb:
        if fa == fb:
            folder = V2_FOLDER_SAME
        elif fa.split("/")[0] == fb.split("/")[0]:
            folder = V2_FOLDER_TOP
    backlink = _links_to(target, cand) or _links_to(cand, target)
    return {
        "moc_shared": V2_MOC_SHARED if (ma & mb) else 0,
        "backlink": V2_BACKLINK if backlink else 0,
        "folder": folder,
    }


def _name_points_v2(target, cand):
    """제목/별칭 일치 — 정확 20 · 제목 안 17 · 본문 안 11."""
    title = _norm(target.get("title", ""))
    body = _norm(target.get("body", ""))
    best = 0
    for name in _names(cand):
        if title and name == title:
            best = max(best, V2_NAME_EXACT)
        elif title and name in title:
            best = max(best, V2_NAME_IN_TITLE)
        elif body and name in body:
            best = max(best, V2_NAME_IN_BODY)
    if best < V2_NAME_IN_BODY:
        cand_body = _norm(cand.get("body", ""))
        for name in _names(target):
            if cand_body and name in cand_body:
                best = max(best, V2_NAME_IN_BODY)
                break
    return best


def _content_points(target, cand):
    """내용 축(상한 45) — 제목 20/17/11 · 본문 공출현 15 · 태그 자카드 10."""
    return {
        "name": float(_name_points_v2(target, cand)),
        "cooccur": _cooccurrence(target, cand) * V2_COOCCUR,
        "tag": _tag_overlap(target, cand) * V2_TAG,
    }


def _graph_edge_points(target, cand, graph_edges):
    """graph_edges 에 (target, cand) 관계가 있으면 +10 (방향 무관)."""
    if not graph_edges:
        return 0
    a, b = _names(target), _names(cand)
    for edge in graph_edges:
        if isinstance(edge, dict):
            src = _norm(edge.get("source") or edge.get("from") or "")
            dst = _norm(edge.get("target") or edge.get("to") or "")
        else:
            pair = list(edge)
            if len(pair) < 2:
                continue
            src, dst = _norm(pair[0]), _norm(pair[1])
        if not src or not dst:
            continue
        if (src in a and dst in b) or (src in b and dst in a):
            return V2_GRAPH_EDGE
    return 0


def _semantic_points(target, cand, adapter, graph_edges):
    """의미 축(상한 25) — 어댑터 코사인 × 25 · 그래프 관계 엣지 +10."""
    cosine = 0.0
    if adapter is not None and getattr(adapter, "is_available", lambda: False)():
        sim = adapter.similarity(target, cand)
        if sim is not None:
            cosine = V2_SEMANTIC_COSINE * max(0.0, min(1.0, float(sim)))
    return {
        "cosine": cosine,
        "graph_edge": float(_graph_edge_points(target, cand, graph_edges)),
    }


def _recency_tiebreak(cand):
    """최신성은 점수가 아니다 — 동점일 때만 쓰는 ±2 정렬 보정값."""
    return round((_recency(cand) - 0.5) * 2 * V2_RECENCY_TIEBREAK, 3)


def _explain_reasons(struct, content, semantic):
    """설명 1줄에 실을 상위 이유 2개."""
    name_label = "제목 일치" if content["name"] >= V2_NAME_IN_TITLE else "본문 언급"
    folder_label = "같은 폴더" if struct["folder"] == V2_FOLDER_SAME else "같은 상위 폴더"
    labeled = [
        (struct["moc_shared"], "같은 MOC"),
        (struct["backlink"], "기존 링크"),
        (content["name"], name_label),
        (content["cooccur"], "본문 공출현"),
        (struct["folder"], folder_label),
        (content["tag"], "태그 겹침"),
        (semantic["cosine"], "의미 유사"),
        (semantic["graph_edge"], "그래프 관계"),
    ]
    ranked = sorted([x for x in labeled if x[0] > 0], key=lambda x: -x[0])
    reasons = [label for _, label in ranked][:2]
    return "·".join(reasons) if reasons else "뚜렷한 신호 없음"


def score_candidate_v2(target, cand, adapter=None, graph_edges=None):
    """v2 점수 1건 — 0~100 정수 · 축별 점수 · 신호 · 설명 1줄."""
    struct = _structure_points(target, cand)
    content = _content_points(target, cand)
    semantic = _semantic_points(target, cand, adapter, graph_edges)

    s_axis = min(V2_STRUCTURE_CAP, int(round(sum(struct.values()))))
    c_axis = min(V2_CONTENT_CAP, int(round(sum(content.values()))))
    m_axis = min(V2_SEMANTIC_CAP, int(round(sum(semantic.values()))))
    total = min(100, s_axis + c_axis + m_axis)

    return {
        "title": cand.get("title", ""),
        "score": total,
        "axes": {"structure": s_axis, "content": c_axis, "semantic": m_axis},
        "signals": {
            "moc_shared": struct["moc_shared"],
            "backlink": struct["backlink"],
            "folder": struct["folder"],
            "name": round(content["name"], 3),
            "cooccur": round(content["cooccur"], 3),
            "tag": round(content["tag"], 3),
            "semantic_cosine": round(semantic["cosine"], 3),
            "graph_edge": semantic["graph_edge"],
            "recency_tiebreak": _recency_tiebreak(cand),
            "is_moc": _is_moc(cand),
        },
        "explain": "{}점(구조 {}·내용 {}·의미 {}): {}".format(
            total, s_axis, c_axis, m_axis,
            _explain_reasons(struct, content, semantic),
        ),
    }


def collapse_clusters(entries, threshold=V2_CLUSTER_JACCARD):
    """제목 토큰 자카드 >= threshold 후보 군집 = 대표 1 유지, 나머지 접기.

    대표 = 군집에 MOC 가 있으면 그 MOC(최고점), 없으면 최고점 항목.
    Returns (kept, collapsed) — 접힌 항목엔 "collapsed": True 가 붙는다.
    """
    token_sets = [set(_tokens(e.get("title", ""), drop_stop=False)) for e in entries]
    taken = [False] * len(entries)
    kept, collapsed = [], []
    for i, entry in enumerate(entries):
        if taken[i]:
            continue
        group = [i]
        taken[i] = True
        for j in range(i + 1, len(entries)):
            if taken[j]:
                continue
            if any(_jaccard(token_sets[k], token_sets[j]) >= threshold for k in group):
                group.append(j)
                taken[j] = True
        members = [entries[k] for k in group]
        if len(members) == 1:
            kept.append(entry)
            continue
        mocs = [m for m in members if m.get("signals", {}).get("is_moc")]
        rep = max(mocs or members, key=lambda e: e.get("score", 0))
        for member in members:
            if member is rep:
                kept.append(member)
            else:
                member["collapsed"] = True
                collapsed.append(member)
    return kept, collapsed


def _closest_moc(target, moc_notes):
    """가장 가까운 MOC — 폴더 조상 체인 → 태그 최다 공유 → 상위 폴더."""
    fa = _norm(target.get("folder", "")).strip("/")
    ta = {_norm(t) for t in (target.get("tags") or []) if t}

    best, best_depth = None, -1
    for note in moc_notes:
        fb = _norm(note.get("folder", "")).strip("/")
        if fa and fb and (fa == fb or fa.startswith(fb + "/")):
            depth = len(fb.split("/"))
            if depth > best_depth:
                best, best_depth = note, depth
    if best is not None:
        return best, "ancestor-folder"

    best, best_shared = None, 0
    for note in moc_notes:
        shared = len(ta & {_norm(t) for t in (note.get("tags") or []) if t})
        if shared > best_shared:
            best, best_shared = note, shared
    if best is not None:
        return best, "tag-majority"

    for note in moc_notes:
        fb = _norm(note.get("folder", "")).strip("/")
        if fa and fb and fa.split("/")[0] == fb.split("/")[0]:
            return note, "top-folder"

    return None, "none"


def _moc_gate_decide(target, top_entries, moc_notes, mode):
    """MOC 게이트 판정 — 상위 후보에 MOC 가 0 일 때만 가장 가까운 MOC 를 고른다."""
    linked = [e for e in top_entries if e.get("signals", {}).get("is_moc")]
    if linked:
        return {"mode": mode, "chosen": linked[0]["title"], "reason": "already-linked"}
    own = [m for m in (target.get("mocs") or []) if m]
    if own:
        return {"mode": mode, "chosen": own[0], "reason": "already-linked"}
    note, reason = _closest_moc(target, moc_notes)
    return {
        "mode": mode,
        "chosen": note.get("title", "") if note is not None else None,
        "reason": reason,
    }


def _v2_sort_key(entry):
    return (-entry["score"], -entry["signals"]["recency_tiebreak"], entry["title"])


def _score_links_v2(
    target,
    candidates,
    *,
    adapter=None,
    max_inline=MAX_INLINE,
    max_related=MAX_RELATED,
    moc_gate=DEFAULT_MOC_GATE,
    graph_edges=None,
):
    """v2 채점 + 등급(inline/related/frontmatter/log) + MOC 게이트 + 군집 접기."""
    scored = []
    self_title = _norm(target.get("title", ""))
    for c in candidates:
        if _norm(c.get("title", "")) == self_title and self_title:
            continue  # never link a note to itself
        scored.append(
            score_candidate_v2(target, c, adapter=adapter, graph_edges=graph_edges)
        )
    scored.sort(key=_v2_sort_key)

    kept, collapsed = collapse_clusters(scored)
    kept.sort(key=_v2_sort_key)

    inline, related, frontmatter, log = [], [], [], []
    for entry in kept:
        s = entry["score"]
        if s >= V2_INLINE_THRESHOLD:
            entry["tier"] = "inline"
            (inline if len(inline) < max_inline else related).append(entry)
        elif s >= V2_RELATED_THRESHOLD:
            entry["tier"] = "related"
            (related if len(related) < max_related else frontmatter).append(entry)
        elif s >= V2_FRONTMATTER_THRESHOLD:
            entry["tier"] = "frontmatter"
            frontmatter.append(entry)
        else:
            entry["tier"] = "log"
            log.append(entry)
    if len(related) > max_related:
        for e in related[max_related:]:
            e["tier"] = "frontmatter"
        frontmatter.extend(related[max_related:])
        related = related[:max_related]
    for e in collapsed:
        e["tier"] = "log"
    log.extend(collapsed)

    gate = _moc_gate_decide(
        target, inline + related, [c for c in candidates if _is_moc(c)], moc_gate
    )
    if (
        moc_gate == "auto"
        and gate["chosen"]
        and gate["reason"] not in ("already-linked", "none")
    ):
        moved = None
        for bucket in (frontmatter, log):
            for e in bucket:
                if e["title"] == gate["chosen"]:
                    moved = (bucket, e)
                    break
            if moved:
                break
        if moved:
            bucket, entry = moved
            bucket.remove(entry)
            entry["tier"] = "related"
            entry["moc_gate"] = True
            related.append(entry)

    return {
        "inline": inline,
        "related": related,
        "frontmatter": frontmatter,
        "log": log,
        "moc_gate": gate,
        "params": {
            "scheme": "v2",
            "inline_threshold": V2_INLINE_THRESHOLD,
            "related_threshold": V2_RELATED_THRESHOLD,
            "frontmatter_threshold": V2_FRONTMATTER_THRESHOLD,
            "adapter": bool(adapter and getattr(adapter, "is_available", lambda: False)()),
            "max_inline": max_inline,
            "max_related": max_related,
            "moc_gate": moc_gate,
        },
    }


def weights_table_markdown(scheme="v2"):
    """배점표를 마크다운 표로 — skills/km-link-strengthening.md §2.2 의 생성 원본."""
    if scheme != "v2":
        raise ValueError("weights_table_markdown: scheme='v2' 만 지원한다")
    structure = "구조 (상한 {})".format(V2_STRUCTURE_CAP)
    content = "내용 (상한 {})".format(V2_CONTENT_CAP)
    semantic = "의미 (상한 {})".format(V2_SEMANTIC_CAP)
    rows = [
        (structure, "MOC 공유", "{}".format(V2_MOC_SHARED)),
        (structure, "위키링크 역추적 (후보→대상 또는 대상→후보 기존 링크)",
         "{}".format(V2_BACKLINK)),
        (structure, "같은 폴더 / 같은 상위 폴더",
         "{} / {}".format(V2_FOLDER_SAME, V2_FOLDER_TOP)),
        (content, "제목·별칭 일치 (정확 / 제목 안 / 본문 안)",
         "{} / {} / {}".format(V2_NAME_EXACT, V2_NAME_IN_TITLE, V2_NAME_IN_BODY)),
        (content, "본문 공출현 (자카드 × {})".format(V2_COOCCUR),
         "{}".format(V2_COOCCUR)),
        (content, "태그 자카드", "{}".format(V2_TAG)),
        (semantic, "어댑터 코사인 × {}".format(V2_SEMANTIC_COSINE),
         "{}".format(V2_SEMANTIC_COSINE)),
        (semantic, "그래프 관계 엣지", "+{}".format(V2_GRAPH_EDGE)),
        ("최신성", "동점 타이브레이커 (정렬 전용 · 점수 아님)",
         "±{}".format(V2_RECENCY_TIEBREAK)),
        ("등급", "인라인 ≥{} (상한 {}) · 관련 {}~{} (상한 {}) · frontmatter {}~{} · 로그 <{}".format(
            V2_INLINE_THRESHOLD, MAX_INLINE,
            V2_RELATED_THRESHOLD, V2_INLINE_THRESHOLD - 1, MAX_RELATED,
            V2_FRONTMATTER_THRESHOLD, V2_RELATED_THRESHOLD - 1,
            V2_FRONTMATTER_THRESHOLD), "—"),
    ]
    lines = ["| 축 | 항목 | 점수 |", "|---|---|---|"]
    lines += ["| {} | {} | {} |".format(*r) for r in rows]
    return "\n".join(lines)
