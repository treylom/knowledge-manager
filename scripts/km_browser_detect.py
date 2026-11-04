#!/usr/bin/env python3
"""km browser auto-detect — pick the browser km uses when a page needs a real browser.

Order (first one that is installed AND answers wins):
  1. ego lite   — `ego-browser` CLI (`ego-browser skill` prints a guide ending in "end of guide")
  2. Aside      — `aside` CLI (`aside --version` exits 0)
  3. fallback   — the existing chain (playwright-cli → Playwright MCP → WebFetch)

The user does not configure anything: km runs this once per task and uses the printed
absolute path, so it works even when the CLI's folder (~/.local/bin) is not on PATH.

`--prefer` carries `browser.provider` from km-config.json:
  - "ego" / "aside"            → used first when it is detected; otherwise the auto order.
  - "hyperbrowser"/"antigravity" → explicit opt-in (needs its own key/app) → returned as-is.
  - "auto" / "playwright" / ""  → auto order. ("playwright" and "aside" were the template
    defaults of older versions, so they are not treated as a deliberate choice that blocks
    ego lite; an installed, answering preferred CLI still wins.)

Output: one JSON line on stdout. `--get provider|bin` prints one field instead.
Exit code: 0 (a decision is always printed) · 2 = bad arguments.
Standard library only. Windows: PATH lookup only (PATHEXT via shutil.which) — fixed
install folders below are macOS/Linux; Windows folders are not measured yet.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

ORDER = ("ego", "aside")
EXPLICIT_PASSTHROUGH = ("hyperbrowser", "antigravity")

# names searched on PATH, then fixed install folders (relative to the home folder)
CANDIDATES = {
    "ego": {
        "names": ("ego-browser",),
        "paths": (
            ".local/bin/ego-browser",
            ".local/share/ego/active_version_dir/Helpers/ego-browser",
        ),
    },
    "aside": {
        "names": ("aside", "aside.exe"),
        "paths": (
            ".local/bin/aside",
            ".aside/cli/Aside CLI.app/Contents/MacOS/aside",
            ".aside/bin/aside",
        ),
    },
}


def _timeout() -> float:
    try:
        return max(0.5, float(os.environ.get("KM_BROWSER_PROBE_TIMEOUT", "15")))
    except ValueError:
        return 15.0


def find_bin(kind: str, home: str, path: str | None) -> str | None:
    spec = CANDIDATES[kind]
    for name in spec["names"]:
        hit = shutil.which(name, path=path)
        if hit:
            return os.path.abspath(hit)
    for rel in spec["paths"]:
        cand = os.path.join(home, rel)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return os.path.abspath(cand)
    return None


def probe(kind: str, binpath: str) -> tuple[bool, str]:
    """True when the CLI answers. Never hangs longer than the probe timeout."""
    args = [binpath, "skill"] if kind == "ego" else [binpath, "--version"]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=_timeout(),
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return False, "probe timeout"
    except OSError as e:
        return False, f"probe failed: {e.__class__.__name__}"
    if r.returncode != 0:
        return False, f"probe exit {r.returncode}"
    if kind == "ego" and "end of guide" not in (r.stdout or ""):
        return False, "guide incomplete"
    return True, "ok"


def detect(prefer: str = "auto", do_probe: bool = True, home: str | None = None,
           path: str | None = None) -> dict:
    home = home or os.path.expanduser("~")
    prefer = (prefer or "auto").strip().lower()
    found: dict[str, dict] = {}
    for kind in ORDER:
        b = find_bin(kind, home, path)
        ready, why = (False, "not installed")
        if b:
            ready, why = probe(kind, b) if do_probe else (True, "not probed")
        found[kind] = {"found": bool(b), "bin": b, "ready": ready, "why": why}

    if prefer in EXPLICIT_PASSTHROUGH:
        provider, reason = prefer, f"browser.provider={prefer} (explicit)"
    else:
        order = list(ORDER)
        if prefer in ORDER:
            order.remove(prefer)
            order.insert(0, prefer)
        provider, reason = "fallback", "no ego lite / Aside answered"
        for kind in order:
            if found[kind]["ready"]:
                provider = kind
                reason = ("preferred " if kind == prefer else "auto: ") + kind
                break

    return {
        "provider": provider,
        "bin": found.get(provider, {}).get("bin"),
        "reason": reason,
        "prefer": prefer,
        "order": ["ego", "aside", "fallback"],
        "detected": found,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prefer", default=os.environ.get("KM_BROWSER_PROVIDER", "auto"),
                    help="browser.provider from km-config.json (default auto)")
    ap.add_argument("--no-probe", action="store_true", help="skip the answer check")
    ap.add_argument("--get", choices=("provider", "bin", "reason"))
    a = ap.parse_args(argv)
    res = detect(prefer=a.prefer, do_probe=not a.no_probe)
    if a.get:
        print(res.get(a.get) or "")
    else:
        print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
