"""FM-parity diagnostiek — REV-schema, inputparameters (Qt-vrij, slice 65+)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import PMTask, RCMProject, TaskType
from rcm_core.units import HOURS_PER_YEAR


@dataclass(frozen=True)
class RevDiagnostics:
    """REV-momenten en kalenderjaren binnen lifecycle."""

    active_moments: int
    structural_moments: int
    active_years: tuple[float, ...]
    structural_years: tuple[float, ...]
    active_intervals_years: tuple[float, ...]


@dataclass(frozen=True)
class FmInputDiagnostics:
    """Invoerparameters die rekentechnische verschillen verklaren."""

    current_age_years: float
    mttf_years: float
    initial_age_aw_years: float | None
    mttf_aw_years: float | None
    pm_task_counts: tuple[tuple[str, int], ...]


def rev_calendar_years(interval_years: float, lifecycle_years: float) -> tuple[float, ...]:
    """Kalenderjaren (vanaf t=0) waarop REV valt binnen lifecycle."""
    if interval_years <= 1e-15 or lifecycle_years <= 0:
        return ()
    years: list[float] = []
    k = 1
    while True:
        t = k * interval_years
        if t > lifecycle_years + 1e-9:
            break
        years.append(t)
        k += 1
    return tuple(years)


def _rev_tasks_for_fm(project: RCMProject, fm_id: str) -> list[PMTask]:
    return [
        t
        for t in project.get_pm_tasks_for_fm(fm_id)
        if t.taak_type == TaskType.REV and float(t.interval_jaar) > 0
    ]


def _disabled_pm_ids(project: RCMProject) -> set[str]:
    raw = (project.import_settings or {}).get("aw_disabled_pm_ids") or []
    if not isinstance(raw, list):
        return set()
    return {str(x) for x in raw}


def compute_rev_diagnostics(project: RCMProject, fm_id: str) -> RevDiagnostics:
    """REV-momenten actief (run) vs structureel (AW-export, incl. uitgeschakeld)."""
    lifecycle = float(project.config.lifecycle_years)
    disabled = _disabled_pm_ids(project)
    rev_tasks = _rev_tasks_for_fm(project, fm_id)

    active_years: set[float] = set()
    structural_years: set[float] = set()
    active_moments = 0
    structural_moments = 0
    active_intervals: list[float] = []

    for task in rev_tasks:
        interval = float(task.interval_jaar)
        years = rev_calendar_years(interval, lifecycle)
        structural_moments += len(years)
        structural_years.update(years)
        if task.pm_id in disabled:
            continue
        active_moments += len(years)
        active_years.update(years)
        active_intervals.append(interval)

    return RevDiagnostics(
        active_moments=active_moments,
        structural_moments=structural_moments,
        active_years=tuple(sorted(active_years)),
        structural_years=tuple(sorted(structural_years)),
        active_intervals_years=tuple(sorted(set(active_intervals))),
    )


def compute_fm_input_diagnostics(project: RCMProject, fm_id: str) -> FmInputDiagnostics:
    fm = project.faalwijzes.get(fm_id)
    meta = ((project.import_settings or {}).get("isograph_causes") or {}).get(fm_id)
    meta_dict = meta if isinstance(meta, dict) else {}
    initial_age_aw = _hours_to_years(meta_dict.get("InitialAge"))
    mttf_aw = _hours_to_years(meta_dict.get("FmMttf"))

    pm_tasks = project.get_pm_tasks_for_fm(fm_id)
    counts: dict[str, int] = {}
    for task in pm_tasks:
        key = task.taak_type.value
        counts[key] = counts.get(key, 0) + 1
    pm_task_counts = tuple(sorted(counts.items()))

    if fm is None:
        return FmInputDiagnostics(
            current_age_years=0.0,
            mttf_years=0.0,
            initial_age_aw_years=initial_age_aw,
            mttf_aw_years=mttf_aw,
            pm_task_counts=pm_task_counts,
        )

    pbs = project.pbs_items.get(fm.pbs_id)
    if pbs is None:
        current_age = 0.0
    else:
        eff_bouwjaar = pbs.effective_bouwjaar(project.pbs_items)
        current_age = (
            float(project.config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
        )

    return FmInputDiagnostics(
        current_age_years=current_age,
        mttf_years=float(fm.mttf_jaar),
        initial_age_aw_years=initial_age_aw,
        mttf_aw_years=mttf_aw,
        pm_task_counts=pm_task_counts,
    )


def aw_expected_failures(
    meta: dict,
    *,
    lifecycle_years: float,
) -> float | None:
    """AW verwacht aantal falen: TotalW, anders OutageFrequency × 8760 × lifecycle."""
    total_w = meta.get("TotalW")
    if total_w not in (None, ""):
        return float(total_w)
    freq = meta.get("OutageFrequency")
    if freq in (None, "") or lifecycle_years <= 0:
        return None
    return float(freq) * HOURS_PER_YEAR * lifecycle_years


def _hours_to_years(raw: object) -> float | None:
    if raw in (None, ""):
        return None
    return float(raw) / HOURS_PER_YEAR


def format_year_list(years: tuple[float, ...], *, max_items: int = 8) -> str:
    if not years:
        return "—"
    shown = years[:max_items]
    text = ", ".join(f"{y:g}" for y in shown)
    if len(years) > max_items:
        text += f", … (+{len(years) - max_items})"
    return text
