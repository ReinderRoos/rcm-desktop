"""Patch apply, audit trail en rollback (slice 95 issue 09)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from rcm_core.models import RCMProject

from rcm_desktop.adapter.normalization_proposal_service import NormalizationProposalItem


@dataclass(frozen=True)
class NormalizationPatch:
    target_fm_id: str
    field: str
    new_value: object
    approved: bool = False


@dataclass
class AuditTrail:
    entries: list[dict[str, object]] = field(default_factory=list)

    @property
    def patch_count(self) -> int:
        return len(self.entries)


def apply_patch(project: RCMProject, patch: NormalizationPatch) -> tuple[RCMProject, AuditTrail]:
    if not patch.approved:
        raise ValueError("Patch requires approved=True")
    updated = copy.deepcopy(project)
    fm = updated.faalwijzes.get(patch.target_fm_id)
    if fm is None:
        raise ValueError(f"Unknown FM: {patch.target_fm_id}")
    previous = getattr(fm, patch.field, None)
    setattr(fm, patch.field, patch.new_value)
    audit = AuditTrail(
        entries=[
            {
                "fm_id": patch.target_fm_id,
                "field": patch.field,
                "previous": previous,
                "new": patch.new_value,
            }
        ]
    )
    return updated, audit


def rollback_last_patch(project: RCMProject, audit: AuditTrail) -> RCMProject:
    if not audit.entries:
        return project
    restored = copy.deepcopy(project)
    entry = audit.entries[-1]
    fm = restored.faalwijzes.get(str(entry["fm_id"]))
    if fm is not None:
        setattr(fm, str(entry["field"]), entry["previous"])
    audit.entries.pop()
    return restored


def apply_approved_normalization(
    project: RCMProject,
    proposal_items: tuple[NormalizationProposalItem, ...],
    *,
    approved_indices: frozenset[int],
) -> tuple[RCMProject, AuditTrail]:
    updated = project
    combined = AuditTrail()
    for index, item in enumerate(proposal_items):
        if index not in approved_indices:
            continue
        target_fm = item.fm_id_a if item.source_side == "a_to_b" else item.fm_id_b
        if target_fm is None:
            continue
        patch = NormalizationPatch(
            target_fm_id=target_fm,
            field=item.field,
            new_value=item.proposed_value,
            approved=True,
        )
        updated, audit = apply_patch(updated, patch)
        combined.entries.extend(audit.entries)
    return updated, combined
