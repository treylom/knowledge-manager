#!/usr/bin/env python3
"""km_ofm_lint.py 시험 — Obsidian Flavored Markdown 경고 검사 5종.

검사마다 양성(잡아야 함)·음성(잡으면 안 됨) 짝을 같은 vault 안에 둔다.
경고 모드: 경고가 있어도 exit 0 · --strict 일 때만 1 · 측정 불가 = 2.
실행: python3 -I -B scripts/tests/test_km_ofm_lint.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "km_ofm_lint.py")

TARGET = """---
tags: [ok]
---
# Target

## Exists

본문 한 줄 ^blk001
줄 가운데 a^mid001 b 는 블록 id 가 아니다

## **Bold** `Code` Title

### Sub

- 목록 항목
- 두 번째

^tbl001
"""

NOTES = {
    "B.md": TARGET,
    # 음성: 모든 링크·문법이 맞는 노트
    "clean.md": """---
tags: [research, ai/agents]
aliases: [Clean]
---
# Clean

## Self Heading

[[B#Exists]] · [[B#Exists|별칭]] · ![[B#Exists]] · [[B#Bold Code Title]]
[[B#exists]] · [[B#Exists#Sub]] · [[B#^blk001]] · [[B#^tbl001]] · [[#Self Heading]]
![[보기.base#표]] · [[없는노트#아무거나]] · [[dup#H]]

> [!note] 제목
> [!WARNING]
> [!faq]- 접힘
> [!tip]+ 펼침

%%한 줄 주석%%

%%
여러 줄 주석
%%

==강조== 그리고 ==또 강조==

`a == b` 와 `%%` 는 코드라 셈하지 않는다

| 표 | 링크 |
|---|---|
| 별칭 | [[B#Exists\\|별칭]] |

비교식은 강조가 아니다: task == "x" · requests==2.32.3 · kind=="coding"
코드식(실 vault 표본): count("/")==2 · sha[:16]==266e · argv[1]==pinned
(위 두 덩이 = 실측 헛경고에서 나온 음성 예시: 표 안 \\| 별칭 · 비교식 a==b)
한국어 조사·문장부호가 붙어 닫힌 강조: ==소개글==이다 · ==끝==, 그리고

```python
x == 1  # [[B#NoSuchHeading]] %%
```
""",
    # 양성: 검사마다 1개씩
    "bad-heading.md": "---\ntags: [x]\n---\n# H\n\n[[B#Missing Heading]] · [[#Nope Self]]\n",
    "bad-block.md": "---\ntags: [x]\n---\n# H\n\n[[B#^zzz999]]\n",
    "bad-block-mid.md": "# H\n\n[[B#^mid001]]\n",
    "bad-table.md": "# H\n\n| a | b |\n|---|---|\n| x | [[B#Ghost\\|별칭]] · [[B#Exists\\|ok]] |\n",
    "bad-callout.md": "---\ntags: [x]\n---\n# H\n\n> [!warnign] 오타\n",
    "bad-fold.md": "---\ntags: [x]\n---\n# H\n\n> [!faq-] 안쪽\n\n> [!-tip] 앞쪽\n\n> -[!note] 밖\n",
    "bad-comment.md": "---\ntags: [x]\n---\n# H\n\n%% 안 닫힌 주석\n",
    "bad-highlight.md": "---\ntags: [x]\n---\n# H\n\n이건 ==안 닫힌 강조\n",
    "bad-tags.md": "---\ntags:\n  - Claude Code\n  - \"#hashed\"\n  - fine\n---\n# H\n",
    "bad-tags-line.md": "---\ntopics: [Claude Code]\ntags:\n  - ok\n  - Claude Code\n---\n# H\n",
    "bad-tags-flow.md": "---\ntags: [\"two words\", ok]\n---\n# H\n",
    # MOC 도 면제 없음
    "Topic-MOC.md": "---\ntype: MOC\ntags: [MOC]\n---\n# Topic\n\n[[B#Ghost Heading]]\n",
    # 이름 겹침 = 모호 → 건너뜀(경고 ❌)
    "dir1/dup.md": "# dup\n\n## Other\n",
    "dir2/dup.md": "# dup\n\n## H\n",
}
# 전체 스캔에서 빠져야 하는 노트(기본 제외 글롭 _meta/*·templates/* · 건너뛰는 폴더 .obsidian·.trash) — 일부러 경고감
SKIPPED = {
    "_meta/m.md": "# m\n\n[[B#Ghost]]\n",
    "templates/t.md": "# t\n\n> [!warnign] x\n",
    ".obsidian/o.md": "# o\n\n[[B#Ghost]]\n",
    ".trash/old.md": "# old\n\n[[B#Ghost]]\n",
}


def make_vault():
    root = tempfile.mkdtemp(prefix="ofm-lint-")
    for rel, body in list(NOTES.items()) + list(SKIPPED.items()):
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
    return root


def run(*args):
    r = subprocess.run([sys.executable, "-I", "-B", SCRIPT] + list(args),
                       capture_output=True, text=True, timeout=60)
    return r


class OfmLint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vault = make_vault()

    def lint(self, note, *extra):
        r = run(self.vault, "--notes", note, "--json", *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def checks(self, note):
        return sorted(w["check"] for w in self.lint(note)["warnings"])

    # 음성 — 맞는 노트는 경고 0
    def test_clean_note_has_no_warnings(self):
        out = self.lint("clean.md")
        self.assertEqual(out["warnings"], [], out)
        self.assertEqual(out["checked"], 1)
        self.assertEqual(out["mode"], "warn")

    # ① 헤딩·블록 링크 대상
    def test_missing_heading_targets(self):
        out = self.lint("bad-heading.md")
        got = [(w["check"], w["detail"]) for w in out["warnings"]]
        self.assertEqual(len(got), 2, got)
        self.assertTrue(all(c == "heading-link" for c, _ in got), got)
        self.assertTrue(any("Missing Heading" in d for _, d in got), got)
        self.assertTrue(any("Nope Self" in d for _, d in got), got)

    def test_missing_block_target(self):
        self.assertEqual(self.checks("bad-block.md"), ["block-link"])

    def test_block_id_only_at_line_end(self):
        # 줄 가운데 ^id 는 블록 id 가 아니다 — 그 id 로 거는 링크는 경고
        self.assertEqual(self.checks("bad-block-mid.md"), ["block-link"])

    # ② 콜아웃 타입 오타
    def test_callout_type_typo(self):
        out = self.lint("bad-callout.md")
        self.assertEqual([w["check"] for w in out["warnings"]], ["callout-type"])
        self.assertIn("warnign", out["warnings"][0]["detail"])

    # ③ 접기 +/- 위치
    def test_fold_marker_position(self):
        self.assertEqual(self.checks("bad-fold.md"),
                         ["callout-fold", "callout-fold", "callout-fold"])

    # ④ %% · == 짝
    def test_unclosed_comment(self):
        self.assertEqual(self.checks("bad-comment.md"), ["comment-pair"])

    def test_unclosed_highlight(self):
        self.assertEqual(self.checks("bad-highlight.md"), ["highlight-pair"])

    def test_table_escaped_alias_link(self):
        # [[노트#헤딩\\|별칭]] — 표 안 별칭 탈출. 대상이 없으면 여전히 잡는다(양성 짝)
        out = self.lint("bad-table.md")
        self.assertEqual([w["check"] for w in out["warnings"]], ["heading-link"])
        self.assertIn("Ghost", out["warnings"][0]["detail"])
        self.assertNotIn("\\", out["warnings"][0]["detail"])

    # ⑤ tags 공백·#
    def test_tags_block_list(self):
        out = self.lint("bad-tags.md")
        got = sorted(w["detail"] for w in out["warnings"])
        self.assertEqual([w["check"] for w in out["warnings"]], ["tag-format", "tag-format"])
        self.assertTrue(any("Claude Code" in d for d in got), got)
        self.assertTrue(any("#hashed" in d for d in got), got)

    def test_tags_line_number_is_the_tags_entry(self):
        # 같은 글자가 topics: 줄에도 있다 — 경고 줄은 tags 항목 줄(frontmatter 5행)
        out = self.lint("bad-tags-line.md")
        self.assertEqual([(w["check"], w["line"]) for w in out["warnings"]], [("tag-format", 5)])

    def test_tags_flow_list(self):
        self.assertEqual(self.checks("bad-tags-flow.md"), ["tag-format"])

    # MOC 면제 없음 (링크 게이트는 MOC 를 moc-self 로 면제한다)
    def test_moc_is_checked(self):
        self.assertEqual(self.checks("Topic-MOC.md"), ["heading-link"])

    # 줄 번호
    def test_line_numbers(self):
        out = self.lint("bad-block.md")
        self.assertEqual(out["warnings"][0]["line"], 6)

    # 종료 코드 계약
    def test_exit_codes(self):
        self.assertEqual(run(self.vault, "--notes", "bad-block.md").returncode, 0)
        self.assertEqual(run(self.vault, "--notes", "bad-block.md", "--strict").returncode, 1)
        self.assertEqual(run(self.vault, "--notes", "clean.md", "--strict").returncode, 0)
        self.assertEqual(run(self.vault, "--notes", "no-such.md").returncode, 2)
        self.assertEqual(run(os.path.join(self.vault, "nope-dir")).returncode, 2)

    # 여러 노트 + 전체 스캔
    def test_multi_and_full_scan(self):
        out = self.lint("clean.md,bad-block.md")
        self.assertEqual(out["checked"], 2)
        r = run(self.vault, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        full = json.loads(r.stdout)
        self.assertEqual(full["checked"], len(NOTES))
        bad_notes = {w["note"] for w in full["warnings"]}
        self.assertNotIn("clean.md", bad_notes)
        self.assertIn("Topic-MOC.md", bad_notes)
        for rel in SKIPPED:                      # 기본 제외·건너뛰는 폴더는 세지도 경고하지도 않는다
            self.assertNotIn(rel, bad_notes)
        # 양성 짝: 제외를 풀면(--exclude '') _meta·templates 는 검사된다(.obsidian·.trash 는 그대로 건너뜀)
        r = run(self.vault, "--json", "--exclude", "")
        allin = json.loads(r.stdout)
        self.assertEqual(allin["checked"], len(NOTES) + 2)
        noted = {w["note"] for w in allin["warnings"]}
        self.assertIn("_meta/m.md", noted)
        self.assertIn("templates/t.md", noted)
        self.assertNotIn(".obsidian/o.md", noted)
        self.assertNotIn(".trash/old.md", noted)

    # 읽을 수 없는 노트(끊긴 심링크) = 경고 모드라도 traceback·exit 1 ❌ → 측정 불가 2 · 정상 노트만 보면 0
    def test_unreadable_note_is_unmeasurable(self):
        root = tempfile.mkdtemp(prefix="ofm-lint-broken-")
        with open(os.path.join(root, "ok.md"), "w", encoding="utf-8") as fh:
            fh.write("# ok\n")
        with open(os.path.join(root, "draft.md"), "w", encoding="utf-8") as fh:
            fh.write("# d\n\n[[ghost#Some Heading]]\n")
        os.symlink(os.path.join(root, "no-such-target.md"), os.path.join(root, "ghost.md"))
        full = run(root)
        self.assertEqual(full.returncode, 2, full.stderr)
        self.assertIn("측정 불가", full.stderr)
        self.assertNotIn("Traceback", full.stderr)
        draft = run(root, "--notes", "draft.md")       # 링크 대상이 끊긴 심링크
        self.assertEqual(draft.returncode, 2, draft.stderr)
        self.assertNotIn("Traceback", draft.stderr)
        ok = run(root, "--notes", "ok.md")             # 음성 짝: 읽을 수 있는 노트만 보면 정상
        self.assertEqual(ok.returncode, 0, ok.stderr)

    # 사람용 출력에도 검사 이름과 합계가 보인다
    def test_text_output(self):
        r = run(self.vault, "--notes", "bad-callout.md")
        self.assertIn("callout-type", r.stdout)
        self.assertIn("warnings=1", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
