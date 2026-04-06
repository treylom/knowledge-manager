import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.state import run_state, STATE_DIR, STEP_ORDER, PREREQUISITES

@pytest.fixture(autouse=True)
def use_tmp_state_dir(tmp_path, monkeypatch):
    """모든 테스트에서 임시 state 디렉토리 사용."""
    monkeypatch.setattr("lib.state.STATE_DIR", str(tmp_path))

class TestInit:
    def test_creates_session_file(self):
        result = run_state("init")
        assert "session_id" in result
        assert result["completed"] == {}
        assert result["current"] == "STEP-0"

    def test_returns_file_path(self):
        result = run_state("init")
        assert "file" in result
        assert os.path.exists(result["file"])

class TestComplete:
    def test_complete_step0(self):
        run_state("init")
        result = run_state("complete", "STEP-0")
        assert result["completed"]["STEP-0"] is not None
        assert result["current"] == "STEP-0.5"

    def test_skip_detection(self):
        run_state("init")
        result = run_state("complete", "STEP-2")
        assert result["error"] == "STEP_SKIP_DETECTED"
        assert "STEP-0" in result["missing"]

    def test_prerequisite_enforcement(self):
        run_state("init")
        for s in STEP_ORDER[:STEP_ORDER.index("STEP-4") + 1]:
            run_state("complete", s)
        result = run_state("complete", "STEP-5")
        assert result["error"] == "STEP_SKIP_DETECTED"
        assert "STEP-4.5" in result["missing"]

    def test_duplicate_complete_is_noop(self):
        run_state("init")
        run_state("complete", "STEP-0")
        result = run_state("complete", "STEP-0")
        assert "error" not in result

class TestCheck:
    def test_check_ready(self):
        run_state("init")
        result = run_state("check", "STEP-0")
        assert result["ready"] is True

    def test_check_not_ready(self):
        run_state("init")
        result = run_state("check", "STEP-4.5")
        assert result["ready"] is False
        assert len(result["missing"]) > 0

class TestShow:
    def test_show_empty(self):
        run_state("init")
        result = run_state("show")
        assert result["completed"] == {}
        assert result["progress"] == "0/12"

    def test_show_after_steps(self):
        run_state("init")
        run_state("complete", "STEP-0")
        run_state("complete", "STEP-0.5")
        result = run_state("show")
        assert result["progress"] == "2/12"
