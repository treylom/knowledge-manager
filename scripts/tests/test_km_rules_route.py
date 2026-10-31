#!/usr/bin/env python3
"""km_rules_route.py v2 — the rule-source step decides by itself whether to run (no model-passed VAULT_MODE),
skips only on a confirmed «other» vault, and ranks by length-normalised overlap.

Run: python3 scripts/tests/test_km_rules_route.py
     KM_RULES_ROUTE=<other copy> python3 scripts/tests/test_km_rules_route.py   # e.g. the pre-fix version → RED
"""
import http.server
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = Path(os.environ.get('KM_RULES_ROUTE') or HERE.parent / 'km_rules_route.py')
SEARCH_MD = HERE.parent.parent / 'commands' / 'search.md'


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


class FakeServer:
    """Minimal /api/search stand-in: returns the given results list."""

    def __init__(self, results):
        body = json.dumps({'results': results}).encode()

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self.httpd = http.server.HTTPServer(('127.0.0.1', 0), H)
        self.url = 'http://127.0.0.1:%d' % self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


class Base(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        t = Path(self.td.name)
        self.home, self.root, self.vault = t / 'home', t / 'repo', t / 'vault'
        for d in (self.home, self.root / 'docs/rules-core', self.root / '.claude/rules', self.vault / 'notes'):
            d.mkdir(parents=True)
        (self.root / '.claude/rules/INDEX.md').write_text(
            '| 트리거 | rule | 핵심 |\n|---|---|---|\n| 멘션 보고 | [comms](comms.md) | 멘션 = 봇마다 |\n', encoding='utf-8')
        (self.root / '.claude/rules/comms.md').write_text('멘션 규칙 코어\n', encoding='utf-8')
        (self.root / 'docs/rules-core/ledger.md').write_text('장부 규칙: 지시 받으면 장부에 적는다.\n', encoding='utf-8')
        (self.vault / 'notes/here.md').write_text('note\n', encoding='utf-8')

    def tearDown(self):
        self.td.cleanup()

    def config(self, endpoint, corpus=True):
        c = {'storage': {'obsidian': {'vaultPath': str(self.vault)}}, 'linking': {'semantic_adapter': {'endpoint': endpoint}}}
        if corpus:
            c['search'] = {'ruleCorpus': {'root': str(self.root), 'index': '.claude/rules/INDEX.md',
                                          'globs': ['docs/rules-core/*.md', '.claude/rules/*.md'], 'top': 5}}
        p = Path(self.td.name) / 'km-config.json'
        p.write_text(json.dumps(c), encoding='utf-8')
        return p

    def run_route(self, cfg, query='장부 규칙', auto=True, extra=()):
        argv = [sys.executable, str(SCRIPT), '--config', str(cfg), '--query', query] + (['--auto'] if auto else []) + list(extra)
        env = {**os.environ, 'HOME': str(self.home), 'KM_RULES_PROBE_TIMEOUT': '3'}
        return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=30)


class AutoGate(Base):
    def test_server_down_still_runs(self):
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertRegex(p.stdout, r'^RULES: v\d+ vault_mode=unknown graphrag=(absent|unreachable) ')
        self.assertIn('docs/rules-core/ledger.md', p.stdout)

    def test_same_vault_runs(self):
        srv = FakeServer([{'entity': 'x', 'source_note': 'notes/here.md'}])
        try:
            p = self.run_route(self.config(srv.url))
        finally:
            srv.close()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertRegex(p.stdout, r'^RULES: v\d+ vault_mode=same graphrag=ok ')
        self.assertIn('docs/rules-core/ledger.md', p.stdout)

    def test_other_vault_skips_with_zero_local_reads(self):
        srv = FakeServer([{'entity': 'x', 'source_note': 'elsewhere/not-here.md'}])
        try:
            p = self.run_route(self.config(srv.url))
        finally:
            srv.close()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('skip(vault_mode=other', p.stdout)
        self.assertNotIn('[rules:', p.stdout)

    def test_results_without_paths_are_not_other(self):
        srv = FakeServer([{'entity': 'x'}])
        try:
            p = self.run_route(self.config(srv.url))
        finally:
            srv.close()
        self.assertRegex(p.stdout, r'^RULES: v\d+ vault_mode=unknown graphrag=ok ')
        self.assertIn('[rules:', p.stdout)

    def test_switch_file_runs_as_disabled(self):
        (self.home / '.claude-state').mkdir()
        (self.home / '.claude-state/km-search-graphrag-off').write_text('')
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()))
        self.assertRegex(p.stdout, r'^RULES: v\d+ vault_mode=unknown graphrag=disabled ')
        self.assertIn('[rules:', p.stdout)

    def test_no_rule_corpus_is_off(self):
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port(), corpus=False), auto=False)  # control: same on v1
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.startswith('RULES: off'), p.stdout)


