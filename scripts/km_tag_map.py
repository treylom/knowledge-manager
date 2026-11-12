#!/usr/bin/env python3
"""km 추천 태그 지도 (2026-11-11) — 표준 라이브러리만 · `python3 -I` 로 실행.

  build   : 태그 수(obsidian-cli `tags counts format=json` 출력 파일 또는 CLI 직접) → 갈래별 TAG-Map.md
            + 짝 파일 <stem>.tags.tsv(전체 태그 색인: 태그·수·사전 별칭 — 잡음 태그 뺌)
  suggest : 핵심어(+물음 원문) → 추천 태그 JSON 1줄 (km_search_guard.py route/menu 와 같은 꼴: 점수·ambiguous·menu)
            찾기 = 전체 색인(짝 파일 · 없으면 지도 줄) · 순위 = ①정확 일치 ②별칭 일치 ③단어 경계 부분 일치

검색 중에는 tags counts 를 부르지 않는다 — build 는 검색 밖에서 한 번 돌리는 명령이다.
이 대본은 모델을 부르지 않는다. 애매하면 갈래 메뉴를 내고, 고르는 것은 검색을 돌리는 모델 몫이다.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import unicodedata

NAMESPACES = ("topic", "kind", "proj", "status")
OWNER_DEFAULT = ("tofukyung", "얼룩소", "threads", "threads-post")
CAT_OWNER = "소유·출처"
CAT_FLAT = "평면 상위"
CAT_REST = "그 밖"
CATEGORIES = tuple(n + "/" for n in NAMESPACES) + (CAT_OWNER, CAT_FLAT)
CLI_DEFAULT = "/Applications/Obsidian.app/Contents/MacOS/obsidian-cli"
CLI_TIMEOUT = 30
MENU_MAX = 15
INDEX_SUFFIX = ".tags.tsv"
KST = datetime.timezone(datetime.timedelta(hours=9))
# 한 줄 꼴: - `#<태그>` (<수>) — 별칭: <a>, <b>   (태그를 코드 글자로 감싼다 — 맨 #태그 는 Obsidian 이
# 이 지도 노트 자체를 그 태그의 노트로 색인해 tag: 검색에 지도가 끼고 다시 만들 때 수가 1씩 부푼다)
LINE = re.compile(r"^- `?#([^`\s]+)`? \((\d+)\) — 별칭: (.*)$")
EDGE_PUNCT = "\"'`«»“”‘’()[]{}<>.,!?;:·…~"
HEX = re.compile(r"^(?:[0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$", re.I)
JOSA = ("에서", "에게", "까지", "부터", "처럼", "보다", "으로", "이랑", "이나",
        "을", "를", "은", "는", "이", "가", "의", "에", "와", "과", "도", "만", "로", "랑", "나")
TIER = {3: "exact", 2: "alias", 1: "partial"}


def nfc(value):
    return unicodedata.normalize("NFC", value)


def fold(value):
    return nfc(value).casefold()


def norm(value):
    """비교용: 대소문자·# 무시 · 구분자(- _ 공백) = '-' 하나."""
    return re.sub(r"[-_\s]+", "-", fold(value).lstrip("#")).strip("-")


def split_ns(tag):
    """'topic/claude-code' → ('topic', 'claude-code') · 네임스페이스 밖이면 ('', tag)."""
    head, sep, rest = tag.partition("/")
    if sep and head.casefold() in NAMESPACES and rest:
        return head.casefold(), rest
    return "", tag


def noise_reason(tag):
    """잡음 태그 규칙(색인·목록에서 뺌): ① '/' 로 시작 ② 첫 글자가 글자(유니코드 L*)가 아님 — 숫자·기호·이모지·«»» 등
    ③ 숫자가 섞인 3·6·8자리 16진 색 코드(#FC1C49 등) ④ 네임스페이스 뿌리(#topic 등 = 아래 태그 수의 합계)."""
    if not tag or tag.startswith("/"):
        return "slash"
    if not unicodedata.category(tag[0]).startswith("L"):
        return "first-char"
    if HEX.match(tag) and re.search(r"\d", tag):
        return "hex-color"
    if fold(tag) in NAMESPACES:
        return "namespace-root"
    return None


