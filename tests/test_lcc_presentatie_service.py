from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from rcm_core.models import RCMProject

from rcm_desktop.adapter.lcc_presentatie_service import materialize_lcc_curve
from rcm_desktop.adapter.lcc_type_filter import LCCTypeFilterSet
from rcm_desktop.adapter.planning_overlay_state import PlanningOverlayState
from rcm_desktop.adapter.results_workspace_state import WorkspaceStateSnapshot
from rcm_desktop.adapter.run_service import RunMetrics, RunResult
from rcm_desktop.adapter.workspace_render_index import SLOT_B, WorkspaceRenderIndex


def _minimal_project() -> RCMProject:
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 10},
            "faalwijzes": {},
            "pbs_items": {},
            "pm_tasks": {},
            "pm_effect_links": {},
            "task_groups": {},
            "functies": {},
        }
    )


def _done_run() -> RunResult:
    return RunResult(
        status="done",
        summary="ok",
        metrics=RunMetrics(
            fm_result_count=0,
            total_lifecycle_faalmomenten=0.0,
            total_cost_eur=0.0,
        ),
    )


def _snapshot() -> WorkspaceStateSnapshot:
    return WorkspaceStateSnapshot(
        modus="lcc",
        source="pbs",
        metric="kosten",
        top_n=10,
        scope_id=None,
        filter_text="",
    )


def test_materialize_lcc_curve_uses_render_index_slot_key():
    render_index = WorkspaceRenderIndex()
    overlay = PlanningOverlayState.inactive()
    filters = LCCTypeFilterSet.all_on()
    project = _minimal_project()
    run = _done_run()
    sentinel = object()
    snap = _snapshot()

    with patch(
        "rcm_desktop.adapter.lcc_presentatie_service.build_tijdsplot_curve",
        return_value=sentinel,
    ):
        first = materialize_lcc_curve(
            render_index,
            project=project,
            run=run,
            scope_id=None,
            cache_modus_key="lcc|test",
            overlay=overlay,
            type_filters=filters,
            snapshot=snap,
            slot=SLOT_B,
        )
        second = materialize_lcc_curve(
            render_index,
            project=project,
            run=run,
            scope_id=None,
            cache_modus_key="lcc|test",
            overlay=overlay,
            type_filters=filters,
            snapshot=snap,
            slot=SLOT_B,
        )

    assert first is sentinel
    assert second is sentinel


def test_workspace_presentation_cache_warm_lcc_delegates_with_slot():
    from rcm_desktop.adapter.workspace_presentation_cache import WorkspacePresentationCache

    render_index = WorkspaceRenderIndex()
    project = _minimal_project()
    run = _done_run()
    overlay = PlanningOverlayState.inactive()
    filters = LCCTypeFilterSet.all_on()
    snap = _snapshot()

    with patch(
        "rcm_desktop.adapter.workspace_presentation_cache.materialize_lcc_curve",
        return_value=MagicMock(),
    ) as mat_mock:
        WorkspacePresentationCache.warm_lcc(
            render_index,
            project=project,
            run=run,
            scope_id="pbs-1",
            cache_modus_key="modus",
            overlay=overlay,
            type_filters=filters,
            snapshot=snap,
            slot=SLOT_B,
        )

    mat_mock.assert_called_once()
    assert mat_mock.call_args.kwargs["slot"] == SLOT_B
