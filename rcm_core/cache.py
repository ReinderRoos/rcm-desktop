"""
cache.py — Hash-gebaseerde incrementele berekening.

Werking:
- Per faalwijze wordt een SHA256-hash berekend over een canonieke JSON-slice van dezelfde
  invoer als de analytische motor (zie :func:`fm_analytical_inputs_dict`).
- De hash + resultaat worden opgeslagen in een cache-bestand (<project>.rcm.cache.json).
- Bij een nieuwe run worden alleen FM's berekend waarvoor de hash is gewijzigd.
- Ongewijzigde FM's worden geladen uit de cache.
- Globale digest (``global_digest``) valideert het hele **domain model**-snapshot; zie
  :func:`load_cache_snapshot` voor het PoC-beleid bij mismatch.

Cachebestand: <project_pad>.rcm.cache.json
Structuur:
{
  "global_digest": "<sha256-hex>",
  "hashes":  { "FM-001": "<sha256>", ... },
  "results": { "FM-001": { ...FMResult.to_dict()... }, ... }
}

Voor run/impact: gebruik :func:`load_cache_snapshot`. :func:`load_cache` leest ruwe
``hashes``/``results`` van schijf (zonder digest-check), o.a. voor tests.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rcm_core.models import FMResult, RCMProject

# Handmatig verhogen wanneer analytische uitkomsten kunnen veranderen zonder wijziging aan project-JSON-vorm.
CACHE_INPUTS_VERSION = 106  # slice 52: effective_sigma via default_sigma_fraction

# Top-level projectvelden die geen motor/cache-invoer zijn (rapportage-metadata).
_DIGEST_EXCLUDED_PROJECT_KEYS = frozenset({"projectnaam", "modelleur"})


# ---------------------------------------------------------------------------
# Hash-berekening
# ---------------------------------------------------------------------------


# Versie van de FM-hash-payload (vorm van ``fm_analytical_inputs_dict``). Verhogen bij
# structurele wijziging van de slice; hoeft niet gelijk te lopen met CACHE_INPUTS_VERSION.
# FM-hash in drie stappen: (1) dict bouwen, (2) json.dumps(sort_keys=True), (3) SHA256.
FM_HASH_INPUT_SLICE_VERSION = 1


def compute_global_digest(project: "RCMProject") -> str:
    """SHA256-hex over canonieke projectinvoer plus cache-inputversie.

    Gebruikt ``RCMProject.to_dict()`` met deterministische JSON (sort_keys).
    ``projectnaam`` en ``modelleur`` zijn rapportage-metadata en worden uitgesloten.
    """
    canonical_dict = project.to_dict()
    for key in _DIGEST_EXCLUDED_PROJECT_KEYS:
        canonical_dict.pop(key, None)
    canonical = json.dumps(canonical_dict, sort_keys=True, ensure_ascii=False)
    payload = f"{canonical}|CACHE_INPUTS_VERSION={CACHE_INPUTS_VERSION}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fm_analytical_inputs_dict(project: "RCMProject", fm_id: str) -> dict | None:
    """Canonieke invoerdict voor één FM — zelfde inhoud als de parallel-worker in ``engine``.

    Gebruikt ``to_dict()``-vormen en gesorteerde sleutels/lijsten zodat
    ``json.dumps(..., sort_keys=True)`` stabiel is. Wijzigingen in **elk** veld
    dat de motor voor deze FM meeneemt (inclusief volledige ``pbs_items`` en
    ``task_groups`` zoals in de worker) invalidates de FM-hash.

    Returns ``None`` als FM of gekoppeld PBS ontbreekt (caller behandelt als affected).
    """
    fm = project.faalwijzes.get(fm_id)
    if fm is None:
        return None
    pbs = project.pbs_items.get(fm.pbs_id)
    if pbs is None:
        return None
    pm_tasks = sorted(project.get_pm_tasks_for_fm(fm_id), key=lambda t: t.pm_id)
    fm_effect_links = sorted(project.get_fm_effect_links_for_fm(fm_id), key=lambda l: l.link_id)
    pm_effect_links_list: list = []
    for pm in pm_tasks:
        pm_effect_links_list.extend(project.get_pm_effect_links_for_pm(pm.pm_id))
    pm_effect_links = sorted(pm_effect_links_list, key=lambda l: l.link_id)
    return {
        "slice": FM_HASH_INPUT_SLICE_VERSION,
        "fm": fm.to_dict(),
        "pbs": pbs.to_dict(),
        "pm_tasks": [t.to_dict() for t in pm_tasks],
        "task_groups": {k: project.task_groups[k].to_dict() for k in sorted(project.task_groups)},
        "config": project.config.to_dict(),
        "fm_effect_links": [l.to_dict() for l in fm_effect_links],
        "pm_effect_links": [l.to_dict() for l in pm_effect_links],
        "pbs_items": {k: project.pbs_items[k].to_dict() for k in sorted(project.pbs_items)},
    }


def compute_fm_hash(project: "RCMProject", fm_id: str) -> str:
    """SHA256-hex over canonieke JSON van de analytische invoer voor ``fm_id``."""
    blob = fm_analytical_inputs_dict(project, fm_id)
    if blob is None:
        return hashlib.sha256(f"missing_inputs|{fm_id}".encode("utf-8")).hexdigest()
    canonical = json.dumps(blob, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Cache persistentie
# ---------------------------------------------------------------------------

def _cache_path(project_path: Path, scenario_key: str | None = None) -> Path:
    """Pad naar FM-cache: ``.rcm.cache.json`` of ``.rcm.cache.<scenario>.json``."""
    p = Path(project_path)
    if scenario_key:
        return p.with_suffix("").with_suffix(f".rcm.cache.{scenario_key.lower()}.json")
    return p.with_suffix("").with_suffix(".rcm.cache.json")


@dataclass(frozen=True)
class CacheSnapshot:
    """Resultaat van :func:`load_cache_snapshot` voor run/impact."""

    hashes: dict[str, str]
    raw_results: dict[str, dict]
    global_layer_trusted: bool
    """False als er een cachebestand was maar ``global_digest`` ontbrak of niet matcht (PoC b)."""
    cache_file_existed: bool


def load_cache(
    project_path: str | Path,
    *,
    scenario_key: str | None = None,
) -> tuple[dict[str, str], dict[str, dict]]:
    """Laad ``hashes`` en ``results`` van schijf zonder digest-validatie (tests / low-level)."""
    path = _cache_path(Path(project_path), scenario_key)
    if not path.exists():
        return {}, {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("hashes") or {}, data.get("results") or {}


def load_cache_snapshot(
    project: "RCMProject",
    project_path: str | Path,
    *,
    scenario_key: str | None = None,
) -> CacheSnapshot:
    """Laad cache alleen als ``global_digest`` overeenkomt met ``project`` (PoC: beleid b).

    Ontbreekt het veld of wijkt het af, dan worden ``hashes`` en ``raw_results`` leeg
    teruggegeven (geen incrementeel vertrouwen in oude resultaten). Toekomstige variant
    (a) zou hier FM-hashes nog kunnen gebruiken na een globale miss — nu niet.

    Ontbrekend bestand: lege payloads, ``global_layer_trusted`` True (lege cache is ok).
    """
    path = _cache_path(Path(project_path), scenario_key)
    if not path.exists():
        return CacheSnapshot({}, {}, True, False)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    stored = data.get("global_digest")
    if not isinstance(stored, str) or not stored or stored != compute_global_digest(project):
        return CacheSnapshot({}, {}, False, True)
    return CacheSnapshot(
        data.get("hashes") or {},
        data.get("results") or {},
        True,
        True,
    )


def save_cache(
    project_path: str | Path,
    hashes: dict[str, str],
    fm_results: "dict[str, FMResult]",
    project: "RCMProject",
    *,
    scenario_key: str | None = None,
) -> None:
    """Sla hashes, resultaten en ``global_digest`` op in het cache-bestand."""
    from rcm_core.models import FMResult  # lokale import om circulaire import te vermijden
    path = _cache_path(Path(project_path), scenario_key)
    data = {
        "global_digest": compute_global_digest(project),
        "hashes": hashes,
        "results": {fm_id: r.to_dict() for fm_id, r in fm_results.items()},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Impact-analyse
# ---------------------------------------------------------------------------

def find_affected_fms(
    project: "RCMProject",
    cached_hashes: dict[str, str],
) -> list[str]:
    """Geeft de fm_id's terug waarvan de hash is gewijzigd t.o.v. de cache."""
    affected: list[str] = []
    for fm_id, fm in project.faalwijzes.items():
        pbs = project.pbs_items.get(fm.pbs_id)
        if pbs is None:
            affected.append(fm_id)
            continue
        current_hash = compute_fm_hash(project, fm_id)
        if cached_hashes.get(fm_id) != current_hash:
            affected.append(fm_id)
    return affected


def merge_results(
    fresh: "dict[str, FMResult]",
    cached_raw: dict[str, dict],
    fresh_fm_ids: list[str],
) -> "dict[str, FMResult]":
    """Voeg verse resultaten samen met gecachte resultaten.

    Gecachte resultaten worden gedeserialiseerd voor FM's die niet opnieuw berekend zijn.
    """
    from rcm_core.models import FMResult

    merged: dict[str, FMResult] = dict(fresh)
    for fm_id, raw in cached_raw.items():
        if fm_id not in fresh_fm_ids:
            merged[fm_id] = FMResult.from_dict(raw)
    return merged
