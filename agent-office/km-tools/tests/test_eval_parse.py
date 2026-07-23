import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.eval_parse import extract_eval_json, extract_eval_score


class TestExtractEvalJson:
    """Fence/prose-tolerant JSON extraction (closes D-3 bench gap #4: 2/13 fenced runs)."""
    def test_bare_json(self):
        assert extract_eval_json('{"score": 0.8, "reason": "ok"}')["score"] == 0.8

    def test_json_code_fence(self):
        raw = '```json\n{"score": 0.7, "evidence": ["a.md:1"]}\n```'
        r = extract_eval_json(raw)
        assert r["score"] == 0.7
        assert r["evidence"] == ["a.md:1"]

    def test_plain_code_fence(self):
        assert extract_eval_json('```\n{"score": 0.6}\n```')["score"] == 0.6

    def test_prose_before_and_after(self):
        raw = 'Here is my evaluation:\n{"score": 0.55, "reason": "meh"}\nHope that helps!'
        assert extract_eval_json(raw)["score"] == 0.55

    def test_fence_with_prose_outside(self):
        raw = 'Sure!\n```json\n{"score": 0.9}\n```\nDone.'
        assert extract_eval_json(raw)["score"] == 0.9

    def test_none_input(self):
        assert extract_eval_json(None)["error"] == "EMPTY_INPUT"

    def test_empty_string(self):
        assert extract_eval_json("   ")["error"] == "EMPTY_INPUT"

    def test_no_json(self):
        assert extract_eval_json("no json here at all")["error"] == "NO_JSON_FOUND"

    def test_json_array_not_object(self):
        # a top-level array is not an evaluator object
        assert extract_eval_json("[1, 2, 3]")["error"] == "NO_JSON_FOUND"

    def test_first_fenced_object_wins(self):
        raw = '```json\n{"score": 0.4}\n```\nand also {"score": 0.99}'
        assert extract_eval_json(raw)["score"] == 0.4

    def test_nested_braces_prose_wrapped(self):
        raw = 'result: {"score": 0.5, "meta": {"k": [1, 2]}} end'
        r = extract_eval_json(raw)
        assert r["score"] == 0.5
        assert r["meta"]["k"] == [1, 2]


class TestExtractEvalScore:
    """Score extraction + [0,1] clamp (never raises)."""
    def test_score_extracted(self):
        assert extract_eval_score('{"score": 0.72}')["score"] == 0.72

    def test_score_clamped_high(self):
        r = extract_eval_score('{"score": 1.4}')
        assert r["score"] == 1.0
        assert r["clamped"] is True

    def test_score_clamped_low(self):
        r = extract_eval_score('{"score": -0.2}')
        assert r["score"] == 0.0
        assert r["clamped"] is True

    def test_in_range_not_clamped(self):
        r = extract_eval_score('{"score": 0.65}')
        assert r["clamped"] is False

    def test_fenced_score(self):
        assert extract_eval_score('```json\n{"score": 0.65}\n```')["score"] == 0.65

    def test_missing_score_key(self):
        assert extract_eval_score('{"reason": "x"}')["error"] == "MISSING_SCORE"

    def test_non_numeric_score(self):
        assert extract_eval_score('{"score": "high"}')["error"] == "SCORE_NOT_NUMERIC"

    def test_custom_metric_key(self):
        assert extract_eval_score('{"consistency": 0.8}', metric="consistency")["score"] == 0.8

    def test_parse_error_propagates(self):
        assert extract_eval_score("garbage")["error"] == "NO_JSON_FOUND"
