#!/usr/bin/env python3
"""km_link_gate.py - 노트별 링크 게이트 (KM 1.3.0 · 스펙 §8 D8).

노트마다 (1) wikilink >= 1 (2) 그 중 MOC 로 가는 링크 >= 1 을 요구한다.
노트 자신이 MOC 면 면제(PASS, reason=moc-self).

exit 0 = 전건 통과 / 1 = 미통과 1건 이상 / 2 = 측정 불가(통과 취급 금지).
표준 라이브러리만 사용한다.
"""
import argparse
import fnmatch
import json
import os
import re
import sys

DEFAULT_EXCLUDE = "_meta/*,templates/*"
LINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules"}


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def frontmatter_lines(text):
    """맨 앞 --- ... --- 블록의 본문 줄만 돌려준다(없으면 빈 목록)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    out = []
    for line in lines[1:]:
        if line.strip() in ("---", "..."):
            break
        out.append(line)
    return out


def is_moc(path, text=None):
    """MOC 판정 3축: 파일명 -MOC.md · frontmatter type: MOC · tags 에 moc."""
    if os.path.basename(path).lower().endswith("-moc.md"):
        return True
    if text is None:
        text = read_text(path)
    tags, in_tags = [], False
    for line in frontmatter_lines(text):
        m = re.match(r"^type:\s*(.+?)\s*$", line, re.I)
        if m and m.group(1).strip().strip("\"'").lower() == "moc":
            return True
        m = re.match(r"^tags:\s*(.*)$", line, re.I)
        if m:
            in_tags = True
            tags += re.findall(r"[A-Za-z0-9_/-]+", m.group(1))
            continue
        if in_tags:
            m = re.match(r"^\s*-\s*(.+?)\s*$", line)
            if m:
                tags.append(m.group(1).strip("\"'"))
                continue
            in_tags = False
    return any(t.lower() == "moc" for t in tags)


def strip_fences(text):
    """코드펜스(``` / ~~~) 안쪽은 링크 추출에서 제외한다."""
    out, fence = [], None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
                continue
            out.append(line)
        elif m and m.group(1) == fence:
            fence = None
    return "\n".join(out)


def extract_links(text):
    return [m.group(1).strip() for m in LINK_RE.finditer(strip_fences(text))]


def scan_md(vault):
    rels = []
    for root, dirs, names in os.walk(vault):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in names:
            if name.lower().endswith(".md"):
                full = os.path.join(root, name)
                rels.append(os.path.relpath(full, vault).replace(os.sep, "/"))
    return sorted(rels)


def excluded(rel, globs):
    return any(fnmatch.fnmatch(rel, g) for g in globs)


def resolve(target, index):
    """target -> vault 내 같은 basename 1건 매칭(.md 생략 허용). 모호/부재 = None."""
    stem = os.path.basename(target.strip()).strip()
    if stem.lower().endswith(".md"):
        stem = stem[:-3]
    hits = index.get(stem.lower(), [])
    return hits[0] if len(hits) == 1 else None


def judge(vault, rel, index, moc_of):
    text = read_text(os.path.join(vault, rel))
    if moc_of[rel]:
        return {"note": rel, "moc_links": 0, "links": 0,
                "verdict": "PASS", "reason": "moc-self"}
    links = extract_links(text)
    moc_links = 0
    for target in links:
        hit = resolve(target, index)
        if hit is not None and moc_of.get(hit):
            moc_links += 1
    if not links:
        reason, verdict = "no-link", "FAIL"
    elif moc_links == 0:
        reason, verdict = "no-moc-link", "FAIL"
    else:
        reason, verdict = "ok", "PASS"
    return {"note": rel, "moc_links": moc_links, "links": len(links),
            "verdict": verdict, "reason": reason}


def die_unmeasurable(msg):
    sys.stderr.write("측정 불가: %s - exit 2 는 통과 취급 ❌\n" % msg)
    return 2


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="노트별 MOC 링크>=1 · 링크>=1 게이트 (exit 0/1/2)")
    ap.add_argument("vault", help="vault 루트 경로")
    ap.add_argument("--notes", default="",
                    help="검사할 노트(vault 상대경로) 쉼표 목록. 지정 시 exclude 무시")
    ap.add_argument("--exclude", default=None,
                    help="제외 글롭 쉼표 목록(기본 %s · '' 로 해제)" % DEFAULT_EXCLUDE)
    ap.add_argument("--json", action="store_true", help="JSON 만 출력")
    args = ap.parse_args(argv)

    raw_exclude = DEFAULT_EXCLUDE if args.exclude is None else args.exclude
    globs = [g.strip() for g in raw_exclude.split(",") if g.strip()]
    vault = os.path.abspath(os.path.expanduser(args.vault))
    if not os.path.isdir(vault):
        return die_unmeasurable("vault 없음 %s" % vault)
    all_md = scan_md(vault)
    if not all_md:
        return die_unmeasurable("md 0건 %s" % vault)

    index = {}
    for rel in all_md:
        index.setdefault(os.path.basename(rel)[:-3].lower(), []).append(rel)
    moc_of = {rel: is_moc(rel, read_text(os.path.join(vault, rel)))
              for rel in all_md}

    if args.notes.strip():
        targets = [n.strip().replace(os.sep, "/")
                   for n in args.notes.split(",") if n.strip()]
        missing = [n for n in targets if n not in all_md]
        if missing:
            return die_unmeasurable("노트 없음 %s" % ",".join(missing))
    else:
        targets = [r for r in all_md if not excluded(r, globs)]
    if not targets:
        return die_unmeasurable("검사 대상 0건(exclude 과다?) %s" % vault)

    rows = [judge(vault, rel, index, moc_of) for rel in targets]
    failed = [r for r in rows if r["verdict"] == "FAIL"]
    payload = {"exclude": raw_exclude, "checked": len(rows),
               "passed": len(rows) - len(failed),
               "failed": [{k: r[k] for k in ("note", "moc_links", "links", "reason")}
                          for r in failed]}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("exclude: %s" % (raw_exclude if globs else "(none)"))
        width = max([len(r["note"]) for r in rows] + [4])
        print("%-*s  %9s  %5s  %-7s  %s"
              % (width, "note", "moc_links", "links", "verdict", "reason"))
        for r in rows:
            print("%-*s  %9d  %5d  %-7s  %s"
                  % (width, r["note"], r["moc_links"], r["links"],
                     r["verdict"], r["reason"]))
        print("checked=%d passed=%d failed=%d"
              % (payload["checked"], payload["passed"], len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
