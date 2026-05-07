from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import FMResult, RCMProject


@dataclass(frozen=True)
class FMResultRow:
    fm_id: str
    faalwijze_omschrijving: str
    pbs_id: str
    bouwdeel_naam: str
    expected_failures: float
    expected_total_downtime_hr: float
    total_cost_eur: float


def build_rows(project: RCMProject, fm_results: list[FMResult]) -> list[FMResultRow]:
    rows: list[FMResultRow] = []
    for fm_result in fm_results:
        fm = project.faalwijzes.get(fm_result.fm_id)
        pbs_item = project.pbs_items.get(fm_result.pbs_id)
        rows.append(
            FMResultRow(
                fm_id=fm_result.fm_id,
                faalwijze_omschrijving=fm.faalwijze_omschrijving if fm is not None else "",
                pbs_id=fm_result.pbs_id,
                bouwdeel_naam=pbs_item.bouwdeel_naam if pbs_item is not None else "",
                expected_failures=fm_result.expected_failures,
                expected_total_downtime_hr=fm_result.expected_total_downtime_hr,
                total_cost_eur=fm_result.total_cost_eur,
            )
        )
    return rows