class Ranking(Base):
    def lib(self):
        import importlib.util
        s = importlib.util.spec_from_file_location('kr_under_test', SCRIPT)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        return m

    def test_particle_strip_keeps_two_char_stem(self):
        m = self.lib()
        self.assertEqual(m.tokens('끝까지'), ['끝까지'])
        self.assertEqual(m.tokens('장부는'), ['장부'])

    def test_long_file_does_not_outrank_focused_file(self):
        m = self.lib()
        (self.root / 'docs/rules-core/a.md').write_text(('잡담 ' * 4000) + '장부 한 번\n', encoding='utf-8')
        (self.root / 'docs/rules-core/zz-focused.md').write_text('장부 장부 장부 규칙\n', encoding='utf-8')
        r = m.route('장부', '', str(self.root), None, ['docs/rules-core/*.md'], 5)
        self.assertTrue(r['rg'][0]['path'].endswith('zz-focused.md'), r['rg'])

    def test_root_agent_file_is_in_corpus(self):
        m = self.lib()
        (self.root / 'AGENTS.md').write_text('작업 대장 = sqlite\n', encoding='utf-8')
        r = m.route('대장 어디', '', str(self.root), None, ['docs/rules-core/*.md'], 5)
        self.assertIn(str(self.root / 'AGENTS.md'), [x['path'] for x in r['merged']])


class DecisionMarks(Base):
    """v3: 후보 아래 «결정 표지» 줄 — 뒤에 있는 해제 문단의 줄 번호가 찍히는가."""

    def cue_after(self, out, rel):
        lines = out.splitlines()
        i = [k for k, l in enumerate(lines) if l.startswith('[rules:') and l.endswith(' ' + rel)]
        self.assertTrue(i, out)
        nxt = lines[i[0] + 1] if i[0] + 1 < len(lines) else ''
        return nxt if nxt.lstrip().startswith('↳') else None

    def test_late_release_line_number_is_printed(self):  # 양성 미끼
        body = ['# 위임 규칙', '', '## 코덱스 위임 기본값', '- 09-28: 코덱스 워커 적극 위임.', '- 10-06 시효: 그때만 적용.']
        body += ['- 잡설 %d' % k for k in range(30)]
        body += ['- 10-13 재개: 코덱스 봇에 다시 적극 위임.', '- 세부 1', '- 세부 2',
                 '- 10-13 21시 해제: 코덱스 위임 재개를 끝낸다.']
        (self.root / 'docs/rules-core/codex.md').write_text('\n'.join(body) + '\n', encoding='utf-8')
        release = len(body)  # 마지막 줄 = 해제
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='코덱스 위임 지금 기준')
        self.assertEqual(p.returncode, 0, p.stderr)
        cue = self.cue_after(p.stdout, 'docs/rules-core/codex.md')
        self.assertIsNotNone(cue, p.stdout)
        self.assertRegex(cue, r'표지 줄 [0-9·…]*\b%d\b' % release)
        self.assertIn('%d줄까지 읽고' % release, cue)
        self.assertIn('3–%d줄' % release, cue)  # 질문과 맞는 절 = «## 코덱스 위임 기본값» 절 전체

    def test_file_without_marks_gets_no_cue(self):  # 음성 미끼
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='장부 규칙')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIsNone(self.cue_after(p.stdout, 'docs/rules-core/ledger.md'), p.stdout)

    def test_daecheero_is_not_a_mark(self):  # 「대체로」 = 표지 아님
        (self.root / 'docs/rules-core/ledger.md').write_text('장부 규칙: 대체로 지시 받으면 장부에 적는다.\n', encoding='utf-8')
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='장부 규칙')
        self.assertIsNone(self.cue_after(p.stdout, 'docs/rules-core/ledger.md'), p.stdout)

    def test_candidate_line_format_unchanged(self):  # 집계기가 읽는 `[rules:x] 경로` 줄은 그대로
        (self.root / 'docs/rules-core/codex.md').write_text('## 코덱스\n- 10-13 해제: 코덱스 위임 끝.\n', encoding='utf-8')
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='코덱스 장부')
        cands = [l for l in p.stdout.splitlines() if l.startswith('[rules:')]
        self.assertTrue(cands, p.stdout)
        for l in cands:
            self.assertRegex(l, r'^\[rules:(index|rg)\] \S+$')


