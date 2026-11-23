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

# 5. 문자열이 «어딘가 있다»가 아니라 값·코드가 맞는지(독립 재검 11-23 변이 6개가 살아남아 조임)
check("코드: WIDE → TOP_K=20 · 기본 cap 20",
      'WIDE) TOP_K=20; READ_CAP="${KM_NOTES:-20}" ;;' in S)
check("코드: QUICK 5/3 · DEEP 10/8", "QUICK) TOP_K=5; READ_CAP=3 ;;" in S and "*) TOP_K=10; READ_CAP=8 ;;" in S)
check("코드: 20 위로 자르기 · 1 아래로 자르기 · 숫자 아니면 20",
      '[ "$READ_CAP" -gt 20 ] && READ_CAP=20' in S and '[ "$READ_CAP" -lt 1 ] && READ_CAP=1' in S
      and "''|*[!0-9]*) READ_CAP=20" in S)
wl = lines_with(S, "WIDE 본문 예산")
check("WIDE 본문 예산 = 정확히 2,500자(25,000 같은 값 ❌)",
      len(wl) == 1 and bool(re.search(r"(?<![0-9,])2,500자", wl[0])) and not re.search(r"\d{2,},\d{3}", wl[0]))
check("WIDE 본문 예산: caller truncated 표지를 보고 다시 읽기", bool(wl) and "truncated" in wl[0] and "offset" in wl[0])
check("WIDE 읽는 차례: 4개씩 묶어 한 응답", bool(lines_with(S, "WIDE 읽는 차례", "4개씩", "한 응답")))
aw = [ln for ln in S.splitlines() if ln.startswith("- WIDE:")]
check("AUTO WIDE 줄: 길이만으론 아님 · 대상 2~3개면 DEEP · 영어 낱말 단위 · 물음표 조건 ❌",
      len(aw) == 1 and "길다는 것만으로는 WIDE 가 아니다" in aw[0] and "2~3개뿐이면" in aw[0]
      and "낱말 단위" in aw[0] and "물음표" not in aw[0] and "?" not in aw[0])
check("modes-output: WIDE 출처 문구 정확", "WIDE: 제한 없음 + 출처 = 실제로 근거로 쓴 노트 전부(≤20)" in MODES)
check("B 블록 제목·집행 계약·영수증 문구 = DEEP·WIDE(코드와 일치)",
      "### B. backlinks 1-hop (DEEP·WIDE 필수" in S and "# 집행 계약: DEEP·WIDE 모드에서" in S
      and "- 그래프 칸(1.8.5): DEEP·WIDE 이면" in S and '[ "${KM_MODE:-}" = WIDE ]; then' in S)
check(".agent 거울: --wide 깃발 줄 · WIDE top_k=20", bool(re.search(r"^- `--wide`", AGENT, re.M)) and "**WIDE**: top_k=20" in AGENT)

# 6. 상한 블록을 실제로 돌려 본다(bash)
import subprocess, tempfile
m = re.search(r'^case "\$\{KM_MODE\}" in QUICK.*?^echo "READ_BUDGET=[^\n]*$', S, re.M | re.S)
ok = bool(m)
if ok:
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
        f.write(m.group(0) + "\n")
    cases = [("QUICK", "", "5", "3"), ("DEEP", "", "10", "8"), ("WIDE", "", "20", "20"), ("WIDE", "12", "20", "12"),
             ("WIDE", "50", "20", "20"), ("WIDE", "0", "20", "1"), ("WIDE", "abc", "20", "20"), ("WIDE", "-5", "20", "20")]
    for mode, notes, tk, cap in cases:
        out = subprocess.run(["bash", f.name], capture_output=True, text=True,
                             env={"PATH": os.environ.get("PATH", ""), "KM_MODE": mode, "KM_NOTES": notes}).stdout
        if ("TOP_K=%s\n" % tk) not in out or ("(cap %s)" % cap) not in out:
            ok = False
            print("   case %s/%s -> %r" % (mode, notes, out))
    os.unlink(f.name)
check("상한 블록 bash 실행 8경우(QUICK 3 · DEEP 8 · WIDE 20 · 12 · 50→20 · 0→1 · abc→20 · -5→20)", ok)

print("\n%d FAIL" % len(FAILS))
sys.exit(1 if FAILS else 0)
