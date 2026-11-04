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
        hubs = []
        for row in ordered.stdout.splitlines()[:3]:
            score, line, target = row.split("\t", 2)
            hubs.append({"path": target, "score": int(score), "line": int(line)})
    except (OSError, subprocess.SubprocessError, ValueError):
        return {"status": "unmeasured", "reason": "route_execution_failed", "hub_count": None}
    lines = text.splitlines()
    evidence_lines = sorted({i for hub in hubs
                             for i in range(max(1, hub["line"] - 2),
                                            min(len(lines), hub["line"] + 2) + 1)})[:130]
    return {"status": "ok", "hub_count": len(hubs), "hubs": hubs,
            "map_sha256": hashlib.sha256(raw).hexdigest(),
            "map_lines_scanned": len(lines),
            "evidence": [{"line": i, "text": lines[i - 1]} for i in evidence_lines],
            "evidence_lines": len(evidence_lines)}


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
    args = parser.parse_args()
    if args.mode == "route":
        result = map_routes(args.map, args.keywords)
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
