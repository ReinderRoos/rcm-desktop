"""Smalle kopie Basis + Correctief tussen faalwijze-rijen (slice 59.3)."""

from __future__ import annotations

from typing import Any, Literal

CopySection = Literal["basis", "correctief"]

_BASIS_FIELDS = (
    "failure_type",
    "mttf_jaar",
    "sigma_jaar",
    "aging_distribution",
    "beta_jaar",
    "is_evident",
    "repair_quality",
    "faalwijze_omschrijving",
    "p_ongewenste_gebeurtenis",
    "eindgevolg",
)

_CORRECTIEF_FIELDS = (
    "cost_cm_eur",
    "downtime_per_failure",
    "notes",
    "aanname_cm_kosten",
    "aanname_downtime",
)


def copy_fields(
    source_row: dict[str, Any],
    target_row: dict[str, Any],
    *,
    sections: tuple[CopySection, ...] = ("basis", "correctief"),
) -> dict[str, Any]:
    """Kopieer geselecteerde secties; ids en FK's in ``target_row`` blijven intact."""
    out = dict(target_row)
    fields: list[str] = []
    if "basis" in sections:
        fields.extend(_BASIS_FIELDS)
    if "correctief" in sections:
        fields.extend(_CORRECTIEF_FIELDS)
    for field in fields:
        if field in source_row:
            value = source_row[field]
            if field == "downtime_per_failure" and isinstance(value, dict):
                out[field] = dict(value)
            else:
                out[field] = value
    return out
