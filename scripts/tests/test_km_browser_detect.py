#!/usr/bin/env python3
"""Contract: km browser auto-detect picks ego lite → Aside → fallback with no user setup.

Each case builds a throw-away home folder and PATH with fake `ego-browser` / `aside`
programs (shell scripts), then runs the real script as a subprocess.
Run: python3 -I -B scripts/tests/test_km_browser_detect.py
"""
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "km_browser_detect.py")

EGO_OK = '#!/bin/sh\nif [ "$1" = skill ]; then echo "[ego-browser:skill] guide"; echo "[ego-browser:skill] end of guide v2.2.0"; exit 0; fi\nexit 0\n'
EGO_BROKEN = '#!/bin/sh\necho "cannot connect" >&2\nexit 3\n'
EGO_NO_GUIDE_END = '#!/bin/sh\necho "[ego-browser:skill] guide (cut)"\nexit 0\n'
EGO_HANG = '#!/bin/sh\nsleep 30\n'
ASIDE_OK = '#!/bin/sh\nif [ "$1" = --version ]; then echo 1.26.0; exit 0; fi\nexit 0\n'


def _write(path, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(body)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class Env:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, "home")
        self.bin = os.path.join(self.tmp.name, "bin")
        os.makedirs(self.home)
        os.makedirs(self.bin)

    def put_path(self, name, body):
        _write(os.path.join(self.bin, name), body)

    def put_home(self, rel, body):
        _write(os.path.join(self.home, rel), body)

    def run(self, *args, timeout_env=None):
        env = {"HOME": self.home, "PATH": self.bin + os.pathsep + "/usr/bin:/bin"}
        if timeout_env:
            env["KM_BROWSER_PROBE_TIMEOUT"] = timeout_env
        r = subprocess.run([sys.executable, "-I", "-B", SCRIPT, *args], env=env,
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise AssertionError(f"rc={r.returncode} err={r.stderr}")
        return json.loads(r.stdout)

    def close(self):
        self.tmp.cleanup()


class Detect(unittest.TestCase):
    def setUp(self):
        self.e = Env()

    def tearDown(self):
        self.e.close()

    # --- the four verdicts asked for --------------------------------------
    def test_1_ego_only(self):
        self.e.put_path("ego-browser", EGO_OK)
        d = self.e.run()
        self.assertEqual(d["provider"], "ego")
        self.assertTrue(d["bin"].endswith("ego-browser"))
        self.assertFalse(d["detected"]["aside"]["found"])

    def test_2_aside_only(self):
        self.e.put_path("aside", ASIDE_OK)
        d = self.e.run()
        self.assertEqual(d["provider"], "aside")
        self.assertFalse(d["detected"]["ego"]["found"])

    def test_3_both_ego_first(self):
        self.e.put_path("ego-browser", EGO_OK)
        self.e.put_path("aside", ASIDE_OK)
        d = self.e.run()
        self.assertEqual(d["provider"], "ego")
        self.assertTrue(d["detected"]["aside"]["ready"])

    def test_4_none_fallback(self):
        d = self.e.run()
        self.assertEqual(d["provider"], "fallback")
        self.assertIsNone(d["bin"])
        self.assertEqual(d["order"], ["ego", "aside", "fallback"])

    # --- not on PATH: fixed install folders, absolute path printed --------
    def test_ego_fixed_folder_not_on_path(self):
        self.e.put_home(".local/bin/ego-browser", EGO_OK)
        d = self.e.run()
        self.assertEqual(d["provider"], "ego")
        self.assertEqual(d["bin"], os.path.join(self.e.home, ".local/bin/ego-browser"))

    def test_aside_app_folder_with_space(self):
        self.e.put_home(".aside/cli/Aside CLI.app/Contents/MacOS/aside", ASIDE_OK)
        d = self.e.run()
        self.assertEqual(d["provider"], "aside")
        self.assertIn("Aside CLI.app", d["bin"])

    # --- installed but not answering → next in order (negative pair) ------
    def test_ego_broken_falls_to_aside(self):
        self.e.put_path("ego-browser", EGO_BROKEN)
        self.e.put_path("aside", ASIDE_OK)
        d = self.e.run()
        self.assertEqual(d["provider"], "aside")
        self.assertTrue(d["detected"]["ego"]["found"])
        self.assertFalse(d["detected"]["ego"]["ready"])

    def test_ego_guide_without_end_is_not_ready(self):
        self.e.put_path("ego-browser", EGO_NO_GUIDE_END)
        d = self.e.run()
        self.assertEqual(d["provider"], "fallback")

    def test_probe_timeout_does_not_hang(self):
        self.e.put_path("ego-browser", EGO_HANG)
        t0 = time.time()
        d = self.e.run(timeout_env="1")
        self.assertLess(time.time() - t0, 15)
        self.assertEqual(d["detected"]["ego"]["why"], "probe timeout")
        self.assertEqual(d["provider"], "fallback")

    # --- km-config.json browser.provider -----------------------------------
    def test_prefer_aside_when_both(self):
        self.e.put_path("ego-browser", EGO_OK)
        self.e.put_path("aside", ASIDE_OK)
        self.assertEqual(self.e.run("--prefer", "aside")["provider"], "aside")

    def test_prefer_aside_missing_goes_ego(self):
        # 1.8.4/1.8.5 template default was "aside": with no Aside, ego lite must still be used
        self.e.put_path("ego-browser", EGO_OK)
        self.assertEqual(self.e.run("--prefer", "aside")["provider"], "ego")

    def test_prefer_playwright_legacy_default_still_auto(self):
        self.e.put_path("ego-browser", EGO_OK)
        self.assertEqual(self.e.run("--prefer", "playwright")["provider"], "ego")

    def test_prefer_hyperbrowser_explicit(self):
        self.e.put_path("ego-browser", EGO_OK)
        self.assertEqual(self.e.run("--prefer", "hyperbrowser")["provider"], "hyperbrowser")

    def test_aside_broken_falls_to_fallback(self):
        self.e.put_path("aside", EGO_BROKEN)
        d = self.e.run()
        self.assertEqual(d["provider"], "fallback")
        self.assertTrue(d["detected"]["aside"]["found"])
        self.assertFalse(d["detected"]["aside"]["ready"])

    def test_aside_prints_version_but_fails_is_not_ready(self):
        # rc check alone (output looks fine, exit code says no)
        self.e.put_path("aside", '#!/bin/sh\necho 1.26.0\nexit 7\n')
        d = self.e.run()
        self.assertEqual(d["provider"], "fallback")
        self.assertEqual(d["detected"]["aside"]["why"], "probe exit 7")

    def test_ego_full_guide_but_fails_is_not_ready(self):
        self.e.put_path("ego-browser", '#!/bin/sh\necho "[ego-browser:skill] end of guide v2.2.0"\nexit 5\n')
        d = self.e.run()
        self.assertEqual(d["provider"], "fallback")
        self.assertEqual(d["detected"]["ego"]["why"], "probe exit 5")

    def test_both_hang_fallback_within_limit(self):
        self.e.put_path("ego-browser", EGO_HANG)
        self.e.put_path("aside", EGO_HANG)
        t0 = time.time()
        d = self.e.run(timeout_env="1")
        self.assertLess(time.time() - t0, 20)
        self.assertEqual(d["provider"], "fallback")
        self.assertEqual(d["detected"]["aside"]["why"], "probe timeout")

    # --- --config reads browser.provider itself ----------------------------
    def _cfg(self, body):
        p = os.path.join(self.e.tmp.name, "km-config.json")
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        return p

    def test_config_aside_used_when_both(self):
        self.e.put_path("ego-browser", EGO_OK)
        self.e.put_path("aside", ASIDE_OK)
        cfg = self._cfg('{"browser": {"provider": "aside"}}')
        self.assertEqual(self.e.run("--config", cfg)["provider"], "aside")

    def test_config_missing_or_broken_is_auto(self):
        self.e.put_path("ego-browser", EGO_OK)
        self.e.put_path("aside", ASIDE_OK)
        bad = self._cfg("{not json")
        d = self.e.run("--config", os.path.join(self.e.tmp.name, "nope.json"), "--config", bad)
        self.assertEqual((d["provider"], d["prefer"]), ("ego", "auto"))

    def test_prefer_flag_beats_config(self):
        self.e.put_path("ego-browser", EGO_OK)
        self.e.put_path("aside", ASIDE_OK)
        cfg = self._cfg('{"browser": {"provider": "aside"}}')
        self.assertEqual(self.e.run("--config", cfg, "--prefer", "ego")["provider"], "ego")

    def test_get_field(self):
        self.e.put_path("aside", ASIDE_OK)
        env = {"HOME": self.e.home, "PATH": self.e.bin + os.pathsep + "/usr/bin:/bin"}
        r = subprocess.run([sys.executable, "-I", "-B", SCRIPT, "--get", "provider"], env=env,
                           capture_output=True, text=True, timeout=60)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "aside"))


