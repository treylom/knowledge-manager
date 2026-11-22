#!/usr/bin/env python3
"""km:search 읽기 예산 계약 — 많이 읽어야 하는 질문은 근거 노트를 20개까지 읽을 수 있고,
얕은 질문의 기본값(QUICK 1-2·총 3 / DEEP 3-5·총 8)은 그대로인지 본다.

쓰는 법: python3 -I -B scripts/tests/test_search_read_budget.py [저장소 뿌리]
(뿌리를 안 주면 이 파일 기준 ../../ · 고치기 전 판에 돌리면 실패해야 한다)
"""
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", ".."))
FAILS = []


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        FAILS.append(name)


def lines_with(text, *needles):
    return [ln for ln in text.splitlines() if all(n in ln for n in needles)]


S = read("commands/search.md")
MODES = read("commands/search-references/modes-output.txt")
GRAPH = read("commands/search-references/phase-2.5-graph.txt")
AGENT = read(".agent/skills/km-search/SKILL.md")
REFS = {f: read("commands/search-references/" + f)
        for f in sorted(os.listdir(os.path.join(ROOT, "commands/search-references"))) if f.endswith(".txt")}

# 1. 넓게 읽기 모드가 있다 — 깃발 · AUTO 조건 · 상한 20
check("search.md: --wide 깃발", bool(re.search(r"`--wide`", S)))
check("search.md: --notes N 깃발(1~20 으로 자름)", bool(lines_with(S, "--notes", "20")))
check("search.md: AUTO 라우팅에 WIDE 조건 줄", bool(re.search(r"^- WIDE:", S, re.M)))
check("search.md: KM_MODE 에 WIDE 값", "QUICK·DEEP·WIDE" in S or "QUICK, DEEP 또는 WIDE" in S)
check("search.md: 읽기 예산 줄에 WIDE 총 ≤20", bool(lines_with(S, "primary evidence reads", "WIDE", "≤20")))
check("search.md: 참조 로드 머리줄에 WIDE ≤20", bool(lines_with(S, "증거 노트 Read 기본 = 3", "WIDE", "≤20")))
check("search.md: top_k WIDE 20", bool(re.search(r"top_k: QUICK 5 / DEEP 10 / WIDE 20", S)))
check("search.md: 20 넘게 읽기 ❌(굳은 상한)", bool(lines_with(S, "20", "초과 ❌")))
check("search.md: DEEP → WIDE 승격 조건", bool(lines_with(S, "승격", "WIDE")))
check("search.md: 6번째부터 본문 2,500자 예산", bool(lines_with(S, "WIDE", "2,500")))
check("search.md: READ_BUDGET 표지 줄", bool(re.search(r'echo "READ_BUDGET=', S)))
check("search.md: 한 응답에 묶어 읽기(병렬 Read)", bool(lines_with(S, "WIDE", "한 응답")))

# 2. 얕은 질문 기본값은 그대로 — 많이 읽기는 «필요할 때만»
check("search.md: QUICK 1-2 · 총 ≤3 유지", bool(lines_with(S, "링크 추가 Read ≤1, 총 ≤3")))
check("search.md: DEEP 추가 ≤3·총 ≤8 유지", bool(lines_with(S, "DEEP 추가 ≤3·총 ≤8")))
check("search.md: 기본 primary = 3 유지", bool(lines_with(S, "primary evidence reads 기본 = 3")))
check("search.md: AUTO 기본은 WIDE 아님(정의형·키워드 = QUICK)", bool(re.search(r"^- QUICK: 그 외", S, re.M)))

# 3. 참조 파일이 옛 상한을 «전체 상한»으로 말하지 않는다
gl = lines_with(GRAPH, "**링크 추적 예산")
check("phase-2.5-graph: 링크 추적 예산 줄에 WIDE", bool(gl) and all("WIDE" in ln for ln in gl))
check("phase-2.5-graph: WIDE 총 20 초과 ❌", bool(lines_with(GRAPH, "WIDE 총 20 초과 ❌")))
check("modes-output: DEEP 중단 규칙에 WIDE 승격", bool(lines_with(MODES, "읽기 중단", "WIDE")) or
      bool(lines_with(MODES, "DEEP 추가 Read ≤3", "WIDE")))
check("modes-output: WIDE 출처 규칙", bool(lines_with(MODES, "WIDE", "출처")))
bare = [f for f, t in REFS.items() if "primary read 예산(기본 3)" in t]
check("참조 파일 머리줄에 «(기본 3)» 만 남은 곳 0 (%s)" % ",".join(bare), not bare)
check(".agent km-search 스킬: WIDE ≤20", bool(lines_with(AGENT, "WIDE", "≤20")))

# 4. 상한은 20 을 넘지 않는다 — 어느 파일에도 WIDE 에 20 넘는 수 ❌
over = []
for name, text in [("search.md", S), ("modes", MODES), ("graph", GRAPH), ("agent", AGENT)]:
    for ln in text.splitlines():
        if "WIDE" in ln and re.search(r"(≤|총 |cap )(2[1-9]|[3-9]\d|\d{3,})\b", ln):
            over.append(name + ": " + ln[:80])
check("WIDE 줄에 20 넘는 상한 0", not over)

print("\n%d FAIL" % len(FAILS))
sys.exit(1 if FAILS else 0)
