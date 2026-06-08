"""Parity-baseline voor projecttotaal kosten en niet-beschikbaarheid (Haarlem + import).

Regresseert tegen onbedoelde inflatie door synthetische NMF-TST-taken of verkeerde
Quantity-semantiek. Zie ook ``tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json.bak``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rcm_core.distributions import expected_failures_lifecycle
from rcm_core.engine import compute_detection_delay_hr, compute_pm_totals, run_analytical
from rcm_core.models import RCMProject

from rcm_desktop.adapter.isograph_import_service import build_from_sheets
from rcm_desktop.adapter.run_service import run as run_single
from tests.helpers.lcc_cm_shape import characterize_cm_year_shape

HAARLEM = Path(__file__).resolve().parent / "fixtures" / "awzi_haarlem_waarderpolder_demo.rcm.json"
HOURS_PER_YEAR = 8760.0


def _load(path: Path) -> RCMProject:
    return RCMProject.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _project_metrics(project: RCMProject) -> dict[str, float]:
    fm_results, _ = run_analytical(project, parallel=False)
    total_cost = sum(r.total_cost_eur for r in fm_results.values())
    total_dt = sum(
        r.expected_total_downtime_hr + r.expected_pm_downtime_hr for r in fm_results.values()
    )
    ly = float(project.config.lifecycle_years)
    return {
        "total_cost_eur": total_cost,
        "total_downtime_hr": total_dt,
        "unavailability_pct": (total_dt / (ly * HOURS_PER_YEAR)) * 100.0 if ly > 0 else 0.0,
    }


@pytest.fixture(scope="module")
def haarlem_project() -> RCMProject:
    return _load(HAARLEM)


def test_haarlem_fixture_has_no_synthetic_nmf_tst_tasks(haarlem_project: RCMProject) -> None:
    synthetic = [
        pm_id
        for pm_id, task in haarlem_project.pm_tasks.items()
        if task.taak_type.value == "TST" and "NMF-test" in task.taak_omschrijving
    ]
    assert synthetic == [], f"Verwijder slice-27 synthetische TST-taken: {synthetic[:5]}"


def test_haarlem_run_metrics_match_post_aging_ssot_baseline(
    haarlem_project: RCMProject,
) -> None:
    """Post slice-22/24 baseline: aging-SSOT met REV in lifecycle-totalen.

    Sequentieel (taakgroep-deduplicatie). Oude waarde 47,8M was pre-REV aging;
    zie ``test_haarlem_aging_without_rev_matches_pre_ssot_total``.
    """
    m = _project_metrics(haarlem_project)
    # Post slice-42: alle random-FM's → aging (121 aging, 0 random).
    assert m["total_cost_eur"] == pytest.approx(23_283_737.99, rel=1e-4)
    assert m["total_downtime_hr"] == pytest.approx(152_275.02, rel=1e-3)
    assert m["unavailability_pct"] == pytest.approx(28.97, rel=1e-2)


def test_haarlem_aging_without_rev_matches_pre_ssot_total(
    haarlem_project: RCMProject,
) -> None:
    """Documenteert dat pre-SSOT totaal = aging zonder REV-effect op faalmomenten."""
    total_cm_no_rev = 0.0
    for fm in haarlem_project.faalwijzes.values():
        pbs = haarlem_project.pbs_items[fm.pbs_id]
        eff_bouwjaar = pbs.effective_bouwjaar(haarlem_project.pbs_items)
        current_age = (
            float(haarlem_project.config.modeljaar - eff_bouwjaar) if eff_bouwjaar > 0 else 0.0
        )
        mult = pbs.effective_multiplicity(haarlem_project.pbs_items)
        ef = (
            expected_failures_lifecycle(
                current_age,
                haarlem_project.config.lifecycle_years,
                fm.failure_type.value,
                fm.mttf_jaar,
                fm.effective_sigma(haarlem_project.config.default_sigma_fraction),
                fm.repair_quality,
                aging_distribution=fm.aging_distribution.value,
                beta_jaar=fm.beta_jaar,
                rev_schedule=(),
            )
            * mult
        )
        total_cm_no_rev += fm.cost_cm_eur * ef

    counted_groups: set[str] = set()
    total_pm = 0.0
    for fm in haarlem_project.faalwijzes.values():
        pm = haarlem_project.get_pm_tasks_for_fm(fm.fm_id)
        pm_cost, _, _ = compute_pm_totals(
            pm,
            haarlem_project.task_groups,
            haarlem_project.config.lifecycle_years,
            counted_groups,
        )
        total_pm += pm_cost

    # Na slice-42 fixture-flip (volledig aging-portfolio); niet vergelijkbaar met pre-flip 47,8M.
    assert total_cm_no_rev + total_pm == pytest.approx(40_984_978.26, rel=1e-4)


def test_haarlem_lcc_cm_characterization_h3(haarlem_project: RCMProject) -> None:
    """Slice 42 D2 — portfolio CM-jaarprofiel niet-vlak, aging-dominant, DS-4b (chart-scale)."""
    fm_results, _ = run_analytical(haarlem_project, parallel=False)
    shape = characterize_cm_year_shape(haarlem_project, fm_results)
    assert shape.reconciles
    assert shape.used_legacy is False
    assert shape.aging_cm_share >= 0.90
    assert shape.cv > 0.10
    assert shape.max_mean_ratio > 1.3


def test_haarlem_kpi_run_service_matches_engine(haarlem_project: RCMProject) -> None:
    run_result = run_single(haarlem_project, HAARLEM, parallel=False)
    assert run_result.status == "done"
    m = _project_metrics(haarlem_project)
    assert run_result.metrics.total_cost_eur == pytest.approx(m["total_cost_eur"], rel=1e-6)
    assert run_result.metrics.total_downtime_hr == pytest.approx(m["total_downtime_hr"], rel=1e-6)


def test_nmf_tst_inflates_detection_delay_per_failure() -> None:
    """Documenteert waarom synthetische TST op niet-evidente FM's KPI's explodeert."""
    project = RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 10.0, "modeljaar": 2026},
            "pbs_items": {
                "PBS-1": {
                    "pbs_id": "PBS-1",
                    "object_naam": "O",
                    "element_naam": "E",
                    "bouwdeel_naam": "B",
                    "multiplicity": 1,
                    "bouwjaar": 2026,
                }
            },
            "functies": {
                "F-1": {
                    "functie_id": "F-1",
                    "pbs_id": "PBS-1",
                    "functie_omschrijving": "f",
                    "is_evident": True,
                }
            },
            "faalwijzes": {
                "FM-1": {
                    "fm_id": "FM-1",
                    "pbs_id": "PBS-1",
                    "functie_id": "F-1",
                    "faalwijze_omschrijving": "hidden",
                    "failure_type": "random",
                    "mttf_jaar": 5.0,
                    "is_evident": False,
                    "cost_cm_eur": 1000.0,
                    "downtime_per_failure": {"value": 2.0, "unit": "uur"},
                }
            },
            "pm_tasks": {
                "PM-TST": {
                    "pm_id": "PM-TST",
                    "fm_id": "FM-1",
                    "taak_type": "TST",
                    "interval_jaar": 2.0,
                    "duration": {"value": 1.0, "unit": "uur"},
                    "cost_eur": 50.0,
                }
            },
        }
    )
    fm = project.faalwijzes["FM-1"]
    pm = project.get_pm_tasks_for_fm("FM-1")
    delay = compute_detection_delay_hr(fm, pm)
    assert delay == pytest.approx(HOURS_PER_YEAR, rel=1e-9)


def test_isograph_quantity_cascades_to_effective_multiplicity() -> None:
    """Quantity per locatie × ouders = effective_multiplicity (Isograph BOM-semantiek)."""
    sheets = {
        "RcmLocations": [
            {"Id": "ROOT", "Parent": "", "Description": "Root", "Quantity": 2},
            {"Id": "LEAF", "Parent": "ROOT", "Description": "Leaf", "Quantity": 3},
        ],
        "RcmFunctions": [{"Id": "F1", "Parent": "LEAF", "Description": "Functie"}],
        "RcmFunctionalFailures": [{"Id": "FF1", "Parent": "F1", "Description": "FF"}],
        "RcmCauses": [
            {
                "Id": "FM-A",
                "Parent": "FF1",
                "Description": "FM",
                "LocationId": "LEAF",
                "FmMttf": 87600,
                "InitialAge": 0,
                "Mttr": 8,
            },
        ],
        "RcmEffects": [{"Id": "E1", "Description": "Effect"}],
        "RcmCauseEffectAssignments": [],
        "RcmCorrectiveTasks": [{"Cause": "FM-A", "TaskDuration": 8, "OperationalCost": 100}],
        "RcmScheduledTasks": [],
        "TaskGroups": [],
        "Project": [{"LifeTime": 876000, "RcmNoSimulations": 100}],
    }
    result = build_from_sheets(sheets, modeljaar=2026)
    pbs = result.project.pbs_items
    assert pbs["ROOT"].multiplicity == 2
    assert pbs["LEAF"].multiplicity == 3
    assert pbs["LEAF"].effective_multiplicity(pbs) == 6
