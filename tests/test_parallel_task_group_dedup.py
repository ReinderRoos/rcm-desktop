"""Slice 43 — parallel run ≡ sequentieel voor taakgroep-PM (K1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rcm_core.engine import run_analytical
from rcm_core.models import FMResult, RCMProject

HAARLEM = Path(__file__).resolve().parent / "fixtures" / "awzi_haarlem_waarderpolder_demo.rcm.json"

_K1_FIELDS = ("total_cost_eur", "pm_cost_eur", "expected_pm_downtime_hr")


def _assert_fm_k1_parity(
    seq: dict[str, FMResult],
    par: dict[str, FMResult],
) -> None:
    assert set(par) == set(seq)
    for fm_id, seq_r in seq.items():
        par_r = par[fm_id]
        for field in _K1_FIELDS:
            assert getattr(par_r, field) == pytest.approx(
                getattr(seq_r, field), rel=1e-6, abs=1e-4
            ), f"{fm_id}.{field}"


def _shared_task_group_project() -> RCMProject:
    """8 FM's: FM-1/FM-2 delen TG-SHARED; overige zonder PM (activeert parallel pool)."""
    lifecycle = 10.0
    group_cost = 10_000.0
    group_interval = 2.0
    pbs = {
        "pbs_id": "PBS-1",
        "object_naam": "O",
        "element_naam": "E",
        "bouwdeel_naam": "B",
        "component_naam": "",
        "multiplicity": 1,
        "bouwjaar": 2026,
    }
    fm_base = {
        "pbs_id": "PBS-1",
        "functie_id": "F1",
        "faalwijze_omschrijving": "Synth",
        "failure_type": "random",
        "mttf_jaar": 50.0,
        "cost_cm_eur": 100.0,
        "downtime_per_failure": {"value": 0.1, "unit": "uur"},
    }
    faalwijzes: dict = {}
    pm_tasks: dict = {}
    for i in range(1, 9):
        fid = f"FM-{i}"
        faalwijzes[fid] = {"fm_id": fid, **fm_base}
    for fid in ("FM-1", "FM-2"):
        pm_tasks[f"PM-{fid}"] = {
            "pm_id": f"PM-{fid}",
            "fm_id": fid,
            "taak_type": "IN",
            "interval_jaar": group_interval,
            "duration": {"value": 1.0, "unit": "uur"},
            "cost_eur": 0.0,
            "task_group_id": "TG-SHARED",
        }
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": lifecycle, "modeljaar": 2026},
            "pbs_items": {"PBS-1": pbs},
            "functies": {},
            "faalwijzes": faalwijzes,
            "pm_tasks": pm_tasks,
            "task_groups": {
                "TG-SHARED": {
                    "group_id": "TG-SHARED",
                    "omschrijving": "Gedeelde inspectieronde",
                    "taak_type": "IN",
                    "interval_jaar": group_interval,
                    "cost_eur": group_cost,
                    "duration": {"value": 1.0, "unit": "uur"},
                    "causes_unavailability": False,
                    "unavailability_fraction": 0.0,
                },
            },
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def test_parallel_matches_sequential_on_shared_task_group_mini() -> None:
    project = _shared_task_group_project()
    seq, _ = run_analytical(project, parallel=False)
    par, _ = run_analytical(project, parallel=True)
    _assert_fm_k1_parity(seq, par)


@pytest.fixture(scope="module")
def haarlem_project() -> RCMProject:
    return RCMProject.from_dict(json.loads(HAARLEM.read_text(encoding="utf-8")))


def test_parallel_matches_sequential_on_haarlem(haarlem_project: RCMProject) -> None:
    seq, _ = run_analytical(haarlem_project, parallel=False)
    par, _ = run_analytical(haarlem_project, parallel=True)
    _assert_fm_k1_parity(seq, par)
