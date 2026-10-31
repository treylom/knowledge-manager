#!/usr/bin/env python3
"""seal_cells.py — external population + body authority for the /km:search shell contract suites.

The suites (test_search_tier0_mb.sh, test_search_graph_expansion.sh) only emit one
`@@CELL<TAB>PASS|FAIL<TAB><id>` line per cell. The verdict is taken here, from a manifest that lives
outside the suites (scripts/tests/cells.manifest):

  body <suite> <region> <sha256>   sha256 of every `# @cell <region>` slice of the suite (prelude included)
  id   <suite> <cell id>           the canonical cell population (zsh cells are dropped only when zsh is absent)
  tool <sha256>                    this checker

  check <suite> — fails (rc 1) when: the manifest seal does not match KM_TEST_MANIFEST_SEAL (or the seal is
                  required by KM_TEST_REQUIRE_SEAL=1 and missing) · a region is added, removed, renamed or its
                  bytes differ · a cell id is missing, extra or recorded twice · any cell FAILs · the suite rc != 0.
  seal          — rewrites the manifest from the current suites (needs bash and zsh, every cell PASS) and prints
                  its sha256.  That sha256 must be pinned OUTSIDE the repo copy (CI: repository variable
                  KM_TEST_MANIFEST_SEAL; reviewers: their own sealed record) — a copy that edits a cell and
                  reseals the manifest changes the manifest hash, which the pinned value then rejects.
Standard library only.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MANIFEST = os.path.join(HERE, "cells.manifest")
SUITES = ("scripts/tests/test_search_tier0_mb.sh", "scripts/tests/test_search_graph_expansion.sh")
MARK = re.compile(rb"^# @cell ([A-Za-z0-9._-]+)\n\Z")
CELL = re.compile(r"^@@CELL\t(PASS|FAIL)\t(.+)$")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def regions(path):
    """[(name, sha256)] in file order; the slice before the first marker is 'prelude'."""
    out, name, buf = [], "prelude", []
    with open(path, "rb") as f:
        for line in f.readlines():
            m = MARK.match(line)
            if m:
                out.append((name, sha(b"".join(buf))))
                name, buf = m.group(1).decode(), [line]
            else:
                buf.append(line)
    out.append((name, sha(b"".join(buf))))
    return out


def shells():
    return ["bash", "zsh"] if shutil.which("zsh") else ["bash"]


def run_suite(suite):
    p = subprocess.run(["bash", os.path.join(REPO, suite)], cwd=REPO, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    text = p.stdout.decode("utf-8", "replace")
    cells = []
    for line in text.splitlines():
        m = CELL.match(line)
        if m:
            cells.append((m.group(1), m.group(2)))
    told = re.findall(r"^shells=(.*)$", text, re.M)
    return p.returncode, cells, (told[-1].split() if told else None), text


def read_manifest():
    with open(MANIFEST, "rb") as f:
        raw = f.read()
    body, ids, tool = {}, {}, None
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        kind, rest = line.split(" ", 1)
        if kind == "body":
            suite, region, h = rest.split(" ")
            body.setdefault(suite, []).append((region, h))
        elif kind == "id":
            suite, cid = rest.split(" ", 1)
            ids.setdefault(suite, []).append(cid)
        elif kind == "tool":
            tool = rest.strip()
        else:
            raise ValueError("unknown manifest line: " + line)
    return raw, body, ids, tool


def check(suite):
    problems = []
    raw, body, ids, tool = read_manifest()
    pinned = os.environ.get("KM_TEST_MANIFEST_SEAL", "").strip()
    if pinned:
        if sha(raw) != pinned:
            problems.append("SEAL mismatch: manifest sha256 %s != pinned KM_TEST_MANIFEST_SEAL %s" % (sha(raw), pinned))
        else:
            print("SEAL ok: manifest sha256 = pinned value")
    elif os.environ.get("KM_TEST_REQUIRE_SEAL") == "1":
        problems.append("SEAL required (KM_TEST_REQUIRE_SEAL=1) but KM_TEST_MANIFEST_SEAL is empty")
    else:
        print("SEAL unpinned: manifest sha256 %s (pin it outside the repo copy to reject resealed copies)" % sha(raw))
    with open(os.path.abspath(__file__), "rb") as f:
        if tool != sha(f.read()):
            problems.append("TOOL hash differs from the manifest (seal_cells.py changed)")
    if suite not in body or suite not in ids:
        problems.append("suite not in manifest: " + suite)
        return report(suite, problems, 0, 0)
    got_regions = regions(os.path.join(REPO, suite))
    names = [n for n, _ in got_regions]
    for n in sorted({n for n in names if names.count(n) > 1}):
        problems.append("BODY region marker repeated: " + n)
    want_regions = body[suite]
    if [n for n, _ in want_regions] != names:
        problems.append("BODY region list differs: want %s got %s" % ([n for n, _ in want_regions], names))
    for (n, h) in got_regions:
        w = dict(want_regions).get(n)
        if w is not None and w != h:
            problems.append("BODY region changed: %s" % n)
    have = shells()
    for req in os.environ.get("KM_TEST_REQUIRE_SHELLS", "").split():
        if req not in have:
            problems.append("required shell missing: " + req)
    want_ids = [i for i in ids[suite] if "zsh" in have or not re.search(r"@zsh(\s|$)", i)]
    rc, cells, told, text = run_suite(suite)
    if told is not None and told != have:
        problems.append("suite reports shells=%s, checker found %s" % (" ".join(told), " ".join(have)))
    seen = [cid for _, cid in cells]
    dups = sorted({c for c in seen if seen.count(c) > 1})
    for c in dups:
        problems.append("ID recorded more than once: " + c)
    for c in sorted(set(want_ids) - set(seen)):
        problems.append("ID missing: " + c)
    for c in sorted(set(seen) - set(want_ids)):
        problems.append("ID not in manifest: " + c)
    for st, c in cells:
        if st != "PASS":
            problems.append("CELL failed: " + c)
    if rc != 0:
        problems.append("suite rc %d" % rc)
    print("cells recorded %d · manifest %d (shells=%s) · regions %d" % (len(seen), len(want_ids), " ".join(have), len(names)))
    return report(suite, problems, len(set(seen) & set(want_ids)), len(want_ids))


def report(suite, problems, n_ok, n_want):
    for p in problems:
        print("FAIL " + p, file=sys.stderr)
    if problems:
        print("SEALED VERDICT %s: RED (%d problems)" % (suite, len(problems)))
        return 1
    print("SEALED VERDICT %s: exact %d/%d · bodies match · all PASS" % (suite, n_ok, n_want))
    return 0


def seal():
    if shells() != ["bash", "zsh"]:
        print("seal needs bash and zsh (the manifest holds both shells' cells)", file=sys.stderr)
        return 1
    lines = ["# km test cell manifest — canonical cell ids and region hashes. Do not edit by hand.",
             "# Regenerate: python3 scripts/tests/seal_cells.py seal · its sha256 is pinned outside the repo copy",
             "# (CI repository variable KM_TEST_MANIFEST_SEAL)."]
    with open(os.path.abspath(__file__), "rb") as f:
        lines.append("tool " + sha(f.read()))
    for suite in SUITES:
        rc, cells, _, text = run_suite(suite)
        seen = [c for _, c in cells]
        if rc != 0 or any(st != "PASS" for st, _ in cells) or len(seen) != len(set(seen)) or not seen:
            print("refusing to seal %s: rc=%d, every cell must PASS once" % (suite, rc), file=sys.stderr)
            return 1
        for n, h in regions(os.path.join(REPO, suite)):
            lines.append("body %s %s %s" % (suite, n, h))
        for c in seen:
            lines.append("id %s %s" % (suite, c))
    data = ("\n".join(lines) + "\n").encode("utf-8")
    with open(MANIFEST, "wb") as f:
        f.write(data)
    print("sealed %s sha256 %s" % (os.path.relpath(MANIFEST, REPO), sha(data)))
    return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "seal":
        return seal()
    if len(argv) == 3 and argv[1] == "check":
        return check(argv[2])
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
