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
):
    """Score every candidate and split into inline / related / log tiers.

    Returns {"inline": [...], "related": [...], "log": [...], "params": {...}}.
    Each entry carries score + per-signal breakdown. Higher score first within tier.
    Caps drop the weakest over-cap entries down to the log tier so nothing is lost.
    """
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
