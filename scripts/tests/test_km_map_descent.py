#!/usr/bin/env python3
"""test_km_map_descent.py — Phase 0.4 map descent (1.8.10): the keyword route stays as it was and
says when it is ambiguous; the descent menus the running model reads are bounded and stay in the vault.

Cells (fixture map + vault in a temp folder, CLI = scripts/km_search_guard.py):
  R01 route-unchanged   — old keys of `route` are exactly the 1.8.9 values (score, order, ≤3 hubs, evidence)
  R02 clear             — one hub carries every keyword, no tie at the cut → ambiguous false
  R03 no-match          — no hub line carries a keyword → ambiguous, reason no_match, exit 0
  R04 partial           — best hub carries fewer keywords than asked → partial_match
  R05 tie-at-cut        — 4th hub has the 3rd hub's score → tie_at_cut (awk order can't choose)
  R06 awk-twin          — python keyword_rows order == awk+sort order (same scores, same lines)
  M01 menu-keywords     — matched hubs first by score, each with title·folder·one-line desc·vault path
  M02 menu-limit        — limit caps items, truncated true, never above 60
  M03 menu-folder       — folder menu = hubs in that subtree, most-linked first, child folders counted
  M04 menu-path-escape  — a map link that climbs out of the vault gets note=null (not followed)
  O01 outlinks          — links of one hub note in order, each with its line, beyond the 2,500-char cut
  O02 outlinks-escape   — ../ or absolute hub path → unmeasured, exit 3
  O03 outlinks-symlink  — hub reached through a symlinked folder → unmeasured (no-follow open)
  O04 outlinks-limit    — limit caps links, truncated true
  C01 cli-exit          — route/menu exit 0 when ok, missing map → exit 3
  B01 block-bash/zsh    — the Phase 0.4-D block of commands/search.md, run as written: ambiguous → menu JSON;
                          clear → only the marker; other → no menu; target_status=ambiguous forces the menu
Standard library only.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GUARD = os.path.join(REPO, "scripts", "km_search_guard.py")
results = []


def check(cell, ok, detail=""):
    results.append((cell, bool(ok)))
    print(("PASS" if ok else "FAIL"), cell, detail)


def load():
    spec = importlib.util.spec_from_file_location("km_search_guard_t", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cli(*args):
    proc = subprocess.run([sys.executable, "-I", "-B", GUARD, *args], capture_output=True, text=True)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, {"raw": proc.stdout + proc.stderr}


MAP = """---
type: moc
---
# vault MOC 지도

## 핵심 허브
- [[../Library/Search/Search-MOC|검색 허브]] · `Library/Search` — reranker 와 벡터 검색 정리 · 링크 9↗ 40↙
- [[../Library/Prompt/Prompt-MOC|Prompt-MOC]] · `Library/Prompt` — 프롬프트 설계 원칙 · 링크 5↗ 12↙

