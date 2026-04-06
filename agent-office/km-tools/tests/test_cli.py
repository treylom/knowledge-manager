"""End-to-end CLI tests via subprocess."""
import json
import os
import subprocess
import sys
import pytest

KM_TOOLS = os.path.join(os.path.dirname(__file__), "..", "km-tools.py")
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def run_cli(*args):
    result = subprocess.run(
        [sys.executable, KM_TOOLS, *args],
        capture_output=True, text=True, timeout=10
    )
    return result


class TestCLILint:
    def test_lint_json_output(self):
        r = run_cli("lint", os.path.join(FIXTURES, "good_draft.md"),
                     "--consistency", "0.8", "--suggestions", "0.7", "--coverage", "0.9")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "lint_score" in data
        assert "breakdown" in data

    def test_lint_without_llm_args(self):
        r = run_cli("lint", os.path.join(FIXTURES, "good_draft.md"))
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert len(data["warnings"]) == 3


class TestCLIDiff:
    def test_diff_json_output(self):
        r = run_cli("diff",
                     os.path.join(FIXTURES, "existing_note.md"),
                     os.path.join(FIXTURES, "updated_note.md"))
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "summary" in data
        assert "markdown" in data

    def test_diff_identical(self):
        path = os.path.join(FIXTURES, "existing_note.md")
        r = run_cli("diff", path, path)
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["summary"]["new"] == 0


class TestCLIState:
    def test_state_init(self):
        r = run_cli("state", "init")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "session_id" in data

    def test_state_show(self):
        run_cli("state", "init")
        r = run_cli("state", "show")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "progress" in data


class TestCLIErrors:
    def test_missing_subcommand(self):
        r = run_cli()
        assert r.returncode != 0

    def test_lint_missing_file(self):
        r = run_cli("lint", "/nonexistent.md")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["error"] == "FILE_NOT_FOUND"
