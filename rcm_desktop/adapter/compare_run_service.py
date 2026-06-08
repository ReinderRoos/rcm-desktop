"""Qt-free orchestration for one A/B slot motor run (slice 56)."""



from __future__ import annotations



from dataclasses import dataclass

from pathlib import Path



from rcm_core.models import RCMProject



from rcm_desktop.adapter import run_service

from rcm_desktop.adapter.compare_run_config import CompareRunConfig

from rcm_desktop.adapter.compare_slot_label import build_compare_slot_label

from rcm_desktop.adapter.compare_slot_state import (

    COMPARE_SLOT_A,

    CompareSlotSnapshot,

)

from rcm_desktop.adapter.planning_run_service import PlanningRunRequest, execute_planning_run

from rcm_desktop.adapter.presentation_cache_service import build_contribution_presentation

from rcm_desktop.adapter.run_service import RunResult



_SCENARIO_UI_KEYS = frozenset({"cm", "pm"})





@dataclass(frozen=True)

class CompareRunOutcome:

    status: str

    summary: str

    snapshot: CompareSlotSnapshot | None





class CompareRunService:

    @staticmethod

    def run_slot(

        project: RCMProject | None,

        project_path: str | Path,

        config: CompareRunConfig,

        *,

        slot_key: str = COMPARE_SLOT_A,

    ) -> CompareRunOutcome:

        if project is None:

            empty = run_service.run(None, project_path, full_recompute=True, parallel=False)

            return CompareRunOutcome(

                status="error",

                summary="Run niet gestart: project ontbreekt.",

                snapshot=None,

            )



        sk = config.scenario_key

        outcome = execute_planning_run(

            PlanningRunRequest(

                project=project,

                project_path=project_path,

                planning_overlay=config.planning_overlay,

                force_recompute=config.force_recompute,

                materialize_scenario=sk if sk in _SCENARIO_UI_KEYS else None,

                scenario_motor_key=sk.upper() if sk in _SCENARIO_UI_KEYS else None,

            )

        )

        if outcome.status != "done" or outcome.run_result is None:

            return CompareRunOutcome(

                status="error",

                summary=outcome.summary,

                snapshot=None,

            )



        rr = outcome.run_result

        run_project = outcome.project_used or project

        presentation = build_contribution_presentation(run_project, rr)

        label = build_compare_slot_label(

            slot_key,

            scenario_key=config.scenario_key,

            overlay=config.planning_overlay,

        )

        snapshot = CompareSlotSnapshot.from_motor_run(

            run_result=rr,

            presentation=presentation,

            scenario_key=config.scenario_key,

            overlay_at_run=config.planning_overlay,

            label=label,

        )

        return CompareRunOutcome(

            status="done",

            summary=rr.summary,

            snapshot=snapshot,

        )


