"""Qt-vrije navigatieboom PBS → functie → faalwijze (slice 35 issue 07)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from rcm_core.models import RCMProject


class NavigationNodeKind(Enum):
    PBS = "pbs"
    FUNCTIE = "functie"
    FAALWIJZE = "faalwijze"


@dataclass(frozen=True)
class RcmNavigationNode:
    kind: NavigationNodeKind
    node_id: str
    label: str
    children: tuple["RcmNavigationNode", ...] = ()


def scope_pbs_id_for_node(node: RcmNavigationNode, project: RCMProject) -> str | None:
    """PBS-id voor presentatie-scope (subtree-filter)."""
    if node.kind == NavigationNodeKind.PBS:
        return node.node_id if node.node_id in project.pbs_items else None
    if node.kind == NavigationNodeKind.FUNCTIE:
        functie = project.functies.get(node.node_id)
        return functie.pbs_id if functie is not None else None
    if node.kind == NavigationNodeKind.FAALWIJZE:
        fm = project.faalwijzes.get(node.node_id)
        return fm.pbs_id if fm is not None else None
    return None


def build_rcm_navigation_tree(project: RCMProject) -> tuple[RcmNavigationNode, ...]:
    """Deterministische structuurboom met Isograph-ID's op functie/faalwijze."""
    if not project.pbs_items:
        return ()

    children_pbs: dict[str | None, list[str]] = {}
    for pbs_id, item in project.pbs_items.items():
        parent = item.parent_pbs_id
        if parent is None or parent not in project.pbs_items:
            parent_key: str | None = None
        else:
            parent_key = parent
        children_pbs.setdefault(parent_key, []).append(pbs_id)
    for child_ids in children_pbs.values():
        child_ids.sort()

    functies_by_pbs: dict[str, list[str]] = {}
    for fid, functie in project.functies.items():
        if functie.pbs_id in project.pbs_items:
            functies_by_pbs.setdefault(functie.pbs_id, []).append(fid)
    for ids in functies_by_pbs.values():
        ids.sort()

    fm_by_functie: dict[str, list[str]] = {}
    for fm_id, fm in project.faalwijzes.items():
        if fm.functie_id in project.functies:
            fm_by_functie.setdefault(fm.functie_id, []).append(fm_id)
    for ids in fm_by_functie.values():
        ids.sort()

    def functie_node(functie_id: str) -> RcmNavigationNode:
        fm_children = tuple(
            RcmNavigationNode(
                kind=NavigationNodeKind.FAALWIJZE,
                node_id=fm_id,
                label=fm_id,
            )
            for fm_id in fm_by_functie.get(functie_id, ())
        )
        return RcmNavigationNode(
            kind=NavigationNodeKind.FUNCTIE,
            node_id=functie_id,
            label=functie_id,
            children=fm_children,
        )

    def pbs_node(pbs_id: str) -> RcmNavigationNode:
        item = project.pbs_items[pbs_id]
        label = item.bouwdeel_naam or pbs_id
        sub_pbs = tuple(pbs_node(cid) for cid in children_pbs.get(pbs_id, ()))
        func_nodes = tuple(functie_node(fid) for fid in functies_by_pbs.get(pbs_id, ()))
        return RcmNavigationNode(
            kind=NavigationNodeKind.PBS,
            node_id=pbs_id,
            label=label,
            children=sub_pbs + func_nodes,
        )

    return tuple(pbs_node(rid) for rid in children_pbs.get(None, ()))