def die(reason, **extra):
    print(json.dumps(dict({"status": "error", "reason": reason}, **extra), ensure_ascii=False))
    raise SystemExit(3)


def cli_cmd(cli, vault, *args):
    # vault= 는 «명령 맨 앞»에 줄 때만 따른다(명령 뒤에 붙이면 앱의 활성 볼트로 감 · 11-11 실측)
    return [cli] + ([f"vault={vault}"] if vault else []) + list(args)


def run_cli(cmd):
    # 표준입력은 건드리지 않는다 — stdin=/dev/null 이면 obsidian-cli 가 0 B 를 낸다(11-06 실측)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT)


# ── 태그 수 읽기 ────────────────────────────────────────────────────────────
def load_counts(counts_json, cli, vault):
    vault_path = ""
    if counts_json:
        try:
            with open(counts_json, encoding="utf-8-sig") as f:
                raw = f.read()
        except OSError as e:
            die("counts_read_failed", detail=str(e))
        source = os.path.basename(counts_json)
    else:
        cli = cli or CLI_DEFAULT
        if not os.access(cli, os.X_OK):
            die("cli_not_executable", cli=cli)
        try:
            run = run_cli(cli_cmd(cli, vault, "tags", "counts", "format=json"))
            where = run_cli(cli_cmd(cli, vault, "vault", "info=path"))
        except (OSError, subprocess.SubprocessError) as e:
            die("cli_failed", detail=str(e)[:200])
        if run.returncode != 0:
            die("cli_failed", rc=run.returncode, detail=(run.stderr or run.stdout)[:200])
        raw = run.stdout
        out = (where.stdout or "").strip()
        vault_path = out if where.returncode == 0 and out.startswith("/") and "\n" not in out else ""
        source = "obsidian-cli tags counts" + (f" (vault={vault})" if vault else " (활성 볼트)")
    try:
        data = json.loads(raw)
        assert isinstance(data, list)
    except (ValueError, AssertionError):
        die("counts_not_json_list", head=raw[:120])
    counts = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        tag = nfc(str(item.get("tag") or "")).lstrip("#").strip()
        try:
            n = int(str(item.get("count") or "0").replace(",", ""))
        except ValueError:
            continue
        if tag:
            counts[tag] = counts.get(tag, 0) + n
    return counts, source, vault_path


# ── 7월 태그 사전(§1a 표기 병합 · §1b 한/영 동의어 · v1.1 매핑 · §2 소유·출처) ────────
def parse_dictionary(path):
    with open(path, encoding="utf-8-sig") as f:
        text = nfc(f.read())
    pairs = []  # (정본, [다른 표기 …])
    for line in text.splitlines():
        m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*([^|]*)\|", line)
        if not m:
            continue
        canon = split_ns(m.group(1).strip())[1]
        variants = re.findall(r"([^\s+()=|`]+)\(\d[\d,]*\)", m.group(2))
        pairs.append((canon, variants))
    for left, right in re.findall(r"`([^`]+)`\s*→\s*`([^`]+)`", text):
        pairs.append((split_ns(right.strip())[1], [left.strip()]))
    groups = []  # 같은 정본으로 묶인 표기들(순서 유지) — 겹치면 합친다
    for canon, variants in pairs:
        members = [canon] + [v for v in variants if v]
        keys = {fold(x) for x in members}
        hit = [g for g in groups if keys & {fold(x) for x in g}]
        merged = []
        for g in hit + [members]:
            for x in g:
                if fold(x) not in {fold(y) for y in merged}:
                    merged.append(x)
        groups = [g for g in groups if g not in hit] + [merged]
    owner = []
    sec = re.search(r"###\s*소유·출처[^\n]*\n(.*?)(?=\n##|\Z)", text, re.S)
    if sec:
        owner = re.findall(r"`([^`/\s]+)`\(\d[\d,]*\)", sec.group(1))
    return groups, owner


