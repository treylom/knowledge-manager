#!/usr/bin/env python3
"""km_base_check.py 시험 — 폴더 Base 저장 조건 5 (경고 모드).

Obsidian CLI 는 가짜(stub)로 바꿔 끼운다: base:query 가 돌려줄 줄을 환경변수 파일에서 읽고,
.base 파일이 없으면 진짜 CLI 처럼 «종료코드 0 + Error:» 를 낸다(2026-11-06 실측 꼴).
실행: python3 -I -B scripts/tests/test_km_base_check.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "km_base_check.py")
FOLDER = "020-Library/Research/topic-x"

GOOD_BASE = """filters:
  and:
    - file.inFolder("020-Library/Research/topic-x")
    - file.ext == "md"
views:
  - type: table
    name: 노트
    order:
      - file.name
      - date
"""
# 빈 껍데기(Obsidian «새 Base» 기본 꼴 · 필터 없음)
EMPTY_BASE = """views:
  - type: table
    name: Table
"""
# kepano 6-01 버전 예시 꼴: and/or 두 키를 한 객체에 나란히 = 규칙 위반
TWO_KEY_BASE = """filters:
  and:
    - file.inFolder("020-Library/Research/topic-x")
  or:
    - file.hasTag("x")
views:
  - type: table
    name: 노트
