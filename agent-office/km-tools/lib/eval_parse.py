"""Robust extraction of an evaluator's JSON object from LLM output.

The blind lint evaluators return {"score":.., "evidence":[..], "reason":".."}.
Live runs sometimes wrap that JSON in ```json ... ``` code fences or surround it
with prose (observed 2/13 runs in the 2026-07-23 D-3 bench). This helper extracts
the JSON object tolerantly so the pipeline never mis-parses a valid response, and
never raises — parse failure is returned as a structured {"error": ...} dict.
"""
import json
import re

_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)


def extract_eval_json(raw):
    """Return the first valid JSON *object* found in `raw`.

    Tolerates: bare JSON, ```json fenced``` JSON, prose before/after the JSON.
    On failure returns {"error": <code>, "message": <detail>} (never raises).
    """
    if raw is None:
        return {"error": "EMPTY_INPUT", "message": "evaluator output was None"}
    text = str(raw).strip()
    if not text:
        return {"error": "EMPTY_INPUT", "message": "evaluator output was empty"}

    candidates = []
    # 1) contents of any ```...``` code fence (most specific first)
    for m in _FENCE_RE.finditer(text):
        inner = m.group(1).strip()
        if inner:
            candidates.append(inner)
    # 2) the whole string (bare JSON)
    candidates.append(text)
    # 3) substring from first '{' to last '}' (prose-wrapped, no fence)
    lo, hi = text.find("{"), text.rfind("}")
    if lo != -1 and hi != -1 and hi > lo:
        candidates.append(text[lo:hi + 1])

    for cand in candidates:
        try:
            obj = json.loads(cand)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict):
            return obj
    return {"error": "NO_JSON_FOUND",
            "message": "no valid JSON object in evaluator output"}


def extract_eval_score(raw, metric="score"):
    """Convenience: raw text -> object -> validated float score clamped to [0,1].

    Returns {"score": float, "clamped": bool, "raw_score": float} on success,
    or {"error": <code>, "message": <detail>} on failure. Never raises.
    """
    obj = extract_eval_json(raw)
    if "error" in obj:
        return obj
    if metric not in obj:
        return {"error": "MISSING_SCORE",
                "message": f"key '{metric}' not present in evaluator JSON"}
    try:
        val = float(obj[metric])
    except (TypeError, ValueError):
        return {"error": "SCORE_NOT_NUMERIC",
                "message": f"'{metric}'={obj[metric]!r} is not a number"}
    clamped_val = max(0.0, min(1.0, val))
    return {"score": clamped_val, "clamped": clamped_val != val, "raw_score": val}
