"""Section-level diff between two markdown notes using difflib."""
import os
import re
from difflib import SequenceMatcher


def _extract_sections(content):
    """Split markdown into sections by ## headings."""
    body = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, count=1, flags=re.DOTALL)

    sections = {}
    current_heading = "(intro)"
    current_lines = []

    for line in body.split("\n"):
        if re.match(r"^##\s+", line):
            if current_lines:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def _similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def _heading_similarity(h1, h2):
    """Compare headings ignoring ## prefix."""
    clean1 = re.sub(r"^#+\s*", "", h1).strip()
    clean2 = re.sub(r"^#+\s*", "", h2).strip()
    return _similarity(clean1, clean2)


def _diff_lines(old_text, new_text, max_lines=10):
    """Generate unified diff lines (truncated)."""
    old = old_text.split("\n")
    new = new_text.split("\n")
    lines = []
    sm = SequenceMatcher(None, old, new)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "replace" or op == "delete":
            for line in old[i1:i2]:
                lines.append(f"-{line}")
        if op == "replace" or op == "insert":
            for line in new[j1:j2]:
                lines.append(f"+{line}")
        if len(lines) >= max_lines:
            break
    return lines[:max_lines]


def run_diff(existing_path, new_path):
    for p in (existing_path, new_path):
        if not os.path.exists(p):
            return {"error": "FILE_NOT_FOUND", "message": f"File not found: {p}"}

    with open(existing_path, "r", encoding="utf-8") as f:
        old_content = f.read()
    with open(new_path, "r", encoding="utf-8") as f:
        new_content = f.read()

    old_sections = _extract_sections(old_content)
    new_sections = _extract_sections(new_content)

    results = []
    matched_new = set()

    for old_h, old_body in old_sections.items():
        if old_h == "(intro)":
            continue

        # Exact heading match
        if old_h in new_sections:
            matched_new.add(old_h)
            sim = _similarity(old_body, new_sections[old_h])
            if sim < 1.0:
                results.append({
                    "type": "CHANGED",
                    "heading": old_h,
                    "similarity": round(sim, 2),
                    "diff_lines": _diff_lines(old_body, new_sections[old_h])
                })
            continue

        # Try rename detection
        # Primary: heading similarity >= 0.6
        # Fallback: body similarity >= 0.5 (catches cross-language renames)
        best_match = None
        best_sim = 0.0
        for new_h in new_sections:
            if new_h in matched_new or new_h == "(intro)":
                continue
            h_sim = _heading_similarity(old_h, new_h)
            b_sim = _similarity(old_body, new_sections[new_h])
            # Accept if headings are similar enough, or if body content
            # strongly matches (cross-language heading rename)
            combined = max(h_sim, b_sim * 0.8)
            if combined >= 0.4 and b_sim >= 0.5 and combined > best_sim:
                best_match = new_h
                best_sim = round(h_sim, 2)

        if best_match:
            matched_new.add(best_match)
            results.append({
                "type": "RENAMED",
                "heading": best_match,
                "old_heading": old_h,
                "similarity": round(best_sim, 2)
            })
        else:
            results.append({
                "type": "REMOVED",
                "heading": old_h
            })

    # New sections (not matched)
    for new_h, new_body in new_sections.items():
        if new_h not in matched_new and new_h != "(intro)":
            preview = new_body[:100].replace("\n", " ")
            results.append({
                "type": "NEW",
                "heading": new_h,
                "preview": preview
            })

    summary = {
        "new": sum(1 for r in results if r["type"] == "NEW"),
        "changed": sum(1 for r in results if r["type"] == "CHANGED"),
        "removed": sum(1 for r in results if r["type"] == "REMOVED"),
        "renamed": sum(1 for r in results if r["type"] == "RENAMED"),
    }

    markdown = _build_markdown(results)

    return {
        "summary": summary,
        "sections": results,
        "markdown": markdown
    }


def _build_markdown(results):
    lines = ["## 변경점 요약 (vs 기존 노트)"]

    new = [r for r in results if r["type"] == "NEW"]
    if new:
        lines.append("### 추가된 내용 [NEW]")
        for r in new:
            lines.append(f"- {r['heading']}: {r.get('preview', '')}")

    changed = [r for r in results if r["type"] == "CHANGED"]
    if changed:
        lines.append("### 수정된 내용 [CHANGED]")
        for r in changed:
            lines.append(f"- {r['heading']} (유사도 {r['similarity']})")

    removed = [r for r in results if r["type"] == "REMOVED"]
    if removed:
        lines.append("### 삭제된 내용 [REMOVED]")
        for r in removed:
            lines.append(f"- {r['heading']}: (삭제됨)")

    renamed = [r for r in results if r["type"] == "RENAMED"]
    if renamed:
        lines.append("### 구조 변경 [RENAMED]")
        for r in renamed:
            lines.append(f"- {r['old_heading']} → {r['heading']} (유사도 {r['similarity']})")

    return "\n".join(lines)
