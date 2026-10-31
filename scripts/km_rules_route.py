#!/usr/bin/env python3
"""km:search — 규칙 원본 축(Tier 0-R). 서버 무변경 · Tier 1 결과 불변 · 아래에 덧붙이는 후보만 낸다.

왜: 운영 규율 질문의 정답 파일은 vault 노트가 아니라 repo 루트 규칙 코퍼스(docs/rules-* · .claude/rules ·
.claude/skills/*/SKILL.md · 공용 레지스트리 yaml · 루트 AGENTS.md/CLAUDE.md)에 산다. 색인기(라이브 vault .md 만)도
Obsidian CLI(열린 vault 만)도 여기엔 닿지 않는다. 그래서 별도 코퍼스를 직접 훑는다.

설정(km-config.json · 없으면 꺼짐 = 현행과 동일):
  "search": {"ruleCorpus": {"root": "<repo 루트>", "index": ".claude/rules/INDEX.md",
                            "globs": ["docs/rules-core/*.md", ...], "top": 5}}

두 축:
  [rules:index] INDEX.md 트리거 표 행(트리거 칸 + 핵심 칸)과 질의 낱말 겹침(idf 가중) 상위 2행 → 그 행의 rule 이름으로
                .claude/rules/<n>.md · docs/rules-core/<n>.md · docs/rules-full/<n>.md 중 실재하는 것
  [rules:rg]    코퍼스 파일마다 질의 낱말 겹침(idf × 길이 정규화한 낱말 빈도 · 파일 이름에 있으면 덧점) 상위
  합친 순서 = index 축 먼저(≤4) → rg 축으로 top 까지 채움 · 중복 제거.

v2 (2026-10-26):
  ① --auto = 「돌릴지」를 모델이 아니라 이 대본이 정한다. 설정의 vaultPath·endpoint 를 직접 읽고, GraphRAG 끔 스위치를
     보고, 서버에 같은 질의를 1회 물어 결과 source_note 가 이 vault 에 실재하는지(존재만) 본다. 건너뛰는 경우 =
     경로 가진 결과가 있는데 하나도 이 vault 에 없을 때(= other 확정) «뿐». 서버 꺼짐·시한·끔 스위치·경로 없는
     결과 = other 가 확정 안 됐으니 돈다. (실측: v1 은 모델이 블록 자체를 안 돌린 회차가 15 중 11)
  ② rg 축 = 길이 정규화(BM25 꼴) — 긴 스킬 파일이 낱말을 많이 품어 질문과 무관하게 위로 오던 쏠림을 줄인다.
  ③ 조사 떼기 = 가장 긴 조사 하나만 · 남는 줄기가 2자 미만이면 안 뗌(「끝까지」가 「끝까」로 잘리던 문제).
  ④ 루트 에이전트 지시 파일(AGENTS.md · CLAUDE.md)은 있으면 코퍼스에 늘 넣는다(저장소 관례 · 설정 globs 와 별개).
  정답표·문항별 사전 ❌ — 전부 «원칙»(어디를 보나·어떻게 겹침을 세나)만.

v3 (2026-10-26 오후):
  ⑤ 후보마다 그 파일의 결정 표지(해제·대체·정정·철회) 줄 번호를 들여쓴 한 줄로 덧붙인다 — 질문 낱말이 든 표지 줄 중
     뒤쪽 ≤5 · 마지막 표지 줄/전체 줄. 실측: v2 판에서 원본을 열고도 앞 «재개» 문단만 읽고 몇 줄 아래 «해제» 문단을
     놓친 회차(9문항 중 1 · 두 길 다). 글 지시(명령서)는 바꿔 쓰이므로 단서는 대본 출력에 둔다. `[rules:x] 경로` 줄은 그대로.

v4 (2026-10-26 저녁):
  ⑥ 후보 원본 안 노트 이름([[링크]] · 백틱 `이름.md` · 볼트에 실재하는 백틱 슬러그)을 대본이 vaultPath 안 파일 이름으로 미리
     풀어 «↳ 가리키는 노트» 한 줄로 덧붙인다 — 고른 절 안 링크 먼저, 그다음 절에서 가까운 줄 순(≤12). 볼트에 없으면
     «볼트에 없음», 규칙 코퍼스 파일 이름이면 «규칙 원본», 찾기 자체가 실패(뿌리 없음·시한)면 «노트 찾기 못 함»(부재 아님).
     늘 «레포 전체 훑기 ❌». 실측: v3 판 한 문항에서 규칙 원본 안 [[노트]] 하나를 찾으려고
     모델이 레포 루트(약 300만 파일)에서 prune 없는 find·grep -r 을 돌려 4칸 중 3칸 180초 시한. 그 링크는 고른 절(34–47줄)
     밖 49줄 → 절 안만 풀면 못 막으므로 파일 전체를 풀되 절 안을 앞에 둔다.

경계 (1.8.5 공개 전 검토):
  ⑦ «노트 찾기 못 함» 다음 줄 `↳ $ …` 명령은 모델이 그대로 치는 실행 지점 — 따로 한 줄(표시용 이름과 섞지 않음) · vault
     경로는 문자열로 넣지 않고 "$VAULT_PATH" 변수로만 · 노트 이름은 늘 작은따옴표로 감싼 -g 값으로만(lookup_command · sq).
  ⑧ --auto 탐침: source_note = vault 상대 경로만(classify_note · 거절은 수만 셈 · 거절만으로 other 확정 ❌) · endpoint =
     http/https + 설정 host 만(probe_url) · redirect 안 따라감 · 응답 PROBE_MAX_BYTES 상한 · 전체 시한 · 응답 모양 검사(예외 ❌).

usage: km_rules_route.py --config <후보1> [--config <후보2> …] --query "<질문>" [--keywords "<k1 k2 k3>"] [--auto] [--json]
       --config = km-config.json 후보 경로(실재하는 첫 파일 · Phase -1 순서 = 현재 폴더 → vault)
       --auto   = 위 ① 판정까지 대본이 함 · 없으면 판정 없이 바로 훑음(v1 동작)
"""
import argparse
import glob
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

