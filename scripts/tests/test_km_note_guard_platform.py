#!/usr/bin/env python3
"""test_km_note_guard_platform.py — same-vault note reads stop safely where Python cannot open
without following symlinks.

km_search_guard.local_note opens the vault folder, each sub-folder and the note with
os.O_NOFOLLOW / os.O_DIRECTORY and dir_fd. Windows Python has none of these. There the read must end
as «원문 미확보» (status unmeasured · CLI exit 3) instead of crashing — and the path checks must not be
loosened (no fallback to a plain open()).

Cells (each one imports a fresh copy of the guard and patches the os module, then restores it):
  P01 native          — this machine: the note is read (verified · CLI exit 0)
  W01 no-O_NOFOLLOW   — os.O_NOFOLLOW removed → unmeasured/local_read_unsupported · CLI exit 3
  W02 no-O_DIRECTORY  — os.O_DIRECTORY removed → same
  W03 no-dir_fd       — os.supports_dir_fd without os.open → same
  W04 open-raises     — attributes present but os.open raises NotImplementedError → unmeasured/local_read_failed
  W05 resolver-follow — km_wikilink_resolver.follow on a W01 machine → map_not_verified (no crash, no read)
  W06 no-plain-open   — on W01, builtins.open is never called on the note path (no weaker fallback)
Standard library only.
"""
import builtins
import contextlib
import importlib.util
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(REPO, "scripts")
NOTE = "maps/platform.md"
results = []


def check(cell, ok, detail=""):
    results.append((cell, bool(ok)))
    print(("PASS" if ok else "FAIL"), cell, detail)


def load(name):
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    for mod in ("km_search_guard", "km_wikilink_resolver"):
        sys.modules.pop(mod, None)
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@contextlib.contextmanager
def patched(remove=(), supports=None, open_raises=None):
    saved = {k: getattr(os, k) for k in remove if hasattr(os, k)}
    saved_supports, saved_open = os.supports_dir_fd, os.open
    try:
        for k in remove:
            if hasattr(os, k):
                delattr(os, k)
        if supports is not None:
            os.supports_dir_fd = supports
        if open_raises is not None:
            def boom(*a, **k):
                raise open_raises("simulated")
            os.open = boom
            os.supports_dir_fd = set(saved_supports) | {boom}  # capability declared, the call itself fails
        yield
    finally:
        for k, v in saved.items():
            setattr(os, k, v)
        os.supports_dir_fd, os.open = saved_supports, saved_open


def cli(guard, root):
    argv, out = sys.argv, io.StringIO()
    sys.argv = ["km_search_guard.py", "local", "--root", root, "--expected", NOTE]
    try:
        with contextlib.redirect_stdout(out):
            rc = guard.main()
    finally:
        sys.argv = argv
    return rc, out.getvalue()


with tempfile.TemporaryDirectory() as root:
    os.makedirs(os.path.join(root, "maps"))
    with open(os.path.join(root, NOTE), "w", encoding="utf-8") as fh:
        fh.write("# platform\n[[platform]]\nbody\n")

    g = load("km_search_guard")
    data = g.local_note(root, NOTE)
    rc, _ = cli(g, root)
    check("P01-native", data.get("status") == "verified" and rc == 0, f"status={data.get('status')} rc={rc}")

    for cell, kw in (("W01-no-O_NOFOLLOW", {"remove": ("O_NOFOLLOW",)}),
                     ("W02-no-O_DIRECTORY", {"remove": ("O_DIRECTORY",)}),
                     ("W03-no-dir_fd", {"supports": set()})):
        with patched(**kw):
            g = load("km_search_guard")
            try:
                data = g.local_note(root, NOTE)
                rc, out = cli(g, root)
                ok = (data == {"status": "unmeasured", "reason": "local_read_unsupported", "body_available": False}
                      and rc == 3 and '"local_read_unsupported"' in out)
                detail = f"reason={data.get('reason')} rc={rc}"
            except Exception as exc:  # a crash is the bug this test guards against
                ok, detail = False, f"raised {type(exc).__name__}"
        check(cell, ok, detail)

    with patched(open_raises=NotImplementedError):
        g = load("km_search_guard")
        try:
            data = g.local_note(root, NOTE)
            ok, detail = data.get("reason") == "local_read_failed" and data.get("status") == "unmeasured", f"reason={data.get('reason')}"
        except Exception as exc:
            ok, detail = False, f"raised {type(exc).__name__}"
    check("W04-open-raises", ok, detail)

    with patched(remove=("O_NOFOLLOW",)):
        g = load("km_search_guard")
        r = load("km_wikilink_resolver")
        opened = []
        real_open = builtins.open

        def spy(file, *a, **k):
            opened.append(str(file))
            return real_open(file, *a, **k)
        builtins.open = spy
        try:
            try:
                data = r.follow("same", root, NOTE, "platform",
                                inventory_builder=lambda _root: {"paths": [NOTE], "complete": True})
                ok, detail = data.get("reason") == "map_not_verified", f"reason={data.get('reason')}"
            except Exception as exc:
                ok, detail = False, f"raised {type(exc).__name__}"
        finally:
            builtins.open = real_open
    check("W05-resolver-follow", ok, detail)
    check("W06-no-plain-open", not any(p.endswith("platform.md") for p in opened), f"opened={len(opened)}")

failed = [c for c, ok in results if not ok]
print(f"cells={len(results)} pass={len(results) - len(failed)} fail={len(failed)}")
sys.exit(1 if failed or len(results) != 7 else 0)
