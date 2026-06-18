"""Informatieve AW EffectCost-pariteit (slice 70 issue 10)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from rcm_core.effect_impact_service import aggregate
from rcm_core.models import FMResult, RCMProject
from rcm_core.rcm_cost_benchmark import ParityVerdict

_CAUSE_SETTINGS_KEY = "isograph_causes"


@dataclass(frozen=True)
class EffectCostParityRow:
    fm_id: str
    klasse_id: str
    verdict: ParityVerdict
    rcm2_waarde: float
    eenheid: str
    aw_effect_cost: float | None
    aw_effect_cost_err: float | None
    delta: float | None


@dataclass(frozen=True)
class EffectCostParityReport:
    rows: tuple[EffectCostParityRow, ...]


def build_effect_cost_parity_report(
    project: RCMProject,
    fm_results: Mapping[str, FMResult],
) -> EffectCostParityReport:
    """Vergelijk RCM2 effectimpact met AW EffectCost — informatief, geen gate."""
    settings = project.import_settings.get(_CAUSE_SETTINGS_KEY, {})
    if not isinstance(settings, dict):
        settings = {}

    rows: list[EffectCostParityRow] = []
    for fm_id, fmr in fm_results.items():
        cause_meta = settings.get(fm_id)
        if not isinstance(cause_meta, dict):
            cause_meta = {}
        effect_rows = aggregate(project, {fm_id: fmr}, fm_ids=frozenset({fm_id}))
        for er in effect_rows:
            aw_cost = _float_or_none(cause_meta.get("effect_cost"))
            aw_err = _float_or_none(cause_meta.get("effect_cost_err"))
            if aw_cost is None:
                verdict = ParityVerdict.MISSING_BENCHMARK
                delta = None
            else:
                verdict = ParityVerdict.INFORMATIVE
                delta = er.waarde_totaal - aw_cost
            rows.append(
                EffectCostParityRow(
                    fm_id=fm_id,
                    klasse_id=er.klasse_id,
                    verdict=verdict,
                    rcm2_waarde=er.waarde_totaal,
                    eenheid=er.eenheid,
                    aw_effect_cost=aw_cost,
                    aw_effect_cost_err=aw_err,
                    delta=delta,
                )
            )
    return EffectCostParityReport(rows=tuple(rows))


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