VERSION = 'v4'
PARTICLES = sorted(['은', '는', '이', '가', '을', '를', '의', '에', '에서', '으로', '로', '와', '과', '도', '만', '까지',
                    '부터', '에게', '한테', '이랑', '랑', '하고', '이나', '나', '이다', '이야', '야', '요', '지', '죠',
                    '인가', '인지', '이면', '면', '라고', '이라고', '라는', '이라는', '처럼', '보다', '마다', '조차'],
                   key=len, reverse=True)
STOP = {'뭐', '뭐야', '뭐였', '무엇', '어떻게', '어떤', '언제', '어디', '누구', '누가', '왜', '있지', '있나', '있어', '했지',
        '했나', '하지', '하나', '하는', '하기로', '하려면', '해야', '해야지', '하면', '했던', '정해', '정했', '뒀지', '두고',
        '되지', '되나', '되는', '그리고', '그럼', '이거', '그거', '저거', '지금', '우리', '이번', '그때', '경우', '때문',
        '것', '거', '수', '등', '및', '또는', '그', '이', '저', 'the', 'a', 'an', 'of', 'to', 'and', 'or', 'is', 'in'}
TOKEN_RE = re.compile(r'[0-9A-Za-z가-힣][0-9A-Za-z가-힣_\-]*')
ROOT_AGENT_FILES = ('AGENTS.md', 'CLAUDE.md')
SWITCH = os.path.join(os.path.expanduser('~'), '.claude-state', 'km-search-graphrag-off')
K1, B, TF_CAP = 1.2, 0.75, 50
# v3 결정 표지: 한 원본 안에 «앞 결정 → 뒤에서 해제·대체·정정·철회» 가 쌓인다. 줄 위치만 알려 주고(날짜 해석 ❌ · 어느 것이
# 현재인지는 읽는 쪽이 날짜로 판단) 출력에 «그 줄까지 읽어라»를 박는다. 「대체로·대체적」은 뺌 · 남는 잡음은 감수(줄 번호일 뿐).
MARK_RE = re.compile(r'해제|대체(?!로|적)|정정|철회')
MARK_SHOW = 5  # 절 안 표지 줄이 이보다 많으면 앞·뒤만(가운데 …)


HEAD_RE = re.compile(r'^#{1,6} ')
# v4 노트 이름: [[이름|별칭]] · [[이름#절]] · [[폴더/이름]] → 이름(.md 뗌) · 백틱 = `이름.md`(경로 없음) 또는 슬러그(볼트에 있을 때만)
LINK_RE = re.compile(r'\[\[([^\]|#\n]+)(?:[#|][^\]\n]*)?\]\]')
TICK_RE = re.compile(r'`([^`\s/]+)`')
SLUG_RE = re.compile(r'^[0-9A-Za-z가-힣][0-9A-Za-z가-힣]*(?:[-_][0-9A-Za-z가-힣]+){2,}$')
NOTE_CAP = 12
# 6초 → 20초: 부하(5분 ≈40+)·두 칸 동시 때 2.3만 파일 목록이 6초를 넘긴 실측(10-26 r1 · «노트 찾기 못 함» 뒤 레포 전체 grep).
# 모델 Bash 시한 120초 안에서 넉넉히 · 넘기면 «못 함» 줄에 그대로 칠 명령을 준다.
LOOKUP_TIMEOUT = float(os.environ.get('KM_RULES_NOTE_TIMEOUT', '20'))
LOOKUP_SKIP_DIRS = ('.git', '.obsidian', '.trash')
_VAULT_INDEX = {}


