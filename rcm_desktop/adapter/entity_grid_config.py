"""Qt-vrije entiteiten-grid configuratie per Input-view (slice 83)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.editing.schemas import ENTITY_SCHEMAS

from rcm_desktop.adapter.faalwijzen_grid_contract import (
    EDITABLE_FIELDS as FAALWIJZEN_EDITABLE,
    READONLY_FIELDS as FAALWIJZEN_READONLY,
    SLICE_FIELD_KEYS,
)


@dataclass(frozen=True)
class EntityGridViewConfig:
    view_id: str
    entity: str
    preset_columns: tuple[str, ...]
    readonly_columns: frozenset[str]
    editable_columns: frozenset[str]
    key_field: str
    optional_columns: frozenset[str] = frozenset()
    derived_columns: frozenset[str] = frozenset()


def _editable_from_preset(
    entity: str,
    preset: tuple[str, ...],
    *,
    readonly: frozenset[str],
    extra_editable: frozenset[str] = frozenset(),
) -> frozenset[str]:
    fields = frozenset(ENTITY_SCHEMAS[entity]["field_types"])
    allow = (frozenset(preset) | extra_editable) & fields
    return allow - readonly


def _config(
    view_id: str,
    entity: str,
    preset: tuple[str, ...],
    *,
    readonly: frozenset[str],
    extra_editable: frozenset[str] = frozenset(),
    optional: frozenset[str] = frozenset(),
    derived: frozenset[str] = frozenset(),
) -> EntityGridViewConfig:
    schema = ENTITY_SCHEMAS[entity]
    return EntityGridViewConfig(
        view_id=view_id,
        entity=entity,
        preset_columns=preset,
        readonly_columns=(readonly | derived) & (frozenset(schema["field_types"]) | derived),
        editable_columns=_editable_from_preset(
            entity, preset, readonly=readonly | derived, extra_editable=extra_editable
        ),
        key_field=str(schema["key_field"]),
        optional_columns=optional,
        derived_columns=derived,
    )


_PM_DERIVED: frozenset[str] = frozenset(
    {
        "pm_first_execution_year",
        "pm_execution_count_lcc",
        "pm_downtime_oh",
        "pm_repair_quality",
        "pm_herstelduur",
    }
)

_PM_OPTIONAL: frozenset[str] = frozenset(
    {
        "library_ref",
        "unavailability_fraction",
        "pm_downtime_oh",
        "pm_repair_quality",
        "pm_herstelduur",
    }
)

_PM_TASKS_PRESET: tuple[str, ...] = (
    "pm_id",
    "fm_id",
    "taak_type",
    "taak_omschrijving",
    "interval_jaar",
    "pm_first_execution_year",
    "cost_eur",
    "pm_execution_count_lcc",
    "causes_unavailability",
    "task_group_id",
)

_EFFECT_PRESET: tuple[str, ...] = (
    "klasse_id",
    "omschrijving",
    "functie_id",
    "categorie",
    "cost_gevolg_eur",
)

_TASK_GROUPS_PRESET: tuple[str, ...] = (
    "group_id",
    "omschrijving",
    "taak_type",
    "interval_jaar",
    "cost_eur",
    "causes_unavailability",
)

_CORRECTIEF_PRESET: tuple[str, ...] = (
    "fm_id",
    "pbs_id",
    "faalwijze_omschrijving",
    "cost_cm_eur",
    "repair_quality",
    "aanname_cm_kosten",
    "aanname_downtime",
)

ENTITY_GRID_VIEW_CONFIGS: tuple[EntityGridViewConfig, ...] = (
    _config(
        "input.faalwijzen",
        "faalwijzes",
        SLICE_FIELD_KEYS,
        readonly=FAALWIJZEN_READONLY,
        extra_editable=FAALWIJZEN_EDITABLE,
        optional=frozenset(
            {
                "eindgevolg",
                "notes",
                "library_ref",
                "aanname_faalmodel",
                "aanname_effectklasse",
                "downtime_per_failure",
            }
        ),
    ),
    _config(
        "input.rev_tasks",
        "pm_tasks",
        _PM_TASKS_PRESET,
        readonly=frozenset({"pm_id"}),
        optional=_PM_OPTIONAL,
        derived=_PM_DERIVED,
    ),
    _config(
        "input.effecten",
        "effect_klassen",
        _EFFECT_PRESET,
        readonly=frozenset({"klasse_id"}),
        optional=frozenset({"notes", "aanname_gevolg_kosten"}),
    ),
    _config(
        "input.taakgroepen",
        "task_groups",
        _TASK_GROUPS_PRESET,
        readonly=frozenset({"group_id"}),
        optional=frozenset({"library_ref", "notes", "unavailability_fraction"}),
    ),
    _config(
        "input.correctief",
        "faalwijzes",
        _CORRECTIEF_PRESET,
        readonly=frozenset({"fm_id", "pbs_id", "faalwijze_omschrijving"}),
        extra_editable=frozenset(
            {"cost_cm_eur", "repair_quality", "aanname_cm_kosten", "aanname_downtime"}
        ),
        optional=frozenset(
            {
                "downtime_per_failure",
                "aanname_faalmodel",
                "p_ongewenste_gebeurtenis",
            }
        ),
    ),
)

_CONFIG_BY_VIEW: dict[str, EntityGridViewConfig] = {
    cfg.view_id: cfg for cfg in ENTITY_GRID_VIEW_CONFIGS
}


def entity_grid_config_for_view(view_id: str) -> EntityGridViewConfig | None:
    return _CONFIG_BY_VIEW.get(view_id)


def schema_columns_for_view(view_id: str) -> tuple[str, ...]:
    cfg = entity_grid_config_for_view(view_id)
    if cfg is None:
        return ()
    schema_fields = ENTITY_SCHEMAS[cfg.entity]["field_types"]
    preset_set = set(cfg.preset_columns)
    optional_ordered = [c for c in sorted(cfg.optional_columns) if c in schema_fields or c in cfg.derived_columns]
    return cfg.preset_columns + tuple(c for c in optional_ordered if c not in cfg.preset_columns)


def validate_entity_grid_configs(
    configs: tuple[EntityGridViewConfig, ...],
) -> None:
    seen_views: set[str] = set()
    for cfg in configs:
        if cfg.view_id in seen_views:
            raise ValueError(f"duplicate view_id: {cfg.view_id}")
        seen_views.add(cfg.view_id)
        schema = ENTITY_SCHEMAS.get(cfg.entity)
        if schema is None:
            raise ValueError(f"unknown entity {cfg.entity!r} for {cfg.view_id}")
        fields = set(schema["field_types"])
        for col in cfg.preset_columns:
            if col in cfg.derived_columns:
                continue
            if col not in fields:
                raise ValueError(
                    f"preset column {col!r} not in schema for {cfg.view_id}"
                )
        for col in cfg.optional_columns:
            if col in cfg.derived_columns:
                continue
            if col not in fields:
                raise ValueError(
                    f"optional column {col!r} not in schema for {cfg.view_id}"
                )
        unknown_editable = cfg.editable_columns - fields
        if unknown_editable:
            raise ValueError(
                f"editable columns not in schema for {cfg.view_id}: {unknown_editable}"
            )
        if cfg.key_field != schema["key_field"]:
            raise ValueError(
                f"key_field mismatch for {cfg.view_id}: {cfg.key_field!r}"
            )


validate_entity_grid_configs(ENTITY_GRID_VIEW_CONFIGS)
