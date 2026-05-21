"""
models.py — Domeinmodel voor het RCM-project.

Dataklassen voor de fysiek-functionele decompositie (PBS), faalwijzen,
preventief onderhoud, taakgroepen en berekeningsresultaten.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from rcm_core.import_settings_contract import normalize_import_settings
from rcm_core.units import TimeDuration, TimeUnit
from rcm_core.config import RCMConfig


# ---------------------------------------------------------------------------
# Enumeraties
# ---------------------------------------------------------------------------

class FailureType(str, Enum):
    RANDOM = "random"  # willekeurig falen: exponentiaalverdeling, constante hazard
    AGING  = "aging"   # verouderingsfalen: normaalverdeling rond MTTF


class TaskType(str, Enum):
    SVO = "SVO"  # Standard Verzorgend Onderhoud — verplicht, niet uit te zetten
    IN  = "IN"   # Inspectie — detecteert niet-merkbaar falen
    TST = "TST"  # Test — toestandsafhankelijk onderhoud (TAO)
    REV = "REV"  # Revisie/Vervanging — leidt doorgaans tot niet-beschikbaarheid


# ---------------------------------------------------------------------------
# Bibliotheek — herbruikbare referentie-aannamen
# ---------------------------------------------------------------------------

@dataclass
class BibliotheekItem:
    """Herbruikbare referentie-aanname (bibliotheekgegeven).

    Categorieën: "faalmodel" | "cm_kosten" | "pm_kosten" |
                 "leeftijd" | "multipliciteit" | "effectklasse"
    """
    bibliotheek_id: str       # bijv. "FC02", "FE13", "BIB-001"
    categorie: str            # zie categorieën hierboven
    omschrijving: str         # mensleesbare beschrijving
    waarde: str               # de aangenomen waarde (bijv. "MTTF=125 jr, OLD=100 jr")
    bron: str = ""            # bronverwijzing (rapport, norm, inspectie)
    toelichting: str = ""     # verdere toelichting / voorbehouden

    def to_dict(self) -> dict:
        return {
            "bibliotheek_id": self.bibliotheek_id,
            "categorie": self.categorie,
            "omschrijving": self.omschrijving,
            "waarde": self.waarde,
            "bron": self.bron,
            "toelichting": self.toelichting,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BibliotheekItem":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Product Breakdown Structure (PBS) — NEN 2769: Object/Element/Bouwdeel
# ---------------------------------------------------------------------------

@dataclass
class PBSItem:
    pbs_id: str
    object_naam: str
    element_naam: str
    bouwdeel_naam: str
    component_naam: str = ""
    multiplicity: int = 1               # aantal identieke exemplaren (opbossen)
    ontwerpleeftijd_jaar: float = 0.0   # OLD: ontwerpleeftijd in jaren
    bouwjaar: int = 0                   # jaar van bouw/installatie
    library_ref: str = ""
    notes: str = ""
    aanname_leeftijd: str = ""          # bron/motivatie voor bouwjaar (bijv. "DISK-inspectie 2022")
    aanname_multipliciteit: str = ""    # motivatie multipliciteit (bijv. "2x achterloops + 2 onderloops = 4")

    parent_pbs_id: Optional[str] = None  # FK → PBSItem (bovenliggende laag, optioneel)

    def current_age(self, modeljaar: int) -> float:
        """Leeftijd op modeljaar = modeljaar − bouwjaar.
        Nooit handmatig de leeftijd ophogen — pas modeljaar aan in Config."""
        if self.bouwjaar == 0:
            return 0.0
        return float(modeljaar - self.bouwjaar)

    def effective_bouwjaar(self, all_pbs: dict[str, "PBSItem"]) -> int:
        """Eigen bouwjaar als > 0, anders recursief overgenomen van parent."""
        if self.bouwjaar > 0:
            return self.bouwjaar
        if self.parent_pbs_id and self.parent_pbs_id in all_pbs:
            return all_pbs[self.parent_pbs_id].effective_bouwjaar(all_pbs)
        return 0

    def effective_multiplicity(self, all_pbs: dict[str, "PBSItem"]) -> int:
        """Product van eigen multiplicity × alle voorouders (cascaderende multipliciteit)."""
        if self.parent_pbs_id and self.parent_pbs_id in all_pbs:
            return self.multiplicity * all_pbs[self.parent_pbs_id].effective_multiplicity(all_pbs)
        return self.multiplicity

    def effective_aanname_leeftijd(self, all_pbs: dict[str, "PBSItem"]) -> str:
        """Erft leeftijdsaanname van dichtstbijzijnde parent met ingevulde aanname."""
        if self.aanname_leeftijd:
            return self.aanname_leeftijd
        if self.parent_pbs_id and self.parent_pbs_id in all_pbs:
            return all_pbs[self.parent_pbs_id].effective_aanname_leeftijd(all_pbs)
        eff = self.bouwjaar
        return f"[Overgenomen van hiërarchie: bouwjaar={eff}]" if eff else ""

    def mttf_from_old(self, config: RCMConfig) -> float:
        """MTTF = default_mttf_multiplier × ontwerpleeftijd."""
        return config.default_mttf_multiplier * self.ontwerpleeftijd_jaar

    def to_dict(self) -> dict:
        return {
            "pbs_id": self.pbs_id,
            "object_naam": self.object_naam,
            "element_naam": self.element_naam,
            "bouwdeel_naam": self.bouwdeel_naam,
            "component_naam": self.component_naam,
            "multiplicity": self.multiplicity,
            "ontwerpleeftijd_jaar": self.ontwerpleeftijd_jaar,
            "bouwjaar": self.bouwjaar,
            "parent_pbs_id": self.parent_pbs_id,
            "library_ref": self.library_ref,
            "notes": self.notes,
            "aanname_leeftijd": self.aanname_leeftijd,
            "aanname_multipliciteit": self.aanname_multipliciteit,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PBSItem":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Functies
# ---------------------------------------------------------------------------

@dataclass
class Functie:
    functie_id: str
    pbs_id: str                        # FK → PBSItem
    functie_omschrijving: str
    functioneel_gevolg: str = ""       # gevolg als functie uitvalt
    is_evident: bool = True            # is functioneel falen direct merkbaar?
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "functie_id": self.functie_id,
            "pbs_id": self.pbs_id,
            "functie_omschrijving": self.functie_omschrijving,
            "functioneel_gevolg": self.functioneel_gevolg,
            "is_evident": self.is_evident,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Functie":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Faalwijzen
# ---------------------------------------------------------------------------

@dataclass
class Faalwijze:
    fm_id: str
    pbs_id: str                         # FK → PBSItem
    functie_id: str                     # FK → Functie
    faalwijze_omschrijving: str
    eindgevolg: str = ""                # eindsysteemgevolg bij falen
    failure_type: FailureType = FailureType.RANDOM
    mttf_jaar: float = 0.0              # Mean Time To Failure in jaren
    sigma_jaar: float = 0.0             # standaarddeviatie; 0 → 0,15 × MTTF
    repair_quality: float = 1.0         # 0=as-good-as-old, 1=as-good-as-new
    is_evident: bool = True             # False = niet-merkbaar falen
    p_ongewenste_gebeurtenis: float = 1.0  # fractie dat falen tot ongewenste gebeurtenis leidt
    downtime_per_failure: TimeDuration = field(
        default_factory=lambda: TimeDuration(0.0, TimeUnit.HOURS)
    )
    cost_cm_eur: float = 0.0            # kosten correctief onderhoud per faling
    library_ref: str = ""
    notes: str = ""
    aanname_faalmodel: str = ""         # bron MTTF/sigma (bijv. "R17 stalen damwanden, MTTF=125jr")
    aanname_cm_kosten: str = ""         # motivatie CM-kosten (bijv. "lokaal herstel 30 keuro, 1 maand")
    aanname_downtime: str = ""          # motivatie downtime_per_failure waarde (bijv. "2 werkdagen: vervanging + kraanwachttijd")
    aanname_effectklasse: str = ""      # motivatie effectklasstoekenning (bijv. "niet merkbaar → VGM-5")

    @property
    def effective_sigma(self) -> float:
        """Gebruik opgegeven sigma; bij 0 de standaard 15% van MTTF."""
        if self.sigma_jaar > 0:
            return self.sigma_jaar
        return 0.15 * self.mttf_jaar

    def effective_aanname_faalmodel(self, project: "RCMProject") -> str:
        """Retourneert de faalmodel-aanname; valt terug op bibliotheekitem als aanname leeg is."""
        if self.aanname_faalmodel:
            return self.aanname_faalmodel
        item = project.get_bibliotheek_item(self.library_ref)
        if item and item.categorie == "faalmodel":
            return f"[Bibliotheek {self.library_ref}]: {item.waarde} — {item.bron}"
        return ""

    def to_dict(self) -> dict:
        return {
            "fm_id": self.fm_id,
            "pbs_id": self.pbs_id,
            "functie_id": self.functie_id,
            "faalwijze_omschrijving": self.faalwijze_omschrijving,
            "eindgevolg": self.eindgevolg,
            "failure_type": self.failure_type.value,
            "mttf_jaar": self.mttf_jaar,
            "sigma_jaar": self.sigma_jaar,
            "repair_quality": self.repair_quality,
            "is_evident": self.is_evident,
            "p_ongewenste_gebeurtenis": self.p_ongewenste_gebeurtenis,
            "downtime_per_failure": self.downtime_per_failure.to_dict(),
            "cost_cm_eur": self.cost_cm_eur,
            "library_ref": self.library_ref,
            "notes": self.notes,
            "aanname_faalmodel": self.aanname_faalmodel,
            "aanname_cm_kosten": self.aanname_cm_kosten,
            "aanname_downtime": self.aanname_downtime,
            "aanname_effectklasse": self.aanname_effectklasse,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Faalwijze":
        d = dict(d)
        if "failure_type" in d:
            d["failure_type"] = FailureType(d["failure_type"])
        if "downtime_per_failure" in d and isinstance(d["downtime_per_failure"], dict):
            d["downtime_per_failure"] = TimeDuration.from_dict(d["downtime_per_failure"])
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Preventief Onderhoud
# ---------------------------------------------------------------------------

@dataclass
class PMTask:
    pm_id: str
    fm_id: str                          # FK → Faalwijze
    taak_type: TaskType
    taak_omschrijving: str = ""
    interval_jaar: float = 1.0
    duration: TimeDuration = field(
        default_factory=lambda: TimeDuration(0.0, TimeUnit.HOURS)
    )
    cost_eur: float = 0.0
    effectiveness: float = 1.0          # fractie waarmee P(falen) wordt gereduceerd
    causes_unavailability: bool = False  # leidt deze taak tot niet-beschikbaarheid?
    unavailability_fraction: float = 0.0  # fractie van taakvoltooiingstijd niet-beschikbaar
    task_group_id: Optional[str] = None  # FK → TaskGroup (kosten éénmalig)
    library_ref: str = ""
    notes: str = ""
    aanname_kosten: str = ""            # motivatie PM-kosten
    aanname_interval: str = ""          # motivatie interval (bijv. "NEN-3140 vereist 1x/5jaar")
    cm_kosten_als_basis: bool = False   # True → effective_aanname_kosten erft van parent FM
    is_wettelijk_verplicht: bool = False  # wettelijk verplicht onderhoud (WET-laag in LCC/LTAP)
    aging_effect_pct: float = 0.0       # REV: effect op veroudering (0–100); default 100 bij REV in from_dict

    def effective_aanname_kosten(self, project: "RCMProject") -> str:
        """Retourneert de kostenaanname; erft CM-aanname van parent FM indien cm_kosten_als_basis."""
        if self.aanname_kosten:
            return self.aanname_kosten
        if self.cm_kosten_als_basis:
            fm = project.faalwijzes.get(self.fm_id)
            if fm and fm.aanname_cm_kosten:
                return f"[Basis CM-kosten {self.fm_id}]: {fm.aanname_cm_kosten}"
        item = project.get_bibliotheek_item(self.library_ref)
        if item and item.categorie in ("pm_kosten", "cm_kosten"):
            return f"[Bibliotheek {self.library_ref}]: {item.waarde}"
        return ""

    def to_dict(self) -> dict:
        return {
            "pm_id": self.pm_id,
            "fm_id": self.fm_id,
            "taak_type": self.taak_type.value,
            "taak_omschrijving": self.taak_omschrijving,
            "interval_jaar": self.interval_jaar,
            "duration": self.duration.to_dict(),
            "cost_eur": self.cost_eur,
            "effectiveness": self.effectiveness,
            "causes_unavailability": self.causes_unavailability,
            "unavailability_fraction": self.unavailability_fraction,
            "task_group_id": self.task_group_id,
            "library_ref": self.library_ref,
            "notes": self.notes,
            "aanname_kosten": self.aanname_kosten,
            "aanname_interval": self.aanname_interval,
            "cm_kosten_als_basis": self.cm_kosten_als_basis,
            "is_wettelijk_verplicht": self.is_wettelijk_verplicht,
            "aging_effect_pct": self.aging_effect_pct,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PMTask":
        d = dict(d)
        if "taak_type" in d:
            d["taak_type"] = TaskType(d["taak_type"])
        if "duration" in d and isinstance(d["duration"], dict):
            d["duration"] = TimeDuration.from_dict(d["duration"])
        if "aging_effect_pct" not in d:
            tt = d.get("taak_type")
            if tt == TaskType.REV or tt == TaskType.REV.value or tt == "REV":
                d["aging_effect_pct"] = 100.0
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Taakgroepen — bundelen meerdere PM-taken; kosten éénmalig
# ---------------------------------------------------------------------------

@dataclass
class TaskGroup:
    group_id: str
    omschrijving: str
    taak_type: TaskType
    interval_jaar: float
    duration: TimeDuration = field(
        default_factory=lambda: TimeDuration(0.0, TimeUnit.HOURS)
    )
    cost_eur: float = 0.0
    causes_unavailability: bool = False
    unavailability_fraction: float = 0.0
    library_ref: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "group_id": self.group_id,
            "omschrijving": self.omschrijving,
            "taak_type": self.taak_type.value,
            "interval_jaar": self.interval_jaar,
            "duration": self.duration.to_dict(),
            "cost_eur": self.cost_eur,
            "causes_unavailability": self.causes_unavailability,
            "unavailability_fraction": self.unavailability_fraction,
            "library_ref": self.library_ref,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TaskGroup":
        d = dict(d)
        if "taak_type" in d:
            d["taak_type"] = TaskType(d["taak_type"])
        if "duration" in d and isinstance(d["duration"], dict):
            d["duration"] = TimeDuration.from_dict(d["duration"])
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Effectklassen — kwalitatieve systeemgevolgen gekoppeld aan functies
# ---------------------------------------------------------------------------

@dataclass
class EffectKlasse:
    """Beschrijft een degradatiemodus op systeemniveau, gekoppeld aan een functie.

    Voorbeelden: "Volledig uitval verpompen", "Gereduceerde pompcapaciteit",
    "Veiligheidsrisico RI&E-klasse II".
    De ernst is kwalitatief beschreven; de fractie waarmee een FM of PM-taak
    tot dit gevolg leidt staat op de koppeling (FMEffectLink / PMEffectLink).
    """
    klasse_id: str
    omschrijving: str
    functie_id: str            # FK → Functie
    categorie: str = ""        # bijv. "beschikbaarheid", "veiligheid", "RI&E-I"
    notes: str = ""
    cost_gevolg_eur: float = 0.0        # kosten gevolgschade per faalgebeurtenis (euro)
    aanname_gevolg_kosten: str = ""     # motivatie gevolgschadekosten

    def to_dict(self) -> dict:
        return {
            "klasse_id": self.klasse_id,
            "omschrijving": self.omschrijving,
            "functie_id": self.functie_id,
            "categorie": self.categorie,
            "notes": self.notes,
            "cost_gevolg_eur": self.cost_gevolg_eur,
            "aanname_gevolg_kosten": self.aanname_gevolg_kosten,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EffectKlasse":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class FMEffectLink:
    """Koppeling tussen een faalwijze en een effectklasse.

    fractie: P(dit gevolg | falen treedt op) — onafhankelijke parameter, 0–1.
    Een faalwijze kan aan meerdere effectklassen bijdragen.
    """
    link_id: str
    fm_id: str          # FK → Faalwijze
    klasse_id: str      # FK → EffectKlasse
    fractie: float = 1.0
    aanname_fractie: str = ""  # motivatie fractie (bijv. "RF=0.01 RWS-richtlijn", "redundantie 2-van-4")

    def to_dict(self) -> dict:
        return {
            "link_id": self.link_id,
            "fm_id": self.fm_id,
            "klasse_id": self.klasse_id,
            "fractie": self.fractie,
            "aanname_fractie": self.aanname_fractie,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FMEffectLink":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class PMEffectLink:
    """Koppeling tussen een PM-taak en een effectklasse.

    fractie: welk deel van de taakvoltooiingstijd dit systeemgevolg optreedt, 0–1.
    Een PM-taak kan aan meerdere effectklassen bijdragen.
    """
    link_id: str
    pm_id: str          # FK → PMTask (of group_id → TaskGroup)
    klasse_id: str      # FK → EffectKlasse
    fractie: float = 1.0
    aanname_fractie: str = ""  # motivatie fractie

    def to_dict(self) -> dict:
        return {
            "link_id": self.link_id,
            "pm_id": self.pm_id,
            "klasse_id": self.klasse_id,
            "fractie": self.fractie,
            "aanname_fractie": self.aanname_fractie,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PMEffectLink":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Resultaatklassen (geschreven door engine/simulation)
# ---------------------------------------------------------------------------

@dataclass
class FMHorizonProfile:
    """Jaarlijkse CM/nb-reeksen per horizonbucket (NMF)."""

    cor_eur: list[float]
    cor_downtime_hr: list[float]
    hidden_nb_hr: list[float]

    def to_dict(self) -> dict:
        return {
            "cor_eur": list(self.cor_eur),
            "cor_downtime_hr": list(self.cor_downtime_hr),
            "hidden_nb_hr": list(self.hidden_nb_hr),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FMHorizonProfile":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class FMResult:
    fm_id: str
    pbs_id: str
    p_failure_lifecycle: float          # P(minstens één faling in lifecycle)
    expected_failures: float            # verwacht aantal falingen in lifecycle
    expected_raw_downtime_hr: float     # reparatietijd × verwacht aantal falingen
    expected_detection_delay_hr: float  # extra downtime door niet-merkbaar falen
    expected_total_downtime_hr: float   # som: raw + detection
    expected_pm_downtime_hr: float      # downtime door PM-taken
    expected_cm_cost_eur: float         # CM-kosten × verwacht aantal falingen
    pm_cost_eur: float                  # totale PM-kosten over lifecycle
    total_cost_eur: float               # CM + PM
    risk_contribution: float            # expected_failures × p_ongewenste_gebeurtenis
    effect_bijdragen: dict[str, float] = field(default_factory=dict)
    # klasse_id → expected_failures × fractie (per FMEffectLink)
    horizon_profile: FMHorizonProfile | None = None
    effect_bijdragen_per_jaar: dict[str, list[float]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        out = {
            "fm_id": self.fm_id,
            "pbs_id": self.pbs_id,
            "p_failure_lifecycle": self.p_failure_lifecycle,
            "expected_failures": self.expected_failures,
            "expected_raw_downtime_hr": self.expected_raw_downtime_hr,
            "expected_detection_delay_hr": self.expected_detection_delay_hr,
            "expected_total_downtime_hr": self.expected_total_downtime_hr,
            "expected_pm_downtime_hr": self.expected_pm_downtime_hr,
            "expected_cm_cost_eur": self.expected_cm_cost_eur,
            "pm_cost_eur": self.pm_cost_eur,
            "total_cost_eur": self.total_cost_eur,
            "risk_contribution": self.risk_contribution,
            "effect_bijdragen": self.effect_bijdragen,
            "effect_bijdragen_per_jaar": self.effect_bijdragen_per_jaar,
        }
        if self.horizon_profile is not None:
            out["horizon_profile"] = self.horizon_profile.to_dict()
        return out

    @classmethod
    def from_dict(cls, d: dict) -> "FMResult":
        data = dict(d)
        raw_hp = data.pop("horizon_profile", None)
        horizon_profile = (
            FMHorizonProfile.from_dict(raw_hp) if isinstance(raw_hp, dict) else raw_hp
        )
        known = {f for f in cls.__dataclass_fields__}
        return cls(
            **{k: v for k, v in data.items() if k in known},
            horizon_profile=horizon_profile,
        )


@dataclass
class PBSResult:
    pbs_id: str
    bouwdeel_naam: str
    total_expected_failures: float
    total_downtime_hr: float            # CM + PM downtime
    total_cm_cost_eur: float
    total_pm_cost_eur: float
    total_cost_eur: float
    unavailability_pct: float           # total_downtime / (lifecycle × 8760) × 100
    total_risk_contribution: float
    fm_results: list[FMResult] = field(default_factory=list)
    effect_bijdragen: dict[str, float] = field(default_factory=dict)
    # klasse_id → som van alle FM- en PM-effectbijdragen voor dit PBS-item

    def to_dict(self) -> dict:
        return {
            "pbs_id": self.pbs_id,
            "bouwdeel_naam": self.bouwdeel_naam,
            "total_expected_failures": self.total_expected_failures,
            "total_downtime_hr": self.total_downtime_hr,
            "total_cm_cost_eur": self.total_cm_cost_eur,
            "total_pm_cost_eur": self.total_pm_cost_eur,
            "total_cost_eur": self.total_cost_eur,
            "unavailability_pct": self.unavailability_pct,
            "total_risk_contribution": self.total_risk_contribution,
            "fm_results": [r.to_dict() for r in self.fm_results],
            "effect_bijdragen": self.effect_bijdragen,
        }


# ---------------------------------------------------------------------------
# RCMProject — toplevelcontainer
# ---------------------------------------------------------------------------

@dataclass
class RCMProject:
    config: RCMConfig = field(default_factory=RCMConfig)
    pbs_items: dict[str, PBSItem] = field(default_factory=dict)
    functies: dict[str, Functie] = field(default_factory=dict)
    faalwijzes: dict[str, Faalwijze] = field(default_factory=dict)
    pm_tasks: dict[str, PMTask] = field(default_factory=dict)
    task_groups: dict[str, TaskGroup] = field(default_factory=dict)
    effect_klassen: dict[str, EffectKlasse] = field(default_factory=dict)
    fm_effect_links: dict[str, FMEffectLink] = field(default_factory=dict)
    pm_effect_links: dict[str, PMEffectLink] = field(default_factory=dict)
    bibliotheek: dict[str, BibliotheekItem] = field(default_factory=dict)
    import_settings: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Opzoekhelpers
    # ------------------------------------------------------------------

    def get_faalwijzes_for_pbs(self, pbs_id: str) -> list[Faalwijze]:
        return [fm for fm in self.faalwijzes.values() if fm.pbs_id == pbs_id]

    def get_pm_tasks_for_fm(self, fm_id: str) -> list[PMTask]:
        return [t for t in self.pm_tasks.values() if t.fm_id == fm_id]

    def get_fm_effect_links_for_fm(self, fm_id: str) -> list[FMEffectLink]:
        return [l for l in self.fm_effect_links.values() if l.fm_id == fm_id]

    def get_pm_effect_links_for_pm(self, pm_id: str) -> list[PMEffectLink]:
        return [l for l in self.pm_effect_links.values() if l.pm_id == pm_id]

    def get_bibliotheek_item(self, ref: str) -> Optional[BibliotheekItem]:
        """Geeft het bibliotheekitem met het opgegeven ID, of None."""
        return self.bibliotheek.get(ref) if ref else None

    # ------------------------------------------------------------------
    # Bibliotheek — opslaan vanuit model-item
    # ------------------------------------------------------------------

    def sla_op_als_bibliotheek(
        self,
        entiteit_id: str,
        bibliotheek_id: str,
        omschrijving: str,
        overschrijf: bool = False,
    ) -> list[BibliotheekItem]:
        """Sla de aannamen van een model-item op als bibliotheekitem(s).

        Zoekt in volgorde: Faalwijze → PMTask → PBSItem → EffectKlasse.
        Bij een Faalwijze worden twee items aangemaakt (suffix -FM en -CM)
        tenzij één van de aannamen leeg is.

        Retourneert de lijst van aangemaakte/bijgewerkte BibliotheekItems.
        Gooit ValueError als bibliotheek_id al bestaat én overschrijf=False.
        """
        if not overschrijf and bibliotheek_id in self.bibliotheek:
            raise ValueError(
                f"Bibliotheekitem '{bibliotheek_id}' bestaat al. "
                "Gebruik overschrijf=True om het te overschrijven."
            )

        items: list[BibliotheekItem] = []

        if entiteit_id in self.faalwijzes:
            fm = self.faalwijzes[entiteit_id]
            # Faalmodel-item
            if fm.aanname_faalmodel:
                fm_id_bib = f"{bibliotheek_id}-FM"
                if not overschrijf and fm_id_bib in self.bibliotheek:
                    raise ValueError(
                        f"Bibliotheekitem '{fm_id_bib}' bestaat al. "
                        "Gebruik overschrijf=True."
                    )
                item_fm = BibliotheekItem(
                    bibliotheek_id=fm_id_bib,
                    categorie="faalmodel",
                    omschrijving=omschrijving,
                    waarde=f"MTTF={fm.mttf_jaar:.1f} jr, σ={fm.effective_sigma:.1f} jr",
                    bron=fm.aanname_faalmodel,
                    toelichting=fm.notes,
                )
                self.bibliotheek[fm_id_bib] = item_fm
                items.append(item_fm)
            # CM-kosten-item
            if fm.aanname_cm_kosten:
                cm_id_bib = f"{bibliotheek_id}-CM"
                if not overschrijf and cm_id_bib in self.bibliotheek:
                    raise ValueError(
                        f"Bibliotheekitem '{cm_id_bib}' bestaat al. "
                        "Gebruik overschrijf=True."
                    )
                item_cm = BibliotheekItem(
                    bibliotheek_id=cm_id_bib,
                    categorie="cm_kosten",
                    omschrijving=omschrijving,
                    waarde=f"€{fm.cost_cm_eur:,.0f}",
                    bron=fm.aanname_cm_kosten,
                    toelichting=fm.notes,
                )
                self.bibliotheek[cm_id_bib] = item_cm
                items.append(item_cm)
            # Als beide aannamen leeg: één enkel item zonder suffix
            if not items:
                item = BibliotheekItem(
                    bibliotheek_id=bibliotheek_id,
                    categorie="faalmodel",
                    omschrijving=omschrijving,
                    waarde=f"MTTF={fm.mttf_jaar:.1f} jr, σ={fm.effective_sigma:.1f} jr",
                    bron="",
                    toelichting=fm.notes,
                )
                self.bibliotheek[bibliotheek_id] = item
                items.append(item)

        elif entiteit_id in self.pm_tasks:
            pm = self.pm_tasks[entiteit_id]
            item = BibliotheekItem(
                bibliotheek_id=bibliotheek_id,
                categorie="pm_kosten",
                omschrijving=omschrijving,
                waarde=f"€{pm.cost_eur:,.0f}, interval={pm.interval_jaar:.1f} jr",
                bron=pm.aanname_kosten or pm.effective_aanname_kosten(self),
                toelichting=f"interval motivatie: {pm.aanname_interval}" if pm.aanname_interval else pm.notes,
            )
            self.bibliotheek[bibliotheek_id] = item
            items.append(item)

        elif entiteit_id in self.pbs_items:
            pbs = self.pbs_items[entiteit_id]
            # Leeftijdsitem
            item_l = BibliotheekItem(
                bibliotheek_id=bibliotheek_id,
                categorie="leeftijd",
                omschrijving=omschrijving,
                waarde=f"bouwjaar={pbs.bouwjaar}, OLD={pbs.ontwerpleeftijd_jaar:.0f} jr",
                bron=pbs.aanname_leeftijd or pbs.effective_aanname_leeftijd(self.pbs_items),
                toelichting=pbs.notes,
            )
            self.bibliotheek[bibliotheek_id] = item_l
            items.append(item_l)
            # Multipliciteitsitem (alleen als afwijkend van 1 of aanname aanwezig)
            if pbs.multiplicity != 1 or pbs.aanname_multipliciteit:
                mul_id = f"{bibliotheek_id}-MUL"
                if not overschrijf and mul_id in self.bibliotheek:
                    raise ValueError(
                        f"Bibliotheekitem '{mul_id}' bestaat al. "
                        "Gebruik overschrijf=True."
                    )
                item_m = BibliotheekItem(
                    bibliotheek_id=mul_id,
                    categorie="multipliciteit",
                    omschrijving=omschrijving,
                    waarde=f"n={pbs.multiplicity}",
                    bron=pbs.aanname_multipliciteit,
                    toelichting=pbs.notes,
                )
                self.bibliotheek[mul_id] = item_m
                items.append(item_m)

        elif entiteit_id in self.effect_klassen:
            ek = self.effect_klassen[entiteit_id]
            item = BibliotheekItem(
                bibliotheek_id=bibliotheek_id,
                categorie="effectklasse",
                omschrijving=omschrijving,
                waarde=f"{ek.omschrijving}; gevolgkosten=€{ek.cost_gevolg_eur:,.0f}",
                bron=ek.aanname_gevolg_kosten,
                toelichting=ek.notes,
            )
            self.bibliotheek[bibliotheek_id] = item
            items.append(item)

        else:
            raise ValueError(
                f"Entiteit '{entiteit_id}' niet gevonden in faalwijzes, "
                "pm_tasks, pbs_items of effect_klassen."
            )

        return items

    # ------------------------------------------------------------------
    # Serialisatie
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        out: dict[str, Any] = {
            "config": self.config.to_dict(),
            "pbs_items": {k: v.to_dict() for k, v in self.pbs_items.items()},
            "functies": {k: v.to_dict() for k, v in self.functies.items()},
            "faalwijzes": {k: v.to_dict() for k, v in self.faalwijzes.items()},
            "pm_tasks": {k: v.to_dict() for k, v in self.pm_tasks.items()},
            "task_groups": {k: v.to_dict() for k, v in self.task_groups.items()},
            "effect_klassen": {k: v.to_dict() for k, v in self.effect_klassen.items()},
            "fm_effect_links": {k: v.to_dict() for k, v in self.fm_effect_links.items()},
            "pm_effect_links": {k: v.to_dict() for k, v in self.pm_effect_links.items()},
            "bibliotheek": {k: v.to_dict() for k, v in self.bibliotheek.items()},
        }
        if self.import_settings:
            normalized = normalize_import_settings(self.import_settings)
            if len(normalized) > 1:
                out["import_settings"] = normalized
        return out

    @classmethod
    def from_dict(cls, d: dict) -> "RCMProject":
        config = RCMConfig.from_dict(d.get("config", {}))
        pbs_items = {k: PBSItem.from_dict(v) for k, v in d.get("pbs_items", {}).items()}
        functies = {k: Functie.from_dict(v) for k, v in d.get("functies", {}).items()}
        faalwijzes = {k: Faalwijze.from_dict(v) for k, v in d.get("faalwijzes", {}).items()}
        pm_tasks = {k: PMTask.from_dict(v) for k, v in d.get("pm_tasks", {}).items()}
        task_groups = {k: TaskGroup.from_dict(v) for k, v in d.get("task_groups", {}).items()}
        effect_klassen = {
            k: EffectKlasse.from_dict(v) for k, v in d.get("effect_klassen", {}).items()
        }
        fm_effect_links = {
            k: FMEffectLink.from_dict(v) for k, v in d.get("fm_effect_links", {}).items()
        }
        pm_effect_links = {
            k: PMEffectLink.from_dict(v) for k, v in d.get("pm_effect_links", {}).items()
        }
        bibliotheek = {
            k: BibliotheekItem.from_dict(v) for k, v in d.get("bibliotheek", {}).items()
        }
        raw_import = d.get("import_settings")
        import_settings = (
            normalize_import_settings(raw_import) if raw_import is not None else {}
        )
        return cls(
            config=config,
            pbs_items=pbs_items,
            functies=functies,
            faalwijzes=faalwijzes,
            pm_tasks=pm_tasks,
            task_groups=task_groups,
            effect_klassen=effect_klassen,
            fm_effect_links=fm_effect_links,
            pm_effect_links=pm_effect_links,
            bibliotheek=bibliotheek,
            import_settings=import_settings,
        )