class NoteLinks(Base):
    """v4: 후보 원본 안 [[노트]] 를 대본이 볼트(vaultPath) 안에서 미리 풀어 «↳ 가리키는 노트» 줄로 — 모델이 레포 전체 find 를 안 돌게."""

    def note_line(self, out, rel):
        lines = out.splitlines()
        i = [k for k, l in enumerate(lines) if l.startswith('[rules:') and l.endswith(' ' + rel)]
        self.assertTrue(i, out)
        for l in lines[i[0] + 1:]:
            if l.startswith('[rules:'):
                break
            if '↳ 가리키는 노트' in l:
                return l
        return None

    def write_rule(self, body):
        (self.root / 'docs/rules-core/icloud.md').write_text(body, encoding='utf-8')

    def test_linked_note_resolves_to_vault_path(self):  # 양성 미끼
        (self.vault / 'notes/deep').mkdir(parents=True)
        (self.vault / 'notes/deep/binaries-not-vault.md').write_text('x\n', encoding='utf-8')
        (self.vault / '.claude-memory').mkdir()
        (self.vault / '.claude-memory/feedback_hidden_note.md').write_text('x\n', encoding='utf-8')
        self.write_rule('# 납품\n## iCloud 납품\n- 바이너리는 iCloud 에([[binaries-not-vault|별칭]]) · [[feedback_hidden_note#절]]\n')
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='iCloud 납품 바이너리')
        self.assertEqual(p.returncode, 0, p.stderr)
        nl = self.note_line(p.stdout, 'docs/rules-core/icloud.md')
        self.assertIsNotNone(nl, p.stdout)
        self.assertIn('notes/deep/binaries-not-vault.md', nl)
        self.assertIn('.claude-memory/feedback_hidden_note.md', nl)

    def test_rule_without_links_gets_no_note_line(self):  # 음성 미끼
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='장부 규칙')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('docs/rules-core/ledger.md', p.stdout)
        self.assertNotIn('가리키는 노트', p.stdout)

    def test_missing_note_says_not_in_vault(self):  # 없는 노트
        self.write_rule('## iCloud 납품\n- 바이너리는 iCloud 에 [[no-such-note-anywhere]]\n')
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='iCloud 납품 바이너리')
        nl = self.note_line(p.stdout, 'docs/rules-core/icloud.md')
        self.assertIsNotNone(nl, p.stdout)
        self.assertIn('볼트에 없음', nl)
        self.assertIn('no-such-note-anywhere', nl)
        self.assertIn('레포 전체 훑기 ❌', nl)

    def test_link_outside_chosen_section_is_still_resolved(self):  # 실측 꼴: 고른 절 밖(다음 절) 링크
        (self.vault / 'notes/far-note.md').write_text('x\n', encoding='utf-8')
        self.write_rule('## 동기화 대상\n- 동기화 동기화 대상 규칙\n## 납품\n- 파일은 [[far-note]]\n')
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='동기화 대상 파일')
        nl = self.note_line(p.stdout, 'docs/rules-core/icloud.md')
        self.assertIsNotNone(nl, p.stdout)
        self.assertIn('notes/far-note.md', nl)

    def test_rule_corpus_stem_is_labeled_rule_not_absent(self):
        self.write_rule('## iCloud 납품\n- 바이너리 = [[ledger]]\n')
        p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='iCloud 납품 바이너리')
        nl = self.note_line(p.stdout, 'docs/rules-core/icloud.md')
        self.assertIsNotNone(nl, p.stdout)
        self.assertIn('규칙 원본 docs/rules-core/ledger.md', nl)
        self.assertNotIn('볼트에 없음', nl)

    def test_lookup_timeout_is_not_absence(self):  # 시한 넘김(부하) ≠ «볼트에 없음»
        self.write_rule('## iCloud 납품\n- 바이너리는 iCloud 에 [[some-note]]\n')
        os.environ['KM_RULES_NOTE_TIMEOUT'] = '0.000001'
        try:
            p = self.run_route(self.config('http://127.0.0.1:%d' % free_port()), query='iCloud 납품 바이너리', auto=False)
        finally:
            del os.environ['KM_RULES_NOTE_TIMEOUT']
        nl = self.note_line(p.stdout, 'docs/rules-core/icloud.md')
        self.assertIsNotNone(nl, p.stdout)
        self.assertIn('노트 찾기 못 함(시한', nl)
        self.assertNotIn('볼트에 없음', nl)

    def test_lookup_failure_is_not_absence(self):  # 찾기 실패(뿌리 없음) ≠ «볼트에 없음»
        import shutil
        self.write_rule('## iCloud 납품\n- 바이너리는 iCloud 에 [[some-note]]\n')
        cfg = self.config('http://127.0.0.1:%d' % free_port())
        shutil.rmtree(self.vault)
        p = self.run_route(cfg, query='iCloud 납품 바이너리', auto=False)
        nl = self.note_line(p.stdout, 'docs/rules-core/icloud.md')
        self.assertIsNotNone(nl, p.stdout)
        self.assertIn('노트 찾기 못 함', nl)
        self.assertIn("rg --files --hidden -g '<이름>.md' '%s'" % self.vault, nl)  # 칠 명령 = vault 한정
        self.assertNotIn('볼트에 없음', nl)
        self.assertIn('레포 전체 훑기 ❌', nl)


