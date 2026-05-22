"""Unit tests — meekoppelkansen discovery (slice 39)."""

from __future__ import annotations

import pytest

from rcm_core.models import RCMProject, TaskType

from rcm_desktop.adapter.meekoppelkansen_discovery_service import discover_meekoppelkansen


def _project_two_rev_same_element() -> RCMProject:
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 40.0, "modeljaar": 2026},
            "pbs_items": {
                "PBS-A": {
                    "pbs_id": "PBS-A",
                    "object_naam": "X",
                    "element_naam": "Pomp",
                    "bouwdeel_naam": "",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                },
                "PBS-B": {
                    "pbs_id": "PBS-B",
                    "object_naam": "Y",
                    "element_naam": "Motor",
                    "bouwdeel_naam": "",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                },
            },
            "functies": {},
            "faalwijzes": {
                "FM-A": {
                    "fm_id": "FM-A",
                    "pbs_id": "PBS-A",
                    "functie_id": "F1",
                    "faalwijze_omschrijving": "A",
                    "failure_type": "random",
                    "mttf_jaar": 10.0,
                    "downtime_per_failure": {"value": 1.0, "unit": "uur"},
                },
                "FM-B": {
                    "fm_id": "FM-B",
                    "pbs_id": "PBS-B",
                    "functie_id": "F2",
                    "faalwijze_omschrijving": "B",
                    "failure_type": "random",
                    "mttf_jaar": 10.0,
                    "downtime_per_failure": {"value": 1.0, "unit": "uur"},
                },
            },
            "pm_tasks": {
                "PM-REV-10": {
                    "pm_id": "PM-REV-10",
                    "fm_id": "FM-A",
                    "taak_type": "REV",
                    "interval_jaar": 10.0,
                },
                "PM-REV-12": {
                    "pm_id": "PM-REV-12",
                    "fm_id": "FM-A",
                    "taak_type": "REV",
                    "interval_jaar": 12.0,
                },
                "PM-IN": {
                    "pm_id": "PM-IN",
                    "fm_id": "FM-A",
                    "taak_type": "IN",
                    "interval_jaar": 11.0,
                },
                "PM-OTHER-ELEM": {
                    "pm_id": "PM-OTHER-ELEM",
                    "fm_id": "FM-B",
                    "taak_type": "REV",
                    "interval_jaar": 11.0,
                },
            },
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def test_discovers_rev_pair_same_element_within_window():
    rows = discover_meekoppelkansen(_project_two_rev_same_element(), window_years=2)
    assert len(rows) == 1
    r = rows[0]
    assert r.element_naam == "Pomp"
    assert r.pm_a == "PM-REV-10"
    assert r.pm_b == "PM-REV-12"
    assert r.jaar_a == 10
    assert r.jaar_b == 12
    assert r.jaar_delta == 2


def test_non_rev_and_different_element_excluded():
    rows = discover_meekoppelkansen(_project_two_rev_same_element(), window_years=2)
    pm_ids = {r.pm_a for r in rows} | {r.pm_b for r in rows}
    assert "PM-IN" not in pm_ids
    assert "PM-OTHER-ELEM" not in pm_ids


def test_delta_greater_than_window_excluded():
    rows = discover_meekoppelkansen(_project_two_rev_same_element(), window_years=1)
    assert rows == ()


def test_interval_zero_excluded():
    from dataclasses import replace

    project = _project_two_rev_same_element()
    project.pm_tasks["PM-ZERO"] = replace(
        project.pm_tasks["PM-REV-10"],
        pm_id="PM-ZERO",
        interval_jaar=0.0,
    )
    rows = discover_meekoppelkansen(project, window_years=5)
    assert all("PM-ZERO" not in (r.pm_a, r.pm_b) for r in rows)


def test_window_three_includes_delta_two_pair():
    rows = discover_meekoppelkansen(_project_two_rev_same_element(), window_years=3)
    assert len(rows) == 1


def test_window_one_vs_three_changes_pair_count():
    from dataclasses import replace

    project = _project_two_rev_same_element()
    project.pm_tasks["PM-REV-11"] = replace(
        project.pm_tasks["PM-REV-12"],
        pm_id="PM-REV-11",
        interval_jaar=11.0,
    )
    assert len(discover_meekoppelkansen(project, window_years=1)) == 2
    assert len(discover_meekoppelkansen(project, window_years=3)) == 3
