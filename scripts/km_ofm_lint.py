#!/usr/bin/env python3
"""km_ofm_lint.py - Obsidian Flavored Markdown 경고 검사 (KM · 경고 모드).

검사 5종(kepano/obsidian-skills obsidian-markdown 규칙에서 기계로 잴 수 있는 것만):
  heading-link / block-link  [[노트#헤딩]] · [[노트#^블록]] · [[#헤딩]] 대상이 실제로 있나
  callout-type               > [!타입] 이 Obsidian 기본 타입인가(사용자 CSS 콜아웃에도 경고가 뜬다 — 그땐 무시)
  callout-fold               접기 +/- 가 ] 바로 뒤가 아닌 곳에 있나
  comment-pair / highlight-pair   %% 짝(문서 전체) · 여는 == 의 짝(줄 단위 · 비교식 a==b 제외)
  tag-format                 frontmatter tags 항목에 공백 또는 맨 앞 # 이 있나

km_link_gate.py 를 대체하지 않는다 — 링크 게이트(노트 이름·MOC 링크)와 «함께» 돈다.
링크 게이트가 면제하는 MOC 도 여기서는 검사한다.
노트 자체가 없는 링크·이름이 겹치는 링크·.md 가 아닌 대상(.base 보기 등)은 건너뛴다.

exit 0 = 검사함(경고가 있어도 0 · 저장을 막지 않는다) / 1 = --strict 이고 경고 1건 이상
exit 2 = 측정 불가(vault·노트 없음 · 읽을 수 없는 노트 — 끊긴 심링크·권한) — 통과 취급 ❌, 사유를 표시하고 저장은 계속한다.
표준 라이브러리만 사용한다.
"""
import argparse
import fnmatch
import json
import os
import re
import sys

DEFAULT_EXCLUDE = "_meta/*,templates/*"
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules"}
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
LINK_RE = re.compile(r"!?\[\[([^\]]+?)\]\]")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
HIGHLIGHT_SPAN_RE = re.compile(r"(?<!=)==(?=[^\s=])(.+?)(?<=[^\s=])==(?!=)")
BLOCK_ID_RE =re.compile(r"(?:^|\s)\^([A-Za-z0-9-]+)\s*$")
CALLOUT_RE = re.compile(r"^\s*(?:>\s*)+(.*)$")
# Obsidian 기본 콜아웃 타입 + 별칭 (https://help.obsidian.md/callouts)
CALLOUT_TYPES = {
    "note", "abstract", "summary", "tldr", "info", "todo", "tip", "hint",
    "important", "success", "check", "done", "question", "help", "faq",
    "warning", "caution", "attention", "failure", "fail", "missing",
    "danger", "error", "bug", "example", "quote", "cite",
}


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def split_frontmatter(lines):
    """(frontmatter 줄 목록, 본문 시작 인덱스)."""
    if not lines or lines[0].strip() != "---":
        return [], 0
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return lines[1:i], i + 1
    return [], 0


def body_lines(lines, start):
    """본문 줄을 (줄번호, 텍스트)로 — 코드펜스 안은 빼고 인라인 코드는 지운다."""
    out, fence = [], None
    for idx in range(start, len(lines)):
        line = lines[idx]
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
                continue
            out.append((idx + 1, INLINE_CODE_RE.sub("", line)))
        elif m and m.group(1) == fence:
            fence = None
    return out


def norm_heading(text):
    """헤딩 비교용: 강조·코드 표시 지우고 공백 하나로, 대소문자 무시."""
    t = re.sub(r"[*_`~=]", "", text)
    t = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def anchors(text):
    """노트의 (헤딩 집합, 블록 id 집합)."""
    lines = text.splitlines()
    _, start = split_frontmatter(lines)
    heads, blocks, fence = set(), set(), None
    for line in lines[start:]:
        m = FENCE_RE.match(line)
        if fence is None and m:
            fence = m.group(1)
            continue
        if fence is not None:
            if m and m.group(1) == fence:
                fence = None
            continue
        h = HEADING_RE.match(line)
        if h:
            heads.add(norm_heading(h.group(2)))
        b = BLOCK_ID_RE.search(line)
        if b:
            blocks.add(b.group(1))
    return heads, blocks


