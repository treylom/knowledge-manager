#!/usr/bin/env python3
"""km:search Tier 2 단계 대본(6.2판 · 2026-11-11) — 볼트 확인 · 구조 문서 · VS · 추천 태그 · CLI 검색 · 1단 확장.

명령 글(commands/search.md)은 이 대본을 «한 줄»로 부르기만 한다. 5b판에서는 이 단계들이 약 230줄 셸 블록이었고,
실제 모델이 그 블록을 줄여 다시 써서 VS·추천 태그·1단 확장 표지가 0/3 이었다(벤치 첫 점검 3실행 · 11-11).

부르는 꼴(명령 글과 같음):
  python3 -I -B km_cli_stage.py --vault-path P --vault-name N --cli C --vault-mode M --keywords K --query Q
                                [--target-status S] [--tier1-top "a|b"] [--tier1-paths "p1|p2|p3"] [--tag-map F] [--tag-pick "#a #b"] [--ext-notes "a|b"]
  · 인자는 전부 선택이다(빠져도·모르는 인자가 와도 돈다). 표준 라이브러리만 쓴다. 임시 파일을 쓰지 않는다.
  · --tag-pick 가 있으면 «추천 태그 고른 회»만 돈다(볼트 확인 1 + 태그 검색 ≤2).

지키는 것:
  · obsidian-cli 호출 = [cli, "vault=<이름>", 명령, …] — 볼트 인자는 «맨 앞»(뒤에 두면 무시된다 · 11-11 실측) · 이름이 비면 인자를 뺀다.
  · 호출마다 시한 KM_CLI_TIMEOUT(기본 20초) · 전체 마감 KM_CLI_BUDGET(기본 90초) · 시한 초과 2회면 남은 CLI 호출 안 함.
    시한이 되면 프로세스 묶음째 죽인다(start_new_session + killpg).
  · CLI 호출 합계 ≤ 14 = 볼트 확인 1 + 검색 ≤2(재시도 1) + 추천 태그 ≤3 + 확장 ≤8.
  · 6.1판: CLI 글자 검색이 «rc 0 + 빈 출력»이거나 «시한 초과»면 같은 인자로 1회 다시 부른다(검색 칸 2개 안 · 둘 중 하나만 1회).
    시한 초과 재시도는 남은 마감(KM_CLI_BUDGET − 지난 시간)이 호출 시한(KM_CLI_TIMEOUT) 이상일 때만 — 모자라면 안 부르고
    CLI_STATE 줄에 retry=0(재시도 예산 없음). obsidian-cli 가 드물게(≈3/110) 첫 시도에 멈췄다가 다시 부르면 답하는 꼴(벤치 첫 점검 1/3).
  · 앞머리 vault info=path: 경로 = front(이름 줌)/active(이름 없음) · «Vault not found.» = 이번 실행만 이름 빼고 active
    · 그 밖(403·오류·빈 출력·시한) = unknown 으로 찍고 계속 간다(이름 그대로).
  · stdin = 빈 파이프(stdin=PIPE · communicate 가 바로 닫음). 11-11 실측: 상속·/dev/null·빈 파이프 세 꼴 모두 출력 같음
    (vault info·search·backlinks·properties·links) · 단 바깥 stdin 이 «닫힌»(fd 0 없음) 채 상속하면 CLI 가 0 B 를 낸다
    (verifier 재현) → 상속을 버리고 빈 파이프로 고정. 바깥 stdin 이 닫혀도 1403 B 그대로(실측). 11-06 «/dev/null 이면 0 B» 는
    오늘 재현 안 됨(각 1회 관측) — 그날 원인은 닫힌 stdin 이었을 수 있다(잠정).
  · 6.2판 ①: 앞 단계(볼트 확인·추천 태그) 시한 초과 2회로 «남은 호출 중단»이 걸려도 CLI 글자 검색은 전체 마감 안이면 최소 1회
    + 시한 초과면 다시 1회(6.1판 재시도 규칙 그대로 · 남은 마감 ≥ 호출 시한) · 확장 단계는 중단 그대로.
  · 6.2판 ②: 추천 태그 검색은 시한에 안 걸린 호출만 센다 — 전부 시한이면 TAG_REC_STATE=timeout · KM_STAGES tagrec=timeout:0
    (섞이면 used(<시한 아닌 수>)).
  · 6.2판 ③: 같은/다른 볼트 = 대본이 다시 확인 — --tier1-paths(Tier 1 결과 source_note 상위 · «|» 구분)의 앞 N건
    (KM_VMODE_TOP · 기본 3 · 볼트 상대 경로만 셈: 절대경로·«..»는 뺌 · 앞 «./» 뗌)을 VAULT_PATH 아래에서 파일로 확인 →
    하나라도 있으면 same · 0건이면 other · 대본 값이 --vault-mode(모델 값)를 이긴다 → VAULT_MODE_CHECK=<값>(k/n) model=<모델값>
    → VAULT_MODE=<값> 1줄. 셀 경로가 없거나 VAULT_PATH 가 없으면 모델 값 그대로(KM_STAGES vmode=model(<모델값>)).
    덧: 1단 확장 노트 가운데 같은 경로 목록에서 «볼트에 없음»으로 확인된 이름은 부르지 않는다(EXT_DROP=<n> 1줄 · 확인 못 한 이름은 그대로).
  · VAULT_MODE=other(확인값 우선) → STRUCT_STATE=skip(other) 1줄 + KM_STAGES 1줄(로컬 읽기·CLI 0 · 확인했으면 VAULT_MODE_CHECK 1줄 더).
  · 출력 ≤ 80줄 · stderr 잡음 0 · 무슨 일이 나도 마지막 줄 = KM_STAGES · 끝 코드 0.

KM_STAGES 칸(순서 고정): vault struct hubs vs tagrec cli ext prop bl ln tag type calls timeouts
  + 6판 덧칸(timeouts 뒤): c_vault c_search c_props c_bl c_ln c_tag mode run
  + 6.1판 덧칸(run 바로 앞): retry = CLI 글자 검색을 다시 부른 수(0|1 · 다시 부른 호출도 calls·c_search·timeouts 에 그대로 셈)
  + 6.2판 덧칸(retry 뒤 · run 앞): cli_try = CLI 글자 검색을 실제로 보낸 수(0|1|2 · 재시도 포함)
        · vmode = same(k/n)|other(k/n)(대본 확인 · k = 볼트에 있는 수 · n = 본 수)|model(<모델값>)(확인 못 함 · 빈 값 = empty)
  prop = 속성을 읽은 노트 수 · bl = 역링크 «건수 합»(CLI 가 준 목록 길이) · ln = 정방향 링크 «건수 합»
  tag = [tag:#…] 줄 수 · type = [type:…]/[status:…] 줄 수 · calls = 실제 CLI 호출 수 · timeouts = 시한 초과 수
  c_* = 실제로 보낸 CLI 명령 종류별 수(c_vault = vault info · c_search = tag: 아닌 search · c_tag = query=tag: search
        · c_props = properties · c_bl = backlinks · c_ln = links) — 합 = calls · 중계가 받은 명령 수와 짝지어 맞춰 본다
  mode = main|pick · run = 실행마다 새로 뽑는 16진 10자(지어낼 수 없는 값) — 5판 표지 줄 끝에도 같은 run= 을 붙인다.
"""
import importlib.util
import json
import math
import os
import re
import secrets
import signal
import subprocess
import sys
import time
import unicodedata