## 전체 MOC 목록 (폴더순)
### Library (5)
- [[../Library/Search/Search-MOC|검색 허브]] · `Library/Search` — reranker 와 벡터 검색 정리 · 링크 9↗ 40↙
- [[../Library/Search/Vector-MOC|Vector-MOC]] · `Library/Search/Vector` — 임베딩 공간 노트 · 링크 3↗ 2↙
- [[../Library/Prompt/Prompt-MOC|Prompt-MOC]] · `Library/Prompt` — 프롬프트 설계 원칙 · 링크 5↗ 12↙
- [[../Library/Prompt/Agent-MOC|Agent-MOC]] · `Library/Prompt` — 에이전트 프롬프트 · 링크 2↗ 70↙
- [[../../outside/Escape-MOC|Escape-MOC]] · `outside` — 지도 밖으로 나가는 링크 · 링크 1↗ 1↙
### Projects (2)
- [[../Projects/Tie-MOC|Tie-MOC]] · `Projects` — 프롬프트 회의 · 링크 1↗ 1↙
- [[../Projects/Tie2-MOC|Tie2-MOC]] · `Projects` — 프롬프트 메모 · 링크 1↗ 1↙
"""

HUB_BODY = "# 검색 허브\n" + ("채움 글자 " * 400) + "\n" + "\n".join(
    f"- [[Note-{i:02d}|노트 {i}]] — 설명 {i}" for i in range(1, 51)) + "\n"


def build(root):
    os.makedirs(os.path.join(root, "000-START-HERE"))
    os.makedirs(os.path.join(root, "Library", "Search"))
    with open(os.path.join(root, "000-START-HERE", "MOC-Map.md"), "w", encoding="utf-8") as f:
        f.write(MAP)
    with open(os.path.join(root, "Library", "Search", "Search-MOC.md"), "w", encoding="utf-8") as f:
        f.write(HUB_BODY)
    real = os.path.join(root, "..", "real-elsewhere")
    os.makedirs(real, exist_ok=True)
    with open(os.path.join(real, "Linked-MOC.md"), "w", encoding="utf-8") as f:
        f.write("- [[Secret]]\n")
    os.symlink(os.path.abspath(real), os.path.join(root, "Library", "Linked"))


with tempfile.TemporaryDirectory() as tmp:
    root = os.path.join(tmp, "vault")
    os.makedirs(root)
    build(root)
    mpath = os.path.join(root, "000-START-HERE", "MOC-Map.md")
    g = load()

    # R01 — the 1.8.9 keys, recomputed by hand from the awk rule
    r = g.map_routes(mpath, "reranker 벡터")
    old_keys = {"status", "hub_count", "hubs", "map_sha256", "map_lines_scanned", "evidence", "evidence_lines"}
    check("R01 route-unchanged",
          old_keys <= set(r) and r["hubs"] == [{"path": "../Library/Search/Search-MOC", "score": 2, "line": 7}]
          and r["hub_count"] == 1 and r["evidence_lines"] == 5 and r["evidence"][0]["line"] == 5,
          json.dumps(r["hubs"], ensure_ascii=False))
    check("R02 clear", r["ambiguous"] is False and r["ambiguity"] == [] and r["candidates_total"] == 1)

    r = g.map_routes(mpath, "없는낱말")
    check("R03 no-match", r["status"] == "ok" and r["hub_count"] == 0 and r["ambiguity"] == ["no_match"])

    r = g.map_routes(mpath, "reranker 없는낱말")
    check("R04 partial", r["ambiguity"] == ["partial_match"], str(r["ambiguity"]))

    r = g.map_routes(mpath, "프롬프트")
    check("R05 tie-at-cut", "tie_at_cut" in r["ambiguity"] and r["hub_count"] == 3
          and r["candidates_total"] == 4, f'{r["ambiguity"]} total={r["candidates_total"]}')

    text = open(mpath, encoding="utf-8").read()
    twin = all([t for _, _, t in g.keyword_rows(text, k)[:3]] == [h["path"] for h in g.map_routes(mpath, k)["hubs"]]
               for k in ("프롬프트", "reranker 벡터", "에이전트 프롬프트", "MOC", "없는낱말"))
    check("R06 awk-twin", twin)

    m = g.descent_menu(mpath, "프롬프트 에이전트")
    first = m["items"][0]
    check("M01 menu-keywords", m["mode"] == "keywords" and first["name"] == "Agent-MOC" and first["score"] == 2
          and first["folder"] == "Library/Prompt" and first["desc"].startswith("에이전트 프롬프트")
          and first["note"] == "Library/Prompt/Agent-MOC.md" and m["hubs_total"] == 7,
          json.dumps(first, ensure_ascii=False))

    m = g.descent_menu(mpath, "프롬프트", limit=2)
    big = os.path.join(root, "000-START-HERE", "Big-Map.md")
    with open(big, "w", encoding="utf-8") as f:
        f.write("\n".join(f"- [[../Bulk/Hub-{i:03d}|Hub {i}]] · `Bulk` — 대량 허브 {i}" for i in range(75)) + "\n")
    m_big = g.descent_menu(big, "대량", limit=999)
    m_fold = g.descent_menu(big, "", folder="Bulk", limit=999)
    check("M02 menu-limit", len(m["items"]) == 2 and m["truncated"] is True
          and len(m_big["items"]) == 60 and m_big["truncated"] is True and m_big["matched_total"] == 75
          and len(m_fold["items"]) == 60 and m_fold["hubs_total"] == 75,
          f'{len(m_big["items"])} {len(m_fold["items"])}')

    m = g.descent_menu(mpath, "", folder="Library")
    names = [i["name"] for i in m["items"]]
    check("M03 menu-folder", m["mode"] == "folder" and names[0] == "Agent-MOC" and "Tie-MOC" not in names
          and {"folder": "Library/Search", "hubs": 2} in m["subfolders"] and m["hubs_total"] == 4,
          f"{names} {m['subfolders']}")

    m = g.descent_menu(mpath, "지도 밖")
    esc = [i for i in m["items"] if i["name"] == "Escape-MOC"]
    check("M04 menu-path-escape", esc and esc[0]["note"] is None)

    o = g.hub_outlinks(root, "Library/Search/Search-MOC.md")
    check("O01 outlinks", o["status"] == "ok" and o["links_total"] == 50 and o["links"][0]["name"] == "Note-01"
          and o["links"][0]["line"] == 3 and len(HUB_BODY) > 2500 and o["body_available"] is False,
          f'total={o.get("links_total")}')

    rc1, o1 = cli("outlinks", "--root", root, "--hub", "../vault/Library/Search/Search-MOC.md")
    rc2, o2 = cli("outlinks", "--root", root, "--hub", os.path.join(root, "Library/Search/Search-MOC.md"))
    check("O02 outlinks-escape", rc1 == 3 and rc2 == 3 and o1["status"] == "unmeasured" and o2["status"] == "unmeasured")

    o = g.hub_outlinks(root, "Library/Linked/Linked-MOC.md")
    check("O03 outlinks-symlink", o["status"] == "unmeasured", o.get("reason"))

    o = g.hub_outlinks(root, "Library/Search/Search-MOC.md", limit=5)
    o_big = g.hub_outlinks(root, "Library/Search/Search-MOC.md", limit=999)
    check("O04 outlinks-limit", len(o["links"]) == 5 and o["truncated"] is True
          and len(o_big["links"]) == 40 and o_big["links_total"] == 50)

    rc_a, a = cli("route", "--map", mpath, "--keywords", "프롬프트")
    rc_b, b = cli("menu", "--map", mpath, "--keywords", "프롬프트")
    rc_c, c = cli("menu", "--map", os.path.join(root, "nope.md"), "--keywords", "x")
    check("C01 cli-exit", rc_a == 0 and a["ambiguous"] is True and rc_b == 0 and rc_c == 3 and c["status"] == "unmeasured")

    import re as _re
    import shutil as _shutil
    body = open(os.path.join(REPO, "commands", "search.md"), encoding="utf-8").read()
    sect = body[body.index("##### Phase 0.4-D"):]
    block = _re.search(r"```bash\n(.*?)```", sect, _re.S).group(1)
    for shell in ("bash", "zsh"):
        exe = _shutil.which(shell)
        if not exe:
            print("SKIP", f"B01 block-{shell}", "shell not installed")
            continue
        # 1.8.13: the block no longer parses MAP_RESULT — the Tier 2 stage script prints ROUTE_AMBIGUOUS and the
        # model passes it back (plus VAULT_PATH, from which the block derives STRUCT_DIR)
        def run(route_ambiguous, vault_mode="same", target_status=""):
            env = dict(os.environ, CLAUDE_PLUGIN_ROOT=REPO, VAULT_PATH=root,
                       ROUTE_AMBIGUOUS=route_ambiguous, QUERY_KEYWORDS="프롬프트",
                       VAULT_MODE=vault_mode, TARGET_STATUS=target_status)
            return subprocess.run([exe, "-c", block], capture_output=True, text=True, env=env).stdout
        amb = run("1")
        clear = run("0")
        other = run("1", vault_mode="other")
        forced = run("0", target_status="ambiguous")
        check(f"B01 block-{shell}", "ROUTE_AMBIGUOUS=1" in amb and '"mode": "keywords"' in amb
              and clear.strip() == "ROUTE_AMBIGUOUS=0" and '"mode"' not in other
              and '"mode": "keywords"' in forced, repr(clear))

failed = [c for c, ok in results if not ok]
print(f"cells={len(results)} pass={len(results) - len(failed)} fail={len(failed)}")
sys.exit(1 if failed else 0)
