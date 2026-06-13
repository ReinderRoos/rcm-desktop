"""Uniformeringsvoorstel builder (slice 95 issue 08)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_desktop.adapter.compare_balanced_presentation_service import ComparePresentation
from rcm_desktop.adapter.compare_diff_service import FieldDiff


@dataclass(frozen=True)
class NormalizationProposalItem:
    fm_id_a: str | None
    fm_id_b: str | None
    field: str
    proposed_value: object
    source_side: str  # a_to_b | b_to_a
    approved: bool = False


@dataclass(frozen=True)
class NormalizationProposal:
    direction: str
    items: tuple[NormalizationProposalItem, ...]


def build_normalization_proposals(
    presentation: ComparePresentation,
    *,
    direction: str = "a_to_b",
) -> NormalizationProposal:
    items: list[NormalizationProposalItem] = []
    for entry in presentation.entries:
        pair = entry.pair
        if pair.fm_id_a is None or pair.fm_id_b is None:
            continue
        for diff in entry.field_diffs:
            if direction == "a_to_b":
                proposed = diff.value_b
                source = "a_to_b"
            else:
                proposed = diff.value_a
                source = "b_to_a"
            items.append(
                NormalizationProposalItem(
                    fm_id_a=pair.fm_id_a,
                    fm_id_b=pair.fm_id_b,
                    field=diff.field,
                    proposed_value=proposed,
                    source_side=source,
                    approved=False,
                )
            )
    return NormalizationProposal(direction=direction, items=tuple(items))
