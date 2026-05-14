"""Unit tests for export_utils — verify all 4 formats generate correctly."""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.skills.export_utils import (
    save_md, save_docx, save_pptx, save_xlsx,
    save_all_formats, _parse_sections, _parse_table_rows,
)

SAMPLE_CONTENT = """# SEO 关键词研究报告

## 数据总览

| 关键词 | 搜索量 | 竞争度 |
|--------|--------|--------|
| standing desk | 22000 | 高 |
| electric desk | 49500 | 高 |

## 结论

这些关键词商业价值极高。
"""


class TestExportMd:
    def test_save_md(self, tmp_path):
        import tools.skills.export_utils as mod
        old_dir = mod.EXPORTS_DIR
        mod.EXPORTS_DIR = tmp_path
        try:
            fname = save_md(SAMPLE_CONTENT, "test-report")
            path = tmp_path / fname
            assert path.exists()
            content = path.read_text()
            assert "SEO 关键词研究报告" in content
            assert "| standing desk | 22000 | 高 |" in content
        finally:
            mod.EXPORTS_DIR = old_dir


class TestExportDocx:
    def test_save_docx(self, tmp_path):
        import tools.skills.export_utils as mod
        old_dir = mod.EXPORTS_DIR
        mod.EXPORTS_DIR = tmp_path
        try:
            fname = save_docx(SAMPLE_CONTENT, "test-report")
            if not fname:
                pytest.skip("python-docx not installed")
            path = tmp_path / fname
            assert path.exists()
            assert path.stat().st_size > 1000  # Should have real content
        finally:
            mod.EXPORTS_DIR = old_dir


class TestExportPptx:
    def test_save_pptx(self, tmp_path):
        import tools.skills.export_utils as mod
        old_dir = mod.EXPORTS_DIR
        mod.EXPORTS_DIR = tmp_path
        try:
            fname = save_pptx(SAMPLE_CONTENT, "test-report")
            if not fname:
                pytest.skip("python-pptx not installed")
            path = tmp_path / fname
            assert path.exists()
            assert path.stat().st_size > 5000
        finally:
            mod.EXPORTS_DIR = old_dir


class TestExportXlsx:
    def test_save_xlsx_extracts_table(self, tmp_path):
        import tools.skills.export_utils as mod
        old_dir = mod.EXPORTS_DIR
        mod.EXPORTS_DIR = tmp_path
        try:
            fname = save_xlsx(SAMPLE_CONTENT, "test-report")
            if not fname:
                pytest.skip("openpyxl not installed")
            path = tmp_path / fname
            assert path.exists()

            import openpyxl
            wb = openpyxl.load_workbook(str(path))
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            assert len(rows) >= 3  # header + 2 data rows
            assert rows[0][0] == "关键词" or rows[0][0] == "Content"
        finally:
            mod.EXPORTS_DIR = old_dir


class TestSaveAllFormats:
    def test_returns_all_four(self, tmp_path):
        import tools.skills.export_utils as mod
        old_dir = mod.EXPORTS_DIR
        mod.EXPORTS_DIR = tmp_path
        try:
            result = save_all_formats(SAMPLE_CONTENT, "full-report")
            assert "md" in result
            assert "docx" in result
            assert "pptx" in result
            assert "xlsx" in result
            for ext, fname in result.items():
                if fname:
                    assert (tmp_path / fname).exists()
        finally:
            mod.EXPORTS_DIR = old_dir


class TestParseSections:
    def test_extracts_headings(self):
        sections = _parse_sections(SAMPLE_CONTENT)
        assert len(sections) >= 2
        assert sections[0]["title"] == "SEO 关键词研究报告"


class TestParseTableRows:
    def test_extracts_table(self):
        rows = _parse_table_rows(SAMPLE_CONTENT)
        assert len(rows) >= 3  # header + separator + 2 data
