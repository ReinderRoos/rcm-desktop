"""Regelgebaseerde rapportteksten (slice 57)."""

from __future__ import annotations

from rcm_desktop import messages
from rcm_desktop.adapter.kpi_table_service import (
    KPI_KEY_LIFECYCLE_COSTS_EUR,
    KPI_KEY_UNAVAILABILITY_PCT,
    KPITable,
)
from rcm_desktop.adapter.report_functie_selection_service import ReportFunctieChapter
from rcm_desktop.adapter.report_run_source_service import ReportRunBundle


def build_kpi_narrative(bundle: ReportRunBundle, kpi_table: KPITable) -> tuple[str, ...]:
    paragraphs: list[str] = []
    if bundle.mode == "compare" and len(bundle.scenarios) >= 2:
        keys = {s.scenario_key for s in bundle.scenarios}
        if len(keys) > 1:
            paragraphs.append(messages.REPORT_NARRATIVE_SCENARIO_MISMATCH)
        delta_row = next(
            (row for row in kpi_table.rows if row.key == KPI_KEY_UNAVAILABILITY_PCT),
            None,
        )
        if delta_row is not None and len(delta_row.cells) >= 3:
            raw = delta_row.cells[-1].raw
            if isinstance(raw, (int, float)) and abs(float(raw)) >= 0.01:
                paragraphs.append(
                    f"Het verschil in lifecycle niet-beschikbaarheid bedraagt {abs(float(raw)):.4f} %-punt."
                )
        cost_row = next(
            (row for row in kpi_table.rows if row.key == KPI_KEY_LIFECYCLE_COSTS_EUR),
            None,
        )
        if cost_row is not None and len(cost_row.cells) >= 3:
            raw = cost_row.cells[-1].raw
            if isinstance(raw, (int, float)) and abs(float(raw)) >= 1.0:
                paragraphs.append(
                    f"Het verschil in lifecycle kosten bedraagt {abs(float(raw)):,.0f} EUR."
                )
    if not paragraphs:
        paragraphs.append(
            "De KPI's hieronder zijn gebaseerd op de voltooide motorrun(s) met vaste projectscope."
        )
    return tuple(paragraphs[:4])


def build_functie_narrative(
    chapter: ReportFunctieChapter,
    *,
    kind: str,
    project_share_pct: float,
) -> tuple[str, ...]:
    ek_text = ", ".join(chapter.effect_klasse_labels) if chapter.effect_klasse_labels else "—"
    lines = [
        f"Functie-aandeel t.o.v. project ({kind}): {chapter.impact_pct:.2f}% "
        f"(projecttotaal-context: {project_share_pct:.2f}%).",
        f"Gekoppelde effectklassen: {ek_text}.",
    ]
    return tuple(lines)
