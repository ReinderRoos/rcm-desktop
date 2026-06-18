"""Uniformeren review-presentatie (slice 95 issue 10)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop import messages
from rcm_desktop.adapter.normalization_proposal_service import (
    NormalizationProposal,
    NormalizationProposalItem,
)


@dataclass(frozen=True)
class NormalizationReviewRow:
    index: int
    fm_id_a: str | None
    fm_id_b: str | None
    field: str
    proposed_value: object
    source_side: str
    source_label: str
    approved: bool


@dataclass(frozen=True)
class NormalizationReviewPresentation:
    direction: str
    items: tuple[NormalizationReviewRow, ...]


def _source_label(source_side: str) -> str:
    if source_side == "b_to_a":
        return messages.NORMALIZATION_REVIEW_SOURCE_B_TO_A
    return messages.NORMALIZATION_REVIEW_SOURCE_A_TO_B


def build_normalization_review_presentation(
    proposal: NormalizationProposal,
) -> NormalizationReviewPresentation:
    rows: list[NormalizationReviewRow] = []
    for index, item in enumerate(proposal.items):
        rows.append(
            NormalizationReviewRow(
                index=index,
                fm_id_a=item.fm_id_a,
                fm_id_b=item.fm_id_b,
                field=item.field,
                proposed_value=item.proposed_value,
                source_side=item.source_side,
                source_label=_source_label(item.source_side),
                approved=item.approved,
            )
        )
    return NormalizationReviewPresentation(direction=proposal.direction, items=tuple(rows))


def with_approval(
    proposal: NormalizationProposal,
    *,
    approved_indices: frozenset[int],
) -> NormalizationProposal:
    items: list[NormalizationProposalItem] = []
    for index, item in enumerate(proposal.items):
        items.append(
            NormalizationProposalItem(
                fm_id_a=item.fm_id_a,
                fm_id_b=item.fm_id_b,
                field=item.field,
                proposed_value=item.proposed_value,
                source_side=item.source_side,
                approved=index in approved_indices,
            )
        )
    return NormalizationProposal(direction=proposal.direction, items=tuple(items))
