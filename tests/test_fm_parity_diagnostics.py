"""Tests — FM parity diagnostics (slice 65+)."""

from __future__ import annotations

import pytest

from rcm_core.config import RCMConfig
from rcm_core.fm_parity_diagnostics import (
    aw_expected_failures,
    compute_rev_diagnostics,
    rev_calendar_years,
)
from rcm_core.models import (
    FailureType,
    Faalwijze,
    PBSItem,
    PMTask,
    RCMProject,
    TaskType,
)
from rcm_core.units import TimeDuration, TimeUnit


def _project_with_rev(*, disabled: bool = False) -> RCMProject:
    fm_id = "FM-1"
    pm_id = f"{fm_id}|REV|0"
    project = RCMProject(
        config=RCMConfig(
            lifecycle_years=50.0,
            modeljaar=2026,
        ),
        pbs_items={
            "P1": PBSItem(
                pbs_id="P1",
                object_naam="O",
                element_naam="E",
                bouwdeel_naam="P",
                bouwjaar=2000,
            )
        },
        faalwijzes={
            fm_id: Faalwijze(
                fm_id=fm_id,
                pbs_id="P1",
                functie_id="F1",
                faalwijze_omschrijving="Test FM",
                failure_type=FailureType.AGING,
                mttf_jaar=25.0,
            )
        },
        pm_tasks={
            pm_id: PMTask(
                pm_id=pm_id,
                fm_id=fm_id,
                taak_type=TaskType.REV,
                interval_jaar=16.0,
                duration=TimeDuration(8.0, TimeUnit.HOURS),
                cost_eur=2500.0,
            )
        },
        import_settings={
            "isograph_causes": {
                fm_id: {
                    "TotalW": 8.583,
                    "InitialAge": 8760,
                    "FmMttf": 219000,
                }
            },
            "aw_disabled_pm_ids": [pm_id] if disabled else [],
        },
    )
    return project


def test_rev_calendar_years_counts_moments_in_lifecycle() -> None:
    assert rev_calendar_years(16.0, 50.0) == (16.0, 32.0, 48.0)
    assert rev_calendar_years(25.0, 50.0) == (25.0, 50.0)


def test_compute_rev_diagnostics_active_vs_structural() -> None:
    active = compute_rev_diagnostics(_project_with_rev(disabled=False), "FM-1")
    assert active.active_moments == 3
    assert active.structural_moments == 3
    assert active.active_years == (16.0, 32.0, 48.0)

    disabled = compute_rev_diagnostics(_project_with_rev(disabled=True), "FM-1")
    assert disabled.structural_moments == 3
    assert disabled.active_moments == 0
    assert disabled.active_years == ()


def test_aw_expected_failures_prefers_total_w() -> None:
    meta = {"TotalW": 8.583, "OutageFrequency": 0.001}
    assert aw_expected_failures(meta, lifecycle_years=50.0) == 8.583


def test_aw_expected_failures_from_outage_frequency() -> None:
    meta = {"OutageFrequency": 1.95958904109589e-05}
    value = aw_expected_failures(meta, lifecycle_years=50.0)
    assert value is not None
    assert value == pytest.approx(8.583)