def dict_aliases(tag, groups):
    base = split_ns(tag)[1]
    out, seen = [], {fold(tag), fold(base)}
    for g in groups:
        if fold(base) in {fold(x) for x in g}:
            for x in g:
                if fold(x) not in seen:
                    seen.add(fold(x))
                    out.append(x)
    return out


def aliases_for(tag, groups):
    _, base = split_ns(tag)
    out = []
    if base != tag:
        out.append(base)
    if re.search(r"[-_]", base):
        out.append(re.sub(r"[-_]+", " ", base).strip())
    out.extend(dict_aliases(tag, groups))
    seen = {fold(tag)}
    result = []
    for a in out:
        if a and fold(a) not in seen:
            seen.add(fold(a))
            result.append(a)
    return result


# ── build ─────────────────────────────────────────────────────────────────
def build(args):
    counts, source, vault_path = load_counts(args.counts_json, args.cli, args.vault)
    source_vault = args.source_vault or vault_path or "unknown(태그 수 파일 — --source-vault 로 적을 것)"
    groups, owner = parse_dictionary(args.dict) if args.dict else ([], [])
    owner_set = {fold(x) for x in list(owner) + list(OWNER_DEFAULT)}
    cats = {c: [] for c in CATEGORIES}
    flat, rest, noise, kept = [], 0, {}, []
    order = sorted(counts.items(), key=lambda kv: (-kv[1], fold(kv[0]), kv[0]))
    for tag, n in order:
        why = noise_reason(tag)
        if why:
            noise[why] = noise.get(why, 0) + 1
            continue
        kept.append((tag, n))
        ns, _ = split_ns(tag)
        if ns:
            cats[ns + "/"].append((tag, n))
        elif fold(tag) in owner_set:
            cats[CAT_OWNER].append((tag, n))
        elif "/" not in tag and n >= args.flat_min:
            flat.append((tag, n))
        else:
            rest += 1
    cats[CAT_FLAT] = flat[:args.flat_top]
    rest += max(0, len(flat) - args.flat_top)
    stem = os.path.splitext(args.out)[0]
    index_path = stem + INDEX_SUFFIX
    now = datetime.datetime.now(KST).replace(microsecond=0).isoformat()
    lines = ["---", "type: moc", "tags: [kind/moc]", f"generated: {now}",
             "source: tags counts", f"source_input: {json.dumps(source, ensure_ascii=False)}",
             f"source_vault: {json.dumps(source_vault, ensure_ascii=False)}",
             f"total_tags: {len(counts)}", f"indexed_tags: {len(kept)}",
             f"noise_tags: {sum(noise.values())}",
             f"tag_index: {json.dumps(os.path.basename(index_path), ensure_ascii=False)}", "categories:"]
    for c in CATEGORIES:
        lines.append(f"  {json.dumps(c, ensure_ascii=False)}: {len(cats[c])}")
    lines.append(f"  \"{CAT_REST}\": {rest}")
    lines += ["---", "", "# TAG-Map — 갈래별 태그 목록", "",
              "km 검색의 추천 태그 목록 — 만드는 명령 = `\"$CLI\" vault=<볼트> tags counts format=json > tags.json && "
              "python3 -I <km 플러그인>/scripts/km_tag_map.py build --in tags.json --out <이 파일> "
              "--source-vault <볼트> [--dict <태그 사전.md>]` (손으로 고치지 말고 다시 만든다 · 검색 중엔 tags counts 를 부르지 않는다).",
              f"만든 볼트 = {source_vault} · 전체 태그 색인(검색이 쓰는 것) = 짝 파일 `{os.path.basename(index_path)}`(태그 {len(kept):,}개 · 잡음 {sum(noise.values()):,}개 뺌)."]
    for c in CATEGORIES:
        lines += ["", f"## {c}"]
        for tag, n in cats[c]:
            al = aliases_for(tag, groups)
            lines.append(f"- `#{tag}` ({n}) — 별칭: {', '.join(al) if al else '-'}")
    lines += ["", "---", "",
              f"{CAT_REST}: 태그 {rest:,}개 — 목록에 싣지 않음(평면 수 < {args.flat_min} · 평면 상위 {args.flat_top} 밖 · "
              f"그 밖 네임스페이스) · 검색은 짝 파일 색인으로 이것까지 찾는다 · 잡음 {sum(noise.values()):,}개는 색인에서도 뺌", ""]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    idx = [f"# km tag index v1\tsource_vault={source_vault}\tgenerated={now}\tcolumns=tag,count,dict_aliases"]
    idx += [f"{tag}\t{n}\t{','.join(dict_aliases(tag, groups))}" for tag, n in kept]
    for path, body in ((args.out, "\n".join(lines)), (index_path, "\n".join(idx) + "\n")):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, path)
    summary = {"status": "ok", "out": args.out, "index": index_path, "source_vault": source_vault,
               "total_tags": len(counts), "indexed_tags": len(kept), "noise": noise, "source": source,
               "categories": {c: len(cats[c]) for c in CATEGORIES}, "rest": rest, "synonym_groups": len(groups)}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


