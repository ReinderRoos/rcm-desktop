"""Slice 101 issue 08 — MC RF column aligns with analytical resolver."""

from __future__ import annotations

from rcm_core.config import RCMConfig
from rcm_core.models import Faalwijze, PBSItem, RCMProject
from rcm_core.simulation_engine import FMMCResult, MetricBand
from rcm_core.units import TimeDuration, TimeUnit

from rcm_desktop.adapter.result_view_service import FMResultRow, enrich_fm_rows_with_nmf_rf
from rcm_desktop.adapter.simulation_engine_service import build_mc_fm_rows


def test_build_mc_fm_rows_rf_matches_analytical_enrichment() -> None:
    project = RCMProject(
        config=RCMConfig(lifecycle_years=5.0, modeljaar=2020),
        pbs_items={"PBS-1": PBSItem("PBS-1", "o", "e", "Pomp")},
        faalwijzes={
            "FM-1": Faalwijze(
                fm_id="FM-1",
                pbs_id="PBS-1",
                functie_id="F",
                faalwijze_omschrijving="Test",
                mttf_jaar=10.0,
                downtime_per_failure=TimeDuration(10.0, TimeUnit.HOURS),
            ),
        },
    )
    mc_fm = FMMCResult(
        fm_id="FM-1",
        pbs_id="PBS-1",
        failures=MetricBand(p10=1.0, p50=2.0, p90=3.0),
        downtime_hr=MetricBand(p10=1.0, p50=2.0, p90=3.0),
        total_cost_eur=MetricBand(p10=10.0, p50=20.0, p90=30.0),
        n_completed=100,
        seed=1,
    )
    mc_row = build_mc_fm_rows(project, {"FM-1": mc_fm})[0]
    anal_row = enrich_fm_rows_with_nmf_rf(
        project,
        out=(
            FMResultRow(
                fm_id="FM-1",
                pbs_id="PBS-1",
                faalwijze_omschrijving="Test",
                bouwdeel_naam="Pomp",
                expected_failures=2.0,
                expected_total_downtime_hr=20.0,
                total_cost_eur=20.0,
                is_nmf=False,
                rf=0.0,
            ),
        ),
        nb_filter=None,
    )[0]
    assert mc_row.rf == anal_row.rf
