"""Schema-gedreven grid-contract voor faalwijzen batch-bewerking (slice 46)."""

from __future__ import annotations

from rcm_core.editing.schemas import ENTITY_SCHEMAS

_ENTITY = "faalwijzes"
_SCHEMA = ENTITY_SCHEMAS[_ENTITY]
_REGISTRY_FIELDS = frozenset(_SCHEMA["field_types"])

READONLY_GRID_FIELDS: tuple[str, ...] = ("fm_id", "pbs_id")

# Must (C) + should (B) uit PRD slice 46 — alleen velden die in de registry staan.
_GRID_MUST_ALLOWLIST: frozenset[str] = frozenset(
    {
        "failure_type",
        "aging_distribution",
        "mttf_jaar",
        "sigma_jaar",
        "beta_jaar",
        "is_evident",
        "faalwijze_omschrijving",
        "functie_id",
        "repair_quality",
    }
)
_GRID_SHOULD_ALLOWLIST: frozenset[str] = frozenset(
    {"cost_cm_eur", "p_ongewenste_gebeurtenis"}
)

_GRID_COLUMN_ORDER: tuple[str, ...] = (
    "fm_id",
    "pbs_id",
    "failure_type",
    "aging_distribution",
    "is_evident",
    "faalwijze_omschrijving",
    "functie_id",
    "mttf_jaar",
    "sigma_jaar",
    "beta_jaar",
    "repair_quality",
    "cost_cm_eur",
    "p_ongewenste_gebeurtenis",
)


def grid_editable_fields() -> frozenset[str]:
    allow = (_GRID_MUST_ALLOWLIST | _GRID_SHOULD_ALLOWLIST) & _REGISTRY_FIELDS
    return frozenset(allow)


def grid_column_keys() -> tuple[str, ...]:
    editable = grid_editable_fields()
    out: list[str] = []
    for key in _GRID_COLUMN_ORDER:
        if key in READONLY_GRID_FIELDS or key in editable:
            out.append(key)
    return tuple(out)


# Back-compat alias voor bestaande tests/imports
SLICE_FIELD_KEYS: tuple[str, ...] = grid_column_keys()
EDITABLE_FIELDS: frozenset[str] = grid_editable_fields()
READONLY_FIELDS: frozenset[str] = frozenset(READONLY_GRID_FIELDS)
