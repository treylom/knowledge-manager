#!/usr/bin/env python3
"""POSIX rename-boundary signals, not a hardware power-loss simulation.

Each signal is sent by the test's mv child to its installer parent after a
successful rename. No signal is sent to the test runner or a process group.
Only temporary project trees are installed into or removed by this suite.
"""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install-to-project.sh"
DIRECTORIES = ("commands", "skills", "agents", "scripts")
CHECKPOINTS = tuple("aside-" + d for d in DIRECTORIES) + tuple(
    "place-" + d for d in DIRECTORIES
) + ("config",)


def snapshot(root):
    """Record paths, file bytes and modes; fail on a read error, never skip it."""
    result = {}
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            result[relative] = ("link", os.readlink(path))
        elif path.is_dir():
            result[relative] = ("dir", path.stat().st_mode & 0o777)
        else:
            result[relative] = ("file", path.stat().st_mode & 0o777, path.read_bytes())
    return result


@unittest.skipUnless(os.name == "posix", "requires POSIX signals and bash")
class InstallSignals(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="km-signal-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        # The shell waits for a foreground child; this does not inherit the
        # ignored SIGINT disposition of an asynchronous shell job.
        patterns = []
        for directory in DIRECTORIES:
            patterns += [
                f"aside-{directory}:*/.claude/{directory}:*/.km-install-staging.*.old-{directory}",
                f"place-{directory}:*/.km-install-staging.*/{directory}:*/.claude/{directory}",
            ]
        patterns += ["config:*/.km-install-staging.*/km-config.example.json:*/km-config.example.json"]
        wrapper = """#!/bin/bash
set -eu
case "${KM_TEST_AT:-}:$1:${2:-}" in
  PATTERNS)
    "${KM_REAL_MV}" "$@"
    printf '%s\\n' "${KM_TEST_AT}" >> "${KM_TEST_MARKER}"
    kill -"${KM_TEST_SIGNAL}" "${PPID}"
    exit 0 ;;
esac
if [ "${KM_TEST_REPEAT:-0}" = 1 ] && [ "${2:-}" = "${KM_TEST_PROJECT}/.claude/skills" ]; then
  "${KM_REAL_MV}" "$@"
  printf '%s\\n' 'cleanup-signal' >> "${KM_TEST_MARKER}"
  kill -"${KM_TEST_SIGNAL}" "${PPID}"
  exit 0
fi
exec "${KM_REAL_MV}" "$@"
""".replace("PATTERNS", "|".join(patterns))
        fake_mv = self.fake_bin / "mv"
        fake_mv.write_text(wrapper)
        fake_mv.chmod(0o755)
        self.env = os.environ.copy()
        self.env.pop("KM_SOURCE_ROOT", None)
        self.env.update(PATH=str(self.fake_bin) + os.pathsep + os.environ["PATH"],
                        KM_REAL_MV=shutil.which("mv"), KM_TEST_REPEAT="0")

    def project(self, name, config=False):
        project = self.root / name
        for directory in DIRECTORIES:
            destination = project / ".claude" / directory
            destination.mkdir(parents=True)
            (destination / "private.txt").write_bytes(b"private:" + directory.encode())
        (project / ".claude/commands/search.md").write_bytes(b"ORIGINAL\x00SEARCH\n")
        if config:
            (project / "km-config.example.json").write_bytes(b"EXISTING CONFIG\n")
        return project

    def install(self, project, checkpoint, sig, repeat=False):
        marker = self.root / (project.name + ".injected")
        env = dict(self.env, KM_TEST_AT=checkpoint, KM_TEST_SIGNAL=sig,
                   KM_TEST_MARKER=str(marker), KM_TEST_PROJECT=str(project),
                   KM_TEST_REPEAT="1" if repeat else "0")
        result = subprocess.run(["bash", str(INSTALLER), str(project)], env=env,
                                capture_output=True, timeout=30)
        self.assertTrue(marker.is_file(), "requested rename boundary was not reached")
        return result, marker.read_text().splitlines()

    def test_catchable_signals_at_every_rename(self):
        # 3 signals x 9 rename boundaries = 27 independent projects.
        for sig in ("HUP", "INT", "TERM"):
            for checkpoint in CHECKPOINTS:
                with self.subTest(signal=sig, checkpoint=checkpoint):
                    project = self.project(sig + "-" + checkpoint)
                    before = snapshot(project)
                    result, injections = self.install(project, checkpoint, sig)
                    self.assertEqual(injections, [checkpoint])
                    self.assertEqual(result.returncode, 128 + getattr(signal, "SIG" + sig), result.stderr)
                    self.assertEqual(snapshot(project), before)
                    self.assertIn(b"the previous files were put back", result.stderr)

    def test_second_signal_does_not_interrupt_cleanup(self):
        for sig in ("HUP", "INT", "TERM"):
            with self.subTest(signal=sig):
                project = self.project("second-" + sig, config=True)
                before = snapshot(project)
                result, injections = self.install(project, "place-skills", sig, repeat=True)
                self.assertEqual(injections, ["place-skills", "cleanup-signal"])
                self.assertEqual(result.returncode, 128 + getattr(signal, "SIG" + sig))
                self.assertEqual(snapshot(project), before)

    def test_kill_keeps_previous_bytes_and_retry_refuses_residue(self):
        # SIGKILL cannot run EXIT cleanup. Verify recoverable files and a
        # non-mutating retry, not automatic rollback or disk durability.
        for checkpoint in CHECKPOINTS:
            with self.subTest(checkpoint=checkpoint):
                project = self.project("kill-" + checkpoint)
                before = snapshot(project)
                result, injections = self.install(project, checkpoint, "KILL")
                self.assertEqual(result.returncode, -signal.SIGKILL)
                self.assertEqual(injections, [checkpoint])
                claude = project / ".claude"
                stages = [p for p in claude.glob(".km-install-staging.*") if ".old-" not in p.name]
                self.assertEqual(len(stages), 1)
                for relative, value in before.items():
                    if value[0] != "file":
                        continue
                    _, directory, name = relative.split("/", 2)
                    old = claude / (stages[0].name + ".old-" + directory) / name
                    current = project / relative
                    self.assertTrue(any(p.is_file() and p.read_bytes() == value[2]
                                        for p in (old, current)), relative)
                after_kill = snapshot(project)
                retry = subprocess.run(["bash", str(INSTALLER), str(project)],
                                       env=self.env, capture_output=True, timeout=30)
                self.assertNotEqual(retry.returncode, 0, "unfinished install was silently replaced")
                self.assertIn(b"unfinished install", retry.stderr)
                self.assertEqual(snapshot(project), after_kill)

    def test_orphan_backup_alone_is_not_deleted(self):
        project = self.project("orphan")
        old = project / ".claude/.km-install-staging.123.old-commands"
        old.mkdir()
        (old / "only-surviving-copy").write_bytes(b"KEEP\x00ME")
        before = snapshot(project)
        result = subprocess.run(["bash", str(INSTALLER), str(project)],
                                capture_output=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"unfinished install", result.stderr)
        self.assertEqual(snapshot(project), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
