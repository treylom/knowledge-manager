#!/usr/bin/env python3
"""test_command_posargs.py — Claude Code 가 바꿔 넣는 위치 인자 꼴이 명령·스킬 본문에 없는지 본다.

Claude Code 는 슬래시 명령 본문을 모델에 싣기 전에 `$ARGUMENTS` 와 함께 `$0`·`$1`·`$2`… 도
사용자가 친 인자 낱말(0부터 셈)로 바꿔 넣는다 — 코드 블록 안이든 작은따옴표 안이든 가리지 않는다.
실측(1.8.9 고침 때 · 가짜 API 서버로 첫 요청 캡처): `/km:search 8월 중순 회의 기록` 에서
`"$1/api/search?q=…"` → `"중순/api/search?q=…"`, awk `{print "V\\t" $0}` → `{print "V\\t" 8월}`.
그 번호의 낱말이 없으면(인자 3개인데 `$9`) 그대로 남는다 — 그래서 짧은 질문 시험만으로는 안 보인다.

뜻이 같고 치환되지 않는 꼴(실측): 셸 `"${1}"` · awk `$(0)`·`$(1)`.
`\\$1` 로 막으려 하지 말 것 — Claude Code 가 역슬래시를 떼고 `$1` 을 남긴다(실측).

검사 대상 = Claude Code 가 본문을 그대로 싣는 파일: `commands/*.md`(한 층) · `skills/*/SKILL.md`.
Read 로만 읽는 파일(`commands/search-references/*.txt`, 낱장 `skills/*.md`)은 치환되지 않아 대상 밖.
표준 라이브러리만.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POSARG = re.compile(r"\$[0-9]")
fails = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" — " + detail if detail else ""))
    if not ok:
        fails.append(name)


# 미끼 쌍: 검사 정규식이 위험 꼴은 잡고(양성) 안전 꼴은 놓아주는지(음성)
check("bait-positive", all(POSARG.search(s) for s in ['"$1/api"', "{print $0}", "$B$6", "\\$1"]))
check("bait-negative", not any(POSARG.search(s) for s in ['"${1}/api"', "{print $(0)}", "$ARGUMENTS", "${CLAUDE_PLUGIN_ROOT}"]))

targets = sorted(glob.glob(os.path.join(REPO, "commands", "*.md")) + glob.glob(os.path.join(REPO, "skills", "*", "SKILL.md")))
check("targets-found", len(targets) >= 5, f"{len(targets)} files")
for p in targets:
    rel = os.path.relpath(p, REPO)
    hits = [f"{i}:{l.strip()[:100]}" for i, l in enumerate(open(p, encoding="utf-8"), 1) if POSARG.search(l)]
    check("no-posarg " + rel, not hits, "; ".join(hits[:3]))

# 바꾼 꼴이 옛 꼴과 같은 출력인지(awk · 셸) — 이 기계에 있는 awk·셸 전부
awks = [a for a in ("awk", "gawk", "mawk") if shutil.which(a)]
for a in awks:
    for old, new in (("{print \"V\\t\" $0}", "{print \"V\\t\" $(0)}"), ("{print $1, $2}", "{print $(1), $(2)}"),
                     ("{ print substr($0, 1, 1) \"|\" substr($0, 3) }", "{ print substr($(0), 1, 1) \"|\" substr($(0), 3) }")):
        o = subprocess.run([a, old], input="V x y\nT 한글 둘\n", capture_output=True, text=True).stdout
        n = subprocess.run([a, new], input="V x y\nT 한글 둘\n", capture_output=True, text=True).stdout
        check(f"awk-same {a} {new}", o == n and o != "", repr(n[:40]))
for sh in [s for s in ("bash", "zsh") if shutil.which(s)]:
    body = 'f() { printf "%s|" "$1/api" "${1}/api"; }; f http://h:1'
    out = subprocess.run([sh, "-c", body], capture_output=True, text=True).stdout
    check(f"shell-same {sh}", out == "http://h:1/api|http://h:1/api|", out)

print("OK" if not fails else f"FAILED {len(fails)}")
sys.exit(1 if fails else 0)
