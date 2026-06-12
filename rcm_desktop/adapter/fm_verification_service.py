"""FM-verificatieview voor inspectorpaneel (slice 34).

Bouwt read-only presentatie uit motor-`FMResult` + project. Geen Qt-imports.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from rcm_core.cache import compute_fm_hash
from rcm_core.effect_impact_service import (
    EffectNbFilterSet,
    EffectPresentation,
    aggregate,
    nb_scalar_for_fm,
    nb_yearly_series,
)
from rcm_core.models import Faalwijze, FMResult, RCMProject

_NB_LIFECYCLE_HOURS = EffectPresentation(
    horizon="lifecycle", unavailability_display="hours"
)

from rcm_desktop.adapter.calendar_year import calendar_year_for_horizon_index
from rcm_desktop.adapter.horizon_bucket_series import (
    faalmomenten_per_bucket,
    motor_cor_eur_per_bucket,
    motor_cor_downtime_per_bucket,
    motor_hidden_nb_per_bucket,
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
    pm_effect_links: tuple[FMVerificationEffectLinkRow, ...] = ()


@dataclass(frozen=True)
class FMVerificationEffectResultRow:
    klasse_id: str
    label: str
    rf_display: str
    waarde_cm: float
    waarde_pm: float
    waarde_totaal: float
    eenheid: str


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
    #: Gepresenteerde (NB-gefilterde) niet-beschikbaarheid per bucket, uren.
    #: Lege filter = totale NB-bucketreeks (ADR-0010); slice 74.
    nb_downtime_hr: float = 0.0


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
    effect_result_rows: tuple[FMVerificationEffectResultRow, ...] = ()


def build_fm_verification_view(
    project: RCMProject,
    fmr: FMResult,
    *,
    nb_filter: EffectNbFilterSet | None = None,
) -> FMVerificationView:
    filt = nb_filter or EffectNbFilterSet()
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
        faal_buckets = faalmomenten_per_bucket(project, fmr)
        cor_eur = motor_cor_eur_per_bucket(fmr, num)
        cor_dt = motor_cor_downtime_per_bucket(fmr, num)
        hidden = motor_hidden_nb_per_bucket(fmr, num)
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

        nb_buckets = nb_yearly_series(project, {fmr.fm_id: fmr}, nb_filter=filt)
        while len(nb_buckets) < num:
            nb_buckets.append(0.0)
        nb_buckets = nb_buckets[:num]

        modeljaar = int(project.config.modeljaar)
        year_rows = tuple(
            FMVerificationYearRow(
                calendar_year=calendar_year_for_horizon_index(modeljaar, h),
                faalmomenten=float(faal_buckets[h]),
                cor_eur=float(cor_eur[h]),
                cor_downtime_hr=float(cor_dt[h]),
                hidden_nb_hr=float(hidden[h]),
                nb_downtime_hr=float(nb_buckets[h]),
            )
            for h in range(num)
        )
        reconcile_ok, reconcile_notes = _reconcile(lifecycle, year_rows, hp_sums=(cor_eur, cor_dt, hidden))

    effect_rows = _effect_result_rows(project, fmr)

    # Slice 74: de getoonde lifecycle-downtime reflecteert de actieve NB-filter.
    # Lege filter short-circuit → identiek aan vandaag (motor-CM-downtime); de
    # reconcile/hash/identiteit zijn al op de motorwaarden berekend.
    display_lifecycle = lifecycle
    if not filt.is_all():
        display_lifecycle = replace(
            lifecycle,
            expected_total_downtime_hr=nb_scalar_for_fm(
                project, fmr, nb_filter=filt, presentation=_NB_LIFECYCLE_HOURS
            ),
        )

    return FMVerificationView(
        fm_id=fmr.fm_id,
        faalwijze_omschrijving=faalwijze_omschrijving,
        pbs_id=fmr.pbs_id,
        bouwdeel_naam=bouwdeel_naam,
        fm_input_hash=fm_input_hash,
        inputs=inputs,
        lifecycle=display_lifecycle,
        year_rows=year_rows,
        profile_missing=profile_missing,
        reconcile_ok=reconcile_ok,
        reconcile_notes=tuple(reconcile_notes),
        effect_result_rows=effect_rows,
    )


def _effect_result_rows(
    project: RCMProject,
    fmr: FMResult,
) -> tuple[FMVerificationEffectResultRow, ...]:
    rows = aggregate(
        project,
        {fmr.fm_id: fmr},
        fm_ids=frozenset({fmr.fm_id}),
    )
    return tuple(
        FMVerificationEffectResultRow(
            klasse_id=r.klasse_id,
            label=r.label,
            rf_display=r.rf_display,
            waarde_cm=r.waarde_cm,
            waarde_pm=r.waarde_pm,
            waarde_totaal=r.waarde_totaal,
            eenheid=r.eenheid,
        )
        for r in rows
    )


def _build_inputs(project: RCMProject, fm: Faalwijze) -> FMVerificationInputs:
    pbs = project.pbs_items.get(fm.pbs_id)
    modeljaar = int(project.config.modeljaar)
    initial_age = pbs.current_age(modeljaar) if pbs is not None else 0.0
    sigma_raw = float(fm.sigma_jaar)
    sigma_uses_default = sigma_raw <= 0.0
    sigma_display = float(fm.effective_sigma(project.config.default_sigma_fraction)) if sigma_uses_default else sigma_raw
    effect_rows = _effect_link_rows(project, project.get_fm_effect_links_for_fm(fm.fm_id))
    pm_ids = {t.pm_id for t in project.get_pm_tasks_for_fm(fm.fm_id)}
    pm_links = [
        link for link in project.pm_effect_links.values() if link.pm_id in pm_ids
    ]
    pm_effect_rows = _effect_link_rows(project, sorted(pm_links, key=lambda l: l.link_id))
    return FMVerificationInputs(
        initial_age_jaar=initial_age,
        mttf_jaar=float(fm.mttf_jaar),
        failure_type=fm.failure_type.value,
        sigma_jaar=sigma_display,
        sigma_uses_default=sigma_uses_default,
        mttr_hr=float(fm.downtime_per_failure.to_hours()),
        cost_cm_eur=float(fm.cost_cm_eur),
        effect_links=tuple(effect_rows),
        pm_effect_links=tuple(pm_effect_rows),
    )


def _effect_link_rows(
    project: RCMProject,
    links: list,
) -> list[FMVerificationEffectLinkRow]:
    rows: list[FMVerificationEffectLinkRow] = []
    for link in links:
        ek = project.effect_klassen.get(link.klasse_id)
        omsch = ek.omschrijving if ek is not None else ""
        rows.append(
            FMVerificationEffectLinkRow(
                klasse_id=link.klasse_id,
                effect_omschrijving=omsch,
                fractie=float(link.fractie),
            )
        )
    return rows


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
