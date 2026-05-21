from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject


@dataclass(frozen=True)
class TopFaalwijze:
    fm_id: str
    faalwijze_omschrijving: str


@dataclass(frozen=True)
class ProjectPreview:
    pbs_items: int
    functies: int
    faalwijzes: int
    pm_tasks: int
    top_faalwijzes: list[TopFaalwijze]


def build(project: RCMProject) -> ProjectPreview:
    top_faalwijzes = [
        TopFaalwijze(
            fm_id=fm.fm_id,
            faalwijze_omschrijving=fm.faalwijze_omschrijving,
        )
        for fm in list(project.faalwijzes.values())[:5]
    ]
    return ProjectPreview(
        pbs_items=len(project.pbs_items),
        functies=len(project.functies),
        faalwijzes=len(project.faalwijzes),
        pm_tasks=len(project.pm_tasks),
        top_faalwijzes=top_faalwijzes,
    )