sys.dont_write_bytecode = True  # -B 를 빼고 불러도 __pycache__ 를 만들지 않는다

HERE = os.path.dirname(os.path.abspath(__file__))
CLI_DEFAULT = "/Applications/Obsidian.app/Contents/MacOS/obsidian-cli"
TAG_MAP_NAME = "000-START-HERE/TAG-Map.md"
MAX_LINES = 80
CAP = {"vault": 1, "search": 2, "tagrec": 3, "ext": 8}
CALL_CAP = sum(CAP.values())  # 14


def nfc(s):
    return unicodedata.normalize("NFC", s or "")


def load_module(name):
    """-I 는 대본 폴더를 sys.path 에 넣지 않는다 → 같은 폴더의 파일을 경로로 직접 싣는다(없으면 None)."""
    path = os.path.join(HERE, name + ".py")
    if not os.path.isfile(path):
        return None
    try:
        spec = importlib.util.spec_from_file_location("km_stage_" + name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


def parse_args(argv):
    """argparse 대신 손으로 받는다 — '-' 로 시작하는 값·모르는 인자·빠진 값에도 죽지 않게."""
    keys = {"--vault-path": "vault_path", "--vault-name": "vault_name", "--cli": "cli", "--vault-mode": "vault_mode",
            "--keywords": "keywords", "--query": "query", "--target-status": "target_status",
            "--tier1-top": "tier1_top", "--tier1-paths": "tier1_paths", "--tag-map": "tag_map", "--graphrag-state": "graphrag_state", "--tag-pick": "tag_pick", "--ext-notes": "ext_notes"}
    a = {v: "" for v in keys.values()}
    unknown = []
    i = 0
    while i < len(argv):
        k = argv[i]
        if "=" in k and k.split("=", 1)[0] in keys:
            k, v = k.split("=", 1)
            a[keys[k]] = v
            i += 1
        elif k in keys:
            a[keys[k]] = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
        else:
            unknown.append(k)
            i += 1
    # 줄바꿈·탭 = 빈칸(표지 줄이 물리적으로 쪼개지지 않게)
    return {k: re.sub(r"[\r\n\t\v\f]+", " ", nfc(v)).strip() for k, v in a.items()}, unknown


class Runner:
    """obsidian-cli 호출 — 볼트 인자 맨 앞 · 시한 · 상한 · 기록."""

    def __init__(self, cli, vault_name):
        self.cli = cli
        self.vault = vault_name
        self.calls = 0
        self.timeouts = 0
        self.used = {k: 0 for k in CAP}
        self.kind = {k: 0 for k in ("vault", "search", "props", "bl", "ln", "tag")}
        try:
            self.timeout = max(1.0, float(os.environ.get("KM_CLI_TIMEOUT", "20")))
            if not math.isfinite(self.timeout):
                raise ValueError
            self.timeout = min(self.timeout, 600.0)
        except ValueError:
            self.timeout = 20.0
        try:
            self.budget = max(5.0, float(os.environ.get("KM_CLI_BUDGET", "90")))
            if not math.isfinite(self.budget):
                raise ValueError
            self.budget = min(self.budget, 3600.0)
        except ValueError:
            self.budget = 90.0
        self.t0 = time.monotonic()
        self.stopped = ""  # 비어 있지 않으면 더 부르지 않는다(사유)
        self.retry = 0  # CLI 글자 검색 재시도 수(6.1판)
        self.cli_try = 0  # CLI 글자 검색을 실제로 보낸 수(6.2판)

    def left(self):
        return self.budget - (time.monotonic() - self.t0)

    def can(self, stage, force=False):
        """force = 시한 2회 중단만 넘는다(6.2판 · CLI 글자 검색 전용) — 마감·상한은 그대로 지킨다."""
        if self.stopped and not (force and self.stopped == "timeouts"):
            return False
        if self.used[stage] >= CAP[stage] or self.calls >= CALL_CAP:
            return False
        if time.monotonic() - self.t0 >= self.budget - 1:
            self.stopped = "budget"
            return False
        return True

    def run(self, stage, *args, force=False):
        """(rc, stdout 글) · 못 부르면 (None, "") · 시한이면 (124, "")."""
        if not self.can(stage, force):
            return None, ""
        cmd = [self.cli] + (["vault=" + self.vault] if self.vault else []) + list(args)
        self.calls += 1
        self.used[stage] += 1
        c0 = args[0] if args else ""
        if c0 == "search":
            k = "tag" if any(str(x).startswith("query=tag:") for x in args) else "search"
        else:
            k = {"vault": "vault", "properties": "props", "backlinks": "bl", "links": "ln"}.get(c0, "search")
        self.kind[k] += 1
        left = self.budget - (time.monotonic() - self.t0)
        tmo = max(1.0, min(self.timeout, left))
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
        except OSError:
            return 127, ""
        try:
            out, _ = p.communicate(input=b"", timeout=tmo)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                p.communicate(timeout=2)
            except Exception:
                pass
            self.timeouts += 1
            if self.timeouts >= 2 and not self.stopped:
                self.stopped = "timeouts"
            return 124, ""
        return p.returncode, nfc(out.decode("utf-8", "replace"))


def js(s):
    try:
        return json.loads(s)
    except Exception:
        return None


def paths_of(raw):
    """CLI JSON 목록 → 경로 목록(TAG-Map 자체는 뺌) · 목록이 아니면 None."""
    r = js(raw)
    if not isinstance(r, list):
        return None
    out = []
    for x in r:
        p = x if isinstance(x, str) else (str(x.get("file") or x.get("path") or "") if isinstance(x, dict) else "")
        if p and not p.endswith(TAG_MAP_NAME) and p not in out:
            out.append(p)
    return out


def note_name(p):
    return os.path.splitext(os.path.basename(p))[0]


def first_line(s, n=80):
    s = (s or "").strip().splitlines()
    return s[0][:n] if s else ""


RUN_ID = secrets.token_hex(5)


class Out:
    def __init__(self):
        self.lines = []

    def __call__(self, s=""):
        for ln in str(s).split("\n"):
            self.lines.append(ln)

    def mark(self, s):
        """5판 표지 줄 — 끝에 이번 실행의 run= 을 붙인다(손으로 찍은 표지와 가르기)."""
        self.lines.append("%s run=%s" % (s, RUN_ID))


def check_vmode(a):
    """③ 같은/다른 볼트 다시 확인 → (vmode 칸, 쓸 모드, 볼트에 없다고 확인된 경로 이름 집합 · 있다고 확인된 이름 집합)."""
    model = a["vault_mode"]
    vp = a["vault_path"]
    try:
        top = int(os.environ.get("KM_VMODE_TOP", "3"))
    except ValueError:
        top = 3
    top = min(max(top, 1), 10)
    seen, cand = set(), []
    for x in a["tier1_paths"].split("|"):
        x = x.strip()
        while x.startswith("./"):
            x = x[2:]
        if not x or os.path.isabs(x) or ".." in x.replace("\\", "/").split("/") or x in seen:
            continue
        seen.add(x)
        cand.append(x)
    absent, present = set(), set()
    if not (vp and os.path.isdir(vp) and cand):
        return "model(%s)" % (model or "empty"), model, absent, present
    root = os.path.realpath(vp)
    for x in cand:  # 확장 노트 걸러내기에는 받은 경로 전부(상한 10)를 쓴다 · 판정은 앞 N건만
        f = os.path.realpath(os.path.join(root, x))
        ok = os.path.isfile(f) and os.path.commonpath([root, f]) == root
        (present if ok else absent).add(x)
        if len(present) + len(absent) >= 10:
            break
    k = sum(1 for x in cand[:top] if x in present)
    n = len(cand[:top])
    mode = "same" if k else "other"
    return "%s(%d/%d)" % (mode, k, n), mode, absent, present


def stage_vault(o, R, vault_path, st):
    """① 볼트 확인. st['vault'] = front|active|unknown."""
    if not R.cli_ok:
        o.mark("CLI_VAULT=unknown (no-cli)")
        st["vault"] = "unknown"
        return
    name = R.vault
    rc, out = R.run("vault", "vault", "info=path")
    out_s = out.strip()
    if out_s == "Vault not found.":
        o.mark("CLI_VAULT=active (not-found:%s)" % name)
        R.vault = ""  # 이번 실행만 이름을 뺀다
        st["vault"] = "active"
    elif rc == 0 and out_s and len(out_s.splitlines()) == 1 and out_s.startswith("/"):
        st["vault"] = "front" if name else "active"
        o.mark("CLI_VAULT=%s (%s)" % (out_s, st["vault"]))
        if vault_path:
            try:
                if os.path.realpath(out_s) != os.path.realpath(vault_path):
                    o("⚠ CLI 볼트 ≠ VAULT_PATH (%s ≠ %s) — 파일 읽기와 CLI 숫자가 다른 볼트에서 온다" % (out_s, vault_path))
            except Exception:
                pass
    else:
        why = "timeout" if rc == 124 else ("rc=%s" % rc if rc else "not-a-path")
        o.mark("CLI_VAULT=unknown (%s)" % why)  # 403·오류 = unknown · 이름 그대로 · CLI 단계는 계속
        st["vault"] = "unknown"


def stage_struct(o, a, st, guard):
    """② 구조 문서 3개 + MOC-Map 경로 점수(Phase 0.4)."""
    sd = os.path.join(a["vault_path"], "000-START-HERE") if a["vault_path"] else ""
    miss = [f for f in ("START-HERE", "VAULT-STRUCTURE", "MOC-Map") if not (sd and os.path.isfile(os.path.join(sd, f + ".md")))]
    st["struct"] = 3 - len(miss)
    o.mark("STRUCT_DOCS=%d/3 missing=[%s]" % (st["struct"], " ".join(miss)))
    kw = a["keywords"] or a["query"]
    res = None
    if guard is not None and sd:
        try:
            res = guard.map_routes(os.path.join(sd, "MOC-Map.md"), kw)
        except Exception:
            res = None
    amb = 0
    if isinstance(res, dict) and res.get("status") == "ok":
        st["hubs"] = res.get("hub_count") or 0
        st["route"] = "ok"
        o.mark("ROUTE_SCAN=ok ROUTE_HUB_COUNT=%d" % st["hubs"])
        amb = 1 if res.get("ambiguous") else 0
    else:
        st["route"] = "unmeasured"
        o.mark("ROUTE_SCAN=unmeasured ROUTE_HUB_COUNT=unmeasured")
    if a["target_status"] == "ambiguous":
        amb = 1
    o.mark("ROUTE_AMBIGUOUS=%d" % amb)
    if isinstance(res, dict) and res.get("status") == "ok":
        hubs = [h.get("path", "") for h in res.get("hubs") or []]
        o("ROUTE_HUBS=" + " | ".join(h for h in hubs if h))
        o("MAP_RESULT=" + json.dumps(res, ensure_ascii=False))
    if amb:
        o("→ ROUTE_AMBIGUOUS=1 — Phase 0.4-D 지도 하강(menu) 블록을 돈다")


def stage_vs(o, a, st):
    """③ VAULT-STRUCTURE 폴더 역할 줄 ≤8 — 그 파일 1개만 읽는다."""
    f = os.path.join(a["vault_path"], "000-START-HERE", "VAULT-STRUCTURE.md") if a["vault_path"] else ""
    if not (f and os.path.isfile(f)):
        st["vs_state"] = "absent"
        o.mark("VS_STATE=absent")
        return
    kw = [w.casefold() for w in (a["keywords"] or a["query"]).split() if len(w) >= 2]
    try:
        lines = nfc(open(f, encoding="utf-8").read()).splitlines()
    except Exception:
        lines = []
    if lines and lines[0].strip() == "---":
        end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), 0)
        lines = lines[end + 1:]
    out = []
    for l in lines:
        s = l.strip()
        if not s or s.startswith("```"):
            continue
        if not re.search(r"[\w.가-힣-]/|\b\d{3}-|[├└]──", s):
            continue
        if kw and any(k in s.casefold() for k in kw):
            out.append("[vs] " + s[:200])
        if len(out) >= 8:
            break
    st["vs"] = len(out)
    if out:
        for x in out:
            o(x)
        o("→ [vs] 줄에 나온 폴더를 CLI 결과 경로 추리기·path_hint 에 쓴다")
        st["vs_state"] = "ok(%d줄)" % len(out)
    else:
        st["vs_state"] = "none"
    o.mark("VS_STATE=" + st["vs_state"])


