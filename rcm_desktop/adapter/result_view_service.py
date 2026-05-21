from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import FMResult, PBSResult, RCMProject


@dataclass(frozen=True)
class FMResultRow:
    fm_id: str
    faalwijze_omschrijving: str
    pbs_id: str
    bouwdeel_naam: str
    expected_failures: float
    expected_total_downtime_hr: float
    total_cost_eur: float


@dataclass(frozen=True)
class PBSResultRow:
    pbs_id: str
    bouwdeel_naam: str
    parent_pbs_id: str | None
    level: int
    sort_path: tuple[str, ...]
    expected_failures_self: float
    total_downtime_hr_self: float
    total_cost_eur_self: float
    expected_failures_total: float
    total_downtime_hr_total: float
    total_cost_eur_total: float
    unavailability_pct_total: float


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


def build_pbs_rows(project: RCMProject, pbs_results: dict[str, PBSResult]) -> list[PBSResultRow]:
    if not pbs_results:
        return []

    children: dict[str, list[str]] = {}
    for pbs_id, item in project.pbs_items.items():
        parent_id = item.parent_pbs_id if item.parent_pbs_id in project.pbs_items else None
        children.setdefault(parent_id or "", []).append(pbs_id)
    for ids in children.values():
        ids.sort()

    lifecycle_hours = float(project.config.lifecycle_years) * 8760.0
    def _self_values(pbs_id: str) -> tuple[float, float, float]:
        result = pbs_results.get(pbs_id)
        if result is None:
            return 0.0, 0.0, 0.0
        return result.total_expected_failures, result.total_downtime_hr, result.total_cost_eur

    def _totals(pbs_id: str, in_path: set[str]) -> tuple[float, float, float]:
        expected_failures_self, total_downtime_hr_self, total_cost_eur_self = _self_values(pbs_id)
        expected_failures_total = expected_failures_self
        total_downtime_hr_total = total_downtime_hr_self
        total_cost_eur_total = total_cost_eur_self
        next_path = set(in_path)
        next_path.add(pbs_id)
        for child_id in children.get(pbs_id, []):
            if child_id in next_path:
                continue
            child_failures, child_downtime, child_cost = _totals(child_id, next_path)
            expected_failures_total += child_failures
            total_downtime_hr_total += child_downtime
            total_cost_eur_total += child_cost
        return expected_failures_total, total_downtime_hr_total, total_cost_eur_total

    totals_by_id: dict[str, tuple[float, float, float]] = {
        pbs_id: _totals(pbs_id, set()) for pbs_id in project.pbs_items
    }

    emitted: set[str] = set()
    rows: list[PBSResultRow] = []

    def _walk(pbs_id: str, level: int, path: tuple[str, ...], in_path: set[str]) -> None:
        if pbs_id in emitted:
            return

        emitted.add(pbs_id)
        expected_failures_self, total_downtime_hr_self, total_cost_eur_self = _self_values(pbs_id)
        expected_failures_total, total_downtime_hr_total, total_cost_eur_total = totals_by_id[pbs_id]

        next_path = path + (pbs_id,)

        row = PBSResultRow(
            pbs_id=pbs_id,
            bouwdeel_naam=project.pbs_items[pbs_id].bouwdeel_naam,
            parent_pbs_id=project.pbs_items[pbs_id].parent_pbs_id,
            level=level,
            sort_path=next_path,
            expected_failures_self=expected_failures_self,
            total_downtime_hr_self=total_downtime_hr_self,
            total_cost_eur_self=total_cost_eur_self,
            expected_failures_total=expected_failures_total,
            total_downtime_hr_total=total_downtime_hr_total,
            total_cost_eur_total=total_cost_eur_total,
            unavailability_pct_total=(
                0.0 if lifecycle_hours <= 0.0 else (total_downtime_hr_total / lifecycle_hours) * 100.0
            ),
        )
        rows.append(row)

        next_in_path = set(in_path)
        next_in_path.add(pbs_id)
        for child_id in children.get(pbs_id, []):
            if child_id in next_in_path:
                continue
            _walk(child_id, level + 1, next_path, next_in_path)

    root_ids = children.get("", [])
    for root_id in root_ids:
        if root_id in emitted:
            continue
        _walk(root_id, 0, tuple(), set())

    for remaining_id in sorted(project.pbs_items):
        if remaining_id in emitted:
            continue
        _walk(remaining_id, 0, tuple(), set())

    return rows


