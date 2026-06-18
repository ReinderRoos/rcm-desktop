"""Hard-clear scenario slots on project lifecycle events (slice 100 issue 04)."""

from __future__ import annotations

from enum import Enum

from rcm_desktop.adapter.scenario_workflow_service import ScenarioWorkflowService


class ScenarioInvalidationReason(Enum):
    PATH_CHANGED = "path_changed"
    PROJECT_CLEARED = "project_cleared"
    PROJECT_RELOADED = "project_reloaded"
    IMPORT_SUCCESS = "import_success"


def clear_scenarios_on_invalidation(
    workflow: ScenarioWorkflowService,
    reason: ScenarioInvalidationReason,
) -> None:
    """All listed invalidation reasons wipe scenario 1/2 slots (slice 56 extended)."""
    _ = reason
    workflow.clear_all()
