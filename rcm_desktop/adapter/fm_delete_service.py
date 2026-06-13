"""Faalwijze verwijderen — bevestiging en cascade via editing-pipeline (slice 99)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.editing.validation import normalize_key

from rcm_desktop.adapter.entity_edit_service import EntityEditService
from rcm_desktop.adapter.input_revalidation_service import revalidate_input_buffer


@dataclass(frozen=True)
class FmDeleteConfirmation:
    fm_id: str
    pm_task_count: int
    fm_effect_link_count: int
    pm_effect_link_count: int
    task_group_count: int

    @property
    def has_linked_entities(self) -> bool:
        return (
            self.pm_task_count > 0
            or self.fm_effect_link_count > 0
            or self.pm_effect_link_count > 0
            or self.task_group_count > 0
        )


def build_fm_delete_confirmation(service: EntityEditService, fm_id: str) -> FmDeleteConfirmation:
    target = normalize_key(fm_id)
    session = service.editing_session.session
    current = session.get("edit_current", {})
    pm_rows = current.get("pm_tasks", [])
    pm_for_fm = [r for r in pm_rows if normalize_key(r.get("fm_id")) == target]
    pm_ids = {normalize_key(r.get("pm_id")) for r in pm_for_fm}
    fm_effect_count = sum(
        1 for r in current.get("fm_effect_links", []) if normalize_key(r.get("fm_id")) == target
    )
    pm_effect_count = sum(
        1 for r in current.get("pm_effect_links", []) if normalize_key(r.get("pm_id")) in pm_ids
    )
    task_group_ids = {
        normalize_key(r.get("task_group_id"))
        for r in pm_for_fm
        if normalize_key(r.get("task_group_id"))
    }
    return FmDeleteConfirmation(
        fm_id=target,
        pm_task_count=len(pm_for_fm),
        fm_effect_link_count=fm_effect_count,
        pm_effect_link_count=pm_effect_count,
        task_group_count=len(task_group_ids),
    )


def delete_faalwijze_row(service: EntityEditService, fm_id: str) -> None:
    """Verwijder FM en gekoppelde rijen uit de edit-buffer."""
    if service.config.entity != "faalwijzes":
        raise ValueError("delete_faalwijze_row is alleen voor faalwijzen-view")
    service.delete_row(fm_id)