def find_tag_map(a):
    for p in (os.environ.get("KM_TAG_MAP", ""), a["tag_map"],
              os.path.join(a["vault_path"], TAG_MAP_NAME) if a["vault_path"] else ""):
        if p and os.path.isfile(p):
            return p
    return ""


def stage_tagrec(o, a, R, st, pick_run):
    """④ 추천 태그 — TAG-Map 에서 ≤3 고르고 tag: 검색(태그마다 ≤3 줄). 애매하면 첫 회 1개 + 메뉴."""
    tm_py = os.path.join(HERE, "km_tag_map.py")
    tag_map = find_tag_map(a)
    state, n, hits, n_to = "", 0, 0, 0
    if a["vault_mode"] == "other":
        state = "skipped(other)"
    elif not (a["keywords"] or a["query"] or a["tag_pick"]):
        state = "skipped(none)"
    elif not tag_map:
        state = "absent"
        o("TAG-Map 없음(KM_TAG_MAP·볼트 000-START-HERE 둘 다 · 짝 색인 TAG-Map.tags.tsv 는 같은 폴더에) — 검색 밖에서 만드는 명령은 km_tag_map.py build(보고서 «TAG-Map 명령»)")
    elif not os.path.isfile(tm_py):
        state = "skipped(no-script)"
    elif not R.cli_ok:
        state = "skipped(no-cli)"
    plan = None
    if not state:
        try:
            r = subprocess.run([sys.executable, "-I", "-B", tm_py, "suggest", "--map", tag_map, "--keywords", a["keywords"],
                                "--query", a["query"], "--top", "3", "--pick", a["tag_pick"]],
                               stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
            plan = js(r.stdout.decode("utf-8", "replace"))
        except Exception:
            plan = None
        if not isinstance(plan, dict):
            state = "absent"
            o("TAG-Map 을 읽지 못함 — 검색 밖에서 km_tag_map.py build 로 다시 만든다")
    if not state:
        amb = bool(plan.get("ambiguous"))
        why = plan.get("ambiguity") or "none"
        take = 2 if plan.get("picked") else (1 if amb else 3)
        tags = (plan.get("tags") or [])[:take]
        if (plan.get("index") or "?") != "full":
            o("⚠ 짝 색인(TAG-Map.tags.tsv) 없음 — 지도 상위 목록만으로 찾음(낮은 빈도 태그는 못 찾는다 · 두 파일을 같은 폴더에)")
        o("추천 태그(%s · 색인 %s): %s" % (why, plan.get("index") or "?", " ".join(
            "%s(%s · %s · %s)" % (t.get("tag"), t.get("count"), t.get("category"), t.get("why")) for t in tags)))
        for x in plan.get("rejected") or []:
            o("목록 밖이라 버림: " + str(x))
        for t in tags:
            name = str(t.get("tag") or "").lstrip("#")
            if not name:
                continue
            rc, raw = R.run("tagrec", "search", "query=tag:" + name, "format=json", "limit=20")
            if rc is None:
                break
            if rc == 124:  # 시한 초과 = 찾은 것으로 안 센다(6.2판)
                n_to += 1
                continue
            n += 1
            ps = paths_of(raw) or []
            for p in ps[:3]:
                o("[tag-rec:#%s] %s" % (name, p))
            hits += len(ps[:3])
        if amb and not plan.get("picked"):
            shown = 0
            for c, ts in (plan.get("menu") or {}).items():
                if ts and shown < 4:
                    o("[tag-menu:%s] %s" % (c, " ".join(ts[:15])))
                    shown += 1
            o("→ 애매함(%s) — 위 메뉴에서 물음에 맞는 태그 ≤2 를 골라(이미 찾은 태그 말고 · 목록 밖 이름 ❌) 맨 앞 값 줄에 TAG_PICK=\"#a #b\" 만 더 적어 같은 블록을 1회 더" % why)
        state = "used(%d)" % n if n else ("timeout" if n_to else ("skipped(ambiguous)" if amb else "skipped(none)"))
    st["tagrec"], st["tagrec_k"] = state, n
    o.mark("TAG_REC_HITS=%d" % hits)
    o.mark("TAG_REC_STATE=" + state)


def cli_query(q, cq):
    if cq is not None:
        try:
            return cq.sanitize(q)
        except Exception:
            pass
    return re.sub(r'([^\s"]):(\s|\)|$)', r"\1\2", q)


def stage_cli(o, a, R, st, cq):
    """⑤ CLI 검색 — 질의 = 핵심어 앞 2개(비면 원문) · 0 B(rc 0) 또는 시한 초과(남은 마감 ≥ 호출 시한)면 같은 인자로 1회 재시도."""
    kws = a["keywords"].split()
    q = " ".join(kws[:2]) or a["query"]
    state, paths, no_retry = "absent", [], ""
    if R.cli_ok and q:
        args = ("search", "query=" + cli_query(q, cq), "format=json", "limit=50")
        pre_stop = R.stopped  # 앞 단계 시한 2회 중단이어도 글자 검색은 최소 1회(6.2판 · 마감·상한은 지킴)
        rc, raw = R.run("search", *args, force=True)
        if rc is not None:
            R.cli_try += 1
        elif pre_stop:
            no_retry = "마감 중단" if R.stopped == "budget" else "시한 초과 %d회 중단" % R.timeouts
        def again():  # 실제로 보낸 재시도만 센다(마감 문턱에 막혀 못 부르면 retry 그대로 · 첫 결과 유지 · verifier 6.1)
            rc2, raw2 = R.run("search", *args, force=True)
            if rc2 is None:
                return rc, raw
            R.retry += 1
            R.cli_try += 1
            return rc2, raw2
        if rc == 0 and not raw.strip():
            rc, raw = again()
        elif rc == 124:  # 시한 초과 → 남은 마감이 호출 시한 이상일 때만 같은 인자로 1회(6.1판)
            left = R.left()
            if R.stopped == "budget":
                no_retry = "마감 중단"
            elif left < R.timeout:
                no_retry = "재시도 예산 없음"
                o("CLI_OUT=(시한 %ds 초과 · 재시도 예산 없음 — 남은 %.1f초 < 시한 %ds)" % (int(R.timeout), max(0.0, left), int(R.timeout)))
            else:
                rc, raw = again()
                if not R.retry:
                    no_retry = "마감 중단"
        ps = paths_of(raw)
        if rc is None:
            state = "error"
        elif ps is None:
            state = "empty" if "No matches" in raw else "error"
            if raw.strip():
                o("CLI_OUT=" + first_line(raw))
            elif rc == 124 and no_retry != "재시도 예산 없음":
                o("CLI_OUT=(시한 %ds 초과%s)" % (int(R.timeout), " · 재시도 뒤" if R.retry else ""))
        else:
            paths = ps
            state = "ok" if ps else "empty"
    elif R.cli_ok:
        state = "empty"
    st["cli"], st["cli_n"], st["cli_paths"] = state, len(paths), paths
    tail = " retry=%d" % R.retry if R.retry else (" retry=0(%s)" % no_retry if no_retry else "")
    o.mark("CLI_STATE=%s cli_hits=%d cli_q=%s%s" % (state, len(paths), q, tail))
    for p in paths[:10]:
        o("[cli] " + p)
    if len(paths) > 10:
        o("[cli] … 외 %d건(경로·제목으로 추린다)" % (len(paths) - 10))


def stage_ext(o, a, R, st, cq):
    """⑥ 1단 확장 — 노트 ≤2 마다 properties·backlinks·links, 태그 검색, 속성 좁히기(S4) · 호출 ≤8."""
    notes, src = [], "model"
    if a["ext_notes"]:
        notes = [x for x in re.split(r"[|\n]", a["ext_notes"]) if x.strip()][:2]
    if not notes and a["tier1_top"]:
        notes, src = [x for x in a["tier1_top"].split("|") if x.strip()][:2], "tier1"
    if not notes and st.get("cli_paths"):
        ps = [p for p in st["cli_paths"] if p.endswith(".md")]
        kw = [k.casefold() for k in (a["keywords"] or a["query"]).split() if len(k) >= 2]
        hit = [p for p in ps if any(k in note_name(p).casefold() for k in kw)]
        notes, src = [note_name(p) for p in (hit + [p for p in ps if p not in hit])[:2]], "cli"
    notes = [os.path.splitext(n.strip())[0] if n.strip().endswith(".md") else n.strip() for n in notes]
    gone = {note_name(x) for x in st.get("vm_absent", ())} - {note_name(x) for x in st.get("vm_present", ())}
    if src in ("model", "tier1") and gone:
        pool = [x for x in re.split(r"[|\n]", a["ext_notes"] if src == "model" else a["tier1_top"]) if x.strip()]
        pool = [os.path.splitext(x.strip())[0] if x.strip().endswith(".md") else x.strip() for x in pool]
        drop = [x for x in pool if x in gone]
        if drop:
            o("EXT_DROP=%d (볼트에 없음: %s)" % (len(drop), ", ".join(drop)[:120]))
            notes = [x for x in pool if x not in gone][:2]
    if not notes and st.get("cli_paths") and src != "cli":
        ps = [p for p in st["cli_paths"] if p.endswith(".md")]
        kw = [k.casefold() for k in (a["keywords"] or a["query"]).split() if len(k) >= 2]
        hit = [p for p in ps if any(k in note_name(p).casefold() for k in kw)]
        notes, src = [note_name(p) for p in (hit + [p for p in ps if p not in hit])[:2]], "cli"
    if not notes:
        src = "none"
    c = {"prop": 0, "bl": 0, "ln": 0, "tag": 0, "type": 0}
    tags, prop_kv = [], ""
    if not R.cli_ok:
        state = "skip(no-cli)"
    elif not notes:
        state = "skip(no-notes)"
    else:
        state = "done"
        for n in notes:
            rc, praw = R.run("ext", "properties", "file=" + n, "format=json")
            if rc is None:
                break
            p = js(praw)
            if isinstance(p, dict):
                c["prop"] += 1
                t = p.get("tags") or []
                tl = [t] if isinstance(t, str) else ([str(x) for x in t] if isinstance(t, list) else [])
                tl = [x.lstrip("#") for x in tl if x]
                o("[prop] %s — type=%s · tags=%s · aliases=%s" % (n, p.get("type") or p.get("kind") or "-", ",".join(tl[:5]) or "-", p.get("aliases") or "-"))
                for x in tl[:2]:
                    if x not in tags:
                        tags.append(x)
                if not prop_kv:
                    pk = "type" if p.get("type") else ("status" if p.get("status") else "")
                    if pk:
                        v = p.get(pk)
                        v = v[0] if isinstance(v, list) and v else v
                        if isinstance(v, str) and v.strip() and "]" not in v:
                            prop_kv = (pk, v.strip())
            else:
                o("[prop] %s — 속성 없음/읽기 실패" % n)
            rc, braw = R.run("ext", "backlinks", "file=" + n, "format=json")
            if rc is not None:
                b = js(braw)
                bl = [(x.get("file") or "") if isinstance(x, dict) else str(x) for x in b] if isinstance(b, list) else []
                c["bl"] += len(bl)
                o("[bl] %s — 역링크 %d건%s" % (n, len(bl), "" if isinstance(b, list) else " (CLI 목록 아님)"))
                for x in bl[:3]:
                    o("[bl] " + x)
            rc, lraw = R.run("ext", "links", "file=" + n)
            if rc is not None:
                ln = [l.strip() for l in lraw.splitlines() if l.strip().endswith(".md")]
                c["ln"] += len(ln)
                for x in ln[:3]:
                    o("[ln] " + x)
        # 확장 상한 8 = 노트 2 × 3 + 태그·속성 2 · 속성 좁히기([type:]/[status:] 를 내는 유일한 호출)를 먼저 남기고 태그 검색을 줄인다
        reserve = 1 if prop_kv else 0
        for t in tags[:2]:
            if CAP["ext"] - R.used["ext"] <= reserve:
                break
            rc, traw = R.run("ext", "search", "query=tag:" + t, "format=json", "limit=20")
            if rc is None:
                break
            for x in (paths_of(traw) or [])[:3]:
                o("[tag:#%s] %s" % (t, x))
                c["tag"] += 1
        if prop_kv:
            pk, pv = prop_kv
            pq = '[%s:"%s"]' % (pk, pv) if " " in pv else "[%s:%s]" % (pk, pv)
            k1 = ((a["keywords"] or a["query"]).split() or [""])[0]
            if k1:
                pq += " " + cli_query(k1, cq)
            rc, praw = R.run("ext", "search", "query=" + pq, "format=json", "limit=20")
            if rc is not None:
                for x in (paths_of(praw) or [])[:3]:
                    o("[%s:%s] %s" % (pk, pv, x))
                    c["type"] += 1
        if R.stopped:
            state = "partial(%s)" % R.stopped
    st["ext"], st["ext_calls"] = state, R.used["ext"]
    st.update(c)
    o.mark("EXT_STATE=%s ext_calls=%d EXT_SRC=%s" % (state, R.used["ext"], src))


def stages_line(st, R, run):
    kd = R.kind if R else {}
    return ("KM_STAGES vault=%s struct=%s hubs=%s vs=%s tagrec=%s:%s cli=%s:%s ext=%s:%s prop=%s bl=%s ln=%s tag=%s type=%s calls=%s timeouts=%s"
            " c_vault=%d c_search=%d c_props=%d c_bl=%d c_ln=%d c_tag=%d mode=%s retry=%d cli_try=%d vmode=%s run=%s"
            % (st.get("vault", "unknown"), "%s/3" % st["struct"] if isinstance(st.get("struct"), int) else st.get("struct", "skip"),
               st.get("hubs", "na"), st.get("vs", 0), st.get("tagrec", "skip"), st.get("tagrec_k", 0),
               st.get("cli", "skip"), st.get("cli_n", 0), st.get("ext", "skip"), st.get("ext_calls", 0),
               st.get("prop", 0), st.get("bl", 0), st.get("ln", 0), st.get("tag", 0), st.get("type", 0),
               R.calls if R else 0, R.timeouts if R else 0,
               kd.get("vault", 0), kd.get("search", 0), kd.get("props", 0), kd.get("bl", 0), kd.get("ln", 0), kd.get("tag", 0), run, R.retry if R else 0, R.cli_try if R else 0, st.get("vmode", "model(empty)"), RUN_ID))


def main(argv):
    o = Out()
    st = {}
    R = None
    run = "main"
    try:
        a, unknown = parse_args(argv)
        run = "pick" if a["tag_pick"] else "main"
        vm, mode_used, st["vm_absent"], st["vm_present"] = check_vmode(a)
        st["vmode"] = vm
        if not vm.startswith("model("):
            o.mark("VAULT_MODE_CHECK=%s model=%s → VAULT_MODE=%s" % (vm, a["vault_mode"] or "empty", mode_used))
        a["vault_mode"] = mode_used
        if a["vault_mode"] == "other":
            st.update(vault="skip", struct="skip", tagrec="skipped(other)")
            o.mark("STRUCT_STATE=skip(other)")
            return o, st, R, run
        if unknown:
            o("KM_STAGE_ARGS=모르는 인자 %d개 무시(%s)" % (len(unknown), " ".join(unknown)[:60]))
        if not a["vault_name"] and a["vault_path"]:
            a["vault_name"] = os.path.basename(a["vault_path"].rstrip("/"))
        cli = a["cli"] or os.environ.get("OBSIDIAN_CLI", "") or CLI_DEFAULT
        R = Runner(cli, a["vault_name"])
        R.cli_ok = os.path.isfile(cli) and os.access(cli, os.X_OK)
        cq = load_module("km_cli_query")
        def guard(name, fn, *fa):
            """한 단계가 예외로 죽어도 다음 단계·표지는 이어진다(그 단계 표지는 error 로)."""
            try:
                fn(*fa)
            except Exception as e:
                o("KM_STAGE_ERROR=%s:%s: %s" % (name, type(e).__name__, str(e)[:60]))
                dflt = {"vault": ("vault", "unknown", "CLI_VAULT=unknown (error)"),
                        "vs": ("vs_state", "error", "VS_STATE=error"),
                        "tagrec": ("tagrec", "error", "TAG_REC_STATE=error"),
                        "cli": ("cli", "error", "CLI_STATE=error cli_hits=0 cli_q="),
                        "ext": ("ext", "error", "EXT_STATE=error ext_calls=%d EXT_SRC=none" % R.used["ext"])}.get(name)
                if name == "struct":
                    st.setdefault("struct", 0)
                    st.setdefault("route", "unmeasured")
                elif dflt:
                    st[dflt[0]] = dflt[1]
                    o.mark(dflt[2])
                st.setdefault("cli", "error")
                st.setdefault("cli_n", 0)
                st.setdefault("tagrec", "error")
                if name == "ext":
                    st["ext_calls"] = R.used["ext"]

        guard("vault", stage_vault, o, R, a["vault_path"], st)
        if run == "pick":
            st["struct"] = "pick"
            guard("tagrec", stage_tagrec, o, a, R, st, True)
            return o, st, R, run
        guard("struct", stage_struct, o, a, st, load_module("km_search_guard"))
        guard("vs", stage_vs, o, a, st)
        guard("tagrec", stage_tagrec, o, a, R, st, False)
        o.mark("STRUCT_STATE=ran STRUCT_DOCS=%d/3 ROUTE_SCAN=%s VS_STATE=%s TAG_REC_STATE=%s"
          % (st["struct"], st.get("route", "unmeasured"), st.get("vs_state", "absent"), st.get("tagrec")))
        guard("cli", stage_cli, o, a, R, st, cq)
        guard("ext", stage_ext, o, a, R, st, cq)
        hubs = st.get("hubs", "na")
        if a["graphrag_state"] == "ok":
            tier = "GraphRAG 서버"
        elif st["cli"] in ("ok", "empty"):
            tier = "Obsidian CLI"
        else:
            tier = "텍스트 검색"
        graph = " + 그래프 확장(backlinks %d)" % st.get("bl", 0) if st.get("ext", "").startswith(("done", "partial")) else ""
        o("끝 줄(그대로 베껴 쓰기): 검색: %s · CLI %s(%d건) + 구조 문서(%d/3 참조 · 허브 %s · VS %d줄) + 태그 추천(%s)%s"
          % (tier, st["cli"], st["cli_n"], st["struct"], hubs if hubs != "na" else 0, st.get("vs", 0), st.get("tagrec"), graph))
        if R.stopped:
            o("⚠ CLI 호출 중단(%s) — 시한 %ds · 마감 %ds · 남은 단계는 건너뜀" % (R.stopped, int(R.timeout), int(R.budget)))
    except Exception as e:  # 표지 없이 죽지 않는다
        o("KM_STAGE_ERROR=%s: %s" % (type(e).__name__, str(e)[:80]))
    return o, st, R, run


if __name__ == "__main__":
    o, st, R, run = main(sys.argv[1:])
    last = stages_line(st, R, run)
    lines = o.lines
    if len(lines) > MAX_LINES - 1:
        keep = MAX_LINES - 2
        lines = lines[:keep] + ["… 줄 상한 %d — %d줄 생략" % (MAX_LINES, len(o.lines) - keep)]
    try:
        sys.stdout.buffer.write(("\n".join(lines + [last]) + "\n").encode("utf-8", "replace"))
        sys.stdout.flush()
    except Exception:
        pass
    sys.exit(0)
