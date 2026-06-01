"""Niet-blokkerende modelwaarschuwingen voor de faalwijze-editor (slice 49)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from rcm_core.editing.validation import normalize_key
from rcm_core.models import FailureType, RCMProject, TaskType

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.fk_normalization import is_empty_fk_key
from rcm_desktop.adapter.fm_edit_bundle_service import _edit_current

TabHint = Literal["basis", "preventief"]


@dataclass(frozen=True)
class FmEditFinding:
    code: str
    message_nl: str
    tab_hint: TabHint | None = None
    related_pm_id: str | None = None
    peer_count: int | None = None


def normalize_pm_omschrijving(text: str) -> str:
    s = str(text or "").strip().lower()
    return re.sub(r"\s+", " ", s)


def intervals_within_ten_percent(a: float, b: float) -> bool:
    a_f, b_f = float(a), float(b)
    if a_f <= 0 or b_f <= 0:
        return a_f == b_f
    return abs(a_f - b_f) <= 0.1 * max(a_f, b_f)


def pm_measure_key(row: dict[str, Any]) -> tuple[str, str, float] | None:
    taak_type = _task_type_value(row.get("taak_type"))
    if not taak_type:
        return None
    oms = normalize_pm_omschrijving(str(row.get("taak_omschrijving") or ""))
    if not oms:
        return None
    try:
        interval = float(row.get("interval_jaar") or 0)
    except (TypeError, ValueError):
        return None
    if interval <= 0:
        return None
    return taak_type, oms, interval


def count_cross_component_peers(
    pm_row: dict[str, Any],
    *,
    fm_id: str,
    pbs_id: str,
    pm_rows: list[dict[str, Any]],
    fm_pbs_by_id: dict[str, str],
) -> int:
    """Aantal PM-rijen op andere PBS met dezelfde maatregel-sleutel."""
    key = pm_measure_key(pm_row)
    if key is None:
        return 0
    taak_type, oms, interval = key
    if taak_type == TaskType.REV.value or taak_type == "REV":
        return 0
    if not is_empty_fk_key(pm_row.get("task_group_id")):
        return 0
    target_pbs = normalize_key(pbs_id)
    count = 0
    for other in pm_rows:
        other_fm = normalize_key(other.get("fm_id"))
        if not other_fm or other_fm == normalize_key(fm_id):
            continue
        other_pbs = normalize_key(fm_pbs_by_id.get(other_fm, ""))
        if not other_pbs or other_pbs == target_pbs:
            continue
        other_key = pm_measure_key(other)
        if other_key is None:
            continue
        ot, oo, oi = other_key
        if ot != taak_type or oo != oms:
            continue
        if intervals_within_ten_percent(interval, oi):
            count += 1
    return count


def _task_type_value(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, TaskType):
        return raw.value
    if isinstance(raw, dict) and "value" in raw:
        return str(raw["value"])
    return str(raw).strip()


def _failure_type_value(raw: Any) -> str:
    if raw is None:
        return FailureType.RANDOM.value
    if isinstance(raw, FailureType):
        return raw.value
    return str(raw).strip().lower()


def _fm_row_and_pbs(
    session: EditingSession | dict[str, Any],
    fm_id: str,
) -> tuple[dict[str, Any] | None, str]:
    current = _edit_current(session)
    target = normalize_key(fm_id)
    fm_row = next(
        (r for r in current.get("faalwijzes", []) if normalize_key(r.get("fm_id")) == target),
        None,
    )
    if fm_row is None:
        return None, ""
    return fm_row, normalize_key(fm_row.get("pbs_id"))


def _fm_pbs_map(current: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    return {
        normalize_key(r.get("fm_id")): normalize_key(r.get("pbs_id"))
        for r in current.get("faalwijzes", [])
        if normalize_key(r.get("fm_id"))
    }


def findings_for_edit_rows(
    fm_id: str,
    faalwijze_rows: list[dict[str, Any]],
    pm_task_rows: list[dict[str, Any]],
    *,
    messages_module: Any | None = None,
) -> list[FmEditFinding]:
    """Findings op basis van rij-lijsten (geen sessie-mutatie)."""
    from rcm_desktop import messages as default_messages

    msg = messages_module or default_messages
    target = normalize_key(fm_id)
    fm_row = next(
        (r for r in faalwijze_rows if normalize_key(r.get("fm_id")) == target),
        None,
    )
    if fm_row is None:
        return []
    pbs_id = normalize_key(fm_row.get("pbs_id"))
    pm_rows = list(pm_task_rows)
    fm_pbs = _fm_pbs_map({"faalwijzes": faalwijze_rows})
    failure_type = _failure_type_value(fm_row.get("failure_type"))

    out: list[FmEditFinding] = []

    pm_for_fm = [r for r in pm_rows if normalize_key(r.get("fm_id")) == target]
    has_rev = any(
        _task_type_value(r.get("taak_type")) == TaskType.REV.value
        and float(r.get("interval_jaar") or 0) > 0
        for r in pm_for_fm
    )

    if failure_type == FailureType.AGING.value and not has_rev:
        out.append(
            FmEditFinding(
                code="AGING_WITHOUT_REV",
                message_nl=msg.FM_EDITOR_WARN_AGING_WITHOUT_REV,
                tab_hint="basis",
            )
        )
    if has_rev and failure_type != FailureType.AGING.value:
        out.append(
            FmEditFinding(
                code="REV_WITHOUT_AGING",
                message_nl=msg.FM_EDITOR_WARN_REV_WITHOUT_AGING,
                tab_hint="basis",
            )
        )

    for pm_row in pm_for_fm:
        peers = count_cross_component_peers(
            pm_row,
            fm_id=fm_id,
            pbs_id=pbs_id,
            pm_rows=pm_rows,
            fm_pbs_by_id=fm_pbs,
        )
        if peers > 0:
            pm_id = normalize_key(pm_row.get("pm_id")) or "?"
            out.append(
                FmEditFinding(
                    code="PM_BUNDLE_SUGGEST",
                    message_nl=msg.FM_EDITOR_WARN_PM_BUNDLE_SUGGEST.format(
                        pm_id=pm_id,
                        count=peers,
                    ),
                    tab_hint="preventief",
                    related_pm_id=pm_id,
                    peer_count=peers,
                )
            )

    return out


def findings_for_fm(
    session: EditingSession | dict[str, Any],
    fm_id: str,
    *,
    messages_module: Any | None = None,
) -> list[FmEditFinding]:
    """Niet-blokkerende findings voor één faalwijze uit edit_current."""
    current = _edit_current(session)
    return findings_for_edit_rows(
        fm_id,
        list(current.get("faalwijzes", [])),
        list(current.get("pm_tasks", [])),
        messages_module=messages_module,
    )


def findings_for_fm_from_project(project: RCMProject, fm_id: str) -> list[FmEditFinding]:
    """Findings op basis van een materialiseerd project (tests/fixtures)."""
    from rcm_desktop.adapter.fm_edit_commit_service import create_edit_session

    session = create_edit_session(project)
    return findings_for_fm(session, fm_id)
