from __future__ import annotations

from pathlib import Path

import pytest

from rcm_desktop.adapter.report_pdf_exporter import ReportPdfExportError, export_docx_to_pdf


def test_pdf_export_raises_when_soffice_missing(tmp_path: Path) -> None:
    docx = tmp_path / "r.docx"
    docx.write_bytes(b"PK")
    with pytest.raises(ReportPdfExportError):
        export_docx_to_pdf(docx, soffice_executable="__missing_soffice__")
