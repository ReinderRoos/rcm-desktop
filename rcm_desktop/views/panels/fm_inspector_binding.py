"""FM-inspector presentatie in FM-detail-modus (slice 74 + panel-extractie)."""

from __future__ import annotations

from typing import Any

from rcm_desktop import messages
from rcm_desktop.adapter.fm_verification_service import FMVerificationView
from rcm_desktop.adapter.fm_verification_year_table_model import FMVerificationYearTableModel
from rcm_desktop.adapter import workspace_session_service as wss
from rcm_desktop.formatting import format_eur, format_float, format_int


def refresh_fm_inspector(window: Any, fm_id: str | None) -> None:
    if not hasattr(window, "fm_inspector_panel"):
        return
    if fm_id is None:
        window.fm_inspector_empty_label.setVisible(True)
        window.fm_inspector_panel.setVisible(False)
        return
    session = window._project_session()
    fmr = window._fm_core_result_for_id(fm_id)
    if session is None or fmr is None:
        window.fm_inspector_empty_label.setVisible(True)
        window.fm_inspector_panel.setVisible(False)
        return
    view = wss.build_fm_verification_for_session(
        session, fmr, nb_filter=window.workspace_state.snapshot().effect_nb_filter
    )
    apply_fm_inspector_view(window, view)


def apply_fm_inspector_view(window: Any, view: FMVerificationView) -> None:
    window.fm_inspector_empty_label.setVisible(False)
    window.fm_inspector_panel.setVisible(True)
    window.fm_inspector_identity_label.setText(
        f"{view.fm_id} — {view.faalwijze_omschrijving}\n"
        f"{view.pbs_id} — {view.bouwdeel_naam}"
    )
    lc = view.lifecycle
    lines = [
        f"{messages.WORKSPACE_FM_INSPECTOR_FAALMOMENTEN}: "
        f"{format_int(int(round(lc.expected_failures)))}",
        f"{messages.WORKSPACE_FM_INSPECTOR_RAW_DOWNTIME}: "
        f"{format_float(lc.expected_raw_downtime_hr)}",
        f"{messages.WORKSPACE_FM_INSPECTOR_DETECTION_DELAY}: "
        f"{format_float(lc.expected_detection_delay_hr)}",
        f"{messages.WORKSPACE_FM_INSPECTOR_PM_DOWNTIME}: "
        f"{format_float(lc.expected_pm_downtime_hr)}",
        f"{messages.WORKSPACE_FM_INSPECTOR_TOTAL_DOWNTIME}: "
        f"{format_float(lc.expected_total_downtime_hr)}",
        f"{messages.WORKSPACE_FM_INSPECTOR_CM_COST}: "
        f"{format_eur(lc.expected_cm_cost_eur)}",
        f"{messages.WORKSPACE_FM_INSPECTOR_PM_COST}: "
        f"{format_eur(lc.pm_cost_eur)}",
        f"{messages.WORKSPACE_FM_INSPECTOR_TOTAL_COST}: "
        f"{format_eur(lc.total_cost_eur)}",
    ]
    if lc.effect_bijdragen:
        effects = ", ".join(f"{kid}: {format_float(v)}" for kid, v in lc.effect_bijdragen)
        lines.append(f"{messages.WORKSPACE_FM_INSPECTOR_EFFECTS}: {effects}")
    window.fm_inspector_lifecycle_label.setText("\n".join(lines))
    if view.fm_input_hash:
        window.fm_inspector_hash_label.setText(
            f"{messages.WORKSPACE_FM_INSPECTOR_HASH_PREFIX} {view.fm_input_hash}"
        )
    else:
        window.fm_inspector_hash_label.setText(messages.WORKSPACE_FM_INSPECTOR_HASH_MISSING)
    if view.profile_missing:
        window.fm_inspector_profile_missing_label.setText(
            messages.WORKSPACE_FM_INSPECTOR_PROFILE_MISSING
        )
        window.fm_inspector_profile_missing_label.setVisible(True)
        window.fm_inspector_year_table_view.setVisible(False)
        window.fm_inspector_year_table_view.setModel(None)
        reconcile_prefix = messages.WORKSPACE_FM_INSPECTOR_RECONCILE_WARN
    else:
        window.fm_inspector_profile_missing_label.setVisible(False)
        window.fm_inspector_year_table_view.setVisible(True)
        year_model = FMVerificationYearTableModel(view.year_rows)
        window.fm_inspector_year_table_view.setModel(year_model)
        reconcile_prefix = (
            messages.WORKSPACE_FM_INSPECTOR_RECONCILE_OK
            if view.reconcile_ok
            else messages.WORKSPACE_FM_INSPECTOR_RECONCILE_WARN
        )
    notes = "; ".join(view.reconcile_notes)
    window.fm_inspector_reconcile_label.setText(f"{reconcile_prefix} — {notes}")
