"""UI-split voor correctieve kosten (adapter-only; geen diskvelden)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CmCostSplit:
    materiaal_eur: float
    arbeid_eur: float


_DEFAULT_MATERIAAL_FRACTION = 0.5


def _parse_hint_ratio(hint: str | None) -> float | None:
    if not hint:
        return None
    text = hint.strip().lower()
    m = re.search(r"materiaal\s*=\s*([\d.,]+)", text)
    a = re.search(r"arbeid\s*=\s*([\d.,]+)", text)
    if m and a:
        try:
            mat = float(m.group(1).replace(",", "."))
            arb = float(a.group(1).replace(",", "."))
            total = mat + arb
            if total > 0:
                return mat / total
        except ValueError:
            return None
    return None


def split_cm_cost(cost_cm_eur: float, hint: str | None = None) -> CmCostSplit:
    total = float(cost_cm_eur or 0.0)
    fraction = _parse_hint_ratio(hint)
    if fraction is None:
        fraction = _DEFAULT_MATERIAAL_FRACTION
    materiaal = round(total * fraction, 2)
    arbeid = round(total - materiaal, 2)
    return CmCostSplit(materiaal_eur=materiaal, arbeid_eur=arbeid)


def merge_cm_cost(split: CmCostSplit) -> float:
    return round(float(split.materiaal_eur or 0.0) + float(split.arbeid_eur or 0.0), 2)