# ── suggest ───────────────────────────────────────────────────────────────
def read_map(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            text = nfc(f.read())
    except OSError as e:
        die("map_read_failed", detail=str(e))
    entries, order, cat = [], [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cat = line[3:].strip()
            if cat not in order:
                order.append(cat)
            continue
        m = LINE.match(line)
        if m and cat:
            al = m.group(3).strip()
            entries.append({"tag": m.group(1), "count": int(m.group(2)), "category": cat,
                            "aliases": [] if al in ("", "-") else [a.strip() for a in al.split(", ") if a.strip()]})
    return entries, order


def read_index(map_path, map_entries):
    """짝 파일(전체 색인)이 있으면 그것으로 · 없으면 지도 줄만(4판 첫 꼴)."""
    path = os.path.splitext(map_path)[0] + INDEX_SUFFIX
    by_tag = {e["tag"]: e for e in map_entries}
    if not os.path.isfile(path):
        return map_entries, False
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = nfc(line.rstrip("\n")).split("\t")
            if len(parts) < 2:
                continue
            tag, n = parts[0], int(parts[1] or 0)
            dal = [a for a in (parts[2].split(",") if len(parts) > 2 else []) if a]
            known = by_tag.get(tag)
            if known:
                out.append(known)
                continue
            ns, _ = split_ns(tag)
            out.append({"tag": tag, "count": n, "category": (ns + "/") if ns else CAT_REST, "aliases": dal})
    return out, True


def word_variants(w):
    """원형 + 한글 조사 뗀 꼴(줄기 2자+) — 둘 중 더 잘 맞는 쪽을 쓴다."""
    out = [w]
    if re.search(r"[가-힣]$", w):
        for j in JOSA:
            if w.endswith(j) and len(w) - len(j) >= 2:
                out.append(w[: -len(j)])
                break
    return out


def words(value):
    out = []
    for w in nfc(value or "").split():
        w = norm(w.strip(EDGE_PUNCT))
        if len(w) >= 2 and w not in out:
            out.append(w)
    return out


def same(a, b):
    """같은 낱말: 대소문자·#·구분자 무시(norm 뒤) · 끝 s 하나 무시."""
    return a == b or a + "s" == b or a == b + "s"


def prepare(entry):
    tag = entry["tag"]
    full = norm(tag)
    last = norm(tag.rsplit("/", 1)[-1])
    base = norm(split_ns(tag)[1])
    exact = {full, last, base, full.replace("-", ""), last.replace("-", "")}
    alias = {norm(a) for a in entry["aliases"]} | {norm(a).replace("-", "") for a in entry["aliases"]}
    alias -= exact
    toks = [t for t in re.split(r"[-/]", full) if t]
    return exact, alias, toks, [[t for t in re.split(r"[-/]", norm(a)) if t] for a in entry["aliases"]]


def contiguous(needle, hay):
    n = len(needle)
    for i in range(len(hay) - n + 1):
        if all(same(needle[j], hay[i + j]) if j == n - 1 else needle[j] == hay[i + j] for j in range(n)):
            return True
    return False


class Index:
    """정확·별칭·낱말 조각을 거꾸로 찾는 표 — 태그 1만 개도 낱말마다 표 몇 번 보기로 끝난다(전부 훑기 ❌)."""

    def __init__(self, entries):
        self.entries = entries
        self.preps = []
        self.exact, self.alias, self.tok = {}, {}, {}
        for i, e in enumerate(entries):
            prep = prepare(e)
            self.preps.append(prep)
            for x in prep[0]:
                self.exact.setdefault(x, set()).add(i)
            for x in prep[1]:
                self.alias.setdefault(x, set()).add(i)
            for t in set(prep[2] + [t for at in prep[3] for t in at]):
                self.tok.setdefault(t, set()).add(i)

    @staticmethod
    def forms(term):
        out = {term, term + "s"}
        if term.endswith("s") and len(term) > 1:
            out.add(term[:-1])
        return out

    def tiers(self, term):
        """term → {태그 번호: 단} · 3 정확 · 2 별칭 · 1 단어 경계 부분(조각 3자+ · 낱말 경계만)."""
        found = {}
        for x in self.forms(term):
            for i in self.exact.get(x, ()):
                found[i] = 3
        for x in self.forms(term):
            for i in self.alias.get(x, ()):
                found.setdefault(i, 2)
        if len(term.replace("-", "")) >= 3:
            need = [t for t in term.split("-") if t]
            cands = set()
            first = need[0] if len(need) > 1 else None
            for x in ({first} if first else self.forms(need[0])):
                cands |= self.tok.get(x, set())
            for i in cands:
                if i in found:
                    continue
                prep = self.preps[i]
                if contiguous(need, prep[2]) or any(contiguous(need, at) for at in prep[3]):
                    found[i] = 1
        return found


def compounds(ws):
    """이웃한 낱말 2·3개를 이어 붙인 꼴(- 와 붙여 쓰기) → (이은 꼴, 낱말 위치들)."""
    out = []
    for size in (2, 3):
        for i in range(len(ws) - size + 1):
            part = ws[i:i + size]
            out.append(("-".join(part), list(range(i, i + size))))
            out.append(("".join(part), list(range(i, i + size))))
    return out


def word_tiers(index, ws):
    """낱말마다 태그별 가장 높은 단 — 이웃 낱말을 이은 꼴이 맞으면 그 낱말들 모두 그 단.
    돌려주는 것: {태그 번호: ([단…], [맞은 꼴…])}"""
    out = {}

    def put(i, pos, t, via):
        best, vias = out.setdefault(i, ([0] * len(ws), [""] * len(ws)))
        if t > best[pos]:
            best[pos], vias[pos] = t, via

    for pos, w in enumerate(ws):
        for v in word_variants(w):
            for i, t in index.tiers(v).items():
                put(i, pos, t, v)
    for term, poss in compounds(ws):
        for i, t in index.tiers(term).items():
            for pos in poss:
                put(i, pos, t, term)
    return out


def rank(index, kw, extra):
    kt, et = word_tiers(index, kw), word_tiers(index, extra)
    ranked = []
    for i in set(kt) | set(et):
        kb, kv = kt.get(i, ([0] * len(kw), [""] * len(kw)))
        eb, ev = et.get(i, ([0] * len(extra), [""] * len(extra)))
        score = sum(kb) + sum(eb)
        if not score:
            continue
        key = (sum(1 for t in kb if t == 3), sum(1 for t in kb if t == 2), sum(1 for t in kb if t == 1), sum(eb))
        why = [f"{w}→{TIER[t]}({v})" for w, t, v in zip(kw, kb, kv) if t]
        why += [f"{w}→{TIER[t]}({v})·원문" for w, t, v in zip(extra, eb, ev) if t]
        covered = [w for w, t in zip(kw, kb) if t]
        ranked.append((key, score, index.entries[i], covered, " · ".join(why)))
    return ranked


def suggest(args):
    map_entries, order = read_map(args.map)
    entries, indexed = read_index(args.map, map_entries)
    top = max(1, args.top)
    kw = words(args.keywords)
    extra = [w for w in words(args.query) if w not in kw]
    if not kw:
        kw, extra = extra, []
    by_fold = {fold(e["tag"]): e for e in entries}
    result = {"tags": [], "ambiguous": False, "ambiguity": "none", "menu": {}, "keywords": kw + extra,
              "index": "full" if indexed else "map-only", "searched": len(entries)}
    scores = {}
    if args.pick and args.pick.strip():
        picked, rejected = [], []
        for name in re.split(r"[\s,]+", nfc(args.pick).strip()):
            name = name.strip(EDGE_PUNCT).lstrip("#")
            if not name:
                continue
            e = by_fold.get(fold(name))
            if e and e not in picked:
                picked.append(e)
            elif not e:
                rejected.append("#" + name)
        result["picked"] = True
        result["rejected"] = rejected
        result["tags"] = [{"tag": "#" + e["tag"], "count": e["count"], "category": e["category"],
                           "score": 0, "why": "pick(메뉴에서 고름)"} for e in picked[:top]]
        if not picked:
            result["ambiguous"], result["ambiguity"] = True, "no_match"
    else:
        ranked = rank(Index(entries), kw, extra) if kw else []
        for _, sc, e, _, _ in ranked:
            scores[e["tag"]] = sc
        ranked.sort(key=lambda r: ([-x for x in r[0]], -r[2]["count"], fold(r[2]["tag"]), r[2]["tag"]))
        result["tags"] = [{"tag": "#" + e["tag"], "count": e["count"], "category": e["category"],
                           "score": s, "why": why} for _, s, e, _, why in ranked[:top]]
        # partial = 최고 순위 태그가 --keywords 중 일부만 맞음(물음 원문 낱말은 보탬일 뿐 판정에 넣지 않는다)
        if not ranked:
            result["ambiguity"] = "no_match"
        elif len(ranked[0][3]) < len(kw):
            result["ambiguity"] = "partial_match"
        elif len(ranked) > top and ranked[top - 1][0] == ranked[top][0]:
            result["ambiguity"] = "tie_at_cut"
        result["ambiguous"] = result["ambiguity"] != "none"
    if result["ambiguous"]:
        for c in order:
            inside = [e for e in map_entries if e["category"] == c]
            inside.sort(key=lambda e: (-scores.get(e["tag"], 0), -e["count"], fold(e["tag"]), e["tag"]))
            result["menu"][c] = ["#" + e["tag"] for e in inside[:MENU_MAX]]
    print(json.dumps(result, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser(description="km 추천 태그 지도")
    sub = p.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--in", "--counts-json", dest="counts_json",
                   help="obsidian-cli `tags counts format=json` 출력 파일(없으면 --cli 로 직접 받음)")
    b.add_argument("--cli", default=os.environ.get("OBSIDIAN_CLI") or CLI_DEFAULT)
    b.add_argument("--vault", default="", help="CLI 로 직접 받을 때 맨 앞 vault=<이름>")
    b.add_argument("--source-vault", default="", help="머리에 적을 «만든 볼트»(파일로 받을 때 필수 권장)")
    b.add_argument("--dict")
    b.add_argument("--flat-min", type=int, default=10)
    b.add_argument("--flat-top", type=int, default=150)
    s = sub.add_parser("suggest")
    s.add_argument("--map", required=True)
    s.add_argument("--keywords", default="")
    s.add_argument("--query", default="")
    s.add_argument("--top", type=int, default=3)
    s.add_argument("--pick", default="", help="메뉴에서 고른 태그(공백·쉼표 구분) — 색인에 있는 것만 받는다")
    args = p.parse_args()
    return build(args) if args.mode == "build" else suggest(args)


if __name__ == "__main__":
    sys.exit(main())