def sections(lines):
    """제목(#) 줄로 자른 절 → [(시작줄, 끝줄)] (1-based · 첫 제목 앞 머리도 한 절)."""
    starts = [0] + [i for i, l in enumerate(lines) if HEAD_RE.match(l) and i > 0]
    return [(s + 1, (starts[k + 1] if k + 1 < len(starts) else len(lines))) for k, s in enumerate(starts)]


def best_section(lines, toks):
    """질문 낱말 겹침(idf × 길이 정규화 · rg 축과 같은 꼴)이 가장 큰 제목 절 → (시작줄, 끝줄) | None."""
    secs = sections(lines)
    toks = [t for t in toks if t not in PARTICLES]
    if not toks or not secs:
        return None
    bodies = ['\n'.join(lines[a - 1:b]).lower() for a, b in secs]
    idf = idf_table(bodies, toks)
    avg = sum(len(x) for x in bodies) / len(bodies) or 1
    best = (0.0, None)
    for k, body in enumerate(bodies):
        norm = K1 * (1 - B + B * len(body) / avg)
        sc = 0.0
        for t in toks:
            tf = min(body.count(t), TF_CAP)
            sc += max(idf[t], 0.0) * tf * (K1 + 1) / (tf + norm)
        if sc > best[0]:
            best = (sc, k)
    return secs[best[1]] if best[1] is not None else None


def vault_index(vault):
    """vaultPath 안 .md 파일 상대경로 목록(질의당 1회 · 캐시) → (ok, 사유, [경로]). 숨은 폴더 포함 · .git/.obsidian/.trash 뺌.
    rg 있으면 rg --files(실측 2.3만 파일 ≈1초) · 없으면 os.walk + 마감. 실패(뿌리 없음·시한) = ok False — 부재가 아니다."""
    if vault in _VAULT_INDEX:
        return _VAULT_INDEX[vault]
    res = None
    if not vault or not os.path.isdir(vault):
        res = (False, 'vaultPath 없음', [])
    elif shutil.which('rg'):
        argv = [shutil.which('rg'), '--files', '--hidden', '--no-ignore', '-g', '*.md']
        for d in LOOKUP_SKIP_DIRS:
            argv += ['-g', '!%s' % d]
        try:
            p = subprocess.run(argv + [vault], capture_output=True, text=True, timeout=LOOKUP_TIMEOUT)
            if p.returncode in (0, 1):
                res = (True, '', [os.path.relpath(x, vault) for x in p.stdout.splitlines() if x])
        except subprocess.TimeoutExpired:
            res = (False, '시한 %gs' % LOOKUP_TIMEOUT, [])
        except OSError:
            res = None
    if res is None:
        deadline, out = time.time() + LOOKUP_TIMEOUT, []
        res = (True, '', out)
        for d, dirs, files in os.walk(vault):
            dirs[:] = [x for x in dirs if x not in LOOKUP_SKIP_DIRS]
            out += [os.path.relpath(os.path.join(d, f), vault) for f in files if f.endswith('.md')]
            if time.time() > deadline:
                res = (False, '시한 %gs' % LOOKUP_TIMEOUT, [])
                break
    _VAULT_INDEX[vault] = res
    return res


def note_names(lines, sec):
    """→ [(이름, 링크냐)] · 고른 절 안 먼저, 그다음 절에서 가까운 줄 순 · 중복 제거."""
    found = []
    for i, l in enumerate(lines, 1):
        for m in LINK_RE.finditer(l):
            n = m.group(1).strip()
            found.append((i, n[:-3] if n.endswith('.md') else n, True))
        for m in TICK_RE.finditer(l):
            n = m.group(1)
            if n.endswith('.md') and len(n) > 3:
                found.append((i, n[:-3], True))
            elif SLUG_RE.match(n):
                found.append((i, n, False))
    a, b = sec if sec else (1, len(lines))

    def dist(i):
        return 0 if a <= i <= b else (a - i if i < a else i - b)
    out, seen = [], set()
    for i, n, is_link in sorted(found, key=lambda x: (dist(x[0]), x[0])):
        if n and n not in seen:
            seen.add(n)
            out.append((n, is_link))
    return out


