"""Qt-vrije celweergave voor entiteiten-grid (slice 87)."""

from __future__ import annotations

from typing import Any

from rcm_core.models import RCMProject

from rcm_desktop import messages
from rcm_desktop.formatting import format_float

_FAILURE_TYPE_LABELS = {
    "random": messages.FAALWIJZEN_FAILURE_RANDOM,
    "aging": messages.FAALWIJZEN_FAILURE_AGING,
}

_AGING_DISTRIBUTION_LABELS = {
    "normal": "Normal",
    "truncated_normal_0": "Links-afgeknipt normal 0+",
    "weibull_2p": "Weibull 2p",
}


def display_faalwijze_field(project: RCMProject, field: str, value: Any) -> str:
    if field == "fm_id":
        return str(value or "")
    if field == "pbs_id":
        return str(value or "")
    if field == "failure_type":
        s = str(value or "random")
        return _FAILURE_TYPE_LABELS.get(s, s)
    if field == "aging_distribution":
        s = str(value or "normal")
        return _AGING_DISTRIBUTION_LABELS.get(s, s)
    if field == "is_evident":
        return messages.FAALWIJZEN_NMF_JA if not bool(value) else messages.FAALWIJZEN_NMF_NEE
    if field == "faalwijze_omschrijving":
        return str(value or "")
    if field == "functie_id":
        fid = str(value or "").strip()
        if not fid:
            return ""
        fn = project.functies.get(fid)
        if fn is None:
            return fid
        return f"{fid} — {fn.functie_omschrijving}"
    if field in (
        "mttf_jaar",
        "sigma_jaar",
        "beta_jaar",
        "repair_quality",
        "cost_cm_eur",
        "p_ongewenste_gebeurtenis",
    ):
        if value is None:
            return ""
        try:
            return format_float(float(value))
        except (TypeError, ValueError):
            return str(value)
    return str(value or "")
