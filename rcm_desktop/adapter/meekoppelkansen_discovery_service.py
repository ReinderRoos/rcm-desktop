"""Meekoppelkansen discovery — RCM1-parity (slice 39, ADR-0005)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject, TaskType


@dataclass(frozen=True)
class MeekoppelSuggestion:
    element_naam: str
    pm_a: str
    pm_b: str
    pbs_a: str
    pbs_b: str
    jaar_a: int
    jaar_b: int
    jaar_delta: int
    reden: str


def discover_meekoppelkansen(
    project: RCMProject,
    *,
    window_years: int = 2,
) -> tuple[MeekoppelSuggestion, ...]:
    """REV-paren op hetzelfde element met due-jaren binnen ``window_years``."""
    if window_years < 0:
        return ()

    rev_rows: list[tuple[str, str, str, int]] = []
    for task in project.pm_tasks.values():
        if task.taak_type != TaskType.REV:
            continue
        if task.interval_jaar <= 0:
            continue
        fm = project.faalwijzes.get(task.fm_id)
        if fm is None:
            continue
        pbs = project.pbs_items.get(fm.pbs_id)
        if pbs is None or not (pbs.element_naam or "").strip():
            continue
        due = int(round(task.interval_jaar))
        rev_rows.append((task.pm_id, fm.pbs_id, pbs.element_naam.strip(), due))

    by_element: dict[str, list[tuple[str, str, int]]] = {}
    for pm_id, pbs_id, element, due in rev_rows:
        by_element.setdefault(element, []).append((pm_id, pbs_id, due))

    out: list[MeekoppelSuggestion] = []
    for element, items in sorted(by_element.items()):
        for i in range(len(items)):
            pm_i, pbs_i, jaar_i = items[i]
            for j in range(i + 1, len(items)):
                pm_j, pbs_j, jaar_j = items[j]
                pm_a, pbs_a, jaar_a = (pm_i, pbs_i, jaar_i)
                pm_b, pbs_b, jaar_b = (pm_j, pbs_j, jaar_j)
                if pm_b < pm_a:
                    pm_a, pbs_a, jaar_a, pm_b, pbs_b, jaar_b = (
                        pm_b,
                        pbs_b,
                        jaar_b,
                        pm_a,
                        pbs_a,
                        jaar_a,
                    )
                delta = abs(jaar_a - jaar_b)
                if delta > window_years:
                    continue
                out.append(
                    MeekoppelSuggestion(
                        element_naam=element,
                        pm_a=pm_a,
                        pm_b=pm_b,
                        pbs_a=pbs_a,
                        pbs_b=pbs_b,
                        jaar_a=jaar_a,
                        jaar_b=jaar_b,
                        jaar_delta=delta,
                        reden=(
                            f"REV op '{element}', due-jaren {jaar_a} en {jaar_b} "
                            f"(Δ={delta} jaar, venster {window_years})"
                        ),
                    )
                )
    return tuple(out)