def lookup_command(names):
    """«노트 찾기 못 함» 줄 끝에 붙는 실행 줄. vault 경로는 문자열로 넣지 않고 이미 정해진 셸 변수 "$VAULT_PATH" 로만
    가리키고(비었으면 ${VAULT_PATH:?} 가 멈춤), 노트 이름은 shlex.quote 로 감싼 -g 값으로만 넣는다 — 작은따옴표·$(…)·백틱·
    공백이 든 이름·경로가 셸 명령이 되지 않게(생성한 줄을 그대로 치라고 지시하므로 실행 지점이다)."""
    globs = ' '.join('-g %s' % sq(n + '.md') for n in names)
    return 'rg --files --hidden %s -- "${VAULT_PATH:?VAULT_PATH 를 이 vault 경로로 다시 할당}"' % globs


def clean(s):
    """출력에 찍는 경로·이름의 제어 문자(줄바꿈 등) → '?' — 파일 이름으로 «↳ $» 줄을 지어내지 못하게(명령 인자는 sq 로 따로)."""
    return ''.join(ch if ch.isprintable() else '?' for ch in s)


def sq(s):
    """항상 작은따옴표로 감싼다(shlex.quote 는 안전 글자만이면 따옴표를 생략해 zsh 의 `=이름` 확장이 남는다)."""
    return "'%s'" % s.replace("'", "'\"'\"'")


def note_line(path, toks, vault, corpus, root):
    """후보 아래 «↳ 가리키는 노트» 한 줄 | None(노트 이름 0 · 볼트에 있는 슬러그도 0)."""
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    names = note_names(lines, best_section(lines, toks))
    links = [n for n, link in names if link]
    if not names:
        return None
    ok, why, files = vault_index(vault)
    if not ok:
        if not links:
            return None
        # 명령은 따로 한 줄 — 원본 글에서 온 노트 이름(표시용)이 같은 줄에 있으면 이름 안에 «구분 문구 + 명령»을 넣어
        # 명령 시작점을 속일 수 있다(이름엔 줄바꿈이 없으므로 다음 줄은 고정 머리말 + 대본이 만든 명령뿐).
        return ('    ↳ 가리키는 노트 %s — 노트 찾기 못 함(%s · 부재 아님) · 레포 전체 훑기 ❌ · 찾을 땐 다음 줄 명령만\n'
                '    ↳ $ %s'
                % ('·'.join('[[%s]]' % clean(n) for n in links[:NOTE_CAP]), why, lookup_command(links[:NOTE_CAP])))
    by_stem = {}
    for f in files:
        by_stem.setdefault(os.path.splitext(os.path.basename(f))[0], []).append(f)
    stems = {}
    for d in corpus:
        stems.setdefault(d['stem'], d['path'])
    hits, absent, used, cut = [], [], 0, False
    for n, link in names:
        if used >= NOTE_CAP:
            cut = True
            break
        base = os.path.basename(n)
        cand = by_stem.get(base, [])
        if '/' in n:
            cand = [f for f in cand if os.path.splitext(f)[0].endswith(n)]
        if cand:
            cand = sorted(cand, key=lambda f: (len(f), f))
            hits.append('[[%s]] → %s%s' % (clean(n), clean(cand[0]), (' (같은 이름 %d개 더)' % (len(cand) - 1)) if len(cand) > 1 else ''))
        elif link and base.lower() in stems:
            hits.append('[[%s]] → 규칙 원본 %s' % (clean(n), clean(os.path.relpath(stems[base.lower()], root))))
        elif link:
            absent.append(clean(n))
        else:
            continue  # 볼트에 없는 백틱 슬러그 = 노트 이름 아님(훅·도구 이름 등)
        used += 1
    if not hits and not absent:
        return None
    parts = ' · '.join(hits)
    if absent:
        parts += '%s볼트에 없음: %s' % (' · ' if parts else '', '·'.join(absent))
    if cut:
        parts += ' · (상한 %d · 고른 절에서 먼 링크는 생략)' % NOTE_CAP
    return '    ↳ 가리키는 노트(대본이 vaultPath 안 파일 이름으로 찾음): %s — 레포 전체 훑기 ❌' % parts


