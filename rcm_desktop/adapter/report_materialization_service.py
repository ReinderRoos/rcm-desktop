"""Bouw ReportDocument uit project + runs (slice 57)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rcm_core.effect_impact_service import aggregate, collect_fm_ids_for_functie
from rcm_core.models import RCMProject

from rcm_desktop import messages
from rcm_desktop.adapter.contribution_chart_service import build_contribution_rows
from rcm_desktop.adapter.kpi_table_service import build_kpi_compare_table, build_kpi_table
from rcm_desktop.adapter.report_chart_renderer import (
    build_project_lcc_curve,
    build_project_unavailability_chart,
    render_lcc_chart_png,
    render_unavailability_chart_png,
)
from rcm_desktop.adapter.report_document import (
    ReportDocument,
    ReportFigure,
    ReportParagraph,
    ReportSection,
    ReportTable,
)
from rcm_desktop.adapter.report_functie_selection_service import (
    ReportFunctieChapter,
    select_report_functies,
)
from rcm_desktop.adapter.report_narrative_service import (
    build_functie_narrative,
    build_kpi_narrative,
)
from rcm_desktop.adapter.report_options import ReportOptions
from rcm_desktop.adapter.report_run_source_service import ReportRunBundle
from rcm_desktop.adapter.results_workspace_state import (
    ContributionPresentation,
    METRIC_KOSTEN,
    METRIC_NIET_BESCHIKBAARHEID,
    SOURCE_FAALWIJZE,
    SOURCE_PBS,
)
from rcm_desktop.adapter.unavailability_chart_service import build_unavailability_chart_input

_REPORT_PRESENTATION = ContributionPresentation(
    horizon="lifecycle",
    unavailability_display="percent",
)
_TOP_N = 10


def materialize_report(
    project: RCMProject,
    bundle: ReportRunBundle,
    options: ReportOptions,
    *,
    project_path: Path | None = None,
) -> ReportDocument:
    primary = bundle.scenarios[0]
    selection = select_report_functies(
        project,
        primary,
        scope_id=options.scope_id,
        nb_threshold_pct=options.nb_threshold_pct,
        cost_threshold_pct=options.cost_threshold_pct,
        include_below_threshold=options.include_below_threshold,
    )
    sections: list[ReportSection] = [
        _build_cover(project, bundle, project_path=project_path),
        _build_kpi_section(project, bundle, options),
        _build_project_charts_section(project, bundle),
    ]
    for chapter in selection.nb_chapters:
        sections.append(
            _build_functie_section(
                project,
                bundle,
                chapter,
                kind="nb",
                metric=METRIC_NIET_BESCHIKBAARHEID,
                section_prefix="Niet-beschikbaarheid",
            )
        )
    for chapter in selection.cost_chapters:
        sections.append(
            _build_functie_section(
                project,
                bundle,
                chapter,
                kind="kosten",
                metric=METRIC_KOSTEN,
                section_prefix="Kosten",
            )
        )
    sections.append(_build_appendix(selection))
    return ReportDocument(sections=tuple(sections))


def _build_cover(
    project: RCMProject,
    bundle: ReportRunBundle,
    *,
    project_path: Path | None,
) -> ReportSection:
    name = project.projectnaam.strip()
    if not name and project_path is not None:
        name = project_path.stem
    if not name:
        name = "RCM-project"
    modelleur = project.modelleur.strip() or "—"
    mode_label = (
        messages.REPORT_COVER_SCENARIO_COMPARE
        if bundle.mode == "compare"
        else messages.REPORT_COVER_SCENARIO_SINGLE
    )
    scenario_lines = [f"{s.key}: {s.label}" for s in bundle.scenarios]
    return ReportSection(
        title=messages.REPORT_SECTION_COVER,
        paragraphs=(
            ReportParagraph(text=f"Project: {name}"),
            ReportParagraph(text=f"Modelleur: {modelleur}"),
            ReportParagraph(text=f"Datum: {datetime.now().date().isoformat()}"),
            ReportParagraph(text=mode_label),
            ReportParagraph(text="Scenario's: " + "; ".join(scenario_lines)),
        ),
    )


def _build_kpi_section(
    project: RCMProject,
    bundle: ReportRunBundle,
    options: ReportOptions,
) -> ReportSection:
    if bundle.mode == "compare" and len(bundle.scenarios) >= 2:
        scenarios = tuple(
            (s.key, s.label, s.run_result) for s in bundle.scenarios[:2]
        )
        table = build_kpi_compare_table(
            project=project,
            scenarios=scenarios,
            scope_id=options.scope_id,
        )
    else:
        table = build_kpi_table(
            project=project,
            run_result=bundle.scenarios[0].run_result,
            scope_id=options.scope_id,
        )
    headers = ("KPI",) + table.scenario_labels
    rows = tuple(
        (row.label,) + tuple(cell.display for cell in row.cells) for row in table.rows
    )
    context = messages.REPORT_KPI_CONTEXT_TEMPLATE.format(
        lifecycle_years=int(project.config.lifecycle_years),
        modeljaar=int(project.config.modeljaar),
    )
    narrative = build_kpi_narrative(bundle, table)
    return ReportSection(
        title=messages.REPORT_SECTION_KPI,
        paragraphs=(ReportParagraph(text=context),)
        + tuple(ReportParagraph(text=t) for t in narrative),
        tables=(
            ReportTable(headers=headers, rows=rows),
        ),
    )


def _build_project_charts_section(
    project: RCMProject,
    bundle: ReportRunBundle,
) -> ReportSection:
    children: list[ReportSection] = []
    for scenario in bundle.scenarios:
        nb_chart = build_project_unavailability_chart(project, scenario.run_result)
        if nb_chart is not None:
            png = render_unavailability_chart_png(nb_chart)
            children.append(
                ReportSection(
                    title=f"{messages.REPORT_SECTION_PROJECT_NB} — {scenario.label}",
                    figures=(
                        ReportFigure(
                            png_bytes=png,
                            caption=messages.REPORT_APPENDIX_NB_PROXY,
                        ),
                    ),
                )
            )
        lcc = build_project_lcc_curve(
            project, scenario.run_result, scenario.overlay_at_run
        )
        if lcc is not None:
            png = render_lcc_chart_png(lcc)
            children.append(
                ReportSection(
                    title=f"{messages.REPORT_SECTION_PROJECT_LCC} — {scenario.label}",
                    figures=(ReportFigure(png_bytes=png, caption=scenario.label),),
                )
            )
    if not children:
        return ReportSection(title=messages.REPORT_SECTION_PROJECT_NB, paragraphs=())
    if len(children) == 1:
        return children[0]
    return ReportSection(
        title="Projectoverzicht",
        children=tuple(children),
    )


def _functie_scope_id(project: RCMProject, functie_id: str) -> str | None:
    functie = project.functies.get(functie_id)
    if functie is None:
        return None
    return functie.pbs_id


def _build_functie_section(
    project: RCMProject,
    bundle: ReportRunBundle,
    chapter: ReportFunctieChapter,
    *,
    kind: str,
    metric: str,
    section_prefix: str,
) -> ReportSection:
    scope_id = _functie_scope_id(project, chapter.functie_id)
    scope_kind = "nb" if metric == METRIC_NIET_BESCHIKBAARHEID else "cost"
    fm_scope = collect_fm_ids_for_functie(project, chapter.functie_id, scope_kind)
    children: list[ReportSection] = []
    primary = bundle.scenarios[0]
    narrative = build_functie_narrative(
        chapter,
        kind=kind,
        project_share_pct=chapter.impact_pct,
    )
    header = (
        f"{section_prefix}: {chapter.title} — "
        f"effectklassen: {', '.join(chapter.effect_klasse_labels) or '—'}"
    )
    for scenario in bundle.scenarios:
        top_rows = build_contribution_rows(
            project,
            scenario.run_result,
            source=SOURCE_FAALWIJZE,
            metric=metric,
            top_n=_TOP_N,
            scope_id=None,
            fm_ids=fm_scope,
            presentation=_REPORT_PRESENTATION,
        )
        table_rows = tuple(
            (r.label, f"{r.value:.2f}", f"{r.share_pct:.1f}%") for r in top_rows
        )
        children.append(
            ReportSection(
                title=f"Top 10 — {scenario.label}",
                tables=(
                    ReportTable(
                        headers=("Component", "Waarde", "Aandeel %"),
                        rows=table_rows,
                    ),
                ),
            )
        )
        chart = build_unavailability_chart_input(
            project,
            scenario.run_result,
            scope_id=scope_id,
        )
        if chart is not None and metric == METRIC_NIET_BESCHIKBAARHEID:
            children.append(
                ReportSection(
                    title=f"Tijdsplot — {scenario.label}",
                    figures=(
                        ReportFigure(
                            png_bytes=render_unavailability_chart_png(chart),
                            caption=messages.REPORT_APPENDIX_NB_PROXY,
                        ),
                    ),
                )
            )
        if metric == METRIC_KOSTEN:
            from rcm_desktop.adapter.report_chart_renderer import build_project_lcc_curve

            lcc = build_project_lcc_curve(
                project, scenario.run_result, scenario.overlay_at_run
            )
            if lcc is not None:
                children.append(
                    ReportSection(
                        title=f"LCC — {scenario.label}",
                        figures=(
                            ReportFigure(
                                png_bytes=render_lcc_chart_png(lcc),
                                caption=scenario.label,
                            ),
                        ),
                    )
                )
        fm_dict = {fr.fm_id: fr for fr in scenario.run_result.fm_core_results}
        effect_impact_rows = aggregate(
            project,
            fm_dict,
            fm_ids=fm_scope,
        )
        if effect_impact_rows:
            children.append(
                ReportSection(
                    title=f"Effectimpact — {scenario.label}",
                    tables=(
                        ReportTable(
                            headers=("Effectklasse", "Waarde", "Eenheid", "RF", "Aandeel %"),
                            rows=tuple(
                                (
                                    r.label,
                                    f"{r.waarde_totaal:.2f}",
                                    r.eenheid,
                                    r.rf_display,
                                    f"{r.share_pct:.1f}%",
                                )
                                for r in effect_impact_rows
                            ),
                        ),
                    ),
                )
            )
        pbs_rows = build_contribution_rows(
            project,
            scenario.run_result,
            source=SOURCE_PBS,
            metric=metric,
            top_n=_TOP_N,
            scope_id=scope_id,
            presentation=_REPORT_PRESENTATION,
        )
        children.append(
            ReportSection(
                title=f"PBS-opbouw — {scenario.label}",
                tables=(
                    ReportTable(
                        headers=("Component", "Waarde", "Aandeel %"),
                        rows=tuple(
                            (r.label, f"{r.value:.2f}", f"{r.share_pct:.1f}%")
                            for r in pbs_rows
                        ),
                    ),
                ),
            )
        )
    return ReportSection(
        title=header,
        paragraphs=tuple(ReportParagraph(text=t) for t in narrative),
        children=tuple(children),
    )


def _build_appendix(selection) -> ReportSection:
    return ReportSection(
        title=messages.REPORT_SECTION_APPENDIX,
        paragraphs=(
            ReportParagraph(text=messages.REPORT_APPENDIX_NB_PROXY),
            ReportParagraph(text=messages.REPORT_APPENDIX_NB_OVER_100),
            ReportParagraph(
                text=messages.REPORT_APPENDIX_BELOW_THRESHOLD.format(
                    nb_count=selection.excluded_nb_count,
                    cost_count=selection.excluded_cost_count,
                )
            ),
        ),
    )