def parse_tags(fm_lines):
    """frontmatter tags 값을 (원문 문자열, frontmatter 안 줄 인덱스) 목록으로. 흐름 [a, b]·블록 - a·한 줄 a 모두."""
    out, in_tags = [], False
    for idx, line in enumerate(fm_lines):
        m = re.match(r"^tags:\s*(.*?)\s*$", line, re.I)
        if m:
            val = m.group(1)
            in_tags = val == ""
            if val.startswith("[") and val.endswith("]"):
                out += [(x.strip().strip("\"'"), idx) for x in val[1:-1].split(",") if x.strip()]
            elif val:
                out.append((val.strip("\"'"), idx))
            continue
        if in_tags:
            m = re.match(r"^\s*-\s*(.*?)\s*$", line)
            if m:
                out.append((m.group(1).strip("\"'"), idx))
                continue
            in_tags = False
    return out


def scan_md(vault):
    rels = []
    for root, dirs, names in os.walk(vault):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in names:
            if name.lower().endswith(".md"):
                rels.append(os.path.relpath(os.path.join(root, name), vault).replace(os.sep, "/"))
    return sorted(rels)


class Vault:
    def __init__(self, root, all_md):
        self.root = root
        self.index = {}
        for rel in all_md:
            self.index.setdefault(os.path.basename(rel)[:-3].lower(), []).append(rel)
        self._anchors = {}

    def resolve(self, target):
        """이름 → vault 상대경로 1건. 없음·모호·md 아님 = None."""
        name = os.path.basename(target.strip())
        low = name.lower()
        if "." in name and not low.endswith(".md"):
            return None  # .base·.canvas·이미지 등 — 헤딩 개념이 다르다
        if low.endswith(".md"):
            low = low[:-3]
        hits = self.index.get(low, [])
        return hits[0] if len(hits) == 1 else None

    def anchors_of(self, rel):
        if rel not in self._anchors:
            self._anchors[rel] = anchors(read_text(os.path.join(self.root, rel)))
        return self._anchors[rel]


def lint_note(vault, rel):
    text = read_text(os.path.join(vault.root, rel))
    lines = text.splitlines()
    fm, start = split_frontmatter(lines)
    body = body_lines(lines, start)
    warns = []

    def warn(line, check, detail):
        warns.append({"note": rel, "line": line, "check": check, "detail": detail})

    # ① 헤딩·블록 링크
    for ln, line in body:
        for m in LINK_RE.finditer(line):
            # 표 안 별칭은 [[노트#헤딩\|별칭]] 로 탈출한다 — 꼬리 \ 는 헤딩 이름이 아니다
            inner = m.group(1).split("|", 1)[0].rstrip("\\")
            if "#" not in inner:
                continue
            name, frag = inner.split("#", 1)
            target = rel if not name.strip() else vault.resolve(name)
            if target is None:
                continue
            heads, blocks = vault.anchors_of(target)
            if frag.startswith("^"):
                if frag[1:].strip() not in blocks:
                    warn(ln, "block-link", "[[%s]] — 블록 ^%s 없음" % (inner, frag[1:].strip()))
                continue
            last = frag.split("#")[-1]
            if norm_heading(last) not in heads:
                warn(ln, "heading-link", "[[%s]] — 헤딩 «%s» 없음" % (inner, last.strip()))

    # ② 콜아웃 타입 · ③ 접기 위치
    for ln, line in body:
        m = CALLOUT_RE.match(line)
        if not m:
            continue
        rest = m.group(1)
        if re.match(r"^[+-]\s*\[!", rest):
            warn(ln, "callout-fold", "접기 표시가 [! 앞에 있음 — `> [!타입]-` 꼴로")
            continue
        c = re.match(r"^\[!([^\]]*)\]", rest)
        if not c:
            continue
        raw = c.group(1)
        if re.search(r"[+-]", raw):
            warn(ln, "callout-fold", "접기 표시 «%s» 가 [! ] 안에 있음 — `> [!타입]-` 꼴로" % raw)
            continue
        if raw.strip().lower() not in CALLOUT_TYPES:
            warn(ln, "callout-type", "콜아웃 타입 «%s» 는 기본 타입이 아님(오타? · 사용자 CSS 콜아웃이면 무시)" % raw.strip())

    # ④ %% 짝 — 여러 줄에 걸칠 수 있어 문서 전체로 센다
    marks = [(ln, line.count("%%")) for ln, line in body if "%%" in line]
    if sum(n for _, n in marks) % 2:
        warn(marks[-1][0], "comment-pair", "%% 개수가 홀수 — 닫히지 않은 주석")
    # ④ == 짝 — 줄 단위. 짝 맞은 강조(==글자…글자==, 뒤에 조사·문장부호가 붙어도)를 먼저 지우고,
    #   남은 == 중 «여는 꼴»(앞이 줄 처음·공백, 뒤가 공백 아님)만 닫히지 않은 강조로 본다.
    #   ` == `(뒤 공백)·`a==b`·`requests==1.0`·`f(x)==2`·`a[:3]==b`(앞이 글자·괄호) 는 비교식이라 세지 않는다.
    for ln, line in body:
        rest = HIGHLIGHT_SPAN_RE.sub("", line)
        n = 0
        for m in re.finditer(r"(?<!=)==(?!=)", rest):
            before = rest[m.start() - 1] if m.start() > 0 else " "
            after = rest[m.end()] if m.end() < len(rest) else " "
            if before.isspace() and not after.isspace():
                n += 1
        if n:
            warn(ln, "highlight-pair", "여는 == 에 짝이 없음 — 닫히지 않은 강조(비교식이면 무시)")

    # ⑤ tags
    for tag, idx in parse_tags(fm):
        if tag.startswith("#") or re.search(r"\s", tag):
            warn(idx + 2, "tag-format", "tags 항목 «%s» — 공백·맨 앞 # 은 태그가 깨짐" % tag)
    return warns


