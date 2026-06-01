"""PBS boompad labels — Qt-vrij (slice 40)."""

from __future__ import annotations

from rcm_core.models import RCMProject

_PATH_SEPARATOR = " › "


def path_label(project: RCMProject, pbs_id: str) -> str:
    """Pad root → knoop via parent_pbs_id; segment = bouwdeel_naam of pbs_id."""
    item = project.pbs_items.get(pbs_id)
    if item is None:
        return pbs_id

    segments: list[str] = []
    seen: set[str] = set()
    current = item
    while current is not None:
        if current.pbs_id in seen:
            break
        seen.add(current.pbs_id)
        label = (current.bouwdeel_naam or "").strip() or current.pbs_id
        segments.append(label)
        parent_id = current.parent_pbs_id
        if parent_id is None or parent_id not in project.pbs_items:
            break
        current = project.pbs_items[parent_id]

    segments.reverse()
    return _PATH_SEPARATOR.join(segments)
