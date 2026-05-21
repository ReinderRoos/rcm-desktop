"""Qt-vrije what-if planning overlay (slice 28)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from rcm_core.models import RCMProject, TaskType


@dataclass(frozen=True)
class PlanningOverlayState:
    """Presentatie-overlay: geen mutatie van project-JSON."""

    active: bool
    anchor_years: tuple[tuple[str, float], ...]
    disabled_pm_ids: frozenset[str]

    @classmethod
    def inactive(cls) -> PlanningOverlayState:
        return cls(active=False, anchor_years=(), disabled_pm_ids=frozenset())

    @classmethod
    def from_import_settings(
        cls,
        import_settings: Mapping[str, Any] | None,
    ) -> PlanningOverlayState:
        """Seed overlay from AW ScheduledTask.Enabled=False (slice 35 follow-up)."""
        if not import_settings:
            return cls.inactive()
        raw = import_settings.get("aw_disabled_pm_ids")
        if not raw:
            return cls.inactive()
        disabled = frozenset(str(pm_id) for pm_id in raw if pm_id)
        if not disabled:
            return cls.inactive()
        return cls(active=True, anchor_years=(), disabled_pm_ids=disabled)

    def begin_what_if(self) -> PlanningOverlayState:
        return PlanningOverlayState(active=True, anchor_years=(), disabled_pm_ids=frozenset())

    def reset_overlay(self) -> PlanningOverlayState:
        return PlanningOverlayState.inactive()

    def anchor_years_dict(self) -> dict[str, float]:
        return dict(self.anchor_years)

    def with_anchor_years(self, anchor_years: dict[str, float]) -> PlanningOverlayState:
        return PlanningOverlayState(
            active=self.active,
            anchor_years=tuple(sorted(anchor_years.items())),
            disabled_pm_ids=self.disabled_pm_ids,
        )

    def set_passive(self, pm_id: str, *, passive: bool) -> PlanningOverlayState:
        disabled = set(self.disabled_pm_ids)
        if passive:
            disabled.add(pm_id)
        else:
            disabled.discard(pm_id)
        return PlanningOverlayState(
            active=self.active,
            anchor_years=self.anchor_years,
            disabled_pm_ids=frozenset(disabled),
        )

    def bulk_all_rev_passive(self, project: RCMProject) -> PlanningOverlayState:
        rev_ids = _rev_pm_ids(project)
        return PlanningOverlayState(
            active=True,
            anchor_years=self.anchor_years,
            disabled_pm_ids=self.disabled_pm_ids | rev_ids,
        )

    def bulk_all_rev_active(self, project: RCMProject) -> PlanningOverlayState:
        rev_ids = _rev_pm_ids(project)
        disabled = set(self.disabled_pm_ids) - rev_ids
        return PlanningOverlayState(
            active=self.active,
            anchor_years=self.anchor_years,
            disabled_pm_ids=frozenset(disabled),
        )

    def all_rev_passive(self, project: RCMProject) -> bool:
        rev_ids = _rev_pm_ids(project)
        return bool(rev_ids) and rev_ids <= self.disabled_pm_ids

    def after_successful_overlay_run(self) -> PlanningOverlayState:
        """Behoud passieve set na herberekenen (slice 30): plot = laatste run."""
        return PlanningOverlayState(
            active=self.active,
            anchor_years=self.anchor_years,
            disabled_pm_ids=self.disabled_pm_ids,
        )

    def change_count(self) -> int:
        n_anchors = sum(1 for _pm, year in self.anchor_years if abs(year) > 1e-12)
        return n_anchors + len(self.disabled_pm_ids)


def _rev_pm_ids(project: RCMProject) -> frozenset[str]:
    return frozenset(
        task.pm_id
        for task in project.pm_tasks.values()
        if task.taak_type == TaskType.REV
    )
