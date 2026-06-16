"""Faalwijze-analyse aligned compare rows for FM scenariovergelijking (slice 102-B1)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.compare_slot_state import COMPARE_SLOT_A, COMPARE_SLOT_B
from rcm_desktop.adapter.compare_view_service import ComparePanel
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.results_workspace_state import METRIC_FAALMOMENTEN, METRIC_KOSTEN
from rcm_desktop.adapter.simulation_engine_service import FMMCResultRow
from rcm_desktop.adapter.workspace_view_service import FMDetailView

HIGHLIGHT_RELATIVE_THRESHOLD = 0.20

FM_COMPARE_VIEW_TABLE = "table"
FM_COMPARE_VIEW_DIAGRAM = "diagram"


@dataclass(frozen=True)
class FaalwijzeCompareSlotCell:
    metric_value: float | None
    is_nmf: bool = False
    rf: float = 0.0


@dataclass(frozen=True)
class FaalwijzeCompareRow:
    fm_id: str
    label: str
    bouwdeel_naam: str
    s1: float | None
    s2: float | None
    highlight: bool
    s1_cell: FaalwijzeCompareSlotCell
    s2_cell: FaalwijzeCompareSlotCell


@dataclass(frozen=True)
class FaalwijzeComparePresentation:
    rows: tuple[FaalwijzeCompareRow, ...]
    metric: str


@dataclass(frozen=True)
class _SlotFmEntry:
    fm_id: str
    label: str
    bouwdeel_naam: str
    metric_value: float
    is_nmf: bool
    rf: float


def compute_fm_compare_highlight(s1: float, s2: float) -> bool:
    if s1 <= 0:
        return False
    return abs(s1 - s2) / s1 > HIGHLIGHT_RELATIVE_THRESHOLD


def metric_value_from_analytical(row: FMResultRow, metric: str) -> float:
    if metric == METRIC_FAALMOMENTEN:
        return row.expected_failures
    if metric == METRIC_KOSTEN:
        return row.total_cost_eur
    return row.expected_total_downtime_hr


def metric_value_from_mc(row: FMMCResultRow, metric: str) -> float:
    if metric == METRIC_FAALMOMENTEN:
        return row.failures_band.p50
    if metric == METRIC_KOSTEN:
        return row.cost_band.p50
    return row.downtime_band.p50


def _entries_from_fm_view(fm: FMDetailView, *, metric: str) -> dict[str, _SlotFmEntry]:
    out: dict[str, _SlotFmEntry] = {}
    if fm.is_mc_mode:
        for row in fm.mc_rows:
            out[row.fm_id] = _SlotFmEntry(
                fm_id=row.fm_id,
                label=row.faalwijze_omschrijving,
                bouwdeel_naam=row.bouwdeel_naam,
                metric_value=metric_value_from_mc(row, metric),
                is_nmf=row.is_nmf,
                rf=row.rf,
            )
        return out
    for row in fm.fm_rows:
        out[row.fm_id] = _SlotFmEntry(
            fm_id=row.fm_id,
            label=row.faalwijze_omschrijving,
            bouwdeel_naam=row.bouwdeel_naam,
            metric_value=metric_value_from_analytical(row, metric),
            is_nmf=row.is_nmf,
            rf=row.rf,
        )
    return out


def _panel_by_slot(panels: tuple[ComparePanel, ...]) -> dict[str, ComparePanel]:
    return {panel.slot_key: panel for panel in panels}


def _sort_key_s1(row: FaalwijzeCompareRow) -> tuple[int, float, str]:
    if row.s1 is None:
        return (1, 0.0, row.fm_id)
    return (0, -row.s1, row.fm_id)


def build_faalwijze_compare_presentation(
    panels: tuple[ComparePanel, ...],
    *,
    metric: str,
) -> FaalwijzeComparePresentation:
    by_slot = _panel_by_slot(panels)
    panel_a = by_slot.get(COMPARE_SLOT_A)
    panel_b = by_slot.get(COMPARE_SLOT_B)
    entries_a: dict[str, _SlotFmEntry] = {}
    entries_b: dict[str, _SlotFmEntry] = {}
    if panel_a is not None and panel_a.filled and panel_a.fm is not None:
        entries_a = _entries_from_fm_view(panel_a.fm, metric=metric)
    if panel_b is not None and panel_b.filled and panel_b.fm is not None:
        entries_b = _entries_from_fm_view(panel_b.fm, metric=metric)

    fm_ids = sorted(set(entries_a) | set(entries_b))
    rows: list[FaalwijzeCompareRow] = []
    for fm_id in fm_ids:
        entry_a = entries_a.get(fm_id)
        entry_b = entries_b.get(fm_id)
        label = ""
        bouwdeel = ""
        if entry_a is not None:
            label = entry_a.label
            bouwdeel = entry_a.bouwdeel_naam
        elif entry_b is not None:
            label = entry_b.label
            bouwdeel = entry_b.bouwdeel_naam
        s1 = entry_a.metric_value if entry_a is not None else None
        s2 = entry_b.metric_value if entry_b is not None else None
        highlight = False
        if s1 is not None and s2 is not None:
            highlight = compute_fm_compare_highlight(s1, s2)
        s1_cell = FaalwijzeCompareSlotCell(
            metric_value=s1,
            is_nmf=entry_a.is_nmf if entry_a is not None else False,
            rf=entry_a.rf if entry_a is not None else 0.0,
        )
        s2_cell = FaalwijzeCompareSlotCell(
            metric_value=s2,
            is_nmf=entry_b.is_nmf if entry_b is not None else False,
            rf=entry_b.rf if entry_b is not None else 0.0,
        )
        rows.append(
            FaalwijzeCompareRow(
                fm_id=fm_id,
                label=label,
                bouwdeel_naam=bouwdeel,
                s1=s1,
                s2=s2,
                highlight=highlight,
                s1_cell=s1_cell,
                s2_cell=s2_cell,
            )
        )
    rows.sort(key=_sort_key_s1)
    return FaalwijzeComparePresentation(rows=tuple(rows), metric=metric)
