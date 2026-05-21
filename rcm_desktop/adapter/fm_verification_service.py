"""FM-verificatieview voor inspectorpaneel (slice 34).

Bouwt read-only presentatie uit motor-`FMResult` + project. Geen Qt-imports.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from rcm_core.cache import compute_fm_hash
from rcm_core.models import Faalwijze, FMResult, RCMProject

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.contribution_horizon_value_service import (
    _faalmomenten_per_bucket,
)
from rcm_core.lcc_profile import ltap_horizon_bucket_count

_RECONCILE_ABS = 1e-3


@dataclass(frozen=True)
class FMVerificationEffectLinkRow:
    klasse_id: str
    effect_omschrijving: str
    fractie: float


@dataclass(frozen=True)
class FMVerificationInputs:
    initial_age_jaar: float
    mttf_jaar: float
    failure_type: str
    sigma_jaar: float
    sigma_uses_default: bool
    mttr_hr: float
    cost_cm_eur: float
    effect_links: tuple[FMVerificationEffectLinkRow, ...]


@dataclass(frozen=True)
class FMVerificationLifecycle:
    expected_failures: float
    expected_raw_downtime_hr: float
    expected_detection_delay_hr: float
    expected_pm_downtime_hr: float
    expected_total_downtime_hr: float
    expected_cm_cost_eur: float
    pm_cost_eur: float
    total_cost_eur: float
    effect_bijdragen: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class FMVerificationYearRow:
    calendar_year: int
    faalmomenten: float
    cor_eur: float
    cor_downtime_hr: float
    hidden_nb_hr: float


@dataclass(frozen=True)
class FMVerificationView:
    fm_id: str
    faalwijze_omschrijving: str
    pbs_id: str
    bouwdeel_naam: str
    fm_input_hash: str | None
    inputs: FMVerificationInputs | None
    lifecycle: FMVerificationLifecycle
    year_rows: tuple[FMVerificationYearRow, ...]
    profile_missing: bool
    reconcile_ok: bool
    reconcile_notes: tuple[str, ...]


def build_fm_verification_view(project: RCMProject, fmr: FMResult) -> FMVerificationView:
    fm = project.faalwijzes.get(fmr.fm_id)
    faalwijze_omschrijving = fm.faalwijze_omschrijving if fm is not None else ""
    pbs = project.pbs_items.get(fmr.pbs_id)
    bouwdeel_naam = pbs.bouwdeel_naam if pbs is not None else ""

    lifecycle = FMVerificationLifecycle(
        expected_failures=float(fmr.expected_failures),
        expected_raw_downtime_hr=float(fmr.expected_raw_downtime_hr),
        expected_detection_delay_hr=float(fmr.expected_detection_delay_hr),
        expected_pm_downtime_hr=float(fmr.expected_pm_downtime_hr),
        expected_total_downtime_hr=float(fmr.expected_total_downtime_hr),
        expected_cm_cost_eur=float(fmr.expected_cm_cost_eur),
        pm_cost_eur=float(fmr.pm_cost_eur),
        total_cost_eur=float(fmr.total_cost_eur),
        effect_bijdragen=tuple(
            sorted((str(k), float(v)) for k, v in fmr.effect_bijdragen.items())
        ),
    )

    fm_input_hash: str | None = None
    inputs: FMVerificationInputs | None = None
    if fm is not None:
        fm_input_hash = compute_fm_hash(project, fmr.fm_id)
        inputs = _build_inputs(project, fm)

    hp = fmr.horizon_profile
    profile_missing = hp is None
    year_rows: tuple[FMVerificationYearRow, ...] = ()
    reconcile_ok = False
    reconcile_notes: list[str] = []

    if profile_missing:
        reconcile_notes.append(
            "Geen horizon_profile: alleen lifecycle-totalen zijn betrouwbaar."
        )
    else:
        num = ltap_horizon_bucket_count(float(project.config.lifecycle_years))
        faal_buckets = _faalmomenten_per_bucket(project, fmr)
        cor_eur = list(hp.cor_eur)
        cor_dt = list(hp.cor_downtime_hr)
        hidden = list(hp.hidden_nb_hr)
        while len(cor_eur) < num:
            cor_eur.append(0.0)
        while len(cor_dt) < num:
            cor_dt.append(0.0)
        while len(hidden) < num:
            hidden.append(0.0)
        cor_eur = cor_eur[:num]
        cor_dt = cor_dt[:num]
        hidden = hidden[:num]
        while len(faal_buckets) < num:
            faal_buckets.append(0.0)
        faal_buckets = faal_buckets[:num]

        modeljaar = int(project.config.modeljaar)
        year_rows = tuple(
            FMVerificationYearRow(
                calendar_year=calendar_year_for_horizon_index(modeljaar, h),
                faalmomenten=float(faal_buckets[h]),
                cor_eur=float(cor_eur[h]),
                cor_downtime_hr=float(cor_dt[h]),
                hidden_nb_hr=float(hidden[h]),
            )
            for h in range(num)
        )
        reconcile_ok, reconcile_notes = _reconcile(lifecycle, year_rows, hp_sums=(cor_eur, cor_dt, hidden))

    return FMVerificationView(
        fm_id=fmr.fm_id,
        faalwijze_omschrijving=faalwijze_omschrijving,
        pbs_id=fmr.pbs_id,
        bouwdeel_naam=bouwdeel_naam,
        fm_input_hash=fm_input_hash,
        inputs=inputs,
        lifecycle=lifecycle,
        year_rows=year_rows,
        profile_missing=profile_missing,
        reconcile_ok=reconcile_ok,
        reconcile_notes=tuple(reconcile_notes),
    )


def _build_inputs(project: RCMProject, fm: Faalwijze) -> FMVerificationInputs:
    pbs = project.pbs_items.get(fm.pbs_id)
    modeljaar = int(project.config.modeljaar)
    initial_age = pbs.current_age(modeljaar) if pbs is not None else 0.0
    sigma_raw = float(fm.sigma_jaar)
    sigma_uses_default = sigma_raw <= 0.0
    sigma_display = float(fm.effective_sigma) if sigma_uses_default else sigma_raw
    effect_rows: list[FMVerificationEffectLinkRow] = []
    for link in sorted(
        project.get_fm_effect_links_for_fm(fm.fm_id), key=lambda l: l.link_id
    ):
        ek = project.effect_klassen.get(link.klasse_id)
        omsch = ek.omschrijving if ek is not None else ""
        effect_rows.append(
            FMVerificationEffectLinkRow(
                klasse_id=link.klasse_id,
                effect_omschrijving=omsch,
                fractie=float(link.fractie),
            )
        )
    return FMVerificationInputs(
        initial_age_jaar=initial_age,
        mttf_jaar=float(fm.mttf_jaar),
        failure_type=fm.failure_type.value,
        sigma_jaar=sigma_display,
        sigma_uses_default=sigma_uses_default,
        mttr_hr=float(fm.downtime_per_failure.to_hours()),
        cost_cm_eur=float(fm.cost_cm_eur),
        effect_links=tuple(effect_rows),
    )


def _reconcile(
    lifecycle: FMVerificationLifecycle,
    year_rows: tuple[FMVerificationYearRow, ...],
    *,
    hp_sums: tuple[list[float], list[float], list[float]],
) -> tuple[bool, list[str]]:
    notes: list[str] = []
    ok = True

    sum_faal = sum(r.faalmomenten for r in year_rows)
    if not math.isclose(sum_faal, lifecycle.expected_failures, abs_tol=_RECONCILE_ABS):
        ok = False
        notes.append(
            f"Faalmomenten: som buckets ({sum_faal:.4f}) ≠ lifecycle ({lifecycle.expected_failures:.4f})."
        )

    cor_eur, cor_dt, hidden = hp_sums
    sum_eur = float(sum(cor_eur))
    if not math.isclose(sum_eur, lifecycle.expected_cm_cost_eur, abs_tol=_RECONCILE_ABS):
        ok = False
        notes.append(
            f"Correctief EUR: som buckets ({sum_eur:.2f}) ≠ lifecycle CM ({lifecycle.expected_cm_cost_eur:.2f})."
        )

    sum_hidden = float(sum(hidden))
    if not math.isclose(
        sum_hidden, lifecycle.expected_detection_delay_hr, abs_tol=_RECONCILE_ABS
    ):
        ok = False
        notes.append(
            "Verborgen NB: som buckets wijkt af van detection delay (lifecycle)."
        )

    sum_cor_dt = float(sum(cor_dt))
    target_cm_dt = lifecycle.expected_total_downtime_hr
    if not math.isclose(sum_cor_dt, target_cm_dt, abs_tol=_RECONCILE_ABS):
        ok = False
        notes.append(
            f"Correctieve downtime: som buckets ({sum_cor_dt:.2f}) ≠ lifecycle CM-downtime ({target_cm_dt:.2f})."
        )

    if ok:
        notes.append("Reconcile OK: buckets en lifecycle komen overeen (binnen tolerantie).")

    return ok, notes
