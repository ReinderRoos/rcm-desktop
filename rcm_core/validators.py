"""
validators.py — FK-controles en domeinvalidaties voor RCMProject.

Retourneert een lijst van ValidationError-objecten (nooit exceptions).
Een lege lijst betekent: project is geldig.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rcm_core.models import FailureType

if TYPE_CHECKING:
    from rcm_core.models import RCMProject


@dataclass
class ValidationError:
    code: str
    message: str
    context: str = ""  # bijv. fm_id of pbs_id

    def __str__(self) -> str:
        ctx = f" [{self.context}]" if self.context else ""
        return f"[{self.code}]{ctx} {self.message}"


def validate_project(project: "RCMProject") -> list[ValidationError]:
    """Valideer structurele integriteit van het project (FK-controles, numerieke grenzen).

    Retourneert een lege lijst als het project structureel geldig is.
    Voor aanname-volledigheid, gebruik validate_aannamen() afzonderlijk.
    """
    errors: list[ValidationError] = []

    errors.extend(_validate_pbs(project))
    errors.extend(_validate_functies(project))
    errors.extend(_validate_faalwijzes(project))
    errors.extend(_validate_pm_tasks(project))
    errors.extend(_validate_task_groups(project))
    errors.extend(_validate_effect_klassen(project))
    errors.extend(_validate_fm_effect_links(project))
    errors.extend(_validate_pm_effect_links(project))
    errors.extend(_validate_config(project))

    return errors


def validate_aannamen(project: "RCMProject") -> list[ValidationError]:
    """Controleer volledigheid en coherentie van aannamen (waarschuwingen).

    Los van validate_project() — retourneert waarschuwingen over ontbrekende
    of tegenstrijdige aannamen. Een lege lijst betekent dat alle aannamen
    aanwezig en coherent zijn.
    """
    return _validate_aannamen(project)


def _validate_pbs(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    for pbs_id, pbs in project.pbs_items.items():
        if pbs.multiplicity < 1:
            errors.append(ValidationError(
                "PBS_MULTIPLICITY", f"multiplicity moet >= 1 zijn (is {pbs.multiplicity})", pbs_id
            ))
        if pbs.ontwerpleeftijd_jaar < 0:
            errors.append(ValidationError(
                "PBS_OLD_NEGATIVE", "ontwerpleeftijd_jaar mag niet negatief zijn", pbs_id
            ))
        if pbs.bouwjaar < 0:
            errors.append(ValidationError(
                "PBS_BOUWJAAR_NEGATIVE", "bouwjaar mag niet negatief zijn", pbs_id
            ))
        if pbs.parent_pbs_id is not None:
            if pbs.parent_pbs_id not in project.pbs_items:
                errors.append(ValidationError(
                    "PBS_PARENT_FK",
                    f"parent_pbs_id '{pbs.parent_pbs_id}' bestaat niet",
                    pbs_id,
                ))
            elif pbs.parent_pbs_id == pbs_id:
                errors.append(ValidationError(
                    "PBS_PARENT_SELF", "PBS-item verwijst naar zichzelf als parent", pbs_id
                ))

    # Effectief bouwjaar mag niet 0 zijn na parent-resolutie
    for pbs_id, pbs in project.pbs_items.items():
        if pbs.effective_bouwjaar(project.pbs_items) == 0:
            errors.append(ValidationError(
                "PBS_EFFECTIVE_BOUWJAAR_ZERO",
                "effectief bouwjaar is 0 (geen geldig bouwjaar in eigen item of parent-keten)",
                pbs_id,
            ))

    # Kind mag niet ouder zijn dan zijn parent
    for pbs_id, pbs in project.pbs_items.items():
        if pbs.bouwjaar > 0 and pbs.parent_pbs_id and pbs.parent_pbs_id in project.pbs_items:
            parent_bj = project.pbs_items[pbs.parent_pbs_id].effective_bouwjaar(project.pbs_items)
            if parent_bj > 0 and pbs.bouwjaar < parent_bj:
                errors.append(ValidationError(
                    "PBS_BOUWJAAR_CHRONOLOGIE",
                    f"bouwjaar {pbs.bouwjaar} ligt vóór het effectieve bouwjaar van de parent "
                    f"({pbs.parent_pbs_id}: {parent_bj})",
                    pbs_id,
                ))

    # Cycle-detectie in de parent-hiërarchie (DFS)
    def has_cycle(start_id: str, visited: set[str]) -> bool:
        current = project.pbs_items.get(start_id)
        if current is None or current.parent_pbs_id is None:
            return False
        if current.parent_pbs_id in visited:
            return True
        visited.add(current.parent_pbs_id)
        return has_cycle(current.parent_pbs_id, visited)

    for pbs_id in project.pbs_items:
        if has_cycle(pbs_id, {pbs_id}):
            errors.append(ValidationError(
                "PBS_PARENT_CYCLE",
                "circulaire parent-verwijzing gedetecteerd",
                pbs_id,
            ))

    return errors


def _validate_functies(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    for func_id, func in project.functies.items():
        if func.pbs_id not in project.pbs_items:
            errors.append(ValidationError(
                "FUNC_PBS_FK", f"pbs_id '{func.pbs_id}' bestaat niet", func_id
            ))
    return errors


def _validate_faalwijzes(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    for fm_id, fm in project.faalwijzes.items():
        if fm.pbs_id not in project.pbs_items:
            errors.append(ValidationError(
                "FM_PBS_FK", f"pbs_id '{fm.pbs_id}' bestaat niet", fm_id
            ))
        if fm.functie_id and fm.functie_id not in project.functies:
            errors.append(ValidationError(
                "FM_FUNC_FK", f"functie_id '{fm.functie_id}' bestaat niet", fm_id
            ))
        if fm.mttf_jaar <= 0:
            errors.append(ValidationError(
                "FM_MTTF_NONPOSITIVE", f"mttf_jaar moet > 0 zijn (is {fm.mttf_jaar})", fm_id
            ))
        if fm.sigma_jaar < 0:
            errors.append(ValidationError(
                "FM_SIGMA_NEGATIVE", f"sigma_jaar mag niet negatief zijn", fm_id
            ))
        if not (0.0 <= fm.repair_quality <= 1.0):
            errors.append(ValidationError(
                "FM_REPAIR_QUALITY", f"repair_quality moet tussen 0 en 1 liggen", fm_id
            ))
        if not (0.0 <= fm.p_ongewenste_gebeurtenis <= 1.0):
            errors.append(ValidationError(
                "FM_P_OG", f"p_ongewenste_gebeurtenis moet tussen 0 en 1 liggen", fm_id
            ))
        if fm.failure_type == FailureType.RANDOM and fm.sigma_jaar > 0:
            errors.append(ValidationError(
                "FM_RANDOM_SIGMA_NONZERO",
                f"failure_type=random (exponentieel) maar sigma_jaar={fm.sigma_jaar} > 0; "
                "exponentieel faalmodel vereist sigma=0",
                fm_id,
            ))
        if fm.downtime_per_failure.value < 0:
            errors.append(ValidationError(
                "FM_DOWNTIME_NEGATIVE", f"downtime_per_failure mag niet negatief zijn", fm_id
            ))
        if fm.cost_cm_eur < 0:
            errors.append(ValidationError(
                "FM_COST_NEGATIVE", f"cost_cm_eur mag niet negatief zijn", fm_id
            ))
    return errors


def _validate_pm_tasks(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    for pm_id, pm in project.pm_tasks.items():
        if pm.fm_id not in project.faalwijzes:
            errors.append(ValidationError(
                "PM_FM_FK", f"fm_id '{pm.fm_id}' bestaat niet", pm_id
            ))
        if pm.task_group_id and pm.task_group_id not in project.task_groups:
            errors.append(ValidationError(
                "PM_TG_FK", f"task_group_id '{pm.task_group_id}' bestaat niet", pm_id
            ))
        if pm.interval_jaar <= 0:
            errors.append(ValidationError(
                "PM_INTERVAL_NONPOSITIVE", f"interval_jaar moet > 0 zijn", pm_id
            ))
        if pm.cost_eur < 0:
            errors.append(ValidationError(
                "PM_COST_NEGATIVE", f"cost_eur mag niet negatief zijn", pm_id
            ))
        if not (0.0 <= pm.unavailability_fraction <= 1.0):
            errors.append(ValidationError(
                "PM_UNAVAIL_FRACTION", f"unavailability_fraction moet tussen 0 en 1 liggen", pm_id
            ))
    return errors


def _validate_task_groups(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    for tg_id, tg in project.task_groups.items():
        if tg.interval_jaar <= 0:
            errors.append(ValidationError(
                "TG_INTERVAL_NONPOSITIVE", f"interval_jaar moet > 0 zijn", tg_id
            ))
        if tg.cost_eur < 0:
            errors.append(ValidationError(
                "TG_COST_NEGATIVE", f"cost_eur mag niet negatief zijn", tg_id
            ))
    return errors


def _validate_effect_klassen(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    for klasse_id, ek in project.effect_klassen.items():
        if ek.functie_id and ek.functie_id not in project.functies:
            errors.append(ValidationError(
                "EK_FUNC_FK",
                f"functie_id '{ek.functie_id}' bestaat niet",
                klasse_id,
            ))
    return errors


def _validate_fm_effect_links(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    for link_id, link in project.fm_effect_links.items():
        if link.fm_id not in project.faalwijzes:
            errors.append(ValidationError(
                "FMEL_FM_FK", f"fm_id '{link.fm_id}' bestaat niet", link_id
            ))
        if link.klasse_id not in project.effect_klassen:
            errors.append(ValidationError(
                "FMEL_EK_FK", f"klasse_id '{link.klasse_id}' bestaat niet", link_id
            ))
        if not (0.0 <= link.fractie <= 1.0):
            errors.append(ValidationError(
                "FMEL_FRACTIE", f"fractie moet tussen 0 en 1 liggen (is {link.fractie})", link_id
            ))
    return errors


def _validate_pm_effect_links(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    valid_pm_ids = set(project.pm_tasks.keys()) | set(project.task_groups.keys())
    for link_id, link in project.pm_effect_links.items():
        if link.pm_id not in valid_pm_ids:
            errors.append(ValidationError(
                "PMEL_PM_FK",
                f"pm_id '{link.pm_id}' bestaat niet in pm_tasks of task_groups",
                link_id,
            ))
        if link.klasse_id not in project.effect_klassen:
            errors.append(ValidationError(
                "PMEL_EK_FK", f"klasse_id '{link.klasse_id}' bestaat niet", link_id
            ))
        if not (0.0 <= link.fractie <= 1.0):
            errors.append(ValidationError(
                "PMEL_FRACTIE", f"fractie moet tussen 0 en 1 liggen (is {link.fractie})", link_id
            ))
    return errors


def _validate_config(project: "RCMProject") -> list[ValidationError]:
    errors: list[ValidationError] = []
    cfg = project.config
    if cfg.lifecycle_years <= 0:
        errors.append(ValidationError(
            "CFG_LIFECYCLE", f"lifecycle_years moet > 0 zijn (is {cfg.lifecycle_years})", "config"
        ))
    if cfg.monte_carlo_n < 100:
        errors.append(ValidationError(
            "CFG_MC_N", f"monte_carlo_n moet >= 100 zijn (is {cfg.monte_carlo_n})", "config"
        ))
    if cfg.default_mttf_multiplier <= 0:
        errors.append(ValidationError(
            "CFG_MTTF_MULT", f"default_mttf_multiplier moet > 0 zijn", "config"
        ))
    if cfg.default_sigma_fraction <= 0:
        errors.append(ValidationError(
            "CFG_SIGMA_FRAC", f"default_sigma_fraction moet > 0 zijn", "config"
        ))
    return errors


def _validate_aannamen(project: "RCMProject") -> list[ValidationError]:
    """Coherentiechecks voor aannamen (ontbrekend of tegenstrijdig)."""
    errors: list[ValidationError] = []

    # PBS: leeftijdsaanname
    for pbs_id, pbs in project.pbs_items.items():
        if pbs.library_ref and pbs.library_ref not in project.bibliotheek:
            errors.append(ValidationError(
                "BIBLIOTHEEK_REF_ONBEKEND",
                f"library_ref '{pbs.library_ref}' bestaat niet in de bibliotheek",
                pbs_id,
            ))
        if pbs.bouwjaar > 0 and not pbs.aanname_leeftijd:
            # Controleer of de aanname ergens in de hiërarchie beschikbaar is
            inherited = pbs.effective_aanname_leeftijd(project.pbs_items)
            if not inherited or inherited.startswith("[Overgenomen"):
                errors.append(ValidationError(
                    "AANNAME_LEEFTIJD_ONTBREEKT",
                    "bouwjaar is ingevuld maar aanname_leeftijd ontbreekt (geen motivatie)",
                    pbs_id,
                ))
            else:
                errors.append(ValidationError(
                    "AANNAME_LEEFTIJD_GEERFDE",
                    f"aanname_leeftijd overgenomen van parent: {inherited[:80]}",
                    pbs_id,
                ))

    # Faalwijzen: faalmodel + CM-kosten + library_ref
    for fm_id, fm in project.faalwijzes.items():
        if fm.library_ref and fm.library_ref not in project.bibliotheek:
            errors.append(ValidationError(
                "BIBLIOTHEEK_REF_ONBEKEND",
                f"library_ref '{fm.library_ref}' bestaat niet in de bibliotheek",
                fm_id,
            ))
        if not fm.aanname_faalmodel and not project.get_bibliotheek_item(fm.library_ref):
            errors.append(ValidationError(
                "AANNAME_FAALMODEL_ONTBREEKT",
                "aanname_faalmodel leeg en geen overeenkomend bibliotheekitem",
                fm_id,
            ))
        if fm.cost_cm_eur > 0 and not fm.aanname_cm_kosten:
            errors.append(ValidationError(
                "AANNAME_CM_KOSTEN_ONTBREEKT",
                f"cost_cm_eur={fm.cost_cm_eur:.0f} maar aanname_cm_kosten ontbreekt",
                fm_id,
            ))

    # PM-taken: kosten + interval
    for pm_id, pm in project.pm_tasks.items():
        if pm.library_ref and pm.library_ref not in project.bibliotheek:
            errors.append(ValidationError(
                "BIBLIOTHEEK_REF_ONBEKEND",
                f"library_ref '{pm.library_ref}' bestaat niet in de bibliotheek",
                pm_id,
            ))
        if pm.cost_eur > 0 and not pm.effective_aanname_kosten(project):
            errors.append(ValidationError(
                "AANNAME_PM_KOSTEN_ONTBREEKT",
                f"cost_eur={pm.cost_eur:.0f} maar geen kostenmotivatie (aanname_kosten leeg, "
                "cm_kosten_als_basis=False, geen bibliotheekitem)",
                pm_id,
            ))
        # Waarschuwing als PM-kosten hoger zijn dan CM-kosten zonder expliciete motivatie
        fm = project.faalwijzes.get(pm.fm_id)
        if fm and pm.cost_eur > fm.cost_cm_eur > 0 and not pm.aanname_kosten:
            errors.append(ValidationError(
                "PM_KOSTEN_HOGER_DAN_CM",
                f"PM-kosten ({pm.cost_eur:.0f}) > CM-kosten ({fm.cost_cm_eur:.0f}) "
                "zonder aanname_kosten ter motivatie",
                pm_id,
            ))

    # FM-effect links: fractie < 1 zonder motivatie
    for link_id, link in project.fm_effect_links.items():
        if link.fractie < 1.0 and not link.aanname_fractie:
            errors.append(ValidationError(
                "FRACTIE_ZONDER_MOTIVATIE",
                f"fractie={link.fractie} (< 1.0) maar aanname_fractie ontbreekt",
                link_id,
            ))

    # PM-effect links: idem
    for link_id, link in project.pm_effect_links.items():
        if link.fractie < 1.0 and not link.aanname_fractie:
            errors.append(ValidationError(
                "FRACTIE_ZONDER_MOTIVATIE",
                f"fractie={link.fractie} (< 1.0) maar aanname_fractie ontbreekt",
                link_id,
            ))

    return errors
