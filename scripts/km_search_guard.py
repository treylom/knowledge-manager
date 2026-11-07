"""Bounded map routing and path-bound note evidence. No network transport."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

MAX_BYTES = 262144
MAX_CHARS = 2500
AWK = r'''
    BEGIN { m = split(tolower(kws), T, " "); for (i = 1; i <= m; i++) if (!(T[i] in U)) { U[T[i]] = 1; K[++n] = T[i] } }
    { l = tolower($0); s = $0
      while (match(s, /\[\[[^]|#]*/)) { h = substr(s, RSTART + 2, RLENGTH - 2); s = substr(s, RSTART + RLENGTH)
        if (!(h in F)) F[h] = NR
        for (i = 1; i <= n; i++) if (index(l, K[i])) M[h SUBSEP i] = 1 } }
    END { for (h in F) { c = 0; for (i = 1; i <= n; i++) if ((h SUBSEP i) in M) c++; if (c) printf "%d\t%d\t%s\n", c, F[h], h } }'''


def unavailable(reason):
    return {"status": "unmeasured", "reason": reason, "body_available": False}


def relative_note(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid relative note")
    value = unicodedata.normalize("NFC", value)
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValueError("absolute note")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("noncanonical note")
    if not value.endswith(".md") or any(ord(c) < 32 for c in value):
        raise ValueError("invalid note name")
    return value


def verified_body(expected, payload):
    try:
        expected = relative_note(expected)
    except ValueError:
        return unavailable("invalid_source_note")
    if not isinstance(payload, dict):
        return unavailable("invalid_response")
    try:
        actual = relative_note(payload.get("note_path"))
    except ValueError:
        return unavailable("invalid_response_path")
    if actual != expected:
        return unavailable("path_mismatch")
    body = payload.get("body")
    if not isinstance(body, str) or not body:
        return unavailable("missing_body")
    delivered = body[:MAX_CHARS]
    return {"status": "verified", "source_note": expected,
            "body_available": True, "body": delivered,
            "body_sha256": hashlib.sha256(delivered.encode()).hexdigest(),
            "truncated": len(body) > MAX_CHARS or payload.get("truncated") is True}


def other_note(expected, entity, transport):
    """The caller validates before the single injected transport attempt."""
    try:
        relative_note(expected)
    except ValueError:
        return unavailable("invalid_source_note")
    if not isinstance(entity, str) or not entity or "/" in entity or "\\" in entity:
        return unavailable("invalid_entity")
    try:
        payload = transport(entity, max_chars=MAX_CHARS,
                            connect_timeout=3, total_timeout=15)
    except Exception:
        return unavailable("note_request_failed")
    return verified_body(expected, payload)


def no_follow_open_supported():
    """Same-vault reads open every folder and the file without following symlinks.
    That needs os.O_NOFOLLOW, os.O_DIRECTORY and dir_fd support for os.open — not on Windows Python."""
    return (hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")
            and os.open in getattr(os, "supports_dir_fd", ()))


def local_note(root, expected):
    try:
        relative = relative_note(expected)
    except ValueError:
        return unavailable("invalid_source_note")
    if not no_follow_open_supported():
        return unavailable("local_read_unsupported")
    descriptors = []
    try:
        directory = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptors.append(os.open(root, directory))
        parts = relative.split("/")
        for part in parts[:-1]:
            descriptors.append(os.open(part, directory, dir_fd=descriptors[-1]))
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW,
                     dir_fd=descriptors[-1])
        with os.fdopen(fd, "rb") as source:
            raw = source.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return unavailable("note_too_large")
        return verified_body(relative, {"note_path": relative,
                                       "body": raw.decode("utf-8-sig")})
    except (OSError, UnicodeError, AttributeError, NotImplementedError):
        return unavailable("local_read_failed")
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def unique_keywords(keywords):
    """Same split and de-duplication as the awk block (lowercase, single spaces)."""
    seen = []
    for word in ascii_lower(keywords).split():
        if word not in seen:
            seen.append(word)
    return seen


def ascii_lower(value):
    # awk tolower() only folds ASCII letters; keep the same rule so scores match.
    return "".join(c.lower() if c.isascii() else c for c in value)


def ambiguity(rows, keyword_count):
    """Route signals already in the output: no hub hit, no hub carrying every
    keyword, or more hubs tied at the 3rd score than the 3 slots can hold."""
    reasons = []
    if not rows:
        reasons.append("no_match")
    else:
        if rows[0][0] < keyword_count:
            reasons.append("partial_match")
        if len(rows) > 3 and rows[3][0] == rows[2][0]:
            reasons.append("tie_at_cut")
    return reasons


def map_routes(path, keywords, runner=None):
    runner = runner or subprocess.run
    try:
        raw = Path(path).read_bytes()
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeError):
        return {"status": "unmeasured", "reason": "map_read_failed", "hub_count": None}
    try:
        result = runner(["/usr/bin/awk", "-v", "kws=" + keywords, AWK],
                        input=text, text=True, capture_output=True, timeout=10)
        if result.returncode:
            return {"status": "unmeasured", "reason": "awk_failed", "hub_count": None}
        ordered = runner(["/usr/bin/sort", "-t", "\t", "-k1,1nr", "-k2,2n"],
                         input=result.stdout, text=True, capture_output=True, timeout=10)
        if ordered.returncode:
            return {"status": "unmeasured", "reason": "sort_failed", "hub_count": None}
        rows = []
        for row in ordered.stdout.splitlines():
            score, line, target = row.split("\t", 2)
            rows.append((int(score), int(line), target))
        hubs = [{"path": target, "score": score, "line": line}
                for score, line, target in rows[:3]]
    except (OSError, subprocess.SubprocessError, ValueError):
        return {"status": "unmeasured", "reason": "route_execution_failed", "hub_count": None}
    lines = text.splitlines()
    evidence_lines = sorted({i for hub in hubs
                             for i in range(max(1, hub["line"] - 2),
                                            min(len(lines), hub["line"] + 2) + 1)})[:130]
    reasons = ambiguity(rows, len([k for k in unique_keywords(keywords) if k]))
    return {"status": "ok", "hub_count": len(hubs), "hubs": hubs,
            "map_sha256": hashlib.sha256(raw).hexdigest(),
            "map_lines_scanned": len(lines),
            "evidence": [{"line": i, "text": lines[i - 1]} for i in evidence_lines],
            "evidence_lines": len(evidence_lines),
            "candidates_total": len(rows),
            "ambiguous": bool(reasons), "ambiguity": reasons}


# ── map descent menus (1.8.10) ─────────────────────────────────────────────
# The running model reads these bounded menus and chooses; this script never
# calls a model. A menu item = one hub line of the map: name, folder hint, the
# one-line description the map generator wrote.
HUB_LINE = re.compile(r"^\s*- \[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\](.*)$")
DESC_MAX = 160
MENU_MAX = 60
OUTLINK_MAX = 40
WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def map_note_path(target, map_dir="000-START-HERE"):
    """Map link target (relative to the map folder, no .md) → vault-relative note path."""
    target = unicodedata.normalize("NFC", target.strip())
    # "../x" and "./x" are relative to the map folder; "a/b" is from the vault root;
    # a bare name is a sibling of the map (how the map generator writes them).
    if target.startswith(("../", "./")) or "/" not in target:
        joined = map_dir + "/" + target
    else:
        joined = target
    parts = []
    for part in joined.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise ValueError("escapes vault")
            parts.pop()
        else:
            parts.append(part)
    note = "/".join(parts)
    if not note.endswith(".md"):
        note += ".md"
    return relative_note(note)


def parse_map(text):
    """First line per hub target, in map order."""
    hubs, seen = [], set()
    for number, line in enumerate(text.splitlines(), 1):
        match = HUB_LINE.match(line)
        if not match:
            continue
        target = match.group(1).strip()
        if target in seen:
            continue
        seen.add(target)
        rest = match.group(3)
        folder = re.search(r"`([^`]+)`", rest)
        desc = re.sub(r"\s+", " ", re.sub(r"`[^`]*`", "", rest)).strip(" ·—-")
        name = target.rsplit("/", 1)[-1]
        inbound = re.search(r"(\d+)↙", rest)
        hubs.append({"line": number, "target": target, "name": name,
                     "title": (match.group(2) or name).strip(),
                     "folder": folder.group(1) if folder else "",
                     "inbound": int(inbound.group(1)) if inbound else 0,
                     "desc": desc[:DESC_MAX]})
    return hubs


def keyword_rows(text, keywords):
    """Python twin of the awk score: hub → number of keywords on any line that links it."""
    words = [k for k in unique_keywords(keywords) if k]
    first, hits = {}, {}
    for number, line in enumerate(text.splitlines(), 1):
        low = ascii_lower(line)
        for target in re.findall(r"\[\[([^\]|#]*)", line):
            first.setdefault(target, number)
            for i, word in enumerate(words):
                if word in low:
                    hits.setdefault(target, set()).add(i)
    rows = [(len(hits[t]), first[t], t) for t in hits]
    return sorted(rows, key=lambda r: (-r[0], r[1]))


def with_note(hub):
    item = dict(hub)
    try:
        item["note"] = map_note_path(hub["target"])
    except ValueError:
        item["note"] = None
    return item


def descent_menu(path, keywords, folder=None, limit=MENU_MAX):
    try:
        raw = Path(path).read_bytes()
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeError):
        return {"status": "unmeasured", "reason": "map_read_failed"}
    hubs = parse_map(text)
    by_target = {h["target"]: h for h in hubs}
    limit = max(1, min(int(limit), MENU_MAX))
    if folder:
        folder = unicodedata.normalize("NFC", folder.strip().strip("/"))
        inside = [h for h in hubs if h["folder"] == folder
                  or h["folder"].startswith(folder + "/")]
        depth = folder.count("/") + 1
        children = {}
        for h in inside:
            parts = h["folder"].split("/")
            if len(parts) > depth:
                key = "/".join(parts[:depth + 1])
                children[key] = children.get(key, 0) + 1
        # most-linked hubs first (the map's `M↙` count), then map order
        items = sorted(inside, key=lambda h: (-h["inbound"], h["line"]))[:limit]
        return {"status": "ok", "mode": "folder", "folder": folder,
                "map_sha256": hashlib.sha256(raw).hexdigest(),
                "hubs_total": len(inside), "truncated": len(inside) > limit,
                "items": [with_note(h) for h in items],
                "subfolders": [{"folder": k, "hubs": v}
                               for k, v in sorted(children.items(), key=lambda kv: -kv[1])]}
    rows = keyword_rows(text, keywords)
    items = [dict(by_target[t], score=s) for s, _, t in rows if t in by_target][:limit]
    tops = {}
    for h in hubs:
        top = h["folder"].split("/", 1)[0] if h["folder"] else "(no folder)"
        tops[top] = tops.get(top, 0) + 1
    return {"status": "ok", "mode": "keywords",
            "map_sha256": hashlib.sha256(raw).hexdigest(),
            "hubs_total": len(hubs), "matched_total": len(rows),
            "truncated": len(rows) > limit,
            "items": [with_note(h) for h in items],
            "folders": [{"folder": k, "hubs": v}
                        for k, v in sorted(tops.items(), key=lambda kv: -kv[1])]}


def read_nofollow(root, relative):
    """Whole note bytes (≤256KB) through the same no-follow open as local_note."""
    if not no_follow_open_supported():
        raise NotImplementedError("local_read_unsupported")
    descriptors = []
    try:
        directory = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptors.append(os.open(root, directory))
        parts = relative.split("/")
        for part in parts[:-1]:
            descriptors.append(os.open(part, directory, dir_fd=descriptors[-1]))
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=descriptors[-1])
        with os.fdopen(fd, "rb") as source:
            return source.read(MAX_BYTES + 1)
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def hub_outlinks(root, hub, limit=OUTLINK_MAX):
    """Links one hub note carries, in order, each with its line (≤160 chars)."""
    try:
        relative = relative_note(hub)
    except ValueError:
        return unavailable("invalid_source_note")
    if not no_follow_open_supported():
        return unavailable("local_read_unsupported")
    try:
        raw = read_nofollow(root, relative)
    except (OSError, NotImplementedError, AttributeError):
        return unavailable("local_read_failed")
    if len(raw) > MAX_BYTES:
        return unavailable("note_too_large")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError:
        return unavailable("local_read_failed")
    limit = max(1, min(int(limit), OUTLINK_MAX))
    links, seen = [], set()
    for number, line in enumerate(text.splitlines(), 1):
        for target in WIKILINK.findall(line):
            target = target.strip()
            if not target or target in seen:
                continue
            seen.add(target)
            links.append({"name": target.rsplit("/", 1)[-1], "target": target,
                          "line": number, "text": line.strip()[:DESC_MAX]})
    return {"status": "ok", "hub": relative, "body_available": False,
            "links_total": len(links), "truncated": len(links) > limit,
            "links": links[:limit]}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    route = sub.add_parser("route")
    route.add_argument("--map", required=True)
    route.add_argument("--keywords", required=True)
    local = sub.add_parser("local")
    local.add_argument("--root", required=True)
    local.add_argument("--expected", required=True)
    remote = sub.add_parser("remote")
    remote.add_argument("--expected", required=True)
    check = sub.add_parser("check")
    check.add_argument("--expected", required=True)
    menu = sub.add_parser("menu")
    menu.add_argument("--map", required=True)
    menu.add_argument("--keywords", default="")
    menu.add_argument("--folder")
    menu.add_argument("--limit", type=int, default=MENU_MAX)
    links = sub.add_parser("outlinks")
    links.add_argument("--root", required=True)
    links.add_argument("--hub", required=True)
    links.add_argument("--limit", type=int, default=OUTLINK_MAX)
    args = parser.parse_args()
    if args.mode == "route":
        result = map_routes(args.map, args.keywords)
    elif args.mode == "menu":
        result = descent_menu(args.map, args.keywords, args.folder, args.limit)
    elif args.mode == "outlinks":
        result = hub_outlinks(args.root, args.hub, args.limit)
    elif args.mode == "local":
        result = local_note(args.root, args.expected)
    else:
        try:
            relative = relative_note(args.expected)
            if args.mode == "check":
                result = {"status": "verified", "source_note": relative}
            else:
                raw = sys.stdin.buffer.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    result = unavailable("response_too_large")
                else:
                    result = verified_body(relative, json.loads(raw))
        except (ValueError, UnicodeError):
            result = unavailable("invalid_input")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in ("verified", "ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
