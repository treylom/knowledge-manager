"""Lint score calculation — mechanical metrics + LLM-provided scores."""
import os
import re
import yaml


REQUIRED_FIELDS = ["tags", "author", "date", "source", "aliases"]
WEIGHTS = {
    "completeness": 0.20,
    "connections": 0.20,
    "consistency": 0.25,
    "suggestions": 0.15,
    "coverage": 0.20,
}


def _parse_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _count_wikilinks(content):
    """Count [[wikilink]] occurrences in body (after frontmatter)."""
    body = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, count=1, flags=re.DOTALL)
    return len(re.findall(r"\[\[([^\]]+)\]\]", body))


def _score_completeness(frontmatter):
    filled = sum(1 for f in REQUIRED_FIELDS if frontmatter.get(f))
    value = filled / len(REQUIRED_FIELDS)
    detail = {f: bool(frontmatter.get(f)) for f in REQUIRED_FIELDS}
    return value, detail


def _score_connections(count):
    if count == 0:
        value = 0.2
    elif count <= 2:
        value = 0.6
    elif count <= 8:
        value = 1.0
    else:
        value = 0.8
    return value, {"count": count, "range": "3-8"}


def _proof_class(eval_source):
    """Independent only when a blind subagent produced the judged scores; else self-lint."""
    return "independent" if str(eval_source).startswith("subagent:") else "self-lint"


def run_lint(draft_path, consistency, suggestions, coverage, eval_source="llm"):
    if not os.path.exists(draft_path):
        return {"error": "FILE_NOT_FOUND", "message": f"File not found: {draft_path}"}

    with open(draft_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter = _parse_frontmatter(content)
    link_count = _count_wikilinks(content)

    comp_val, comp_detail = _score_completeness(frontmatter)
    conn_val, conn_detail = _score_connections(link_count)

    warnings = []
    llm_metrics = {"consistency": consistency, "suggestions": suggestions, "coverage": coverage}
    for name, val in llm_metrics.items():
        if val is None:
            llm_metrics[name] = 0.0
            warnings.append(f"Missing --{name}, defaulting to 0.0")
        elif val < 0.0 or val > 1.0:
            # A judged metric (LLM/subagent) out of [0,1] would inflate/deflate the
            # weighted score. Clamp defensively so a hallucinated score can't skew pass/fail.
            clamped = max(0.0, min(1.0, val))
            warnings.append(f"--{name} {val} out of [0,1], clamped to {clamped}")
            llm_metrics[name] = clamped

    breakdown = {
        "completeness": {"value": comp_val, "weight": WEIGHTS["completeness"], "detail": comp_detail},
        "connections": {"value": conn_val, "weight": WEIGHTS["connections"], "detail": conn_detail},
        "consistency": {"value": llm_metrics["consistency"], "weight": WEIGHTS["consistency"], "source": eval_source},
        "suggestions": {"value": llm_metrics["suggestions"], "weight": WEIGHTS["suggestions"], "source": eval_source},
        "coverage": {"value": llm_metrics["coverage"], "weight": WEIGHTS["coverage"], "source": eval_source},
    }

    lint_score = round(sum(b["value"] * b["weight"] for b in breakdown.values()), 2)

    return {
        "schema_version": "km-lint-1.1",
        "lint_score": lint_score,
        "passed": lint_score >= 0.7,
        "threshold": 0.7,
        "proof_class": _proof_class(eval_source),
        "breakdown": breakdown,
        "warnings": warnings,
    }
