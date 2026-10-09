#!/usr/bin/env python3
"""km:search — Tier 1-R 규칙 코퍼스 보강(S3 ③). 서버 무변경 · Tier 1 결과 불변 · 아래에 덧붙이는 후보만 낸다.

왜: 운영 규율 질문의 정답 파일은 vault 노트가 아니라 repo 루트 규칙 코퍼스(docs/rules-* · .claude/rules ·
.claude/skills/*/SKILL.md · 공용 레지스트리 yaml)에 산다. 색인기(라이브 vault .md 만)도 Obsidian CLI(열린 vault 만)도
여기엔 닿지 않는다. 그래서 별도 코퍼스를 직접 훑는다.

설정(km-config.json · 없으면 꺼짐 = 현행과 동일):
  "search": {"ruleCorpus": {"root": "<repo 루트>", "index": ".claude/rules/INDEX.md",
                            "globs": ["docs/rules-core/*.md", ...], "top": 5}}

두 축:
  [rules:index] INDEX.md 트리거 표 행(트리거 칸 + 핵심 칸)과 질의 낱말 겹침(idf 가중) 상위 2행 → 그 행의 rule 이름으로
                .claude/rules/<n>.md · docs/rules-core/<n>.md · docs/rules-full/<n>.md 중 실재하는 것
  [rules:rg]    코퍼스 파일마다 질의 낱말 포함 여부(idf 가중 합 · 파일 이름에 있으면 ×3) 상위
  합친 순서 = index 축 먼저(≤4) → rg 축으로 top 까지 채움 · 중복 제거.

usage: km_rules_route.py --config <후보1> [--config <후보2> …] --query "<질문>" [--keywords "<k1 k2 k3>"] [--json]
       --config = km-config.json 후보 경로(실재하는 첫 파일 · Phase -1 순서 = 현재 폴더 → vault)
       키워드가 주어지면 그 낱말 + 질의 낱말을 함께 쓴다(키워드 먼저). 정답표·문항별 사전 ❌.
"""
import argparse
import glob
import json
import math
import os
import re
import sys

PARTICLES = sorted(['은', '는', '이', '가', '을', '를', '의', '에', '에서', '으로', '로', '와', '과', '도', '만', '까지',
                    '부터', '에게', '한테', '이랑', '랑', '하고', '이나', '나', '이다', '이야', '야', '요', '지', '죠',
                    '인가', '인지', '이면', '면', '라고', '이라고', '라는', '이라는', '처럼', '보다', '마다', '조차'],
                   key=len, reverse=True)
STOP = {'뭐', '뭐야', '뭐였', '무엇', '어떻게', '어떤', '언제', '어디', '누구', '누가', '왜', '있지', '있나', '있어', '했지',
        '했나', '하지', '하나', '하는', '하기로', '하려면', '해야', '해야지', '하면', '했던', '정해', '정했', '뒀지', '두고',
        '되지', '되나', '되는', '그리고', '그럼', '이거', '그거', '저거', '지금', '우리', '이번', '그때', '경우', '때문',
        '것', '거', '수', '등', '및', '또는', '그', '이', '저', 'the', 'a', 'an', 'of', 'to', 'and', 'or', 'is', 'in'}
TOKEN_RE = re.compile(r'[0-9A-Za-z가-힣][0-9A-Za-z가-힣_\-]*')


def tokens(text, cap=None):
    out = []
    for t in TOKEN_RE.findall(text or ''):
        tl = t.lower()
        for p in PARTICLES:
            if len(tl) > len(p) + 1 and tl.endswith(p):
                tl = tl[:-len(p)]
                break
        if len(tl) >= 2 and tl not in STOP and tl not in out:
            out.append(tl)
    return out[:cap] if cap else out


def load_corpus(root, globs):
    files = []
    for g in globs:
        files += sorted(glob.glob(os.path.join(root, g)))
    seen, docs = set(), []
    for f in files:
        if f in seen or not os.path.isfile(f):
            continue
        seen.add(f)
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


def route(query, keywords, root, index_rel, globs, top=5):
    toks = tokens(keywords or '') + [t for t in tokens(query) if t not in tokens(keywords or '')]
    res = {'tokens': toks, 'index_rows': [], 'index': [], 'rg': [], 'merged': []}
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
        scored = []
        for d in docs:
            name = d['stem'] + ' ' + d['dir']
            s = sum(didf[t] * (3 if t in name else 1) for t in toks if t in d['body'] or t in name)
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
    res['merged'] = [{'label': l, 'path': p} for l, p in merged[:top]]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', action='append', default=[], help='km-config.json 후보(여러 번 · 실재하는 첫 파일)')
    ap.add_argument('--query', required=True)
    ap.add_argument('--keywords', default='')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    cfg = {}
    for c in a.config:
        if c and os.path.isfile(c):
            try:
                cfg = (json.load(open(c)).get('search') or {}).get('ruleCorpus') or {}
            except (OSError, ValueError):
                cfg = {}
            break
    if not cfg.get('root') or not cfg.get('globs'):
        print('RULES: off (km-config search.ruleCorpus 미설정)')
        return 0
    r = route(a.query, a.keywords, cfg['root'], cfg.get('index'), cfg['globs'], int(cfg.get('top', 5)))
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
        return 0
    print('RULES: tokens=%d index_rows=%d hits=%d' % (len(r['tokens']), len(r['index_rows']), len(r['merged'])))
    for m in r['merged']:
        print('[%s] %s' % (m['label'], os.path.relpath(m['path'], cfg['root'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
