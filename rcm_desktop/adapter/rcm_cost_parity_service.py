"""RCM-Cost parity adapter — view-DTO's voor modelcontrole (slice 65)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import FMResult, RCMProject
from rcm_core.rcm_cost_benchmark import (
    ParityReport,
    ParityVerdict,
    build_parity_report,
    has_aw_benchmarks,
)


@dataclass(frozen=True)
class ParityViewRow:
    fm_id: str
    omschrijving: str
    verdict: ParityVerdict
    verdict_label: str
    aw_total_cost: str
    rcm_total_cost: str
    cost_delta: str
    cost_tolerance: str
    aw_total_tdt: str
    rcm_total_tdt: str
    aw_expected_failures: str
    rcm_expected_failures: str
    failures_delta: str
    rev_moments: str
    rev_years: str
    rev_intervals: str
    aw_cm_downtime: str
    rcm_cm_downtime: str
    aw_pm_downtime: str
    rcm_pm_downtime: str
    aw_insp_downtime: str
    rcm_cm_cost: str
    rcm_pm_cost: str
    p_fail_rcm: str
    current_age: str
    mttf_aw: str
    mttf_rcm: str
    pm_tasks: str


@dataclass(frozen=True)
class ParityViewSummary:
    pass_count: int
    fail_count: int
    informative_count: int
    missing_benchmark_count: int
    benchmark_fm_count: int
    headline: str


@dataclass(frozen=True)
class ParityView:
    rows: tuple[ParityViewRow, ...]
    summary: ParityViewSummary
    has_benchmarks: bool


def _fmt_eur(value: float | None) -> str:
    if value is None:
        return "—"
    return f"€{value:,.2f}"


def _fmt_hr(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.2f}"


def _fmt_count(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.3g}"


def _fmt_delta(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:+,.3g}"


def _fmt_years(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:g}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.2g}%"


_VERDICT_LABELS = {
    ParityVerdict.PASS: "OK",
    ParityVerdict.FAIL: "Afwijking",
    ParityVerdict.INFORMATIVE: "Info",
    ParityVerdict.MISSING_BENCHMARK: "Geen AW",
}


def build_parity_view(project: RCMProject, fm_results: dict[str, FMResult]) -> ParityView:
    report = build_parity_report(project, fm_results)
    rows = tuple(_to_view_row(project, row) for row in report.rows)
    summary = _to_view_summary(report)
    return ParityView(
        rows=rows,
        summary=summary,
        has_benchmarks=has_aw_benchmarks(project),
    )


def _to_view_row(project: RCMProject, row) -> ParityViewRow:
    fm = project.faalwijzes.get(row.fm_id)
    omschrijving = fm.faalwijze_omschrijving if fm is not None else row.fm_id
    rev_label = f"{row.rev_moments_active}"
    if row.rev_moments_structural != row.rev_moments_active:
        rev_label = f"{row.rev_moments_active} ({row.rev_moments_structural} struct.)"
    return ParityViewRow(
        fm_id=row.fm_id,
        omschrijving=omschrijving,
        verdict=row.verdict,
        verdict_label=_VERDICT_LABELS[row.verdict],
        aw_total_cost=_fmt_eur(row.total_cost_aw),
        rcm_total_cost=_fmt_eur(row.total_cost_rcm),
        cost_delta=_fmt_delta(row.total_cost_delta),
        cost_tolerance=_fmt_eur(row.total_cost_tolerance),
        aw_total_tdt=_fmt_hr(row.total_tdt_aw),
        rcm_total_tdt=_fmt_hr(row.total_tdt_rcm),
        aw_expected_failures=_fmt_count(row.expected_failures_aw),
        rcm_expected_failures=_fmt_count(row.expected_failures_rcm),
        failures_delta=_fmt_delta(row.expected_failures_delta),
        rev_moments=rev_label,
        rev_years=row.rev_years_active,
        rev_intervals=row.rev_intervals_years,
        aw_cm_downtime=_fmt_hr(row.cm_downtime_aw),
        rcm_cm_downtime=_fmt_hr(row.cm_downtime_rcm),
        aw_pm_downtime=_fmt_hr(row.pm_downtime_aw),
        rcm_pm_downtime=_fmt_hr(row.pm_downtime_rcm),
        aw_insp_downtime=_fmt_hr(row.insp_downtime_aw),
        rcm_cm_cost=_fmt_eur(row.cm_cost_rcm),
        rcm_pm_cost=_fmt_eur(row.pm_cost_rcm),
        p_fail_rcm=_fmt_pct(row.p_failure_lifecycle_rcm),
        current_age=_fmt_years(row.current_age_years),
        mttf_aw=_fmt_years(row.mttf_aw_years),
        mttf_rcm=_fmt_years(row.mttf_rcm_years),
        pm_tasks=row.pm_task_summary,
    )


def _to_view_summary(report: ParityReport) -> ParityViewSummary:
    s = report.summary
    headline = (
        f"{s.pass_count} OK · {s.fail_count} afwijking · "
        f"{s.informative_count} info · {s.missing_benchmark_count} zonder AW-benchmark"
    )
    return ParityViewSummary(
        pass_count=s.pass_count,
        fail_count=s.fail_count,
        informative_count=s.informative_count,
        missing_benchmark_count=s.missing_benchmark_count,
        benchmark_fm_count=s.benchmark_fm_count,
        headline=headline,
    )
