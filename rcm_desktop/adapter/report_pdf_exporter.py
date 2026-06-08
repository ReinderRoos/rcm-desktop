"""Converteer docx naar PDF via LibreOffice (slice 57)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class ReportPdfExportError(Exception):
    pass


def _find_soffice_executable() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found and Path(found).is_file():
            return found
    for env_key in ("LIBREOFFICE_PROGRAM", "SOFFICE_PATH"):
        candidate = os.environ.get(env_key, "").strip()
        if candidate:
            path = Path(candidate)
            if path.is_file():
                return str(path)
            program = path / "soffice.exe"
            if program.is_file():
                return str(program)
    for program_dir in (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "LibreOffice" / "program",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "LibreOffice"
        / "program",
    ):
        soffice = program_dir / "soffice.exe"
        if soffice.is_file():
            return str(soffice)
    return None


def export_docx_to_pdf(docx_path: Path, *, soffice_executable: str | None = None) -> Path:
    exe = soffice_executable or _find_soffice_executable()
    if not exe:
        raise ReportPdfExportError(
            "LibreOffice (soffice) niet gevonden. Installeer LibreOffice of exporteer handmatig naar PDF."
        )
    if not Path(exe).is_file() and shutil.which(str(exe)) is None:
        raise ReportPdfExportError(
            "LibreOffice (soffice) niet gevonden. Installeer LibreOffice of exporteer handmatig naar PDF."
        )
    out_dir = docx_path.parent
    cmd = [
        exe,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(docx_path),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ReportPdfExportError(detail or f"PDF-conversie mislukt (exit {completed.returncode})")
    pdf_path = docx_path.with_suffix(".pdf")
    if not pdf_path.is_file():
        raise ReportPdfExportError("PDF-bestand niet aangemaakt na conversie.")
    return pdf_path
