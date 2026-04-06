import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.lint import run_lint

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

class TestCompleteness:
    def test_full_frontmatter(self):
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0)
        assert result["breakdown"]["completeness"]["value"] == 1.0

    def test_partial_frontmatter(self):
        result = run_lint(os.path.join(FIXTURES, "bad_draft.md"), 1.0, 1.0, 1.0)
        assert result["breakdown"]["completeness"]["value"] == 0.2  # 1/5

class TestConnections:
    def test_good_connections(self):
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0)
        detail = result["breakdown"]["connections"]["detail"]
        assert detail["count"] == 6
        assert result["breakdown"]["connections"]["value"] == 1.0

    def test_no_connections(self):
        result = run_lint(os.path.join(FIXTURES, "bad_draft.md"), 1.0, 1.0, 1.0)
        assert result["breakdown"]["connections"]["value"] == 0.2

class TestLintScore:
    def test_perfect_score(self):
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0)
        assert result["lint_score"] == 1.0
        assert result["passed"] is True

    def test_threshold(self):
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), 0.3, 0.3, 0.3)
        assert result["passed"] == (result["lint_score"] >= 0.7)

    def test_missing_llm_args_warns(self):
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), None, None, None)
        assert len(result["warnings"]) == 3
        assert result["breakdown"]["consistency"]["value"] == 0.0

    def test_file_not_found(self):
        result = run_lint("/nonexistent.md", 1.0, 1.0, 1.0)
        assert "error" in result