"""

STUB = r"""#!/bin/sh
# 가짜 obsidian CLI: base:query path=<p> format=paths
for a in "$@"; do case "$a" in path=*) P="${a#path=}";; esac; done
if [ ! -f "$STUB_VAULT/$P" ]; then echo "Error: Base file not found: $P"; exit 0; fi
# 새 파일 직후 색인 창: 처음 N번은 0바이트(rc 0) — 2026-11-06 실측 꼴
if [ -n "$STUB_EMPTY" ] && [ -f "$STUB_EMPTY" ]; then n=$(cat "$STUB_EMPTY"); if [ "$n" -gt 0 ]; then echo $((n-1)) > "$STUB_EMPTY"; exit 0; fi; fi
# 진짜 CLI 동작(2026-11-06 실측): 표준입력이 /dev/null(문자 장치)이면 응답 0바이트 · 열린 파이프·소켓이면 전부
if [ -c /dev/stdin ]; then exit 0; fi
cat "$STUB_ROWS"
exit "${STUB_RC:-0}"
"""


class Env:
    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="base-check-")
        self.vault = os.path.join(self.root, "vault")
        self.bin = os.path.join(self.root, "bin")
        os.makedirs(os.path.join(self.vault, FOLDER, "raw"))
        os.makedirs(self.bin)
        self.notes = ["a.md", "b.md", "MOC-topic-x.md"]
        for n in self.notes:
            self.write(f"{FOLDER}/{n}", "# %s\n" % n)
        self.write(f"{FOLDER}/raw/chart.png", "png")
        self.write("020-Library/Research/other/z.md", "# z\n")
        cli = os.path.join(self.bin, "obsidian")
        with open(cli, "w") as fh:
            fh.write(STUB)
        os.chmod(cli, 0o755)
        self.cli = cli
        self.rows = os.path.join(self.root, "rows.txt")
        self.set_rows([f"{FOLDER}/{n}" for n in self.notes])

    def write(self, rel, body):
        p = os.path.join(self.vault, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)

    def set_rows(self, rows):
        with open(self.rows, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows))

    def run(self, base="topic-x.base", moc="MOC-topic-x.md", *extra, stub_rc=0):
        env = dict(os.environ, STUB_VAULT=self.vault, STUB_ROWS=self.rows,
                   STUB_EMPTY=os.path.join(self.root, "empty-count"), STUB_RC=str(stub_rc))
        args = [sys.executable, "-I", "-B", SCRIPT, self.vault, "--folder", FOLDER,
                "--base", f"{FOLDER}/{base}", "--moc", f"{FOLDER}/{moc}",
                "--cli", self.cli, "--json", "--retry-wait", "0"] + list(extra)
        # cron·CI 처럼 표준입력 = /dev/null 로 부른다
        r = subprocess.run(args, capture_output=True, text=True, env=env, timeout=60,
                           stdin=subprocess.DEVNULL)
        out = json.loads(r.stdout) if r.stdout.strip().startswith("{") else None
        return r.returncode, out, r.stderr


def verdicts(out):
    return {c["id"]: c["pass"] for c in out["conditions"]}


class BaseCheck(unittest.TestCase):
    def setUp(self):
        self.e = Env()

    def good(self):
        self.e.write(f"{FOLDER}/topic-x.base", GOOD_BASE)
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "# MOC\n\n![[topic-x.base]]\n")

    # 양성: 5조건 모두 통과
    def test_all_five_pass(self):
        self.good()
        rc, out, err = self.e.run()
        self.assertEqual(rc, 0, err)
        self.assertEqual(verdicts(out), {"filter": True, "expected-set": True, "query-rows": True,
                                         "moc-entry": True, "no-duplicate": True})
        self.assertEqual(out["rows"], 3)
        self.assertEqual(out["expected"], 3)

    # 음성 ① 빈 껍데기: 조회는 vault 전체(1행+)가 나오지만 필터·집합이 틀려 FAIL
    def test_empty_shell_is_not_a_pass(self):
        self.e.write(f"{FOLDER}/topic-x.base", EMPTY_BASE)
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "![[topic-x.base]]\n")
        self.e.set_rows([f"{FOLDER}/{n}" for n in self.e.notes] + ["020-Library/Research/other/z.md"])
        rc, out, _ = self.e.run()
        v = verdicts(out)
        self.assertEqual(rc, 1)
        self.assertTrue(v["query-rows"])          # «1행+» 만으로는 못 막는다
        self.assertFalse(v["filter"])
        self.assertFalse(v["expected-set"])

    # 음성 ② 필터 두 키 나란히(kepano/obsidian-skills 2026-06-06 수정 전 꼴)
    def test_two_logic_keys_side_by_side(self):
        self.e.write(f"{FOLDER}/topic-x.base", TWO_KEY_BASE)
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "![[topic-x.base]]\n")
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 1)
        self.assertFalse(verdicts(out)["filter"])

    # 음성 ②-b 다른 폴더를 거르는 .base: 조회 결과가 우연히 맞아도 필터 조건으로 FAIL
    def test_filter_on_another_folder(self):
        self.e.write(f"{FOLDER}/topic-x.base", GOOD_BASE.replace(FOLDER, "020-Library/Research/other"))
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "![[topic-x.base]]\n")
        rc, out, _ = self.e.run()
        v = verdicts(out)
        self.assertEqual(rc, 1)
        self.assertFalse(v["filter"])
        self.assertTrue(v["expected-set"])        # 조회 집합만으로는 못 잡는 꼴

    # 음성 ②-c 폴더 이름의 부분 문자열(topic-x ⊂ topic-xy)은 같은 폴더 조건이 아니다
    def test_filter_on_folder_with_longer_name(self):
        self.e.write(f"{FOLDER}/topic-x.base", GOOD_BASE.replace(FOLDER, FOLDER + "y"))
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "![[topic-x.base]]\n")
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 1)
        self.assertFalse(verdicts(out)["filter"])
        self.assertFalse(verdicts(out)["no-duplicate"])   # 같은 폴더를 거르는 .base 0개

    # 음성 ③ 없는 .base: CLI 는 rc 0 + Error: — 출력으로 판정
    def test_cli_error_with_rc0(self):
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "![[topic-x.base]]\n")
        rc, out, _ = self.e.run(base="ghost.base")
        self.assertEqual(rc, 2)                   # .base 파일 없음 = 측정 불가

    def test_query_error_line_fails_rows(self):
        self.good()
        self.e.set_rows(["Error: Base file not found: topic-x.base"])
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 1)
        self.assertFalse(verdicts(out)["query-rows"])
        self.assertIn("Error:", out["query_error"])

    # 음성 ③-b CLI 가 0 아닌 종료코드면 행이 찍혀도 조회 실패
    def test_cli_nonzero_rc_fails_rows(self):
        self.good()
        rc, out, _ = self.e.run(stub_rc=3)
        self.assertEqual(rc, 1)
        v = verdicts(out)
        self.assertFalse(v["query-rows"])
        self.assertFalse(v["expected-set"])
        self.assertEqual(out["query_rc"], 3)

    # 읽을 수 없는 .base(끊긴 심링크)가 폴더에 있으면 traceback·exit 1 ❌ → 측정 불가 2
    def test_broken_symlink_base_is_unmeasurable(self):
        self.good()
        os.symlink(os.path.join(self.e.root, "no-such.base"), os.path.join(self.e.vault, FOLDER, "ghost.base"))
        rc, out, err = self.e.run()
        self.assertEqual(rc, 2, err)
        self.assertNotIn("Traceback", err)

    # 점 폴더(.trash 등) 안 노트는 기대 집합에 넣지 않는다
    def test_dot_folder_notes_not_expected(self):
        self.good()
        self.e.write(f"{FOLDER}/.trash/old.md", "# old\n")
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 0)
        self.assertEqual(out["expected"], 3)

    # 음성 ④ 기대 집합 불일치(한 노트 빠짐)
    def test_missing_note_in_rows(self):
        self.good()
        self.e.set_rows([f"{FOLDER}/a.md", f"{FOLDER}/MOC-topic-x.md"])
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 1)
        self.assertFalse(verdicts(out)["expected-set"])
        self.assertEqual(out["missing"], [f"{FOLDER}/b.md"])

    # 음성 ⑤ MOC 에서 진입 없음
    def test_moc_without_entry(self):
        self.good()
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "# MOC\n\n[[a]]\n")
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 1)
        self.assertFalse(verdicts(out)["moc-entry"])

    def test_moc_plain_link_counts(self):
        self.good()
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "# MOC\n\n[[topic-x.base|노트 표]]\n")
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 0)

    # 음성 ⑥ 재저장 중복: 같은 폴더를 거르는 .base 가 둘 · MOC 진입 줄 둘
    def test_duplicate_base_and_embed(self):
        self.good()
        self.e.write(f"{FOLDER}/topic-x 1.base", GOOD_BASE)
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 1)
        self.assertFalse(verdicts(out)["no-duplicate"])

    def test_duplicate_embed_line(self):
        self.good()
        self.e.write(f"{FOLDER}/MOC-topic-x.md", "![[topic-x.base]]\n\n![[topic-x.base]]\n")
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 1)
        self.assertFalse(verdicts(out)["no-duplicate"])

    # 색인 창 0바이트: 다시 물어서 통과(양성) · 끝까지 0바이트면 미통과 + 사유(음성)
    def _empty(self, n):
        with open(os.path.join(self.e.root, "empty-count"), "w") as fh:
            fh.write(str(n))

    def test_zero_byte_then_rows_retries(self):
        self.good()
        self._empty(2)
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 0)
        self.assertEqual(out["attempts"], 3)

    def test_zero_byte_retries_up_to_the_limit(self):
        # 기본 --retries 3 = 첫 질문 + 다시 3번 → 0바이트 3번 뒤 4번째에 행
        self.good()
        self._empty(3)
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 0)
        self.assertEqual(out["attempts"], 4)

    def test_zero_byte_forever_fails_with_reason(self):
        self.good()
        self._empty(99)
        rc, out, _ = self.e.run()
        self.assertEqual(rc, 1)
        self.assertFalse(verdicts(out)["query-rows"])
        self.assertIn("0 B", [c for c in out["conditions"] if c["id"] == "query-rows"][0]["why"])

    # CLI 없음 = 측정 불가
    def test_cli_missing(self):
        self.good()
        rc, out, err = self.e.run("topic-x.base", "MOC-topic-x.md", "--cli", "/nonexistent/obsidian")
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
