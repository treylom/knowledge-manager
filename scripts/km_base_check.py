#!/usr/bin/env python3
"""km_base_check.py - 폴더 노트 표(.base) 저장 조건 5 검사 (KM · 시범 · 저장 흐름에는 아직 안 넣음).

조건(2026-11-06 kepano/obsidian-skills 흡수 검토):
  filter        .base 에 명시 주제 필터가 있다 — 전역 filters 가 있고, 논리 키(and/or/not)는
                한 객체에 «정확히 하나»(kepano/obsidian-skills obsidian-bases 규칙 · 2026-06-06 반영 수정), 폴더·태그 조건 포함
  expected-set  Obsidian 이 돌려준 노트 집합 == 그 폴더(하위 포함)의 .md 집합
  query-rows    Obsidian CLI base:query 가 1행 이상 · 출력에 «Error:» 없음(CLI 는 오류도 종료코드 0)
  moc-entry     폴더 MOC 에서 ![[x.base]] 또는 [[x.base…]] 로 들어갈 수 있다
  no-duplicate  같은 폴더를 거르는 .base 가 1개 · MOC 진입 줄도 1개(재저장해도 늘지 않음)

빈 껍데기(필터 없는 기본 표)는 vault 전체를 돌려줘 «1행+» 은 통과하지만 filter·expected-set 에서 떨어진다.
exit 0 = 5조건 통과 / 1 = 하나 이상 미통과(이 검사기는 판정만 낸다 — 저장을 막을지는 부르는 쪽이 정한다)
exit 2 = 측정 불가(.base·MOC·CLI 없음 · 읽을 수 없는 .base·MOC) — 통과 취급 ❌. 표준 라이브러리만 사용한다.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

LOGIC_KEY_RE = re.compile(r"^(\s*)(-\s+)?(and|or|not):\s*$")
TOPIC_RE = re.compile(r"file\.(inFolder|hasTag)\(")


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def filters_block(text):
    """맨 바깥 filters: 의 (한 줄 값, 아래 블록 줄 목록). 없으면 None."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^filters:\s*(.*?)\s*$", line)
        if not m:
            continue
        block = []
        for nxt in lines[i + 1:]:
            if nxt.strip() and not nxt[0].isspace():
                break
            block.append(nxt)
        return m.group(1), block
    return None


def logic_key_violations(block):
    """한 객체 안에 and/or/not 가 둘 이상 나란히 있는 줄 번호(블록 기준) 목록."""
    rows = []
    for idx, line in enumerate(block):
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        m = LOGIC_KEY_RE.match(line)
        dash = bool(m and m.group(2))
        col = indent + (len(m.group(2)) if dash else 0) if m else indent
        rows.append((idx, indent, col, dash, bool(m)))
    bad = []
    for pos, (idx, indent, col, dash, is_logic) in enumerate(rows):
        if not is_logic or dash:
            continue
        # 같은 객체의 앞 형제 키: 뒤로 가며 col 보다 얕은 줄을 만나기 전, 같은 col 에 있는 키
        for pidx, pindent, pcol, pdash, plogic in reversed(rows[:pos]):
            if pcol < col and not (pdash and pcol == col):
                break
            if pcol == col and plogic:
                bad.append(idx)
                break
            if pindent < col:
                break
    return bad


def check_filter(text, folder):
    fb = filters_block(text)
    if fb is None:
        return False, "전역 filters 없음(빈 껍데기 · 기본 표)"
    inline, block = fb
    body = inline + "\n" + "\n".join(block)
    if not body.strip():
        return False, "filters 가 비어 있음"
    bad = logic_key_violations(block)
    if bad:
        return False, "한 객체에 논리 키 둘 이상(and/or/not 은 정확히 하나) — filters 아래 %d번째 줄" % (bad[0] + 1)
    if not TOPIC_RE.search(body):
        return False, "주제 조건(file.inFolder/file.hasTag) 없음"
    if not mentions_folder(body, folder) and "file.hasTag(" not in body:
        return False, "폴더 «%s» 조건 없음" % folder
    return True, "ok"


def mentions_folder(text, folder):
    """폴더 경로가 «경로 단위로» 들어 있나 — topic-x 가 topic-xy·my-topic-x 안의 부분 문자열로 걸리지 않게.
    뒤에 / 가 오는 것(하위 폴더)은 같은 폴더 조건으로 본다."""
    return re.search(r"(?<![\w/.\-])%s(?![\w.\-])" % re.escape(folder), text) is not None


def expected_set(vault, folder):
    root = os.path.join(vault, folder)
    out = set()
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for n in names:
            if n.lower().endswith(".md"):
                out.add(os.path.relpath(os.path.join(dirpath, n), vault).replace(os.sep, "/"))
    return out


def entry_count(moc_text, base_name):
    stem = re.escape(base_name[:-5] if base_name.endswith(".base") else base_name)
    pat = re.compile(r"!?\[\[(?:[^\]|#]*/)?%s\.base(?:#[^\]|]*)?(?:\\?\|[^\]]*)?\]\]" % stem)
    return len(pat.findall(moc_text))


def run_cli(cmd):
    """CLI 를 «열어 둔 빈 파이프»를 표준입력으로 주고 부른다.

    2026-11-06 실측(base:query · 2.3MB 응답): 표준입력이 /dev/null 이면 응답이 0바이트(rc 0)로 오고,
    열린 파이프·소켓이면 전부 온다(3/3). cron·CI 는 보통 /dev/null 이라 그대로 두면 거짓 0행이 된다.
    """
    r_fd, w_fd = os.pipe()
    try:
        return subprocess.run(cmd, stdin=r_fd, capture_output=True, text=True,
                              errors="replace", timeout=120)
    finally:
        os.close(r_fd)
        os.close(w_fd)


