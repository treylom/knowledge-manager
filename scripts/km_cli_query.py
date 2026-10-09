#!/usr/bin/env python3
"""km:search — obsidian-cli 질의 이스케이프(S3 ②).

Obsidian 검색 문법은 `낱말:` 을 연산자로 읽는다. 모르는 연산자면 CLI 가 rc 0 · stdout 에
`Error: Operator "X" not recognized` 를 찍고 끝난다(JSON 아님). 실측: 「(기준: 최신 규칙)」 · 「14:26」 · 「https://…」.

규칙(질의 문자열만 바꾼다):
  1) 큰따옴표 "…" 안과 대괄호 […] 안은 그대로 — 구문 검색 · 속성 검색 [k:v]
  2) 알려진 연산자(file path content tag line block section task task-todo task-done match-case ignore-case)
     로 시작하는 토큰은 그대로 — 앞의 ( · - 는 건너뛰고 판정
  3) 그 밖의 `낱말:`(콜론이 토큰 끝) → 콜론 제거
  4) 그 밖의 `a:b`(가운데 콜론 · 시각 · URL) → 토큰 몸통을 큰따옴표로 감쌈(앞 ( - · 뒤 ) 는 바깥에 둠)
  5) 콜론 없는 질의 = 바이트 그대로

usage: km_cli_query.py "<query>"   → stdout = 바뀐 질의(개행 없음)
"""
import sys

OPS = {'file', 'path', 'content', 'tag', 'line', 'block', 'section', 'task', 'task-todo', 'task-done',
       'match-case', 'ignore-case'}


def split_tokens(q):
    """빈칸으로 나누되 "…" · […] 안의 빈칸은 토큰 안에 둔다. 구분 빈칸도 함께 돌려 원문 간격을 보존."""
    out, cur, inq, depth = [], '', False, 0
    for ch in q:
        if ch == '"' and depth == 0:
            inq = not inq
        elif ch == '[' and not inq:
            depth += 1
        elif ch == ']' and not inq and depth:
            depth -= 1
        if ch.isspace() and not inq and depth == 0:
            if cur:
                out.append(cur)
                cur = ''
            out.append(ch)
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def fix_token(t):
    if ':' not in t or t.isspace() or '"' in t or '[' in t:
        return t
    i = 0
    while i < len(t) and t[i] in '(-':
        i += 1
    j = len(t)
    while j > i and t[j - 1] == ')':
        j -= 1
    lead, core, trail = t[:i], t[i:j], t[j:]
    if ':' not in core:
        return t
    if core.split(':', 1)[0].lower() in OPS:
        return t
    if core.endswith(':') and core.count(':') == 1:
        core = core[:-1]
    else:
        core = '"' + core + '"'
    return lead + core + trail


def sanitize(q):
    if ':' not in q:
        return q
    return ''.join(fix_token(t) for t in split_tokens(q))


if __name__ == '__main__':
    sys.stdout.write(sanitize(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()))
