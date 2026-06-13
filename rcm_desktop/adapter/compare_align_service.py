"""FM-uitlijning voor dual-project compare (slice 95 issue 05)."""

from __future__ import annotations

from dataclasses import dataclass

from rcm_core.models import RCMProject


@dataclass(frozen=True)
class FailureModePair:
    fm_id_a: str | None
    fm_id_b: str | None
    match_kind: str  # id | fingerprint | manual | unmatched_a | unmatched_b


def align_failure_modes(project_a: RCMProject, project_b: RCMProject) -> tuple[FailureModePair, ...]:
    ids_a = set(project_a.faalwijzes.keys())
    ids_b = set(project_b.faalwijzes.keys())
    matched = sorted(ids_a & ids_b)
    only_a = sorted(ids_a - ids_b)
    only_b = sorted(ids_b - ids_a)
    pairs: list[FailureModePair] = [
        FailureModePair(fm_id_a=fm_id, fm_id_b=fm_id, match_kind="id") for fm_id in matched
    ]
    pairs.extend(
        FailureModePair(fm_id_a=fm_id, fm_id_b=None, match_kind="unmatched_a") for fm_id in only_a
    )
    pairs.extend(
        FailureModePair(fm_id_a=None, fm_id_b=fm_id, match_kind="unmatched_b") for fm_id in only_b
    )
    return tuple(pairs)
