import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.diff import run_diff

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

class TestDiffSummary:
    def test_detects_new_sections(self):
        result = run_diff(
            os.path.join(FIXTURES, "existing_note.md"),
            os.path.join(FIXTURES, "updated_note.md")
        )
        assert result["summary"]["new"] >= 1

    def test_detects_changed_sections(self):
        result = run_diff(
            os.path.join(FIXTURES, "existing_note.md"),
            os.path.join(FIXTURES, "updated_note.md")
        )
        assert result["summary"]["changed"] >= 1

    def test_detects_renamed_sections(self):
        result = run_diff(
            os.path.join(FIXTURES, "existing_note.md"),
            os.path.join(FIXTURES, "updated_note.md")
        )
        renamed = [s for s in result["sections"] if s["type"] == "RENAMED"]
        assert len(renamed) >= 1

class TestDiffOutput:
    def test_markdown_field_exists(self):
        result = run_diff(
            os.path.join(FIXTURES, "existing_note.md"),
            os.path.join(FIXTURES, "updated_note.md")
        )
        assert "markdown" in result
        assert "## 변경점 요약" in result["markdown"]

    def test_sections_have_required_fields(self):
        result = run_diff(
            os.path.join(FIXTURES, "existing_note.md"),
            os.path.join(FIXTURES, "updated_note.md")
        )
        for section in result["sections"]:
            assert "type" in section
            assert "heading" in section
            assert section["type"] in ("NEW", "CHANGED", "REMOVED", "RENAMED")

class TestDiffEdgeCases:
    def test_identical_files(self):
        path = os.path.join(FIXTURES, "existing_note.md")
        result = run_diff(path, path)
        assert result["summary"]["new"] == 0
        assert result["summary"]["changed"] == 0
        assert result["summary"]["removed"] == 0

    def test_file_not_found(self):
        result = run_diff("/nonexistent.md", "/also_nonexistent.md")
        assert "error" in result
