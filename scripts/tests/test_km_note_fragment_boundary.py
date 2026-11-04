#!/usr/bin/env python3
"""test_km_note_fragment_boundary.py — the note fragment is the first 2,500 characters, and a link
that ends one character before that boundary must come back whole.

Why: a real /km:search case found its answer (a URL) at characters 2,431-2,499 of the note — one
character inside the 2,500-character fragment. The success depends on that fixed budget. If the
budget shrinks, or the guard starts cutting earlier, this test fails instead of the answer silently
disappearing. Synthetic fixture only (placeholder host under .invalid); no network.

Cells:
  B01 constants     — scripts/km_search_guard.py MAX_CHARS = 2500 · km_note_caller.sh asks max_chars=2500
  B02 local-inside  — URL at chars 2,431-2,499 (0-based) → `local` returns the whole URL · truncated=true
  B03 local-cut     — same body shifted by one character (URL ends at 2,500) → whole URL absent, all but
                      its last character present (the boundary bites exactly there)
  B04 remote-inside — same check through `remote` (server payload JSON on stdin)
  B05 remote-cut    — shifted payload through `remote` → whole URL absent
  B06 caller-same   — km_note_caller.sh same-mode → whole URL present
  B07 decoy         — a string that is NOT in the body is reported absent (ZZQXFRAGDECOY = 0)
Standard library only.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GUARD = os.path.join(REPO, "scripts", "km_search_guard.py")
CALLER = os.path.join(REPO, "scripts", "km_note_caller.sh")
BUDGET = 2500
START = 2431          # first character of the URL (0-based)
END = 2499            # last character of the URL (0-based) — one before the boundary
URL_HEAD = "https://boundary-fixture.example.invalid/notes/"
URL = URL_HEAD + "x" * ((END - START + 1) - len(URL_HEAD))
assert len(URL) == END - START + 1, len(URL)
NOTE = "maps/fragment-boundary.md"

results = []


def check(cell, ok, detail=""):
    results.append((cell, bool(ok)))
    print(("PASS" if ok else "FAIL"), cell, detail)


def body_with_url(shift):
    head = "a" * (START + shift)
    tail = "\n" + "b" * 600 + "\n"
    body = head + URL + tail
    assert body.index(URL) == START + shift
    return body


def guard(*args, stdin=None):
    out = subprocess.run([sys.executable, "-I", "-B", GUARD, *args], input=stdin,
                         capture_output=True, text=True, timeout=30)
    return out.returncode, json.loads(out.stdout)


def write_vault(root, body):
    os.makedirs(os.path.join(root, "maps"), exist_ok=True)
    with open(os.path.join(root, NOTE), "w", encoding="utf-8") as fh:
        fh.write(body)


guard_src = open(GUARD, encoding="utf-8").read()
caller_src = open(CALLER, encoding="utf-8").read()
check("B01-constants",
      re.search(r"^MAX_CHARS = 2500$", guard_src, re.M) and caller_src.count("max_chars=2500") == 1,
      "MAX_CHARS=2500 · caller max_chars=2500")

with tempfile.TemporaryDirectory() as tmp:
    inside = os.path.join(tmp, "inside")
    cut = os.path.join(tmp, "cut")
    write_vault(inside, body_with_url(0))
    write_vault(cut, body_with_url(1))

    rc, data = guard("local", "--root", inside, "--expected", NOTE)
    check("B02-local-inside",
          rc == 0 and data.get("status") == "verified" and len(data["body"]) == BUDGET
          and URL in data["body"] and data["body"].index(URL) + len(URL) - 1 == END
          and data.get("truncated") is True,
          f"rc={rc} len={len(data.get('body', ''))}")

    rc, data = guard("local", "--root", cut, "--expected", NOTE)
    check("B03-local-cut",
          rc == 0 and URL not in data["body"] and data["body"].endswith(URL[:-1]),
          f"rc={rc} whole_url_present={URL in data.get('body', '')}")

    for cell, shift in (("B04-remote-inside", 0), ("B05-remote-cut", 1)):
        payload = json.dumps({"note_path": NOTE, "body": body_with_url(shift)})
        rc, data = guard("remote", "--expected", NOTE, stdin=payload)
        want = shift == 0
        check(cell, rc == 0 and (URL in data["body"]) is want,
              f"rc={rc} whole_url_present={URL in data.get('body', '')}")

    out = subprocess.run(["bash", CALLER, "same", inside, NOTE, "fragment-boundary", ""],
                         capture_output=True, text=True, timeout=30)
    data = json.loads(out.stdout)
    check("B06-caller-same", out.returncode == 0 and URL in data.get("body", ""),
          f"rc={out.returncode}")
    check("B07-decoy", data.get("body", "").count("ZZQXFRAGDECOY") == 0, "ZZQXFRAGDECOY=0")

failed = [c for c, ok in results if not ok]
print(f"cells={len(results)} pass={len(results) - len(failed)} fail={len(failed)}")
sys.exit(1 if failed or len(results) != 7 else 0)
