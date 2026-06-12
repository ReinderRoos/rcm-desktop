"""RCM-Cost benchmark parity — vergelijk motorresultaten met AW-export (ADR-0008)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from rcm_core.models import FMResult, RCMProject
from rcm_core.fm_parity_diagnostics import (
    aw_expected_failures,
    compute_fm_input_diagnostics,
    compute_rev_diagnostics,
    format_year_list,
)

_CAUSE_SETTINGS_KEY = "isograph_causes"


class ParityVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INFORMATIVE = "informative"
    MISSING_BENCHMARK = "missing_benchmark"


@dataclass(frozen=True)
class ParitySummary:
    pass_count: int
    fail_count: int
    informative_count: int
    missing_benchmark_count: int
    benchmark_fm_count: int


@dataclass(frozen=True)
class ParityRow:
    fm_id: str
    verdict: ParityVerdict
    total_cost_aw: float | None
    total_cost_rcm: float | None
    total_cost_delta: float | None
    total_cost_tolerance: float | None
    total_tdt_aw: float | None
    total_tdt_rcm: float | None
    total_tdt_delta: float | None
    total_tdt_tolerance: float | None
    # Diagnostiek (informative — verklaart rekentechnische afwijkingen)
    expected_failures_aw: float | None
    expected_failures_rcm: float | None
    expected_failures_delta: float | None
    rev_moments_active: int
    rev_moments_structural: int
    rev_years_active: str
    rev_intervals_years: str
    cm_downtime_aw: float | None
    cm_downtime_rcm: float | None
    pm_downtime_aw: float | None
    pm_downtime_rcm: float | None
    insp_downtime_aw: float | None
    cm_cost_rcm: float | None
    pm_cost_rcm: float | None
    p_failure_lifecycle_rcm: float | None
    current_age_years: float | None
    mttf_aw_years: float | None
    mttf_rcm_years: float | None
    pm_task_summary: str


@dataclass(frozen=True)
class ParityReport:
    rows: tuple[ParityRow, ...]
    summary: ParitySummary


def aw_tolerance_eur(
    aw_value: float,
    *,
    err_pc: float | None,
    err_abs: float | None,
) -> float:
    """AW-onzekerheidsband: max(abs, err% × |AW-waarde|); err% in procentpunten."""
    parts: list[float] = []
    if err_abs is not None and float(err_abs) > 0:
        parts.append(float(err_abs))
    if err_pc is not None and float(err_pc) > 0:
        parts.append(float(err_pc) / 100.0 * abs(aw_value))
    return max(parts) if parts else 0.0


def metric_within_aw_band(
    *,
    actual: float,
    aw_value: float,
    err_pc: float | None,
    err_abs: float | None,
) -> bool:
    tolerance = aw_tolerance_eur(aw_value, err_pc=err_pc, err_abs=err_abs)
    if tolerance <= 0:
        return False
    return abs(actual - aw_value) <= tolerance


def _cause_meta(project: RCMProject) -> dict[str, Any]:
    settings = project.import_settings or {}
    raw = settings.get(_CAUSE_SETTINGS_KEY) or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def has_aw_benchmarks(project: RCMProject) -> bool:
    for meta in _cause_meta(project).values():
        if not isinstance(meta, dict):
            continue
        if meta.get("TotalCost") not in (None, ""):
            return True
    return False


def _float_or_none(raw: object) -> float | None:
    if raw in (None, ""):
        return None
    return float(raw)


def _metric_check(
    *,
    actual: float | None,
    aw_value: float | None,
    err_pc: float | None,
    err_abs: float | None,
    gates: bool,
) -> tuple[ParityVerdict, float | None, float | None]:
    if aw_value is None:
        return ParityVerdict.MISSING_BENCHMARK, None, None
    if actual is None:
        return ParityVerdict.INFORMATIVE, None, aw_tolerance_eur(
            aw_value, err_pc=err_pc, err_abs=err_abs
        )
    tolerance = aw_tolerance_eur(aw_value, err_pc=err_pc, err_abs=err_abs)
    delta = actual - aw_value
    if not gates or tolerance <= 0:
        return ParityVerdict.INFORMATIVE, delta, tolerance
    if abs(delta) <= tolerance:
        return ParityVerdict.PASS, delta, tolerance
    return ParityVerdict.FAIL, delta, tolerance


def _combine_verdicts(*verdicts: ParityVerdict) -> ParityVerdict:
    if ParityVerdict.FAIL in verdicts:
        return ParityVerdict.FAIL
    gated = [v for v in verdicts if v in (ParityVerdict.PASS, ParityVerdict.FAIL)]
    if gated and all(v == ParityVerdict.PASS for v in gated):
        return ParityVerdict.PASS
    if ParityVerdict.INFORMATIVE in verdicts:
        return ParityVerdict.INFORMATIVE
    if all(v == ParityVerdict.MISSING_BENCHMARK for v in verdicts):
        return ParityVerdict.MISSING_BENCHMARK
    return ParityVerdict.INFORMATIVE


def build_parity_report(
    project: RCMProject,
    fm_results: Mapping[str, FMResult],
) -> ParityReport:
    cause_meta = _cause_meta(project)
    rows: list[ParityRow] = []
    pass_count = fail_count = informative_count = missing_benchmark_count = benchmark_fm_count = 0

    for fm_id in sorted(fm_results):
        result = fm_results[fm_id]
        meta = cause_meta.get(fm_id)
        meta_dict = meta if isinstance(meta, dict) else {}

        aw_cost = _float_or_none(meta_dict.get("TotalCost"))
        aw_tdt = _float_or_none(meta_dict.get("TotalTdt"))
        rcm_cost = result.total_cost_eur
        rcm_tdt = result.expected_total_downtime_hr + result.expected_pm_downtime_hr

        cost_verdict, cost_delta, cost_tol = _metric_check(
            actual=rcm_cost,
            aw_value=aw_cost,
            err_pc=_float_or_none(meta_dict.get("TotalCostErrPc")),
            err_abs=_float_or_none(meta_dict.get("TotalCostErrAbs")),
            gates=True,
        )
        tdt_verdict, tdt_delta, tdt_tol = _metric_check(
            actual=rcm_tdt,
            aw_value=aw_tdt,
            err_pc=_float_or_none(meta_dict.get("TotalTdtErr")),
            err_abs=None,
            gates=_float_or_none(meta_dict.get("TotalTdtErr")) is not None,
        )
        verdict = _combine_verdicts(cost_verdict, tdt_verdict)

        lifecycle = float(project.config.lifecycle_years)
        aw_ef = aw_expected_failures(meta_dict, lifecycle_years=lifecycle)
        rcm_ef = result.expected_failures
        ef_delta = (rcm_ef - aw_ef) if aw_ef is not None else None

        rev = compute_rev_diagnostics(project, fm_id)
        inputs = compute_fm_input_diagnostics(project, fm_id)
        pm_summary = ", ".join(f"{k}={v}" for k, v in inputs.pm_task_counts) or "—"

        if aw_cost is not None:
            benchmark_fm_count += 1
        if verdict == ParityVerdict.PASS:
            pass_count += 1
        elif verdict == ParityVerdict.FAIL:
            fail_count += 1
        elif verdict == ParityVerdict.MISSING_BENCHMARK:
            missing_benchmark_count += 1
        else:
            informative_count += 1

        rows.append(
            ParityRow(
                fm_id=fm_id,
                verdict=verdict,
                total_cost_aw=aw_cost,
                total_cost_rcm=rcm_cost,
                total_cost_delta=cost_delta,
                total_cost_tolerance=cost_tol,
                total_tdt_aw=aw_tdt,
                total_tdt_rcm=rcm_tdt,
                total_tdt_delta=tdt_delta,
                total_tdt_tolerance=tdt_tol,
                expected_failures_aw=aw_ef,
                expected_failures_rcm=rcm_ef,
                expected_failures_delta=ef_delta,
                rev_moments_active=rev.active_moments,
                rev_moments_structural=rev.structural_moments,
                rev_years_active=format_year_list(rev.active_years),
                rev_intervals_years=format_year_list(rev.active_intervals_years, max_items=4),
                cm_downtime_aw=_float_or_none(meta_dict.get("CTdt")),
                cm_downtime_rcm=result.expected_total_downtime_hr,
                pm_downtime_aw=_float_or_none(meta_dict.get("PTdt")),
                pm_downtime_rcm=result.expected_pm_downtime_hr,
                insp_downtime_aw=_float_or_none(meta_dict.get("ITdt")),
                cm_cost_rcm=result.expected_cm_cost_eur,
                pm_cost_rcm=result.pm_cost_eur,
                p_failure_lifecycle_rcm=result.p_failure_lifecycle,
                current_age_years=inputs.current_age_years,
                mttf_aw_years=inputs.mttf_aw_years,
                mttf_rcm_years=inputs.mttf_years,
                pm_task_summary=pm_summary,
            )
        )

    summary = ParitySummary(
        pass_count=pass_count,
        fail_count=fail_count,
        informative_count=informative_count,
        missing_benchmark_count=missing_benchmark_count,
        benchmark_fm_count=benchmark_fm_count,
    )
    return ParityReport(rows=tuple(rows), summary=summary)
