"""Portfolio-merge: submodellen naast elkaar onder fictieve top-PBS (ADR-0009)."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from rcm_core.config import RCMConfig
from rcm_core.library_distill import (
    distill_project_catalog,
    merge_catalog_to_bibliotheek,
)
from rcm_core.models import (
    BibliotheekItem,
    EffectKlasse,
    Faalwijze,
    FMEffectLink,
    Functie,
    PBSItem,
    PMEffectLink,
    PMTask,
    RCMProject,
    TaskGroup,
)
from rcm_core.portfolio_manifest import PortfolioManifest, PortfolioSourceEntry

PORTFOLIO_TOP_PBS_ID = "PBS-PORTFOLIO"
SCHAKEL_ROOT_SUFFIX = "SCHAKEL-ROOT"


@dataclass(frozen=True)
class PortfolioSource:
    """Geladen bronmodel voor merge."""

    source_id: str
    netwerkschakel_label: str
    project: RCMProject
    relative_path: str = ""


@dataclass(frozen=True)
class PortfolioMergeResult:
    project: RCMProject
    manifest: PortfolioManifest


def prefix_entity_id(netwerkschakel: str, orig_id: str) -> str:
    return f"{netwerkschakel}::{orig_id}"


def _schakel_root_id(netwerkschakel: str) -> str:
    return prefix_entity_id(netwerkschakel, SCHAKEL_ROOT_SUFFIX)


def _maybe_prefix_ref(netwerkschakel: str, ref: str) -> str:
    if not ref:
        return ""
    return prefix_entity_id(netwerkschakel, ref)


def _remap_pbs_items(
    project: RCMProject,
    netwerkschakel: str,
) -> dict[str, PBSItem]:
    schakel_root = _schakel_root_id(netwerkschakel)
    out: dict[str, PBSItem] = {
        schakel_root: PBSItem(
            pbs_id=schakel_root,
            object_naam=netwerkschakel,
            element_naam=netwerkschakel,
            bouwdeel_naam=f"Netwerkschakel {netwerkschakel}",
            parent_pbs_id=PORTFOLIO_TOP_PBS_ID,
        ),
    }
    for pbs in project.pbs_items.values():
        new_id = prefix_entity_id(netwerkschakel, pbs.pbs_id)
        parent = pbs.parent_pbs_id
        new_parent = (
            _maybe_prefix_ref(netwerkschakel, parent)
            if parent
            else schakel_root
        )
        out[new_id] = replace(
            pbs,
            pbs_id=new_id,
            parent_pbs_id=new_parent,
            library_ref=_maybe_prefix_ref(netwerkschakel, pbs.library_ref),
        )
    return out


def _remap_dict_items[T](
    items: dict[str, T],
    netwerkschakel: str,
    *,
    id_attr: str,
    remap_fields: dict[str, str] | None = None,
) -> dict[str, T]:
    out: dict[str, T] = {}
    for key, item in items.items():
        orig_id = getattr(item, id_attr)
        new_id = prefix_entity_id(netwerkschakel, orig_id)
        updates: dict[str, Any] = {id_attr: new_id}
        for field, prefix_as in (remap_fields or {}).items():
            val = getattr(item, field)
            if isinstance(val, str) and val:
                updates[field] = _maybe_prefix_ref(netwerkschakel, val)
        out[new_id] = replace(item, **updates)
    return out


def _remap_bibliotheek(
    bibliotheek: dict[str, BibliotheekItem],
    netwerkschakel: str,
) -> dict[str, BibliotheekItem]:
    out: dict[str, BibliotheekItem] = {}
    for bib_id, item in bibliotheek.items():
        new_id = prefix_entity_id(netwerkschakel, bib_id)
        out[new_id] = replace(item, bibliotheek_id=new_id)
    return out


def _remap_source_project(project: RCMProject, netwerkschakel: str) -> RCMProject:
    pbs_items = _remap_pbs_items(project, netwerkschakel)
    functies = _remap_dict_items(
        project.functies, netwerkschakel, id_attr="functie_id", remap_fields={"pbs_id": "pbs_id"}
    )
    faalwijzes = _remap_dict_items(
        project.faalwijzes,
        netwerkschakel,
        id_attr="fm_id",
        remap_fields={
            "pbs_id": "pbs_id",
            "functie_id": "functie_id",
            "library_ref": "library_ref",
        },
    )
    pm_tasks = _remap_dict_items(
        project.pm_tasks,
        netwerkschakel,
        id_attr="pm_id",
        remap_fields={"fm_id": "fm_id", "library_ref": "library_ref"},
    )
    task_groups = _remap_dict_items(
        project.task_groups,
        netwerkschakel,
        id_attr="group_id",
        remap_fields={"library_ref": "library_ref"},
    )
    effect_klassen = _remap_dict_items(
        project.effect_klassen,
        netwerkschakel,
        id_attr="klasse_id",
        remap_fields={"functie_id": "functie_id"},
    )
    fm_effect_links = _remap_dict_items(
        project.fm_effect_links,
        netwerkschakel,
        id_attr="link_id",
        remap_fields={"fm_id": "fm_id", "klasse_id": "klasse_id"},
    )
    pm_effect_links = _remap_dict_items(
        project.pm_effect_links,
        netwerkschakel,
        id_attr="link_id",
        remap_fields={"pm_id": "pm_id", "klasse_id": "klasse_id"},
    )
    bibliotheek = _remap_bibliotheek(project.bibliotheek, netwerkschakel)

    return RCMProject(
        config=deepcopy(project.config),
        projectnaam=project.projectnaam,
        modelleur=project.modelleur,
        pbs_items=pbs_items,
        functies=functies,
        faalwijzes=faalwijzes,
        pm_tasks=pm_tasks,
        task_groups=task_groups,
        effect_klassen=effect_klassen,
        fm_effect_links=fm_effect_links,
        pm_effect_links=pm_effect_links,
        bibliotheek=bibliotheek,
        import_settings=dict(project.import_settings),
    )


def _portfolio_display_config(sources: list[PortfolioSource]) -> RCMConfig:
    """Weergave-defaults: langste lifecycle, eerste modeljaar — geen submodel-overschrijving."""
    if not sources:
        return RCMConfig()
    lifecycles = [s.project.config.lifecycle_years for s in sources]
    modeljaren = [s.project.config.modeljaar for s in sources]
    base = deepcopy(sources[0].project.config)
    base.lifecycle_years = max(lifecycles)
    base.modeljaar = modeljaren[0]
    return base


def _record_id_map(
    source: PortfolioSource,
    manifest_sources: list[PortfolioSourceEntry],
    id_map: dict[str, str],
) -> None:
    net = source.netwerkschakel_label
    proj = source.project
    for fm_id in proj.faalwijzes:
        scoped = prefix_entity_id(net, fm_id)
        id_map[f"{source.source_id}::{fm_id}"] = scoped
    for pbs_id in proj.pbs_items:
        id_map[f"{source.source_id}::{pbs_id}"] = prefix_entity_id(net, pbs_id)
    manifest_sources.append(
        PortfolioSourceEntry(
            source_id=source.source_id,
            netwerkschakel_label=net,
            relative_path=source.relative_path,
            source_type="rcm_json",
            sha256="",
            mtime_ns=0,
            lifecycle_years=proj.config.lifecycle_years,
            modeljaar=proj.config.modeljaar,
            fm_count=len(proj.faalwijzes),
        )
    )


def merge_portfolio_sources(
    sources: list[PortfolioSource],
    *,
    portfolio_name: str = "",
    scan_root_label: str = "",
) -> PortfolioMergeResult:
    """Voeg bronmodellen samen onder fictieve top-PBS; geen stille FM-dedup."""
    if not sources:
        raise ValueError("Minimaal één bron vereist voor portfolio-merge")

    top_pbs = PBSItem(
        pbs_id=PORTFOLIO_TOP_PBS_ID,
        object_naam="Portfolio",
        element_naam="Portfolio",
        bouwdeel_naam="Samengesteld portfolio",
        parent_pbs_id=None,
    )

    merged = RCMProject(config=_portfolio_display_config(sources))
    merged.pbs_items[PORTFOLIO_TOP_PBS_ID] = top_pbs
    if portfolio_name:
        merged.projectnaam = portfolio_name

    manifest_sources: list[PortfolioSourceEntry] = []
    id_map: dict[str, str] = {}
    catalog = []

    for source in sources:
        remapped = _remap_source_project(source.project, source.netwerkschakel_label)
        merged.pbs_items.update(remapped.pbs_items)
        merged.functies.update(remapped.functies)
        merged.faalwijzes.update(remapped.faalwijzes)
        merged.pm_tasks.update(remapped.pm_tasks)
        merged.task_groups.update(remapped.task_groups)
        merged.effect_klassen.update(remapped.effect_klassen)
        merged.fm_effect_links.update(remapped.fm_effect_links)
        merged.pm_effect_links.update(remapped.pm_effect_links)
        merged.bibliotheek.update(remapped.bibliotheek)

        _record_id_map(source, manifest_sources, id_map)
        catalog.extend(
            distill_project_catalog(
                source.project,
                source_id=source.source_id,
                netwerkschakel=source.netwerkschakel_label,
                relative_path=source.relative_path,
            )
        )

    merged.bibliotheek = merge_catalog_to_bibliotheek(
        catalog, existing=merged.bibliotheek
    )

    manifest = PortfolioManifest(
        scan_root_label=scan_root_label,
        sources=manifest_sources,
        id_map=id_map,
    )
    merged.import_settings["portfolio_manifest"] = manifest.to_dict()

    return PortfolioMergeResult(project=merged, manifest=manifest)


def portfolio_manifest_sidecar_path(portfolio_path: Path) -> Path:
    """Sidecar naast ``*.rcm.json`` (ADR-0009)."""
    name = portfolio_path.name
    if name.endswith(".rcm.json"):
        base = name[: -len(".rcm.json")]
    else:
        base = portfolio_path.stem
    return portfolio_path.parent / f"{base}.portfolio_manifest.json"


def save_portfolio_manifest_sidecar(
    manifest: PortfolioManifest,
    portfolio_path: Path,
) -> Path:
    path = portfolio_manifest_sidecar_path(portfolio_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(manifest.to_dict(), fh, indent=2, ensure_ascii=False)
    return path


def load_portfolio_manifest_sidecar(portfolio_path: Path) -> PortfolioManifest | None:
    path = portfolio_manifest_sidecar_path(portfolio_path)
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return PortfolioManifest.from_dict(data)
