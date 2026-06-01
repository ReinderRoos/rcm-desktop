"""Unit tests — meekoppelkansen discovery (slice 39/40)."""

from __future__ import annotations

from dataclasses import replace

from rcm_core.models import RCMProject

from rcm_desktop.adapter.meekoppelkansen_discovery_service import discover_meekoppel_locations


def _project_two_rev_same_pbs() -> RCMProject:
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 40.0, "modeljaar": 2026},
            "pbs_items": {
                "PBS-A": {
                    "pbs_id": "PBS-A",
                    "object_naam": "X",
                    "element_naam": "Pomp",
                    "bouwdeel_naam": "Locatie A",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                },
                "PBS-B": {
                    "pbs_id": "PBS-B",
                    "object_naam": "Y",
                    "element_naam": "Motor",
                    "bouwdeel_naam": "Locatie B",
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
                "PM-OTHER": {
                    "pm_id": "PM-OTHER",
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


def _project_same_element_name_two_pbs() -> RCMProject:
    """Twee locaties met dezelfde element_naam — locatie-discovery moet scheiden."""
    return RCMProject.from_dict(
        {
            "config": {"lifecycle_years": 40.0, "modeljaar": 2026},
            "pbs_items": {
                "PBS-1": {
                    "pbs_id": "PBS-1",
                    "object_naam": "",
                    "element_naam": "Pomp",
                    "bouwdeel_naam": "Pomp 1",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                },
                "PBS-2": {
                    "pbs_id": "PBS-2",
                    "object_naam": "",
                    "element_naam": "Pomp",
                    "bouwdeel_naam": "Pomp 2",
                    "component_naam": "",
                    "multiplicity": 1,
                    "bouwjaar": 2000,
                },
            },
            "functies": {},
            "faalwijzes": {
                "FM-1": {
                    "fm_id": "FM-1",
                    "pbs_id": "PBS-1",
                    "functie_id": "F1",
                    "faalwijze_omschrijving": "A",
                    "failure_type": "random",
                    "mttf_jaar": 10.0,
                    "downtime_per_failure": {"value": 1.0, "unit": "uur"},
                },
                "FM-2": {
                    "fm_id": "FM-2",
                    "pbs_id": "PBS-2",
                    "functie_id": "F2",
                    "faalwijze_omschrijving": "B",
                    "failure_type": "random",
                    "mttf_jaar": 10.0,
                    "downtime_per_failure": {"value": 1.0, "unit": "uur"},
                },
            },
            "pm_tasks": {
                "PM-A1": {
                    "pm_id": "PM-A1",
                    "fm_id": "FM-1",
                    "taak_type": "REV",
                    "interval_jaar": 10.0,
                },
                "PM-A2": {
                    "pm_id": "PM-A2",
                    "fm_id": "FM-1",
                    "taak_type": "REV",
                    "interval_jaar": 12.0,
                },
                "PM-B1": {
                    "pm_id": "PM-B1",
                    "fm_id": "FM-2",
                    "taak_type": "REV",
                    "interval_jaar": 11.0,
                },
                "PM-B2": {
                    "pm_id": "PM-B2",
                    "fm_id": "FM-2",
                    "taak_type": "REV",
                    "interval_jaar": 12.0,
                },
            },
            "task_groups": {},
            "effect_klassen": {},
            "fm_effect_links": {},
            "pm_effect_links": {},
            "bibliotheek": {},
        }
    )


def test_location_group_discovers_rev_pair_on_same_pbs():
    rows = discover_meekoppel_locations(_project_two_rev_same_pbs(), window_years=2)
    assert len(rows) == 1
    g = rows[0]
    assert g.pbs_id == "PBS-A"
    assert g.path_label == "Locatie A"
    assert g.rev_count == 2
    assert g.span_jaar == 2
    pm_ids = {t.pm_id for t in g.tasks}
    assert pm_ids == {"PM-REV-10", "PM-REV-12"}


def test_same_element_name_two_pbs_yields_two_location_groups():
    rows = discover_meekoppel_locations(_project_same_element_name_two_pbs(), window_years=2)
    assert len(rows) == 2
    pbs_ids = {g.pbs_id for g in rows}
    assert pbs_ids == {"PBS-1", "PBS-2"}


def test_non_rev_and_different_pbs_excluded():
    rows = discover_meekoppel_locations(_project_two_rev_same_pbs(), window_years=2)
    pm_ids = {t.pm_id for g in rows for t in g.tasks}
    assert "PM-IN" not in pm_ids
    assert "PM-OTHER" not in pm_ids


def test_span_greater_than_window_excluded():
    rows = discover_meekoppel_locations(_project_two_rev_same_pbs(), window_years=1)
    assert rows == ()


def test_interval_zero_excluded():
    project = _project_two_rev_same_pbs()
    project.pm_tasks["PM-ZERO"] = replace(
        project.pm_tasks["PM-REV-10"],
        pm_id="PM-ZERO",
        interval_jaar=0.0,
    )
    rows = discover_meekoppel_locations(project, window_years=5)
    pm_ids = {t.pm_id for g in rows for t in g.tasks}
    assert "PM-ZERO" not in pm_ids


def test_window_three_includes_three_rev_group():
    project = _project_two_rev_same_pbs()
    project.pm_tasks["PM-REV-11"] = replace(
        project.pm_tasks["PM-REV-12"],
        pm_id="PM-REV-11",
        interval_jaar=11.0,
    )
    assert discover_meekoppel_locations(project, window_years=1) == ()
    groups = discover_meekoppel_locations(project, window_years=3)
    assert len(groups) == 1
    assert groups[0].rev_count == 3
    assert groups[0].min_due_jaar == 10
    assert groups[0].max_due_jaar == 12
