import os
import sys
import tempfile
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

class TestEvalSource:
    """--eval-source provenance stamp (blind subagent eval design, D-2)."""
    LLM_METRICS = ("consistency", "suggestions", "coverage")

    def test_default_source_is_llm_backward_compat(self):
        # No eval_source arg → existing callers get identical output.
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0)
        for m in self.LLM_METRICS:
            assert result["breakdown"][m]["source"] == "llm"

    def test_subagent_source_stamped(self):
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0,
                          eval_source="subagent:sonnet")
        for m in self.LLM_METRICS:
            assert result["breakdown"][m]["source"] == "subagent:sonnet"

    def test_self_source_stamped(self):
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0,
                          eval_source="self")
        for m in self.LLM_METRICS:
            assert result["breakdown"][m]["source"] == "self"

    def test_mechanical_metrics_have_no_source(self):
        # completeness/connections are computed, not judged → no provenance stamp.
        result = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0,
                          eval_source="subagent:sonnet")
        assert "source" not in result["breakdown"]["completeness"]
        assert "source" not in result["breakdown"]["connections"]

    def test_score_unchanged_by_eval_source(self):
        # Provenance stamp must not alter the numeric score.
        base = run_lint(os.path.join(FIXTURES, "good_draft.md"), 0.9, 0.85, 0.95)
        stamped = run_lint(os.path.join(FIXTURES, "good_draft.md"), 0.9, 0.85, 0.95,
                           eval_source="subagent:sonnet")
        assert base["lint_score"] == stamped["lint_score"]

class TestProofClass:
    """Top-level proof_class + schema_version (§7 검증 사다리 정직 표기, 보강3)."""
    def test_subagent_is_independent(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0,
                     eval_source="subagent:sonnet")
        assert r["proof_class"] == "independent"

    def test_self_is_self_lint(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0,
                     eval_source="self")
        assert r["proof_class"] == "self-lint"

    def test_default_llm_is_self_lint(self):
        # legacy/self-eval default → not independently verified.
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0)
        assert r["proof_class"] == "self-lint"

    def test_schema_version_present(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0)
        assert "schema_version" in r


class TestJudgedScoreClamping:
    """Judged metrics (LLM/subagent) out of [0,1] clamped, not trusted raw (2026-07-23 공개 전 견고화)."""
    def test_above_one_clamped(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.5, 1.0, 1.0)
        assert r["breakdown"]["consistency"]["value"] == 1.0
        assert any("consistency" in w and "clamped" in w for w in r["warnings"])

    def test_negative_clamped(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), -0.5, 1.0, 1.0)
        assert r["breakdown"]["consistency"]["value"] == 0.0
        assert any("consistency" in w for w in r["warnings"])

    def test_clamp_prevents_score_over_one(self):
        # All judged metrics hallucinated high must not push lint_score above 1.0.
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 5.0, 5.0, 5.0)
        assert r["lint_score"] <= 1.0

    def test_in_range_not_clamped(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 0.7, 0.7, 0.7)
        assert not any("clamped" in w for w in r["warnings"])

    def test_exact_bounds_not_clamped(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 0.0, 1.0, 0.5)
        assert not any("clamped" in w for w in r["warnings"])


class TestThresholdBoundary:
    """Pass/fail boundary at exactly 0.7 (off-by-one on the gate)."""
    def test_exactly_threshold_passes(self):
        # good_draft: comp 1.0*.20 + conn 1.0*.20 = 0.40 mechanical.
        # judged all=0.5 → 0.5*(.25+.15+.20)=0.30 → total 0.70 → passed (>= 0.7).
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 0.5, 0.5, 0.5)
        assert r["lint_score"] == 0.7
        assert r["passed"] is True

    def test_just_below_threshold_fails(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 0.49, 0.49, 0.49)
        assert r["lint_score"] < 0.7
        assert r["passed"] is False


class TestMalformedDrafts:
    """Robustness against empty / no-frontmatter / body-only / huge drafts (no crash)."""
    def _tmp(self, content):
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_empty_file(self):
        p = self._tmp("")
        try:
            r = run_lint(p, 1.0, 1.0, 1.0)
            assert r["breakdown"]["completeness"]["value"] == 0.0
            assert r["breakdown"]["connections"]["value"] == 0.2
            assert "lint_score" in r
        finally:
            os.remove(p)

    def test_no_frontmatter_body_only(self):
        p = self._tmp("# Title\n\nBody with [[LinkA]] and [[LinkB]] and [[LinkC]].\n")
        try:
            r = run_lint(p, 1.0, 1.0, 1.0)
            assert r["breakdown"]["completeness"]["value"] == 0.0
            assert r["breakdown"]["connections"]["detail"]["count"] == 3
        finally:
            os.remove(p)

    def test_frontmatter_but_no_body(self):
        p = self._tmp("---\ntags: [x]\nauthor: me\ndate: 2026-07-23\nsource: http://x\naliases: [y]\n---\n")
        try:
            r = run_lint(p, 1.0, 1.0, 1.0)
            assert r["breakdown"]["completeness"]["value"] == 1.0
            assert r["breakdown"]["connections"]["value"] == 0.2  # zero links
        finally:
            os.remove(p)

    def test_large_draft_no_crash(self):
        body = "\n".join(f"para {i} [[Link{i % 5}]]" for i in range(5000))
        p = self._tmp("---\ntags: [x]\n---\n" + body)
        try:
            r = run_lint(p, 0.8, 0.8, 0.8)
            assert "lint_score" in r
            assert r["breakdown"]["connections"]["detail"]["count"] == 5000
        finally:
            os.remove(p)


class TestEvalSourceEdgeCases:
    """Exact provenance contract: case-sensitive 'subagent:' prefix, no leading space."""
    def test_empty_eval_source_is_self_lint(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0, eval_source="")
        assert r["proof_class"] == "self-lint"
        assert r["breakdown"]["consistency"]["source"] == ""

    def test_subagent_prefix_variants_independent(self):
        for src in ("subagent:sonnet", "subagent:opus", "subagent:gpt-5"):
            r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0, eval_source=src)
            assert r["proof_class"] == "independent", f"{src} should be independent"

    def test_lookalike_not_independent(self):
        for src in ("subagent", "self-subagent", "SubAgent:sonnet", " subagent:x"):
            r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0, eval_source=src)
            assert r["proof_class"] == "self-lint", f"{src!r} wrongly independent"

    def test_unicode_eval_source_preserved(self):
        r = run_lint(os.path.join(FIXTURES, "good_draft.md"), 1.0, 1.0, 1.0, eval_source="subagent:손석희")
        assert r["proof_class"] == "independent"
        assert r["breakdown"]["consistency"]["source"] == "subagent:손석희"