class ReceiptVaultLookupTimeout(unittest.TestCase):
    """영수증 절 vault-lookup 줄 = 시한(KM_VL_TIMEOUT · 기본 20초) — 넘기면 VL_HITS=timeout + «부재 단정 금지» · 자식까지 끔."""

    SLOW = '#!/bin/bash\nsleep 40 &\necho partial\nsleep 40\necho late\n'
    FAST = '#!/bin/bash\necho a\necho b\necho c\n'

    def run_line(self, body, shell):
        import shutil
        import time
        if not shutil.which(shell):
            self.skipTest(shell + ' 없음')
        line = [l for l in SEARCH_MD.read_text(encoding='utf-8').splitlines()
                if l.startswith('if [ "${VAULT_MODE:-}" = other ]; then VL_HITS=skip;')]
        self.assertEqual(len(line), 1)
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / '.claude/scripts').mkdir(parents=True)
            (Path(td) / '.claude/scripts/vault-lookup.sh').write_text(body)
            env = {**os.environ, 'VAULT_MODE': 'same', 'VAULT_PATH': td, 'QUERY': '영상 사진', 'KM_VL_TIMEOUT': '2'}
            t = time.time()
            p = subprocess.run([shell, '-c', line[0]], capture_output=True, text=True, env=env, timeout=90, cwd=td)
            return p.stdout, time.time() - t

    def test_slow_lookup_times_out_bash(self):  # 양성
        out, secs = self.run_line(self.SLOW, 'bash')
        self.assertIn('VL_HITS=timeout', out)
        self.assertIn('VL_UNAVAILABLE=1 — 부재 단정 금지', out)
        self.assertLess(secs, 15, out)  # 자식 sleep 이 출력 통로를 붙잡고 있으면 40초+

    def test_slow_lookup_times_out_zsh(self):  # 양성 · Claude Code Bash = 사용자 셸(zsh)
        out, secs = self.run_line(self.SLOW, 'zsh')
        self.assertIn('VL_HITS=timeout', out)
        self.assertLess(secs, 15, out)

    def test_fast_lookup_counts_lines(self):  # 음성 — 빨리 끝나면 지금과 같음
        for sh in ('bash', 'zsh'):
            out, secs = self.run_line(self.FAST, sh)
            self.assertIn('VL_HITS=3', out, sh)
            self.assertNotIn('VL_UNAVAILABLE', out, sh)
            self.assertNotIn('timeout', out, sh)


class SearchMdContract(unittest.TestCase):
    def setUp(self):
        self.s = SEARCH_MD.read_text(encoding='utf-8')

    def test_rule_step_sits_in_tier0_fence_with_substitutable_root(self):
        tier0 = self.s[self.s.index('## Tier 0'):self.s.index('## 검색 엔진')]
        fence = re.search(r'```bash\n(.*?)```', tier0, re.S).group(1)
        self.assertIn('MB_STATE', fence)
        self.assertIn('"$KM_RULES" --auto', fence)
        self.assertIn('KM_RULES="${CLAUDE_PLUGIN_ROOT}/scripts/km_rules_route.py"', fence)  # `:-` form is not substituted
        self.assertNotIn('VAULT_MODE', fence)  # the gate is the script's, not the model's

    def test_read_to_last_decision_line_present(self):
        tier0 = self.s[self.s.index('## Tier 0'):self.s.index('## 검색 엔진')]
        self.assertIn('날짜순 마지막 결정(해제·대체·정정·철회 표지)까지 읽고', tier0)

    def test_no_repo_wide_find_line_present(self):  # v4: 노트 찾기 = 대본 줄 또는 vault-lookup.sh
        tier0 = self.s[self.s.index('## Tier 0'):self.s.index('## 검색 엔진')]
        self.assertIn('레포 루트 `find .`·`grep -r` ❌', tier0)
        self.assertIn('↳ 가리키는 노트', tier0)

    def test_cli_query_path_uses_bare_root(self):
        self.assertIn('KM_CLI_Q="${CLAUDE_PLUGIN_ROOT}/scripts/km_cli_query.py"', self.s)
        self.assertNotIn('${CLAUDE_PLUGIN_ROOT:-}/scripts/', self.s)  # 경로 줄에 `:-` 꼴 0

    def test_no_runnable_block_left_under_tier1r(self):
        a = self.s.index('#### Tier 1-R')
        b = self.s.index('**other 보호:**', a)
        self.assertNotIn('```bash', self.s[a:b])
        self.assertNotIn('km_rules_route.py --auto` 가', self.s[:a].split('## Tier 0')[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