def main(argv=None):
    ap = argparse.ArgumentParser(description="폴더 .base 저장 조건 5 (exit 0 통과 / 1 미통과 / 2 측정 불가)")
    ap.add_argument("vault", help="Obsidian 이 열어 둔 vault 루트(라이브)")
    ap.add_argument("--folder", required=True, help="vault 상대 폴더")
    ap.add_argument("--base", required=True, help="vault 상대 .base 경로")
    ap.add_argument("--moc", required=True, help="vault 상대 폴더 MOC 경로")
    ap.add_argument("--cli", default=os.environ.get("OBSIDIAN_CLI") or shutil.which("obsidian") or "obsidian")
    ap.add_argument("--vault-name", default="", help="CLI vault= 값(여러 vault 를 열어 둘 때)")
    ap.add_argument("--retries", type=int, default=3,
                    help="0바이트 응답(새 파일 직후 색인 창) 때 다시 묻는 횟수(기본 3)")
    ap.add_argument("--retry-wait", type=float, default=3.0, help="다시 묻기 전 쉬는 초(기본 3)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    vault = os.path.abspath(os.path.expanduser(a.vault))
    folder = a.folder.strip("/")
    base_abs, moc_abs = os.path.join(vault, a.base), os.path.join(vault, a.moc)
    for label, p in (("vault", vault), ("폴더", os.path.join(vault, folder))):
        if not os.path.isdir(p):
            sys.stderr.write("측정 불가: %s 없음 %s\n" % (label, p))
            return 2
    for label, p in ((".base", base_abs), ("MOC", moc_abs)):
        if not os.path.isfile(p):
            sys.stderr.write("측정 불가: %s 없음 %s\n" % (label, p))
            return 2
    if not (os.path.isfile(a.cli) and os.access(a.cli, os.X_OK)) and not shutil.which(a.cli):
        sys.stderr.write("측정 불가: Obsidian CLI 없음 %s\n" % a.cli)
        return 2

    cmd = [a.cli, "base:query", "path=%s" % a.base, "format=paths"]
    if a.vault_name:
        cmd.append("vault=%s" % a.vault_name)
    # 0바이트 + rc 0 = 무결과가 아니라 도구 순간 빈손(새 .base 직후 색인 창 · 2026-11-06 실측) → 쉬고 다시 묻는다
    attempts = 0
    while True:
        attempts += 1
        try:
            r = run_cli(cmd)
        except (OSError, subprocess.TimeoutExpired) as exc:
            sys.stderr.write("측정 불가: CLI 실행 실패 %s\n" % exc)
            return 2
        if (r.stdout + r.stderr).strip() or attempts > a.retries:
            break
        time.sleep(a.retry_wait)
    zero_byte = not (r.stdout + r.stderr).strip()
    out_lines = [l.strip() for l in (r.stdout + "\n" + r.stderr).splitlines() if l.strip()]
    err_line = next((l for l in out_lines if l.startswith("Error:")), "")
    rows = set() if err_line or r.returncode != 0 else {l for l in out_lines}

    expected = expected_set(vault, folder)
    base_name = os.path.basename(a.base)
    same_folder = []
    # 끊긴 심링크·권한 없음 .base·MOC = traceback·exit 1 ❌ → 측정 불가(2)
    try:
        base_text, moc_text = read_text(base_abs), read_text(moc_abs)
        for dirpath, _, names in os.walk(os.path.join(vault, folder)):
            for n in names:
                if n.endswith(".base") and mentions_folder(read_text(os.path.join(dirpath, n)), folder):
                    same_folder.append(os.path.relpath(os.path.join(dirpath, n), vault))
    except OSError as exc:
        sys.stderr.write("측정 불가: 파일을 읽을 수 없음 %s\n" % exc)
        return 2
    f_ok, f_why = check_filter(base_text, folder)
    entries = entry_count(moc_text, base_name)
    conds = [
        {"id": "filter", "pass": f_ok, "why": f_why},
        {"id": "expected-set", "pass": bool(rows) and rows == expected,
         "why": "rows %d · expected %d · missing %d · extra %d"
                % (len(rows), len(expected), len(expected - rows), len(rows - expected))},
        {"id": "query-rows", "pass": len(rows) >= 1 and not err_line and r.returncode == 0,
         "why": err_line or ("0 B 응답 %d회(색인 안 됨?) — 무결과로 단정 ❌" % attempts if zero_byte
                             else "rc=%d rows=%d" % (r.returncode, len(rows)))},
        {"id": "moc-entry", "pass": entries >= 1, "why": "MOC 진입 %d" % entries},
        {"id": "no-duplicate", "pass": len(same_folder) == 1 and entries <= 1,
         "why": "같은 폴더 .base %d · MOC 진입 %d" % (len(same_folder), entries)},
    ]
    payload = {"base": a.base, "folder": folder, "rows": len(rows), "expected": len(expected),
               "missing": sorted(expected - rows), "extra": sorted(rows - expected)[:20],
               "query_rc": r.returncode, "query_error": err_line, "attempts": attempts, "conditions": conds,
               "passed": all(c["pass"] for c in conds)}
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for c in conds:
            print("%-13s %s  %s" % (c["id"], "PASS" if c["pass"] else "FAIL", c["why"]))
        print("rows=%d expected=%d passed=%s" % (len(rows), len(expected), payload["passed"]))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