def decision_marks(path, toks):
    """→ None (표지 0) | {'n','last','lines','sec','sec_title','sec_marks'}.
    sec = 질문 낱말 겹침(idf × 길이 정규화 · rg 축과 같은 꼴)이 가장 큰 제목 절 · sec_marks = 그 절 안 표지 줄."""
    try:
        with open(path, encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None
    hits = [i + 1 for i, l in enumerate(lines) if MARK_RE.search(l)]
    if not hits:
        return None
    out = {'n': len(hits), 'last': hits[-1], 'lines': len(lines), 'sec': None, 'sec_title': '', 'sec_marks': []}
    sec = best_section(lines, toks)
    if sec:
        a, b = sec
        out['sec'] = (a, b)
        out['sec_title'] = lines[a - 1].lstrip('#').strip()[:40] if HEAD_RE.match(lines[a - 1]) else ''
        out['sec_marks'] = [n for n in hits if a <= n <= b]
    return out


def short(nums, show=MARK_SHOW):
    nums = [str(n) for n in nums]
    if len(nums) <= show + 1:
        return '·'.join(nums)
    h = show // 2
    return '·'.join(nums[:h]) + '·…·' + '·'.join(nums[-(show - h):])


def mark_line(m):
    """후보 아래 들여쓴 한 줄 — 읽을 범위와 표지 줄 번호 + «끝 결정까지 읽어라» 지시(지시는 출력에 · 명령서 글은 바꿔 쓰인다)."""
    if m.get('sec') and m['sec_marks']:
        a, b = m['sec']
        where = '질문과 맞는 절 %d–%d줄%s 안 표지 줄 %s' % (a, b, (' «%s»' % m['sec_title']) if m['sec_title'] else '',
                                                   short(m['sec_marks']))
        upto = max(b, m['sec_marks'][-1])
    else:
        where = '질문과 맞는 절에 표지 없음'
        upto = m['last']
    return ('    ↳ 결정 표지(해제·대체·정정·철회) %d곳 · %s · 파일 마지막 표지 %d/%d줄 — 열면 최소 %d줄까지 읽고 '
            '날짜가 가장 늦은 결정을 «현재 기준»으로(앞 문단만 읽고 단정 ❌)' % (m['n'], where, m['last'], m['lines'], upto))


def tokens(text, cap=None):
    out = []
    for t in TOKEN_RE.findall(text or ''):
        tl = t.lower()
        for p in PARTICLES:  # longest matching particle only · keep the word whole if the stem would be < 2 chars
            if tl.endswith(p):
                if len(tl) - len(p) >= 2:
                    tl = tl[:-len(p)]
                break
        if len(tl) >= 2 and tl not in STOP and tl not in out:
            out.append(tl)
    return out[:cap] if cap else out


def load_corpus(root, globs):
    files = [os.path.join(root, f) for f in ROOT_AGENT_FILES]
    for g in globs:
        files += sorted(glob.glob(os.path.join(root, g)))
    seen, docs = set(), []
    for f in files:
        rf = os.path.realpath(f)
        if rf in seen or not os.path.isfile(f):
            continue
        seen.add(rf)
        try:
            body = open(f, encoding='utf-8', errors='replace').read().lower()
        except OSError:
            continue
        docs.append({'path': f, 'stem': os.path.splitext(os.path.basename(f))[0].lower(), 'body': body,
                     'dir': os.path.basename(os.path.dirname(f)).lower()})
    return docs


def idf_table(texts, toks):
    n = max(len(texts), 1)
    return {t: math.log((n + 1) / (sum(1 for x in texts if t in x) + 0.5)) for t in toks}


def parse_index(index_path):
    rows = []
    if not index_path or not os.path.isfile(index_path):
        return rows
    for line in open(index_path, encoding='utf-8', errors='replace'):
        if not line.startswith('|') or line.startswith('|---') or line.startswith('| 트리거'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 3:
            continue
        names = [os.path.splitext(os.path.basename(m))[0] for m in re.findall(r'\]\(([^)]+\.md)\)', cells[1])]
        if not names:
            continue
        rows.append({'text': (cells[0] + ' ' + cells[2]).lower(), 'names': names})
    return rows


def route(query, keywords, root, index_rel, globs, top=5, vault=None):
    toks = tokens(keywords or '') + [t for t in tokens(query) if t not in tokens(keywords or '')]
    res = {'version': VERSION, 'tokens': toks, 'index_rows': [], 'index': [], 'rg': [], 'merged': []}
    if not toks:
        return res
    rows = parse_index(os.path.join(root, index_rel) if index_rel else None)
    if rows:
        iidf = idf_table([r['text'] for r in rows], toks)
        scored = []
        for i, r in enumerate(rows):
            s = sum(iidf[t] for t in toks if t in r['text'])
            if s > 0:
                scored.append((s, i, r))
        scored.sort(key=lambda x: (-x[0], x[1]))
        for s, i, r in scored[:2]:
            res['index_rows'].append({'row': i, 'score': round(s, 3), 'names': r['names']})
            for n in r['names']:
                for rel in ('docs/rules-full/%s.md', 'docs/rules-core/%s.md', '.claude/rules/%s.md'):
                    p = os.path.join(root, rel % n)
                    if os.path.isfile(p) and p not in res['index']:
                        res['index'].append(p)
    docs = load_corpus(root, globs)
    if docs:
        didf = idf_table([d['body'] for d in docs], toks)
        avg = sum(len(d['body']) for d in docs) / len(docs)
        scored = []
        for d in docs:
            name = d['stem'] + ' ' + d['dir']
            norm = K1 * (1 - B + B * len(d['body']) / avg)
            s = 0.0
            for t in toks:
                tf = min(d['body'].count(t), TF_CAP)
                w = max(didf[t], 0.0)
                s += w * tf * (K1 + 1) / (tf + norm) + (2 * w if t in name else 0)
            if s > 0:
                scored.append((s, d['path']))
        scored.sort(key=lambda x: (-x[0], len(x[1]), x[1]))
        res['rg'] = [{'path': p, 'score': round(s, 3)} for s, p in scored[:top * 2]]
    merged = []
    for p in res['index'][:4]:
        merged.append(('rules:index', p))
    for x in res['rg']:
        if len(merged) >= top:
            break
        if x['path'] not in [m[1] for m in merged]:
            merged.append(('rules:rg', x['path']))
    res['merged'] = [{'label': l, 'path': p, 'marks': decision_marks(p, toks),
                      'notes': note_line(p, toks, vault, docs, root) if vault is not None else None} for l, p in merged[:top]]
    return res


def _env_int(name, default, low):
    try:
        return max(low, int(os.environ.get(name, default)))
    except ValueError:
        return default


PROBE_MAX_BYTES = _env_int('KM_RULES_PROBE_MAX_BYTES', 1 << 20, 1)  # 응답 상한(넘으면 misrouted)
PROBE_TIMEOUT_DEFAULT = 8.0
PROBE_TIMEOUT_MAX = 30.0  # 탐침 시한 env 상한(초) — 넘거나 숫자가 아니면 기본값


def _env_timeout(warn):
    """KM_RULES_PROBE_TIMEOUT → 유한·양수·상한 이하 float | 기본값(+사유 1줄). 예외를 던지지 않는다."""
    raw = os.environ.get('KM_RULES_PROBE_TIMEOUT')
    if raw is None:
        return PROBE_TIMEOUT_DEFAULT
    try:
        v = float(raw)
    except ValueError:
        v = None
    if v is None or not math.isfinite(v) or v <= 0 or v > PROBE_TIMEOUT_MAX:
        warn('KM_RULES_PROBE_TIMEOUT', 'not a number in (0, %g]' % PROBE_TIMEOUT_MAX)
        return PROBE_TIMEOUT_DEFAULT
    return v


def cfg_node(cfg, path, warn):
    """중첩 설정 칸 → dict. 경로 중간이 객체가 아니면 {}(안전한 기본값) + 사유 1줄 — traceback 0."""
    node, seen = cfg, []
    for k in path:
        seen.append(k)
        node = node.get(k) if isinstance(node, dict) else None
        if node is None:
            return {}
        if not isinstance(node, dict):
            warn('.'.join(seen), 'not an object')
            return {}
    return node


def cfg_str(node, key, dotted, warn):
    """설정 문자열 칸 → str | ''(없음·빈 값·다른 형 = 기본값, 다른 형이면 사유 1줄)."""
    v = node.get(key)
    if v is None or v == '':
        return ''
    if not isinstance(v, str):
        warn(dotted, 'not a string')
        return ''
    return v


def config_warner():
    """사유 줄 = stderr `RULES_CONFIG_IGNORED=<칸>: <사유>` (같은 칸은 1번) — stdout `RULES:` 줄 모양은 그대로."""
    done = set()

    def warn(dotted, why):
        if dotted not in done:
            done.add(dotted)
            print('RULES_CONFIG_IGNORED=%s: %s' % (dotted, why), file=sys.stderr)
    return warn
PROBE_MAX_RESULTS = 50   # top_k=5 를 묻는다 · 이보다 많으면 모양이 틀린 응답
NOTE_PATH_MAX = 1024     # source_note 한 개 길이 상한(문자)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """탐침은 redirect 를 따라가지 않는다 → 3xx 는 HTTPError 로 올라와 misrouted."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe_url(endpoint, query):
    """endpoint → 탐침 URL | None(정책 밖). http/https · host 있음 · 계정 정보·query·fragment 없음 만 허용 —
    요청은 설정에 적힌 그 host 하나로만 간다(redirect 도 안 따라감)."""
    if not isinstance(endpoint, str) or not endpoint or any(c in endpoint for c in '\x00\r\n?#'):
        return None
    try:
        u = urllib.parse.urlsplit(endpoint.strip())
        u.port  # 잘못된 port = ValueError
    except ValueError:
        return None
    if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password or u.query or u.fragment:
        return None
    return endpoint.strip().rstrip('/') + '/api/search?' + urllib.parse.urlencode({'q': query, 'top_k': 5, 'mode': 'hybrid'})


def classify_note(vault, n):
    """서버가 준 source_note 하나 → 'in'(이 vault 안 실재 파일) | 'absent'(vault 상대 경로로 맞지만 없음) |
    'rejected:<사유>'(비문자열·빈 값·NUL·절대 경로·`..`·vault 밖으로 풀림·너무 김). 예외를 던지지 않는다."""
    if not isinstance(n, str):
        return 'rejected:not-string'
    if not n.strip() or n != n.strip() or len(n) > NOTE_PATH_MAX:
        return 'rejected:length'
    if '\x00' in n:
        return 'rejected:nul'
    try:
        n.encode('utf-8')
    except UnicodeEncodeError:  # 짝 없는 서로게이트 등 — 경로 함수에 넣으면 예외
        return 'rejected:encoding'
    if os.path.isabs(n) or n.startswith(('/', '\\', '~')) or re.match(r'^[A-Za-z]:', n):
        return 'rejected:absolute'
    if '..' in re.split(r'[\\/]', n):
        return 'rejected:dotdot'
    try:
        root = os.path.realpath(vault)
        full = os.path.realpath(os.path.join(root, n))
        if os.path.commonpath([root, full]) != root or full == root:
            return 'rejected:outside-vault'
        return 'in' if os.path.isfile(full) else 'absent'
    except (OSError, ValueError, UnicodeError):
        return 'rejected:invalid'


def _fetch(url, timeout, box):
    """일꾼: box['r'] = ('ok', body) | ('slow', None) | ('http', None) | ('err', 예외). body ≤ PROBE_MAX_BYTES+64KiB."""
    opener = urllib.request.build_opener(_NoRedirect)
    deadline = time.monotonic() + timeout
    try:
        with opener.open(url, timeout=timeout) as r:
            chunks, size = [], 0
            while size <= PROBE_MAX_BYTES:
                if time.monotonic() > deadline:
                    box['r'] = ('slow', None)
                    return
                c = r.read1(65536)
                if not c:
                    break
                chunks.append(c)
                size += len(c)
            box['r'] = ('ok', b''.join(chunks))
    except urllib.error.HTTPError:
        box['r'] = ('http', None)
    except Exception as e:
        box['r'] = ('err', e)


def decide(full_cfg, query, timeout=None, switch=SWITCH, warn=None):
    """--auto gate, decided here (not by the model) → (run?, vault_mode, graphrag_state, rejected_notes).
    Skip only when vault_mode == 'other' is confirmed: vault-relative results exist, none is in this vault, and no
    result was rejected. Endpoint = http/https on the configured host only · no redirect · response ≤ PROBE_MAX_BYTES ·
    shape = {"results": [ {…}, … ]} (anything else → misrouted, never an exception)."""
    warn = warn or config_warner()
    full_cfg = full_cfg if isinstance(full_cfg, dict) else {}
    vault = cfg_str(cfg_node(full_cfg, ('storage', 'obsidian'), warn), 'vaultPath', 'storage.obsidian.vaultPath', warn)
    endpoint = (cfg_str(cfg_node(full_cfg, ('linking', 'semantic_adapter'), warn), 'endpoint',
                        'linking.semantic_adapter.endpoint', warn)
                or os.environ.get('GRAPHRAG_API_URL') or 'http://127.0.0.1:8400')
    if os.path.exists(switch):
        return True, 'unknown', 'disabled', 0
    timeout = float(timeout) if timeout is not None else _env_timeout(warn)
    url = probe_url(endpoint, query)
    if url is None:
        return True, 'unknown', 'misrouted', 0
    # 전체 벽시계 예산 = timeout(+0.5초) — 소켓 시한은 한 번 읽기마다라 헤더·본문을 한 바이트씩 흘리면 끝없이 늘어난다.
    # 연결·헤더·본문을 일꾼 스레드에서 받고 여기선 그 예산만큼만 기다린다(넘기면 unreachable · 스레드는 데몬).
    box = {}
    worker = threading.Thread(target=_fetch, args=(url, timeout, box), daemon=True)
    worker.start()
    worker.join(timeout + 0.5)
    kind, val = box.get('r', ('slow', None))
    if kind == 'slow':
        return True, 'unknown', 'unreachable', 0
    if kind == 'http':  # 4xx·5xx · 3xx(redirect 안 따라감)
        return True, 'unknown', 'misrouted', 0
    if kind == 'err':  # refused · timeout · sandbox-blocked
        reason = getattr(val, 'reason', val)
        return True, 'unknown', 'absent' if isinstance(reason, ConnectionRefusedError) else 'unreachable', 0
    body = val
    if len(body) > PROBE_MAX_BYTES:
        return True, 'unknown', 'misrouted', 0
    try:
        doc = json.loads(body)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return True, 'unknown', 'misrouted', 0
    if not isinstance(doc, dict):
        return True, 'unknown', 'misrouted', 0
    results = doc.get('results')
    if results is None:
        results = []
    if not isinstance(results, list) or len(results) > PROBE_MAX_RESULTS or not all(isinstance(x, dict) for x in results):
        return True, 'unknown', 'misrouted', 0
    notes = [x['source_note'] for x in results if x.get('source_note') not in (None, '')]
    if not notes or not vault or not os.path.isdir(vault):
        return True, 'unknown', 'ok', 0
    kinds = [classify_note(vault, n) for n in notes]
    rejected = sum(1 for k in kinds if k.startswith('rejected:'))
    if 'in' in kinds:
        return True, 'same', 'ok', rejected
    if rejected:
        return True, 'unknown', 'ok', rejected
    return False, 'other', 'ok', 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', action='append', default=[], help='km-config.json 후보(여러 번 · 실재하는 첫 파일)')
    ap.add_argument('--query', required=True)
    ap.add_argument('--keywords', default='')
    ap.add_argument('--auto', action='store_true', help='돌릴지 판정(볼트 같음/다름 · 서버 상태)을 대본이 함')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    warn = config_warner()
    full = {}
    for c in a.config:
        if c and os.path.isfile(c):
            try:
                with open(c, encoding='utf-8') as fh:
                    full = json.load(fh)
            except (OSError, ValueError, RecursionError):
                full = {}
            break
    if not isinstance(full, dict):
        warn('(top level)', 'not an object')
        full = {}
    cfg = cfg_node(full, ('search', 'ruleCorpus'), warn)
    root = cfg_str(cfg, 'root', 'search.ruleCorpus.root', warn)
    globs = cfg.get('globs')
    if globs is not None and not (isinstance(globs, list) and all(isinstance(g, str) for g in globs)):
        warn('search.ruleCorpus.globs', 'not a list of strings')
        globs = None
    index = cfg_str(cfg, 'index', 'search.ruleCorpus.index', warn) or None
    top = cfg.get('top', 5)
    if isinstance(top, bool) or not isinstance(top, int) or not 1 <= top <= 50:
        if 'top' in cfg:
            warn('search.ruleCorpus.top', 'not an integer in 1..50')
        top = 5
    if not root or not globs:
        print('RULES: off (km-config search.ruleCorpus 미설정)')
        return 0
    gate = ''
    if a.auto:
        run, vm, gs, rej = decide(full, a.query, warn=warn)
        gate = ' vault_mode=%s graphrag=%s%s' % (vm, gs, (' notes_rejected=%d' % rej) if rej else '')
        if not run:
            print('RULES: %s skip(vault_mode=other — 서버 색인이 다른 vault · 로컬 규칙 읽기 0)%s' % (VERSION, gate))
            return 0
    vault = cfg_str(cfg_node(full, ('storage', 'obsidian'), warn), 'vaultPath', 'storage.obsidian.vaultPath', warn)
    r = route(a.query, a.keywords, root, index, globs, top, vault=vault)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
        return 0
    print('RULES: %s%s tokens=%d index_rows=%d hits=%d' % (VERSION, gate, len(r['tokens']), len(r['index_rows']), len(r['merged'])))
    for m in r['merged']:
        print('[%s] %s' % (m['label'], clean(os.path.relpath(m['path'], root))))
        if m.get('marks'):
            print(mark_line(m['marks']))
        if m.get('notes'):
            print(m['notes'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
