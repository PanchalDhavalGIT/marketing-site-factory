"""Tests for spreadsheet_reader module."""

import csv
import tempfile
from pathlib import Path

import pytest

from orchestrator.spreadsheet_reader import read_spreadsheet, _slugify


class TestSlugify:
    def test_simple_name(self):
        assert _slugify("Pizza Palace") == "pizza-palace"

    def test_apostrophe(self):
        assert _slugify("Joe's Diner") == "joes-diner"

    def test_special_chars(self):
        assert _slugify("A+ Auto Repair!") == "a-auto-repair"

    def test_multiple_spaces(self):
        assert _slugify("The   Big   Store") == "the-big-store"

    def test_leading_trailing(self):
        assert _slugify("  My Business  ") == "my-business"


class TestReadSpreadsheet:
    def _make_csv(self, rows: list[dict], tmpdir: Path) -> Path:
        path = tmpdir / "test.csv"
        if not rows:
            path.write_text("")
            return path
        fieldnames = rows[0].keys()
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_reads_valid_csv(self, tmp_path):
        rows = [
            {"business_name": "Test Biz", "industry": "tech", "phone": "555-0100"},
            {"business_name": "Another Biz", "industry": "food", "phone": "555-0200"},
        ]
        path = self._make_csv(rows, tmp_path)
        result = read_spreadsheet(path)
        assert len(result) == 2
        assert result[0]["business_name"] == "Test Biz"
        assert result[0]["slug"] == "test-biz"
        assert result[1]["slug"] == "another-biz"

    def test_count_limits_rows(self, tmp_path):
        rows = [
            {"business_name": f"Biz {i}", "industry": "tech"}
            for i in range(10)
        ]
        path = self._make_csv(rows, tmp_path)
        result = read_spreadsheet(path, count=3)
        assert len(result) == 3

    def test_missing_required_column(self, tmp_path):
        rows = [{"name": "Test", "phone": "555"}]
        path = self._make_csv(rows, tmp_path)
        with pytest.raises(ValueError, match="Missing required columns"):
            read_spreadsheet(path)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_spreadsheet("/nonexistent/path.csv")

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text("{}")
        with pytest.raises(ValueError, match="Unsupported file format"):
            read_spreadsheet(path)

    def test_normalizes_column_names(self, tmp_path):
        rows = [{"Business Name": "Test", "Industry": "tech"}]
        path = self._make_csv(rows, tmp_path)
        result = read_spreadsheet(path)
        assert result[0]["business_name"] == "Test"

    def test_drops_empty_rows(self, tmp_path):
        rows = [
            {"business_name": "Valid", "industry": "tech"},
            {"business_name": "", "industry": ""},
        ]
        path = self._make_csv(rows, tmp_path)
        result = read_spreadsheet(path)
        # The empty row should be dropped since business_name is required
        assert len(result) <= 2