def die_unmeasurable(msg):
    sys.stderr.write("측정 불가: %s - exit 2 는 통과 취급 ❌ (경고 모드라 저장은 계속)\n" % msg)
    return 2


def main(argv=None):
    ap = argparse.ArgumentParser(description="OFM 경고 검사 5종 (exit 0 경고 모드 / --strict 1 / 측정 불가 2)")
    ap.add_argument("vault", help="vault 루트 경로")
    ap.add_argument("--notes", default="", help="검사할 노트(vault 상대경로) 쉼표 목록")
    ap.add_argument("--exclude", default=None,
                    help="전체 스캔 제외 글롭(기본 %s · '' 로 해제)" % DEFAULT_EXCLUDE)
    ap.add_argument("--json", action="store_true", help="JSON 만 출력")
    ap.add_argument("--strict", action="store_true", help="경고가 있으면 exit 1")
    args = ap.parse_args(argv)

    root = os.path.abspath(os.path.expanduser(args.vault))
    if not os.path.isdir(root):
        return die_unmeasurable("vault 없음 %s" % root)
    all_md = scan_md(root)
    if not all_md:
        return die_unmeasurable("md 0건 %s" % root)
    raw_exclude = DEFAULT_EXCLUDE if args.exclude is None else args.exclude
    globs = [g.strip() for g in raw_exclude.split(",") if g.strip()]
    if args.notes.strip():
        targets = [n.strip().replace(os.sep, "/") for n in args.notes.split(",") if n.strip()]
        missing = [n for n in targets if n not in all_md]
        if missing:
            return die_unmeasurable("노트 없음 %s" % ",".join(missing))
    else:
        targets = [r for r in all_md if not any(fnmatch.fnmatch(r, g) for g in globs)]
    if not targets:
        return die_unmeasurable("검사 대상 0건 %s" % root)

    vault = Vault(root, all_md)
    warnings = []
    for rel in targets:
        # 검사 노트나 그 링크 대상이 끊긴 심링크·읽기 권한 없음·(--notes 로 지정한) .md 이름 폴더면
        # 경고 모드라도 traceback·exit 1 ❌ → 측정 불가(2). 전체 스캔은 파일만 모으므로 .md 이름 폴더는 애초에 안 들어온다.
        try:
            warnings += lint_note(vault, rel)
        except OSError as exc:
            return die_unmeasurable("%s 검사 중 파일을 읽을 수 없음 (%s)" % (rel, exc))
    payload = {"mode": "strict" if args.strict else "warn", "checked": len(targets),
               "warnings": warnings}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for w in warnings:
            print("%s:%d  %-14s  %s" % (w["note"], w["line"], w["check"], w["detail"]))
        print("checked=%d warnings=%d mode=%s" % (len(targets), len(warnings), payload["mode"]))
    return 1 if (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