class DocsWiring(unittest.TestCase):
    """The docs that open web pages call the detector, and new configs default to auto."""
    ROOT = os.path.dirname(os.path.dirname(HERE))

    def read(self, rel):
        with open(os.path.join(self.ROOT, rel), encoding="utf-8") as f:
            return f.read()

    def test_docs_call_detector(self):
        for rel in ("commands/knowledge-manager.md", "skills/km-browser-abstraction.md",
                    ".agent/skills/km-browser-abstraction/SKILL.md"):
            s = self.read(rel)
            self.assertIn("scripts/km_browser_detect.py", s, rel)
            self.assertIn("provider=ego", s, rel)
            self.assertIn("provider=fallback", s, rel)
            self.assertIn('--config "./km-config.json"', s, rel)
            self.assertNotIn('--prefer "auto"', s, rel)

    def test_no_scrapling_missing_skips_browser_slot(self):
        # every doc in the plugin: «no Scrapling → straight to playwright-cli» must not skip the browser slot
        bad = ("별도 준비, 없으면 playwright-cli", "별도 준비, 없으면 `playwright-cli`",
               "없으면 `playwright-cli` 로 갑니다")
        hits = []
        for top in ("commands", "skills", "agents", ".agent"):
            for dirpath, _, files in os.walk(os.path.join(self.ROOT, top)):
                for fn in files:
                    if fn.endswith(".md"):
                        p = os.path.join(dirpath, fn)
                        with open(p, encoding="utf-8") as f:
                            s = f.read()
                        hits += [f"{os.path.relpath(p, self.ROOT)}: {b}" for b in bad if b in s]
        self.assertEqual(hits, [])
        # positive pair: the replacement wording is really there
        self.assertIn("없으면 브라우저 자동 탐색(ego lite → Aside), 그다음 playwright-cli",
                      self.read("agents/knowledge-manager.md"))

    def test_setup_detects_before_playwright_question(self):
        s = self.read("commands/knowledge-manager-setup.md")
        a = s.find("km_browser_detect.py")
        b = s.find("### Playwright 설치 (브라우저가 없을 때만)")
        self.assertTrue(0 < a < b, "setup must run the detector before the Playwright question")
        self.assertNotIn("### Playwright 설치 (필수)", s)
        self.assertIn("Playwright 는 설치하지 않아도 돼요", s)

    def test_new_configs_default_auto(self):
        cfg = json.loads(self.read("km-config.example.json"))
        self.assertEqual(cfg["browser"]["provider"], "auto")
        self.assertIn('provider: "auto"', self.read("commands/knowledge-manager-setup.md"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