@dataclass(frozen=True)
class PBSTreeNode:
    pbs_id: str
    row: PBSResultRow
    children: tuple["PBSTreeNode", ...] = ()


def build_pbs_tree(rows: list[PBSResultRow]) -> tuple[PBSTreeNode, ...]:
    """Bouw PBS-hiërarchie uit rijen; eerste rij per `pbs_id` wint."""
    if not rows:
        return ()

    by_id: dict[str, PBSResultRow] = {}
    for row in rows:
        by_id.setdefault(row.pbs_id, row)

    children_map: dict[str | None, list[str]] = {}
    for pbs_id, row in by_id.items():
        parent = row.parent_pbs_id
        if parent is None or parent not in by_id:
            parent_key: str | None = None
        else:
            parent_key = parent
        children_map.setdefault(parent_key, []).append(pbs_id)
    for child_ids in children_map.values():
        child_ids.sort()

    def make_node(pbs_id: str) -> PBSTreeNode:
        child_ids = children_map.get(pbs_id, [])
        return PBSTreeNode(
            pbs_id=pbs_id,
            row=by_id[pbs_id],
            children=tuple(make_node(cid) for cid in child_ids),
        )

    root_ids = children_map.get(None, [])
    root_ids.sort()
    return tuple(make_node(rid) for rid in root_ids)


def build_pbs_structure_tree(project: RCMProject) -> tuple[PBSTreeNode, ...]:
    """PBS-structuur vóór run: nul-aggregaten, bouwdeel uit `PBSItem`."""
    if not project.pbs_items:
        return ()

    children: dict[str | None, list[str]] = {}
    for pbs_id, item in project.pbs_items.items():
        parent = item.parent_pbs_id
        if parent is None or parent not in project.pbs_items:
            parent_key: str | None = None
        else:
            parent_key = parent
        children.setdefault(parent_key, []).append(pbs_id)
    for child_ids in children.values():
        child_ids.sort()

    emitted: set[str] = set()
    rows: list[PBSResultRow] = []

    def _walk(pbs_id: str, level: int, path: tuple[str, ...], in_path: set[str]) -> None:
        if pbs_id in emitted:
            return
        emitted.add(pbs_id)
        item = project.pbs_items[pbs_id]
        parent_id = item.parent_pbs_id
        if parent_id not in project.pbs_items:
            parent_id = None
        next_path = path + (pbs_id,)
        rows.append(
            PBSResultRow(
                pbs_id=pbs_id,
                bouwdeel_naam=item.bouwdeel_naam,
                parent_pbs_id=parent_id,
                level=level,
                sort_path=next_path,
                expected_failures_self=0.0,
                total_downtime_hr_self=0.0,
                total_cost_eur_self=0.0,
                expected_failures_total=0.0,
                total_downtime_hr_total=0.0,
                total_cost_eur_total=0.0,
                unavailability_pct_total=0.0,
            )
        )
        next_in_path = set(in_path)
        next_in_path.add(pbs_id)
        for child_id in children.get(pbs_id, ()):
            if child_id in next_in_path:
                continue
            _walk(child_id, level + 1, next_path, next_in_path)

    for root_id in children.get(None, ()):
        if root_id not in emitted:
            _walk(root_id, 0, tuple(), set())
    for remaining_id in sorted(project.pbs_items):
        if remaining_id not in emitted:
            _walk(remaining_id, 0, tuple(), set())

    return build_pbs_tree(rows)
