"""Orchestreer rapportgeneratie (slice 57)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject

from rcm_desktop.adapter.report_docx_writer import write_report_docx
from rcm_desktop.adapter.report_materialization_service import materialize_report
from rcm_desktop.adapter.report_options import ReportOptions
from rcm_desktop.adapter.report_pdf_exporter import ReportPdfExportError, export_docx_to_pdf
from rcm_desktop.adapter.report_run_source_service import ReportRunBundle


@dataclass(frozen=True)
class ReportGenerationOutcome:
    docx_path: Path
    pdf_path: Path | None
    pdf_error: str | None


def generate_report_files(
    project: RCMProject,
    bundle: ReportRunBundle,
    options: ReportOptions,
    *,
    project_path: Path | None = None,
    pdf_exporter=export_docx_to_pdf,
) -> ReportGenerationOutcome:
    document = materialize_report(
        project,
        bundle,
        options,
        project_path=project_path,
    )
    docx_path = write_report_docx(document, options.output_docx_path)
    pdf_path: Path | None = None
    pdf_error: str | None = None
    if options.generate_pdf:
        try:
            pdf_path = pdf_exporter(docx_path)
        except ReportPdfExportError as exc:
            pdf_error = str(exc)
    return ReportGenerationOutcome(
        docx_path=docx_path,
        pdf_path=pdf_path,
        pdf_error=pdf_error,
    )
