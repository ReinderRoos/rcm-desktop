from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rcm_core.models import RCMProject
from rcm_desktop.adapter.run_policy import SCENARIO_RUN_POLICY
from rcm_desktop.adapter.run_service import RunResult, run as run_single


SCENARIO_CM = "CM"
SCENARIO_PM = "PM"


@dataclass(frozen=True)
class ScenarioRunPairResult:
    status: str
    summary: str
    cm_result: RunResult | None
    pm_result: RunResult | None
    cm_project: RCMProject | None = None
    pm_project: RCMProject | None = None


@dataclass(frozen=True)
class ScenarioSingleRunResult:
    """Resultaat van één scenario-run (CM of PM)."""

    scenario: str
    status: str
    summary: str
    run_result: RunResult | None
    scenario_project: RCMProject | None


def _run_scenario(
    project: RCMProject | None,
    project_path: str | Path,
    *,
    scenario: str,
) -> ScenarioSingleRunResult:
    """Gedeelde materialisatie + run helper voor zowel `run_cm` als `run_compare`.

    Maakt scenario-specifieke project-clone via `build_project_for_scenario`
    en draait `run_incremental_analysis` via `run_service.run`.
    """
    if project is None:
        empty = run_single(None, project_path, full_recompute=True, parallel=False)
        return ScenarioSingleRunResult(
            scenario=scenario,
            status="error",
            summary=f"{scenario}-scenario niet gestart: project ontbreekt.",
            run_result=empty,
            scenario_project=None,
        )

    scenario_project = build_project_for_scenario(project, scenario)
    opts = SCENARIO_RUN_POLICY.scenario_options()
    rr = run_single(
        scenario_project,
        project_path,
        full_recompute=opts.full_recompute,
        parallel=opts.parallel,
        scenario_key=scenario,
    )
    if rr.status != "done":
        return ScenarioSingleRunResult(
            scenario=scenario,
            status="error",
            summary=f"{scenario}-scenario mislukt.",
            run_result=rr,
            scenario_project=scenario_project,
        )
    return ScenarioSingleRunResult(
        scenario=scenario,
        status="done",
        summary=f"{scenario}-scenario voltooid.",
        run_result=rr,
        scenario_project=scenario_project,
    )


def run_cm(project: RCMProject | None, project_path: str | Path) -> ScenarioSingleRunResult:
    """Run uitsluitend het CM-scenario.

    Hergebruikt dezelfde scenario-materialisatie en motor-aanroep als
    `run_compare`'s CM-tak, zodat aggregaten exact overeenkomen.
    """
    return _run_scenario(project, project_path, scenario=SCENARIO_CM)


def run_pm(project: RCMProject | None, project_path: str | Path) -> ScenarioSingleRunResult:
    """Run uitsluitend het PM-scenario (voorbereid voor slice 07)."""
    return _run_scenario(project, project_path, scenario=SCENARIO_PM)


def run_compare(project: RCMProject | None, project_path: str | Path) -> ScenarioRunPairResult:
    if project is None:
        empty = run_single(None, project_path, full_recompute=True, parallel=False)
        return ScenarioRunPairResult(
            status="error",
            summary="Vergelijkrun niet gestart: project ontbreekt.",
            cm_result=empty,
            pm_result=None,
            cm_project=None,
            pm_project=None,
        )

    cm = _run_scenario(project, project_path, scenario=SCENARIO_CM)
    if cm.status != "done":
        return ScenarioRunPairResult(
            status="error",
            summary="CM-scenario mislukt; vergelijking niet beschikbaar.",
            cm_result=cm.run_result,
            pm_result=None,
            cm_project=cm.scenario_project,
            pm_project=None,
        )

    pm = _run_scenario(project, project_path, scenario=SCENARIO_PM)
    if pm.status != "done":
        return ScenarioRunPairResult(
            status="error",
            summary="PM-scenario mislukt; vergelijking niet beschikbaar.",
            cm_result=cm.run_result,
            pm_result=pm.run_result,
            cm_project=cm.scenario_project,
            pm_project=pm.scenario_project,
        )

    return ScenarioRunPairResult(
        status="done",
        summary="CM/PM-vergelijking voltooid.",
        cm_result=cm.run_result,
        pm_result=pm.run_result,
        cm_project=cm.scenario_project,
        pm_project=pm.scenario_project,
    )


def build_project_for_scenario(project: RCMProject, scenario: str) -> RCMProject:
    from rcm_core.scenarios import pm_tasks_for_scenario

    clone = RCMProject.from_dict(project.to_dict())
    allowed_ids = pm_tasks_for_scenario(clone, scenario)
    clone.pm_tasks = {pm_id: t for pm_id, t in clone.pm_tasks.items() if pm_id in allowed_ids}
    clone.pm_effect_links = {
        link_id: link
        for link_id, link in clone.pm_effect_links.items()
        if link.pm_id in allowed_ids
    }
    return clone

